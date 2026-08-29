from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


class TaskCreate(BaseModel):
    prompt: str = Field(min_length=8, max_length=2_000)
    scenario: Literal["normal", "risk"] = "normal"


class ReviewDecision(BaseModel):
    action: Literal["approve", "reject", "retry"]
    comment: str = Field(default="", max_length=500)


class WorkflowNode(BaseModel):
    id: str
    name: str
    status: NodeStatus = NodeStatus.PENDING
    summary: str = "等待执行"
    attempts: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


class GoalSpec(BaseModel):
    objective: str
    metric: str = "30 天复购率"
    uplift_target: str = "相对提升 5%"
    audience: str = "高流失风险、高客单价用户"
    observation_window: str = "未来 30 天"
    constraints: list[str] = Field(default_factory=list)


class TaskEvent(BaseModel):
    sequence: int
    event: str
    task_id: str
    node: str | None = None
    status: str
    summary: str
    detail: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class TaskState(BaseModel):
    id: str
    prompt: str
    scenario: str
    status: TaskStatus = TaskStatus.DRAFT
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    goal: GoalSpec | None = None
    nodes: list[WorkflowNode]
    assets: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    events: list[TaskEvent] = Field(default_factory=list)
    review: dict[str, Any] | None = None

