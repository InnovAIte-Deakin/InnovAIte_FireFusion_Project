"""
Misinformation scoring functions operating on a LoadedModel bundle.

The adapter supports both the legacy binary DeBERTa classifier and the
multi-task DeBERTa model.
"""

from typing import Any, Literal

from api.model_loader import LoadedModel
from src.models.misinformation.deberta import classify_multitask, classify_text

Severity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]


def risk_score_max_softmax(probabilities: dict[str, float]) -> float:
    if not probabilities:
        return 0.0
    return float(max(probabilities.values()))


def severity_from_risk(risk_score: float) -> Severity:
    if risk_score >= 0.9:
        return "CRITICAL"
    if risk_score >= 0.75:
        return "HIGH"
    if risk_score >= 0.6:
        return "MEDIUM"
    return "LOW"


def _with_misinformation_risk(prediction: dict[str, Any]) -> dict[str, Any]:
    result = dict(prediction)
    probabilities = result.get("probabilities", {})
    risk_score = risk_score_max_softmax(probabilities)
    result["risk_score"] = risk_score
    result["severity"] = severity_from_risk(risk_score)
    return result


def _predict_tasks(
    content: str,
    bundle: LoadedModel,
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any] | None]:
    common_args = {
        "tokenizer": bundle.tokenizer,
        "model": bundle.model,
        "device": bundle.device,
        "max_len": bundle.max_len,
    }

    if bundle.kind == "deberta_sequence_binary":
        binary_result = classify_text(content, **common_args)
        return _with_misinformation_risk(binary_result), None, None

    if bundle.kind == "deberta_multitask":
        task_results = classify_multitask(content, **common_args)

        misinformation = task_results.get("misinformation") or task_results.get("misinfo")
        if misinformation is None:
            raise ValueError("multi-task model did not return a misinformation prediction")

        urgency = task_results.get("urgency")
        humanitarian = (
            task_results.get("humanitarian_task")
            or task_results.get("humanitarian")
        )
        return _with_misinformation_risk(misinformation), urgency, humanitarian

    raise ValueError(f"unsupported misinformation model kind: {bundle.kind!r}")


def predict_misinformation(
    post: dict[str, Any],
    bundle: LoadedModel,
) -> dict[str, Any]:
    """
    Classify one social post.

    Required keys are ``id`` and ``content``. A multi-task model returns
    misinformation, urgency, and humanitarian predictions in one pass.
    """
    if "id" not in post or "content" not in post:
        raise KeyError("post must include 'id' and 'content'")

    content = post["content"]
    if not isinstance(content, str) or not content.strip():
        raise ValueError("post content must be a non-empty string")

    misinformation, urgency, humanitarian = _predict_tasks(content, bundle)

    return {
        "model_id": bundle.model_id,
        "domain": bundle.domain,
        "id": post["id"],
        "author_name": post.get("author_name"),
        "platform": post.get("platform"),
        "content": content,
        "share_count": post.get("share_count"),
        "ts": post.get("ts"),
        "post_url": post.get("post_url"),
        "misinformation": misinformation,
        "urgency": urgency,
        "humanitarian_task": humanitarian,
        "checkpoint": str(bundle.checkpoint_path),
    }