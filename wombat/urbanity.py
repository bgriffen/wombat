import wombat.helper as helper
import urbanity as urb
import os
import pickle
class Urbanity:
    def __init__(self,dataset_path,city,zoom):
        self.dataset_path = dataset_path
        self.city = city
        self.zoom = zoom
        self.map = urb.Map(country="Australia",zoom=zoom)
        self.ma .center = helper.caplatlon[city]
        self.pbf_path = os.path.join(self.dataset_path,"pbf","Australia.osm.pbf")
        self.tmp_file = 'tmp_region.geojson'
        
    def define_region(self,gdf):
        gdf.to_file(self.tmp_file, driver='GeoJSON')
        self.map.add_polygon_boundary(self.tmp_file)
    
    def run(self,graph_attr=True,building_attr=True,pop_attr=True,svi_attr=True,poi_attr=True,bandwith=200):
        self.graph, self.nodes, self.edges = self.map.get_street_network(filepath=self.pbf_path,
                                                                        location=self.city, 
                                                                        graph_attr=True,
                                                                        building_attr=True, 
                                                                        pop_attr=True, 
                                                                        svi_attr=True,
                                                                        poi_attr=True,
                                                                        bandwidth=200)
    
    def save(self):
        with open(os.path.join(self.city+".pickle"), 'wb') as file:
            pickle.dump(self.graph, file)
        self.nodes.to_file(os.path.join(self.city+"_nodes.geojson"), driver='GeoJSON')
        self.edges.to_file(os.path.join(self.city+"_edges.geojson"), driver='GeoJSON')
        self.stats.to_csv(os.path.join(self.city+"_stats.csv"))
        
    def aggregate(self,save=True):
        self.stats = self.map.get_aggregate_stats(location=self.city,filepath=self.pbf_path,column="SA3_NAME21")
    
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

