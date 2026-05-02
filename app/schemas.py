from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class Persona(BaseModel):
    id: str
    name: str
    role: str
    perspective: str
    priority_questions: list[str] = Field(default_factory=list)
    character: Optional["Character"] = None


class Character(BaseModel):
    id: str
    name: str
    archetype: str
    tagline: str
    visual: str
    speech_style: str
    motion: str = ""
    relationship: str = ""
    texture: str = ""
    color: str
    accent_color: str
    symbol: str


class AgentMessage(BaseModel):
    stage: Literal[
        "persona_generation",
        "moderator",
        "specialist",
        "debate",
        "critic",
        "synthesizer",
    ]
    agent_id: str
    agent_name: str
    role: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class SolveRequest(BaseModel):
    problem: str = Field(..., min_length=5)
    persona_count: int = Field(default=4, ge=3, le=5)
    debate_rounds: int = Field(default=1, ge=1, le=3)
    use_llm: bool = True
    model: Optional[str] = None
    temperature: float = Field(default=0.35, ge=0.0, le=1.2)


class Evaluation(BaseModel):
    consistency: int = Field(..., ge=1, le=5)
    specificity: int = Field(..., ge=1, le=5)
    risk_awareness: int = Field(..., ge=1, le=5)
    feasibility: int = Field(..., ge=1, le=5)
    overall_comment: str
    improvement_suggestions: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SolveResponse(BaseModel):
    run_id: Optional[str] = None
    problem: str
    personas: list[Persona]
    messages: list[AgentMessage]
    final_answer: str
    evaluation: Evaluation
    used_llm: bool
    model: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RunSummary(BaseModel):
    run_id: str
    problem_preview: str
    created_at: datetime
    used_llm: bool
    model: str
    average_score: float
