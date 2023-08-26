import os,glob
import tempfile
import numpy as np
import pandas as pd
import geopandas as gpd
import wombat.helper as helper
from geopandas.tools import sjoin
import wombat.tools_buildings as tools_buildings
from wombat.datasets import Datasets,City
import shapely
import math

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

class Buildings(Datasets):
    def __init__(self, dataset_path,city):  
        super().__init__(dataset_path,city)
        self.City = City(city)
        self.buildings_msft = None
        self.buildings_osm = None
        self.buildings = None

    def make_footprints(self,gdf=None,radius=None):
        tools_buildings.make_footprints(city=self.City.name,dataset_path=self.dataset_path,gdf=gdf,radius=radius)

#   TODO - process building footprint information once tiles downloaded
#    def download(self,region_name="Australia"):
#        dataset_links_path = os.path.join(self.msft_path,"dataset-links.csv")
#        if not os.path.exists(dataset_links_path):
#            df = pd.read_csv("https://minedbuildings.blob.core.windows.net/global-buildings/dataset-links.csv")
#            df.to_csv(dataset_links_path,index=False)
#        else:
#            df = pd.read_csv(dataset_links_path)
#        df = df[df["Location"] == self.region]
#        download_urls(list(df['Url']),self.msft_path)

    def load(self,load_osm=False,load_msft=False,load_combined=True):
        
        if os.path.exists(self.msft_footprints_filename) and load_msft:
            print("...Microsoft")
            self.buildings_msft = gpd.read_file(self.msft_footprints_filename,drive="GeoJSON",engine='pyogrio')
            self.buildings_msft['is_osm'] = False
            
        if os.path.exists(self.osm_footprint_filename) and load_osm:
            print("...OSM")
            self.buildings_osm = gpd.read_file(self.osm_footprint_filename,drive="GeoJSON",engine='pyogrio')
            self.buildings_osm['is_osm'] = True
            
        if os.path.exists(self.combined_footprints_filename) and load_combined:
            self.buildings = gpd.read_file(self.combined_footprints_filename,drive="GeoJSON",engine='pyogrio')

    def calc_overlaps(self):
        self.buildings = tools_buildings.calc_intersection_between_msft_and_osm(self.buildings_msft,
                                                                                self.buildings_osm,
                                                                                fout=self.combined_footprints_filename)
        
    def add_buildings(self,map,which=None,nbuildings=None,bounding_box=False,bbox_width=1,center_latlon=None):
        #if reset:
        #    self.reset_map()

        self.which = which

        if which == "all":
            gdf = self.buildings
        if which == "msft":
            gdf = self.buildings_msft
        if which == "osm":
            gdf = self.buildings_osm

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

        map.add_gdf(rgdf,layer_name='Bounding Box', style={'color': 'black','fillOpacity':0},hover_style={'color': 'red','fillOpacity':0})

        #self.map.center = (south_west[0]+north_east[0])/2, (south_west[1]+north_east[1])/2
        #self.map.zoom=15

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
        if nbuildings is not None:
            self.buildings_gdf_filter = self.buildings_gdf_filter[:nbuildings].copy()
                
#        # Extract coordinates from polygons and generate geometry
#        aoi_geom = helper.generate_geom(list(self.buildings_gdf_filter['geometry'].iloc[0].exterior.coords))
#        # Create aoi_shape from the aoi_geom
#        aoi_shape = shapely.geometry.shape(aoi_geom)
#        # Calculate the centroid of the shape
#        centroid = aoi_shape.centroid
        # Set map center coordinates on the basis of centroid
#        self.map.center = (centroid.y, centroid.x)

        #print(f"The centroid for this layer are: {self.map.center}")

        #self.map = new_map(centroid.y, centroid.x,self.mapbox_token,zoom=self.zoom)
        if which == "all":
            mask_osm = self.buildings_gdf_filter['is_osm'] == True
            mask_msft = self.buildings_gdf_filter['is_osm'] == False
            if (mask_osm).any():
                map.add_gdf(self.buildings_gdf_filter[mask_osm],layer_name='OSM Buildings', style={'color': 'red','fillOpacity':0,'weight':1.3},hover_style={'color': 'red','fillOpacity':0.3,'weight':2.8})
            if (mask_msft).any():
                map.add_gdf(self.buildings_gdf_filter[mask_msft],layer_name='MSFT Buildings', style={'color': 'blue','fillOpacity':0,'weight':1.3},hover_style={'color': 'blue','fillOpacity':0.3,'weight':2.8})
        else:
            print(self.buildings_gdf_filter.shape)
            map.add_gdf(self.buildings_gdf_filter,layer_name='%s buildings'%which,show=False)
        return map
    
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

        # old way from downloading files
        # fout = os.path.join(self.msft_path,self.region+".json.gz")
        # if not os.path.exists(fout):
        #     if download:
        #         self.download()
        #     csv_files = glob.glob(self.dataset_path + '/**/*.csv.gz', recursive=True)
        #     dfs = []
        #     for f in tqdm(csv_files):
        #         dfi = pd.read_json(csv_files[0], compression='gzip', lines=True)
        #         fsplit = f.split("/")
        #         #dfi['RegionName'] = fsplit[-3].split("=")[1]
        #         dfi['Quad'] = int(fsplit[-2].split("=")[1])
        #         dfs.append(dfi)
        #     df = pd.concat(dfs,ignore_index=True)
        #     df.to_json(fout, compression='gzip')
        # self.buildings_msft_gdf = pd.read_json(fout, compression='gzip')

