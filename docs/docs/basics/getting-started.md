---
sidebar_position: 2
---

# Getting Started

Here's a quick example to get you started:

```python
import wombat

# initialise
w = wombat()
w.set_city("Brisbane")

# get elevation information
elevation = w.elevation_at_latlong(lat,long)
print(elevation)

# get school information
schools = w.get_schools(top_seifa=True)
print(schools)
```
