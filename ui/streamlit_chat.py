from __future__ import annotations

import html
from datetime import timedelta

import streamlit as st

from app.schemas import SearchRecord, SolveResponse
from ui.streamlit_browser import scroll_chat_to_bottom
from ui.streamlit_common import (
    avatar_markup,
    character_class,
    character_for_persona,
    message_content_html,
    normalize_summary_text,
    stage_meta_label,
    system_avatar_label,
    trim_summary,
)


def initial_problem_item(response: SolveResponse) -> dict:
    return {
        "kind": "user",
        "name": "나",
        "meta": "처음 입력한 문제",
        "content": response.problem,
    }

def message_item(message, personas_by_id: dict) -> dict | None:
    if message.stage == "persona_generation":
        return None
    if message.stage == "critic":
        return None
    if message.stage == "user":
        return {
            "kind": "user",
            "name": "나",
            "meta": "내 의견",
            "content": message.content,
        }

    persona = personas_by_id.get(message.agent_id)
    character = character_for_persona(persona)
    is_persona_message = message.stage in {"specialist", "debate"}
    kind = "agent" if is_persona_message else "system"
    fallback = system_avatar_label(message.agent_id, message.agent_name, message.stage)
    return {
        "kind": kind,
        "name": message.agent_name,
        "meta": stage_meta_label(message),
        "content": message.content,
        "character": character,
        "avatar_name": message.agent_name,
        "avatar_fallback": fallback,
        "stage": message.stage,
        "round": message.metadata.get("round"),
        "phase": message.metadata.get("phase"),
        "groupable": message.stage in {"specialist", "debate"},
    }

def chat_thread_items(response: SolveResponse, confirmed_settings: dict | None = None) -> list[dict]:
    personas_by_id = {persona.id: persona for persona in response.personas}
    items = [initial_problem_item(response)]
    placed_search_indexes: set[int] = set()
    round_searches: dict[tuple[str, int | None], list[tuple[int, SearchRecord]]] = {}
    followup_searches: list[tuple[int, SearchRecord]] = []

    for index, record in enumerate(response.search_records):
        if record.phase == "initial" and index not in placed_search_indexes:
            items.append(search_record_activity_item(record))
            placed_search_indexes.add(index)
        elif record.phase == "followup":
            followup_searches.append((index, record))
        elif record.phase in {"debate_round", "evaluation_extra_round"}:
            round_searches.setdefault((record.phase, record.round_number), []).append((index, record))

    followup_search_index = 0
    for message in response.messages:
        for index, record in searches_before_message(message, round_searches):
            if index not in placed_search_indexes:
                items.append(search_record_activity_item(record))
                placed_search_indexes.add(index)
        item = message_item(message, personas_by_id)
        if item:
            items.append(item)
        if message.stage == "user" and followup_search_index < len(followup_searches):
            index, record = followup_searches[followup_search_index]
            if index not in placed_search_indexes:
                items.append(search_record_activity_item(record))
                placed_search_indexes.add(index)
            followup_search_index += 1
    for index, record in enumerate(response.search_records):
        if index not in placed_search_indexes:
            items.append(search_record_activity_item(record))
    return items

def searches_before_message(
    message,
    round_searches: dict[tuple[str, int | None], list[tuple[int, SearchRecord]]],
) -> list[tuple[int, SearchRecord]]:
    round_number = message.metadata.get("round")
    if round_number is None:
        return []
    try:
        normalized_round = int(round_number)
    except (TypeError, ValueError):
        return []

    phase = message.metadata.get("phase")
    if phase == "evaluation_extra_round":
        key = ("evaluation_extra_round", normalized_round)
    elif message.stage in {"moderator", "debate"}:
        key = ("debate_round", normalized_round)
    else:
        return []
    return round_searches.pop(key, [])

def grouped_chat_thread_items(
    response: SolveResponse,
    confirmed_settings: dict | None = None,
) -> list[dict]:
    return group_agent_items(chat_thread_items(response, confirmed_settings=confirmed_settings))

def group_agent_items(
    items: list[dict],
    expand_last_group: bool = False,
    expanded_group_key: str | None = None,
) -> list[dict]:
    grouped_items: list[dict] = []
    agent_group: list[dict] = []
    group_index = 0

    def flush_group() -> None:
        nonlocal agent_group, group_index
        if not agent_group:
            return
        grouped_items.append(agent_group_item(agent_group, group_index))
        group_index += 1
        agent_group = []

    for item in items:
        if item.get("groupable"):
            agent_group.append(item)
        else:
            flush_group()
            grouped_items.append(item)
    flush_group()

    if expanded_group_key is not None:
        for item in grouped_items:
            if item.get("kind") == "agent_group":
                item["expanded"] = item.get("group_key") == expanded_group_key
    elif expand_last_group:
        for item in reversed(grouped_items):
            if item.get("kind") == "agent_group":
                item["expanded"] = True
                break
    return grouped_items

def agent_group_item(agent_items: list[dict], group_index: int) -> dict:
    first_item = agent_items[0]
    stage = first_item.get("stage")
    round_number = first_item.get("round")
    phase = first_item.get("phase")
    speaker_count = len(agent_items)

    if stage == "specialist":
        title = "Agent 첫 의견"
    elif phase == "user_response":
        title = "후속 Agent 답변"
    elif round_number:
        title = f"{round_number}라운드 Agent 발화"
    else:
        title = "Agent 발화"

    return {
        "kind": "agent_group",
        "items": agent_items,
        "title": title,
        "meta": f"{speaker_count}개 발화",
        "group_id": group_index,
        "group_key": agent_group_key(first_item, group_index),
        "expanded": False,
    }

def agent_group_key(item: dict, group_index: int | None = None) -> str:
    stage = str(item.get("stage") or "agent")
    round_number = item.get("round")
    phase = str(item.get("phase") or "")
    if stage == "specialist":
        return "specialist_initial"
    if round_number:
        return f"{stage}_round_{round_number}"
    if group_index is not None:
        return f"{stage}_{phase}_group_{group_index}"
    return f"{stage}_{phase}"

def render_chat_bubble(item: dict) -> None:
    kind = item.get("kind", "agent")
    name = str(item.get("name", "Agent"))
    meta = str(item.get("meta", ""))
    content = str(item.get("content", ""))
    character = item.get("character")
    character_css = character_class(character)

    if kind == "user":
        meta_markup = ""
        if item.get("show_meta"):
            meta_markup = (
                f'<div class="pg-message-meta"><span class="pg-message-name">{html.escape(name)}</span>'
                f"<span>{html.escape(meta)}</span></div>"
            )
        st.markdown(
            (
                '<div class="pg-chat-shell">'
                '<div class="pg-chat-row pg-chat-row-user">'
                '<div class="pg-chat-bubble pg-chat-bubble-user">'
                f"{meta_markup}"
                f'<div class="pg-message-content">{message_content_html(content)}</div>'
                "</div>"
                "</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        return

    bubble_class = "pg-chat-bubble-system" if kind == "system" else "pg-chat-bubble-agent"
    row_class = "pg-chat-row-system" if kind == "system" else "pg-chat-row-agent"
    content_markup = (
        moderator_message_html(content)
        if item.get("stage") == "moderator"
        else message_content_html(content)
    )
    avatar = avatar_markup(
        str(item.get("avatar_name", name)),
        character,
        str(item.get("avatar_fallback", "")),
    )
    st.markdown(
        f"""
<div class="pg-chat-shell">
<div class="pg-chat-row {row_class}">
  <div class="pg-chat-avatar-wrap">{avatar}</div>
  <div class="pg-chat-bubble {bubble_class} {character_css}">
    <div class="pg-message-meta"><span class="pg-message-name">{html.escape(name)}</span><span>{html.escape(meta)}</span></div>
    {content_markup}
  </div>
</div>
</div>
""",
        unsafe_allow_html=True,
    )

def moderator_summary(content: str, max_length: int = 90) -> str:
    cleaned = normalize_summary_text(content)
    if len(cleaned) <= max_length:
        return cleaned

    first_boundary = -1
    for marker in ("다.", "요.", ". ", "? ", "! "):
        index = cleaned.find(marker)
        while 0 <= index < max_length:
            boundary = index + len(marker)
            if boundary >= 24 and (first_boundary == -1 or boundary < first_boundary):
                first_boundary = boundary
                break
            index = cleaned.find(marker, index + len(marker))

    if first_boundary != -1:
        return cleaned[:first_boundary].strip()
    return trim_summary(cleaned, max_length)

def moderator_message_html(content: str) -> str:
    summary = moderator_summary(content)
    normalized = normalize_summary_text(content)
    if normalized == summary:
        return message_content_html(content)
    return f"""
<div class="pg-moderator-preview">{message_content_html(summary)}</div>
<details class="pg-moderator-full">
  <summary>전문 보기</summary>
  <div class="pg-moderator-full-body">{message_content_html(content)}</div>
</details>
"""

def render_agent_group(item: dict) -> None:
    title = str(item.get("title", "Agent 발화"))
    meta = str(item.get("meta", ""))
    label = f"{title} · {meta}" if meta else title
    open_attribute = " open" if item.get("expanded", False) else ""

    rows = [
        f"""
<details class="pg-agent-group-details"{open_attribute}>
  <summary>{html.escape(label)}</summary>
  <div class="pg-agent-group-content">
    <span class="pg-agent-group-content-anchor"></span>
"""
    ]
    for agent_item in item.get("items", []):
        name = str(agent_item.get("name", "Agent"))
        item_meta = str(agent_item.get("meta", ""))
        content = str(agent_item.get("content", ""))
        character = agent_item.get("character")
        character_css = character_class(character)
        avatar = avatar_markup(
            str(agent_item.get("avatar_name", name)),
            character,
            str(agent_item.get("avatar_fallback", "")),
        )
        rows.append(
            f"""
<div class="pg-agent-group-message">
  <div class="pg-chat-avatar-wrap">{avatar}</div>
  <div class="pg-agent-group-body pg-chat-bubble-agent {character_css}">
    <div class="pg-message-meta"><span class="pg-message-name">{html.escape(name)}</span><span>{html.escape(item_meta)}</span></div>
    {message_content_html(content)}
  </div>
</div>
"""
        )
    rows.append(
        """
  </div>
</details>
"""
    )
    st.markdown("\n".join(rows), unsafe_allow_html=True)

def render_final_answer(response: SolveResponse) -> None:
    if not response.final_answer.strip():
        return
    st.markdown(
        f"""
<div class="pg-final-answer-only">
  {message_content_html(response.final_answer)}
</div>
""",
        unsafe_allow_html=True,
    )

def work_history_items(
    response: SolveResponse,
    confirmed_settings: dict | None = None,
) -> list[dict]:
    return [
        item
        for item in grouped_chat_thread_items(response, confirmed_settings=confirmed_settings)
        if include_work_history_item(item)
    ]

def include_work_history_item(item: dict) -> bool:
    if item.get("kind") == "user" and item.get("meta") == "처음 입력한 문제":
        return False
    if item.get("stage") == "synthesizer":
        return False
    return True

def render_work_history(
    response: SolveResponse,
    confirmed_settings: dict | None = None,
) -> None:
    items = work_history_items(response, confirmed_settings=confirmed_settings)
    if not items:
        return

    with st.expander(response_work_duration_label(response), expanded=False):
        st.markdown('<span class="pg-work-history-anchor"></span>', unsafe_allow_html=True)
        for item in items:
            render_chat_item(item)

def response_work_duration_label(response: SolveResponse) -> str:
    return format_activity_duration(response_work_elapsed_ms(response))

def response_work_elapsed_ms(response: SolveResponse) -> int:
    starts = []
    for record in response.search_records:
        starts.append(record.created_at - timedelta(milliseconds=record.elapsed_ms or 0))
    for record in response.reasoning_records:
        starts.append(record.created_at)
    for record in response.memory_records:
        starts.append(record.created_at)
    if starts:
        elapsed = response.created_at - min(starts)
        return max(0, int(elapsed.total_seconds() * 1000))
    return sum(max(0, int(record.elapsed_ms or 0)) for record in response.search_records)

def search_record_activity_item(record: SearchRecord) -> dict:
    root_queries = [node.query for node in record.query_tree[:3]] or list(record.queries[:3])
    return {
        "kind": "activity",
        "source": "search",
        "phase": record.phase,
        "round_number": record.round_number,
        "mode": record.mode,
        "provider": record.provider or "search",
        "status": record.status,
        "queries": list(record.queries),
        "query_count": len(record.queries),
        "root_queries": root_queries,
        "result_count": record.result_count,
        "elapsed_ms": record.elapsed_ms,
        "error": record.error,
        "running": False,
    }

def format_activity_duration(elapsed_ms: int | float | None) -> str:
    elapsed = int(elapsed_ms or 0)
    if elapsed <= 0:
        return "작업 기록"
    if elapsed < 1000:
        return "1s 미만 동안 작업"
    total_seconds = max(1, round(elapsed / 1000))
    minutes, seconds = divmod(total_seconds, 60)
    if minutes:
        return f"{minutes}m {seconds}s 동안 작업"
    return f"{seconds}s 동안 작업"

def search_activity_title(item: dict) -> str:
    if item.get("running"):
        return "작업 중"
    return format_activity_duration(item.get("elapsed_ms"))

def search_activity_summary(item: dict) -> str:
    status = str(item.get("status") or "")
    event_type = str(item.get("event_type") or "")
    if item.get("running"):
        if event_type == "search_queries":
            return "웹 검색 중"
        return "검색 필요 여부 확인 중"
    if status == "fetched":
        return "검색 사용"
    if status == "no_results":
        return "검색 결과 없음"
    if status == "not_needed":
        return "검색 생략"
    if status == "off":
        return "검색 꺼짐"
    if status == "error":
        return "검색 오류"
    return "검색 확인"

def search_activity_phase_label(item: dict) -> str:
    phase = item.get("phase")
    round_number = item.get("round_number")
    if phase == "debate_round":
        return f"{round_number}라운드 검색" if round_number else "라운드 검색"
    if phase == "evaluation_extra_round":
        return f"{round_number}라운드 보강 검색" if round_number else "보강 검색"
    if phase == "followup":
        return "후속 검색"
    return "초기 검색"

def render_activity_item(item: dict) -> None:
    if item.get("source") != "search":
        return
    title = search_activity_title(item)
    summary = search_activity_summary(item)
    phase = search_activity_phase_label(item)
    mode = str(item.get("mode") or "auto")
    provider = str(item.get("provider") or "search")
    status = str(item.get("status") or "")
    result_count = int(item.get("result_count") or 0)
    error = str(item.get("error") or "")
    queries = [str(query) for query in item.get("queries", []) if str(query).strip()]
    root_queries = [str(query) for query in item.get("root_queries", []) if str(query).strip()]
    representative_queries = root_queries[:3] or queries[:3]
    query_count = int(item.get("query_count") or len(queries))
    open_attribute = " open" if item.get("running") else ""
    rows = [
        '<div class="pg-chat-shell pg-activity-shell">',
        '<div class="pg-activity-row">',
        f'<details class="pg-work-activity"{open_attribute}>',
        '<summary>',
        f'<span class="pg-work-title">{html.escape(title)}</span>',
        f'<span class="pg-work-summary">{html.escape(summary)}</span>',
        '<span class="pg-work-chevron">›</span>',
        '</summary>',
        '<div class="pg-work-body">',
        '<div class="pg-work-step">',
        '<div class="pg-work-step-title">검색 판단</div>',
        f'<div class="pg-work-step-detail">{html.escape(phase)} · {html.escape(mode)} · {html.escape(provider)}</div>',
        '</div>',
    ]
    if representative_queries:
        rows.extend(
            [
                '<div class="pg-work-step">',
                '<div class="pg-work-step-title">대표 검색어</div>',
                '<div class="pg-work-query-list">',
                *[
                    f'<span class="pg-work-query">{html.escape(query)}</span>'
                    for query in representative_queries
                ],
                '</div>',
                '</div>',
            ]
        )
    if status == "fetched":
        rows.extend(
            [
                '<div class="pg-work-step">',
                '<div class="pg-work-step-title">검색 결과</div>',
                f'<div class="pg-work-step-detail">총 {query_count}개 검색어를 확인했고, 중복 제거 후 {result_count}개 snippet을 사용했습니다.</div>',
                '</div>',
            ]
        )
    elif status == "no_results":
        rows.extend(
            [
                '<div class="pg-work-step">',
                '<div class="pg-work-step-title">검색 결과</div>',
                '<div class="pg-work-step-detail">검색은 수행했지만 사용할 결과가 없었습니다.</div>',
                '</div>',
            ]
        )
    elif status == "not_needed":
        rows.extend(
            [
                '<div class="pg-work-step">',
                '<div class="pg-work-step-title">결정</div>',
                '<div class="pg-work-step-detail">현재 질문은 내부 토론만으로 답해도 충분하다고 판단했습니다.</div>',
                '</div>',
            ]
        )
    elif status == "off":
        rows.extend(
            [
                '<div class="pg-work-step">',
                '<div class="pg-work-step-title">결정</div>',
                '<div class="pg-work-step-detail">사용자 설정에 따라 외부 검색 없이 진행했습니다.</div>',
                '</div>',
            ]
        )
    elif status == "error":
        rows.extend(
            [
                '<div class="pg-work-step">',
                '<div class="pg-work-step-title">오류</div>',
                f'<div class="pg-work-step-detail">{html.escape(error or "검색 없이 대화를 계속 진행했습니다.")}</div>',
                '</div>',
            ]
        )
    elif item.get("running"):
        rows.extend(
            [
                '<div class="pg-work-step">',
                '<div class="pg-work-step-title">진행 중</div>',
                '<div class="pg-work-step-detail">검색 판단과 검색어 정리를 진행하고 있습니다.</div>',
                '</div>',
            ]
        )
    rows.extend(['</div>', '</details>', '</div>', '</div>'])
    st.markdown("".join(rows), unsafe_allow_html=True)

def render_chat_item(item: dict) -> None:
    if item.get("kind") == "activity":
        render_activity_item(item)
    elif item.get("kind") == "agent_group":
        render_agent_group(item)
    else:
        render_chat_bubble(item)

def render_chat_items(items: list[dict]) -> None:
    for item in group_agent_items(items):
        render_chat_item(item)

def render_chat_thread(
    response: SolveResponse,
    include_anchor: bool = True,
    confirmed_settings: dict | None = None,
) -> None:
    render_chat_bubble(initial_problem_item(response))
    render_work_history(response, confirmed_settings=confirmed_settings)
    render_final_answer(response)
    if include_anchor:
        st.markdown('<div id="pg-chat-bottom" class="pg-scroll-anchor"></div>', unsafe_allow_html=True)
        scroll_chat_to_bottom()

def render_pending_problem_thread(problem: str) -> None:
    render_chat_bubble(
        {
            "kind": "user",
            "name": "나",
            "meta": "처음 입력한 문제",
            "content": problem,
        }
    )

def render_empty_state() -> None:
    st.markdown(
        """
<div class="pg-empty-state">
  <div class="pg-empty-title">어떤 문제를 고민중이신가요?</div>
  <div class="pg-empty-subtitle">여러 관점이 필요한 결정을 함께 정리해드릴게요.</div>
</div>
""",
        unsafe_allow_html=True,
    )
