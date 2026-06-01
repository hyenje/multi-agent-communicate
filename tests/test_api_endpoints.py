import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.llm import LLMClient
from app.main import app


class APIEndpointTest(unittest.TestCase):
    def setUp(self):
        self.runs_dir = tempfile.TemporaryDirectory()
        self.memory_runs_dir = tempfile.TemporaryDirectory()
        self.previous_env = {
            key: os.environ.get(key)
            for key in (
                "PERSONA_GRAPH_RUNS_DIR",
                "PERSONA_GRAPH_MEMORY_RUNS_DIR",
                "PERSONA_GRAPH_MODEL",
                "PERSONA_GRAPH_AVAILABLE_MODELS",
                "PERSONA_GRAPH_DEFAULT_PROVIDER",
                "OPENAI_API_KEY",
                "OPENAI_BASE_URL",
                "UPSTAGE_API_KEY",
                "UPSTAGE_BASE_URL",
            )
        }
        os.environ["PERSONA_GRAPH_RUNS_DIR"] = self.runs_dir.name
        os.environ["PERSONA_GRAPH_MEMORY_RUNS_DIR"] = self.memory_runs_dir.name
        os.environ["PERSONA_GRAPH_MODEL"] = "openai:test-default"
        os.environ["PERSONA_GRAPH_AVAILABLE_MODELS"] = "openai:test-default,upstage:solar-pro3"
        self.client = TestClient(app)

    def tearDown(self):
        for key, value in self.previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.runs_dir.cleanup()
        self.memory_runs_dir.cleanup()

    def test_models_endpoint_exposes_server_catalog(self):
        response = self.client.get("/models")

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("openai:test-default", payload["default_model"])
        self.assertEqual(
            ["openai:test-default", "upstage:solar-pro3"],
            [model["id"] for model in payload["models"]],
        )
        self.assertEqual(
            ["OpenAI · test-default", "Upstage · solar-pro3"],
            [model["label"] for model in payload["models"]],
        )
        self.assertEqual(
            ["openai", "upstage"],
            [model["provider"] for model in payload["models"]],
        )

    def test_models_endpoint_includes_default_when_available_list_omits_it(self):
        os.environ["PERSONA_GRAPH_AVAILABLE_MODELS"] = "upstage:solar-pro3"

        response = self.client.get("/models")

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            ["openai:test-default", "upstage:solar-pro3"],
            [model["id"] for model in response.json()["models"]],
        )

    def test_llm_client_routes_prefixed_upstage_model(self):
        os.environ["UPSTAGE_API_KEY"] = "test-upstage-key"
        os.environ.pop("OPENAI_API_KEY", None)

        client = LLMClient(model="upstage:solar-pro3", enabled=False)

        self.assertEqual("upstage:solar-pro3", client.model)
        self.assertEqual("solar-pro3", client.api_model)
        self.assertEqual("upstage", client.provider)
        self.assertEqual("test-upstage-key", client.api_key)
        self.assertEqual("https://api.upstage.ai/v1", client.base_url)

    def test_llm_client_uses_langchain_chat_model(self):
        os.environ["OPENAI_API_KEY"] = "test-openai-key"
        os.environ["OPENAI_BASE_URL"] = "https://example.test/v1"

        class FakeChatOpenAI:
            instances = []

            def __init__(self, **kwargs):
                self.kwargs = kwargs
                self.messages = None
                self.bound_kwargs = None
                FakeChatOpenAI.instances.append(self)

            def bind(self, **kwargs):
                self.bound_kwargs = kwargs
                return self

            def invoke(self, messages):
                self.messages = messages
                return SimpleNamespace(content=" LangChain reply ")

        with patch("langchain_openai.ChatOpenAI", FakeChatOpenAI):
            client = LLMClient(model="openai:test-default", temperature=0.4)
            result = client.complete("system prompt", "user prompt", temperature=0.2)

        self.assertTrue(result.used_llm)
        self.assertEqual("LangChain reply", result.content)
        instance = FakeChatOpenAI.instances[0]
        self.assertEqual("test-default", instance.kwargs["model"])
        self.assertEqual("test-openai-key", instance.kwargs["api_key"])
        self.assertEqual("https://example.test/v1", instance.kwargs["base_url"])
        self.assertEqual(0.4, instance.kwargs["temperature"])
        self.assertEqual({"temperature": 0.2}, instance.bound_kwargs)
        self.assertEqual(
            [("system", "system prompt"), ("human", "user prompt")],
            instance.messages,
        )

    def test_llm_client_uses_langchain_structured_output(self):
        os.environ["OPENAI_API_KEY"] = "test-openai-key"

        class StructuredReply(BaseModel):
            answer: str

        class FakeChatOpenAI:
            instances = []

            def __init__(self, **kwargs):
                self.kwargs = kwargs
                self.schema = None
                self.messages = None
                self.bound_kwargs = None
                FakeChatOpenAI.instances.append(self)

            def bind(self, **kwargs):
                self.bound_kwargs = kwargs
                return self

            def with_structured_output(self, schema):
                self.schema = schema
                return self

            def invoke(self, messages):
                self.messages = messages
                return self.schema(answer="structured reply")

        with patch("langchain_openai.ChatOpenAI", FakeChatOpenAI):
            client = LLMClient(model="openai:test-default", temperature=0.4)
            result = client.complete_structured(
                "system prompt",
                "user prompt",
                StructuredReply,
                temperature=0.1,
            )

        self.assertTrue(result.used_llm)
        self.assertIsInstance(result.value, StructuredReply)
        self.assertEqual("structured reply", result.value.answer)
        instance = FakeChatOpenAI.instances[0]
        self.assertEqual({"temperature": 0.1}, instance.bound_kwargs)
        self.assertEqual(StructuredReply, instance.schema)
        self.assertEqual(
            [("system", "system prompt"), ("human", "user prompt")],
            instance.messages,
        )

    def test_solve_stream_saves_selected_allowed_model(self):
        with self.client.stream(
            "POST",
            "/solve/stream",
            json={
                "problem": "2주 안에 보여줄 AI 프로젝트 MVP를 정해야 한다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
                "model": "upstage:solar-pro3",
            },
        ) as response:
            self.assertEqual(200, response.status_code)
            events = self._read_events(response)

        self.assertEqual("final_response", events[-1]["type"])
        self.assertEqual("upstage:solar-pro3", events[-1]["response"]["model"])
        run_id = events[-1]["response"]["run_id"]

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        self.assertEqual("upstage:solar-pro3", detail.json()["model"])

    def test_solve_rejects_unavailable_model(self):
        response = self.client.post(
            "/solve",
            json={
                "problem": "2주 안에 보여줄 AI 프로젝트 MVP를 정해야 한다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
                "model": "unknown-model",
            },
        )

        self.assertEqual(422, response.status_code)
        self.assertIn("unknown-model", response.json()["detail"])

    def test_solve_stream_saves_final_response(self):
        with self.client.stream(
            "POST",
            "/solve/stream",
            json={
                "problem": "2주 안에 보여줄 AI 프로젝트 MVP를 정해야 한다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
            },
        ) as response:
            self.assertEqual(200, response.status_code)
            self.assertEqual(
                "application/x-ndjson",
                response.headers["content-type"].split(";")[0],
            )
            events = self._read_events(response)

        self.assertIn("personas_ready", [event["type"] for event in events])
        self.assertEqual("final_response", events[-1]["type"])
        run_id = events[-1]["response"]["run_id"]

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        self.assertEqual(run_id, detail.json()["run_id"])

    def test_solve_stream_saves_search_mode_off_record(self):
        with self.client.stream(
            "POST",
            "/solve/stream",
            json={
                "problem": "오늘 저녁 추천해줘",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
                "search_mode": "off",
            },
        ) as response:
            self.assertEqual(200, response.status_code)
            events = self._read_events(response)

        final_response = events[-1]["response"]
        run_id = final_response["run_id"]

        self.assertEqual("off", final_response["search_records"][0]["status"])

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        self.assertEqual("off", detail.json()["search_records"][0]["status"])

    def test_solve_stream_includes_reasoning_records(self):
        with self.client.stream(
            "POST",
            "/solve/stream",
            json={
                "problem": "2주 안에 보여줄 AI 프로젝트 MVP를 정해야 한다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
            },
        ) as response:
            self.assertEqual(200, response.status_code)
            events = self._read_events(response)

        final_response = events[-1]["response"]
        run_id = final_response["run_id"]

        self.assertEqual("skipped_no_llm", final_response["reasoning_records"][0]["status"])

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        self.assertEqual("skipped_no_llm", detail.json()["reasoning_records"][0]["status"])

    def test_solve_stream_includes_memory_records(self):
        with self.client.stream(
            "POST",
            "/solve/stream",
            json={
                "problem": "2주 안에 보여줄 AI 프로젝트 MVP를 정해야 한다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
            },
        ) as response:
            self.assertEqual(200, response.status_code)
            events = self._read_events(response)

        final_response = events[-1]["response"]
        run_id = final_response["run_id"]

        self.assertEqual("empty", final_response["memory_records"][0]["status"])

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        self.assertEqual("empty", detail.json()["memory_records"][0]["status"])

    def test_followup_stream_loads_and_updates_saved_run(self):
        created = self.client.post(
            "/solve",
            json={
                "problem": "저예산 Physical AI 프로젝트를 검증하고 싶다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
            },
        ).json()
        run_id = created["run_id"]

        with self.client.stream(
            "POST",
            f"/runs/{run_id}/messages/stream",
            json={
                "content": "예산은 100만 원이고 발표 장면이 중요하다.",
                "max_agents": 2,
                "use_llm": False,
            },
        ) as response:
            self.assertEqual(200, response.status_code)
            events = self._read_events(response)

        first_message_event = next(event for event in events if event["type"] == "agent_message")
        self.assertEqual("agent_message", events[0]["type"])
        self.assertEqual("user", first_message_event["message"]["stage"])
        self.assertEqual("final_response", events[-1]["type"])
        self.assertEqual(run_id, events[-1]["response"]["run_id"])

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        stages = [message["stage"] for message in detail.json()["messages"]]
        self.assertIn("user", stages)

    def test_followup_stream_uses_selected_allowed_model(self):
        created = self.client.post(
            "/solve",
            json={
                "problem": "저예산 Physical AI 프로젝트를 검증하고 싶다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
            },
        ).json()
        run_id = created["run_id"]

        with self.client.stream(
            "POST",
            f"/runs/{run_id}/messages/stream",
            json={
                "content": "모델 선택이 저장되는지 확인하고 싶다.",
                "max_agents": 2,
                "use_llm": False,
                "model": "upstage:solar-pro3",
            },
        ) as response:
            self.assertEqual(200, response.status_code)
            events = self._read_events(response)

        self.assertEqual("final_response", events[-1]["type"])
        self.assertEqual("upstage:solar-pro3", events[-1]["response"]["model"])

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        self.assertEqual("upstage:solar-pro3", detail.json()["model"])

    def test_followup_stream_saves_search_mode_off_record(self):
        created = self.client.post(
            "/solve",
            json={
                "problem": "저예산 Physical AI 프로젝트를 검증하고 싶다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
            },
        ).json()
        run_id = created["run_id"]

        with self.client.stream(
            "POST",
            f"/runs/{run_id}/messages/stream",
            json={
                "content": "오늘 기준으로 다시 봐줘.",
                "max_agents": 2,
                "use_llm": False,
                "search_mode": "off",
            },
        ) as response:
            self.assertEqual(200, response.status_code)
            events = self._read_events(response)

        final_response = events[-1]["response"]

        self.assertEqual("off", final_response["search_records"][-1]["status"])

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        self.assertEqual("off", detail.json()["search_records"][-1]["status"])

    def test_followup_stream_appends_reasoning_record(self):
        created = self.client.post(
            "/solve",
            json={
                "problem": "저예산 Physical AI 프로젝트를 검증하고 싶다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
            },
        ).json()
        run_id = created["run_id"]

        with self.client.stream(
            "POST",
            f"/runs/{run_id}/messages/stream",
            json={
                "content": "발표 장면을 더 선명하게 해줘.",
                "max_agents": 2,
                "use_llm": False,
            },
        ) as response:
            self.assertEqual(200, response.status_code)
            events = self._read_events(response)

        final_response = events[-1]["response"]

        self.assertEqual(2, len(final_response["reasoning_records"]))
        self.assertEqual("followup", final_response["reasoning_records"][-1]["phase"])

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        self.assertEqual(2, len(detail.json()["reasoning_records"]))

    def test_followup_stream_appends_memory_record(self):
        created = self.client.post(
            "/solve",
            json={
                "problem": "저예산 Physical AI 프로젝트를 검증하고 싶다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
            },
        ).json()
        run_id = created["run_id"]

        with self.client.stream(
            "POST",
            f"/runs/{run_id}/messages/stream",
            json={
                "content": "발표 장면을 더 선명하게 해줘.",
                "max_agents": 2,
                "use_llm": False,
            },
        ) as response:
            self.assertEqual(200, response.status_code)
            events = self._read_events(response)

        final_response = events[-1]["response"]

        self.assertEqual(2, len(final_response["memory_records"]))
        self.assertEqual("followup", final_response["memory_records"][-1]["phase"])

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        self.assertEqual(2, len(detail.json()["memory_records"]))

    def test_saved_run_without_reasoning_records_still_loads(self):
        created = self.client.post(
            "/solve",
            json={
                "problem": "저장 호환성을 확인한다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
            },
        ).json()
        run_id = created["run_id"]
        path = Path(self.runs_dir.name) / f"{run_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("reasoning_records", None)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        self.assertEqual([], detail.json()["reasoning_records"])

    def test_saved_run_without_memory_records_still_loads(self):
        created = self.client.post(
            "/solve",
            json={
                "problem": "저장 호환성을 확인한다.",
                "persona_count": 3,
                "debate_rounds": 1,
                "use_llm": False,
            },
        ).json()
        run_id = created["run_id"]
        path = Path(self.runs_dir.name) / f"{run_id}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data.pop("memory_records", None)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        detail = self.client.get(f"/runs/{run_id}")

        self.assertEqual(200, detail.status_code)
        self.assertEqual([], detail.json()["memory_records"])

    def _read_events(self, response):
        events = []
        for line in response.iter_lines():
            if not line:
                continue
            if isinstance(line, bytes):
                line = line.decode("utf-8")
            events.append(json.loads(line))
        return events


if __name__ == "__main__":
    unittest.main()
