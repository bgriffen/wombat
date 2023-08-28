import numpy as np

def distance(s_lat, s_lng, e_lat, e_lng):
    """Calculate the distance between two points on the Earth's surface using the Haversine formula.
    
    Args:
        s_lat (float): Latitude of the starting point in degrees.
        s_lng (float): Longitude of the starting point in degrees.
        e_lat (float): Latitude of the ending point in degrees.
        e_lng (float): Longitude of the ending point in degrees.
    
    Returns:
        float: The distance between the two points in kilometers.
    """
    # Alternative but slower I believe
    # from sklearn.metrics.pairwise import haversine_distances
    # hd = haversine_distances( data[['lat','long']].apply(np.deg2rad).values ,dfschool[['Latitude','Longitude']].apply(np.deg2rad).values)* 6373000/1000
    
    R = 6373.0  # radius of earth

    s_lat = s_lat * np.pi / 180.0
    s_lng = np.deg2rad(s_lng)
    e_lat = np.deg2rad(e_lat)
    e_lng = np.deg2rad(e_lng)

    d = np.sin((e_lat - s_lat) / 2) ** 2 + np.cos(s_lat) * np.cos(e_lat) * np.sin((e_lng - s_lng) / 2) ** 2

    return 2 * R * np.arcsin(np.sqrt(d))

#def distance_to_cbd(d_lat, d_lng, s_lat, s_lng):
#    return distance(d_lat, d_lng, s_lat, s_lng)
