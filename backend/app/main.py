from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controllers.hydrology_controller import router as hydrology_router

app = FastAPI(title="Watershed Analysis API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Only include watershed analysis endpoints
app.include_router(hydrology_router)


@app.get("/health")
def health():
    return {"status": "ok"}
