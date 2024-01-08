import json


def parse_json_markdown(json_string: str) -> dict:
    json_string = json_string.strip()
    start_index = json_string.find("```json")
    end_index = json_string.find("```", start_index + len("```json"))

    if start_index != -1 and end_index != -1:
        extracted_content = json_string[start_index + len("```json") : end_index].strip()
        parsed = json.loads(extracted_content)
    elif start_index != -1 and end_index == -1 and json_string.endswith("``"):
        end_index = json_string.find("``", start_index + len("```json"))
        extracted_content = json_string[start_index + len("```json") : end_index].strip()
        parsed = json.loads(extracted_content)
    elif json_string.startswith("{"):
        parsed = json.loads(json_string)
    else:
        raise ValueError("Could not find JSON block in the output.")
    return parsed
