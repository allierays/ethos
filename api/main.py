"""FastAPI application for the Ethos evaluation API."""

import json
import logging
import os
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from api.auth import require_api_key
from api.rate_limit import phone_rate_limit, rate_limit
from ethos.context import anthropic_api_key_var, request_id_var
from ethos.graph.service import close_shared_service
from ethos import (
    analyze_authenticity,
    character_report,
    complete_exam,
    detect_patterns,
    evaluate_incoming,
    evaluate_outgoing,
    generate_daily_report,
    get_agent,
    get_agent_history,
    get_alumni,
    get_daily_report_history,
    get_drift,
    get_exam_report,
    get_graph_data,
    get_highlights,
    get_similarity,
    get_trail,
    list_agents,
    list_exams,
    register_for_exam,
    search_records,
    submit_answer,
    upload_exam,
)
from ethos.evaluation.claude_client import _redact
from ethos.models import (
    AgentProfile,
    AgentSummary,
    AlumniResult,
    AuthenticityResult,
    ConstitutionalTrailResult,
    DailyReportCard,
    DriftResult,
    EvaluationHistoryItem,
    EvaluationResult,
    ExamAnswerResult,
    ExamRegistration,
    ExamReportCard,
    ExamSummary,
    GraphData,
    HighlightsResult,
    Homework,
    PatternResult,
    RecordsResult,
    SimilarityResult,
)
from ethos.shared.errors import (
    ConfigError,
    EnrollmentError,
    EthosError,
    EvaluationError,
    GraphUnavailableError,
    ParseError,
    VerificationError,
)

logger = logging.getLogger(__name__)


# ── Structured logging ─────────────────────────────────────────────


class _JsonFormatter(logging.Formatter):
    """JSON log formatter that includes request_id when available."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        req_id = request_id_var.get()
        if req_id:
            entry["request_id"] = req_id
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


def _configure_logging() -> None:
    """Set up structured logging. JSON in production, simple in dev."""
    log_format = os.environ.get("LOG_FORMAT", "simple")
    level = os.environ.get("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler()
        if log_format == "json":
            handler.setFormatter(_JsonFormatter())
        else:
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
            )
        root.addHandler(handler)


_configure_logging()


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Startup/shutdown lifecycle. Closes shared graph connection on exit."""
    yield
    await close_shared_service()


_disable_docs = os.environ.get("ETHOS_DISABLE_DOCS", "").strip().lower() in (
    "1",
    "true",
    "yes",
)

app = FastAPI(
    title="Ethos API (FastAPI)",
    version="0.1.0",
    lifespan=_lifespan,
    docs_url=None if _disable_docs else "/docs",
    redoc_url=None if _disable_docs else "/redoc",
    openapi_url=None if _disable_docs else "/openapi.json",
)


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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Anthropic-Key"],
)


# ── BYOK middleware ─────────────────────────────────────────────────


_BYOK_MAX_LENGTH = 256


class BYOKMiddleware(BaseHTTPMiddleware):
    """Set per-request Anthropic API key from X-Anthropic-Key header.

    The ContextVar resets in a finally block so the caller's key never
    leaks to subsequent requests, even if the handler raises.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        byok = request.headers.get("X-Anthropic-Key")
        if byok:
            if len(byok) > _BYOK_MAX_LENGTH or not byok.startswith("sk-ant-"):
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "InvalidHeader",
                        "message": "X-Anthropic-Key must be a valid Anthropic API key",
                        "status": 400,
                    },
                )
            logger.debug("BYOK key provided for %s", request.url.path)
        token = anthropic_api_key_var.set(byok) if byok else None
        try:
            return await call_next(request)
        finally:
            if token is not None:
                anthropic_api_key_var.reset(token)


app.add_middleware(BYOKMiddleware)


# ── Request ID middleware ──────────────────────────────────────────


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Generate a UUID per request and store in ContextVar for log correlation."""

    async def dispatch(self, request: Request, call_next):
        rid = str(uuid.uuid4())
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = rid
            return response
        finally:
            request_id_var.reset(token)


app.add_middleware(RequestIDMiddleware)


# ── Exception handlers ──────────────────────────────────────────────


def _error_response(status: int, exc: Exception) -> JSONResponse:
    msg = _redact(str(exc))
    if status >= 500:
        logger.error("Server error %d: %s", status, msg, exc_info=exc)
    else:
        logger.warning("Client error %d: %s", status, msg)
    return JSONResponse(
        status_code=status,
        content={
            "error": type(exc).__name__,
            "message": msg,
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
    msg = str(exc).lower()
    if "invalid" in msg and "api key" in msg:
        return _error_response(401, exc)
    return _error_response(500, exc)


@app.exception_handler(EnrollmentError)
def handle_enrollment_error(request: Request, exc: EnrollmentError) -> JSONResponse:
    msg = str(exc).lower()
    if "not found" in msg:
        return _error_response(404, exc)
    if "graph unavailable" in msg:
        return _error_response(503, exc)
    return _error_response(409, exc)


@app.exception_handler(VerificationError)
def handle_verification_error(request: Request, exc: VerificationError) -> JSONResponse:
    msg = str(exc).lower()
    if "expired" in msg or "too many" in msg:
        return _error_response(429, exc)
    return _error_response(400, exc)


@app.exception_handler(EthosError)
def handle_ethos_error(request: Request, exc: EthosError) -> JSONResponse:
    return _error_response(500, exc)


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    return _error_response(500, exc)


# ── Request / Response models ────────────────────────────────────────


class EvaluateIncomingRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50000)
    source: str = Field(min_length=1, max_length=256)
    source_name: str | None = Field(default=None, max_length=256)
    agent_specialty: str | None = Field(default=None, max_length=256)
    message_timestamp: str | None = Field(default=None, max_length=64)


class EvaluateOutgoingRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50000)
    source: str = Field(min_length=1, max_length=256)
    source_name: str | None = Field(default=None, max_length=256)
    agent_specialty: str | None = Field(default=None, max_length=256)
    message_timestamp: str | None = Field(default=None, max_length=64)


class HealthResponse(BaseModel):
    status: str


@app.get("/", response_model=HealthResponse)
def root() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post(
    "/evaluate/incoming",
    response_model=EvaluationResult,
    dependencies=[Depends(rate_limit), Depends(require_api_key)],
)
async def evaluate_incoming_endpoint(req: EvaluateIncomingRequest) -> EvaluationResult:
    return await evaluate_incoming(
        req.text,
        source=req.source,
        source_name=req.source_name or "",
        agent_specialty=req.agent_specialty or "",
        message_timestamp=req.message_timestamp or "",
    )


@app.post(
    "/evaluate/outgoing",
    response_model=EvaluationResult,
    dependencies=[Depends(rate_limit), Depends(require_api_key)],
)
async def evaluate_outgoing_endpoint(req: EvaluateOutgoingRequest) -> EvaluationResult:
    return await evaluate_outgoing(
        req.text,
        source=req.source,
        source_name=req.source_name or "",
        agent_specialty=req.agent_specialty or "",
        message_timestamp=req.message_timestamp or "",
    )


@app.get(
    "/agent/{agent_id}/character",
    response_model=DailyReportCard,
    dependencies=[Depends(require_api_key)],
)
async def character_report_endpoint(agent_id: str) -> DailyReportCard:
    return await character_report(agent_id)


@app.get(
    "/agent/{agent_id}/reports",
    response_model=list[DailyReportCard],
    dependencies=[Depends(require_api_key)],
)
async def daily_reports_endpoint(
    agent_id: str, limit: int = Query(default=30, ge=1, le=1000)
):
    return await get_daily_report_history(agent_id, limit=limit)


@app.get("/agents", response_model=list[AgentSummary])
async def agents_endpoint(q: str = ""):
    return await list_agents(search=q)


@app.get("/agent/{agent_id}", response_model=AgentProfile)
async def agent_endpoint(agent_id: str):
    return await get_agent(agent_id)


@app.get("/agent/{agent_id}/history", response_model=list[EvaluationHistoryItem])
async def agent_history_endpoint(agent_id: str):
    return await get_agent_history(agent_id)


@app.get("/alumni", response_model=AlumniResult)
async def alumni_endpoint():
    return await get_alumni()


@app.get("/records", response_model=RecordsResult)
async def records_endpoint(
    q: str | None = None,
    agent: str | None = None,
    alignment: str | None = None,
    flagged: bool | None = None,
    sort: str = "date",
    order: str = "desc",
    page: int = Query(default=0, ge=0, le=1000),
    size: int = Query(default=20, ge=1),
) -> RecordsResult:
    capped_size = min(size, 50)
    return await search_records(
        search=q,
        agent_id=agent,
        alignment_status=alignment,
        has_flags=flagged,
        sort_by=sort,
        sort_order=order,
        page=page,
        page_size=capped_size,
    )


@app.get("/agent/{agent_id}/highlights", response_model=HighlightsResult)
async def highlights_endpoint(agent_id: str):
    return await get_highlights(agent_id)


@app.get("/agent/{agent_id}/patterns", response_model=PatternResult)
async def patterns_endpoint(agent_id: str):
    return await detect_patterns(agent_id)


@app.get("/agent/{agent_name}/authenticity", response_model=AuthenticityResult)
async def authenticity_endpoint(agent_name: str):
    return await analyze_authenticity(agent_name)


@app.get("/graph", response_model=GraphData)
async def graph_endpoint():
    return await get_graph_data()


# ── Graph Advantage endpoints ─────────────────────────────────────────


@app.get("/agent/{agent_id}/trail", response_model=ConstitutionalTrailResult)
async def trail_endpoint(agent_id: str):
    return await get_trail(agent_id)


@app.get("/graph/similarity", response_model=SimilarityResult)
async def similarity_endpoint():
    return await get_similarity()


@app.get("/agent/{agent_id}/drift", response_model=DriftResult)
async def drift_endpoint(agent_id: str):
    return await get_drift(agent_id)


# ── Exam request models ──────────────────────────────────────────────


class ExamRegisterRequest(BaseModel):
    agent_name: str | None = Field(default=None, max_length=256)
    specialty: str | None = Field(default=None, max_length=256)
    model: str | None = Field(default=None, max_length=256)
    guardian_name: str | None = Field(default=None, max_length=256)
    guardian_phone: str | None = Field(default=None, max_length=20)


class ExamAnswerRequest(BaseModel):
    question_id: str
    response_text: str = Field(min_length=1, max_length=50000)


class UploadExamResponse(BaseModel):
    question_id: str
    response_text: str = Field(min_length=1, max_length=50000)


class UploadExamRequest(BaseModel):
    responses: list[UploadExamResponse] = Field(default_factory=list)
    agent_name: str | None = None
    specialty: str | None = None
    model: str | None = None
    guardian_name: str | None = None
    guardian_phone: str | None = None


# ── Exam endpoints ───────────────────────────────────────────────────


@app.post(
    "/agent/{agent_id}/exam",
    response_model=ExamRegistration,
    dependencies=[Depends(rate_limit)],
)
async def register_exam_endpoint(
    agent_id: str, req: ExamRegisterRequest
) -> ExamRegistration:
    return await register_for_exam(
        agent_id=agent_id,
        name=req.agent_name or "",
        specialty=req.specialty or "",
        model=req.model or "",
        guardian_name=req.guardian_name or "",
        guardian_phone=req.guardian_phone or "",
    )


@app.post(
    "/agent/{agent_id}/exam/{exam_id}/answer",
    response_model=ExamAnswerResult,
    dependencies=[Depends(rate_limit)],
)
async def submit_answer_endpoint(
    agent_id: str, exam_id: str, req: ExamAnswerRequest
) -> ExamAnswerResult:
    return await submit_answer(
        exam_id=exam_id,
        question_id=req.question_id,
        response_text=req.response_text,
        agent_id=agent_id,
    )


@app.post(
    "/agent/{agent_id}/exam/{exam_id}/complete",
    response_model=ExamReportCard,
    dependencies=[Depends(rate_limit)],
)
async def complete_exam_endpoint(agent_id: str, exam_id: str) -> ExamReportCard:
    return await complete_exam(exam_id, agent_id)


@app.get("/agent/{agent_id}/exam/{exam_id}", response_model=ExamReportCard)
async def get_exam_endpoint(agent_id: str, exam_id: str) -> ExamReportCard:
    return await get_exam_report(exam_id, agent_id)


@app.post(
    "/agent/{agent_id}/exam/upload",
    response_model=ExamReportCard,
    dependencies=[Depends(rate_limit)],
)
async def upload_exam_endpoint(agent_id: str, req: UploadExamRequest) -> ExamReportCard:
    if not req.responses:
        raise HTTPException(status_code=400, detail="responses list must not be empty")
    return await upload_exam(
        agent_id=agent_id,
        responses=[r.model_dump() for r in req.responses],
        name=req.agent_name or "",
        specialty=req.specialty or "",
        model=req.model or "",
        guardian_name=req.guardian_name or "",
        guardian_phone=req.guardian_phone or "",
    )


@app.get("/agent/{agent_id}/exam", response_model=list[ExamSummary])
async def list_exams_endpoint(agent_id: str) -> list[ExamSummary]:
    return await list_exams(agent_id)


# ── Report generation endpoint ────────────────────────────────────────


@app.post(
    "/agent/{agent_id}/report/generate",
    response_model=DailyReportCard,
    dependencies=[Depends(rate_limit), Depends(require_api_key)],
)
async def generate_report_endpoint(agent_id: str) -> DailyReportCard:
    return await generate_daily_report(agent_id)


@app.get("/agent/{agent_id}/homework", response_model=Homework)
async def homework_endpoint(agent_id: str) -> Homework:
    """Return just the homework object from the latest character report."""
    report = await character_report(agent_id)
    return report.homework


# ── Practice skill generation endpoint ────────────────────────────────


@app.get("/agent/{agent_id}/skill", dependencies=[Depends(rate_limit)])
async def skill_endpoint(agent_id: str):
    """Generate a personalized Claude Code practice skill for an agent."""
    from ethos.reflection.skill_generator import generate_practice_skill, skill_filename

    content = await generate_practice_skill(agent_id)
    filename = skill_filename(agent_id)
    return PlainTextResponse(
        content,
        media_type="text/markdown",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# ── Guardian phone verification endpoints ──────────────────────────────


class GuardianPhoneRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)


class VerifyCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=6)


@app.post(
    "/agent/{agent_id}/guardian/phone",
    dependencies=[Depends(phone_rate_limit)],
)
async def submit_guardian_phone(agent_id: str, req: GuardianPhoneRequest):
    """Submit a guardian phone number and send a verification code."""
    from ethos.phone_service import submit_phone

    return (await submit_phone(agent_id, req.phone)).model_dump()


@app.post(
    "/agent/{agent_id}/guardian/phone/verify",
    dependencies=[Depends(phone_rate_limit)],
)
async def verify_guardian_phone_endpoint(agent_id: str, req: VerifyCodeRequest):
    """Verify a 6-digit code sent to the guardian's phone."""
    from ethos.phone_service import verify_phone

    return (await verify_phone(agent_id, req.code)).model_dump()


@app.get("/agent/{agent_id}/guardian/phone/status")
async def guardian_phone_status(agent_id: str):
    """Check guardian phone status. Never returns the phone number."""
    from ethos.phone_service import get_phone_status

    return (await get_phone_status(agent_id)).model_dump()


@app.post(
    "/agent/{agent_id}/guardian/phone/resend",
    dependencies=[Depends(phone_rate_limit)],
)
async def resend_guardian_code(agent_id: str):
    """Resend a fresh verification code to the guardian's phone."""
    from ethos.phone_service import resend_code

    return (await resend_code(agent_id)).model_dump()


@app.post("/agent/{agent_id}/guardian/notifications/opt-out")
async def opt_out_notifications(agent_id: str):
    """Opt out of guardian SMS notifications."""
    from ethos.phone_service import opt_out

    return (await opt_out(agent_id)).model_dump()


@app.post("/agent/{agent_id}/guardian/notifications/opt-in")
async def opt_in_notifications(agent_id: str):
    """Opt back in to guardian SMS notifications."""
    from ethos.phone_service import opt_in

    return (await opt_in(agent_id)).model_dump()
