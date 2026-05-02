from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas import RunSummary, SolveRequest, SolveResponse
from app.storage import list_runs, load_run, save_run
from app.workflow import solve_problem


load_dotenv()

app = FastAPI(
    title="PersonaGraph API",
    description="Multi-agent persona debate and synthesis MVP.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "PersonaGraph"}


@app.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest) -> SolveResponse:
    response = solve_problem(
        problem=request.problem,
        persona_count=request.persona_count,
        debate_rounds=request.debate_rounds,
        use_llm=request.use_llm,
        model=request.model,
        temperature=request.temperature,
    )
    return save_run(response)


@app.get("/runs", response_model=list[RunSummary])
def runs() -> list[RunSummary]:
    return list_runs()


@app.get("/runs/{run_id}", response_model=SolveResponse)
def run_detail(run_id: str) -> SolveResponse:
    try:
        return load_run(run_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Run not found") from None
