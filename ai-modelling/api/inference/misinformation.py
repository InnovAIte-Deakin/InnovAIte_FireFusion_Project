"""
Misinformation scoring: pure functions over a ``LoadedModel`` bundle.

Routers call this after resolving ``model_id`` via ``model_loader``.
"""
from typing import Any, Literal

from api.model_loader import LoadedModel
from src.models.misinformation.deberta import classify_text

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


def predict_misinformation(post: dict[str, Any], bundle: LoadedModel) -> dict[str, Any]:
    """
    Classify a single social post. Required keys: ``id``, ``content``.
    """
    if "id" not in post or "content" not in post:
        raise KeyError("post must include 'id' and 'content'")

    cls_out = classify_text(
        str(post["content"]),
        tokenizer=bundle.tokenizer,
        model=bundle.model,
        device=bundle.device,
        max_len=bundle.max_len,
    )
    probs = cls_out["probabilities"]
    risk = risk_score_max_softmax(probs)
    severity = severity_from_risk(risk)

    return {
        "model_id": bundle.model_id,
        "domain": bundle.domain,
        "id": post["id"],
        "author_name": post.get("author_name"),
        "platform": post.get("platform"),
        "content": post["content"],
        "share_count": post.get("share_count"),
        "ts": post.get("ts"),
        "post_url": post.get("post_url"),
        "label_id": cls_out["label_id"],
        "label": cls_out["label"],
        "confidence": cls_out["confidence"],
        "probabilities": probs,
        "risk_score": risk,
        "severity": severity,
        "checkpoint": str(bundle.checkpoint_path),
    }