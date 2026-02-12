"""FastAPI application for the Ethos evaluation API."""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from api.auth import require_api_key
from api.rate_limit import rate_limit

from ethos import (
    detect_patterns,
    evaluate,
    get_agent,
    get_agent_history,
    get_cohort,
    get_graph_data,
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
    GraphData,
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
    source_name: str = ""
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


@app.post(
    "/evaluate",
    response_model=EvaluationResult,
    dependencies=[Depends(require_api_key), Depends(rate_limit)],
)
def evaluate_endpoint(req: EvaluateRequest):
    return evaluate(req.text, source=req.source, source_name=req.source_name)


@app.post(
    "/reflect",
    response_model=ReflectionResult,
    dependencies=[Depends(require_api_key)],
)
def reflect_endpoint(req: ReflectRequest):
    return reflect(req.agent_id, text=req.text)


@app.get("/agents", response_model=list[AgentSummary])
def agents_endpoint(q: str = ""):
    return list_agents(search=q)


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


@app.get("/graph", response_model=GraphData)
def graph_endpoint():
    return get_graph_data()
