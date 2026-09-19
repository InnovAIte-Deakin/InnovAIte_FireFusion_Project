import ipaddress
import re
from datetime import datetime
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator, model_validator

from ..models.geojson import Geometry
from .models import LEAST_SEVERE, MOST_SEVERE, Region, RegionAssessment

MAX_LABEL_LENGTH = 100
MAX_URL_LENGTH = 2048
MAX_EMAIL_LENGTH = 254
# A region this detailed is not a region a responder drew by hand, and each
# vertex is compared against every forecast polygon on every evaluation.
MAX_REGION_VERTICES = 500

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_AMBIGUOUS_LAST_LABEL = re.compile(r"^(?:0x[0-9a-f]+|[0-9]+)$")
_INTERNAL_SUFFIXES = (".localhost", ".local", ".internal", ".lan", ".home", ".corp")


def validate_webhook_url(url: str, *, allow_insecure: bool = False) -> str:
    """Reject webhook URLs the backend should never be made to call.

    A subscriber supplies this URL and, once delivery exists, the backend will
    send requests to it. Without checks that is a server-side request forgery
    hole: a caller could aim the backend at cloud metadata endpoints or
    internal services.

    Checked here: https only, no embedded credentials, and no private,
    loopback, link-local or otherwise non-public literal address or internal
    hostname. allow_insecure relaxes the scheme and address rules for local
    development only.

    This cannot catch a public hostname that resolves to a private address, so
    delivery must re-check the resolved address at send time.
    """
    if len(url) > MAX_URL_LENGTH:
        raise ValueError("webhook URL is too long")

    parts = urlsplit(url)

    if parts.scheme not in ("https", "http"):
        raise ValueError("webhook URL must use https")
    if parts.scheme == "http" and not allow_insecure:
        raise ValueError("webhook URL must use https")
    if not parts.hostname:
        raise ValueError("webhook URL must include a host")
    if parts.username is not None or parts.password is not None:
        raise ValueError("webhook URL must not contain credentials")

    if allow_insecure:
        return url

    host = parts.hostname.lower().rstrip(".")

    if host == "localhost" or host.endswith(_INTERNAL_SUFFIXES):
        raise ValueError("webhook URL must not point at an internal host")

    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None

    if address is not None:
        candidates = [address]
        if getattr(address, "ipv4_mapped", None) is not None:
            candidates.append(address.ipv4_mapped)
        for candidate in candidates:
            if (
                candidate.is_private
                or candidate.is_loopback
                or candidate.is_link_local
                or candidate.is_multicast
                or candidate.is_reserved
                or candidate.is_unspecified
            ):
                raise ValueError("webhook URL must not point at a non-public address")
        return url

    # Forms like http://2130706433 or http://0x7f000001 are accepted by many
    # resolvers as IP addresses but are not parsed as such above.
    if _AMBIGUOUS_LAST_LABEL.match(host.rsplit(".", 1)[-1]):
        raise ValueError("webhook URL host looks like an encoded IP address")

    return url


class SubscriptionCreate(BaseModel):
    """What a client sends to subscribe to a region."""

    label: str = Field(min_length=1, max_length=MAX_LABEL_LENGTH)
    threshold_risk_factor: int = Field(ge=MOST_SEVERE, le=LEAST_SEVERE)

    # The region: a bounding box [min_lon, min_lat, max_lon, max_lat], or a
    # GeoJSON polygon. Exactly one.
    bbox: tuple[float, float, float, float] | None = None
    geometry: Geometry | None = None

    # Where to send alerts. At least one. Delivery itself is a later phase.
    webhook_url: str | None = None
    email: str | None = None

    @field_validator("label")
    @classmethod
    def _label_is_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("label must not be blank")
        return value.strip()

    @field_validator("email")
    @classmethod
    def _email_looks_valid(cls, value: str | None) -> str | None:
        if value is not None and (
            len(value) > MAX_EMAIL_LENGTH or not _EMAIL.match(value)
        ):
            raise ValueError("email is not a valid address")
        return value

    @model_validator(mode="after")
    def _region_and_channel(self):
        if (self.bbox is None) == (self.geometry is None):
            raise ValueError("provide exactly one of bbox or geometry")
        if self.webhook_url is None and self.email is None:
            raise ValueError("provide at least one of webhook_url or email")
        return self

    def to_region(self) -> Region:
        if self.bbox is not None:
            region = Region.from_bbox(*self.bbox)
        else:
            region = Region(geometry=self.geometry)

        vertices = sum(len(ring) for ring in region.geometry.coordinates)
        if vertices > MAX_REGION_VERTICES:
            raise ValueError(
                f"region has {vertices} vertices; the limit is {MAX_REGION_VERTICES}"
            )
        return region


class Subscription(BaseModel):
    """A stored subscription."""

    id: str
    label: str
    region: Region
    threshold_risk_factor: int = Field(ge=MOST_SEVERE, le=LEAST_SEVERE)
    webhook_url: str | None = None
    email: str | None = None
    created_at: datetime

    # What the forecast showed over this region when the subscription was
    # created. It is the "previous" state for the first evaluation, so an
    # existing risk is not announced as if it were new. None when the forecast
    # could not be read, in which case the first evaluation may alert.
    baseline: RegionAssessment | None = None
