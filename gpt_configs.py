from enum import Enum


class Modes(Enum):
    WEB_SEARCH = 1
    SCRAPE = 2


def get_assist(client, mode: Modes):
    match mode:
        case Modes.WEB_SEARCH:
            return get_web_search_assist(client)
        case Modes.SCRAPE:
            return get_scrape_assist(client)


def get_web_search_assist(client):
    assistant_instruction = ("You are a market analyst. Given the name of a german company, "
                             "you research (or guess in case there is no info available) the amount of employees. "
                             "Tell if you found a real number or guessed it out of the blue. "
                             "Always check the website first using the access-link tool, "
                             "and proceed to tavily-search if not successfull. "
                             "Important: Respond in this format: {“employees”: int or range, “guessed”: boolean,"
                             "“source”: link}. Never add anything else.")

    return client.beta.assistants.create(
        instructions=assistant_instruction,
        model="gpt-4-1106-preview",
        tools=[{
            "type": "function",
            "function": {
                "name": "tavily_search",
                "description": "Search for information on the entire web.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string",
                                  "description": "The search query to use. For example: "
                                                 "'Provide a competitive analysis of Open Source survey tools'"},
                    },
                    "required": ["query"]
                }
            }
        },
            {
                "type": "function",
                "function": {
                    "name": "open_website",
                    "description": "Open a specific  from the.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string",
                                      "description": "The url to access. For example: "
                                                     "'https://apple.com'"},
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    )


def get_scrape_assist(client):
    assistant_instruction = ("You are a market analyst. Given the name of a german company, "
                             "you research the amount of employees by scraping their homepage. "
                             "Tell if you found a real number or guessed it out of the blue. "
                             "Always check the website first using the access-link tool, "
                             "and proceed to tavily-search if not successfull. "
                             "Important: Respond in this format: {“employees”: int or range, “guessed”: boolean,"
                             "“source”: link}. Never add anything else.")

    return client.beta.assistants.create(
        instructions=assistant_instruction,
        model="gpt-4-1106-preview",
        tools=[{
            "type": "function",
            "function": {
                "name": "scrape_homepage",
                "description": "Search for information on the entire web.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string",
                                  "description": "The search query to use. For example: "
                                                 "'Provide a competitive analysis of Open Source survey tools'"},
                    },
                    "required": ["query"]
                }
            }
        },
            {
                "type": "function",
                "function": {
                    "name": "open_website",
                    "description": "Open a specific  from the.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string",
                                      "description": "The url to access. For example: "
                                                     "'https://apple.com'"},
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
    )
