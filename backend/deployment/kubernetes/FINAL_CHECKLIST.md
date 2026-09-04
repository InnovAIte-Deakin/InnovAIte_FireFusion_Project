# Final validation checklist

- [x] Base Kubernetes package renders successfully.
- [x] Local Kubernetes overlay renders successfully.
- [x] Dependency-first local bootstrap renders successfully.
- [x] FireFusion API reaches 1/1 Running with zero restarts.
- [x] Aggregator API reaches 1/1 Running with zero restarts.
- [x] Model API reaches 1/1 Running with zero restarts.
- [x] PostgreSQL, RabbitMQ, and Redis reach 1/1 Running.
- [x] Internal `/health` checks pass for all three Backend APIs.
- [x] Aggregator Docker image builds without baking `API_KEY` into the image.
