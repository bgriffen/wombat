#import folium
#from folium import GeoJson
#from folium import Rectangle
from shapely.ops import transform
import wombat.helper as helper
import geopandas as gpd
import os
import shapely
from wombat.datasets import Datasets,City
#import leafmap.foliumap as leafmap
import math
#import folium
import json
from urllib.error import HTTPError
import wombat.tools_buildings as tools_buildings

def new_map(center_latitude, center_longitude,mapbox_token,zoom):
    folium_map = folium.Map(location=[center_latitude, center_longitude], zoom_start=zoom)
    folium.TileLayer(
            tiles='https://api.mapbox.com/styles/v1/mapbox/satellite-v9/tiles/{z}/{x}/{y}?access_token=' + mapbox_token,
            attr='Map Data &copy; <a href="https://www.mapbox.com/">Mapbox</a>',
            name='Mapbox Aerial',
        ).add_to(folium_map)
    return folium_map


import pandas as pd

class Viz:
    def __init__(self, dataset_path,city,zoom=14):
        #super().__init__(dataset_path,city)
        #self.map = new_map(center_latitude, center_longitude,mapbox_token,zoom=zoom)
        self.City = City(city)
        #self.map = leafmap.Map() #location=[self.City.lat,self.City.lon],zoom_start=zoom) #,height="700px",width="100%")
        #self.map.center = ()
        #self.map.zoom = zoom
        #self.map.layout.height = "800px"
        #self.map.layout.width = "100%"
        
        self.buildings_gdf_full = None
        #self.mapbox_token = mapbox_token

    def add_choropleth(self, geo_data, data, columns, key_on, fill_color='YlOrRd', fill_opacity=0.7, line_opacity=0.2, legend_name='Legend'):
        folium.Choropleth(
            geo_data=geo_data,
            data=data,
            columns=columns,
            key_on=key_on,
            fill_color=fill_color,
            fill_opacity=fill_opacity,
            line_opacity=line_opacity,
            legend_name=legend_name,
        ).add_to(self.map)   

        self.buildings_gdf_combined = tools_buildings.calc_intersection_between_msft_and_osm(self.buildings_gdf_msft,self.buildings_gdf_osm)
    
    def add_gdf(self,gdf):
        self.map.add_gdf(gdf)
        

    def remove_layer(self, name):
        for child in self.map._children.values():
            if child.get_name() == name:
                self.map._children.pop(child.get_name())
    
    def show_map(self):
        folium.LayerControl().add_to(self.map)
        return self.map

