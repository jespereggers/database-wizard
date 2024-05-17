from keys import TAVILY_API_KEY
from tavily import TavilyClient

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


def get_tavily_search(query: str) -> str:
    search_result: str = tavily_client.get_search_context(query, search_depth="advanced", max_tokens=8000)
    return search_result


def str_represents_int(text) -> bool:
    if isinstance(text, (dict, list)):
        return False

    try:
        int(text)
        return True
    except ValueError:
        return False
