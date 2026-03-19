from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routes import profiles, analysis

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Skill-Bridge Career Navigator",
    description="AI-powered career gap analysis and learning roadmap generator.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profiles.router)
app.include_router(analysis.router)


@app.get("/health")
def health():
    return {"status": "ok"}
