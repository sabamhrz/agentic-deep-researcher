def search_web_text(query: str, max_results: int = 8) -> str:
    """Run a DuckDuckGo web search and return formatted snippets."""
    ddgs_cls = _load_ddgs()
    if ddgs_cls is None:
        return "Web search is unavailable. Install ddgs: pip install ddgs"

    try:
        with ddgs_cls() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        return f"Search failed: {exc}"

    if not results:
        return "No web results found for this query."

    snippets = []
    for index, result in enumerate(results, 1):
        title = result.get("title", "Untitled")
        body = result.get("body", "")
        href = result.get("href", "")
        snippets.append(f"{index}. {title}\n{body}\nSource: {href}")

    return "\n\n".join(snippets)


def _load_ddgs():
    try:
        from ddgs import DDGS

        return DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS

            return DDGS
        except ImportError:
            return None
