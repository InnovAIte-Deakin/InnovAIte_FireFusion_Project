from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class MisinformationPostIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    author_name: str = ""
    platform: str = ""
    content: str
    share_count: int = Field(default=0, ge=0)
    ts: datetime | None = None
    post_url: str = ""


class MisinformationPostOut(BaseModel):
    model_config = ConfigDict(extra="allow")

    model_id: str
    domain: str
    id: str
    author_name: str | None = None
    platform: str | None = None
    content: str
    share_count: int | None = None
    ts: datetime | str | None = None
    post_url: str | None = None
    label_id: int
    label: str
    confidence: float
    probabilities: dict[str, float]
    risk_score: float
    severity: str
    checkpoint: str