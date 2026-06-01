from __future__ import annotations

from pydantic import BaseModel, Field

from app.llm import LLMClient, complete_structured
from app.schemas import AgentMessage, Persona


class PersonaListOutput(BaseModel):
    personas: list[Persona] = Field(default_factory=list)


DEFAULT_PERSONAS = [
    Persona(
        id="product_strategist",
        name="제품 전략가",
        role="MVP 범위와 사용자 가치를 정리하는 역할",
        perspective="가장 작은 데모로 실제 가치를 증명하는 데 집중합니다.",
        priority_questions=["첫 사용자는 누구인가?", "성공 순간은 무엇인가?", "무엇을 과감히 줄일 수 있는가?"],
    ),
    Persona(
        id="systems_engineer",
        name="시스템 엔지니어",
        role="아키텍처와 안정성을 검토하는 역할",
        perspective="구현 가능성, 인터페이스, 실패 지점, 운영 단순성을 점검합니다.",
        priority_questions=["워크플로는 어디서 실패할 수 있는가?", "어떤 상태를 로그로 남겨야 하는가?", "어떻게 테스트할 것인가?"],
    ),
    Persona(
        id="ai_researcher",
        name="AI 연구자",
        role="추론 품질과 평가 기준을 설계하는 역할",
        perspective="프롬프트 구조, 에이전트 역할, 비판 루프, 결과 평가를 개선합니다.",
        priority_questions=["이 역할이 추론 품질을 높이는가?", "약한 답변은 어떻게 감지할 것인가?", "무엇을 평가 지표로 삼을 것인가?"],
    ),
    Persona(
        id="demo_director",
        name="데모 디렉터",
        role="발표와 포트폴리오 흐름을 설계하는 역할",
        perspective="결과물을 명확하고 인상적이며 안정적인 데모로 보이게 만듭니다.",
        priority_questions=["청중이 처음 봐야 할 장면은 무엇인가?", "어떤 시나리오가 아이디어를 가장 잘 보여주는가?", "어떤 화면을 증거로 남길 것인가?"],
    ),
    Persona(
        id="risk_analyst",
        name="리스크 분석가",
        role="리스크, 비용, 범위를 통제하는 역할",
        perspective="숨은 복잡도, 일정 함정, 2주 MVP를 위협하는 결정을 찾아냅니다.",
        priority_questions=["범위가 과한 부분은 무엇인가?", "외부 서비스에 의존하는 부분은 무엇인가?", "반드시 폴백이 필요한 부분은 무엇인가?"],
    ),
]


class PersonaGenerator:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def generate(self, problem: str, count: int, search_context: str | None = None) -> tuple[list[Persona], AgentMessage]:
        context_block = f"\n참고 자료 (페르소나 설계에 활용하세요):\n{search_context}\n" if search_context else ""
        prompt = f"""
이 문제를 해결하기 위한 상호보완적인 AI 에이전트 페르소나 {count}개를 만드세요.

문제:
{problem}
{context_block}
반드시 personas 필드를 가진 JSON 객체만 반환하세요.
personas의 각 항목은 다음 필드를 포함해야 합니다.
- id: snake_case 형식의 고유 ID
- name: 짧은 한국어 에이전트 이름
- role: 한 문장의 한국어 역할 설명
- perspective: 한 문장의 한국어 관점 설명
- priority_questions: 한국어로 된 구체적 질문 2~4개

출력 규칙:
- 한국어 사용자를 위한 자연스러운 한국어로 작성하세요.
- OpenAI, API, MVP처럼 필요한 고유명사나 기술 약어 외에는 영어를 쓰지 마세요.
"""
        result = complete_structured(
            self.llm,
            system_prompt="당신은 한국어 다중 에이전트 팀을 설계합니다. 엄격한 JSON만 반환하세요.",
            user_prompt=prompt,
            schema=PersonaListOutput,
            temperature=0.25,
        )

        personas = self._from_output(result.value, count) if result.used_llm else []
        if not personas:
            personas = DEFAULT_PERSONAS[:count]

        content = "\n\n".join(
            f"{idx}. {persona.name} ({persona.role})\n- 관점: {persona.perspective}\n- 핵심 질문: "
            + ", ".join(persona.priority_questions)
            for idx, persona in enumerate(personas, start=1)
        )
        message = AgentMessage(
            stage="persona_generation",
            agent_id="persona_generator",
            agent_name="페르소나 생성기",
            role="문제에 맞는 에이전트 팀을 생성하는 역할",
            content=content,
            metadata={"source": "llm" if result.used_llm and personas else "fallback", "error": result.error},
        )
        return personas, message

    def _from_output(self, output: object, count: int) -> list[Persona]:
        if not isinstance(output, PersonaListOutput):
            return []

        personas: list[Persona] = []
        for index, item in enumerate(output.personas[:count], start=1):
            try:
                personas.append(
                    Persona(
                        id=(item.id or f"persona_{index}").strip().replace(" ", "_").lower(),
                        name=item.name.strip(),
                        role=item.role.strip(),
                        perspective=item.perspective.strip(),
                        priority_questions=[q.strip() for q in item.priority_questions if q.strip()][:4],
                    )
                )
            except (TypeError, ValueError):
                continue
        return personas
