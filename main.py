import osmnx as ox
import geopandas as gpd

REGION_NAME = "Waterloo Region, Ontario, Canada"

BUFFER_M = 800
U_BUFFER_M = 400

roads = ox.graph_from_place(REGION_NAME, network_type="drive")
_, road_edges = ox.graph_to_gdfs(roads)

residential = ox.features_from_place(
    REGION_NAME,
{"landuse": "residential"}
)
transit_stops = ox.features_from_place(
    REGION_NAME,
    {"highway": "bus_stop", "railway": ["station", "halt", "tram_stop"]}
)
universities = ox.features_from_place(
    REGION_NAME,
    {"amenity": "university"}
)

road_edges = road_edges.to_crs(epsg=32617)
residential = residential.to_crs(epsg=32617)
transit_stops = transit_stops.to_crs(epsg=32617)
universities = universities.to_crs(epsg=32617)

stop_centroids = transit_stops.copy()
stop_centroids["geometry"] = stop_centroids.geometry.centroid
transit_buffers = stop_centroids.geometry.buffer(BUFFER_M).union_all()
transit_buffers_gdf = gpd.GeoDataFrame(geometry=[transit_buffers], crs="epsg:32617")

res_poly = residential[residential.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
total_res_area = res_poly.geometry.area.sum()
covered_res_area = res_poly.geometry.intersection(transit_buffers).area.sum()
pct_covered_res_area = covered_res_area / total_res_area * 100

unis = universities.copy()
uni_buffers = unis.geometry.buffer(U_BUFFER_M).union_all()
uni_buffers_gdf = gpd.GeoDataFrame(geometry=[uni_buffers], crs="epsg:32617")

covered_by_uni = res_poly.geometry.intersection(uni_buffers).area.sum()
pct_covered_by_uni = covered_by_uni / total_res_area * 100


