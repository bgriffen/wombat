import wombat.helper as helper
from wombat.urbanity import Urbanity
from wombat.datasets import Boundary

class Wombat:
    def __init__(self,dataset_path,zoom=10):
        self.zoom = zoom
        self.dataset_path = dataset_path
        self.Boundary = Boundary(dataset_path)
        self.Urbanity = Urbanity(dataset_path,self.zoom)
        
    def set_city(city):
        self.city = city
        self.Boundary.load(city)
        
    def run_urbanity(self):
        self.Urbanity.run(self.Boundary.gdf)