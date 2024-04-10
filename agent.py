# -*- coding: windows-1252 -*-

from keys import GOOGLE_API_KEY, GOOGLE_CS_ID
from bs4 import BeautifulSoup
import urllib.parse
import toolbox
import csv_manager
import gpt_manager
import requests
import os

INPUT_PATH = 'input/event-sheet.csv'
OUTPUT_PATH = 'output/event-sheet.csv'


def get_about_link(url) -> str:
    search_term: str = 'team OR unternehmen OR profil OR ueber_uns site:' + url

    search_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CS_ID}&q={search_term}"
    response = requests.get(search_url).json()

    first_result_link: str = "unknown"

    if 'items' in response.keys():
        if len(response['items']) > 0:
            first_result_link = response['items'][0]['link']

    return first_result_link


def get_link_content(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

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
            filter_var = type(sample_filter[key][1])(sample[key])

            match sample_filter[key][0]:
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


def gpt_response_is_valid(response: dict) -> bool:
    if response == {}:
        return False
    if "employees" in response.keys() and toolbox.str_represents_int(response["employees"]):
        return True
    return False


def mod_sample(sample: list, sample_filter: dict, add: list) -> list:
    result: list = []
    print("Start process with ", sample)
    sample_categories: list = sample[0].keys()

    for element in sample:
        element["Name"] = element["Name"].replace("\x9f", "ß").replace("\x96", "Ö").replace("\x84", "Ä")
        extension: dict = {}
        success: bool = False

        for i in add:
            extension[i] = "unknown"

        # apply filters
        if is_valid_sample(element, sample_filter) and element['Fahrzeit ok?'] == 'ja':
            # stage 1: scraping
            print("Enter stage 1 / 3 for ", element["Name"])

            if "Website" in sample_categories:
                about_link: str = get_about_link(
                    element["Website"].replace("https://", "").replace("http://", "").replace("www.", "")
                )
                print("Got about-link: " + about_link)

                if about_link != "unknown":
                    link_content: str = get_link_content(about_link).encode('cp1252', errors='replace').decode('cp1252')
                    gpt_response: dict = gpt_manager.ask_scrape_gpt(link_content)
                    print("Got response: ", gpt_response)

                    if gpt_response_is_valid(gpt_response):
                        extension["employees"] = int(gpt_response["employees"])
                        extension["source"] = urllib.parse.unquote(about_link)

                        if gpt_response["guessed"] == "nein":
                            extension["stage"] = "scraping"
                            success = True
                        else:
                            extension["stage"] = "guessing"

            if not success:
                print("Enter stage 2 for " + element["Name"])
                # stage 2: searching
                search_prompt: str = element["Name"] + " Mitarbeiterzahl"
                search_results: str = toolbox.get_tavily_search(search_prompt)
                gpt_output: dict = gpt_manager.ask_search_gpt(search_results)
                print("Got response: ", gpt_output)

                if gpt_response_is_valid(gpt_output) and gpt_output["employees"] != "unknown":
                    extension["employees"] = gpt_output["employees"]
                    extension["source"] = urllib.parse.unquote(gpt_output["source"])
                    extension["stage"] = "searching"

        element.update(extension)
        result.append(element)

    return result


def get_files_in_folder(folder_path: str):
    try:
        if os.path.isdir(folder_path):
            files: list = os.listdir(folder_path)
            return files
        else:
            return "Der angegebene Pfad ist kein Verzeichnis."
    except Exception as e:
        return f"Fehler beim Auflisten der Dateien: {str(e)}"


data: list = csv_manager.to_list(INPUT_PATH)
export: list = []


def bind_exports(folder_path: str):
    files: list = os.listdir(folder_path)
    files.sort(key=lambda x: int(x.split('.')[0]))

    exports: list = []

    for file_path in files:
        path: str = "output/event/" + str(file_path)

        if os.path.exists(path):
            fraction: dict = csv_manager.to_list(path)[0]
            if fraction["stage"] == "searching" or fraction["stage"] == "scraping":
                export.append(fraction)
                # new_fraction: list = mod_sample([data[index]], {}, ["employees", "source", "stage"])

                # print("Save ", new_fraction)
            # csv_result: str = csv_manager.list_to_csv(new_fraction)
            # csv_manager.save(csv_result, "output/event/" + str(index) + ".csv")

        if not os.path.exists("output/event/" + str(file_path) + ".csv"):
            fraction: list = mod_sample([data[file_path]], {}, ["employees", "source", "stage"])

            print("Save ", fraction)
            csv_result: str = csv_manager.list_to_csv(fraction)
            csv_manager.save(csv_result, "output/event/" + str(file_path) + ".csv")

    csv_export: str = csv_manager.list_to_csv(export).replace("\x9f", "ß").replace("\x96", "Ö").replace("\x84",
                                                                                                        "Ä").replace(
        "\x9c", "Ü")
    csv_manager.save(csv_export, "output/event-sheet.csv")


bind_exports("output/event")
