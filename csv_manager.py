import os
import csv
import chardet


def to_list(file_path: str) -> list:
    encoding: str = detect_encoding(file_path)

    data = []
    with open(file_path, 'r', encoding=encoding) as file:
        csv_reader = csv.reader(file, delimiter=';')
        for row in csv_reader:
            data.append(row)

    result: list = []
    keys: list = data[0]

    for row in range(1, len(data)):
        result.append({})

        for key in range(0, len(keys)):
            result[row - 1][keys[key]] = data[row][key]

    return result


def list_to_csv(sample: list) -> str:
    if len(sample) == 0 or len(sample) == 1 and sample[0] is None:
        return ''

    result: str = ''

    categories = sample[0].keys()

    for i in categories:
        result += i + ";"

    result = result[:-1] + '\n'

    for element in sample:
        for key in element:
            result += str(element[key]) + ';'

        result = result[:-1] + '\n'

    return result


def save(text: str, file_path: str):
    if not os.path.exists(file_path):
        open(file_path, 'w').close()

    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text)
    except Exception as e:
        print(f"Error occured while saving to {file_path}: {e}")


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        return chardet.detect(file.read())['encoding']
