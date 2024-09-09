import csv
from .base_dataloader import DataLoader

class CsvLoader(DataLoader):
    def load(self):
        with open(self.path, 'r') as file:
            reader = csv.reader(file)
            data = list(reader)
        return data

