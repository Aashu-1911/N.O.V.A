"""
Handlers package — convenience re-exports for all command handler functions.

Each sub-module contains handlers for a group of related intents.  All handlers
share the same calling convention::

    handler(entities: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ResponseDict

where ``ResponseDict`` is ``Dict[str, Any]`` with the keys:

- ``status`` — ``"success"``, ``"error"``, or ``"partial"``
- ``reply``  — human-readable response text
- ``payload`` — optional additional structured data
- ``intent``  — injected by :func:`core.command_executor.execute_command`

Handler modules
---------------
- :mod:`handlers.task_handler`    — add_task, show_tasks, complete_task, show_stats, update_task
- :mod:`handlers.browser_handler` — open_website, search_web
- :mod:`handlers.app_handler`     — open_application, close_application
- :mod:`handlers.system_handler`  — lock_pc, take_screenshot, volume_control
- :mod:`handlers.media_handler`   — play_music, media_control
- :mod:`handlers.chat_handler`    — general_chat (LLM fallback)
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
