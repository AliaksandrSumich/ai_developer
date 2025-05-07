import os
import json
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_config(config_path='config.json'):
    with open(config_path, 'r') as f:
        return json.load(f)

def collect_files(content_dir):
    file_data = []
    for root, _, files in os.walk(content_dir):
        for file in files:
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                file_data.append({
                    "path_to_file": os.path.relpath(path, content_dir),
                    "file_text": f.read()
                })
    return file_data

def call_ai(prompt, files):

    user_input = {
        "prompt": prompt,
        "files": files
    }

    response = client.chat.completions.create(model="gpt-4o",
    messages=[
        {
            "role": "system",
            "content": "You are an AI code assistant. Return only valid JSON in the format: [{\"path_to_file\": string, \"file_text\": string\\ not put here the file name. only file content}, ...]"
        },
        {
            "role": "user",
            "content": json.dumps(user_input)
        }
    ],
    temperature=0.7)

    try:
        ai_output = response.choices[0].message.content
        return json.loads(ai_output)
    except Exception as e:
        print("Error parsing AI response:", e)
        print("Raw response:\n", response.choices[0].message.content)
        raise

def write_files(content_dir, updated_files):
    for file in updated_files:
        full_path = os.path.join(content_dir, file["path_to_file"])
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(file["file_text"])

def main():
    config = load_config()
    content_dir = config["content_dir"]
    prompt = config["prompt"]

    files = collect_files(content_dir)
    updated_files = call_ai(prompt, files)
    write_files(content_dir, updated_files)
    print("Files updated.")

if __name__ == "__main__":
    main()
