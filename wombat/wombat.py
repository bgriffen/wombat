import wombat.helper as helper
#from wombat.urbanity import Urbanity
from wombat.boundary import Boundary
from wombat.buildings import Buildings
#from wombat.visualise import WombatMap
from wombat.schools import Schools
from wombat.datasets import Datasets,City
from wombat.elevation import Elevation
import os
import warnings
import platform

from shapely.errors import ShapelyDeprecationWarning
#import ipyleaflet
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning) 
warnings.filterwarnings("ignore", category=UserWarning) 
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore')
warnings.filterwarnings("ignore", category=DeprecationWarning)

from wombat.datasets import City
import geopandas as gpd
import leafmap.foliumap as leafmap

def new_map(center,zoom=10):
    mymap = leafmap.Map() #location=center,zoom_start=zoom)
    #mymap.add_basemap("CartoDB.VoyagerNoLabels", shown=False)
    #mymap.add_tile_layer(url="http://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", name = 'Google Streets',attribution="Google", shown=True)
    #mymap.add_tile_layer(url="http://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", name = 'Google Satellite',attribution="Google", shown=False)
    #mymap.add_tile_layer(url="http://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}", name = 'Google Terrain',attribution="Google", shown=False)
    #mymap.add_tile_layer(url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",name = "Google Hybrid",attribution="Google", shown=False)
    #mymap.attribution_control = True
    return mymap

get_gccs_name = {"Canberra":"Australian Capital Territory",
                "Brisbane":"Greater Brisbane",
                "Hobart":"Greater Hobart",
                "Adelaide":"Greater Adelaide",
                "Darwin":"Greater Darwin",
                "Melbourne":"Greater Melbourne",
                "Sydney":"Greater Sydney",
                "Perth":"Greater Perth"}

def graph_to_geopandas(item):
    return gpd.GeoDataFrame(item,crs='EPSG:4326')
    
class Wombat(leafmap.Map):
    def __init__(self,dataset_path,**kwargs): #='E:\\ResilioData\\Datasets\\wombatdata\\'
        super().__init__(**kwargs)
        
        self.dataset_path = dataset_path
        self.Datasets = Datasets(self.dataset_path)
        self.Boundary = Boundary(self.dataset_path)
        self.Elevation = Elevation(self.dataset_path)
        #self.zoom = 10
        #self.mymap.add_tile_layer(url="http://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}", name = 'Google Satellite',attribution="Google", shown=False)
        #self.Map = new_map(center=[-27.4698, 153.0251],zoom=self.zoom)
        #self.country = country
    
    def set_area_as_country(self):
        self.gdf = self.Boundary.get_country()
        
    def set_area_as_state(self,state=None):
        self.gdf = self.Boundary.get_state(state)
    
    def set_area_as_states(self):
        self.gdf = self.Boundary.get_states()
    
    def set_area_as_sa4(self,belonging_to):
        self.gdf = self.Boundary.get_sa4(belonging_to)
      
    def set_area_as_sa3(self,belonging_to):
        self.gdf = self.Boundary.get_sa3(belonging_to)
    
    def set_area_as_sa2(self,belonging_to):
        self.gdf = self.Boundary.get_sa2(belonging_to)
        
    def set_area_as_sa1(self,belonging_to):
        self.gdf = self.Boundary.get_sa1(belonging_to)
    
    def set_area_as_meshblocks(self,belonging_to):
        self.gdf = self.Boundary.get_meshblocks(belonging_to)
        
    # Method to set the city for analysis and initialize Urbanity object instance
    def set_area_as_city(self,city):
        self.gdf = self.Boundary.get_gcc(city)
        #self.Urbanity = Urbanity(dataset_path=self.dataset_path,city=city)
        self.Buildings = Buildings(dataset_path=self.dataset_path,city=city)
        #self.Viz = Viz(dataset_path=self.dataset_path,city=city,zoom=self.zoom)
        self.Schools = Schools(dataset_path=self.dataset_path,city=city)
        self.Elevation = Elevation(dataset_path=self.dataset_path,city=city)
        self.City = self.City = City(city)
        self.Datasets = Datasets(self.dataset_path,city=city)
        #self.map = leafmap.Map(location=[self.City.lat,self.City.lon],zoom_start=self.zoom)
        #self.set_center(self.City.lon,self.City.lat)
        #self.fit_bounds(self.get_bounds(), padding=(30, 30))
        
    def download_osm(self):
        self.Datasets.download_osm()
        
    def remove_polygon_boundary(self) -> None:
        """Removes polygon boundary from map object.
        """        
        polygon_exists = False
        for i in self.layers:
            if isinstance(i, ipyleaflet.leaflet.GeoData):
                polygon_exists = True
        if polygon_exists:
            self.remove_layer(self.layers[len(self.layers)-1])
            print('Polygon bounding layer removed.')
        else:
            print('No polygon layer found on map.')

    def show_boundary(self):
        #self.Map = new_map([self.City.lat,self.City.lon],zoom=self.zoom)
        self.add_gdf(self.Boundary.gdf.copy(),layer_name='[ SA3 Boundary ] %s'%self.City.name)
    
    def show_schools(self,secondary_catchment=True,
                          primary_catchment=True,
                          combined_schools=True):
        
        #self.Schools.df_filter = self.Schools.get_schools_within_latlon_radius(radius=radius) # kms
        
        #if junior_catchment: 
        #    self.add_gdf(self.Schools.gdf_junior.copy(),layer_name='Junior Catchment', style={'color': 'red','fillOpacity':0,'weight':1.3},hover_style={'color': 'red','fillOpacity':0.3,'weight':2.8})
            
        if primary_catchment: 
            self.add_gdf(self.Schools.gdf_primary.copy(),layer_name='Primary Catchment', style={'color': 'green','fillOpacity':0,'weight':1.3},hover_style={'color': 'green','fillOpacity':0.3,'weight':2.8})
            self.add_points_from_xy(
                                    self.Schools.df_primary[self.Schools.schoolcols+['Latitude','Longitude']],
                                    x="Longitude",
                                    y="Latitude",
                                    color_column='School Type',
                                    icon_names=['child'],
                                    spin=False,
                                    add_legend=True,
                                    layer_name="Schools Locations"
                                )
        
        if secondary_catchment: 
            self.add_gdf(self.Schools.gdf_secondary.copy(),layer_name='Secondary Catchment', style={'color': 'blue','fillOpacity':0,'weight':1.3},hover_style={'color': 'blue','fillOpacity':0.3,'weight':2.8})
            self.add_points_from_xy(
                                    self.Schools.df_secondary[self.Schools.schoolcols+['Latitude','Longitude']],
                                    x="Longitude",
                                    y="Latitude",
                                    color_column='School Type',
                                    icon_names=['users'],
                                    spin=False,
                                    add_legend=True,
                                    layer_name="Senior Schools"
                                )
        
        if combined_schools:       
            iconmap = {"Combined":"institution","Primary":"child","Secondary":"users","Special":"wheelchair"}
            icon_names = [iconmap[t] for t in list(set(self.Schools.df_combined['School Type']))]
        
            self.add_points_from_xy(
                                    self.Schools.df_combined[self.Schools.schoolcols+['Latitude','Longitude']],
                                    x="Longitude",
                                    y="Latitude",
                                    color_column='School Type',
                                    icon_names=icon_names,
                                    spin=False,
                                    add_legend=True,
                                    layer_name="Primary+Secondary"
                                )      
                  
        #from bs4 import BeautifulSoup
        #w.Schools.gdf_junior['Description']=w.Schools.gdf_junior.apply(lambda x: BeautifulSoup(x['Description']).get_text().replace('\n',' '),axis=1)
        #self.add_points_from_xy(dfs.head(), x="Longitude", y="Latitude")
        
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
