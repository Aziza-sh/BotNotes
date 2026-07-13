from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import notes, users, ai


@asynccontextmanager
async def lifespan(app: FastAPI):

    yield


app = FastAPI(
    title="BotNotes API",
    description="REST API для управления конспектами Telegram-бота",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(notes.router, prefix="/api/v1/notes", tags=["Конспекты"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Пользователи"])
app.include_router(ai.router, prefix="/api/v1/ai", tags=["AI"])


@app.get("/", summary="Проверка работоспособности")
async def root():
    return {
        "status": "ok",
        "service": "BotNotes API",
    }
