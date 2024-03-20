import csv


def to_list(file_path: str) -> list:
    data = []
    with open(file_path, 'r', encoding='latin-1') as file:
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


def dict_to_csv(sample: dict) -> str:
    return ""


def save(text: str, file_path: str):
    try:
        with open(file_path, 'w') as file:
            file.write(text)
        print(f"String saved to {file_path} successfully.")
    except Exception as e:
        print(f"Error occurred while saving to {file_path}: {e}")
