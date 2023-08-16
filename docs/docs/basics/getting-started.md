---
sidebar_position: 2
---

# Getting Started

Here's a quick example to get you started:

```python
import wombat
import os

# initialise
w = wombat.Wombat(dataset_path=os.environ['WOMBAT_DATA_PATH'])

# set city
w.set_city("Brisbane")

# query elevation information
elevation = w.Elevation.get_elevation(lat,lon)
print(elevation)

# query school information
schools = w.Schools.get_schools_within_radius(lat,lon,radius)
print(schools)
```
