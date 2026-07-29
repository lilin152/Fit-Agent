"""Compatibility exports for the old Agent entry module.

Importing this module no longer creates a client or sends an API request.
"""

from app.Agent.profile_agent import AgentContext, create_profile_agent

__all__ = ["AgentContext", "create_profile_agent"]
