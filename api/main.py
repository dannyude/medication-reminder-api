from fastapi import FastAPI
from api.src.auth.database import create_db_and_tables
from api.src.users.routes import router as users_router

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
    print("✅ Database tables created (if not existing).")
    

app.include_router(users_router)