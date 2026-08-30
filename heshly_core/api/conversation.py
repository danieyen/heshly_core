from __future__ import annotations

# Alias for singular import path - n8n may call heshly_core.api.conversation.get_stale_conversations
# Re-export everything from conversations (plural) to prevent 417 "has no attribute"

from heshly_core.api.conversations import (
    ConversationAPI,
    get,
    get_stale,
    get_stale_conversations,
    health,
    list_stale,
    list_stale_conversations,
    set_status,
)

__all__ = [
    "ConversationAPI",
    "get",
    "get_stale",
    "get_stale_conversations",
    "health",
    "list_stale",
    "list_stale_conversations",
    "set_status",
]
