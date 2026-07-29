"""Terminal chat loop for the body-profile intake agent."""

from __future__ import annotations

from pprint import pformat
import sys
from typing import Any
from uuid import uuid4
import warnings

from langgraph.types import Command

from app.Agent.profile_agent import AgentContext, create_profile_agent
from app.config import load_settings
from app.repositories.profile_repository import ProfileRepository


def _messages_from_result(result: Any) -> list[Any]:
    value = getattr(result, "value", result)
    if isinstance(value, dict):
        return value.get("messages", [])
    return []


def _interrupts_from_result(result: Any) -> tuple[Any, ...]:
    interrupts = getattr(result, "interrupts", None)
    return tuple(interrupts or ())


def _print_latest_assistant_message(result: Any) -> None:
    messages = _messages_from_result(result)
    for message in reversed(messages):
        message_type = getattr(message, "type", None) or getattr(message, "role", None)
        content = getattr(message, "content", None)
        if isinstance(message, dict):
            message_type = message.get("type") or message.get("role")
            content = message.get("content")
        if message_type in {"ai", "assistant"} and content:
            print(f"\n助手：{content}\n")
            return


def _print_interrupt(interrupt: Any) -> None:
    value = getattr(interrupt, "value", interrupt)
    print("\n[需要人工确认的工具调用]")
    print(pformat(value, width=100, sort_dicts=False))


def _build_decisions(interrupt: Any) -> list[dict[str, str]]:
    _print_interrupt(interrupt)
    value = getattr(interrupt, "value", interrupt)
    action_requests = value.get("action_requests", []) if isinstance(value, dict) else []
    action_count = max(1, len(action_requests))
    decisions: list[dict[str, str]] = []

    for index in range(action_count):
        if action_count > 1:
            print(f"正在审批第 {index + 1}/{action_count} 个动作。")
        while True:
            decision = input("输入 approve 执行写入，或 reject 拒绝：").strip().lower()
            if decision == "approve":
                decisions.append({"type": "approve"})
                break
            if decision == "reject":
                message = input("拒绝原因，可直接回车：").strip()
                decisions.append(
                    {"type": "reject", "message": message or "用户拒绝保存资料"}
                )
                break
            print("只接受 approve 或 reject。")
    return decisions


def _invoke_agent(agent: Any, payload: Any, config: dict[str, Any], context: AgentContext) -> Any:
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=r"(?s)^Pydantic serializer warnings:.*field_name='context'.*$",
            category=UserWarning,
            module=r"pydantic\.(functional_validators|main)",
        )
        return agent.invoke(payload, config=config, context=context, version="v2")


def _run_until_complete(agent: Any, result: Any, config: dict[str, Any], context: AgentContext) -> Any:
    while True:
        interrupts = _interrupts_from_result(result)
        if not interrupts:
            return result
        decisions = [
            decision
            for interrupt in interrupts
            for decision in _build_decisions(interrupt)
        ]
        result = _invoke_agent(
            agent,
            Command(resume={"decisions": decisions}),
            config,
            context,
        )


def _select_user_id(repository: ProfileRepository) -> int:
    users = repository.list_users()
    if not users:
        raise RuntimeError("数据库中没有用户，请先运行种子数据或创建用户。")

    print("可用用户：")
    for user in users:
        name = user.get("username") or "未命名"
        print(f"  {user['user_id']}: {name} <{user.get('email')}> ")

    default = str(users[0]["user_id"])
    raw = input(f"请选择 user_id，直接回车默认 {default}：").strip() or default
    try:
        user_id = int(raw)
    except ValueError as exc:
        raise RuntimeError("user_id 必须是整数。") from exc
    if not repository.user_exists(user_id):
        raise RuntimeError(f"user_id={user_id} 不存在。")
    return user_id


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    settings = load_settings(require_api_key=True)
    repository = ProfileRepository(settings.database_path)
    repository.initialize()

    user_id = _select_user_id(repository)
    context: AgentContext = {"user_id": user_id}
    thread_id = input("thread_id，可直接回车自动生成：").strip() or f"profile-{user_id}-{uuid4()}"
    config = {"configurable": {"thread_id": thread_id}}
    agent = create_profile_agent(settings=settings, repository=repository)

    print("\n身体资料采集 Agent 已启动。输入 exit / quit 结束。\n")
    while True:
        user_text = input("用户：").strip()
        if user_text.lower() in {"exit", "quit", "q"}:
            print("已退出。")
            return
        if not user_text:
            continue

        result = _invoke_agent(
            agent,
            {"messages": [{"role": "user", "content": user_text}]},
            config,
            context,
        )
        result = _run_until_complete(agent, result, config, context)
        _print_latest_assistant_message(result)


if __name__ == "__main__":
    main()
