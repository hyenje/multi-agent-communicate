from __future__ import annotations

from pydantic import BaseModel, Field

from app.llm import LLMClient, complete_structured
from app.schemas import AgentMessage, Evaluation


class EvaluationOutput(BaseModel):
    consistency: int = Field(..., ge=1, le=5)
    specificity: int = Field(..., ge=1, le=5)
    risk_awareness: int = Field(..., ge=1, le=5)
    feasibility: int = Field(..., ge=1, le=5)
    overall_comment: str
    improvement_suggestions: list[str] = Field(default_factory=list)


class ReverseVerificationOutput(BaseModel):
    score: int = Field(..., ge=1, le=5)
    missing_points: list[str] = Field(default_factory=list)
    unsupported_points: list[str] = Field(default_factory=list)
    style_issues: list[str] = Field(default_factory=list)
    needs_extra_round: bool = False
    refine_instruction: str = ""


class EvaluatorAgent:
    REVERSE_VERIFICATION_THRESHOLD = 4
    REVERSE_VERIFICATION_MAX_ATTEMPTS = 3

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
        result = complete_structured(
            self.llm,
            system_prompt="당신은 한국어 다중 에이전트 추론 품질을 평가합니다. 엄격한 JSON만 반환하세요.",
            user_prompt=prompt,
            schema=EvaluationOutput,
            temperature=0.15,
        )

        source = "fallback"
        evaluation = self._from_output(result.value) if result.used_llm else None
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

    def reverse_verify(
        self,
        problem: str,
        debate_messages: list[AgentMessage],
        critique: AgentMessage,
        synthesis: AgentMessage,
        search_context: str | None = None,
        memory_context: str | None = None,
    ) -> dict[str, object]:
        transcript = "\n\n".join(
            f"[{message.agent_name} / {message.role}]\n{message.content}" for message in debate_messages
        )
        search_block = f"\n검색 근거:\n{search_context}\n" if search_context else ""
        memory_block = f"\n선별 품질 메모리:\n{memory_context}\n" if memory_context else ""
        prompt = f"""
사용자의 원래 문제:
{problem}

토론 발언:
{transcript}

내부 비판:
{critique.content}
{search_block}{memory_block}

최종 정리:
{synthesis.content}

역방향 검증을 하세요.
위 최종 정리만 보고 사용자의 원래 요구를 거꾸로 추정했을 때, 실제 문제와 충분히 맞는지 평가하세요.
반드시 JSON 객체만 반환하세요.
- score: integer 1-5
- missing_points: 최종 정리에서 빠진 사용자 요구나 토론 핵심 배열
- unsupported_points: 토론 근거 없이 새로 추가된 주장 배열
- style_issues: 너무 길거나 짧음, Markdown 형식, 불필요한 후속 제안 등 읽기 문제 배열
- needs_extra_round: boolean, 단순 재작성으로 해결하기 어렵고 에이전트 의견을 한 번 더 받아야 하면 true
- refine_instruction: 다음 최종 정리를 고칠 때 따라야 할 한국어 지시문 한 문장

평가 기준:
- 사용자의 실제 질문에 직접 답해야 합니다.
- 토론과 내부 비판에서 나온 핵심을 반영해야 합니다.
- 새로운 주제나 후속 제안을 임의로 추가하면 감점합니다.
- 검색 근거와 선별 품질 메모리에 없는 구체 사실을 단정하면 unsupported_points에 넣고 감점합니다.
- 선별 품질 메모리의 과거 답변 문장을 복사한 흔적이 있으면 style_issues에 넣고 감점합니다.
- 발표 화면에서 읽을 수 있도록 너무 길지도, 너무 짧지도 않아야 합니다.
- 단순 문장 다듬기로 충분하면 needs_extra_round는 false입니다.
"""
        result = complete_structured(
            self.llm,
            system_prompt="당신은 한국어 다중 에이전트 토론의 최종 답변을 역방향 검증합니다. 엄격한 JSON만 반환하세요.",
            user_prompt=prompt,
            schema=ReverseVerificationOutput,
            temperature=0.1,
        )

        verification = self._reverse_from_output(result.value) if result.used_llm else None
        source = "fallback"
        error = result.error
        if result.used_llm and verification is not None:
            source = "llm"
        elif result.used_llm:
            error = "Unable to parse LLM reverse verification JSON."

        if verification is None:
            verification = self._reverse_fallback(problem, synthesis)
            verification["error"] = error

        verification["source"] = source
        return verification

    def _from_output(self, output: object) -> Evaluation | None:
        if not isinstance(output, EvaluationOutput):
            return None

        try:
            return Evaluation(
                consistency=self._score(output.consistency),
                specificity=self._score(output.specificity),
                risk_awareness=self._score(output.risk_awareness),
                feasibility=self._score(output.feasibility),
                overall_comment=output.overall_comment.strip(),
                improvement_suggestions=[
                    str(item).strip()
                    for item in output.improvement_suggestions
                    if str(item).strip()
                ][:3],
                metadata={},
            )
        except (TypeError, ValueError):
            return None

    def _reverse_from_output(self, output: object) -> dict[str, object] | None:
        if not isinstance(output, ReverseVerificationOutput):
            return None

        try:
            score = self._score(output.score)
            return {
                "score": score,
                "passed": score >= self.REVERSE_VERIFICATION_THRESHOLD,
                "threshold": self.REVERSE_VERIFICATION_THRESHOLD,
                "missing_points": self._string_list(output.missing_points),
                "unsupported_points": self._string_list(output.unsupported_points),
                "style_issues": self._string_list(output.style_issues),
                "needs_extra_round": output.needs_extra_round and score < self.REVERSE_VERIFICATION_THRESHOLD,
                "refine_instruction": output.refine_instruction.strip(),
            }
        except (TypeError, ValueError):
            return None

    def _fallback(
        self,
        debate_messages: list[AgentMessage],
        critique: AgentMessage,
        synthesis: AgentMessage,
    ) -> Evaluation:
        final_answer = synthesis.content
        line_count = len([line for line in final_answer.splitlines() if line.strip()])
        action_count = sum(
            1
            for keyword in ["실행", "먼저", "그다음", "마지막", "바로 할 일", "확인"]
            if keyword in final_answer
        )
        has_risk = any(keyword in final_answer for keyword in ["리스크", "위험", "주의", "대응"])
        has_next_action = any(keyword in final_answer for keyword in ["다음", "24시간", "실행", "액션", "바로 할 일"])

        responder_count = len({message.agent_id for message in debate_messages})
        response_turns = len([message for message in debate_messages if message.stage == "debate"])

        consistency = 5 if responder_count >= 3 and response_turns >= 3 else 4 if critique.content else 3
        specificity = 5 if 4 <= line_count <= 6 and action_count >= 2 else 4 if line_count <= 8 else 3
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

    def _reverse_fallback(self, problem: str, synthesis: AgentMessage) -> dict[str, object]:
        final_answer = synthesis.content
        lines = [line.strip() for line in final_answer.splitlines() if line.strip()]
        has_sections = any(section in final_answer for section in ["최종 결론", "최종 판단", "결론은", "결론"])
        has_actions = any(keyword in final_answer for keyword in ["실행", "먼저", "그다음", "바로 할 일", "확인"])
        has_risk = any(keyword in final_answer for keyword in ["주의", "리스크", "위험", "대응"])
        overlap = len(self._keyword_terms(problem) & self._keyword_terms(final_answer))

        score = 5 if has_sections and has_actions and has_risk and overlap >= 2 else 4 if has_sections else 3
        return {
            "score": score,
            "passed": score >= self.REVERSE_VERIFICATION_THRESHOLD,
            "threshold": self.REVERSE_VERIFICATION_THRESHOLD,
            "missing_points": [] if score >= self.REVERSE_VERIFICATION_THRESHOLD else ["사용자 문제와 최종 정리의 연결이 약합니다."],
            "unsupported_points": [],
            "style_issues": [] if 4 <= len(lines) <= 6 else ["최종 정리는 한 페이지에서 읽히도록 4~6줄로 줄이는 편이 좋습니다."],
            "needs_extra_round": False,
            "refine_instruction": "사용자 질문과 직접 연결되는 결론, 실행 순서, 주의점을 균형 있게 다시 정리하세요.",
        }

    def _score(self, value: object) -> int:
        score = int(value)
        if score < 1:
            return 1
        if score > 5:
            return 5
        return score

    def _string_list(self, value: object) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item).strip() for item in value if item is not None and str(item).strip()][:5]

    def _keyword_terms(self, text: str) -> set[str]:
        normalized = "".join(
            character.lower() if character.isalnum() else " "
            for character in text
        )
        return {term for term in normalized.split() if len(term) >= 2 and not term.isdigit()}
