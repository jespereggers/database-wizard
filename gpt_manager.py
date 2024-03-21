import gpt_configs

from keys import OPENAI_API_KEY, TAVILY_API_KEY
from openai import OpenAI
from tavily import TavilyClient
import json
import time

client = OpenAI(api_key=OPENAI_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


def ask_scrape_gpt(page_content: str) -> str:
    prompt: str = (
            'Dies ist der Inhalt einer Unternehmensinfoseite:\n'
            + page_content + '\n\n'
            + 'Wichtig: Antworte nur mit einer Zahl oder "unknown". Füge nie irgendwas anderes hinzu'
    )
    return "unknown"

    response = client.chat.completions.create(
        # most advanced model
        model="gpt-4-turbo-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                ]
            }
        ],
    )
    answer: str = response.choices[0].message.content

    return answer


def tavily_search(query):
    search_result = tavily_client.get_search_context(query, search_depth="advanced", max_tokens=8000)
    return search_result


def open_website(query):
    print("open " + query)
    return "25 Mitarbeiter"


def submit_tool_outputs(thread_id, run_id, tools_to_call):
    tool_output_array = []

    for tool in tools_to_call:
        output = None
        tool_call_id = tool.id
        function_name = tool.function.name
        function_args = tool.function.arguments

        print(function_name)

        match function_name:
            case "tavily_search":
                output = tavily_search(query=json.loads(function_args)["query"])
            case "open_website":
                output = open_website(query=json.loads(function_args)["query"])

        if output:
            tool_output_array.append({"tool_call_id": tool_call_id, "output": output})

    return client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run_id,
        tool_outputs=tool_output_array
    )


def wait_for_run_completion(thread_id, run_id):
    while True:
        time.sleep(1)
        run_client = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        print(f"Current run status: {run_client.status}")
        if run_client.status in ['completed', 'failed', 'requires_action']:
            return run_client


def init_assist(mode: gpt_configs.Modes) -> [object, object]:
    assistant = gpt_configs.get_assist(client, mode)
    thread = client.beta.threads.create()
    return [assistant, thread]


def get_thread() -> object:
    return client.beta.threads.create()


def ask_assist(assistant, thread, message: str) -> str:
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
    )

    run = wait_for_run_completion(thread.id, run.id)

    if run.status == 'failed':
        print(run.error)
    elif run.status == 'requires_action':
        submit_tool_outputs(thread.id, run.id, run.required_action.submit_tool_outputs.tool_calls)
        wait_for_run_completion(thread.id, run.id)

    messages = client.beta.threads.messages.list(thread_id=thread.id)

    response: str = messages.data[0].content[0].text.value

    client.beta.threads.delete(thread.id)

    return response
