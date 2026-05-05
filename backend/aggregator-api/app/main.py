from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routers import hello
from .internal.services.sql_event_listener import sql_event_listener
from .internal.services.aggregator_service import AggregatorService
from .internal.services.messaging_service import MessagingService
import asyncio

# handling specific object lifecycles
# similar to @Bean from Spring Boot
@asynccontextmanager
async def init_lifespan_objects(app: FastAPI):
    messaging_service = await MessagingService.create()
    aggregator_service = AggregatorService(messaging_service)

    aggregator_task = asyncio.create_task(sql_event_listener(aggregator_service))

    yield

    aggregator_task.cancel()
    await messaging_service.close()

app = FastAPI(lifespan=init_lifespan_objects)
app.include_router(hello.router)