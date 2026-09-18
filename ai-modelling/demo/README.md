# Multi-task Misinformation Demo

This folder contains the Streamlit interface used for the FireFusion text-analysis demonstration.

A user enters a bushfire-related claim or selects one of the prepared examples. The interface sends the claim to the existing `/predict/misinformation` API and displays results from the three DeBERTa classification tasks:

- misinformation detection
- urgency classification
- humanitarian classification

Each result includes a predicted label, confidence score and class probabilities. The interface also displays the existing risk score, severity and full technical API response.

## Required checkpoint

Download the `multi-task-deberta` checkpoint and place it at:

```text
src/models/misinformation/checkpoints/multi-task-deberta