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
    def __init__(self, dataset_path,city):   #(self,city,dataset_path,kind='poly',region="Australia"):
        super().__init__(dataset_path,city)
        self.City = City(city)
        #self.city = city
        #self.kind = kind
        #self.dataset_path = os.path.join(dataset_path,"footprints")
        #self.msft_path = os.path.join(dataset_path,'footprints','microsoft_buildings')
        #self.pbf_path = os.path.join(dataset_path,'pbf/')
        #self.msft_footprints_filename = os.path.join(self.dataset_path,f"{self.city}_{kind}_msft_footprints.geojson")
        #self.osm_footprint_filename = os.path.join(dataset_path,'footprints',f"{self.city}_osm_footprints.geojson")
        #self.region = region
        #self.buildings_msft_gdf = None

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

    def load(self,download=False):
        self.msft_buildings = gpd.read_file(self.msft_footprints_filename)
        self.osm_buildings = tools_buildings.get_or_make_osm_footprints(self.City.name,self.pbf_path,self.osm_footprint_filename)

    def calc_overlaps(self):
        #tools_buildings.calc_overlaps(self.msft_buildings,self.osm_buildings)
        self.unique_buildings = tools_buildings.calc_intersection_between_msft_and_osm(self.msft_buildings,self.osm_buildings)

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

