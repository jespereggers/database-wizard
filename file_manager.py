def load_as_string(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    return file_content
