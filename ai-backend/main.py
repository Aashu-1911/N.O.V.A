from fastapi import FastAPI

from api.routes import router
from database import init_db
from managers.app_manager import load_start_menu_apps
from adapters.voice_adapter import voice_command_callback

app = FastAPI(title="Jarvis AI")
init_db()
app.include_router(router)


@app.on_event("startup")
def startup_event():
    load_start_menu_apps()
    print("Application started")


def setup_voice(voice_manager) -> None:
    """
    Register the voice adapter callback with a VoiceInputManager instance.

    Call this after creating the VoiceInputManager to wire up voice → command
    routing via the adapter pattern::

        from voice import VoiceInputManager
        from main import setup_voice

        vm = VoiceInputManager()
        setup_voice(vm)
        vm.start_listening()

    voice_adapter is the ONLY module that imports both voice and
    command_executor, keeping the two subsystems fully decoupled.
    """
    voice_manager.on_command(voice_command_callback)
