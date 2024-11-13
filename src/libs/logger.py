import os
import logging
from pathlib import Path

def set_logger(name):
    index = 0
    folder_path = Path(f"./logs/{name}")
    folder_path.mkdir(parents=True, exist_ok=True)
   
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    indexes = []
    for file in files:
        print(file)
        indexes.append(int(file.split("_").pop()[0]))

    if len(indexes):
        index = max(indexes) + 1

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"./logs/{name}/pylog_{name}_{index}.log", mode='a'),
            logging.StreamHandler() 
        ]
    )
