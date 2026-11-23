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

class TaskPrediction(BaseModel):
    """One task head's prediction: class, its confidence, and the full probability map."""

    model_config = ConfigDict(extra="forbid")

    label_id: int
    label: str
    confidence: float
    probabilities: dict[str, float]

class MisinformationTaskPredictions(BaseModel):
    """Predictions specifically only for the misinformation, urgency, and humanitarian tasks."""

    model_config = ConfigDict(extra="allow")

    misinfo: TaskPrediction
    urgency: TaskPrediction | None = None
    humanitarian: TaskPrediction | None = None

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
    tasks: MisinformationTaskPredictions
    checkpoint: str