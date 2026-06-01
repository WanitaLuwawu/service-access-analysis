import osmnx as ox
import geopandas as gpd
from matplotlib import pyplot as plt
from matplotlib import patches as mpatches
import folium
import os

# User input and configuration
def run(region_name, buffer, outputs):
    walk_time = {400: "5-Min", 800: "10-Min", 1200: "15-Min"}.get(buffer, "10-Min")

    # Generate file names
    clean_region = region_name.lower().replace(" ", "_").replace(",", "")
    clean_walk_time = walk_time.lower().replace("-", "_")
    DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
    PNG_OUTPUT = os.path.join(DOWNLOADS, f"{clean_region}_{clean_walk_time}_city_map.png")
    HTML_OUTPUT = os.path.join(DOWNLOADS, f"{clean_region}_{clean_walk_time}_city_map.html")

    # Data retrieval (OSMnx)
    roads = ox.graph_from_place(region_name, network_type="drive")
    _, road_edges = ox.graph_to_gdfs(roads)

    residential = ox.features_from_place(region_name, {"landuse": "residential"})
    residential = residential[residential.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]

    transit = ox.features_from_place(
        region_name,
        {
            "highway": "bus_stop",
            "railway": ["station", "halt", "tram_stop"],
            "public_transport": "platform"
        }
    )

    healthcare = ox.features_from_place(
        region_name,
        {"amenity": ["hospital", "clinic", "doctors", "pharmacy"]}
    )

    education = ox.features_from_place(
        region_name,
        {
            "amenity": ["school", "university", "college"],
            "landuse": "education"
        }
    )

    grocery = ox.features_from_place(
        region_name,
        {
            "shop": ["supermarket", "grocery", "convenience"],
            "amenity": "marketplace"
        }
    )

    # Coordinate projections and spatial analysis
    # Estimate the best local UTM zone to perform accurate metric buffering (meters)
    utm_crs = residential.estimate_utm_crs()

    road_edges = road_edges.to_crs(utm_crs)
    residential = residential.to_crs(utm_crs)
    transit = transit.to_crs(utm_crs)
    healthcare = healthcare.to_crs(utm_crs)
    education = education.to_crs(utm_crs)
    grocery = grocery.to_crs(utm_crs)

    # Generate service buffers
    transit_buffer = transit.geometry.buffer(buffer).union_all()
    healthcare_buffer = healthcare.geometry.buffer(buffer).union_all()
    education_buffer = education.geometry.buffer(buffer).union_all()
    grocery_buffer = grocery.geometry.buffer(buffer).union_all()

    # Find the intersection overlap of all services combined
    all_services_buffer = (transit_buffer
                           .intersection(healthcare_buffer)
                           .intersection(education_buffer)
                           .intersection(grocery_buffer))

    # Isolate valid residential polygon footprints
    res_poly = residential[residential.geometry.geom_type.isin(["Polygon", "MultiPolygon"])].copy()
    total_area = res_poly.geometry.area.sum()

    # Helper function to compute specific coverage numbers
    def get_coverage_pct(res_gdf, service_buffer):
        covered = res_gdf.geometry.intersection(service_buffer).area.sum()
        return (covered / total_area) * 100


    # Compute specific statistics across asset brackets
    pct_transit = get_coverage_pct(res_poly, transit_buffer)
    pct_healthcare = get_coverage_pct(res_poly, healthcare_buffer)
    pct_education = get_coverage_pct(res_poly, education_buffer)
    pct_grocery = get_coverage_pct(res_poly, grocery_buffer)
    pct_ideal = get_coverage_pct(res_poly, all_services_buffer)

    # Prepare datasets for plotting (WGS84 / EPSG:4326)
    road_edges_plot = road_edges.to_crs(epsg=4326)
    residential_plot = residential.to_crs(epsg=4326)
    transit_plot = transit.to_crs(epsg=4326)
    healthcare_plot = healthcare.to_crs(epsg=4326)
    education_plot = education.to_crs(epsg=4326)
    grocery_plot = grocery.to_crs(epsg=4326)

    # Dynamically project buffers using the accurate local UTM projection instead of hardcoded zones
    transit_buffer_gdf = gpd.GeoDataFrame(geometry=[transit_buffer], crs=utm_crs).to_crs(epsg=4326)
    healthcare_buffer_gdf = gpd.GeoDataFrame(geometry=[healthcare_buffer], crs=utm_crs).to_crs(epsg=4326)
    education_buffer_gdf = gpd.GeoDataFrame(geometry=[education_buffer], crs=utm_crs).to_crs(epsg=4326)
    grocery_buffer_gdf = gpd.GeoDataFrame(geometry=[grocery_buffer], crs=utm_crs).to_crs(epsg=4326)


    # Matplotlib static plot generation
    def plot_layer(gdf, ax, color, zorder=5):
        points = gdf[gdf.geometry.geom_type == "Point"]
        polys = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]

        if not points.empty:
            points.plot(ax=ax, color=color, markersize=4, alpha=0.8, zorder=zorder)
        if not polys.empty:
            polys.plot(ax=ax, color=color, alpha=0.4, linewidth=0, zorder=zorder)

    fig, ax = plt.subplots(figsize=(10, 8))
    manager = plt.get_current_fig_manager()
    manager.window.wm_geometry("+50+50")

    # Frame bounding window context around residential parcels
    bounds = res_poly.to_crs(epsg=4326).total_bounds
    ax.set_xlim(bounds[0] - 0.02, bounds[2] + 0.02)
    ax.set_ylim(bounds[1] - 0.04, bounds[3] + 0.02)

    # Plot background structural networks
    road_edges_plot.plot(ax=ax, color="#333333", alpha=0.2, linewidth=0.3)
    residential_plot.plot(ax=ax, color="#FF6B9D", alpha=0.6, linewidth=0)

    # Plot specific point/polygon POI features
    plot_layer(transit_plot, ax, "#4A90D9")
    plot_layer(healthcare_plot, ax, "#E74C3C")
    plot_layer(education_plot, ax, "#F5A623")
    plot_layer(grocery_plot, ax, "#27AE60")

    # Plot transparent buffer layers
    transit_buffer_gdf.plot(ax=ax, color="#4A90D9", alpha=0.15, linewidth=0)
    healthcare_buffer_gdf.plot(ax=ax, color="#E74C3C", alpha=0.15, linewidth=0)
    education_buffer_gdf.plot(ax=ax, color="#F5A623", alpha=0.15, linewidth=0)
    grocery_buffer_gdf.plot(ax=ax, color="#27AE60", alpha=0.15, linewidth=0)

    ax.tick_params(axis='both', which='major', labelsize=8, length=2, width=0.5)

    # Dynamic legends matching user choice
    legend_items = [
        mpatches.Patch(color="#FF6B9D", alpha=0.8, label="Residential"),
        mpatches.Patch(color="#4A90D9", alpha=0.5, label=f"Transit ({buffer}m buffer)"),
        mpatches.Patch(color="#E74C3C", alpha=0.5, label=f"Healthcare ({buffer}m buffer)"),
        mpatches.Patch(color="#F5A623", alpha=0.5, label=f"Education ({buffer}m buffer)"),
        mpatches.Patch(color="#27AE60", alpha=0.5, label=f"Food / Grocery ({buffer}m buffer)"),
    ]
    ax.legend(handles=legend_items, loc="lower left", fontsize=8, framealpha=0.9)

    ax.set_title(
        f"{region_name.split(',')[0]} ({walk_time} City Analysis) — Access: {pct_ideal:.1f}%",
        fontsize=11, fontweight="bold", pad=12
    )

    if "png" in outputs:
        plt.savefig(PNG_OUTPUT, dpi=150, bbox_inches='tight')
    plt.close()
    plt.close()


    # Folium interactive map generation
    def add_service_points_interactive(gdf, feature_group, color, default_name):
        points = gdf[gdf.geometry.geom_type == "Point"]
        polys = gdf[gdf.geometry.geom_type.isin(["Polygon", "MultiPolygon"])]

        # Add points as simple light markers
        for _, row in points.iterrows():
            # Double check that geometry element is populated
            if row.geometry is None or row.geometry.is_empty:
                continue

            pt = row.geometry
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

        # Process larger footprint polygons if present
        if not polys.empty:
            polys = polys.copy()
            polys["name"] = polys["name"].fillna(default_name).astype(str)
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

    m = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=13,
        tiles="CartoDB positron"
    )

    # Residential layer
    res_layer = folium.FeatureGroup(name="Residential Areas", show=True)
    folium.GeoJson(
        residential_plot,
        style_function=lambda _: {
            "fillColor": "#FF6B9D",
            "color": "none",
            "fillOpacity": 0.3,
        },
    ).add_to(res_layer)
    res_layer.add_to(m)

    # Setup layer configuration mapping metrics
    layers_config = [
        ("Transit", transit_buffer_gdf, transit_plot, "#4A90D9", "Transit Stop"),
        ("Healthcare", healthcare_buffer_gdf, healthcare_plot, "#E74C3C", "Healthcare Facility"),
        ("Education", education_buffer_gdf, education_plot, "#F5A623", "Educational Facility"),
        ("Grocery & Food", grocery_buffer_gdf, grocery_plot, "#27AE60", "Grocery / Marketplace")
    ]

    for label, buffer_gdf, plot_gdf, color, default_name in layers_config:
        layer = folium.FeatureGroup(name=f"{label} Coverage Area", show=True)

        # Add buffer footprint
        folium.GeoJson(
            buffer_gdf,
            style_function=lambda _, c=color: {
                "fillColor": c,
                "color": "none",
                "fillOpacity": 0.15,
            }
        ).add_to(layer)

        # Add specific markers
        add_service_points_interactive(plot_gdf, layer, color, default_name)
        layer.add_to(m)

    # Add interactive layer control panel
    folium.LayerControl(collapsed=False).add_to(m)

    # Save output
    m.save(HTML_OUTPUT)

    return {
        "metrics": {
            "transit": pct_transit,
            "healthcare": pct_healthcare,
            "education": pct_education,
            "grocery": pct_grocery,
            "ideal": pct_ideal,
        },
        "files": {
            "png": f"/view/{PNG_OUTPUT}" if "png" in outputs else None,
            "html": f"/view/{HTML_OUTPUT}" if "html" in outputs else None,
        }
    }