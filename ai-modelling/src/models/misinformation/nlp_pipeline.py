"""
End-to-end NLP pipeline for narrative clustering.

This module orchestrates the workflow: load/prepare posts, call the LLM client,
run narrative clustering, and return/save structured cluster outputs for
downstream analysis and monitoring.
""""""
Cluster social media posts into bushfire misinformation narratives.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .llm_client import LLMClient,  LLMConfig, render_prompt
from typing import Literal
from pydantic import BaseModel, Field
import json
from pathlib import Path

# ---------- Input schemas ----------
class InputPost(BaseModel):
    id: str
    author: str
    platform: str
    content: str
    share_count: int
    timestamp: datetime
    post_url: str


# ---------- Narrative output schemas ----------
Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]

class NarrativePost(BaseModel):
    post_id: str
    key_claim: str
    platform: str

class Narrative(BaseModel):
    narrative_id: str
    narrative_summary: str
    severity: Severity
    post_count: int = Field(ge=0)
    posts: list[NarrativePost]
    timestamp_earliest: datetime
    timestamp_latest: datetime

class NarrativeResult(BaseModel):
    narratives: list[Narrative]


# ---------- Narrative Clustering ----------
CLUSTER_PROMPT_TEMPLATE = """
You are a wildfire misinformation analyst supporting emergency risk triage.

Goal:
Cluster social posts into coherent misinformation narratives for bushfire operations.
Prioritize life-safety harm and decision-impact during active fire events.

Input:
You will receive a JSON array named posts_json.
Each post has:
- id (string)
- author (string)
- platform (string)
- content (string)
- share_count (integer)
- timestamp (ISO-8601 string)
- post_url (string)

Output format (required):
Return ONLY one valid JSON object with this top-level shape:
{
  "narratives": [
    {
      "narrative_id": "nar_001",
      "narrative_summary": "string",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "post_count": 0,
      "posts": [
        {
          "post_id": "post_001",
          "key_claim": "string",
          "platform": "TWITTER"
        }
      ],
      "timestamp_earliest": "2026-01-22T06:14:00+11:00",
      "timestamp_latest": "2026-01-22T07:48:00+11:00"
    }
  ]
}

Severity rules:
- CRITICAL: immediate life-safety harm if believed (fake evacuation/safety directions/scams).
- HIGH: materially false claims likely to alter public decisions/trust.
- MEDIUM: unverified/speculative claims with moderate harm.
- LOW: weak/low-impact misleading content.

Strict constraints:
- JSON only, no markdown.
- Do not invent post IDs.
- Every post_id must exist in input.
- A post can belong to only one narrative.
- post_count must equal len(posts).
- timestamp_earliest/latest must be min/max timestamps from member posts.

Now process this input:
{posts_json}
""".strip()


@dataclass
class ClusterConfig:
    strict_json: bool = True
    enforce_all_posts_used_once: bool = True

class NarrativeClusterer:
    def __init__(
        self,
        client: LLMClient,
        *,
        prompt_template: str,
        config: ClusterConfig | None = None,
    ) -> None:
        self.client = client
        self.prompt_template = prompt_template
        self.config = config or ClusterConfig()

    @staticmethod
    def _normalize_input_posts(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # unify incoming backend field variants
        return [
            {
                "id": p.get("id"),
                "author": p.get("author", p.get("author_name")),
                "platform": p.get("platform"),
                "content": p.get("content"),
                "share_count": p.get("share_count", 0),
                "timestamp": p.get("timestamp", p.get("ts")),
                "post_url": p.get("post_url"),
            }
            for p in posts
        ]

    @staticmethod
    def _validate_input_posts(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        validated = [InputPost.model_validate(p) for p in posts]
        return [v.model_dump(mode="json") for v in validated]

    def _validate_output(
        self,
        result: dict[str, Any],
        input_posts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        parsed = NarrativeResult.model_validate(result)
        input_ids = {str(p["id"]) for p in input_posts}
        used_ids: set[str] = set()

        for nar in parsed.narratives:
            # enforce post_count consistency even if model got it wrong
            nar.post_count = len(nar.posts)

            for item in nar.posts:
                pid = str(item.post_id)
                if pid not in input_ids:
                    raise ValueError(f"Unknown post_id in output: {pid}")
                if pid in used_ids:
                    raise ValueError(f"Duplicate post_id across narratives: {pid}")
                used_ids.add(pid)

        if self.config.enforce_all_posts_used_once and used_ids != input_ids:
            missing = sorted(input_ids - used_ids)
            raise ValueError(f"Some input posts were not assigned: {missing}")

        return parsed.model_dump(mode="json")

    def run(self, posts: list[dict[str, Any]]) -> dict[str, Any]:
        normalized = self._normalize_input_posts(posts)
        posts_for_prompt = self._validate_input_posts(normalized)
        prompt = render_prompt(self.prompt_template, {"posts_json": posts_for_prompt})

        result = (
            self.client.generate_json(prompt)
            if self.config.strict_json
            else {"raw_output": self.client.generate_text(prompt)}
        )

        if not self.config.strict_json:
            return result

        return self._validate_output(result, posts_for_prompt)


# ---------- Narrative Clustering ----------
def main() -> None:
    # Adjust path if running from a different working directory.
    project_root = Path(__file__).resolve().parents[4]
    posts_path = project_root / "posts.json"

    raw_posts = json.loads(posts_path.read_text(encoding="utf-8"))

    client = LLMClient(
        LLMConfig(
            provider="gemini",          # or "openai"
            model="gemini-3-flash-preview",
            temperature=0.2,
            max_retries=3,
        )
    )

    clusterer = NarrativeClusterer(
        client=client,
        prompt_template=CLUSTER_PROMPT_TEMPLATE,   # rename to CLUSTER_PROMPT_TEMPLATE if you can
        config=ClusterConfig(
            strict_json=True,
            enforce_all_posts_used_once=True,
        ),
    )

    result = clusterer.run(raw_posts)

    # Small test output
    narratives = result.get("narratives", [])
    print(f"Generated narratives: {len(narratives)}")
    for n in narratives:
        print(
            f"- {n['narrative_id']} | {n['severity']} | "
            f"posts={n['post_count']} | "
            f"{n['timestamp_earliest']} -> {n['timestamp_latest']}"
        )

if __name__ == "__main__":
    main()