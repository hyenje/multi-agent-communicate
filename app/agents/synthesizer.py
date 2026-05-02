from app.llm import LLMClient
from app.schemas import AgentMessage


class SynthesizerAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def synthesize(
        self,
        problem: str,
        debate_messages: list[AgentMessage],
        critique: AgentMessage,
    ) -> AgentMessage:
        transcript = "\n\n".join(
            f"[{message.agent_name} / {message.role}]\n{message.content}" for message in debate_messages
        )
        prompt = f"""
문제:
{problem}

토론 발언:
{transcript}

비판:
{critique.content}

충돌을 정리하고 토론을 실행 가능한 계획으로 통합한 최종 답변을 작성하세요.
반드시 자연스러운 한국어로 작성하고, 고유명사나 기술 약어 외에는 영어를 최소화하세요.
다음 구조를 사용하세요.
1. 최종 결론
2. 선택한 방향
3. 실행 단계
4. 리스크와 대응
5. 다음 24시간 액션
"""
        result = self.llm.complete(
            system_prompt="당신은 한국어 다중 에이전트 토론을 명확한 최종 결정과 다음 행동으로 통합합니다.",
            user_prompt=prompt,
            temperature=0.3,
        )
        content = result.content if result.used_llm and result.content else self._fallback(problem, critique)
        return AgentMessage(
            stage="synthesizer",
            agent_id="synthesizer",
            agent_name="종합 에이전트",
            role="토론을 최종 답변으로 통합하는 역할",
            content=content,
            metadata={"source": "llm" if result.used_llm and result.content else "fallback", "error": result.error},
        )

    def _fallback(self, problem: str, critique: AgentMessage) -> str:
        return f"""1. 최종 결론
입력된 문제는 한 번에 거대한 자동화 시스템으로 만들기보다, 관점 생성 -> 역할별 의견 -> 비판 -> 종합이 안정적으로 보이는 MVP로 구현하는 것이 가장 좋습니다.

2. 선택한 방향
문제: {problem}

핵심 방향은 API 기반 LLM 호출을 사용하되, 실패 시에도 같은 형식의 결과가 나오는 폴백을 유지하는 것입니다.

3. 실행 단계
- 문제 입력 폼과 에이전트 수 설정을 만든다.
- 페르소나 생성기가 3~5개 역할을 만든다.
- 전문가 에이전트들이 각자 의견을 낸다.
- 비판 에이전트가 모순, 약한 가정, 누락을 지적한다.
- 종합 에이전트가 최종 결론과 다음 액션으로 정리한다.

4. 리스크와 대응
{critique.content}

5. 다음 24시간 액션
샘플 문제 3개로 로그가 끝까지 생성되는지 확인하고, 발표용으로 가장 설득력 있는 시나리오 하나를 고릅니다."""
