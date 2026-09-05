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
class MisinformationBatchIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    posts: list[MisinformationPostIn] = Field(min_length=1, max_length=100)


class TaskPrediction(BaseModel):
    model_config = ConfigDict(extra="allow")

    label: str
    probabilities: dict[str, float]


class MisinformationTaskOut(TaskPrediction):
    confidence: float
    risk_score: float
    severity: str


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
    misinformation: MisinformationTaskOut
    urgency: TaskPrediction | None = None
    humanitarian_task: TaskPrediction | None = None
    checkpoint: str
class MisinformationBatchOut(BaseModel):
    model_config = ConfigDict(extra="allow")
    results: list[MisinformationPostOut]
    count: int