"""FastAPI application for the Ethos evaluation API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ethos import (
    detect_patterns,
    evaluate,
    get_agent,
    get_agent_history,
    get_cohort,
    insights,
    list_agents,
    reflect,
)
from ethos.models import (
    AgentProfile,
    AgentSummary,
    CohortResult,
    EvaluationHistoryItem,
    EvaluationResult,
    InsightsResult,
    PatternResult,
    ReflectionResult,
)

app = FastAPI(title="Ethos API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaluateRequest(BaseModel):
    text: str
    source: str | None = None
    agent_model: str | None = None


class ReflectRequest(BaseModel):
    agent_id: str
    text: str | None = None


class HealthResponse(BaseModel):
    status: str


@app.get("/", response_model=HealthResponse)
def root() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/evaluate", response_model=EvaluationResult)
def evaluate_endpoint(req: EvaluateRequest):
    return evaluate(req.text, source=req.source)


@app.post("/reflect", response_model=ReflectionResult)
def reflect_endpoint(req: ReflectRequest):
    return reflect(req.agent_id, text=req.text)


@app.get("/agents", response_model=list[AgentSummary])
def agents_endpoint():
    return list_agents()


@app.get("/agent/{agent_id}", response_model=AgentProfile)
def agent_endpoint(agent_id: str):
    return get_agent(agent_id)


@app.get("/agent/{agent_id}/history", response_model=list[EvaluationHistoryItem])
def agent_history_endpoint(agent_id: str):
    return get_agent_history(agent_id)


@app.get("/cohort", response_model=CohortResult)
def cohort_endpoint():
    return get_cohort()


@app.get("/agent/{agent_id}/patterns", response_model=PatternResult)
def patterns_endpoint(agent_id: str):
    return detect_patterns(agent_id)


@app.get("/insights/{agent_id}", response_model=InsightsResult)
def insights_endpoint(agent_id: str):
    return insights(agent_id)
