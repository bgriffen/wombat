import wombat.helper as helper
from wombat.urbanity import Urbanity
from wombat.boundary import Boundary
from wombat.buildings import Buildings
from wombat.visualise import Viz
#from wombat.datasets import Datasets
import os
import warnings
from shapely.errors import ShapelyDeprecationWarning
import ipyleaflet
from urbanity import utils

warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning) 
warnings.filterwarnings("ignore", category=UserWarning) 
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore')

from wombat.datasets import City

class Wombat:
    # Initializing Wombat class with dataset_path and zoom level defaulting to 10
    def __init__(self,dataset_path,zoom=10):
        self.zoom = zoom
        self.dataset_path = dataset_path

    # Method to set the city for analysis and initialize Urbanity object instance
    def set_city(self,city,radius=None):
        self.Boundary = Boundary(self.dataset_path,city=city)
        self.Urbanity = Urbanity(dataset_path=self.dataset_path,city=city)
        self.Buildings = Buildings(dataset_path=self.dataset_path,city=city)
        self.Viz = Viz(dataset_path=self.dataset_path,city=city,zoom=self.zoom)

    def load(self):
        self.Viz.load()
        
    def download_osm(self):
        self.Datasets.download_osm()

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
