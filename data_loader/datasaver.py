import json

class DataSaver:
    def __init__(self):
        pass
    
    def save(self):
        raise NotImplementedError("Subclasses should implement this method.")

class JsonSaver(DataSaver):
    def save(self, path, content):
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(content, file, ensure_ascii=False, indent=4)