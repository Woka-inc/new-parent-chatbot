import json

class DataSaver:
    def __init__(self, path, content):
        self.path = path
        self.content = content
    
    def save(self):
        raise NotImplementedError("Subclasses should implement this method.")

class JsonSaver(DataSaver):
    def save(self):
        with open(self.path, 'w', encoding='utf-8') as file:
            json.dump(self.content, file, ensure_ascii=False, indent=4)