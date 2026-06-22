from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rhimoz_api.routes import transcribe

app = FastAPI(title="Rhimoz API")

# Vite's dev server runs on a different port than uvicorn, so the browser
# treats requests as cross-origin even in local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transcribe.router)
