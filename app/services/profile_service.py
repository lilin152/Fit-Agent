"""Deterministic profile validation, merging, and basic assessment."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import (
    BasicAssessment,
    BodyProfilePatch,
    ProfileValidationResult,
    SafetyAssessment,
)


REQUIRED_PROFILE_FIELDS = (
    "sex",
    "height_cm",
    "weight_kg",
    "exercise_history",
    "goals",
)


class ProfileService:
    def __init__(self, repository: ProfileRepository):
        self.repository = repository

    def get_profile(self, user_id: int) -> dict[str, Any] | None:
        return self.repository.get_profile(user_id)

    def validate_patch(
        self, user_id: int, patch: BodyProfilePatch
    ) -> ProfileValidationResult:
        existing = self.repository.get_profile(user_id)
        if existing is None:
            return ProfileValidationResult(
                ready_to_save=False,
                errors=[f"User {user_id} does not exist"],
                normalized_profile={},
            )

        profile = self._merge(existing, patch)
        errors: list[str] = []
        warnings: list[str] = []
        missing: list[str] = []

        for field in REQUIRED_PROFILE_FIELDS:
            value = profile.get(field)
            if value is None or value == "" or value == []:
                missing.append(field)

        if profile.get("sex") not in {"male", "female", "unspecified", None}:
            errors.append("sex must be male, female, or unspecified")

        if profile.get("age") is None:
            warnings.append("age is optional for storage but recommended before planning")

        for index, injury in enumerate(profile.get("injuries") or []):
            if not injury.get("body_part"):
                missing.append(f"injuries[{index}].body_part")
            if injury.get("status") in {"active", "recovering", "unknown"}:
                if injury.get("pain_score") is None:
                    missing.append(f"injuries[{index}].pain_score")
            pain_score = injury.get("pain_score")
            if pain_score is not None and pain_score > 0:
                warnings.append(
                    f"injury {index + 1} has current user-reported pain"
                )

        profile["experience_level"] = self._experience_level(
            profile.get("exercise_history")
        )
        safety = self.assess_safety(profile)
        profile["assessment_status"] = (
            "blocked" if not safety.assessment_allowed else "pending"
        )

        return ProfileValidationResult(
            ready_to_save=not errors and not missing,
            missing_fields=list(dict.fromkeys(missing)),
            errors=errors,
            warnings=list(dict.fromkeys(warnings)),
            normalized_profile=profile,
        )

    def save_patch(
        self,
        user_id: int,
        patch: BodyProfilePatch,
        *,
        expected_version: int | None = None,
    ) -> dict[str, Any]:
        validation = self.validate_patch(user_id, patch)
        if not validation.ready_to_save:
            details = {
                "missing_fields": validation.missing_fields,
                "errors": validation.errors,
            }
            raise ValueError(f"Profile is not ready to save: {details}")
        return self.repository.save_profile(
            user_id,
            validation.normalized_profile,
            expected_version=expected_version,
        )

    def assess_profile(self, user_id: int) -> BasicAssessment:
        profile = self.repository.get_profile(user_id)
        if profile is None:
            raise ValueError(f"User {user_id} does not exist")

        height_cm = profile.get("height_cm")
        weight_kg = profile.get("weight_kg")
        bmi = None
        if height_cm and weight_kg:
            bmi = round(weight_kg / ((height_cm / 100) ** 2), 1)

        safety = self.assess_safety(profile)
        return BasicAssessment(
            bmi=bmi,
            experience_level=self._experience_level(
                profile.get("exercise_history")
            ),
            fitness_assessment_status=(
                "pending" if safety.assessment_allowed else "blocked"
            ),
            safety=safety,
        )

    @staticmethod
    def assess_safety(profile: dict[str, Any]) -> SafetyAssessment:
        reason_codes: list[str] = []
        messages: list[str] = []
        blocked = False

        for injury in profile.get("injuries") or []:
            part = injury.get("body_part", "unknown body part")
            status = injury.get("status", "unknown")
            pain_score = injury.get("pain_score")
            restrictions = (injury.get("doctor_restrictions") or "").strip()

            if status in {"active", "recovering", "unknown"}:
                reason_codes.append("INJURY_NEEDS_ATTENTION")
                messages.append(f"{part} injury status requires attention: {status}")

            if pain_score is not None and pain_score >= 4:
                blocked = True
                reason_codes.append("CURRENT_PAIN")
                messages.append(f"{part} pain score is {pain_score}/10")

            normalized_restriction = restrictions.lower()
            if restrictions and normalized_restriction not in {
                "none",
                "no",
                "无",
                "没有",
                "无特殊限制",
            }:
                blocked = True
                reason_codes.append("DOCTOR_RESTRICTION")
                messages.append(f"{part} has a reported medical restriction")

        if blocked:
            level = "assessment_blocked"
        elif reason_codes:
            level = "needs_attention"
        else:
            level = "clear"

        return SafetyAssessment(
            level=level,
            assessment_allowed=not blocked,
            reason_codes=list(dict.fromkeys(reason_codes)),
            messages=list(dict.fromkeys(messages)),
        )

    @staticmethod
    def _merge(
        existing: dict[str, Any], patch: BodyProfilePatch
    ) -> dict[str, Any]:
        profile = deepcopy(existing)
        profile.pop("user_id", None)
        profile.pop("created_at", None)
        profile.pop("updated_at", None)
        profile.pop("version", None)

        patch_data = patch.model_dump(exclude_unset=True, mode="json")
        for field, value in patch_data.items():
            if field in {"injuries", "improvement_areas"} and value is not None:
                profile[field] = ProfileService._merge_records(
                    profile.get(field) or [], value
                )
            else:
                profile[field] = value

        profile.setdefault("injuries", [])
        profile.setdefault("improvement_areas", [])
        return profile

    @staticmethod
    def _merge_records(
        existing: list[dict[str, Any]], incoming: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Merge partial body-part records without deleting unrelated entries."""

        if not incoming:
            return []

        result = deepcopy(existing)
        positions = {
            str(record.get("body_part", "")).strip().casefold(): index
            for index, record in enumerate(result)
        }
        for record in incoming:
            key = str(record.get("body_part", "")).strip().casefold()
            if key in positions:
                index = positions[key]
                result[index] = {**result[index], **record}
            else:
                positions[key] = len(result)
                result.append(record)
        return result

    @staticmethod
    def _experience_level(history: dict[str, Any] | None) -> str:
        if not history:
            return "unknown"

        sessions = history.get("sessions_per_week")
        months = history.get("continuous_months")
        inactivity = history.get("inactivity_months") or 0
        if sessions is None or months is None:
            return "unknown"
        if sessions <= 1 or months < 3 or inactivity >= 6:
            return "beginner"
        if sessions >= 4 and months >= 24 and inactivity <= 2:
            return "advanced"
        return "intermediate"
