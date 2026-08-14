from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import discovery, persona, site_gen, leads, brandboost, pitch, voice_agent

app = FastAPI(title="Texas Agent Persona & Site-Gen API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(discovery.router)
app.include_router(persona.router)
app.include_router(site_gen.router)
app.include_router(leads.router)
app.include_router(brandboost.router)
app.include_router(pitch.router)
app.include_router(voice_agent.router)


@app.get("/health")
def health():
    return {"status": "ok"}