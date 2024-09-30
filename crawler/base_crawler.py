from abc import *

class BaseCrawler:
    def __init__(self, path_to_save):
        self.base_url = None
        self.path_to_save = path_to_save
    
    @abstractmethod
    def get_contents_list(self):
        pass