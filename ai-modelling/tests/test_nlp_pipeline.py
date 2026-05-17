import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.misinformation.nlp_pipeline import (
    NarrativeClusterer,
    ClusterConfig,
    CLUSTER_PROMPT_TEMPLATE,
)


class DummyClient:
    def __init__(self, json_result=None, text_result="raw-ok"):
        self._json_result = json_result
        self._text_result = text_result

    def generate_json(self, prompt: str):
        return self._json_result

    def generate_text(self, prompt: str):
        return self._text_result


@pytest.fixture
def raw_posts():
    return [
        {
            "id": "post_001",
            "author_name": "@a",
            "platform": "TWITTER",
            "content": "False evacuation order now",
            "share_count": 10,
            "ts": "2026-01-22T06:14:00+11:00",
            "post_url": "https://x.com/1",
        },
        {
            "id": "post_002",
            "author_name": "@b",
            "platform": "FACEBOOK",
            "content": "Road closed rumor",
            "share_count": 5,
            "ts": "2026-01-22T07:14:00+11:00",
            "post_url": "https://fb.com/2",
        },
    ]


def make_clusterer(json_result, strict_json=True, enforce_all=True):
    client = DummyClient(json_result=json_result)
    return NarrativeClusterer(
        client=client,
        prompt_template=CLUSTER_PROMPT_TEMPLATE,
        config=ClusterConfig(
            strict_json=strict_json,
            enforce_all_posts_used_once=enforce_all,
        ),
    )


def test_normalize_maps_author_and_ts(raw_posts):
    c = make_clusterer({"narratives": []}, enforce_all=False)
    normalized = c._normalize_input_posts(raw_posts)
    assert normalized[0]["author"] == "@a"
    assert normalized[0]["timestamp"] == "2026-01-22T06:14:00+11:00"


def test_run_success_valid_output(raw_posts):
    model_output = {
        "narratives": [
            {
                "narrative_id": "nar_001",
                "narrative_summary": "False evacuation order",
                "severity": "CRITICAL",
                "post_count": 999,  # should be corrected to len(posts)=2
                "posts": [
                    {"post_id": "post_001", "key_claim": "evacuation ordered", "platform": "TWITTER"},
                    {"post_id": "post_002", "key_claim": "road closed", "platform": "FACEBOOK"},
                ],
                "timestamp_earliest": "2026-01-22T06:14:00+11:00",
                "timestamp_latest": "2026-01-22T07:14:00+11:00",
            }
        ]
    }
    c = make_clusterer(model_output, enforce_all=True)
    out = c.run(raw_posts)
    assert "narratives" in out
    assert out["narratives"][0]["post_count"] == 2


def test_unknown_post_id_raises(raw_posts):
    bad = {
        "narratives": [
            {
                "narrative_id": "nar_001",
                "narrative_summary": "x",
                "severity": "HIGH",
                "post_count": 1,
                "posts": [{"post_id": "post_999", "key_claim": "x", "platform": "TWITTER"}],
                "timestamp_earliest": "2026-01-22T06:14:00+11:00",
                "timestamp_latest": "2026-01-22T07:14:00+11:00",
            }
        ]
    }
    c = make_clusterer(bad)
    with pytest.raises(ValueError, match="Unknown post_id"):
        c.run(raw_posts)


def test_duplicate_post_id_across_narratives_raises(raw_posts):
    bad = {
        "narratives": [
            {
                "narrative_id": "nar_001",
                "narrative_summary": "x",
                "severity": "HIGH",
                "post_count": 1,
                "posts": [{"post_id": "post_001", "key_claim": "x", "platform": "TWITTER"}],
                "timestamp_earliest": "2026-01-22T06:14:00+11:00",
                "timestamp_latest": "2026-01-22T06:14:00+11:00",
            },
            {
                "narrative_id": "nar_002",
                "narrative_summary": "y",
                "severity": "MEDIUM",
                "post_count": 1,
                "posts": [{"post_id": "post_001", "key_claim": "y", "platform": "TWITTER"}],
                "timestamp_earliest": "2026-01-22T07:14:00+11:00",
                "timestamp_latest": "2026-01-22T07:14:00+11:00",
            },
        ]
    }
    c = make_clusterer(bad)
    with pytest.raises(ValueError, match="Duplicate post_id"):
        c.run(raw_posts)


def test_missing_post_assignment_raises(raw_posts):
    bad = {
        "narratives": [
            {
                "narrative_id": "nar_001",
                "narrative_summary": "x",
                "severity": "HIGH",
                "post_count": 1,
                "posts": [{"post_id": "post_001", "key_claim": "x", "platform": "TWITTER"}],
                "timestamp_earliest": "2026-01-22T06:14:00+11:00",
                "timestamp_latest": "2026-01-22T06:14:00+11:00",
            }
        ]
    }
    c = make_clusterer(bad, enforce_all=True)
    with pytest.raises(ValueError, match="not assigned"):
        c.run(raw_posts)


def test_non_strict_json_returns_raw(raw_posts):
    c = NarrativeClusterer(
        client=DummyClient(json_result={}, text_result="hello"),
        prompt_template=CLUSTER_PROMPT_TEMPLATE,
        config=ClusterConfig(strict_json=False, enforce_all_posts_used_once=False),
    )
    out = c.run(raw_posts)
    assert out == {"raw_output": "hello"}