import wombat.helper as helper
from wombat.urbanity import Urbanity
from wombat.datasets import Boundary
import os
class Wombat:
    def __init__(self,dataset_path,zoom=10):
        self.zoom = zoom
        self.dataset_path = dataset_path
        
    def set_city(self,city):
        self.city = city
        self.Boundary = Boundary(self.dataset_path)
        self.Boundary.load(city)
        self.Urbanity = Urbanity(city=city,zoom=self.zoom)
        
    def run_urbanity(self,graph_attr=True,
                     building_attr=True,
                     pop_attr=True,
                     svi_attr=True,
                     poi_attr=True,
                     bandwith=200):

        #self.Urbanity.define_region(self.Boundary.gdf)
        
        self.pbf_path = os.path.join(self.dataset_path,"pbf",self.city+".osm.pbf")
        print(self.pbf_path)
        
        self.Urbanity.run(pbf_path=self.pbf_path,graph_attr=graph_attr,
                          building_attr=building_attr,
                          pop_attr=pop_attr,
                          svi_attr=svi_attr,
                          poi_attr=poi_attr,
                          bandwith=200)