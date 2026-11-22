# Misinformation Detection Demo

This folder contains the Streamlit interface used to demonstrate FireFusion’s misinformation-detection workflow.

The user enters a bushfire-related claim, and the interface sends it to the existing `/predict/misinformation` API. The multi-task model returns a prediction for each of three tasks — misinformation (`TRUE`/`FALSE`), urgency, and humanitarian category — each with its class, confidence and class probabilities.

## Run the demo

Set up the [virtual environment and trained checkpoint](../README.md#quick-start-for-misinformation). From `ai-modelling/`, start the API and check that `/predict/models?domain=misinformation` lists `misinfo-deberta`.

```bash
python -m uvicorn api.main:app --reload --host 127.0.0.1 --port 8080
```

In a second terminal, run the interface from the same directory and environment.

```bash
python -m streamlit run demo/misinformation_app.py --server.address 127.0.0.1
```

The interface will open at:

```text
http://127.0.0.1:8501
```

In Windows PowerShell, you can use `.\.venv\Scripts\python.exe` in place of `python` without activating the environment.

The trained DeBERTa checkpoint configured in `api/config/models.yaml` must be available before starting the API.

## Run the tests

```bash
python -m pytest tests/test_misinformation_demo.py -v
```

To run the interface and existing DeBERTa tests together:

```bash
python -m pytest tests/test_deberta.py tests/test_misinformation_demo.py -v
```

## Changing the API address

The interface uses the local API on port `8080` by default. To use another address, set the URL in the terminal where you run Streamlit.

```bash
export FIREFUSION_MISINFORMATION_API_URL="http://127.0.0.1:8081/predict/misinformation"
```

```powershell
$env:FIREFUSION_MISINFORMATION_API_URL = "http://127.0.0.1:8081/predict/misinformation"
```

The classifier output is intended for demonstration and decision support. Bushfire information should still be verified through official emergency-service sources.
