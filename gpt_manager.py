# -*- coding: windows-1252 -*-
import gpt_configs

from keys import OPENAI_API_KEY, TAVILY_API_KEY
from openai import OpenAI
from tavily import TavilyClient
import json
import time

client = OpenAI(api_key=OPENAI_API_KEY)
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)

import json
import requests


def ask_scrape_gpt(page_content: str) -> dict:
    prompt = (
            'Suche die Anzahl der Mitarbeiter eines Unternehmens.\n'
            + 'Dies ist der Inhalt der Unternehmensinfoseite:\n'
            + page_content + '\n\n'
            + 'Wichtig: Antworte immer in diesem Format: {"employees": "int", "guessed": "ja" oder "nein"}.\n'
            + 'Antworte mit {"employees": "unknown", "guessed": "no"} wenn du nichts findest.\n'
    )

    # Configuration for the API call
    headers = {
        "Authorization": "Bearer " + OPENAI_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo-0125",
        "messages": [{
            "role": "user",
            "content": prompt
        }]
    }

    # Sending the request to the OpenAI API
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    response_data = response.json()

    # Extracting the text from the response
    answer = "empty"
    try:
        answer = response_data['choices'][0]['message']['content'].strip()
        output = json.loads(answer)
        if "employees" in output and "guessed" in output:
            return output
        else:
            print("Invalid format returned.")
    except json.JSONDecodeError as e:
        print(f"JSON decoding failed in ask_scrape_gpt: {e}")
        print(answer)
    except KeyError as e:
        print(f"Key error: {e}")
        print(answer)
    except Exception as e:
        print(f"An unexpected error occurred in ask_scrape_gpt: {e}")
        print(answer)

    return {"employees": "unknown", "guessed": "no"}


def ask_search_gpt(search_results: str) -> dict:
    prompt: str = (
            'Ich suche die Anzahl der Mitarbeiter eines Unternehmens. '
            + 'Wenn du mehrere Zahlen findest, wählst du den Mittelwert.\n'
            + 'Dies sind die Inhalte, die ich dazu im Internet gefunden habe:\n'
            + search_results + '\n\n'
            + 'Wichtig: Antworte immmer in diesem Format: {"employees": int oder "unknown", "source": url}.\n'
            + 'Füge nie irgendwas anderes hinzu'
    )

    response = client.chat.completions.create(
        # most advanced model
        model="gpt-3.5-turbo-16k",
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
    output: dict = {}

    try:
        output = json.loads(answer)
        return output
    except json.JSONDecodeError as e:
        print(f"JSON decoding failed in ask_search_gpt: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in ask_search_gpt: {e}")

    return output


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


