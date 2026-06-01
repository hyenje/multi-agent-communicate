import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from app.schemas import (
    AgentMessage,
    Evaluation,
    Persona,
    SearchQueryNode,
    SearchRecord,
    SolveResponse,
)
from ui.streamlit_chat import (
    chat_thread_items,
    format_activity_duration,
    moderator_message_html,
    moderator_summary,
    render_chat_bubble,
    render_chat_thread,
    response_work_duration_label,
    search_record_activity_item,
    work_history_items,
)
from ui.streamlit_streaming import insert_streaming_activity_items


class StreamlitChatRenderingTest(unittest.TestCase):
    def test_moderator_summary_prefers_sentence_boundary(self):
        content = (
            "이번 라운드에서는 이전 발언의 충돌 지점을 먼저 좁히겠습니다. "
            "각 Agent는 새 아이디어를 늘리기보다 하나의 주장에 직접 반응해야 합니다. "
            "마지막에는 다음 결정에 필요한 조건만 남기겠습니다."
        )

        self.assertEqual(
            "이번 라운드에서는 이전 발언의 충돌 지점을 먼저 좁히겠습니다.",
            moderator_summary(content, max_length=80),
        )

    def test_moderator_message_html_keeps_full_text_collapsible(self):
        content = (
            "이번 라운드에서는 이전 발언의 충돌 지점을 먼저 좁히겠습니다. "
            "각 Agent는 새 아이디어를 늘리기보다 하나의 주장에 직접 반응해야 합니다. "
            "마지막에는 다음 결정에 필요한 조건만 남기겠습니다."
        )

        markup = moderator_message_html(content)

        self.assertIn("pg-moderator-preview", markup)
        self.assertIn("전문 보기", markup)
        self.assertIn("각 Agent는 새 아이디어", markup)

    def test_search_records_are_inserted_at_conversation_positions(self):
        response = SolveResponse(
            problem="검색 위치를 확인한다.",
            personas=[
                Persona(
                    id="demo",
                    name="데모 설계자",
                    role="데모 흐름을 보는 역할",
                    perspective="보이는 흐름을 중시합니다.",
                )
            ],
            messages=[
                AgentMessage(
                    stage="moderator",
                    agent_id="moderator",
                    agent_name="사회자 에이전트",
                    role="진행자",
                    content="opening",
                    metadata={"phase": "opening"},
                ),
                AgentMessage(
                    stage="moderator",
                    agent_id="moderator",
                    agent_name="사회자 에이전트",
                    role="진행자",
                    content="round one",
                    metadata={"phase": "response_round", "round": 1},
                ),
                AgentMessage(
                    stage="debate",
                    agent_id="demo",
                    agent_name="데모 설계자",
                    role="데모 흐름을 보는 역할",
                    content="round one reply",
                    metadata={"round": 1},
                ),
                AgentMessage(
                    stage="user",
                    agent_id="user",
                    agent_name="현재",
                    role="사용자",
                    content="후속 의견",
                    metadata={"round": 2},
                ),
                AgentMessage(
                    stage="debate",
                    agent_id="demo",
                    agent_name="데모 설계자",
                    role="데모 흐름을 보는 역할",
                    content="followup reply",
                    metadata={"phase": "user_response", "round": 2},
                ),
            ],
            final_answer="final",
            evaluation=Evaluation(
                consistency=5,
                specificity=5,
                risk_awareness=5,
                feasibility=5,
                overall_comment="ok",
            ),
            search_records=[
                SearchRecord(
                    phase="initial",
                    mode="auto",
                    enabled=True,
                    needed=True,
                    status="fetched",
                    queries=["초기 검색"],
                ),
                SearchRecord(
                    phase="debate_round",
                    round_number=1,
                    mode="auto",
                    enabled=True,
                    needed=True,
                    status="fetched",
                    queries=["라운드 검색"],
                ),
                SearchRecord(
                    phase="followup",
                    mode="auto",
                    enabled=True,
                    needed=True,
                    status="fetched",
                    queries=["후속 검색"],
                ),
            ],
            used_llm=False,
            model="test",
        )

        items = chat_thread_items(response)
        initial_search_index = self._activity_index(items, "initial")
        debate_search_index = self._activity_index(items, "debate_round")
        followup_search_index = self._activity_index(items, "followup")
        round_moderator_index = self._content_index(items, "round one")
        user_index = self._content_index(items, "후속 의견")
        followup_reply_index = self._content_index(items, "followup reply")

        self.assertGreater(initial_search_index, 0)
        self.assertLess(debate_search_index, round_moderator_index)
        self.assertGreater(followup_search_index, user_index)
        self.assertLess(followup_search_index, followup_reply_index)

    def test_personas_are_not_rendered_as_summary_cards(self):
        response = SolveResponse(
            problem="페르소나 표시 방식을 확인한다.",
            personas=[
                Persona(
                    id="demo",
                    name="데모",
                    role="데모 흐름을 보는 역할",
                    perspective="흐름을 중시합니다.",
                ),
                Persona(
                    id="risk",
                    name="리스크",
                    role="위험을 보는 역할",
                    perspective="빈틈을 중시합니다.",
                ),
            ],
            messages=[],
            final_answer="final",
            evaluation=Evaluation(
                consistency=5,
                specificity=5,
                risk_awareness=5,
                feasibility=5,
                overall_comment="ok",
            ),
            used_llm=False,
            model="test",
        )

        items = chat_thread_items(response)
        summary_items = [item for item in items if item.get("kind") == "persona_summary"]

        self.assertEqual([], summary_items)
        self.assertNotIn("페르소나 소개", [item.get("meta") for item in items])

    def test_render_chat_thread_shows_initial_question_before_answer(self):
        response = SolveResponse(
            problem="물음도 화면에 보여야 한다.",
            personas=[],
            messages=[],
            final_answer="답변은 본문으로 보여준다.",
            evaluation=Evaluation(
                consistency=5,
                specificity=5,
                risk_awareness=5,
                feasibility=5,
                overall_comment="ok",
            ),
            used_llm=False,
            model="test",
        )
        calls = []

        with (
            patch("ui.streamlit_chat.render_chat_bubble") as render_bubble,
            patch("ui.streamlit_chat.render_final_answer") as render_answer,
            patch("ui.streamlit_chat.render_work_history") as render_history,
        ):
            render_bubble.side_effect = lambda *_args, **_kwargs: calls.append("question")
            render_history.side_effect = lambda *_args, **_kwargs: calls.append("history")
            render_answer.side_effect = lambda *_args, **_kwargs: calls.append("answer")
            render_chat_thread(response, include_anchor=False)

        render_bubble.assert_called_once()
        self.assertEqual("user", render_bubble.call_args.args[0]["kind"])
        self.assertEqual("물음도 화면에 보여야 한다.", render_bubble.call_args.args[0]["content"])
        render_answer.assert_called_once_with(response)
        render_history.assert_called_once_with(response, confirmed_settings=None)
        self.assertEqual(["question", "history", "answer"], calls)

    def test_user_bubble_hides_chat_metadata_by_default(self):
        with patch("ui.streamlit_chat.st.markdown") as markdown:
            render_chat_bubble(
                {
                    "kind": "user",
                    "name": "나",
                    "meta": "처음 입력한 문제",
                    "content": "질문만 보여준다.",
                }
            )

        markup = markdown.call_args.args[0]
        self.assertIn("질문만 보여준다.", markup)
        self.assertNotIn("처음 입력한 문제", markup)

    def test_work_history_hides_initial_prompt_and_final_answer(self):
        response = SolveResponse(
            problem="3주 안에 AI 학습 도우미를 만들 수 있을지 판단한다.",
            personas=[
                Persona(
                    id="mvp",
                    name="MVP 설계자",
                    role="범위를 줄이는 역할",
                    perspective="3주 안에는 한 가지 학습 흐름만 검증해야 합니다.",
                )
            ],
            messages=[
                AgentMessage(
                    stage="specialist",
                    agent_id="mvp",
                    agent_name="MVP 설계자",
                    role="범위를 줄이는 역할",
                    content="3주 안에는 과목 추천 전체보다 오답 복습 한 흐름을 먼저 검증해야 합니다.",
                    metadata={"source": "llm"},
                ),
                AgentMessage(
                    stage="synthesizer",
                    agent_id="synthesizer",
                    agent_name="종합 에이전트",
                    role="토론을 최종 답변으로 통합하는 역할",
                    content="결론은 오답 복습 한 흐름입니다.",
                    metadata={"source": "llm"},
                )
            ],
            final_answer="결론은 오답 복습 한 흐름으로 좁혀 3주 안에 검증하는 것입니다.",
            evaluation=Evaluation(
                consistency=5,
                specificity=5,
                risk_awareness=5,
                feasibility=5,
                overall_comment="ok",
            ),
            used_llm=True,
            model="test",
        )

        items = work_history_items(response)

        self.assertNotIn("3주 안에 AI 학습 도우미를 만들 수 있을지 판단한다.", [item.get("content") for item in items])
        self.assertNotIn("결론은 오답 복습 한 흐름입니다.", [item.get("content") for item in items])
        self.assertEqual(["agent_group"], [item.get("kind") for item in items])

    def test_work_duration_label_uses_compact_time(self):
        created_at = datetime(2026, 1, 1, 0, 12, 3)
        response = SolveResponse(
            problem="작업 시간을 확인한다.",
            personas=[],
            messages=[],
            final_answer="final",
            evaluation=Evaluation(
                consistency=5,
                specificity=5,
                risk_awareness=5,
                feasibility=5,
                overall_comment="ok",
            ),
            search_records=[
                SearchRecord(
                    phase="initial",
                    mode="auto",
                    enabled=True,
                    needed=False,
                    status="not_needed",
                    elapsed_ms=3000,
                    created_at=created_at - timedelta(minutes=12),
                )
            ],
            used_llm=False,
            model="test",
            created_at=created_at,
        )

        self.assertEqual("12m 3s 동안 작업", response_work_duration_label(response))
        self.assertEqual("2m 3s 동안 작업", format_activity_duration(123000))

    def test_search_activity_summary_uses_root_queries_without_tree_details(self):
        item = search_record_activity_item(
            SearchRecord(
                phase="debate_round",
                round_number=1,
                mode="auto",
                enabled=True,
                needed=True,
                status="fetched",
                queries=["root query", "child query"],
                query_tree=[
                    SearchQueryNode(
                        query="root query",
                        result_count=2,
                        status="fetched",
                        children=[
                            SearchQueryNode(
                                query="child query",
                                result_count=1,
                                status="fetched",
                            )
                        ],
                    )
                ],
                result_count=3,
            )
        )

        self.assertEqual(2, item["query_count"])
        self.assertEqual(["root query"], item["root_queries"])

    def test_streaming_search_activity_stays_before_matching_round(self):
        items = insert_streaming_activity_items(
            [
                {
                    "kind": "system",
                    "stage": "moderator",
                    "content": "opening",
                },
                {
                    "kind": "agent",
                    "stage": "specialist",
                    "content": "initial opinion",
                    "groupable": True,
                },
                {
                    "kind": "system",
                    "stage": "moderator",
                    "round": 1,
                    "phase": "response_round",
                    "content": "round one",
                },
            ],
            [
                {
                    "kind": "activity",
                    "activity_index": 0,
                    "phase": "debate_round",
                    "round_number": 1,
                }
            ],
        )

        activity_index = self._activity_index(items, "debate_round")
        initial_index = self._content_index(items, "initial opinion")
        round_index = self._content_index(items, "round one")

        self.assertGreater(activity_index, initial_index)
        self.assertLess(activity_index, round_index)

    def test_streaming_followup_search_activity_stays_after_user_message(self):
        items = insert_streaming_activity_items(
            [
                {
                    "kind": "user",
                    "content": "후속 의견",
                },
                {
                    "kind": "agent",
                    "stage": "debate",
                    "round": 2,
                    "phase": "user_response",
                    "content": "followup reply",
                    "groupable": True,
                },
            ],
            [
                {
                    "kind": "activity",
                    "activity_index": 0,
                    "phase": "followup",
                }
            ],
        )

        activity_index = self._activity_index(items, "followup")
        user_index = self._content_index(items, "후속 의견")
        reply_index = self._content_index(items, "followup reply")

        self.assertGreater(activity_index, user_index)
        self.assertLess(activity_index, reply_index)

    def _activity_index(self, items: list[dict], phase: str) -> int:
        return next(
            index
            for index, item in enumerate(items)
            if item.get("kind") == "activity" and item.get("phase") == phase
        )

    def _content_index(self, items: list[dict], content: str) -> int:
        return next(index for index, item in enumerate(items) if item.get("content") == content)
