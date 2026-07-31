# Model Output Schemas

This directory contains **JSON Schema** definitions (Draft 2020-12) for every AI model output in the FireFusion project. These schemas serve as the formal contract between the AI Modelling team and downstream consumers (Backend, Data Engineering, Frontend).

## Schema Files

| Schema File | Model | Domain | Description |
|---|---|---|---|
| `bushfire_forecast_output.schema.json` | ConvLSTM Spatiotemporal Forecaster | Bushfire | Gridded environmental variable forecasts (7 features × H×W grid × horizon steps) |
| `bushfire_risk_classification_output.schema.json` | TCN Binary Classifier / FireRiskPipeline | Bushfire | Fire occurrence probability and optional 5-class risk level per grid cell |
| `misinformation_detection_output.schema.json` | DeBERTa v3-large | Misinformation | Post-level binary classification with confidence, risk score, and severity |
| `misinformation_narrative_output.schema.json` | LLM Narrative Clusterer | Misinformation | Grouped narrative clusters with severity ratings for operational triage |

## How to Validate

### Python (jsonschema)

```python
import json
import jsonschema

# Load the schema
with open("api/schemas/output/misinformation_detection_output.schema.json") as f:
    schema = json.load(f)

# Validate a model output against it
output = {
    "model_id": "misinfo-deberta",
    "domain": "misinformation",
    "id": "post_001",
    "content": "Fires are being started deliberately in national parks",
    "label_id": 1,
    "label": "misinformation",
    "confidence": 0.92,
    "probabilities": {"non_misinformation": 0.08, "misinformation": 0.92},
    "risk_score": 0.92,
    "severity": "CRITICAL",
    "checkpoint": "src/models/misinformation/checkpoints/misinfo-deberta"
}

jsonschema.validate(instance=output, schema=schema)
print("Valid!")
```

### JavaScript / Node.js (ajv)

```javascript
const Ajv = require("ajv/dist/2020");
const ajv = new Ajv();

const schema = require("./misinformation_detection_output.schema.json");
const validate = ajv.compile(schema);

const output = { /* model output */ };
const valid = validate(output);
if (!valid) console.error(validate.errors);
```

## Versioning

Each schema includes a `model_version` field (or is versioned at the top level). Follow **semver** conventions:

- **Patch** (`1.0.x`): Documentation-only changes, adding optional fields
- **Minor** (`1.x.0`): Adding new required fields (backward-compatible for consumers that ignore unknowns)
- **Major** (`x.0.0`): Removing or renaming fields, changing types — **breaking change**

## Relationship to Pydantic Models

These schemas are intentionally kept in sync with the Pydantic models in `api/schemas/`:

| JSON Schema | Pydantic Model |
|---|---|
| `misinformation_detection_output.schema.json` | `api/schemas/misinformation.py → MisinformationPostOut` |
| `misinformation_narrative_output.schema.json` | `src/models/misinformation/nlp_pipeline.py → NarrativeResult` |

When updating Pydantic models, please update the corresponding JSON schema file to stay in sync.

## Source References

- **ConvLSTM Forecaster**: `src/models/bushfire/ts_convlstm_forecaster.py`, `ts_convlstm_forecaster_inference.py`
- **TCN Classifier**: `src/models/bushfire/tcn_classifier.py`, `fire_risk_pipeline.py`
- **DeBERTa Classifier**: `src/models/misinformation/deberta.py`, `api/inference/misinformation.py`
- **Narrative Clusterer**: `src/models/misinformation/nlp_pipeline.py`, `llm_client.py`
