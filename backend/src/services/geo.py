import math
from src.constants.geometry import EARTH_RADIUS_KM

def valid_coordinate(lat,lon):
 if not math.isfinite(lat) or not math.isfinite(lon) or not -90<=lat<=90 or not -180<=lon<=180:raise ValueError('纬度须在[-90,90]、经度在[-180,180]且为有限数')
def haversine_km(lat1,lon1,lat2,lon2):
 valid_coordinate(lat1,lon1);valid_coordinate(lat2,lon2)
 p1,p2=math.radians(lat1),math.radians(lat2)
 dlat=math.radians(lat2-lat1);dlon=math.radians(lon2-lon1)
 a=math.sin(dlat/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dlon/2)**2
 a=max(0,min(1,a))
 return 2*EARTH_RADIUS_KM*math.atan2(math.sqrt(a),math.sqrt(1-a))
def distance_matrix(points,candidates):
 return [[haversine_km(c['latitude'],c['longitude'],p['latitude'],p['longitude']) for p in points] for c in candidates]
