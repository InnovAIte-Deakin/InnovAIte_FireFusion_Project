import logging

from .subscriptions import Subscription

logger = logging.getLogger(__name__)

# Everything alerting stores in Redis lives under this prefix, so it can never
# collide with the forecast cache keys ("predictions", "predictions:generated_at").
KEY_PREFIX = "alerting:"
INDEX_KEY = f"{KEY_PREFIX}subscriptions"


def subscription_key(subscription_id: str) -> str:
    return f"{KEY_PREFIX}subscription:{subscription_id}"


class SubscriptionStore:
    """Subscriptions in Redis: one JSON value per subscription, plus an index set.

    The client is passed in rather than imported so the store can be tested
    without a Redis server. Redis failures are not caught here; they propagate
    so the router can report the service as unavailable.
    """

    def __init__(self, client):
        self.client = client

    async def add(self, subscription: Subscription, max_subscriptions: int) -> bool:
        """Store a subscription. Returns False, storing nothing, if that would
        exceed max_subscriptions.

        The write and the count happen in one MULTI/EXEC, and a write that lands
        over the limit is rolled back, so concurrent requests cannot push the
        total past the cap.
        """
        key = subscription_key(subscription.id)

        async with self.client.pipeline(transaction=True) as pipe:
            pipe.set(key, subscription.model_dump_json())
            pipe.sadd(INDEX_KEY, subscription.id)
            pipe.scard(INDEX_KEY)
            _, _, count = await pipe.execute()

        if count > max_subscriptions:
            await self.delete(subscription.id)
            return False
        return True

    async def get(self, subscription_id: str) -> Subscription | None:
        raw = await self.client.get(subscription_key(subscription_id))
        if raw is None:
            return None
        return self._parse(raw, subscription_id)

    async def delete(self, subscription_id: str) -> bool:
        """Remove a subscription. Returns whether it existed."""
        async with self.client.pipeline(transaction=True) as pipe:
            pipe.delete(subscription_key(subscription_id))
            pipe.srem(INDEX_KEY, subscription_id)
            deleted, _ = await pipe.execute()
        return bool(deleted)

    async def list(self) -> list[Subscription]:
        """All subscriptions, oldest first.

        An index entry whose value is gone is removed. A value that cannot be
        parsed is skipped and logged rather than failing the whole listing.
        """
        raw_ids = await self.client.smembers(INDEX_KEY)
        if not raw_ids:
            return []

        ids = sorted(self._text(i) for i in raw_ids)
        values = await self.client.mget([subscription_key(i) for i in ids])

        subscriptions = []
        for subscription_id, raw in zip(ids, values):
            if raw is None:
                await self.client.srem(INDEX_KEY, subscription_id)
                continue
            parsed = self._parse(raw, subscription_id)
            if parsed is not None:
                subscriptions.append(parsed)

        return sorted(subscriptions, key=lambda s: s.created_at)

    @staticmethod
    def _text(value) -> str:
        return value.decode() if isinstance(value, bytes) else value

    @staticmethod
    def _parse(raw, subscription_id: str) -> Subscription | None:
        try:
            return Subscription.model_validate_json(raw)
        except ValueError:
            logger.warning(
                "Stored subscription %s could not be parsed and was skipped",
                subscription_id,
            )
            return None
