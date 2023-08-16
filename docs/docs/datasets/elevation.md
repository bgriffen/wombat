---
sidebar_position: 1
---

# Elevation

Please check out [this summary of the basic concepts](https://www.neonscience.org/resources/learning-hub/tutorials/chm-dsm-dtm-gridded-lidar-data) for Digital Elevation Models (DEM) from Neon. First however is the distinction between DTMs and DSMs. Their figure highlights the main points.

![neonscience](https://raw.githubusercontent.com/NEONScience/NEON-Data-Skills/dev-aten/graphics/lidar-derived-products/DSM-DTM.png)

Additionally, there are a great many DEM datasets available globally, particularly for the US and Europe. These options are nicely highlighted [at this repository](https://github.com/DahnJ/Awesome-DEM).

## Goals

What we ideally need is a single tiff tile that provides decent elevation estimates for a given latitude and longitude across all of Australia. 

We can then simply point to this (large) tiff, and apply an elevation model in Python.

```python
from osgeo import gdal

class ElevationModel:
    def __init__(self, filename, geojson_file):
        self.ds = gdal.Open(filename)
        # Load GeoJSON file data
        with open(geojson_file) as f:
            self.geo_json_data = json.load(f)

    def get_elevation(self, lon, lat):
        gt = self.ds.GetGeoTransform()
        x = int((lon - gt[0]) / gt[1])
        y = int((lat - gt[3]) / gt[5])

        return self.ds.ReadAsArray(x, y, 1, 1)[0][0]
```

Which we can then call via:

```
model = ElevationModel('elevation.tif')

# Let's try Sydney (151.209900, -33.865143)
lon,lat = wombat.datasets.caplatlon['Sydney']

# Calculate elevation
elevation = model.get_elevation(lon, lat)

print(f"Elevation at {lon}, {lat} is {elevation}")
```

This can then be used and extended to calculate viewsheds, walkability metrics and provide to our property pricing models to name a few.

## ELVIS

One primary source of elevation data for Australia via the [ELVIS](https://elevation.fsdf.org.au/)

![elvis](./elvis.jpg)

This data consists of the following: 

* Combined state and national datasets
* Generally lidar-derived data
* Resolutions include: 1m, 2m, 5m, 1 second
* Complete coverage for NSW, Victoria and Tasminia with partial coverage in other state/territories
* Bathymetry also provided for surrounding waters

One can access the [LiDAR 5 Metre Grid models](https://ecat.ga.gov.au/geonetwork/srv/eng/catalog.search#/metadata/89644) from GeoScience Australia, though the piecemeal nature of it makes creating a generalised elevation map for each city is challenging. 

The only government dataset that seems to provides a manageable dataset and achieves out goal:

* [1 second SRTM Level 2 Derived Digital Elevation Model v1.0](https://ecat.ga.gov.au/geonetwork/srv/eng/catalog.search#/metadata/69816)

Which has since been updated (2010) to address several issues in the original dataset.

* [1 second SRTM Level 2 Derived Smoothed Digital Elevation Model (DEM-S) version 1.0 (41GB)](https://researchdata.edu.au/1-second-srtm-version-10/1439881)

> *The 1 second Shuttle Radar Topographic Mission (SRTM) derived smoothed Digital Elevation Model (DEM-S) Version 1.0 is a 1 arc second (~30m) gridded smoothed version of the DEM (ANZCW0703013355). The DEM-S represents ground surface topography, excluding vegetation features, and has been smoothed to reduce noise and improve the representation of surface shape. The dataset was derived from the 1 second Digital Elevation Model Version 1.0 (DSM; ANZCW0703013336) by an adaptive smoothing process that applies more smoothing in flatter areas than hilly areas, and more smoothing in noisier areas than in less noisy areas. This DEM-S supports calculation of local terrain shape attributes such as slope, aspect and curvatures that could not be reliably derived from the unsmoothed DEM because of noise. A full description of the methods is in progress (Gallant et al., in prep) and in the User Guide (Geoscience Australia & CSIRO, 2010).* <br>~Gallant, J. ; Tickle, P.K. ; Wilson, N. ; Dowling, T. ; Read, A. (2010)

Upon downloading this 40GB file, we can check the extent to verify it's coverage:

```python
import matplotlib.pyplot as plt
import geopandas as gpd
import rasterio
from shapely.geometry import shape, box

import wombat

w = wombat.Wombat()

# Path to elevation tif file
tif_file = w.Datasets.elevation_tif_filename

# State and territory boundaries
w.Boundary.load_states_territories()
gdf = w.Boundary.gdf_states_territories

fig,ax = plt.subplots(constrained_layout=True)
gdf.plot(color='white', edgecolor='black',ax=ax)

# Load the TIFF file
src = rasterio.open(tif_file)

# Retrieve the TIFF file's polygon coordinates
left,bottom,right,top = src.bounds

# Create a new GeoDataFrame for the TIFF
tiff_gdf = gpd.GeoDataFrame({'geometry': [box(left,bottom,right,top)]}, 
                            crs=src.crs.to_string())
tiff_gdf = tiff_gdf.to_crs(gdf.crs)

# Plot tiff coverage area over the top of the country boundary
tiff_gdf.plot(ax=ax, facecolor='none', edgecolor='red',linewidth=2)

# Title for the plot
plt.title("Elevation Data Coverage")

# Show the plot
plt.show()
```

There are however other options which have be explored.

## TessaDM
[TessaDM](https://tessadem.com/) provides an API to access elevation data globally. 

![Tessa](TessaDM.jpg)

The downside is that it is per request and there is no free cap available. From their page *"Elevation data were merged and adjusted from multiple sources according to tree height, urbanization and water presence using AW3D30, MERIT DEM, Forest Height, World Settlement Footprint and Global Surface Water"*. You can download the raw binary files (405GB) but this is overkill for our needs.

## FABDEM 
Lastly, there are some more advanced models coming online such as FABDEM by the University of Bristol. FABDEM (Forest And Buildings removed Copernicus DEM) is a global elevation map that removes building and tree height biases from the [Copernicus GLO 30 Digital Elevation Model](https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model) (DEM). The data is available at 1 arc second grid spacing (approximately 30m at the equator) for the globe.

You can download the entire dataset for the Earth [here](https://data.bris.ac.uk/data/dataset/s5hqmjcdj8yo2ibzi9b4ew3sn). https://data.bris.ac.uk/data/dataset/s5hqmjcdj8yo2ibzi9b4ew3sn. For our purposes we only need the tiles for our interested areas. Fortunately in the v1.2 release, the tileset has been provided so those specific tiles for the capitals can be acquired. The tileset for Australis looks as follows:

![FABDEM](FABDEM_tiles.jpg)

The individual tiles that overlap with the major capital cities are as follows:

| tile_name | file_name | zipfile_name |
| --- | --- | --- |
| S013E130 | S013E130_FABDEM_V1-2.tif | S20E130-S-10E140_FABDEM_V1-2.zip |
| S028E152 | S028E152_FABDEM_V1-2.tif | S30E150-S-20E160_FABDEM_V1-2.zip |
| S028E153 | S028E153_FABDEM_V1-2.tif | S30E150-S-20E160_FABDEM_V1-2.zip |
| S032E115 | S032E115_FABDEM_V1-2.tif | S40E110-S-30E120_FABDEM_V1-2.zip |
| S033E115 | S033E115_FABDEM_V1-2.tif | S40E110-S-30E120_FABDEM_V1-2.zip |
| S034E150 | S034E150_FABDEM_V1-2.tif | S40E150-S-30E160_FABDEM_V1-2.zip |
| S034E151 | S034E151_FABDEM_V1-2.tif | S40E150-S-30E160_FABDEM_V1-2.zip |
| S035E138 | S035E138_FABDEM_V1-2.tif | S40E130-S-30E140_FABDEM_V1-2.zip |
| S036E149 | S036E149_FABDEM_V1-2.tif | S40E140-S-30E150_FABDEM_V1-2.zip |
| S038E144 | S038E144_FABDEM_V1-2.tif | S40E140-S-30E150_FABDEM_V1-2.zip |
| S038E145 | S038E145_FABDEM_V1-2.tif | S40E140-S-30E150_FABDEM_V1-2.zip |
| S043E147 | S043E147_FABDEM_V1-2.tif | S50E140-S-40E150_FABDEM_V1-2.zip |

We can then simply loop through these files and download them locally.

```python
import wget
import pandas as pd

# set downloads
output_folder = "/path/to/downloads/"

# download capital city tile info
df = pd.read_csv("FABDEM.csv")

# set base download path
url_base = "https://data.bris.ac.uk/datasets/s5hqmjcdj8yo2ibzi9b4ew3sn"

# loop through each zipfile
for fname in list(set(df['zipfile_name'])):
    url_full = url_base+"/"+fname.replace("-S-","-S")
    wget.download(url_full,output_folder)
```

