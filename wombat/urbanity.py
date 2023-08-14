import wombat.helper as helper
import urbanity as urb
import os
import pickle
from wombat.datasets import Datasets,City

class Urbanity(Datasets):
    def __init__(self,dataset_path,city):
        super().__init__(dataset_path,city)
#        self.dataset_path = dataset_path
#        self.city = city
       # self.zoom = zoom
        self.City = City(city)
        self.urb = urb.Map(country="Australia")
        self.urb.center = (self.City.lat,self.City.lon) #helper.caplatlon[city]
        self.tmp_file = 'tmp_region.geojson'
        print(self.pbf_path)
        
    def define_region(self,gdf):
        gdf.to_file(self.tmp_file, driver='GeoJSON')
        #self.map.add_polygon_boundary(self.tmp_file)
    
    def run(self,graph_attr=True,building_attr=True,pop_attr=True,svi_attr=True,poi_attr=True,bandwith=200):
        self.graph, self.nodes, self.edges = self.urb.get_street_network(filepath=self.pbf_filename,
                                                                        location=self.City.name,
                                                                        graph_attr=True,
                                                                        building_attr=True, 
                                                                        pop_attr=True, 
                                                                        svi_attr=True,
                                                                        poi_attr=True,
                                                                        bandwidth=200)
    
    def save(self):
        with open(os.path.join(self.City.name+".pickle"), 'wb') as file:
            pickle.dump(self.graph, file)
        self.nodes.to_file(os.path.join(self.dataset_path,"urbanity",self.City.name+"_nodes.geojson"), driver='GeoJSON')
        self.edges.to_file(os.path.join(self.dataset_path,"urbanity",self.City.name+"_edges.geojson"), driver='GeoJSON')
        self.stats.to_csv(os.path.join(self.dataset_path,"urbanity",self.City.name+"_stats.csv"))
        
    def aggregate(self,save=True):
        self.stats = self.urb.get_aggregate_stats(location=self.city,filepath=self.pbf_path,column="SA3_NAME21")
    
        # Method to run analysis across all listed cities
    def run_all_cities(self,gdf,radius=None):
        # Iterate over the list of cities
        for city in helper.caplatlon.keys():
            fpath = os.path.join(self.dataset_path,"pbf",city+"osm.pbf")
            # If file already exists, skip current iteration
            if os.path.exists(fpath):
                continue
            # Set city and define region for current city
            self.set_city(city,radius=radius)
            self.define_region(gdf)
            # Run urbanity analysis and aggregate results
            self.run()
            self.aggregate()
            # Save final results
            self.save()

