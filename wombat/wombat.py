import wombat.helper as helper
#from wombat.urbanity import Urbanity
from wombat.boundary import Boundary
from wombat.buildings import Buildings
from wombat.visualise import Viz
from wombat.schools import Schools
from wombat.datasets import Datasets,City
from wombat.elevation import Elevation
import os
import warnings
from shapely.errors import ShapelyDeprecationWarning
#import ipyleaflet
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning) 
warnings.filterwarnings("ignore", category=UserWarning) 
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore')
warnings.filterwarnings("ignore", category=DeprecationWarning)

from wombat.datasets import City

import platform
import leafmap.foliumap as leafmap

class Wombat(leafmap.Map):
    # Initializing Wombat class with dataset_path and zoom level defaulting to 10
    def __init__(self,**kwargs):
    
        super().__init__(**kwargs)
        
        self.zoom = 10
        self.dataset_path = dataset_path
        self.Datasets = Datasets(self.dataset_path)
        self.Boundary = Boundary(self.dataset_path)
        self.Elevation = Elevation(self.dataset_path)
        self.map = leafmap.Map()
        
    # Method to set the city for analysis and initialize Urbanity object instance
    def set_city(self,city,radius=None):
        self.Boundary = Boundary(self.dataset_path,city=city)
        #self.Urbanity = Urbanity(dataset_path=self.dataset_path,city=city)
        self.Buildings = Buildings(dataset_path=self.dataset_path,city=city)
        #self.Viz = Viz(dataset_path=self.dataset_path,city=city,zoom=self.zoom)
        self.Schools = Schools(dataset_path=self.dataset_path,city=city)
        self.Elevation = Elevation(dataset_path=self.dataset_path,city=city)
        self.City = self.City = City(city)
        self.Datasets = Datasets(self.dataset_path,city=city)
        self.map = leafmap.Map(location=[self.City.lat,self.City.lon],zoom_start=self.zoom)
        
    def download_osm(self):
        self.Datasets.download_osm()

    def add_sa3_boundary(self):
        self.map = leafmap.Map(location=[self.City.lat,self.City.lon],zoom_start=self.zoom)
        self.map.add_gdf(self.Boundary.gdf.copy(),layer_name='[ SA3 Boundary ] %s'%self.City.name)
    
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
