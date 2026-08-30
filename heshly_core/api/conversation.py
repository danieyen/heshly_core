from __future__ import annotations

# Alias for singular import path - n8n may call heshly_core.api.conversation.get_stale_conversations
# Re-export everything from conversations (plural) to prevent 417 "has no attribute"

from heshly_core.api.conversations import (
    ConversationAPI,
    get,
    getStale,
    getStaleConversations,
    get_stale,
    get_stale_conversation,
    get_stale_conversations,
    health,
    listStale,
    list_stale,
    list_stale_conversations,
    set_status,
)

__all__ = [
    "ConversationAPI",
    "get",
    "get_stale",
    "get_stale_conversation",
    "get_stale_conversations",
    "getStale",
    "getStaleConversations",
    "health",
    "list_stale",
    "list_stale_conversations",
    "listStale",
    "set_status",
]


def __getattr__(name: str):
    # Fallback for any stale-related method name to prevent 417 "has no attribute"
    if "stale" in name.lower():
        return get_stale_conversations
    raise AttributeError(f"module 'heshly_core.api.conversation' has no attribute '{name}'")
