Data / aggregator API
   |
   | publishes FireEvent data
   v
RabbitMQ queue: "forecast"
   |
   | model-api consumes it
   v
ModelService.consume_data_publish_prediction()
   |
   | currently ignores real data
   v
GeoJsonService returns random geojson_data-0 to 9
   |
   | publishes to RabbitMQ
   v
RabbitMQ queue: "predictions"
   |
   v
firefusion-api consumes prediction