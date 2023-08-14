import geopandas as gpd
from geopandas.tools import sjoin
from shapely.geometry import Point
import wombat.helper as helper
import os
from wombat.datasets import Datasets,City

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

class Boundary(Datasets):
    def __init__(self,dataset_path,city):
        super().__init__(dataset_path,city)
        self.dataset_path = dataset_path
        self.dataset = "SA3_2021_AUST_GDA2020"
        self.City = City(city)
        self.folder = os.path.join(dataset_path,"boundary")
        self.filename = os.path.join(self.folder,"%s.geojson"%self.dataset)
        
        fout = os.path.join(self.folder,self.dataset+"_"+f"{self.City.name}_boundary.geojson")
        print(fout)
        if not os.path.exists(fout):
            self.gdf_full = gpd.read_file(self.filename)
            if self.City.name == "Canberra":  # Hacky handling to sort out beloved ACT/Canberra
                mask_city = self.gdf_full['GCC_NAME21'].str.contains("Australian Capital Territory")
            else:
                mask_city = self.gdf_full['GCC_NAME21'].str.contains(self.City.name)
            self.gdf = self.gdf_full[mask_city]
            self.gdf.to_file(fout)
        else:
            self.gdf = gpd.read_file(fout)
      
        #if radius is not None:
        #    self.set_radius(radius)

        self.names = sorted(list(set(self.gdf['SA3_NAME21'])))
        
    def set_radius(self,radius=10):
        self.gdf = polygons_within_radius(self.gdf,self.City.lat,self.City.lon,radius)

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
            boundary.gdf.to_file(os.path.join(self.pbf_path,city.name+".geojson"), driver='GeoJSON')