import datetime
import logging
logging.basicConfig(filename='log.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

import os
import json
from dotenv import load_dotenv
from openai import OpenAI

from config import content_dir, ignore_files, prompt

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))





def collect_files(content_dir, ignore_files=None):
    ignore_files = ignore_files or []
    file_data = []

    for root, _, files in os.walk(content_dir):

        for file in files:
            ignore_flag = False
            for ignore in ignore_files:
                if ignore in str(file) or ignore in str(root):
                    ignore_flag = True
                    break
            if ignore_flag:
                continue
            print(f'root: {root}, file: {file}')
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    file_data.append({
                        "path_to_file": os.path.relpath(path, content_dir),
                        "file_text": f.read()
                    })
                except Exception as e:
                    logging.error(f'{path} {os.path.relpath(path, content_dir)}, error in read file: {e}')
    return file_data

def call_ai(prompt, files, main_task=''):

    user_input = {
        "prompt": prompt,
        "files": files
    }

    response = client.chat.completions.create(model="gpt-4.1",
    messages=[
        {
            "role": "system",
            "content": "You are an AI code assistant. Our main task to develop the next application: ({main_task})\n List only files, need to be changed or created. Return only valid JSON in the format: [{\"path_to_file\": string, \"file_text\": string\\ not put here the file name. only file content}, ...]".replace("{main_task}", main_task)
        },
        {
            "role": "user",
            "content": json.dumps(user_input)
        }
    ],
)

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

    files = collect_files(content_dir, ignore_files)
    logging.info(f'Files content: {files}')

    with open('main_task.txt', 'r') as f:
        main_task = f.read()

    with open('prompt_history.txt', 'r') as f:
        prompt_history = f.read()

    with open('prompt_history.txt', 'a') as f:
        f.write(f'\n\n{datetime.datetime.now()} {prompt}')


    updated_files = call_ai(f'Previous tasks: ({prompt_history}). Current task: **{prompt}**', files, main_task)
    logging.info(f'Updated files: {updated_files}')
    write_files(content_dir, updated_files)
    print("Files updated.")

if __name__ == "__main__":
    main()
