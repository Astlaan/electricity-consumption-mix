import requests
import json


def read_input(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read().strip()


def write_output(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)


def compress_text(prompt, compression_level, api_token):
    response = requests.post(
        "https://middleout.wehead.com/api/compress",
        headers={
            "Accept": "application/json",
            "Authorization": f"Token {api_token}",
            "Content-Type": "application/json",
        },
        json={"prompt": prompt, "compression_level": compression_level},
        timeout=240,
    )
    return response.json()


if __name__ == "__main__":
    input_file = "entsoe-docs.txt"
    output_file = "output.txt"
    api_token = "zRU3rEpfEw2Cm84oRvvRRg_y9xZYxFHxe2tPzNB4PUc"
    compression_level = 0.7

    prompt = read_input(input_file)
    result = compress_text(prompt, compression_level, api_token)
    write_output(output_file, result)

    print(f"Input read from {input_file}")
    print(f"Output written to {output_file}")
