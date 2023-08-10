import wombat.helper as helper
from wombat.urbanity import Urbanity
from wombat.datasets import Boundary
from wombat.buildings import Buildings
import os

class Wombat:
    # Initializing Wombat class with dataset_path and zoom level defaulting to 10
    def __init__(self,dataset_path,zoom=10):
        self.zoom = zoom
        self.dataset_path = dataset_path
        self.cities = sorted(helper.caplatlon.keys())
        
    # Method to load boundary data into the instance  
    def load(self,boundary_dataset):
        print("Loading boundary data...")
        self.Boundary = Boundary(self.dataset_path,dataset=boundary_dataset)
        
    # Method to set the city for analysis and initialize Urbanity object instance   
    def set_city(self,city,radius=None):
        self.city = city
        self.Boundary.set_city(city,radius)
        self.Urbanity = Urbanity(dataset_path=self.dataset_path,city=city,zoom=self.zoom)
        self.Buildings = Buildings(dataset_path=self.dataset_path,city=city)
        
    # Method to run urbanity analysis with various attributes and a fixed bandwidth of 200   
    def run_urbanity(self,graph_attr=True,
                     building_attr=True,
                     pop_attr=True,
                     svi_attr=True,
                     poi_attr=True,
                     bandwith=200):
  
        self.Urbanity.run(graph_attr=graph_attr,
                          building_attr=building_attr,
                          pop_attr=pop_attr,
                          svi_attr=svi_attr,
                          poi_attr=poi_attr,
                          bandwith=200)
        
