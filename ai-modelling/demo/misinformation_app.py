"""Streamlit interface for demonstrating FireFusion misinformation detection."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4
import math
import streamlit as st


DEFAULT_API_URL = "http://localhost:8080/predict/misinformation"

SAMPLE_CLAIMS = {
    "Evacuation claim": (
        "The evacuation warning for communities near the bushfire has been cancelled."
    ),
    "Road closure claim": (
        "Emergency services have closed the highway because of an active bushfire."
    ),
    "Unofficial claim": (
        "A social media post says the bushfire is completely under control, "
        "but authorities have not confirmed it."
    ),
}


def validate_claim(claim: str) -> str:
    """Validate and clean the claim entered by the user."""
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("Please enter a claim before starting the analysis.")

    cleaned_claim = claim.strip()

    if len(cleaned_claim) < 10:
        raise ValueError("Please enter a more complete claim of at least 10 characters.")

    return cleaned_claim


def build_request_payload(claim: str) -> dict[str, Any]:
    """Create a request matching the existing misinformation API schema."""
    return {
        "id": f"demo-{uuid4().hex[:8]}",
        "author_name": "Demo user",
        "platform": "FireFusion demo",
        "content": validate_claim(claim),
        "share_count": 0,
        "post_url": "",
    }


def analyse_claim(
    claim: str,
    api_url: str = DEFAULT_API_URL,
    timeout: int = 120,
) -> dict[str, Any]:
    """Send a claim to the FireFusion misinformation API."""
    payload = build_request_payload(claim)

    request = Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(
            f"The prediction API returned an error ({exc.code}): {detail}"
        ) from exc
    except URLError as exc:
        raise ConnectionError(
            "Could not connect to the prediction API. "
            "Confirm that the FastAPI server is running on port 8080."
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("The prediction API returned an invalid response.") from exc

    required_fields = {
        "label",
        "confidence",
        "probabilities",
        "risk_score",
        "severity",
    }
    missing_fields = required_fields.difference(result)

    if missing_fields:
        raise RuntimeError(
            f"The API response is missing required fields: "
            f"{', '.join(sorted(missing_fields))}"
        )

    numeric_values = {
        "confidence": result["confidence"],
        "risk_score": result["risk_score"],
    }

    for field_name, value in numeric_values.items():
        try:
            valid = math.isfinite(float(value))
        except (TypeError, ValueError):
            valid = False

        if not valid:
            raise RuntimeError(
                f"The model returned an invalid {field_name}. "
                "Please check the loaded checkpoint."
            )

    probabilities = result["probabilities"]

    if not isinstance(probabilities, dict) or not probabilities:
        raise RuntimeError("The model returned invalid class probabilities.")

    for value in probabilities.values():
        try:
            valid = math.isfinite(float(value))
        except (TypeError, ValueError):
            valid = False

        if not valid:
            raise RuntimeError(
                "The model returned invalid class probabilities. "
                "Please check the loaded checkpoint."
            )

    return result


def format_label(label: str) -> str:
    """Convert an API label into a presentation-friendly label."""
    return label.replace("_", " ").strip().title()


def display_result(result: dict[str, Any]) -> None:
    """Display single-task or multi-task predictions returned by the API."""

    task_predictions = result.get("task_predictions")

    if isinstance(task_predictions, dict) and task_predictions:
        required_tasks = {"misinfo", "urgency", "humanitarian"}
        missing_tasks = required_tasks.difference(task_predictions)

        if missing_tasks:
            raise RuntimeError(
                "The API response is missing task predictions: "
                f"{', '.join(sorted(missing_tasks))}"
            )

        misinfo = task_predictions["misinfo"]
        is_misinformation = str(misinfo["label"]).lower() in {
            "misinformation",
            "true",
        }

        misinfo_label = format_label(str(misinfo["label"]))
        if is_misinformation:
            st.error(f"Misinformation detected: {misinfo_label}")
        else:
            st.success(f"Misinformation detected: {misinfo_label}")

        st.subheader("Multi-task analysis")

        task_details = (
            ("misinfo", "Misinformation"),
            ("urgency", "Urgency"),
            ("humanitarian", "Humanitarian category"),
        )
        columns = st.columns(3)

        for column, (task_name, title) in zip(columns, task_details):
            prediction = task_predictions[task_name]
            label = format_label(str(prediction["label"]))
            confidence = float(prediction["confidence"])

            with column:
                st.markdown(f"**{title}**")
                st.metric("Prediction", label)
                st.caption(f"Confidence: {confidence:.1%}")

        risk_column, severity_column = st.columns(2)
        risk_column.metric("Risk score", f"{float(result['risk_score']):.1%}")
        severity_column.metric("Severity", str(result["severity"]).upper())

        with st.expander("View probabilities for all tasks"):
            for task_name, title in task_details:
                st.markdown(f"**{title}**")
                probabilities = task_predictions[task_name]["probabilities"]

                for probability_label, probability in probabilities.items():
                    readable_label = format_label(str(probability_label))
                    probability_value = float(probability)
                    st.write(f"{readable_label}: {probability_value:.1%}")
                    st.progress(
                        min(max(probability_value, 0.0), 1.0)
                    )
    else:
        label = format_label(str(result["label"]))
        confidence = float(result["confidence"])
        risk_score = float(result["risk_score"])
        severity = str(result["severity"]).upper()
        probabilities = result["probabilities"]

        is_misinformation = str(result["label"]).lower() in {
            "misinformation",
            "true",
        }

        if is_misinformation:
            st.error(f"Prediction: {label}")
        else:
            st.success(f"Prediction: {label}")

        first, second, third = st.columns(3)
        first.metric("Confidence", f"{confidence:.1%}")
        second.metric("Risk score", f"{risk_score:.1%}")
        third.metric("Severity", severity)

        st.subheader("Class probabilities")

        for probability_label, probability in probabilities.items():
            readable_label = format_label(str(probability_label))
            probability_value = float(probability)
            st.write(f"{readable_label}: {probability_value:.1%}")
            st.progress(min(max(probability_value, 0.0), 1.0))

    st.caption(
        "This result is produced by an AI model and should be verified against "
        "official emergency-service information."
    )

    with st.expander("View technical response"):
        st.json(result)


def main() -> None:
    """Render the Streamlit demonstration interface."""
    st.set_page_config(
        page_title="FireFusion Misinformation Detection",
        page_icon="🔥",
        layout="centered",
    )

    st.title("🔥 FireFusion")
    st.header("Bushfire Misinformation Detection")
    st.write(
        "Enter a bushfire-related social media claim to analyse whether it may "
        "contain misinformation."
    )

    if "claim_text" not in st.session_state:
        st.session_state.claim_text = ""

    st.subheader("Example claims")
    sample_columns = st.columns(len(SAMPLE_CLAIMS))

    for column, (button_label, sample_text) in zip(
        sample_columns,
        SAMPLE_CLAIMS.items(),
    ):
        if column.button(button_label, use_container_width=True):
            st.session_state.claim_text = sample_text

    claim = st.text_area(
        "Claim or social media post",
        key="claim_text",
        height=150,
        placeholder="Paste a bushfire-related claim here...",
    )

    api_url = os.getenv("FIREFUSION_MISINFORMATION_API_URL", DEFAULT_API_URL)

    if st.button(
        "Analyse claim",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner("Analysing the claim..."):
                result = analyse_claim(claim, api_url=api_url)
            display_result(result)
        except (ValueError, ConnectionError, RuntimeError) as exc:
            st.error(str(exc))

    with st.sidebar:
        st.subheader("Demo information")
        st.write("Model: Multi-task DeBERTa classifier")
        st.write("Tasks:")
        st.write("• Misinformation detection")
        st.write("• Urgency classification")
        st.write("• Humanitarian classification")
        st.write("API server:")
        st.code("localhost:8080", language=None)
        st.write("Prediction endpoint:")
        st.code("/predict/misinformation", language=None)


if __name__ == "__main__":
    main()