# -*- coding: latin-1 -*-
import csv_manager
import gpt_manager
import json

SAMPLE_PATH = 'input/nearby-500.csv'
OUTPUT_PATH = 'output/nearby-500.csv'


def get_productivity(sample: list) -> str:
    result: str = "Name;Mitarbeiterzahl;Umsatz;Gerundeter Umsatz pro Mitarbeiter\n"

    for company in sample:
        employees = int(company['Mitarbeiterzahl'])
        revenue = float(company['Umsatz EUR'].replace(".", "").split(",")[0])
        productivity: int = round(revenue / float(employees))
        productivity: int = round((productivity / 10000)) * 10000

        if 0 < employees <= 250 and revenue < 2e7 and productivity < 2e6:
            result += (company['Name'] + ";" + company['Mitarbeiterzahl'] + ";"
                       + company['Umsatz EUR'].replace(".", "").split(",")[0] + ";" + str(productivity) + "\n")

    return result


def is_valid_sample(sample: dict, filter: dict) -> bool:
    for key in filter.keys():
        if key in sample.keys():
            filter_var = type(eval(filter[key][1]))(sample[key])

            match filter[0]:
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



def mod_sample(sample: list, filter: dict, add: list) -> list:
    result: list = []

    assist, thread = gpt_manager.init_assist()

    for element in sample:
        extension: dict = {}

        for i in add:
            extension[i] = "empty"

        # apply filters
        if is_valid_sample(element, filter):
            # stage 1: homepage
            pass

            # stage 2 / 3: web search and guessing
            name: str = element['Name']
            thread = gpt_manager.get_thread()
            gpt_output = json.loads(gpt_manager.ask_assist(assist, thread, name))

            extension["GPT-Employees"] = gpt_output["employees"]
            extension["Source"] = gpt_output["Source"]

        if is_valid_sample(extension, filter):
            result.append(element + extension)

    return result


data: list = csv_manager.to_list(SAMPLE_PATH)
mod_data: list = mod_sample([data[0]], {"GPT-Mitarbeiterzahl": ["<", 25]}, ["GPT-Mitarbeiterzahl", "Quelle"])
mod_data_as_csv: str = csv_manager.dict_to_csv(mod_data)
csv_manager.save(mod_data_as_csv, OUTPUT_PATH)
