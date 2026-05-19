import osmnx as ox
import geopandas as gpd
from matplotlib import pyplot as plt
from matplotlib import patches as mpatches
import folium

REGION_NAME = "Waterloo, Ontario, Canada"

BUFFER_1200 = 1200
BUFFER_800 = 800
BUFFER_400 = 400

PNG_OUTPUT  = "waterloo_transit_map.png"
HTML_OUTPUT = "waterloo_transit_map.html"

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

utm_crs = residential.estimate_utm_crs()

road_edges = road_edges.to_crs(utm_crs)
residential = residential.to_crs(utm_crs)
transit = transit.to_crs(utm_crs)
healthcare = healthcare.to_crs(utm_crs)
education = education.to_crs(utm_crs)
grocery = grocery.to_crs(utm_crs)

transit_buffer = transit.geometry.buffer(BUFFER_1200).union_all()
healthcare_buffer = healthcare.geometry.buffer(BUFFER_1200).union_all()
education_buffer = education.geometry.buffer(BUFFER_1200).union_all()
grocery_buffer = grocery.geometry.buffer(BUFFER_1200).union_all()
all_services_buffer = transit_buffer.intersection(healthcare_buffer).intersection(education_buffer).intersection(grocery_buffer)

res_poly = residential[residential.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
total_area = res_poly.geometry.area.sum()
covered_area = res_poly.geometry.intersection(all_services_buffer).area.sum()
pct_ideal = covered_area / total_area * 100

def plot_layer(gdf, ax, color, markersize=4, linewidth=0, zorder=5):
    points = gdf[gdf.geometry.geom_type == "Point"]
    polys  = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]

    if not points.empty:
        points.plot(ax=ax, color=color, markersize=markersize, alpha=0.8, zorder=zorder)
    if not polys.empty:
        polys.plot(ax=ax, color=color, alpha=0.6, linewidth=linewidth, zorder=zorder)

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

plot_layer(transit_plot,    ax, "#4A90D9")
plot_layer(healthcare_plot, ax, "#E74C3C")
plot_layer(education_plot,  ax, "#F5A623")
plot_layer(grocery_plot,    ax, "#27AE60")

transit_buffer_gdf.plot(ax=ax, color="#4A90D9", alpha=0.2, linewidth=0)
healthcare_buffer_gdf.plot(ax=ax, color="#E74C3C", alpha=0.2, linewidth=0)
education_buffer_gdf.plot(ax=ax, facecolor="none", edgecolor="#F5A623", linewidth=0)
grocery_buffer_gdf.plot(ax=ax, color="#27AE60", alpha=0.2, linewidth=0)

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

plt.savefig(PNG_OUTPUT, dpi=150)
plt.show()

def add_service_points(gdf, feature_group, color, default_name):
    points = gdf[gdf.geometry.geom_type == "Point"]
    polys = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]

    for _, row in gdf.iterrows():
        pt = row.geometry.centroid
        name = row.get("name", default_name)
        if not isinstance(name, str):
            name = default_name
        folium.CircleMarker(
            location=[pt.y, pt.x],
            radius=4,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            tooltip=name
        ).add_to(feature_group)

        if not polys.empty:
            polys = polys.copy()
            polys["name"] = polys["name"].fillna(default_name)
            folium.GeoJson(
                polys,
                style_function=lambda _, c=color: {
                    "fillColor": c,
                    "color": "none",
                    "fillOpacity": 0.4
                },
                tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=[""], labels=False)
            ).add_to(feature_group)

centre_lat = (bounds[1] + bounds[3]) / 2
centre_lon = (bounds[0] + bounds[2]) / 2

map = folium.Map(
    location=[centre_lat, centre_lon],
    zoom_start=12,
    tiles="CartoDB dark_matter"
)

res_layer = folium.FeatureGroup(name="Residential Areas", show=True)
folium.GeoJson(
    residential_plot,
    style_function=lambda _: {
        "fillColor": "#FF6B9D",
        "color": "none",
        "fillOpacity": 0.4,
    },
).add_to(res_layer)
res_layer.add_to(map)

transit_layer = folium.FeatureGroup(name="Transit Buffer", show=True)
folium.GeoJson(
    transit_buffer_gdf,
    style_function=lambda _: {
        "fillColor": "#4A90D9",
        "color": "none",
        "fillOpacity": 0.4,
    }
).add_to(transit_layer)
add_service_points(transit_plot, transit_layer, color="#4A90D9", default_name="Transit Stop")
transit_layer.add_to(map)

healthcare_layer = folium.FeatureGroup(name="Healthcare Buffer", show=True)
folium.GeoJson(
    healthcare_buffer_gdf,
    style_function=lambda _: {
        "fillColor": "#E74C3C",
        "color": "none",
        "fillOpacity": 0.4,
    }
).add_to(healthcare_layer)
add_service_points(healthcare_plot, healthcare_layer, color="#E74C3C", default_name="Healthcare")
healthcare_layer.add_to(map)

education_layer = folium.FeatureGroup(name="Education Buffer", show=True)
folium.GeoJson(
    education_buffer_gdf,
    style_function=lambda _: {
        "fillColor": "#F5A623",
        "color": "none",
        "fillOpacity": 0.4,
    }
).add_to(education_layer)
add_service_points(education_plot, education_layer, color="#F5A623", default_name="Education")
education_layer.add_to(map)

grocery_layer = folium.FeatureGroup(name="Grocery Buffer", show=True)
folium.GeoJson(
    grocery_buffer_gdf,
    style_function=lambda _: {
        "fillColor": "#27AE60",
        "color": "none",
        "fillOpacity": 0.4,
    }
).add_to(grocery_layer)
add_service_points(grocery_plot, grocery_layer, color="#27AE60", default_name="Grocery")
grocery_layer.add_to(map)

folium.LayerControl(collapsed=False).add_to(map)

map.save(HTML_OUTPUT)

