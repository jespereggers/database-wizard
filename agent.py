# -*- coding: cp1250 -*-
import file_manager
from keys import GOOGLE_API_KEY, GOOGLE_CS_ID
from bs4 import BeautifulSoup
import urllib.parse
import toolbox
import requests
import csv_manager
import gpt_manager
import os

INPUT_PATH = 'input/event-sheet.csv'
OUTPUT_PATH = 'output/event-sheet.csv'


def get_about_link(url) -> list:
    search_term: str = 'mitarbeiter OR team OR unternehmen OR profil OR firma OR ueber_uns site:' + url

    search_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CS_ID}&q={search_term}"
    response = requests.get(search_url).json()

    links: list = []

    if 'items' in response.keys():
        for i in range(0, len(response['items'])):
            links.append(response['items'][i]['link'])

    return links


def get_snippets(prompt: str) -> list:
    search_url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CS_ID}&q={prompt}"
    response = requests.get(search_url).json()

    first_three_links = []

    if 'items' in response and len(response['items']) > 0:
        for item in response['items'][:3]:
            first_three_links.append(item['snippet'])

    return first_three_links


def get_link_content(url: str) -> str:
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Entferne Skripte und Stylesheets, da diese in der Regel nicht zum Hauptinhalt geh�ren
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Nutze get_text() um den Textinhalt ohne HTML-Tags zu erhalten
        text = soup.get_text()

        # Optional: Entferne mehrere aufeinanderfolgende Leerzeichen und Zeilenumbr�che
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text
    except requests.RequestException as e:
        return str(e)  # Gibt den Fehler als String zur�ck, falls einer auftritt


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

    # stage 1: search on homepage
    if "Domain_p" in sample.keys() and sample["Domain_p"] != "":
        # get link to about-site of a company
        about_links: list = get_about_link(
            sample["Domain_p"].replace("https://", "").replace("http://", "").replace("www.", "")
        )
        about_links = about_links[:3]
        print(about_links)

        for link_index in range(0, len(about_links)):
            link = about_links[link_index]

            # gpt searches on about-site
            link_content: str = get_link_content(link).encode('cp1252', errors='replace').decode('cp1252')
            gpt_response: dict = gpt_manager.ask_scrape_gpt(link_content[:12000])

            if (gpt_response_is_valid(gpt_response) and gpt_response["employees"] != "0"
                    and gpt_response["employees"] != 0):
                extension["Mitarbeiterzahl (Auto)"] = int(gpt_response["employees"])
                extension["Quelle (Auto)"] = urllib.parse.unquote(link)

                print(sample["Name"] + ": " + str(extension["Mitarbeiterzahl (Auto)"]) + " employees")

                for key in extension.keys():
                    sample[key] = extension[key]
                return sample

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
        path_str: str = folder_path + "/" + str(file_path)

        if os.path.exists(path_str):
            fraction: dict = csv_manager.to_list(path_str)[0]
            exports.append(fraction)

    export_as_csv_string: str = csv_manager.list_to_csv(exports)
    csv_manager.save(export_as_csv_string, destination_path)


def get_ignore_list(file_path: str) -> list:
    if os.path.exists(file_path):
        blacklist: list = file_manager.load_list(file_path)
        return blacklist
    else:
        file_manager.save_list(file_path, [])
        return []


def run_agent(project_name: str):
    data: list = csv_manager.to_list("input/" + project_name + ".csv")

    ignore_list: list = get_ignore_list("output/" + project_name + "_ignore.txt")

    for element in data:
        # get employee-count
        path: str = "output/" + project_name + "/" + element["Register-ID"] + ".csv"
        found_result: bool = True

        if element["Register-ID"] in ignore_list:
            print("Skip " + element["Register-ID"])

        if not os.path.exists(path) and not element["Register-ID"] in ignore_list:
            print(element["Name"])

            if element["Mitarbeiterzahl"] == "":
                element = modify(element, ["Mitarbeiterzahl (Auto)", "Quelle (Auto)"])

                if element["Mitarbeiterzahl (Auto)"] == "unknown" or element["Mitarbeiterzahl (Auto)"] == "":
                    found_result = False
            else:
                element["Mitarbeiterzahl (Auto)"] = element["Mitarbeiterzahl"]
                element["Quelle (Auto)"] = "Transfer"

            if found_result:
                element_as_csv: str = csv_manager.list_to_csv([element])
                csv_manager.save(element_as_csv, path)
            else:
                ignore_list.append(element["Register-ID"])

            file_manager.save_list("output/" + project_name + "_ignore.txt", ignore_list)

            print("-------")


# tutorial note 1
project_name_input: str = "sample-051724"  # input("Project Name: ")

run_agent(project_name_input)
bind_exports("output/" + project_name_input, "output/" + project_name_input + ".csv")
