import folium
from folium import GeoJson
from folium import Rectangle
from shapely.ops import transform
import wombat.helper as helper
import geopandas as gpd
import os
import shapely
from wombat.datasets import Datasets,City
import leafmap
import math
import urbanity

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



def get_bounding_box(latitude, longitude, distance_in_kms):
    # Earth’s radius, sphere
    R = 6378137

    # Offsets in meters
    dn = distance_in_kms*1000.
    de = distance_in_kms*1000.

    # Coordinate offsets in radians
    dLat = dn / R
    dLon = de / (R * math.cos(math.pi * latitude / 180))

    # OffsetPosition, decimal degrees
    lat_min = latitude - dLat * 180/math.pi
    lon_min = longitude - dLon * 180/math.pi
    lat_max = latitude + dLat * 180/math.pi
    lon_max = longitude + dLon * 180/math.pi
    
   # bounding_box = 
    return lon_min, lat_min, lon_max, lat_max

def filter_gdf_center_width(gdf,width,center):
    minx, miny, maxx, maxy = get_bounding_box(center[0],center[1],width)
    return filter_gdf_bbox(gdf,minx, miny, maxx, maxy)

def filter_gdf_bbox(gdf, minx, miny, maxx, maxy):
    bbbox = shapely.geometry.box(minx, miny, maxx, maxy)
    return gdf[gdf.geometry.intersects(bbbox)]

import pandas as pd

class Viz(Datasets):
    def __init__(self, dataset_path,city,zoom=14,kind='poly',mapbox_token=None):
        super().__init__(dataset_path,city)
        #self.map = new_map(center_latitude, center_longitude,mapbox_token,zoom=zoom)
        self.City = City(city)
        self.map = leafmap.Map()
        #country_center = urbanity.utils.get_country_centroids()['Australia']['coords']
        #self.map.center = country_center
        self.map.center = (self.City.lat,self.City.lon)
        self.map.zoom = zoom
        self.map.layout.height = "800px"
        self.map.layout.width = "100%"
        
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

    def reset_map(self):
        self.map = leafmap.Map()
        self.map.center = (self.City.lat,self.City.lon)
        self.map.zoom = 14
        self.map.layout.height = "800px"
        self.map.layout.width = "100%"
        self.map.center = (self.City.lat,self.City.lon)
        
    def load(self):
        print("Loading in the building footprints...")
        #if os.path.exists(self.combined_footprints_filename):
            #print("...combined")
            #self.buildings_gdf_combined = gpd.read_file(self.combined_footprints_filename)
        if os.path.exists(self.msft_footprints_filename):
            print("...Microsoft")
            self.buildings_gdf_msft = gpd.read_file(self.msft_footprints_filename)
            self.buildings_gdf_msft['is_osm'] = False
        if os.path.exists(self.osm_footprint_filename):
            print("...OSM")
            self.buildings_gdf_osm = gpd.read_file(self.osm_footprint_filename)
            self.buildings_gdf_msft['is_osm'] = True

        self.buildings_gdf_combined = tools_buildings.calc_intersection_between_msft_and_osm(self.buildings_gdf_msft,self.buildings_gdf_osm)

    def add_building_layer(self,which=None,nbuildings=None,bounding_box=False,bbox_width=1000,center_latlon=None,reset=True):
        if reset:
            self.reset_map()

        self.which = which

        if which == "all":
            gdf = self.buildings_gdf_combined
        if which == "msft":
            gdf = self.buildings_gdf_msft
        if which == "osm":
            gdf = self.buildings_gdf_osm

        self.buildings_gdf_filter = filter_gdf_center_width(gdf,width=bbox_width,center=center_latlon)
        lon_min, lat_min, lon_max, lat_max = get_bounding_box(center_latlon[0],center_latlon[1],bbox_width)
        south_west = (lat_min, lon_min)
        north_east = (lat_max, lon_max)
        # Assuming lon_list and lat_list are defined
        lon_list = [lon_min, lon_max, lon_max, lon_min]
        lat_list = [lat_min, lat_min, lat_max, lat_max]
        # Create the polygon using a list comprehension with zip
        rect_polygon = shapely.geometry.Polygon([point for point in zip(lon_list, lat_list)])
        rgdf = gpd.GeoDataFrame(index=[0], geometry=[rect_polygon])
        rgdf.crs="EPSG:4326"

        #{'style': {'color': 'black', 'fillColor': '#3366cc', 'opacity':0.05, 'weight':1.9, 'dashArray':'2', 'fillOpacity':0.6},
        #                                 'hover_style': {'fillColor': 'orange' , 'fillOpacity': 0.2}}

        self.map.add_gdf(rgdf,layer_name='Bounding Box', style={'color': 'black','fillOpacity':0},hover_style={'color': 'red','fillOpacity':0})

        self.map.center = (south_west[0]+north_east[0])/2, (south_west[1]+north_east[1])/2
        self.map.zoom=15

        building_color_osm = 'red'
        building_color_msft = 'blue'

        #if bounding_box:
        #    # Define the bounding box
        #    if center_latlon is None:
        #        center_latlon = helper.caplatlon[self.city]
        #    minx, miny, maxx, maxy = get_bounding_box(center_latlon[0],center_latlon[1],bbox_width)
        #    bbbox = shapely.geometry.box(minx, miny, maxx, maxy)
        #    # Filter the datasets by the bounding box
            #self.buildings_gdf = filter_by_bbox(self.buildings_gdf_full, bbbox)
        #else:
        #    if nbuildings is not None:
        #        self.buildings_gdf = self.buildings_gdf_full[:nbuildings]
                
#        # Extract coordinates from polygons and generate geometry
#        aoi_geom = helper.generate_geom(list(self.buildings_gdf_filter['geometry'].iloc[0].exterior.coords))
#        # Create aoi_shape from the aoi_geom
#        aoi_shape = shapely.geometry.shape(aoi_geom)
#        # Calculate the centroid of the shape
#        centroid = aoi_shape.centroid
        # Set map center coordinates on the basis of centroid
#        self.map.center = (centroid.y, centroid.x)

        print(f"The centroid for this layer are: {self.map.center}")

        #self.map = new_map(centroid.y, centroid.x,self.mapbox_token,zoom=self.zoom)
        if which == "all":
            mask_osm = self.buildings_gdf_filter['is_osm'] == True
            mask_msft = self.buildings_gdf_filter['is_osm'] == False
            if (mask_osm).any():
                self.map.add_gdf(self.buildings_gdf_filter[mask_osm],layer_name='OSM Buildings', style={'color': 'red','fillOpacity':0,'weight':1.3},hover_style={'color': 'red','fillOpacity':0.3,'weight':2.8})
            if (mask_msft).any():
                self.map.add_gdf(self.buildings_gdf_filter[mask_msft],layer_name='MSFT Buildings', style={'color': 'blue','fillOpacity':0,'weight':1.3},hover_style={'color': 'blue','fillOpacity':0.3,'weight':2.8})
        else:
            self.map.add_gdf(self.buildings_gdf_filter,layer_name='%s buildings'%which,show=False)

        #for _, r in gdf.iterrows():
        #    sim_geo = gpd.GeoSeries(r['geometry']).simplify(tolerance=0.001)
        #    geo_j = sim_geo.to_json()
        #    geo_j = folium.GeoJson(geo_j, name="Microsoft Building Footprints", style_function=lambda feature: {
        #                                'fillColor': building_color_osm,
        #                                'color': building_color_osm}
        #                               )
        #    folium.Popup(r['Name']).add_to(geo_j)
        #    geo_j.add_to(building_layer)
        #building_layer.add_to(self.map)
       # building_layer.add_to(self.map)

    def remove_layer(self, name):
        for child in self.map._children.values():
            if child.get_name() == name:
                self.map._children.pop(child.get_name())
    
    def show_map(self):
        folium.LayerControl().add_to(self.map)
        return self.map

