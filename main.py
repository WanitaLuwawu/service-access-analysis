import osmnx as ox
import geopandas as gpd
from matplotlib import pyplot as plt
from matplotlib import patches as mpatches

REGION_NAME = "Waterloo, Ontario, Canada"

BUFFER_1200 = 1200
BUFFER_800 = 800
BUFFER_400 = 400

roads = ox.graph_from_place(REGION_NAME, network_type="drive")
_, road_edges = ox.graph_to_gdfs(roads)

residential = ox.features_from_place(
    REGION_NAME,
{"landuse": "residential"}
)
transit = ox.features_from_place(
    REGION_NAME,
    {
        "highway": "bus_stop",
        "railway": ["station", "halt", "tram_stop"],
        "public_transport": "platform"
    }
)
healthcare = ox.features_from_place(
    REGION_NAME,
    {"amenity": ["hospital", "clinic", "doctors", "pharmacy"]}
)
education = ox.features_from_place(
    REGION_NAME,
    {
        "amenity": ["school", "university", "college"],
        "landuse": "education"
    }
)
grocery = ox.features_from_place(
    REGION_NAME,
    {
        "shop": ["supermarket", "grocery", "convenience"],
        "amenity": "marketplace"
    }
)

road_edges = road_edges.to_crs(epsg=32617)
residential = residential.to_crs(epsg=32617)
transit = transit.to_crs(epsg=32617)
healthcare = healthcare.to_crs(epsg=32617)
education = education.to_crs(epsg=32617)
grocery = grocery.to_crs(epsg=32617)

transit_buffer = transit.geometry.buffer(BUFFER_1200).union_all()
healthcare_buffer = healthcare.geometry.buffer(BUFFER_1200).union_all()
education_buffer = education.geometry.buffer(BUFFER_1200).union_all()
grocery_buffer = grocery.geometry.buffer(BUFFER_1200).union_all()
all_services_buffer = transit_buffer.intersection(healthcare_buffer).intersection(education_buffer).intersection(grocery_buffer)

res_poly = residential[residential.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
total_area = res_poly.geometry.area.sum()
covered_area = res_poly.geometry.intersection(all_services_buffer).area.sum()
pct_ideal = covered_area / total_area * 100

fig, ax = plt.subplots(figsize=(10, 8))
manager = plt.get_current_fig_manager()
manager.window.wm_geometry("+50+50")
bounds = res_poly.to_crs(epsg=4326).total_bounds

ax.set_xlim(bounds[0] - 0.02, bounds[2] + 0.02)
ax.set_ylim(bounds[1] - 0.04, bounds[3] + 0.02)

road_edges_plot = road_edges.to_crs(epsg=4326)
residential_plot = residential.to_crs(epsg=4326)
transit_plot = transit.to_crs(epsg=4326)
healthcare_plot = healthcare.to_crs(epsg=4326)
education_plot = education.to_crs(epsg=4326)
grocery_plot = grocery.to_crs(epsg=4326)

transit_buffer_gdf     = gpd.GeoDataFrame(geometry=[transit_buffer],     crs="EPSG:32617").to_crs(epsg=4326)
healthcare_buffer_gdf  = gpd.GeoDataFrame(geometry=[healthcare_buffer],  crs="EPSG:32617").to_crs(epsg=4326)
education_buffer_gdf   = gpd.GeoDataFrame(geometry=[education_buffer],   crs="EPSG:32617").to_crs(epsg=4326)
grocery_buffer_gdf     = gpd.GeoDataFrame(geometry=[grocery_buffer],     crs="EPSG:32617").to_crs(epsg=4326)
road_edges_plot.plot(ax=ax, color="#333333", alpha=0.2, linewidth=0.3)

residential_plot.plot(ax=ax, color="#FF6B9D", alpha=0.6, linewidth=0)

transit_buffer_gdf.plot(ax=ax, color="#4A90D9", alpha=0.2, linewidth=0)
healthcare_buffer_gdf.plot(ax=ax, color="#E74C3C", alpha=0.2, linewidth=0)
education_buffer_gdf.plot(ax=ax, color="#F5A623", alpha=0.2, linewidth=0)
grocery_buffer_gdf.plot(ax=ax, color="#27AE60", alpha=0.2, linewidth=0)

transit_plot.plot(ax=ax, color="#4A90D9", markersize=4, alpha=0.8, zorder=5)
healthcare_plot.plot(ax=ax, color="#E74C3C", markersize=6, alpha=0.8, zorder=5)
education_plot.plot(ax=ax, color="#F5A623", markersize=6, alpha=0.8, zorder=5)
grocery_plot.plot(ax=ax, color="#27AE60", markersize=6, alpha=0.8, zorder=5)

ax.tick_params(axis='both', which='major', labelsize=8, length=2, width=0.5)

legend_items = [
    mpatches.Patch(color="#FF6B9D", alpha=0.8,  label="Residential"),
    mpatches.Patch(color="#4A90D9", alpha=0.5,  label="Transit (1200m buffer)"),
    mpatches.Patch(color="#E74C3C", alpha=0.5,  label="Healthcare (1200m buffer)"),
    mpatches.Patch(color="#F5A623", alpha=0.5,  label="Education (1200m buffer)"),
    mpatches.Patch(color="#27AE60", alpha=0.5,  label="Food / Grocery (1200m buffer)"),
]
ax.legend(handles=legend_items, loc="lower left", fontsize=8, framealpha=0.9)
ax.set_title(
    f"Waterloo Region — 15-Minute City Analysis\n"
    f"{pct_ideal:.1f}% of residential area within 1200m of all essential services",
    fontsize=12, fontweight="bold", pad=12
)

plt.show()


