from __future__ import annotations

import os
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import parse_qs, unquote, urlencode, urlparse
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from app.llm import LLMClient, complete_structured
from app.prompt_examples import SEARCH_QUERY_REWRITE_EXAMPLES
from app.schemas import SearchQueryNode


ROOT_QUERY_LIMIT = 3
CHILD_QUERY_LIMIT = 3
QUERY_RESULT_LIMIT = 3
CONTEXT_SNIPPET_LIMIT = 18


@dataclass
class Classification:
    needs_search: bool
    queries: list[str] = field(default_factory=list)
    reason: str = ""


@dataclass
class SearchTreeResult:
    context: str | None
    queries: list[str]
    query_tree: list[SearchQueryNode]
    result_count: int


class SearchClassificationOutput(BaseModel):
    needs_search: bool
    queries: list[str] = Field(default_factory=list)


class SearchQueriesOutput(BaseModel):
    queries: list[str] = Field(default_factory=list)


class SearchClient:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("TAVILY_API_KEY")
        self._client = None
        if self.api_key:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self.api_key)
            except Exception:
                pass

    @property
    def enabled(self) -> bool:
        return True

    @property
    def provider(self) -> str:
        return "tavily" if self._client is not None else "duckduckgo"

    def classify(self, text: str, llm: LLMClient, mode: str = "auto") -> Classification:
        normalized_mode = mode if mode in {"auto", "always", "off"} else "auto"
        stripped = text.strip()
        if normalized_mode == "off":
            return Classification(needs_search=False, reason="off")

        if normalized_mode == "always":
            queries = self._rewrite_queries(stripped, llm, self._fallback_queries(stripped))
            return Classification(
                needs_search=bool(queries),
                queries=queries[:ROOT_QUERY_LIMIT],
                reason="always",
            )

        local_needs_search = self._local_needs_search(stripped)
        llm_classification = self._classify_with_llm(stripped, llm)
        fallback_queries = llm_classification.queries or self._fallback_queries(stripped)

        if llm_classification.needs_search:
            queries = self._rewrite_queries(stripped, llm, fallback_queries)
            return Classification(
                needs_search=bool(queries),
                queries=queries[:ROOT_QUERY_LIMIT],
                reason=llm_classification.reason or "llm",
            )
        if local_needs_search:
            queries = self._rewrite_queries(stripped, llm, fallback_queries)
            return Classification(
                needs_search=bool(queries),
                queries=queries[:ROOT_QUERY_LIMIT],
                reason="heuristic",
            )
        return Classification(needs_search=False, queries=[], reason="not_needed")

    def _classify_with_llm(self, text: str, llm: LLMClient) -> Classification:
        result = complete_structured(
            llm,
            system_prompt="당신은 질문 분류기입니다. 엄격한 JSON만 반환하세요.",
            user_prompt=f"""다음 질문이 외부 검색을 통해 답변 품질이 유의미하게 높아지는지 판단하세요.

검색이 필요한 경우:
- 최신 정보, 현재 상태, 실제 수치, 가격, 상품 비교, 뉴스, 정책, 회사/인물 현황
- 추천 질문 중 시간/장소/가격/메타/트렌드가 중요한 경우
- 게임 메타, 챔피언 패치, 식당/메뉴, 여행, 상품, AI 모델/API/라이브러리/프레임워크처럼 정보가 자주 바뀌는 주제

질문: {text}

반드시 JSON 객체만 반환하세요.
- needs_search: true 또는 false
- queries: 검색어 배열 (needs_search가 true일 때만, 최대 3개, 한국어 또는 영어)""",
            schema=SearchClassificationOutput,
            temperature=0.0,
        )
        if not result.used_llm:
            return Classification(needs_search=False, reason="llm_unavailable")
        if not isinstance(result.value, SearchClassificationOutput):
            return Classification(needs_search=False, reason="llm_parse_error")
        needs = result.value.needs_search
        queries = [str(q).strip() for q in result.value.queries if str(q).strip()][:ROOT_QUERY_LIMIT]
        return Classification(needs_search=needs and bool(queries), queries=queries, reason="llm")

    def _rewrite_queries(self, text: str, llm: LLMClient, fallback_queries: list[str]) -> list[str]:
        fallback = self._dedupe_queries(fallback_queries)[:ROOT_QUERY_LIMIT]
        if not text.strip():
            return fallback

        result = complete_structured(
            llm,
            system_prompt="당신은 웹 검색어 재작성기입니다. 엄격한 JSON만 반환하세요.",
            user_prompt=f"""사용자 입력을 검색엔진 친화적인 검색어 1~3개로 바꾸세요.

예시는 형식과 판단 기준만 참고하고, 예시 문장을 그대로 복사하지 마세요.
{SEARCH_QUERY_REWRITE_EXAMPLES}

사용자 입력:
{text}

출력 JSON 형식:
{{"queries": ["검색어 1", "검색어 2"]}}

규칙:
- 너무 긴 원문 전체를 그대로 검색어로 쓰지 마세요.
- 최신성, 비교, 가격, 사례, 프레임워크, 시뮬레이션처럼 검색 목적이 드러나게 하세요.
- 한국어 질문이어도 영어 검색어가 더 정확하면 영어를 섞으세요.
- API 키, 개인정보, 내부 설정값은 검색어에 넣지 마세요.""",
            schema=SearchQueriesOutput,
            temperature=0.0,
        )
        if not result.used_llm or not isinstance(result.value, SearchQueriesOutput):
            return fallback

        queries = self._dedupe_queries(str(query) for query in result.value.queries)
        return queries[:ROOT_QUERY_LIMIT] or fallback

    def _local_needs_search(self, text: str) -> bool:
        normalized = text.lower()
        compact = "".join(normalized.split())
        terms = (
            "오늘",
            "요즘",
            "최근",
            "현재",
            "최신",
            "이번",
            "2026",
            "패치",
            "추천",
            "비교",
            "순위",
            "가격",
            "후기",
            "사례",
            "트렌드",
            "롤",
            "챔프",
            "메타",
            "승률",
            "픽률",
            "식당",
            "메뉴",
            "맛집",
            "배달",
            "여행",
            "숙소",
            "상품",
            "노트북",
            "폰",
            "라이브러리",
            "프레임워크",
            "회사",
            "정책",
            "뉴스",
        )
        phrases = (
            "ai모델",
            "ai model",
            "aiagent",
            "ai agent",
            "api",
        )
        return any(term in normalized for term in terms) or any(phrase in compact for phrase in phrases)

    def _fallback_queries(self, text: str) -> list[str]:
        stripped = text.strip()
        if not stripped:
            return []
        for line in stripped.splitlines():
            cleaned = line.strip()
            for prefix in ("원 문제:", "문제:", "사용자 입력:"):
                if cleaned.startswith(prefix):
                    query = cleaned.removeprefix(prefix).strip()
                    if query:
                        return [query[:120]]
        return [stripped[:120]]

    def fetch(self, queries: list[str]) -> str | None:
        if not queries:
            return None
        lines: list[str] = []
        for query in self._dedupe_queries(queries):
            result_lines, _ = self._fetch_query(query)
            lines.extend(result_lines[:QUERY_RESULT_LIMIT])
        deduped = self._dedupe_lines(lines)[:CONTEXT_SNIPPET_LIMIT]
        return "\n".join(deduped) if deduped else None

    def fetch_tree(self, root_queries: list[str], llm: LLMClient) -> SearchTreeResult:
        root_queries = self._dedupe_queries(root_queries)[:ROOT_QUERY_LIMIT]
        query_tree: list[SearchQueryNode] = []
        all_queries: list[str] = []
        all_lines: list[str] = []
        seen_queries: set[str] = set()

        for root_query in root_queries:
            seen_queries.add(self._normalize_query(root_query))
            all_queries.append(root_query)
            root_lines, root_error = self._fetch_query(root_query)
            root_lines = root_lines[:QUERY_RESULT_LIMIT]
            root_node = SearchQueryNode(
                query=root_query,
                result_count=len(root_lines),
                status=self._node_status(root_lines, root_error),
                error=root_error,
            )
            all_lines.extend(root_lines)

            for child_query in self._child_queries(root_query, root_lines, llm, seen_queries):
                seen_queries.add(self._normalize_query(child_query))
                all_queries.append(child_query)
                child_lines, child_error = self._fetch_query(child_query)
                child_lines = child_lines[:QUERY_RESULT_LIMIT]
                root_node.children.append(
                    SearchQueryNode(
                        query=child_query,
                        result_count=len(child_lines),
                        status=self._node_status(child_lines, child_error),
                        error=child_error,
                    )
                )
                all_lines.extend(child_lines)

            query_tree.append(root_node)

        deduped_lines = self._dedupe_lines(all_lines)[:CONTEXT_SNIPPET_LIMIT]
        return SearchTreeResult(
            context="\n".join(deduped_lines) if deduped_lines else None,
            queries=all_queries[: ROOT_QUERY_LIMIT + ROOT_QUERY_LIMIT * CHILD_QUERY_LIMIT],
            query_tree=query_tree,
            result_count=len(deduped_lines),
        )

    def _fetch_query(self, query: str) -> tuple[list[str], str | None]:
        if self._client is None:
            return self._fetch_duckduckgo_query(query)
        return self._fetch_tavily_query(query)

    def _fetch_tavily_query(self, query: str) -> tuple[list[str], str | None]:
        try:
            response = self._client.search(query, max_results=QUERY_RESULT_LIMIT)
            lines: list[str] = []
            for item in response.get("results", [])[:QUERY_RESULT_LIMIT]:
                title = item.get("title", "").strip()
                content = item.get("content", "").strip()
                if content:
                    lines.append(self._format_result_line(title, content))
            return lines, None
        except Exception as exc:
            return [], str(exc)

    def _fetch_duckduckgo_query(self, query: str) -> tuple[list[str], str | None]:
        try:
            url = f"https://duckduckgo.com/html/?{urlencode({'q': query})}"
            request = Request(url, headers={"User-Agent": "PersonaGraph/1.0"})
            with urlopen(request, timeout=8) as response:
                html = response.read().decode("utf-8", errors="ignore")
            lines = [
                self._format_result_line(title, snippet or href)
                for title, href, snippet in _parse_duckduckgo_results(html)[:QUERY_RESULT_LIMIT]
                if title and (snippet or href)
            ]
            return lines, None
        except Exception as exc:
            return [], str(exc)

    def _child_queries(
        self,
        root_query: str,
        root_lines: list[str],
        llm: LLMClient,
        seen_queries: set[str],
    ) -> list[str]:
        if not root_lines:
            return []
        result = complete_structured(
            llm,
            system_prompt="당신은 검색 결과를 보고 다음 검색어를 확장하는 리서치 플래너입니다. 엄격한 JSON만 반환하세요.",
            user_prompt=f"""부모 검색어와 검색 결과를 보고, 더 깊게 확인할 자식 검색어를 최대 3개 만드세요.

목표:
- 부족한 관점, 최신성, 비교, 실제 사례, 리스크를 보완합니다.
- 부모 검색어와 거의 같은 검색어를 반복하지 않습니다.
- 너무 긴 문장 대신 검색엔진 친화적인 명사구를 사용합니다.

부모 검색어:
{root_query}

부모 검색 결과:
{self._truncate_context(root_lines)}

출력 JSON:
{{"queries": ["자식 검색어 1", "자식 검색어 2"]}}""",
            schema=SearchQueriesOutput,
            temperature=0.0,
        )
        if not result.used_llm or not isinstance(result.value, SearchQueriesOutput):
            return []

        child_queries: list[str] = []
        for query in self._dedupe_queries(str(query) for query in result.value.queries):
            normalized = self._normalize_query(query)
            if normalized in seen_queries:
                continue
            child_queries.append(query)
            if len(child_queries) >= CHILD_QUERY_LIMIT:
                break
        return child_queries

    def _node_status(self, lines: list[str], error: str | None) -> str:
        if error:
            return "error"
        if lines:
            return "fetched"
        return "no_results"

    def _format_result_line(self, title: str, body: str) -> str:
        clean_title = title.strip() or "검색 결과"
        clean_body = " ".join(body.split())
        return f"[{clean_title}] {clean_body[:300]}"

    def _dedupe_queries(self, queries) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for query in queries:
            cleaned = " ".join(str(query).split())
            normalized = self._normalize_query(cleaned)
            if not cleaned or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(cleaned)
        return deduped

    def _dedupe_lines(self, lines: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for line in lines:
            cleaned = " ".join(line.split())
            normalized = cleaned.lower()
            if not cleaned or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(cleaned)
        return deduped

    def _normalize_query(self, query: str) -> str:
        return " ".join(query.lower().split())

    def _truncate_context(self, lines: list[str]) -> str:
        return "\n".join(lines)[:1200]

class _DuckDuckGoResultParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results: list[dict[str, str]] = []
        self._current: dict[str, str] | None = None
        self._active_field: str | None = None

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = dict(attrs)
        class_name = attrs_dict.get("class", "")
        if tag == "a" and "result__a" in class_name:
            self._current = {
                "title": "",
                "href": _clean_duckduckgo_url(attrs_dict.get("href", "")),
                "snippet": "",
            }
            self._active_field = "title"
            self.results.append(self._current)
            return
        if self._current is not None and "result__snippet" in class_name:
            self._active_field = "snippet"

    def handle_endtag(self, tag: str):
        if tag == "a" and self._active_field == "title":
            self._active_field = None
        elif self._active_field == "snippet":
            self._active_field = None

    def handle_data(self, data: str):
        if self._current is None or self._active_field is None:
            return
        value = " ".join(data.split())
        if not value:
            return
        existing = self._current.get(self._active_field, "")
        self._current[self._active_field] = f"{existing} {value}".strip()


def _parse_duckduckgo_results(html: str) -> list[tuple[str, str, str]]:
    parser = _DuckDuckGoResultParser()
    parser.feed(html)
    parsed: list[tuple[str, str, str]] = []
    for item in parser.results:
        title = item.get("title", "").strip()
        href = item.get("href", "").strip()
        snippet = item.get("snippet", "").strip()
        if title:
            parsed.append((title, href, snippet))
    return parsed


def _clean_duckduckgo_url(href: str) -> str:
    if not href:
        return ""
    parsed = urlparse(href)
    if parsed.path == "/l/":
        target = parse_qs(parsed.query).get("uddg", [""])[0]
        if target:
            return unquote(target)
    return href
