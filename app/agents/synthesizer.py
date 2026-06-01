from __future__ import annotations

import re
from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.llm import LLMClient, complete_structured
from app.prompt_examples import SYNTHESIS_CANDIDATE_EXAMPLES, SYNTHESIS_SELECTION_EXAMPLES
from app.schemas import AgentMessage, ReasoningCandidate, ReasoningRecord


class SynthesisCandidateOutput(BaseModel):
    id: str
    title: str
    answer: str


class SynthesisCandidatesOutput(BaseModel):
    candidates: list[SynthesisCandidateOutput] = Field(default_factory=list)


class SynthesisSelectionOutput(BaseModel):
    selected_id: str
    selection_summary: str
    scores: dict[str, int] = Field(default_factory=dict)


@dataclass
class SynthesisCandidate:
    id: str
    title: str
    answer: str


class SynthesizerAgent:
    CANDIDATE_COUNT = 3

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def synthesize_with_candidates(
        self,
        problem: str,
        debate_messages: list[AgentMessage],
        critique: AgentMessage,
        phase: str,
        search_context: str | None = None,
        memory_context: str | None = None,
    ) -> tuple[AgentMessage, ReasoningRecord]:
        transcript = self._transcript(debate_messages)
        evidence_block = self._evidence_block(search_context, memory_context)
        result = complete_structured(
            self.llm,
            system_prompt="당신은 한국어 다중 에이전트 토론을 최종 답변 후보로 통합합니다. 엄격한 JSON만 반환하세요.",
            user_prompt=f"""토론을 바탕으로 서로 다른 최종 답변 후보 {self.CANDIDATE_COUNT}개를 만드세요.

예시는 형식과 판단 기준만 참고하고, 예시 문장을 그대로 복사하지 마세요.
{SYNTHESIS_CANDIDATE_EXAMPLES}

문제:
{problem}

토론 발언:
{transcript}

비판:
{critique.content}
{evidence_block}

출력 JSON 형식:
{{"candidates": [
  {{"id": "candidate_1", "title": "짧은 한국어 제목", "answer": "5~6줄 최종 답변"}},
  {{"id": "candidate_2", "title": "짧은 한국어 제목", "answer": "5~6줄 최종 답변"}},
  {{"id": "candidate_3", "title": "짧은 한국어 제목", "answer": "5~6줄 최종 답변"}}
]}}

규칙:
- 각 후보의 answer는 사용자에게 그대로 보여줄 수 있는 완성 답변이어야 합니다.
- 후보마다 다른 실행 전략이나 우선순위가 드러나야 합니다.
- 내부 사고과정, 단계별 추론, Chain-of-Thought를 쓰지 마세요.
- Markdown 문법, 번호 목록, 불릿, 굵은 글씨를 쓰지 마세요.
- 토론에 없던 새 주제를 임의로 추가하지 마세요.
- 검색 근거와 선별 품질 메모리가 있으면 그 범위 안에서만 구체 사실을 사용하세요.
- 선별 품질 메모리의 과거 답변 문장을 그대로 복사하지 마세요.""",
            schema=SynthesisCandidatesOutput,
            temperature=0.35,
        )
        if not result.used_llm or result.value is None:
            return self._fallback_candidate_result(
                problem=problem,
                critique=critique,
                phase=phase,
                status="skipped_no_llm",
                enabled=False,
                error=result.error,
            )

        candidates = self._candidates_from_output(result.value)
        if len(candidates) < self.CANDIDATE_COUNT:
            return self._fallback_candidate_result(
                problem=problem,
                critique=critique,
                phase=phase,
                status="fallback",
                enabled=True,
                error="Unable to parse three synthesis candidates.",
            )

        judge_result = complete_structured(
            self.llm,
            system_prompt="당신은 최종 답변 후보를 고르는 검증자입니다. 엄격한 JSON만 반환하세요.",
            user_prompt=f"""사용자의 문제와 토론 근거에 가장 잘 맞는 최종 답변 후보를 고르세요.

예시는 판단 기준만 참고하고, 예시 문장을 그대로 복사하지 마세요.
{SYNTHESIS_SELECTION_EXAMPLES}

문제:
{problem}

토론 발언:
{transcript}

비판:
{critique.content}
{evidence_block}

후보:
{self._format_candidates_for_judge(candidates)}

출력 JSON 형식:
{{"selected_id": "candidate_1", "selection_summary": "한국어 한 문장", "scores": {{"candidate_1": 5, "candidate_2": 3, "candidate_3": 4}}}}

규칙:
- 점수는 1~5 정수입니다.
- selection_summary에는 선택 이유만 요약하세요.
- 직접성, 근거 일치, 가정 위험, 실행 가능성, 간결성을 기준으로 고르세요.
- 검색 근거와 선별 품질 메모리에 어긋나는 후보는 감점하세요.
- 내부 사고과정이나 장문 추론을 쓰지 마세요.""",
            schema=SynthesisSelectionOutput,
            temperature=0.1,
        )
        selection = self._selection_from_output(judge_result.value, candidates) if judge_result.used_llm else None
        if selection is None:
            selected = candidates[0]
            status = "fallback"
            selected_id = selected.id
            summary = "후보 선택 결과를 파싱하지 못해 첫 번째 후보를 사용했습니다."
            scores = {candidate.id: 0 for candidate in candidates}
            error = judge_result.error or "Unable to parse synthesis candidate selection."
        else:
            selected_id, summary, scores = selection
            selected = next((candidate for candidate in candidates if candidate.id == selected_id), candidates[0])
            status = "selected"
            error = judge_result.error

        record = self._reasoning_record(
            phase=phase,
            status=status,
            enabled=True,
            candidates=candidates,
            selected_id=selected.id,
            selection_summary=summary,
            scores=scores,
            error=error,
        )
        message = self._message(
            content=selected.answer,
            source="llm",
            error=result.error,
            phase="initial",
            reasoning_record=record,
        )
        return message, record

    def synthesize(
        self,
        problem: str,
        debate_messages: list[AgentMessage],
        critique: AgentMessage,
        improvement_suggestions: list[str] | None = None,
        previous_synthesis: str | None = None,
        refine_instruction: str | None = None,
        search_context: str | None = None,
        memory_context: str | None = None,
    ) -> AgentMessage:
        transcript = self._transcript(debate_messages)
        evidence_block = self._evidence_block(search_context, memory_context)
        refine_block = ""
        if previous_synthesis or improvement_suggestions or refine_instruction:
            suggestion_text = "\n".join(f"- {item}" for item in (improvement_suggestions or []))
            refine_block = f"""

이전 최종 정리:
{previous_synthesis or "없음"}

평가 기반 개선 제안:
{suggestion_text or "- 별도 개선 제안 없음"}

역방향 검증 피드백:
{refine_instruction or "없음"}
"""
        prompt = f"""
문제:
{problem}

토론 발언:
{transcript}

비판:
{critique.content}
{evidence_block}
{refine_block}

충돌을 정리하고 토론을 실행 가능한 계획으로 통합한 최종 답변을 작성하세요.
반드시 자연스러운 한국어로 작성하고, 고유명사나 기술 약어 외에는 영어를 최소화하세요.
한 페이지 안에서 바로 읽히도록 5~6줄로만 작성하세요.
다음 의미가 자연스럽게 드러나야 합니다.
결론, 이유, 실행 순서, 주의할 점, 바로 할 일

출력 규칙:
- 평가 기반 개선 제안이나 역방향 검증 피드백이 있으면 그 부족분만 보완하세요.
- 토론에 없던 새 주제를 임의로 추가하지 마세요.
- 검색 근거와 선별 품질 메모리가 있으면 그 범위 안에서만 구체 사실을 사용하세요.
- 선별 품질 메모리의 과거 답변 문장을 그대로 복사하지 마세요.
- Markdown 문법을 쓰지 마세요. 번호 목록, 불릿, 제목 기호, 굵은 글씨 표시를 모두 쓰지 마세요.
- 각 줄은 한 문장으로 짧게 작성하세요.
- "원하면", "필요하면", "바로 이어서" 같은 후속 제안 문장으로 끝내지 마세요.
"""
        result = self.llm.complete(
            system_prompt="당신은 한국어 다중 에이전트 토론을 명확한 최종 결정과 다음 행동으로 통합합니다.",
            user_prompt=prompt,
            temperature=0.3,
        )
        content = (
            result.content
            if result.used_llm and result.content
            else self._fallback(problem, critique, improvement_suggestions, refine_instruction)
        )
        return self._message(
            content=content,
            source="llm" if result.used_llm and result.content else "fallback",
            error=result.error,
            phase="refine" if (improvement_suggestions or refine_instruction) else "initial",
        )

    def _fallback_candidate_result(
        self,
        problem: str,
        critique: AgentMessage,
        phase: str,
        status: str,
        enabled: bool,
        error: str | None,
    ) -> tuple[AgentMessage, ReasoningRecord]:
        content = self._fallback(problem, critique)
        record = self._reasoning_record(
            phase=phase,
            status=status,
            enabled=enabled,
            candidates=[],
            selected_id=None,
            selection_summary=None,
            scores={},
            error=error,
        )
        message = self._message(
            content=content,
            source="fallback",
            error=error,
            phase="initial",
            reasoning_record=record,
        )
        return message, record

    def _message(
        self,
        content: str,
        source: str,
        error: str | None,
        phase: str,
        reasoning_record: ReasoningRecord | None = None,
    ) -> AgentMessage:
        metadata = {
            "source": source,
            "error": error,
            "phase": phase,
        }
        if reasoning_record is not None:
            metadata.update(
                {
                    "reasoning_mode": reasoning_record.mode,
                    "reasoning_status": reasoning_record.status,
                    "selected_candidate_id": reasoning_record.selected_id,
                }
            )
        return AgentMessage(
            stage="synthesizer",
            agent_id="synthesizer",
            agent_name="종합 에이전트",
            role="토론을 최종 답변으로 통합하는 역할",
            content=self._clean_final_answer(content),
            metadata=metadata,
        )

    def _reasoning_record(
        self,
        phase: str,
        status: str,
        enabled: bool,
        candidates: list[SynthesisCandidate],
        selected_id: str | None,
        selection_summary: str | None,
        scores: dict[str, int],
        error: str | None,
    ) -> ReasoningRecord:
        normalized_phase = "followup" if phase == "followup" else "initial"
        return ReasoningRecord(
            phase=normalized_phase,
            stage="synthesis",
            mode="tree",
            enabled=enabled,
            status=status,
            candidate_count=len(candidates),
            candidates=[
                ReasoningCandidate(
                    id=candidate.id,
                    title=candidate.title,
                    answer_preview=self._preview(candidate.answer),
                )
                for candidate in candidates
            ],
            selected_id=selected_id,
            selection_summary=selection_summary,
            scores=scores,
            error=error,
        )

    def _candidates_from_output(self, output: object) -> list[SynthesisCandidate]:
        if not isinstance(output, SynthesisCandidatesOutput):
            return []

        candidates: list[SynthesisCandidate] = []
        for index, item in enumerate(output.candidates[: self.CANDIDATE_COUNT], start=1):
            answer = self._clean_final_answer(item.answer.strip())
            if not answer:
                continue
            candidates.append(
                SynthesisCandidate(
                    id=item.id.strip() or f"candidate_{index}",
                    title=item.title.strip() or f"후보 {index}",
                    answer=answer,
                )
            )
        return candidates

    def _selection_from_output(
        self,
        output: object,
        candidates: list[SynthesisCandidate],
    ) -> tuple[str, str, dict[str, int]] | None:
        if not isinstance(output, SynthesisSelectionOutput):
            return None

        candidate_ids = {candidate.id for candidate in candidates}
        selected_id = output.selected_id.strip()
        if selected_id not in candidate_ids:
            return None

        scores = {}
        for candidate_id in candidate_ids:
            scores[candidate_id] = self._score(output.scores.get(candidate_id))

        return selected_id, output.selection_summary.strip(), scores

    def _format_candidates_for_judge(self, candidates: list[SynthesisCandidate]) -> str:
        return "\n\n".join(
            f"[{candidate.id}] {candidate.title}\n{candidate.answer}" for candidate in candidates
        )

    def _evidence_block(self, search_context: str | None, memory_context: str | None) -> str:
        blocks = []
        if search_context:
            blocks.append(f"검색 근거:\n{search_context}")
        if memory_context:
            blocks.append(f"선별 품질 메모리:\n{memory_context}")
        if not blocks:
            return ""
        return "\n\n" + "\n\n".join(blocks) + "\n"

    def _transcript(self, debate_messages: list[AgentMessage]) -> str:
        return "\n\n".join(
            f"[{message.agent_name} / {message.role}]\n{message.content}" for message in debate_messages
        )

    def _preview(self, content: str, max_length: int = 120) -> str:
        collapsed = " ".join(content.split())
        if len(collapsed) <= max_length:
            return collapsed
        return f"{collapsed[: max_length - 1]}..."

    def _score(self, value: object) -> int:
        try:
            score = int(value)
        except (TypeError, ValueError):
            return 0
        if score < 1:
            return 1
        if score > 5:
            return 5
        return score

    def _fallback(
        self,
        problem: str,
        critique: AgentMessage,
        improvement_suggestions: list[str] | None = None,
        refine_instruction: str | None = None,
    ) -> str:
        suggestion_line = ""
        if improvement_suggestions or refine_instruction:
            items = [*list(improvement_suggestions or [])]
            if refine_instruction:
                items.append(refine_instruction)
            suggestion_line = f"\n보완할 점은 {items[0]}입니다."
        return f"""결론은 지금 문제를 한 번에 크게 넓히기보다, 가장 설득력 있는 한 가지 실행 방향으로 좁히는 것입니다.
이유는 관점 생성, 토론, 내부 검토, 최종 정리가 끊기지 않고 이어져야 결과를 믿고 읽을 수 있기 때문입니다.
실행은 먼저 핵심 질문을 정하고, 그다음 에이전트 의견을 비교한 뒤, 마지막에 하나의 행동 계획으로 묶으면 됩니다.
주의할 점은 내부 비판을 그대로 길게 노출하면 읽는 흐름이 무거워진다는 것입니다.
바로 할 일은 샘플 문제 하나로 전체 흐름이 끝까지 자연스럽게 보이는지 확인하는 것입니다.{suggestion_line}"""

    def _clean_final_answer(self, content: str) -> str:
        lines = []
        for line in content.splitlines():
            cleaned = self._strip_markdown(line)
            if not cleaned or self._is_followup_offer(cleaned):
                continue
            if self._is_structural_heading(cleaned):
                continue
            lines.append(cleaned)
        return "\n".join(lines[:6]).strip()

    def _strip_markdown(self, line: str) -> str:
        cleaned = line.strip()
        cleaned = cleaned.replace("**", "")
        cleaned = cleaned.replace("__", "")
        cleaned = re.sub(r"^#{1,6}\s*", "", cleaned)
        cleaned = re.sub(r"^[-*+]\s+", "", cleaned)
        cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned)
        return cleaned.strip()

    def _is_structural_heading(self, line: str) -> bool:
        normalized = line.strip().rstrip(":：")
        headings = {
            "최종 결론",
            "최종 판단",
            "선택한 방향",
            "실행 단계",
            "실행 순서",
            "리스크와 대응",
            "주의할 점",
            "다음 24시간 액션",
            "바로 할 일",
            "보완 포인트 반영",
        }
        return normalized in headings

    def _is_followup_offer(self, line: str) -> bool:
        normalized = line.strip().lower()
        if not normalized:
            return False
        offer_patterns = (
            "원하면",
            "원하시면",
            "필요하면",
            "필요하시면",
            "궁금하면",
            "궁금하시면",
            "바로 이어서",
            "이어 정리",
            "정리해줄게",
            "정리해드릴게",
            "알려줄게",
            "알려드릴게",
            "도와줄게",
            "도와드릴게",
        )
        return any(pattern in normalized for pattern in offer_patterns)
