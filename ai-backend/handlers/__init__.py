"""
Handlers package - exports all command handler functions.
"""

from handlers.task_handler import (
    handle_add_task,
    handle_show_tasks,
    handle_complete_task,
    handle_show_stats,
    handle_update_task,
)
from handlers.browser_handler import (
    handle_open_website,
    handle_search_web,
)
from handlers.app_handler import (
    handle_open_application,
    handle_close_application,
)
from handlers.system_handler import (
    handle_lock_pc,
    handle_screenshot,
    handle_volume_control,
)
from handlers.media_handler import (
    handle_play_music,
    handle_media_control,
)
from handlers.chat_handler import handle_general_chat

__all__ = [
    "handle_add_task",
    "handle_show_tasks",
    "handle_complete_task",
    "handle_show_stats",
    "handle_update_task",
    "handle_open_website",
    "handle_search_web",
    "handle_open_application",
    "handle_close_application",
    "handle_lock_pc",
    "handle_screenshot",
    "handle_volume_control",
    "handle_play_music",
    "handle_media_control",
    "handle_general_chat",
]
