class DataLoader:
    def __init__(self, path):
        self.path = path
    
    def load(self):
        raise NotImplementedError("Subclasses should implement this method.")