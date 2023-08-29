import geopandas as gpd
from geopandas.tools import sjoin
from shapely.geometry import Point,Polygon
import wombat.helper as helper
import os
from wombat.datasets import Datasets,City
import glob
import fiona

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

def load_statistical_area(filename,layer,column_name=None,filter_value=None):
    gdf = gpd.read_file(filename,layer=layer)
    if column_name is not None:
        assert column_name in gdf.columns, print("Only these columns are available:",list(gdf.columns))
        subset_vals = gdf[column_name]
        unique_vals = sorted(list(set(subset_vals)))
        assert filter_value in unique_vals, print("Only these columns are available:",unique_vals)
        return gdf[subset_vals == filter_value]
    return gdf

Australia_BoundingBox = {
    'minx': 112.9519424,
    'miny': -43.7405093,
    'maxx': 153.9933464,
    'maxy': -9.1870234
}

Australia_BoundingBox_geom = Polygon([(Australia_BoundingBox['minx'],Australia_BoundingBox['miny']), 
                                      (Australia_BoundingBox['minx'],Australia_BoundingBox['maxy']), 
                                      (Australia_BoundingBox['maxx'],Australia_BoundingBox['maxy']),
                                      (Australia_BoundingBox['maxx'],Australia_BoundingBox['miny'])])

g = gpd.GeoSeries([Australia_BoundingBox_geom],crs="EPSG:4326")

class StatisticalArea:
    def __init__(self,filename,layer):
        self.filename = filename
        self.layer = layer
        # https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files
        
class Boundary(Datasets):
    def __init__(self,dataset_path):
        super().__init__(dataset_path)
        self.dataset_path = dataset_path
        
        files = glob.glob(os.path.join(self.boundary_path,"*.gpkg"))
        self.Areas = {}
        for filei in files:
            layers = fiona.listlayers(filei)
            for l in layers:
                self.Areas[l.split("_")[0]] = {'filename':filei,'layer':l}

        self.Australia_BoundingBox_Poly = gpd.GeoDataFrame(geometry=g)

    def set_area(self,statistical_area,column_name=None,filter_value=None):
        """_summary_
        Args:
            statistical_area (str): Statistical Area name
            column_name (str, optional): Column of the statistical area (e.g. "SA_NAME21"). Defaults to None.
            filter_value (str, optional): Value to filter over (e.g. "Greater Brisbane"). Defaults to None.
        """ 
        filename = self.Areas[statistical_area]['filename']
        layer = self.Areas[statistical_area]['layer']
        self.gdf = load_statistical_area(filename,
                                         layer,
                                         column_name=column_name,
                                         filter_value=filter_value)
        self.gdf = self.gdf[~self.gdf['geometry'].isna()]
        if "SA4_NAME_2021" in self.gdf.columns:
            self.sa4s = sorted(list(set(self.gdf['SA4_NAME_2021'])))
        if "SA3_NAME_2021" in self.gdf.columns:
            self.sa3s = sorted(list(set(self.gdf['SA3_NAME_2021'])))
        if "STATE_NAME_2021" in self.gdf.columns:
            self.state = sorted(list(set(self.gdf['STATE_NAME_2021'])))
        if "GCCSA_NAME_2021" in self.gdf.columns:
            self.gccsa = sorted(list(set(self.gdf['GCCSA_NAME_2021'])))

    def load_states_territories(self):
        self.gdf_states_territories = gpd.read_file(self.boundary_path_states_territories,engine='pyogrio')
        
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
            boundary.gdf.to_file(os.path.join(self.pbf_path,city.name+".geojson"), driver='GeoJSON',engine='pyogrio')