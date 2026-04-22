from psycopg import AsyncConnection
from .aggregator_service import AggregatorService
from ...config.config import environment

async def sql_event_listener(aggregator_service: AggregatorService):

    connection = await AsyncConnection.connect(environment.relational_db_url, autocommit=True)

    # example sql : "NOTIFY fire_events_channel, 'test';"
    await connection.execute("LISTEN fire_events_channel;")

    # delegates 
    async for notify in connection.notifies():
        print(f"Received: {notify.payload}")
        await aggregator_service.handle_events_update()