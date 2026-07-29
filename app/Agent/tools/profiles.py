"""LangChain tools for profile collection and persistence."""

from __future__ import annotations

from langchain.tools import ToolRuntime, tool

from app.schemas.profile import BodyProfilePatch
from app.services.profile_service import ProfileService


def build_profile_tools(service: ProfileService) -> list:
    def authenticated_user_id(runtime: ToolRuntime) -> int:
        return int(runtime.context["user_id"])

    @tool
    def get_body_profile(runtime: ToolRuntime) -> dict:
        """Get the authenticated user's saved body profile and profile version."""

        profile = service.get_profile(authenticated_user_id(runtime))
        return {"found": profile is not None, "profile": profile}

    @tool
    def validate_profile_patch(
        patch: BodyProfilePatch, runtime: ToolRuntime
    ) -> dict:
        """Validate and normalize only profile facts explicitly stated by the user.

        Call this before asking follow-up questions and before saving. Omitted fields
        are preserved from the current saved profile.
        """

        result = service.validate_patch(authenticated_user_id(runtime), patch)
        return result.model_dump(mode="json")

    @tool
    def save_body_profile(
        patch: BodyProfilePatch,
        runtime: ToolRuntime,
        expected_version: int | None = None,
    ) -> dict:
        """Save a validated profile patch after the user explicitly confirms it.

        Never call this tool before showing the normalized changes to the user and
        receiving an explicit confirmation.
        """

        saved = service.save_patch(
            authenticated_user_id(runtime),
            patch,
            expected_version=expected_version,
        )
        assessment = service.assess_profile(authenticated_user_id(runtime))
        return {
            "success": True,
            "profile": saved,
            "basic_assessment": assessment.model_dump(mode="json"),
        }

    @tool
    def assess_body_profile(runtime: ToolRuntime) -> dict:
        """Calculate deterministic basic metrics and profile safety status.

        This does not diagnose disease and does not assign a fitness-test level.
        """

        return service.assess_profile(authenticated_user_id(runtime)).model_dump(mode="json")

    return [
        get_body_profile,
        validate_profile_patch,
        save_body_profile,
        assess_body_profile,
    ]
