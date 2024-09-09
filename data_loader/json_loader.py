import json
from .base_dataloader import DataLoader

class JsonLoader(DataLoader):
    def __init__(self, path):
        DataLoader.__init__(self, path)

    def load(self):
        with open(self.path, 'r') as file:
            data = json.load(file)
        return data