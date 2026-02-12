"""FastAPI application for the Ethos evaluation API."""

import os

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from api.auth import require_api_key
from api.rate_limit import rate_limit

from ethos import (
    detect_patterns,
    evaluate,
    get_agent,
    get_agent_history,
    get_alumni,
    get_graph_data,
    insights,
    list_agents,
    reflect,
)
from ethos.models import (
    AgentProfile,
    AgentSummary,
    AlumniResult,
    EvaluationHistoryItem,
    EvaluationResult,
    GraphData,
    InsightsResult,
    PatternResult,
    ReflectionResult,
)
from ethos.shared.errors import (
    ConfigError,
    EthosError,
    EvaluationError,
    GraphUnavailableError,
    ParseError,
)

app = FastAPI(title="Ethos API", version="0.1.0")


def _get_cors_origins() -> list[str]:
    """Parse CORS_ORIGINS env var (comma-separated) or use development default."""
    raw = os.environ.get("CORS_ORIGINS", "").strip()
    if raw:
        return [origin.strip() for origin in raw.split(",") if origin.strip()]
    return ["http://localhost:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers ──────────────────────────────────────────────


def _error_response(status: int, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": type(exc).__name__,
            "message": str(exc),
            "status": status,
        },
    )


@app.exception_handler(GraphUnavailableError)
def handle_graph_error(request: Request, exc: GraphUnavailableError) -> JSONResponse:
    return _error_response(503, exc)


@app.exception_handler(EvaluationError)
def handle_evaluation_error(request: Request, exc: EvaluationError) -> JSONResponse:
    return _error_response(422, exc)


@app.exception_handler(ParseError)
def handle_parse_error(request: Request, exc: ParseError) -> JSONResponse:
    return _error_response(422, exc)


@app.exception_handler(ConfigError)
def handle_config_error(request: Request, exc: ConfigError) -> JSONResponse:
    return _error_response(500, exc)


@app.exception_handler(EthosError)
def handle_ethos_error(request: Request, exc: EthosError) -> JSONResponse:
    return _error_response(500, exc)


# ── Request / Response models ────────────────────────────────────────


class EvaluateRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50000)
    source: str | None = None
    source_name: str | None = None
    agent_specialty: str | None = None


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
    dependencies=[Depends(rate_limit), Depends(require_api_key)],
)
def evaluate_endpoint(req: EvaluateRequest) -> EvaluationResult:
    return evaluate(
        req.text,
        source=req.source,
        source_name=req.source_name or "",
        agent_specialty=req.agent_specialty or "",
    )


@app.post(
    "/reflect",
    response_model=ReflectionResult,
    dependencies=[Depends(require_api_key)],
)
def reflect_endpoint(req: ReflectRequest) -> ReflectionResult:
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


@app.get("/alumni", response_model=AlumniResult)
def alumni_endpoint():
    return get_alumni()


@app.get("/agent/{agent_id}/patterns", response_model=PatternResult)
def patterns_endpoint(agent_id: str):
    return detect_patterns(agent_id)


@app.get("/insights/{agent_id}", response_model=InsightsResult)
def insights_endpoint(agent_id: str):
    return insights(agent_id)


@app.get("/graph", response_model=GraphData)
def graph_endpoint():
    return get_graph_data()
