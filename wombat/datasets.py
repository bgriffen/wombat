import geopandas as gpd
from geopandas.tools import sjoin
from shapely.geometry import Point
import wombat.helper as helper
import os

def polygons_within_radius(gdf,lat,lon,radius):
        center_point = gpd.GeoDataFrame(geometry=gpd.points_from_xy([lon],[lat]), crs='EPSG:4326')
        
        # Ensure that GeoJSON is in same CRS as the center point
        gdf = gdf.to_crs(center_point.crs)

        # Buffer center point by 10km radius (assuming the CRS is in degrees, 
        # if it's in meters, adjust the buffer value accordingly)
        center_point.geometry = center_point.geometry.buffer(radius/111.32) # Rough conversion from km to degrees

        # Use spatial join to find polygons that intersect with buffered center point
        polygons_in_radius = sjoin(gdf, center_point, op='intersects')
        return polygons_in_radius 
    
class Boundary:
    def __init__(self,dataset_path):
        self.folder = os.path.join(dataset_path,"boundary")
        self.filename = os.path.join(self.folder,"SA3_2021_AUST_GDA2020.geojson")
        
    def load(self,city):
        self.city = city
        self.gdf_full = gpd.read_file(self.filename)
        self.set_radius()
        
    def set_radius(self,radius=10):
        latlon = helper.caplatlon[self.city]
        lat,lon = latlon[0],latlon[1]
        self.gdf = polygons_within_radius(self.gdf_full,lat,lon,radius)
