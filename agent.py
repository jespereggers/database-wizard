# -*- coding: windows-1252 -*-
import file_manager
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


def get_about_link(url) -> list:
    search_term: str = 'team OR unternehmen OR profil OR ueber_uns site:' + url

    search_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CS_ID}&q={search_term}"
    response = requests.get(search_url).json()

    links: list = []

    if 'items' in response.keys():
        for i in range(0, len(response['items'])):
            links.append(response['items'][i]['link'])

    return links


def get_snippet(company_name) -> str:
    search_term: str = 'Mitarbeiterzahl ' + company_name

    search_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CS_ID}&q={search_term}"
    response = requests.get(search_url).json()

    first_result_link: str = "unknown"

    print()

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
    if ("employees" in response.keys() and response["employees"] != "{}" and not response["employees"] is None
            and toolbox.str_represents_int(response["employees"])):
        return True
    return False


def modify(sample: dict, add: list):
    extension: dict = {}

    for i in add:
        extension[i] = "unknown"
    extension["KI-Rank"] = "Tavily"

    # stage 1: search on homepage
    if "Domain_p" in sample.keys() and sample["Domain_p"] != "":
        print("Enter stage 1 for " + sample["Name"])

        # get link to about-site of a company
        about_links: list = get_about_link(
            sample["Domain_p"].replace("https://", "").replace("http://", "").replace("www.", "")
        )
        about_links = about_links[:2]

        if len(about_links) > 0:
            print("Got about-links: " + about_links[0] + "...")

        for link_index in range(0, len(about_links)):
            link = about_links[link_index]

            # gpt searches on about-site
            link_content: str = get_link_content(link).encode('cp1252', errors='replace').decode('cp1252')
            gpt_response: dict = gpt_manager.ask_scrape_gpt(link_content[:12000])
            print("Got response: ", gpt_response)

            if (gpt_response_is_valid(gpt_response) and gpt_response["employees"] != "0"
                    and gpt_response["employees"] != 0):
                print("Success")
                extension["KI-Mitarbeiterzahl"] = int(gpt_response["employees"])
                extension["KI-Quelle"] = urllib.parse.unquote(link)

                extension["KI-Rank"] = str(link_index)

                for key in extension.keys():
                    sample[key] = extension[key]
                return sample

    # stage 2: search the entire web
    print("Enter stage 2 for " + sample["Name"])

    search_prompt: str = sample["Name"] + " Mitarbeiterzahl"
    search_results: str = toolbox.get_tavily_search(search_prompt)
    gpt_output: dict = gpt_manager.ask_search_gpt(search_results)
    print("Got response: ", gpt_output)

    if gpt_response_is_valid(gpt_output) and gpt_output["employees"] != "unknown":
        extension["KI-Mitarbeiterzahl"] = gpt_output["employees"]
        extension["KI-Quelle"] = urllib.parse.unquote(gpt_output["source"])

    for key in extension.keys():
        sample[key] = extension[key]

    return sample


def get_files_in_folder(folder_path: str):
    try:
        if os.path.isdir(folder_path):
            files: list = os.listdir(folder_path)
            return files
        else:
            return "Der angegebene Pfad ist kein Verzeichnis."
    except Exception as e:
        return f"Fehler beim Auflisten der Dateien: {str(e)}"


def bind_exports(folder_path: str, destination_path: str):
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    files: list = os.listdir(folder_path)

    exports: list = []

    for file_path in files:
        path_str: str = "output/northdata/" + str(file_path)

        if os.path.exists(path_str):
            fraction: dict = csv_manager.to_list(path_str)[0]
            exports.append(fraction)

    export_as_csv_string: str = csv_manager.list_to_csv(exports)
    csv_manager.save(export_as_csv_string, destination_path)


def get_blacklist(file_path: str) -> list:
    if os.path.exists(file_path):
        blacklist: list = file_manager.load_list(file_path)
        return blacklist
    else:
        file_manager.save_list(file_path, [])
        return []


data: list = csv_manager.to_list("input/northdata.CSV")
found_result: bool = True

ignore_list: list = get_blacklist("output/northdata_ignore.txt")

for element in data:
    path: str = "output/northdata/" + element["Register-ID"] + ".csv"
    found_result = True

    if element["Register-ID"] in ignore_list:
        print("Skip " + element["Register-ID"])

    if not os.path.exists(path) and not element["Register-ID"] in ignore_list:
        print("-------")

        print(element)

        if element["Mitarbeiterzahl"] == "":
            element = modify(element, ["KI-Mitarbeiterzahl", "KI-Quelle", "KI-Rank"])

            if element["KI-Mitarbeiterzahl"] == "unknown" or element["KI-Mitarbeiterzahl"] == "":
                found_result = False
        else:
            element["KI-Mitarbeiterzahl"] = element["Mitarbeiterzahl"]
            element["KI-Quelle"] = "Übernommen"

        if found_result:
            element_as_csv: str = csv_manager.list_to_csv([element])
            csv_manager.save(element_as_csv, path)
        else:
            ignore_list.append(element["Register-ID"])

        print(element)
        file_manager.save_list("output/northdata_ignore.txt", ignore_list)
        print("-------")

bind_exports("output/northdata", "output/northdata.csv")
