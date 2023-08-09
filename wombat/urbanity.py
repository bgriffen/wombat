import wombat.helper as helper
import urbanity as urb

class Urbanity:
    def __init__(self,city,zoom=10):
        self.city = city
        self.map = urb.Map(country="Australia",zoom=zoom)
        self.map.center = helper.caplatlon[city]
        
    def run(self,gdf):
        gdf.to_file('tmp_region.geojson', driver='GeoJSON')
        self.map.add_polygon_boundary('tmp_region.geojson')
        
