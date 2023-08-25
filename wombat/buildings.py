import os,glob
import tempfile
import numpy as np
import pandas as pd
import geopandas as gpd
import wombat.helper as helper
from geopandas.tools import sjoin
import wombat.tools_buildings as tools_buildings
from wombat.datasets import Datasets,City

class Buildings(Datasets):
    def __init__(self, dataset_path,city):  
        super().__init__(dataset_path,city)
        self.City = City(city)
        self.msft_buildings = None
        self.osm_buildings = None
        self.builings = None

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
            self.buildings_gdf_combined = gpd.read_file(self.combined_footprints_filename,drive="GeoJSON",engine='pyogrio')

    def calc_overlaps(self):
        self.buildings = tools_buildings.calc_intersection_between_msft_and_osm(self.buildings_msft,
                                                                                self.buildings_osm,
                                                                                fout=self.combined_footprints_filename)

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

