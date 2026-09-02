from fastapi import APIRouter, Query

from ..internal.repositories.aggregator_repository import AggregatorRepository


router = APIRouter(
    prefix="/internal/data",
    tags=["internal-data"]
)


@router.get("/fire-incidents")
async def get_fire_incidents(
    days: int = Query(default=14, ge=1, le=3650)
):
    repository = AggregatorRepository()

    return await repository.get_recent_fire_incidents_v2(days)


@router.get("/fire-risk-inputs")
async def get_fire_risk_inputs(
    hours: int = Query(
        default=720,
        ge=1,
        le=8760
    )
):
    """
    Return currently available Data Engineering weather/environmental
    data for Fire Risk Map AI integration.

    This endpoint exposes DE source data, NOT an AI ForecastRequest.
    """

    repository = AggregatorRepository()

    return await repository.get_fire_risk_source_data(hours)