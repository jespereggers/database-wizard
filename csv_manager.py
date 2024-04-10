import csv


def to_list(file_path: str) -> list:
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file, delimiter=';')
        for row in csv_reader:
            data.append(row)

    result: list = []
    keys: list = data[0]

    for row in range(1, len(data)):
        result.append({})

        for key in range(0, len(keys)):
            result[row-1][keys[key]] = data[row][key]

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
    print("Save file")
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text)
        print(f"String saved to {file_path} successfully.")
    except Exception as e:
        print(f"Error occurred while saving to {file_path}: {e}")
