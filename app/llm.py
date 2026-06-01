from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv

from app.model_catalog import DEFAULT_MODEL, resolve_model_route


@dataclass
class LLMResult:
    content: str
    used_llm: bool
    error: str | None = None


@dataclass
class LLMStructuredResult:
    value: Any | None
    content: str
    used_llm: bool
    error: str | None = None


class LLMClient:
    """Small LangChain-backed LLM wrapper with a graceful local fallback path."""

    def __init__(self, model: str | None = None, temperature: float = 0.35, enabled: bool = True):
        load_dotenv()
        route = resolve_model_route(model)
        self.model = route.id
        self.api_model = route.model
        self.provider = route.provider.id
        self.temperature = temperature
        self.api_key_env = route.provider.api_key_env
        self.api_key = os.getenv(route.provider.api_key_env)
        self.base_url = os.getenv(route.provider.base_url_env) or route.provider.default_base_url
        self.timeout = float(os.getenv("PERSONA_GRAPH_TIMEOUT", "20"))
        self.enabled = enabled and bool(self.api_key)
        self._client = None
        self._init_error: str | None = None

        if self.enabled:
            try:
                from langchain_openai import ChatOpenAI

                kwargs: dict[str, Any] = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                kwargs["timeout"] = self.timeout
                kwargs["model"] = self.api_model
                kwargs["temperature"] = self.temperature
                self._client = ChatOpenAI(**kwargs)
            except Exception as exc:  # pragma: no cover - depends on local package setup
                self.enabled = False
                self._init_error = str(exc)

    @property
    def unavailable_reason(self) -> str:
        if self._init_error:
            return self._init_error
        if not self.api_key:
            return f"{self.api_key_env} is not set."
        return "LLM client is disabled."

    def complete(self, system_prompt: str, user_prompt: str, temperature: float | None = None) -> LLMResult:
        if not self.enabled or self._client is None:
            return LLMResult(content="", used_llm=False, error=self.unavailable_reason)

        try:
            client = self._client
            if temperature is not None:
                client = self._client.bind(temperature=temperature)
            response = client.invoke(
                [
                    ("system", system_prompt),
                    ("human", user_prompt),
                ]
            )
            content = response.content or ""
            return LLMResult(content=content.strip(), used_llm=True)
        except Exception as exc:
            return LLMResult(content="", used_llm=False, error=str(exc))

    def complete_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        schema: Any,
        temperature: float | None = None,
    ) -> LLMStructuredResult:
        if not self.enabled or self._client is None:
            return LLMStructuredResult(value=None, content="", used_llm=False, error=self.unavailable_reason)

        try:
            client = self._client
            if temperature is not None:
                client = self._client.bind(temperature=temperature)
            response = client.with_structured_output(schema).invoke(
                [
                    ("system", system_prompt),
                    ("human", user_prompt),
                ]
            )
            return LLMStructuredResult(
                value=response,
                content=_structured_content(response),
                used_llm=True,
            )
        except Exception as exc:
            fallback = self.complete(system_prompt, user_prompt, temperature=temperature)
            return _structured_result_from_text(fallback, schema, str(exc))


def complete_structured(
    llm: Any,
    system_prompt: str,
    user_prompt: str,
    schema: Any,
    temperature: float | None = None,
) -> LLMStructuredResult:
    method = getattr(llm, "complete_structured", None)
    if callable(method):
        return method(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            temperature=temperature,
        )

    result = llm.complete(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        temperature=temperature,
    )
    return _structured_result_from_text(result, schema)


def _structured_result_from_text(
    result: LLMResult,
    schema: Any,
    fallback_error: str | None = None,
) -> LLMStructuredResult:
    if not result.used_llm or not result.content:
        return LLMStructuredResult(
            value=None,
            content=result.content,
            used_llm=result.used_llm,
            error=result.error or fallback_error,
        )

    parsed = parse_json_object(result.content)
    value = _validate_structured_value(schema, parsed)
    if value is None:
        return LLMStructuredResult(
            value=None,
            content=result.content,
            used_llm=True,
            error=result.error or fallback_error or "Unable to parse structured LLM output.",
        )
    return LLMStructuredResult(value=value, content=result.content, used_llm=True, error=result.error)


def _validate_structured_value(schema: Any, parsed: Any) -> Any | None:
    validator = getattr(schema, "model_validate", None)
    if not callable(validator):
        return parsed

    for candidate in _structured_candidates(schema, parsed):
        try:
            return validator(candidate)
        except (TypeError, ValueError):
            continue
    return None


def _structured_candidates(schema: Any, parsed: Any) -> list[Any]:
    candidates = [parsed]
    fields = getattr(schema, "model_fields", {})
    if len(fields) == 1 and not isinstance(parsed, dict):
        field_name = next(iter(fields))
        candidates.append({field_name: parsed})
    return candidates


def _structured_content(value: Any) -> str:
    if hasattr(value, "model_dump_json"):
        return value.model_dump_json()
    try:
        return json.dumps(value, ensure_ascii=False)
    except TypeError:
        return str(value)


def parse_json_object(raw: str) -> Any | None:
    """Extract JSON from a plain or fenced model response."""
    if not raw:
        return None

    text = raw.strip()
    if text.startswith("```"):
        lines = [line for line in text.splitlines() if not line.strip().startswith("```")]
        text = "\n".join(lines).strip()

    candidates = [text]
    if "[" in text and "]" in text:
        candidates.append(text[text.find("[") : text.rfind("]") + 1])
    if "{" in text and "}" in text:
        candidates.append(text[text.find("{") : text.rfind("}") + 1])

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None
