from __future__ import annotations

from app.llm import LLMClient, parse_json_object
from app.schemas import AgentMessage, Evaluation


class EvaluatorAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def evaluate(
        self,
        problem: str,
        debate_messages: list[AgentMessage],
        critique: AgentMessage,
        synthesis: AgentMessage,
    ) -> Evaluation:
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

최종 종합:
{synthesis.content}

최종 결과를 평가하세요. 반드시 JSON 객체만 반환하세요.
- consistency: integer 1-5
- specificity: integer 1-5
- risk_awareness: integer 1-5
- feasibility: integer 1-5
- overall_comment: 한국어 한 문장 총평
- improvement_suggestions: 한국어 개선 제안 1~3개 배열

출력 규칙:
- 한국어 사용자를 위한 자연스러운 한국어로 작성하세요.
- OpenAI, API, MVP처럼 필요한 고유명사나 기술 약어 외에는 영어를 쓰지 마세요.
"""
        result = self.llm.complete(
            system_prompt="당신은 한국어 다중 에이전트 추론 품질을 평가합니다. 엄격한 JSON만 반환하세요.",
            user_prompt=prompt,
            temperature=0.15,
        )

        source = "fallback"
        evaluation = self._from_llm(result.content) if result.used_llm else None
        error = result.error
        if result.used_llm and evaluation is not None:
            source = "llm"
        elif result.used_llm:
            error = "Unable to parse LLM evaluation JSON."

        if evaluation is None:
            evaluation = self._fallback(debate_messages, critique, synthesis)
            evaluation.metadata["error"] = error

        evaluation.metadata["source"] = source
        return evaluation

    def _from_llm(self, raw: str) -> Evaluation | None:
        parsed = parse_json_object(raw)
        if not isinstance(parsed, dict):
            return None

        try:
            return Evaluation(
                consistency=self._score(parsed.get("consistency")),
                specificity=self._score(parsed.get("specificity")),
                risk_awareness=self._score(parsed.get("risk_awareness")),
                feasibility=self._score(parsed.get("feasibility")),
                overall_comment=str(parsed["overall_comment"]).strip(),
                improvement_suggestions=[
                    str(item).strip()
                    for item in parsed.get("improvement_suggestions", [])
                    if str(item).strip()
                ][:3],
                metadata={},
            )
        except (KeyError, TypeError, ValueError):
            return None

    def _fallback(
        self,
        debate_messages: list[AgentMessage],
        critique: AgentMessage,
        synthesis: AgentMessage,
    ) -> Evaluation:
        final_answer = synthesis.content
        bullet_count = final_answer.count("- ") + final_answer.count("\n1.")
        has_risk = any(keyword in final_answer for keyword in ["리스크", "위험", "주의", "대응"])
        has_next_action = any(keyword in final_answer for keyword in ["다음", "24시간", "실행 단계", "액션"])

        responder_count = len({message.agent_id for message in debate_messages})
        response_turns = len([message for message in debate_messages if message.stage == "debate"])

        consistency = 5 if responder_count >= 3 and response_turns >= 3 else 4 if critique.content else 3
        specificity = 5 if bullet_count >= 6 else 4 if bullet_count >= 3 else 3
        risk_awareness = 5 if has_risk else 3
        feasibility = 5 if has_next_action else 4

        return Evaluation(
            consistency=consistency,
            specificity=specificity,
            risk_awareness=risk_awareness,
            feasibility=feasibility,
            overall_comment="사회자 진행, 상호 응답, 비판과 종합 흐름이 유지되어 데모용 토론 로그로 사용하기 좋습니다.",
            improvement_suggestions=[
                "최종 답변에 정량적 성공 기준을 1개 이상 추가하면 설득력이 더 좋아집니다.",
                "발표용 시나리오에서는 Before/After 비교 예시를 함께 준비하는 것이 좋습니다.",
            ],
            metadata={},
        )

    def _score(self, value: object) -> int:
        score = int(value)
        if score < 1:
            return 1
        if score > 5:
            return 5
        return score
