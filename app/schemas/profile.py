"""Pydantic schemas shared by the profile agent, service, and tools."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Sex = Literal["male", "female", "unspecified"]
InjurySide = Literal["left", "right", "bilateral", "unknown"]
InjuryStatus = Literal["active", "recovering", "previous", "unknown"]


class ExerciseHistoryInput(BaseModel):
    """Facts about previous exercise, not an LLM-generated ability rating."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=1000)
    sessions_per_week: int | None = Field(default=None, ge=0, le=14)
    continuous_months: int | None = Field(default=None, ge=0, le=1200)
    inactivity_months: int | None = Field(default=None, ge=0, le=1200)


class InjuryInput(BaseModel):
    """A user-reported injury record. It is not a medical diagnosis."""

    model_config = ConfigDict(extra="forbid")

    body_part: str = Field(min_length=1, max_length=100)
    side: InjurySide = "unknown"
    status: InjuryStatus = "unknown"
    pain_score: int | None = Field(default=None, ge=0, le=10)
    trigger_movements: list[str] = Field(default_factory=list, max_length=30)
    doctor_restrictions: str | None = Field(default=None, max_length=1000)
    description: str | None = Field(default=None, max_length=2000)


class ImprovementAreaInput(BaseModel):
    """A body area the user wants to improve, separate from injuries."""

    model_config = ConfigDict(extra="forbid")

    body_part: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)


class BodyProfilePatch(BaseModel):
    """Fields explicitly stated by the user in this conversation."""

    model_config = ConfigDict(extra="forbid")

    sex: Sex | None = None
    age: int | None = Field(default=None, ge=12, le=100)
    height_cm: float | None = Field(default=None, ge=100, le=250)
    weight_kg: float | None = Field(default=None, ge=25, le=350)
    exercise_history: ExerciseHistoryInput | None = None
    goals: list[str] | None = Field(default=None, max_length=20)
    improvement_areas: list[ImprovementAreaInput] | None = None
    injuries: list[InjuryInput] | None = None
    description: str | None = Field(default=None, max_length=4000)


class ProfileValidationResult(BaseModel):
    ready_to_save: bool
    missing_fields: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    normalized_profile: dict[str, Any]


class SafetyAssessment(BaseModel):
    level: Literal["clear", "needs_attention", "assessment_blocked"]
    assessment_allowed: bool
    reason_codes: list[str] = Field(default_factory=list)
    messages: list[str] = Field(default_factory=list)


class BasicAssessment(BaseModel):
    bmi: float | None
    experience_level: Literal["beginner", "intermediate", "advanced", "unknown"]
    fitness_assessment_status: Literal["pending", "blocked"]
    fitness_level: None = None
    safety: SafetyAssessment
