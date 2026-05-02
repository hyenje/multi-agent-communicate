from app.llm import LLMClient
from app.schemas import AgentMessage, Persona


class SpecialistAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def answer(self, problem: str, persona: Persona) -> AgentMessage:
        prompt = f"""
문제:
{problem}

페르소나:
- 이름: {persona.name}
- 역할: {persona.role}
- 관점: {persona.perspective}
- 핵심 질문: {", ".join(persona.priority_questions)}

이 페르소나의 관점에서 실용적인 의견을 작성하세요.
반드시 자연스러운 한국어로 작성하고, 고유명사나 기술 약어 외에는 영어를 최소화하세요.
다음 구조를 사용하세요.
1. 핵심 판단
2. 근거
3. 실행 제안
4. 주의할 점
간결하고 구체적으로 작성하세요.
"""
        result = self.llm.complete(
            system_prompt="당신은 한국어 다중 에이전트 문제 해결 토론에 참여한 전문가입니다. 모든 답변은 자연스러운 한국어로 작성하세요.",
            user_prompt=prompt,
        )
        content = result.content if result.used_llm and result.content else self._fallback(problem, persona)
        return AgentMessage(
            stage="specialist",
            agent_id=persona.id,
            agent_name=persona.name,
            role=persona.role,
            content=content,
            metadata={"source": "llm" if result.used_llm and result.content else "fallback", "error": result.error},
        )

    def respond(
        self,
        problem: str,
        persona: Persona,
        transcript: str,
        moderator_note: str,
        round_number: int,
    ) -> AgentMessage:
        prompt = f"""
문제:
{problem}

페르소나:
- 이름: {persona.name}
- 역할: {persona.role}
- 관점: {persona.perspective}
- 핵심 질문: {", ".join(persona.priority_questions)}

사회자 지시:
{moderator_note}

지금까지의 토론:
{transcript}

{persona.name}의 관점에서 앞선 발언 중 하나를 직접 받아치세요.
반드시 자연스러운 한국어로 작성하고, 고유명사나 기술 약어 외에는 영어를 최소화하세요.
요구사항:
- 앞선 에이전트 이름이나 주장을 하나 이상 직접 언급하세요.
- 단순 반복이 아니라 동의, 반박, 보완 중 하나를 분명히 하세요.
- 마지막에 다음 에이전트가 이어받을 수 있는 질문을 하나 남기세요.
- 4~7문장으로, 실제 대화창의 발언처럼 작성하세요.
"""
        result = self.llm.complete(
            system_prompt="당신은 한국어 다중 에이전트 토론에 참여한 전문가입니다. 앞선 발언에 실제로 반응하며 대화하세요.",
            user_prompt=prompt,
            temperature=0.45,
        )
        content = (
            result.content
            if result.used_llm and result.content
            else self._response_fallback(persona, round_number)
        )
        return AgentMessage(
            stage="debate",
            agent_id=persona.id,
            agent_name=persona.name,
            role=persona.role,
            content=content,
            metadata={
                "source": "llm" if result.used_llm and result.content else "fallback",
                "error": result.error,
                "round": round_number,
            },
        )

    def _fallback(self, problem: str, persona: Persona) -> str:
        questions = "\n".join(f"- {question}" for question in persona.priority_questions)
        return f"""1. 핵심 판단
{persona.name} 관점에서는 이 문제를 '{persona.perspective}' 기준으로 좁혀야 합니다.

2. 근거
현재 문제는 범위가 넓어질수록 구현보다 조율 비용이 커집니다. 먼저 한 번의 입력에서 관점, 비판, 종합이 끝까지 이어지는지 확인하는 것이 중요합니다.

3. 실행 제안
{questions}

4. 주의할 점
초기 MVP에서는 자동화 범위를 늘리기보다 로그 품질, 재현성, 실패 시 폴백을 우선해야 합니다."""

    def _response_fallback(self, persona: Persona, round_number: int) -> str:
        return f"""{round_number}번째 라운드에서는 앞선 의견을 그대로 늘리기보다 실행 조건을 좁히는 쪽으로 보태겠습니다.
저는 {persona.name} 관점에서 "{persona.perspective}" 기준이 빠지면 결론이 좋아 보여도 실제 선택으로 이어지기 어렵다고 봅니다.
앞선 발언의 큰 방향에는 동의하지만, 지금 단계에서는 범위, 성공 기준, 데모 실패 시 대안 중 하나를 더 명확히 해야 합니다.
그래서 다음 발언자는 이 아이디어를 실제로 2주 안에 보여줄 수 있는 최소 단위가 무엇인지 먼저 정해주면 좋겠습니다."""
