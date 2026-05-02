from __future__ import annotations

from app.agents.supervisor import Supervisor
from app.llm import LLMClient
from app.schemas import SolveResponse


def solve_problem(
    problem: str,
    persona_count: int = 4,
    debate_rounds: int = 1,
    use_llm: bool = True,
    model: str | None = None,
    temperature: float = 0.35,
) -> SolveResponse:
    llm = LLMClient(model=model, temperature=temperature, enabled=use_llm)
    supervisor = Supervisor(llm)
    return supervisor.solve(
        problem=problem,
        persona_count=persona_count,
        debate_rounds=debate_rounds,
    )
