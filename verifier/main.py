def load(file_path: str):
    with open(file_path, 'r') as file:
        file_content = file.read()
    return file_content


def run():
    invalid_tags: list = load("invalid_tags.txt").split('\n')
    print(invalid_tags)

    while True:
        tag = input("Scan Tag: ")
        if tag.replace("wattro.io/", "") in invalid_tags:
            print("\033[91mINVALID\033[0m")
        else:
            print("VALID")
        print("-------")


run()
