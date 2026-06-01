from __future__ import annotations

import html
import time

import streamlit as st

from app.schemas import SolveResponse
from ui.api_client import PersonaGraphAPIError, stream_continue_discussion, stream_solve_problem
from ui.streamlit_chat import (
    agent_group_key,
    group_agent_items,
    message_item,
    render_activity_item,
    render_chat_item,
    render_chat_thread,
    render_pending_problem_thread,
)
from ui.streamlit_common import (
    avatar_markup,
    character_for_persona,
    live_message_frames,
    system_avatar_label,
)


SEARCH_EVENT_TYPES = {"search_started", "search_queries", "search_finished"}


def update_search_activities(activities: list[dict], event: dict) -> list[dict]:
    now = time.monotonic()
    if event.get("type") == "search_started" or not activities:
        activity = {"started_at": now, "events": []}
        activities.append(activity)
    else:
        activity = next(
            (candidate for candidate in reversed(activities) if "finished_at" not in candidate),
            activities[-1],
        )
    activity["events"].append(event)
    if event.get("type") == "search_finished":
        activity["finished_at"] = now
    return activities


def search_activity_item(activity: dict | None, activity_index: int | None = None) -> dict | None:
    if not activity or not activity.get("events"):
        return None
    latest = activity["events"][-1]
    finished_at = activity.get("finished_at")
    elapsed_ms = latest.get("elapsed_ms")
    if elapsed_ms is None:
        elapsed_ms = int(((finished_at or time.monotonic()) - activity["started_at"]) * 1000)
    return {
        "kind": "activity",
        "source": "search",
        "phase": latest.get("phase"),
        "round_number": latest.get("round_number"),
        "mode": latest.get("mode"),
        "provider": latest.get("provider") or "search",
        "status": latest.get("status") or "",
        "queries": latest.get("queries", []),
        "query_count": latest.get("query_count") or len(latest.get("queries", [])),
        "root_queries": latest.get("root_queries", latest.get("queries", [])[:3]),
        "result_count": latest.get("result_count") or 0,
        "elapsed_ms": elapsed_ms,
        "error": latest.get("error"),
        "event_type": latest.get("type"),
        "running": latest.get("type") != "search_finished",
        "activity_index": activity_index,
    }


def search_activity_items(activities: list[dict] | None) -> list[dict]:
    return [
        item
        for item in (
            search_activity_item(activity, index)
            for index, activity in enumerate(activities or [])
        )
        if item is not None
    ]


def insert_streaming_activity_items(message_items: list[dict], activity_items: list[dict]) -> list[dict]:
    items: list[dict] = []
    placed_indexes: set[int] = set()

    def pending_before(message_item: dict) -> list[dict]:
        round_number = message_item.get("round")
        if round_number is None:
            return []
        matches = []
        for activity in activity_items:
            index = activity.get("activity_index")
            if index in placed_indexes:
                continue
            if activity.get("round_number") != round_number:
                continue
            if activity.get("phase") == "debate_round" and message_item.get("stage") in {
                "moderator",
                "debate",
            }:
                matches.append(activity)
            elif (
                activity.get("phase") == "evaluation_extra_round"
                and message_item.get("phase") == "evaluation_extra_round"
            ):
                matches.append(activity)
        return matches

    def pending_after(message_item: dict) -> list[dict]:
        if message_item.get("kind") != "user":
            return []
        return [
            activity
            for activity in activity_items
            if activity.get("activity_index") not in placed_indexes
            and activity.get("phase") == "followup"
        ]

    for message_item in message_items:
        for activity in pending_before(message_item):
            items.append(activity)
            placed_indexes.add(activity["activity_index"])
        items.append(message_item)
        for activity in pending_after(message_item):
            items.append(activity)
            placed_indexes.add(activity["activity_index"])

    for activity in activity_items:
        index = activity.get("activity_index")
        if index not in placed_indexes:
            items.append(activity)
            placed_indexes.add(index)
    return items


def render_active_agent_status(active_agent, personas_by_id: dict) -> None:
    if not active_agent:
        return
    stage = str(active_agent.get("stage", "unknown"))
    agent_id = str(active_agent.get("agent_id", ""))
    agent_name = str(active_agent.get("agent_name", "Agent"))
    if stage == "persona_generation":
        label = "페르소나를 구성하고 있습니다..."
        character = None
        fallback = "PG"
    else:
        label = f"{agent_name}가 의견을 정리 중입니다..."
        persona = personas_by_id.get(agent_id)
        character = character_for_persona(persona)
        fallback = system_avatar_label(agent_id, agent_name, stage)
    avatar = avatar_markup(agent_name, character, fallback)
    st.markdown(
        f"""
<div class="pg-chat-shell">
  <div class="pg-chat-row pg-chat-row-agent">
    <div class="pg-chat-avatar-wrap">{avatar}</div>
    <div class="pg-active-status">{html.escape(label)}</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

def render_streaming_chat_thread(
    placeholder,
    live_messages,
    live_personas,
    active_event,
    streaming_message=None,
    base_response: SolveResponse | None = None,
    pending_problem: str | None = None,
    confirmed_settings: dict | None = None,
    keep_agent_group_expanded: bool = False,
    expanded_agent_group_key: str | None = None,
    render_context: bool = True,
    search_activities: list[dict] | None = None,
) -> None:
    with placeholder.container():
        activity_items = search_activity_items(search_activities)
        initial_activity_items = [
            item
            for item in activity_items
            if render_context and base_response is None and item.get("phase") == "initial"
        ]
        timeline_activity_items = [
            item for item in activity_items if item not in initial_activity_items
        ]
        if render_context:
            if base_response is not None:
                render_chat_thread(
                    base_response,
                    include_anchor=False,
                    confirmed_settings=confirmed_settings,
                )
            elif pending_problem:
                render_pending_problem_thread(pending_problem)

        for activity_item in initial_activity_items:
            render_activity_item(activity_item)

        personas_by_id = {
            persona.id: persona
            for persona in (live_personas or (base_response.personas if base_response else []))
        }
        message_items = []
        for message in live_messages:
            item = message_item(message, personas_by_id)
            if item:
                message_items.append(item)
        if streaming_message is not None:
            item = message_item(streaming_message, personas_by_id)
            if item:
                message_items.append(item)
        is_streaming_agent_message = (
            streaming_message is not None
            and streaming_message.stage in {"specialist", "debate"}
        )
        timeline_items = insert_streaming_activity_items(message_items, timeline_activity_items)
        for item in group_agent_items(
            timeline_items,
            expand_last_group=is_streaming_agent_message or keep_agent_group_expanded,
            expanded_group_key=expanded_agent_group_key,
        ):
            render_chat_item(item)
        st.markdown('<div id="pg-chat-bottom" class="pg-scroll-anchor"></div>', unsafe_allow_html=True)
        render_active_agent_status(active_event, personas_by_id)

def consume_chat_stream(
    events,
    base_response: SolveResponse | None = None,
    pending_problem: str | None = None,
    initial_personas=None,
) -> SolveResponse | None:
    live_messages = []
    live_personas = list(initial_personas or [])
    active_event = None
    search_activities = []
    keep_agent_group_expanded = False
    expanded_agent_group_key = None
    final_response = None
    confirmed_settings = st.session_state.get("pg_confirmed_settings")
    render_context = base_response is None
    if base_response is not None:
        render_chat_thread(
            base_response,
            include_anchor=False,
            confirmed_settings=confirmed_settings,
        )
    placeholder = st.empty()
    render_streaming_chat_thread(
        placeholder,
        live_messages,
        live_personas,
        active_event,
        base_response=base_response,
        pending_problem=pending_problem,
        confirmed_settings=confirmed_settings,
        keep_agent_group_expanded=keep_agent_group_expanded,
        expanded_agent_group_key=expanded_agent_group_key,
        render_context=render_context,
        search_activities=search_activities,
    )

    for event in events:
        rendered_this_event = False
        event_type = event.get("type")
        if event_type == "personas_ready":
            live_personas = list(event.get("personas", []))
            active_event = None
            keep_agent_group_expanded = False
            expanded_agent_group_key = None
        elif event_type == "agent_started":
            if event.get("stage") in {"critic", "evaluator"}:
                active_event = None
                continue
            active_event = event
            event_group_key = agent_event_group_key(event)
            if event_group_key != expanded_agent_group_key:
                keep_agent_group_expanded = False
                expanded_agent_group_key = None
        elif event_type == "agent_message":
            message = event.get("message")
            if message is not None:
                if message.stage == "persona_generation":
                    active_event = None
                    keep_agent_group_expanded = False
                    expanded_agent_group_key = None
                elif message.stage == "critic":
                    active_event = None
                    keep_agent_group_expanded = False
                    expanded_agent_group_key = None
                elif message.stage == "user":
                    live_messages.append(message)
                    active_event = None
                    keep_agent_group_expanded = False
                    expanded_agent_group_key = None
                else:
                    keep_agent_group_expanded = message.stage in {"specialist", "debate"}
                    expanded_agent_group_key = (
                        agent_message_group_key(message)
                        if keep_agent_group_expanded
                        else None
                    )
                    for frame in live_message_frames(message.content):
                        preview_message_model = message.model_copy(update={"content": frame})
                        render_streaming_chat_thread(
                            placeholder,
                            live_messages,
                            live_personas,
                            None,
                            streaming_message=preview_message_model,
                            base_response=base_response,
                            pending_problem=pending_problem,
                            confirmed_settings=confirmed_settings,
                            keep_agent_group_expanded=keep_agent_group_expanded,
                            expanded_agent_group_key=expanded_agent_group_key,
                            render_context=render_context,
                            search_activities=search_activities,
                        )
                        rendered_this_event = True
                        time.sleep(0.025)
                    live_messages.append(message)
                    active_event = None
        elif event_type in SEARCH_EVENT_TYPES:
            search_activities = update_search_activities(search_activities, event)
        elif event_type == "final_response":
            final_response = event.get("response")
            active_event = None
            keep_agent_group_expanded = False
            expanded_agent_group_key = None

        if not rendered_this_event:
            render_streaming_chat_thread(
                placeholder,
                live_messages,
                live_personas,
                active_event,
                base_response=base_response,
                pending_problem=pending_problem,
                confirmed_settings=confirmed_settings,
                keep_agent_group_expanded=keep_agent_group_expanded,
                expanded_agent_group_key=expanded_agent_group_key,
                render_context=render_context,
                search_activities=search_activities,
            )

    return final_response

def agent_message_group_key(message) -> str:
    return agent_group_key(
        {
            "stage": message.stage,
            "round": message.metadata.get("round"),
            "phase": message.metadata.get("phase"),
        }
    )

def agent_event_group_key(event: dict) -> str | None:
    stage = str(event.get("stage", ""))
    if stage not in {"specialist", "debate"}:
        return None
    return agent_group_key(
        {
            "stage": stage,
            "round": event.get("round"),
        }
    )

def run_initial_stream() -> None:
    problem = st.session_state.get("pg_pending_problem")
    if not problem:
        st.session_state["pg_chat_mode"] = "empty"
        st.rerun()

    settings = st.session_state["pg_settings"]
    try:
        response = consume_chat_stream(
            stream_solve_problem(
                problem=problem,
                persona_count=int(settings["persona_count"]),
                debate_rounds=int(settings["debate_rounds"]),
                use_llm=bool(settings["use_llm"]),
                model=settings.get("model"),
                search_mode=str(settings.get("search_mode", "auto")),
                temperature=float(settings["temperature"]),
            ),
            pending_problem=problem,
        )
    except PersonaGraphAPIError as exc:
        st.error(str(exc))
        st.session_state["pg_chat_mode"] = "configuring"
        return
    if response is None:
        st.error("토론 결과를 만들지 못했습니다.")
        st.session_state["pg_chat_mode"] = "configuring"
        return
    st.session_state["pg_current_response"] = response
    st.session_state["pg_current_run_id"] = response.run_id
    st.session_state["pg_pending_problem"] = None
    st.session_state["pg_chat_mode"] = "completed"
    st.rerun()

def run_followup_stream() -> None:
    response = st.session_state.get("pg_current_response")
    content = st.session_state.get("pg_pending_followup")
    if response is None or not content:
        st.session_state["pg_chat_mode"] = "completed" if response else "empty"
        st.rerun()

    settings = st.session_state["pg_settings"]
    if not response.run_id:
        st.error("저장된 대화 ID가 없어 이어 말할 수 없습니다.")
        st.session_state["pg_chat_mode"] = "completed"
        return
    try:
        updated = consume_chat_stream(
            stream_continue_discussion(
                run_id=response.run_id,
                content=content,
                max_agents=int(settings["max_reply_agents"]),
                use_llm=bool(settings["use_llm"]),
                model=settings.get("model"),
                search_mode=str(settings.get("search_mode", "auto")),
                temperature=float(settings["temperature"]),
            ),
            base_response=response,
            initial_personas=response.personas,
        )
    except PersonaGraphAPIError as exc:
        st.error(str(exc))
        st.session_state["pg_chat_mode"] = "completed"
        return
    if updated is None:
        st.error("이어 말하기 결과를 만들지 못했습니다.")
        st.session_state["pg_chat_mode"] = "completed"
        return
    st.session_state["pg_current_response"] = updated
    st.session_state["pg_current_run_id"] = updated.run_id
    st.session_state["pg_pending_followup"] = None
    st.session_state["pg_chat_mode"] = "completed"
    st.rerun()
