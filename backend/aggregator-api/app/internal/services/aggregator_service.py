from .messaging_service import MessagingService
from ..repositories.aggregator_repository import AggregatorRepository
from ..models.fire_event import FireEvent

class AggregatorService:
    def __init__(self, messaging: MessagingService):
        self.repository = AggregatorRepository()
        self.messaging = messaging

    async def handle_events_update(self):

        # get data from database
        data: list[FireEvent] = await self.repository.get_recent_events(365)

        for d in data:
            print(d.event_id)

        # encode the model into a JSON
        broker_message = [event.model_dump(mode="json") for event in data]

        await self.messaging.publish_to_forecast_model(broker_message)