"""LangChain profile intake agent assembly."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from app.Agent.deepseek_provider import create_deepseek_model
from app.Agent.tools.profiles import build_profile_tools
from app.config import Settings, load_settings
from app.repositories.profile_repository import ProfileRepository
from app.services.profile_service import ProfileService


class AgentContext(TypedDict):
    user_id: int


def _load_prompt(project_root: Path) -> str:
    prompt_path = project_root / "app" / "prompts" / "profile_intake_prompt.txt"
    return prompt_path.read_text(encoding="utf-8")


def create_profile_agent(
    settings: Settings | None = None,
    repository: ProfileRepository | None = None,
):
    settings = settings or load_settings()
    repository = repository or ProfileRepository(settings.database_path)
    repository.initialize()
    service = ProfileService(repository)

    return create_agent(
        model=create_deepseek_model(settings),
        tools=build_profile_tools(service),
        system_prompt=_load_prompt(settings.project_root),
        context_schema=AgentContext,
        checkpointer=InMemorySaver(),
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "save_body_profile": {
                        "allowed_decisions": ["approve", "reject"]
                    }
                },
                description_prefix="Profile database write pending approval",
            )
        ],
        name="profile_intake_agent",
    )
