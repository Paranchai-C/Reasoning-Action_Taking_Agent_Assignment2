import os
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup


class SearchTool:
    def __init__(self, timeout: int = 20, max_results: int = 5) -> None:
        self.timeout = timeout
        self.max_results = max_results
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")

    def search(self, query: str) -> str:
        query = query.strip()
        if not query:
            return "No results found. The query was empty."

        if self.tavily_api_key:
            result = self._search_tavily(query)
            if result and "No results found" not in result:
                return result

        return self._search_duckduckgo_html(query)

    def _search_tavily(self, query: str) -> str:
        url = "https://api.tavily.com/search"
        payload: Dict[str, Any] = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": self.max_results,
            "include_answer": True,
            "include_raw_content": False,
        }

        response = requests.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        answer = (data.get("answer") or "").strip()
        results: List[Dict[str, Any]] = data.get("results", [])

        lines: List[str] = []
        if answer:
            lines.append(f"Answer summary: {answer}")

        if not results:
            return "No results found."

        for idx, item in enumerate(results[: self.max_results], start=1):
            title = (item.get("title") or "Untitled").strip()
            content = (item.get("content") or "").strip().replace("\n", " ")
            url = (item.get("url") or "").strip()
            if len(content) > 250:
                content = content[:247] + "..."
            lines.append(f"[{idx}] {title} | {content} | {url}")

        return "\n".join(lines)

    def _search_duckduckgo_html(self, query: str) -> str:
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0",
        }
        response = requests.post(
            url,
            data={"q": query},
            headers=headers,
            timeout=self.timeout,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.select(".result")
        if not results:
            return "No results found."

        lines: List[str] = []
        for idx, item in enumerate(results[: self.max_results], start=1):
            title_elem = item.select_one(".result__title")
            snippet_elem = item.select_one(".result__snippet")
            link_elem = item.select_one(".result__url") or item.select_one(".result__a")

            title = title_elem.get_text(" ", strip=True) if title_elem else "Untitled"
            snippet = snippet_elem.get_text(" ", strip=True) if snippet_elem else ""
            link = link_elem.get_text(" ", strip=True) if link_elem else ""

            if len(snippet) > 250:
                snippet = snippet[:247] + "..."
            lines.append(f"[{idx}] {title} | {snippet} | {link}")

        return "\n".join(lines)
