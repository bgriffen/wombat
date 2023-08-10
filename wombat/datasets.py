import geopandas as gpd
from geopandas.tools import sjoin
from shapely.geometry import Point
import wombat.helper as helper
import os

def polygons_within_radius(gdf,lat,lon,radius):
    """Find polygons within a given radius of a center point.
    
    Args:
        gdf (GeoDataFrame): A GeoDataFrame containing polygons.
        lat (float): The latitude of the center point.
        lon (float): The longitude of the center point.
        radius (float): The radius in kilometers.
    
    Returns:
        GeoDataFrame: A GeoDataFrame containing polygons that intersect with the buffered center point.
    """
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
    def __init__(self,dataset_path,dataset):
        self.folder = os.path.join(dataset_path,"boundary")
        self.dataset = dataset
        self.filename = os.path.join(self.folder,"%s.geojson"%dataset)
        self.gdf_full = gpd.read_file(self.filename)

    def set_city(self,city,radius=None):
        self.city = city
        if radius is not None:
            self.set_radius(radius)
        else:
            #search_string = "Greater " + self.city
            #self.gdf = self.gdf_full[self.gdf_full['GCC_NAME21']==search_string]
            mask_city = self.gdf_full['GCC_NAME21'].str.contains(self.city)
            self.gdf = self.gdf_full[mask_city]
        self.names = sorted(list(set(self.gdf['SA3_NAME21'])))
        
    def set_radius(self,radius=10):
        latlon = helper.caplatlon[self.city]
        lat,lon = latlon[0],latlon[1]
        self.gdf = polygons_within_radius(self.gdf_full,lat,lon,radius)

class OpenStreetMap:
    def __init__(self,dataset_path):
        self.dataset_path = dataset_path
        self.pbf_path = os.path.join(dataset_path,"pbf")
    
    def generate_pbf_per_city(self):
        for city in helper.caplatlon.keys():
            print("Running...",city)
            boundary = Boundary(self.dataset_path)
            boundary.load()
            boundary.set_radius(20)
            boundary.gdf.to_file(os.path.join(self.pbf_path,city+".geojson"), driver='GeoJSON')