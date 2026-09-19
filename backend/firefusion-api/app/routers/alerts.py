import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Response, Security, status
from fastapi.security.api_key import APIKeyHeader
from redis.exceptions import RedisError

from ..config.config import environment
from ..internal.alerting.service import SubscriptionLimitReached, SubscriptionService
from ..internal.alerting.store import SubscriptionStore
from ..internal.alerting.subscriptions import Subscription, SubscriptionCreate
from ..internal.services.caching_service import cache_client
from ..internal.services.forecast_service import ForecastService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/alerts", tags=["alerts"])

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

UNAVAILABLE = "Alerting is temporarily unavailable"


async def require_alerts_key(api_key: str | None = Security(api_key_header)) -> None:
    """Require the alerts API key.

    This API decides who is told about a fire, so it fails closed: with no key
    configured it is disabled outright rather than open. It is meant for agency
    systems, not browsers, and the service's CORS policy already allows only GET.
    """
    configured = environment.alerts_api_key
    if not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Alerting is not configured",
        )
    if not api_key or not hmac.compare_digest(api_key, configured):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


def get_subscription_service() -> SubscriptionService:
    return SubscriptionService(
        SubscriptionStore(cache_client),
        ForecastService(),
        max_subscriptions=environment.alerts_max_subscriptions,
        allow_insecure_webhooks=environment.alerts_allow_insecure_webhooks,
    )


@router.post(
    "/subscriptions",
    response_model=Subscription,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_alerts_key)],
    summary="Subscribe to risk escalation in a region",
    responses={
        401: {"description": "Invalid or missing API key"},
        409: {"description": "The subscription limit has been reached"},
        422: {"description": "The request is invalid or unacceptable"},
        503: {"description": "Alerting is not configured or temporarily unavailable"},
    },
)
async def create_subscription(
    request: SubscriptionCreate,
    service: SubscriptionService = Depends(get_subscription_service),
):
    """Subscribe to a region.

    Give the region as a bounding box or a GeoJSON polygon, the severity to be
    alerted at (risk_factor 1 is most severe, 5 least), and where to send alerts.
    The subscription records what the forecast currently shows over the region,
    so it is only alerted about changes from here.
    """
    try:
        return await service.create(request)
    except SubscriptionLimitReached as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except RedisError:
        logger.exception("Redis failure while creating a subscription")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE)


@router.get(
    "/subscriptions",
    response_model=list[Subscription],
    dependencies=[Depends(require_alerts_key)],
    summary="List subscriptions",
)
async def list_subscriptions(
    service: SubscriptionService = Depends(get_subscription_service),
):
    try:
        return await service.list()
    except RedisError:
        logger.exception("Redis failure while listing subscriptions")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE)


@router.get(
    "/subscriptions/{subscription_id}",
    response_model=Subscription,
    dependencies=[Depends(require_alerts_key)],
    summary="Get a subscription",
    responses={404: {"description": "No such subscription"}},
)
async def get_subscription(
    subscription_id: str,
    service: SubscriptionService = Depends(get_subscription_service),
):
    try:
        subscription = await service.get(subscription_id)
    except RedisError:
        logger.exception("Redis failure while reading a subscription")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE)

    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )
    return subscription


@router.delete(
    "/subscriptions/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_alerts_key)],
    summary="Delete a subscription",
    responses={404: {"description": "No such subscription"}},
)
async def delete_subscription(
    subscription_id: str,
    service: SubscriptionService = Depends(get_subscription_service),
):
    try:
        existed = await service.delete(subscription_id)
    except RedisError:
        logger.exception("Redis failure while deleting a subscription")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE)

    if not existed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription {subscription_id} not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
