from fastapi import FastAPI

from api.routes import router
from database import init_db
from managers.app_manager import load_start_menu_apps


app = FastAPI(title="Jarvis AI")
init_db()
app.include_router(router)


@app.on_event("startup")
def startup_event():
    load_start_menu_apps()
    print("Application started")
