import logging
import uuid
from datetime import datetime, timezone

from ..models.geojson import FeatureCollection
from .assessment import assess_region
from .models import Region, RegionAssessment
from .store import SubscriptionStore
from .subscriptions import Subscription, SubscriptionCreate, validate_webhook_url

logger = logging.getLogger(__name__)


class SubscriptionLimitReached(Exception):
    """Raised when creating a subscription would exceed the configured cap."""


class SubscriptionService:

    def __init__(
        self,
        store: SubscriptionStore,
        forecast_service,
        *,
        max_subscriptions: int,
        allow_insecure_webhooks: bool = False,
    ):
        self.store = store
        self.forecast_service = forecast_service
        self.max_subscriptions = max_subscriptions
        self.allow_insecure_webhooks = allow_insecure_webhooks

    async def create(self, request: SubscriptionCreate) -> Subscription:
        """Validate, baseline against the current forecast, and store.

        Raises ValueError for a request that is well-formed but not acceptable
        (an unsafe webhook URL, an oversized region), and
        SubscriptionLimitReached at the cap.
        """
        if request.webhook_url is not None:
            validate_webhook_url(
                request.webhook_url,
                allow_insecure=self.allow_insecure_webhooks,
            )

        region = request.to_region()

        subscription = Subscription(
            id=uuid.uuid4().hex,
            label=request.label,
            region=region,
            threshold_risk_factor=request.threshold_risk_factor,
            webhook_url=request.webhook_url,
            email=request.email,
            created_at=datetime.now(timezone.utc),
            baseline=await self._baseline(region),
        )

        if not await self.store.add(subscription, self.max_subscriptions):
            raise SubscriptionLimitReached(
                f"the limit of {self.max_subscriptions} subscriptions is reached"
            )
        return subscription

    async def list(self) -> list[Subscription]:
        return await self.store.list()

    async def get(self, subscription_id: str) -> Subscription | None:
        return await self.store.get(subscription_id)

    async def delete(self, subscription_id: str) -> bool:
        return await self.store.delete(subscription_id)

    async def _baseline(self, region: Region) -> RegionAssessment | None:
        """What the current forecast shows over the region, or None if unknown.

        Best-effort: an unreadable forecast must not stop someone subscribing.
        With no baseline the first evaluation is free to alert, which errs in
        the safe direction for an emergency tool.
        """
        try:
            forecast = await self.forecast_service.fetch_predictions()
            features = FeatureCollection.model_validate(forecast).features
        except Exception:
            logger.warning(
                "Could not read the current forecast to baseline a new "
                "subscription; it will have no baseline",
                exc_info=True,
            )
            return None

        return assess_region(features, region)
