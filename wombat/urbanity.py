import wombat.helper as helper
import urbanity as urb

class Urbanity:
    def __init__(self,city,zoom):
        self.city = city
        self.zoom = zoom
        self.map = urb.Map(country="Australia",zoom=zoom)
        self.map.center = helper.caplatlon[city]
        
    def define_region(self,gdf):
        gdf.to_file('tmp_region.geojson', driver='GeoJSON')
        self.map.add_polygon_boundary('tmp_region.geojson')
    
    def run(self,pbf_path,graph_attr=True,building_attr=True,pop_attr=True,svi_attr=True,poi_attr=True,bandwith=200):
        self.graph, self.nodes, self.edges = self.map.get_street_network(filepath=pbf_path,location=self.city, 
                                               graph_attr=True,
                                               building_attr=True, 
                                               pop_attr=True, 
                                               svi_attr=True,
                                               poi_attr=True,
                                               bandwidth=200)
        