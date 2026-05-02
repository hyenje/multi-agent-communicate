# PersonaGraph

문제를 입력하면 여러 AI Agent가 각자 다른 페르소나와 역할로 토론하고, 비판과 종합을 거쳐 최종 해결안을 만드는 2주 MVP 프로젝트입니다.

## MVP Flow

1. 사용자가 문제를 입력합니다.
2. Persona Generator가 필요한 페르소나 3~5개를 생성합니다.
3. 미리 정의된 데포르메 피규어형 페르소나 이미지와 성격 중 하나를 각 페르소나에 임의로 배정합니다.
4. Moderator Agent가 의제, 발언 순서, 상호 응답 규칙을 안내합니다.
5. Specialist Agent들이 자기 관점으로 첫 의견을 제시합니다.
6. Moderator Agent가 응답 라운드의 논점을 좁히고, Specialist Agent들이 앞선 발언에 직접 동의, 반박, 보완합니다.
7. Critic Agent가 전체 토론의 모순, 약점, 누락을 지적합니다.
8. Synthesizer Agent가 최종 답변을 통합합니다.
9. Evaluator Agent가 최종 결과를 점수와 총평으로 평가합니다.
10. Streamlit UI에서 배너, 데포르메 페르소나 캐릭터, 에이전트 토론 네트워크, 대화창형 토론 로그, 최종 결론, 평가 요약을 표시하고 실행 결과를 저장합니다.

## Setup

```bash
cd persona-graph
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env`에 LLM API 키를 설정합니다.

```bash
OPENAI_API_KEY=your_api_key_here
PERSONA_GRAPH_MODEL=gpt-5.4-mini
```

`OPENAI_BASE_URL`을 설정하면 OpenAI-compatible provider도 사용할 수 있습니다.

API 키가 없거나 호출이 실패하면 로컬 폴백 응답으로 전체 워크플로가 계속 진행됩니다.

## Run API

```bash
cd persona-graph
uvicorn app.main:app --reload --port 8000
```

API 문서:

- http://localhost:8000/docs

예시 요청:

```bash
curl -X POST http://localhost:8000/solve \
  -H "Content-Type: application/json" \
  -d '{
    "problem": "2주 안에 보여줄 수 있는 AI 프로젝트 MVP를 정해야 한다.",
    "persona_count": 4,
    "debate_rounds": 1,
    "use_llm": true
  }'
```

저장된 실행 목록:

```bash
curl http://localhost:8000/runs
```

특정 실행 불러오기:

```bash
curl http://localhost:8000/runs/<run_id>
```

## Run UI

```bash
cd persona-graph
streamlit run ui/streamlit_app.py
```

Streamlit 기본 주소:

- http://localhost:8501

UI는 `새 토론 실행` 탭과 `저장된 토론 보기` 탭으로 구성됩니다. 새 토론은 실행 후 `data/runs/`에 JSON으로 저장됩니다.

## Project Structure

```text
persona-graph/
  app/
    main.py
    agents/
      persona_generator.py
      moderator.py
      specialist.py
      critic.py
      synthesizer.py
      evaluator.py
      supervisor.py
    llm.py
    characters.py
    schemas.py
    storage.py
    workflow.py
  ui/
    streamlit_app.py
  assets/
    hero/
      personagraph-agent-network.png
    personas/
      persona-deformed-sheet.png
      nori.png
      orbit.png
      ...
    characters/
      sallycore-companion.png
  data/
    runs/
  docs/
    character_design.md
    project_brief.md
    demo_scenarios.md
  README.md
```

## Next Milestones

- 샘플 문제 3개로 데모 로그 품질 확인
- 비교 모드: 일반 LLM 답변 vs PersonaGraph 답변
- 발표용 시나리오와 스크린샷 정리
