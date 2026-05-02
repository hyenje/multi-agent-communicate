from __future__ import annotations

import base64
import html
import os
import re
import sys

from dotenv import load_dotenv

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st

from app.characters import CHARACTER_POOL
from app.schemas import Evaluation, SolveResponse
from app.storage import list_runs, load_run, save_run
from app.workflow import solve_problem


load_dotenv(os.path.join(ROOT_DIR, ".env"))

SAMPLE_PROBLEMS = {
    "Software Maestro 프로젝트 선정": "2026 Software Maestro를 목표로 2주 안에 보여줄 수 있는 AI 프로젝트 MVP를 정해야 한다. 포트폴리오 가치, 데모 안정성, 구현 난이도를 함께 고려해줘.",
    "캠퍼스 팀 프로젝트 리스크": "4명 팀이 3주 안에 AI 기반 학습 도우미를 만들어야 한다. 기능 욕심이 많고 역할 분담이 애매하다. 성공 가능성을 높이는 계획을 제안해줘.",
    "Physical AI 아이디어 검증": "저예산으로 Physical AI 프로젝트를 시작하고 싶다. 하드웨어 구매 전에 시뮬레이션과 소프트웨어 MVP로 검증할 방법을 찾아줘.",
}

STAGE_LABELS = {
    "persona_generation": "페르소나 생성",
    "moderator": "사회자 진행",
    "specialist": "전문가 의견",
    "debate": "상호 응답",
    "critic": "비판",
    "synthesizer": "최종 종합",
}

SOURCE_LABELS = {
    "llm": "LLM",
    "fallback": "기본 응답",
    "unknown": "알 수 없음",
}

HERO_IMAGE_PATH = os.path.join(
    ROOT_DIR, "assets", "hero", "personagraph-agent-network.png"
)
PERSONA_IMAGE_DIR = os.path.join(ROOT_DIR, "assets", "personas")
CHARACTER_IMAGE_PATHS = {
    "nori": os.path.join(PERSONA_IMAGE_DIR, "nori.png"),
    "orbit": os.path.join(PERSONA_IMAGE_DIR, "orbit.png"),
    "milmil": os.path.join(PERSONA_IMAGE_DIR, "milmil.png"),
    "sori": os.path.join(PERSONA_IMAGE_DIR, "sori.png"),
    "mori": os.path.join(PERSONA_IMAGE_DIR, "mori.png"),
    "gyeol": os.path.join(PERSONA_IMAGE_DIR, "gyeol.png"),
    "jari": os.path.join(PERSONA_IMAGE_DIR, "jari.png"),
    "sallycore": os.path.join(PERSONA_IMAGE_DIR, "sallycore.png"),
    "lumi": os.path.join(PERSONA_IMAGE_DIR, "lumi.png"),
    "haneul": os.path.join(PERSONA_IMAGE_DIR, "haneul.png"),
}
CHARACTERS_BY_ID = {character.id: character for character in CHARACTER_POOL}


st.set_page_config(page_title="PersonaGraph", page_icon="PG", layout="wide")


def average_score(evaluation: Evaluation) -> float:
    total = (
        evaluation.consistency
        + evaluation.specificity
        + evaluation.risk_awareness
        + evaluation.feasibility
    )
    return round(total / 4, 2)


@st.cache_data(show_spinner=False)
def image_data_uri(path: str) -> str:
    with open(path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("ascii")
    extension = os.path.splitext(path)[1].lower().lstrip(".") or "png"
    if extension == "jpg":
        extension = "jpeg"
    return f"data:image/{extension};base64,{encoded}"


def render_app_header() -> None:
    if not os.path.exists(HERO_IMAGE_PATH):
        st.title("PersonaGraph")
        st.caption(
            "문제를 입력하면 여러 AI 에이전트가 각자의 페르소나로 토론하고, 비판과 종합을 거쳐 최종 해결안을 만듭니다."
        )
        return

    hero_uri = image_data_uri(HERO_IMAGE_PATH)
    st.markdown(
        f"""
<style>
.pg-hero {{
    min-height: 18rem;
    border-radius: 8px;
    padding: clamp(1.4rem, 4vw, 3rem);
    margin-bottom: 1.25rem;
    display: flex;
    align-items: center;
    background-image:
        linear-gradient(90deg, rgba(255, 255, 255, 0.94) 0%, rgba(255, 255, 255, 0.80) 44%, rgba(255, 255, 255, 0.18) 100%),
        url("{hero_uri}");
    background-size: cover;
    background-position: center;
    border: 1px solid rgba(62, 72, 88, 0.08);
}}
.pg-hero-content {{
    max-width: 44rem;
}}
.pg-hero-kicker {{
    color: #2f80ed;
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0;
    margin-bottom: 0.4rem;
}}
.pg-hero h1 {{
    color: #1f2937;
    font-size: clamp(2.2rem, 4.5vw, 4rem);
    line-height: 1;
    margin: 0 0 0.75rem 0;
    letter-spacing: 0;
}}
.pg-hero p {{
    color: #374151;
    font-size: 1.04rem;
    line-height: 1.65;
    max-width: 38rem;
    margin: 0;
}}
.pg-network {{
    border: 1px solid rgba(47, 128, 237, 0.14);
    border-radius: 8px;
    background: #fbfcfd;
    padding: 0.9rem;
    margin: 0.4rem 0 1.4rem 0;
}}
.pg-network-row {{
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.6rem;
}}
.pg-agent-node {{
    display: flex;
    align-items: center;
    gap: 0.55rem;
    min-width: 11rem;
    max-width: 15rem;
    padding: 0.5rem 0.62rem;
    border-radius: 8px;
    border: 1px solid rgba(31, 41, 55, 0.08);
    background: rgba(255, 255, 255, 0.86);
}}
.pg-agent-node img {{
    width: 3.2rem;
    height: 4.7rem;
    border-radius: 10px;
    object-fit: contain;
    background: #f8f5ef;
    flex: 0 0 auto;
}}
.pg-agent-name {{
    color: #111827;
    font-size: 0.9rem;
    font-weight: 700;
    line-height: 1.25;
}}
.pg-agent-role {{
    color: #4b5563;
    font-size: 0.76rem;
    line-height: 1.3;
    margin-top: 0.16rem;
}}
.pg-connector {{
    width: 2.3rem;
    height: 1px;
    background: linear-gradient(90deg, rgba(47, 128, 237, 0.25), rgba(244, 143, 116, 0.72));
    position: relative;
}}
.pg-connector:after {{
    content: "";
    position: absolute;
    right: -0.05rem;
    top: -0.18rem;
    width: 0.38rem;
    height: 0.38rem;
    border-radius: 999px;
    background: #f48f74;
}}
.pg-portrait {{
    width: 7rem;
    height: 10.6rem;
    border-radius: 14px;
    object-fit: contain;
    background: #f8f5ef;
    border: 1px solid rgba(31, 41, 55, 0.10);
    box-shadow: 0 10px 24px rgba(31, 41, 55, 0.10);
}}
@media (max-width: 640px) {{
    .pg-hero {{
        min-height: 15rem;
        background-position: 58% center;
    }}
    .pg-agent-node {{
        min-width: 100%;
    }}
    .pg-connector {{
        display: none;
    }}
}}
</style>
<section class="pg-hero">
  <div class="pg-hero-content">
    <div class="pg-hero-kicker">multi-agent persona debate</div>
    <h1>PersonaGraph</h1>
    <p>문제를 입력하면 여러 AI 에이전트가 각자의 페르소나로 토론하고, 비판과 종합을 거쳐 최종 해결안을 만듭니다.</p>
  </div>
</section>
""",
        unsafe_allow_html=True,
    )


def render_evaluation(evaluation: Evaluation) -> None:
    st.subheader("평가 요약")
    metric_cols = st.columns(5)
    metric_cols[0].metric("평균", f"{average_score(evaluation)}/5")
    metric_cols[1].metric("일관성", f"{evaluation.consistency}/5")
    metric_cols[2].metric("구체성", f"{evaluation.specificity}/5")
    metric_cols[3].metric("리스크 반영", f"{evaluation.risk_awareness}/5")
    metric_cols[4].metric("실행 가능성", f"{evaluation.feasibility}/5")
    st.markdown(evaluation.overall_comment)
    if evaluation.improvement_suggestions:
        st.markdown("개선 제안")
        for suggestion in evaluation.improvement_suggestions:
            st.markdown(f"- {suggestion}")


def render_response(response: SolveResponse) -> None:
    status = "LLM API 사용" if response.used_llm else "로컬 폴백 사용"
    run_label = f" / run_id={response.run_id}" if response.run_id else ""
    st.success(f"토론 완료: {status} / model={response.model}{run_label}")
    render_agent_network(response.personas)

    left, right = st.columns([0.38, 0.62], gap="large")

    with left:
        st.subheader("생성된 페르소나")
        for persona in response.personas:
            with st.container(border=True):
                st.markdown(f"**{persona.name}**")
                st.caption(persona.role)
                if persona.character:
                    render_character(persona.character)
                st.write(persona.perspective)
                st.markdown("핵심 질문")
                for question in persona.priority_questions:
                    st.markdown(f"- {question}")

    with right:
        st.subheader("에이전트 대화창")
        render_message_timeline(response)

    st.divider()
    st.subheader("최종 결론")
    render_message_content(response.final_answer)
    st.divider()
    render_evaluation(response.evaluation)


def render_message_timeline(response: SolveResponse) -> None:
    personas_by_id = {persona.id: persona for persona in response.personas}
    current_section = ""

    for message in response.messages:
        persona = personas_by_id.get(message.agent_id)
        character = (
            CHARACTERS_BY_ID.get(persona.character.id, persona.character)
            if persona and persona.character
            else None
        )
        section_label = message_section_label(message)
        if section_label != current_section:
            st.markdown(f"#### 현재 라운드: {section_label}")
            current_section = section_label

        avatar = message_avatar(message, character)
        source = message.metadata.get("source", "unknown")
        stage_label = STAGE_LABELS.get(message.stage, message.stage)
        source_label = SOURCE_LABELS.get(source, source)
        round_value = message.metadata.get("round")
        round_label = f" · {round_value}라운드" if round_value else ""
        summary = summarize_message(message.content)

        with st.container(border=True):
            avatar_col, content_col = st.columns([0.14, 0.86], gap="small")
            with avatar_col:
                if avatar:
                    st.image(avatar, width=52)
                else:
                    st.markdown(f"**{message_avatar_text(message)}**")
            with content_col:
                st.markdown(f"**{message.agent_name}**")
                st.caption(f"{stage_label}{round_label} · {source_label} · {message.role}")
                st.markdown(f"**요약:** {html.escape(summary)}", unsafe_allow_html=True)
                with st.expander("전문 보기", expanded=False):
                    render_message_content(message.content)
        st.divider()

    fallback_errors = [
        message.metadata.get("error")
        for message in response.messages
        if message.metadata.get("source") == "fallback" and message.metadata.get("error")
    ]
    if fallback_errors:
        st.caption(f"기본 응답 사용 이유: {fallback_errors[0]}")


def message_section_label(message) -> str:
    if message.stage == "persona_generation":
        return "준비 단계"
    if message.stage == "moderator" and message.metadata.get("phase") == "opening":
        return "오프닝"
    if message.stage == "specialist":
        return "첫 의견"
    if message.stage in {"moderator", "debate"} and message.metadata.get("round"):
        return f"{message.metadata['round']}라운드 상호 응답"
    if message.stage == "critic":
        return "비판 검토"
    if message.stage == "synthesizer":
        return "최종 종합"
    return STAGE_LABELS.get(message.stage, message.stage)


def message_avatar(message, character) -> str | None:
    if character:
        image_path = CHARACTER_IMAGE_PATHS.get(character.id)
        if image_path and os.path.exists(image_path):
            return image_path
    return None


def message_avatar_text(message) -> str:
    return {
        "persona_generation": "PG",
        "moderator": "MOD",
        "critic": "CR",
        "synthesizer": "FIN",
    }.get(message.stage, message.agent_name[:2].upper())


def summarize_message(content: str, max_length: int = 115) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    for line in lines:
        summary = normalize_summary_text(line)
        if summary and not is_structural_heading(summary):
            return trim_summary(summary, max_length)
    return trim_summary(normalize_summary_text(content), max_length)


def normalize_summary_text(text: str) -> str:
    cleaned = re.sub(r"\*\*([^*]+?)\*\*", r"\1", text)
    cleaned = re.sub(r"^[-*]\s+", "", cleaned)
    cleaned = re.sub(r"^\d+[.)]\s+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def is_structural_heading(text: str) -> bool:
    headings = {
        "핵심 판단",
        "근거",
        "실행 제안",
        "주의할 점",
        "모순 또는 충돌",
        "약한 가정",
        "누락된 관점",
        "최종 통합 전에 고쳐야 할 점",
        "최종 결론",
        "선택한 방향",
        "실행 단계",
        "리스크와 대응",
        "다음 24시간 액션",
    }
    return text in headings


def trim_summary(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return f"{text[: max_length - 1].rstrip()}..."


def format_run_label(summary) -> str:
    preview = trim_summary(normalize_summary_text(summary.problem_preview), 80)
    created_at = summary.created_at.strftime("%Y-%m-%d %H:%M:%S")
    return f"{created_at} · {summary.average_score}/5 · {preview}"


def render_message_content(content: str) -> None:
    safe_content = html.escape(content)
    safe_content = re.sub(r"\*\*([^*\n]+?)\*\*", r"<strong>\1</strong>", safe_content)
    st.markdown(safe_content, unsafe_allow_html=True)


def render_character(character) -> None:
    display_character = CHARACTERS_BY_ID.get(character.id, character)
    image_path = CHARACTER_IMAGE_PATHS.get(display_character.id)

    if image_path and os.path.exists(image_path):
        image_col, detail_col = st.columns([0.32, 0.68], gap="small")
        with image_col:
            st.markdown(
                f'<img class="pg-portrait" src="{image_data_uri(image_path)}" alt="{html.escape(display_character.name)}">',
                unsafe_allow_html=True,
            )
        with detail_col:
            render_character_detail(display_character)
        return

    render_character_detail(display_character)


def render_agent_network(personas) -> None:
    if not personas:
        return

    nodes = []
    for index, persona in enumerate(personas):
        character = (
            CHARACTERS_BY_ID.get(persona.character.id, persona.character)
            if persona.character
            else None
        )
        image_path = CHARACTER_IMAGE_PATHS.get(character.id) if character else None
        image_html = ""
        if image_path and os.path.exists(image_path):
            image_html = (
                f'<img src="{image_data_uri(image_path)}" '
                f'alt="{html.escape(character.name)}">'
            )
        name = html.escape(persona.name)
        role = html.escape(character.archetype if character else persona.role)
        nodes.append(
            f"""
<div class="pg-agent-node">
  {image_html}
  <div>
    <div class="pg-agent-name">{name}</div>
    <div class="pg-agent-role">{role}</div>
  </div>
</div>
"""
        )
        if index < len(personas) - 1:
            nodes.append('<div class="pg-connector"></div>')

    st.markdown("#### 토론 네트워크")
    st.markdown(
        f"""
<div class="pg-network">
  <div class="pg-network-row">
    {''.join(nodes)}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_character_detail(character) -> None:
    st.markdown(
        f"""
<div style="
    border-left: 5px solid {character.accent_color};
    background: {character.color};
    padding: 0.75rem;
    border-radius: 0.5rem;
    margin: 0.55rem 0 0.75rem 0;
">
  <div style="display:flex; align-items:center; gap:0.65rem;">
    <div style="
        width:2.4rem;
        height:2.4rem;
        border-radius:50%;
        display:flex;
        align-items:center;
        justify-content:center;
        background:{character.accent_color};
        color:white;
        font-weight:700;
    ">{character.name[:1]}</div>
    <div>
      <div style="font-weight:700;">{character.name} · {character.archetype}</div>
      <div style="font-size:0.88rem;">{character.tagline}</div>
    </div>
  </div>
  <div style="font-size:0.86rem; margin-top:0.55rem;">상징: {character.symbol}</div>
  <div style="font-size:0.86rem; margin-top:0.25rem;">외형: {character.visual}</div>
  <div style="font-size:0.86rem; margin-top:0.25rem;">움직임: {character.motion}</div>
  <div style="font-size:0.86rem; margin-top:0.25rem;">촉감: {character.texture}</div>
  <div style="font-size:0.86rem; margin-top:0.25rem;">관계성: {character.relationship}</div>
  <div style="font-size:0.86rem; margin-top:0.25rem;">말투: {character.speech_style}</div>
</div>
""",
        unsafe_allow_html=True,
    )


render_app_header()

tab_new, tab_saved = st.tabs(["새 토론 실행", "저장된 토론 보기"])

with tab_new:
    with st.sidebar:
        st.header("실행 설정")
        persona_count = st.slider("페르소나 수", min_value=3, max_value=5, value=4)
        debate_rounds = st.slider("상호 응답 라운드", min_value=1, max_value=3, value=1)
        use_llm = st.toggle("LLM API 사용", value=True)
        model = st.text_input("모델명", value=os.getenv("PERSONA_GRAPH_MODEL", "gpt-5.4-mini"))
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.2, value=0.35, step=0.05)
        api_status = "설정됨" if os.getenv("OPENAI_API_KEY") else "미설정"
        st.info(f"OPENAI_API_KEY: {api_status}")

        st.divider()
        selected_sample = st.selectbox("샘플 시나리오", list(SAMPLE_PROBLEMS.keys()))
        load_sample = st.button("샘플 불러오기")

    if load_sample:
        st.session_state["problem_text"] = SAMPLE_PROBLEMS[selected_sample]

    problem = st.text_area(
        "해결할 문제",
        key="problem_text",
        height=160,
        placeholder="예: 2주 안에 데모 가능한 다중 에이전트 AI 프로젝트를 만들고 싶다...",
    )

    run = st.button("에이전트 토론 시작", type="primary", use_container_width=True)

    if run:
        if len(problem.strip()) < 5:
            st.warning("문제를 조금 더 구체적으로 입력해주세요.")
            st.stop()

        with st.spinner("PersonaGraph가 에이전트 토론을 진행 중입니다..."):
            response = solve_problem(
                problem=problem.strip(),
                persona_count=persona_count,
                debate_rounds=debate_rounds,
                use_llm=use_llm,
                model=model.strip() or None,
                temperature=temperature,
            )
            response = save_run(response)

        st.session_state["last_response"] = response
        render_response(response)
    elif st.session_state.get("last_response"):
        render_response(st.session_state["last_response"])
    else:
        st.info("왼쪽에서 샘플을 불러오거나 직접 문제를 입력한 뒤 에이전트 토론을 시작하세요.")

with tab_saved:
    summaries = list_runs()
    if not summaries:
        st.info("아직 저장된 토론 로그가 없습니다.")
    else:
        labels = {
            format_run_label(summary): summary.run_id
            for summary in summaries
        }
        selected_label = st.selectbox("저장된 실행", list(labels.keys()))
        selected_run_id = labels[selected_label]
        try:
            saved_response = load_run(selected_run_id)
        except FileNotFoundError:
            st.error("선택한 로그를 찾을 수 없습니다.")
        else:
            render_response(saved_response)
