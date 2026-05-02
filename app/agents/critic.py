from app.llm import LLMClient
from app.schemas import AgentMessage


class CriticAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def review(self, problem: str, debate_messages: list[AgentMessage]) -> AgentMessage:
        transcript = "\n\n".join(
            f"[{message.agent_name} / {message.role}]\n{message.content}" for message in debate_messages
        )
        prompt = f"""
문제:
{problem}

토론 발언:
{transcript}

토론 전체를 검토하고 모순, 약한 가정, 누락된 제약, 다음 질문을 찾으세요.
반드시 자연스러운 한국어로 작성하고, 고유명사나 기술 약어 외에는 영어를 최소화하세요.
다음 구조로 간결한 비판을 반환하세요.
1. 모순 또는 충돌
2. 약한 가정
3. 누락된 관점
4. 최종 통합 전에 고쳐야 할 점
"""
        result = self.llm.complete(
            system_prompt="당신은 한국어 다중 에이전트 워크플로의 날카롭지만 건설적인 비판자입니다.",
            user_prompt=prompt,
            temperature=0.2,
        )
        content = result.content if result.used_llm and result.content else self._fallback(debate_messages)
        return AgentMessage(
            stage="critic",
            agent_id="critic",
            agent_name="비판 에이전트",
            role="모순, 약한 가정, 누락된 제약을 찾는 역할",
            content=content,
            metadata={"source": "llm" if result.used_llm and result.content else "fallback", "error": result.error},
        )

    def _fallback(self, debate_messages: list[AgentMessage]) -> str:
        names = ", ".join(dict.fromkeys(message.agent_name for message in debate_messages))
        return f"""1. 모순 또는 충돌
{names}의 의견은 대체로 MVP 축소에는 동의하지만, 품질을 높이려는 요구와 2주 일정 사이에 긴장이 있습니다.

2. 약한 가정
LLM 응답이 항상 구조화되어 나온다는 가정은 위험합니다. JSON 파싱 실패, 빈 응답, API 오류에 대비해야 합니다.

3. 누락된 관점
평가 기준이 없으면 다중 에이전트 구조가 실제로 더 나은지 설명하기 어렵습니다. 최소한 로그 완성도, 비판 품질, 최종 답변 일관성을 확인해야 합니다.

4. 최종 통합 전에 고쳐야 할 점
첫 버전은 에이전트 수, 모델명, API 사용 여부를 조절할 수 있어야 하고, 실패해도 데모가 이어져야 합니다."""
