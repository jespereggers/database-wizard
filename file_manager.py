def load_as_string(file_path: str):
    with open(file_path, 'r', encoding='windows-1252') as file:
        file_content = file.read()
    return file_content


def load_list(file_path):
    try:
        with open(file_path, 'r') as file:
            # Assuming each line of the file contains one item of the list
            items = [line.strip() for line in file.readlines()]
        return items
    except FileNotFoundError:
        print("File not found.")
        return None
    except Exception as e:
        print(f"Error occurred: {e}")
        return None


def save_list(file_path: str, content: list):
    with open(file_path, "w") as f:
        for i in content:
            f.write(str(i) + "\n")
