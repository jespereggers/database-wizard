
from keys import GOOGLE_API_KEY, GOOGLE_CS_ID
from bs4 import BeautifulSoup
import csv_manager
import gpt_configs
import gpt_manager
import requests
import json
import sys

SAMPLE_PATH = 'input/nearby-500.csv'
OUTPUT_PATH = 'output/nearby-500.csv'


def get_about_link(url) -> str:
    search_term: str = 'team OR unternehmen OR profil OR ueber_uns site:' + url

    search_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CS_ID}&q={search_term}"
    response = requests.get(search_url).json()
    first_result_link = response['items'][0]['link']

    return first_result_link

def get_link_content(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()  # Stellt sicher, dass ein Fehler geworfen wird bei einem nicht erfolgreichen Statuscode

        content = response.content.decode('utf-8')
        soup = BeautifulSoup(content, 'html.parser')

        # Entferne Skripte und Stylesheets, da diese in der Regel nicht zum Hauptinhalt gehören
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Nutze get_text() um den Textinhalt ohne HTML-Tags zu erhalten
        text = soup.get_text()

        # Optional: Entferne mehrere aufeinanderfolgende Leerzeichen und Zeilenumbrüche
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text
    except requests.RequestException as e:
        return str(e)  # Gibt den Fehler als String zurück, falls einer auftritt


def is_valid_sample(sample: dict, sample_filter: dict) -> bool:
    for key in sample_filter.keys():
        if key in sample.keys() and sample[key] != "unknown":
            filter_var = type(eval(sample_filter[key][1]))(sample[key])

            match sample_filter[0]:
                case "<":
                    if sample[key] < filter_var:
                        return False
                case ">":
                    if sample[key] > filter_var:
                        return False
                case "==":
                    if sample[key] == filter_var:
                        return False
                case "!=":
                    if sample[key] != filter_var:
                        return False
    return True


def mod_sample(sample: list, sample_filter: dict, add: list) -> list:
    result: list = []
    sample_categories: list = sample[0].keys()

    #scrape_assist, thread_scrape = gpt_manager.init_assist(gpt_configs.Modes.WEB_SEARCH)
    #web_search_assist, thread_web_search = gpt_manager.init_assist(gpt_configs.Modes.WEB_SEARCH)

    for element in sample:
        extension: dict = {}

        for i in add:
            extension[i] = "unknown"

        # apply filters
        if is_valid_sample(element, sample_filter):
            # stage 1: homepage
            if "Website" in sample_categories:
                pass
                #about_link: str = get_about_link(element["Website"])
                #link_content: str = get_link_content(about_link).encode('cp1252', errors='replace').decode('cp1252')
                #gpt_response = gpt_manager.ask_scrape_gpt(link_content)
                #if gpt_response != "unknown":
                    #extension["employees"] = int(gpt_response)
                #extension["source"] = "Official Website"

            #name: str = element['Name']
            #thread_scrape = gpt_manager.get_thread()
            #gpt_output = json.loads(gpt_manager.ask_assist(scrape_assist, thread_web_search, name))
            #print(gpt_output)

            # stage 2 / 3: web search and guessing
            #name: str = element['Name']
            #thread_web_search = gpt_manager.get_thread()
            #gpt_output = json.loads(gpt_manager.ask_assist(web_search_assist, thread_web_search, name))

            #extension["GPT-Employees"] = gpt_output["employees"]
            #extension["Source"] = gpt_output["Source"]

        if is_valid_sample(extension, sample_filter):
            element.update(extension)
            result.append(element)

        # temporary
        csv_result: str = csv_manager.list_to_csv(result)
        csv_manager.save(csv_result, "output/testflight/event-sample-" + str(len(result)) + ".csv")

    return result


data: list = csv_manager.to_list(SAMPLE_PATH)
mod_data: list = mod_sample([data[0]], {"employees": ["<", 25]}, ["employees", "source"])
mod_data_as_csv: str = csv_manager.list_to_csv(mod_data)
csv_manager.save(mod_data_as_csv, OUTPUT_PATH)
