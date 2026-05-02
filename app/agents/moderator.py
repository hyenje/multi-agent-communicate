from __future__ import annotations

from app.llm import LLMClient
from app.schemas import AgentMessage, Persona


class ModeratorAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def open(self, problem: str, personas: list[Persona]) -> AgentMessage:
        panel = self._persona_panel(personas)
        prompt = f"""
문제:
{problem}

참여 에이전트:
{panel}

사회자로서 토론을 시작하세요.
반드시 자연스러운 한국어로 작성하고, 고유명사나 기술 약어 외에는 영어를 최소화하세요.
다음 내용을 포함하세요.
1. 오늘 다룰 핵심 쟁점
2. 각 에이전트가 어떤 순서와 태도로 말하면 좋은지
3. 이후 라운드에서는 앞선 발언에 직접 반응해야 한다는 규칙

짧고 대화 진행자처럼 작성하세요.
"""
        result = self.llm.complete(
            system_prompt="당신은 한국어 다중 에이전트 토론을 진행하는 사회자입니다. 토론을 생생하고 질서 있게 이끄세요.",
            user_prompt=prompt,
            temperature=0.25,
        )
        content = result.content if result.used_llm and result.content else self._open_fallback(problem, personas)
        return self._message(
            role="토론의 의제와 발언 규칙을 정하는 진행자",
            content=content,
            result_source="llm" if result.used_llm and result.content else "fallback",
            error=result.error,
            metadata={"phase": "opening"},
        )

    def guide(
        self,
        problem: str,
        personas: list[Persona],
        transcript: str,
        round_number: int,
    ) -> AgentMessage:
        panel = self._persona_panel(personas)
        prompt = f"""
문제:
{problem}

참여 에이전트:
{panel}

지금까지의 토론:
{transcript}

사회자로서 {round_number}번째 상호 응답 라운드를 여세요.
다음 에이전트들이 앞선 발언 중 하나에 직접 동의, 반박, 보완하도록 질문을 던지세요.
반드시 자연스러운 한국어로 작성하고, 고유명사나 기술 약어 외에는 영어를 최소화하세요.
요구사항:
- 새 주제를 늘리기보다 충돌과 빈틈을 좁히게 하세요.
- "누구의 어떤 주장에 반응할지"가 드러나게 하세요.
- 3~5문장으로 작성하세요.
"""
        result = self.llm.complete(
            system_prompt="당신은 한국어 다중 에이전트 토론의 사회자입니다. 발언 사이의 연결을 만들고 논점을 좁히세요.",
            user_prompt=prompt,
            temperature=0.25,
        )
        content = (
            result.content
            if result.used_llm and result.content
            else self._guide_fallback(personas, round_number)
        )
        return self._message(
            role="상호 응답 라운드의 논점을 좁히는 진행자",
            content=content,
            result_source="llm" if result.used_llm and result.content else "fallback",
            error=result.error,
            metadata={"phase": "response_round", "round": round_number},
        )

    def _message(
        self,
        role: str,
        content: str,
        result_source: str,
        error: str | None,
        metadata: dict[str, object],
    ) -> AgentMessage:
        return AgentMessage(
            stage="moderator",
            agent_id="moderator",
            agent_name="사회자 에이전트",
            role=role,
            content=content,
            metadata={"source": result_source, "error": error, **metadata},
        )

    def _persona_panel(self, personas: list[Persona]) -> str:
        return "\n".join(
            f"- {persona.name}: {persona.role} / 관점: {persona.perspective}"
            for persona in personas
        )

    def _open_fallback(self, problem: str, personas: list[Persona]) -> str:
        names = ", ".join(persona.name for persona in personas)
        return f"""토론을 시작하겠습니다. 오늘의 문제는 "{problem}"입니다.
참여자는 {names}이며, 각자 자기 관점에서 먼저 핵심 판단을 말합니다.
이후 라운드에서는 새 의견만 던지지 말고, 앞선 발언 중 하나를 짚어 동의, 반박, 보완 중 하나로 이어가겠습니다.
마지막에는 비판 에이전트가 빈틈을 잡고, 종합 에이전트가 실행 가능한 결론으로 묶겠습니다."""

    def _guide_fallback(self, personas: list[Persona], round_number: int) -> str:
        names = ", ".join(persona.name for persona in personas)
        return f"""{round_number}번째 상호 응답 라운드입니다.
{names}는 직전 발언 또는 가장 강한 주장 하나를 골라 직접 받아주세요.
이번 라운드의 목표는 아이디어를 더 늘리는 것이 아니라, 충돌하는 기준과 실행 조건을 좁히는 것입니다.
각 발언은 동의할 점, 고쳐야 할 점, 다음 결정에 필요한 질문을 남기는 방식으로 이어가겠습니다."""
