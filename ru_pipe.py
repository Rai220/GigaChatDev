from pathlib import Path
from tqdm.auto import tqdm
import os
from time import gmtime, strftime

CONFIG = {
    "LANGCHAIN_TRACING_V2": "true",
    "LANGCHAIN_ENDPOINT": "https://api.smith.langchain.com",
    "OPENAI_API_KEY": "",
    "LANGCHAIN_API_KEY": "",
    "LANGCHAIN_PROJECT": None,
}


prompts_paths = [
    Path("./ru_promts/Gomoku.prompt"),
]
ORG_NAME = "tmp"
SPECIFIC_NAME = "DEBUG"

RUN_PATH = "run.py"
for i in range(1):
    for path in prompts_paths:
        _name = path.stem

        name = _name + f"_{SPECIFIC_NAME}_{i}"
        cur_time = strftime("%Y-%m-%d-%H-%M-%S", gmtime())
        project_name = f"{name}_{cur_time}_dl_n2"
        with open(path) as f:
            task = "\n".join(f.readlines())
        print(path)
        CONFIG["LANGCHAIN_PROJECT"] = project_name
        print(CONFIG)
        for k, v in CONFIG.items():
            os.environ[k] = v
        command = f'python {RUN_PATH} --task "{task}" --name {name} --model GPT_4 --org {ORG_NAME}_{i}'
        os.system(command)
