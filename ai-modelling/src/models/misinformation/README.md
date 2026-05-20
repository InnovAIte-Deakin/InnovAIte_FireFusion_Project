# Misinformation NLP Module

## Overview

This folder contains the Natural Language Processing (NLP) models and pipelines used for bushfire misinformation detection and narrative analysis in the FireFusion project.

The module supports:
- Binary misinformation classification using DeBERTa v3-large
- Narrative clustering of social media posts using Large Language Models (LLMs)
- Prompt-based misinformation analysis
- Structured JSON validation for NLP outputs
- Provider-agnostic LLM integration (Gemini/OpenAI)

The misinformation pipeline is designed to support emergency monitoring workflows by identifying harmful misinformation narratives during bushfire events.

---

# Folder Structure

| File | Purpose |
|---|---|
| `README.md` | Main overview and onboarding guide for the misinformation NLP module |
| `deberta.py` | DeBERTa v3-large model utilities for misinformation classification |
| `llm_client.py` | Provider-agnostic LLM client supporting Gemini and OpenAI |
| `nlp_pipeline.py` | End-to-end narrative clustering and misinformation analysis pipeline |

---

# Module Architecture

This module contains two main NLP systems:

```text
1. Supervised Classification
   ↓
   DeBERTa v3-large
   ↓
   Binary misinformation detection

2. LLM Narrative Clustering
   ↓
   Gemini / OpenAI
   ↓
   Narrative grouping + structured JSON outputs
```

---

# 1. DeBERTa Misinformation Classifier

The `deberta.py` module contains utilities for:
- loading training datasets
- tokenization
- dataset preparation
- classifier creation
- checkpoint loading
- text classification inference

The classifier uses:

```text
microsoft/deberta-v3-large
```

for binary classification:
- `non_misinformation`
- `misinformation`

## Main Features

### Dataset Utilities
- CSV and JSON dataset loading
- schema validation
- label validation

### PyTorch Dataset Support
- custom dataset wrapper
- batch collation utilities
- tokenizer integration

### Model Utilities
- create fresh classifier models
- load checkpoints
- run inference on input text

### Prediction Output
The classifier returns:
- predicted label
- label confidence
- class probabilities

---

# 2. LLM Client Abstraction

The `llm_client.py` module provides a reusable provider-agnostic interface for Large Language Models.

Supported providers:
- Gemini
- OpenAI

## Features

### Text Generation
- prompt-based generation
- retry + backoff handling
- configurable temperature

### Structured JSON Generation
- JSON cleanup
- markdown fence removal
- JSON parsing + validation

### Prompt Utilities
- prompt template rendering
- variable replacement
- prompt loading from files

### Batch Processing
- process JSON datasets
- generate augmented misinformation samples
- narrative clustering support

---

# 3. Narrative Clustering Pipeline

The `nlp_pipeline.py` module orchestrates the full misinformation narrative analysis workflow.

The pipeline:
1. loads social media posts
2. validates post schema
3. sends prompts to LLM providers
4. clusters related misinformation narratives
5. validates structured outputs
6. returns standardized JSON results

---

# Narrative Clustering Workflow

```text
Raw Social Media Posts
        ↓
Input Validation
        ↓
Prompt Construction
        ↓
LLM Narrative Clustering
        ↓
JSON Validation
        ↓
Structured Narrative Output
```

---

# Narrative Output Structure

The pipeline generates structured narrative objects containing:
- narrative ID
- narrative summary
- severity level
- grouped posts
- timestamps
- key misinformation claims

## Severity Levels

| Severity | Meaning |
|---|---|
| `CRITICAL` | Immediate life-safety misinformation |
| `HIGH` | Harmful false claims affecting public trust or decisions |
| `MEDIUM` | Speculative or moderately harmful misinformation |
| `LOW` | Low-impact misleading content |

---

# Validation & Safety Features

The NLP pipeline includes strict validation logic to improve output reliability.

## Input Validation
- validates post schema
- validates timestamps
- validates required fields

## Output Validation
- ensures valid JSON structure
- prevents duplicate post assignment
- verifies narrative consistency
- validates severity labels

---

# Technologies Used

- Python
- PyTorch
- Hugging Face Transformers
- DeBERTa v3-large
- Pydantic
- OpenAI API
- Gemini API
- Pandas

---

# Typical Use Cases

This module supports:
- Bushfire misinformation monitoring
- Social media narrative analysis
- Emergency communication risk analysis
- Harmful content detection
- Narrative clustering
- NLP-based emergency intelligence workflows

---

# Setup Notes

Install dependencies from the project root:

```bash
pip install -r ai-modelling/requirements.txt
```

Configure API keys before running LLM workflows:

```bash
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
```

---

# Example Workflow

```python
from src.models.misinformation.llm_client import LLMClient, LLMConfig
from src.models.misinformation.nlp_pipeline import NarrativeClusterer

client = LLMClient(
    LLMConfig(
        provider="gemini",
        model="gemini-3-flash-preview"
    )
)

clusterer = NarrativeClusterer(
    client=client,
    prompt_template=CLUSTER_PROMPT_TEMPLATE
)

result = clusterer.run(posts)
```

---

# Notes

- The narrative clustering pipeline relies heavily on prompt engineering and structured JSON validation.
- Strict validation rules help reduce malformed or inconsistent LLM outputs.
- The DeBERTa classifier and LLM narrative clustering system are designed as complementary components.
- The module is structured to support future expansion into broader misinformation monitoring workflows.
