from fastapi import FastAPI
from api.src.database import create_db_and_tables
from api.src.auth import routers as AuthRouters


# Import from your other app files


app = FastAPI(
    title="Medi Reminder API",
    description="Async FastAPI backend for medication reminders",
    version="1.0.0"
)

#Startup event — runs once when the app launches
@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()
    print("Database tables created (if not existing).")


app.include_router(AuthRouters.router, prefix="/auth", tags=["Authentication"])