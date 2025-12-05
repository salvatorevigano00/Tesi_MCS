import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np
import os
import glob
import contextily as ctx
from pyproj import Transformer

LAT_MIN_SIM, LAT_MAX_SIM = 41.78, 42.04
LON_MIN_SIM, LON_MAX_SIM = 12.30, 12.72

def find_data_file():
    path_dataset_etl = "experiments_radius_2500/dataset_processato/master_sample.csv"
    if os.path.exists(path_dataset_etl): return path_dataset_etl
    candidates = glob.glob("**/*.csv", recursive=True)
    valid = [f for f in candidates if "kpi" not in f and "rejects" not in f and os.path.getsize(f) > 10240]
    return max(valid, key=os.path.getsize) if valid else None

def generate_rome_map():
    data_path = find_data_file()
    if not data_path:
        print("Nessun file dati trovato")
        return

    print(f"Caricamento dati: {data_path}")
    
    try:
        df = pd.read_csv(data_path, usecols=['lat', 'lon'], nrows=80000)
        df = df[(df['lat'] >= LAT_MIN_SIM) & (df['lat'] <= LAT_MAX_SIM) & (df['lon'] >= LON_MIN_SIM) & (df['lon'] <= LON_MAX_SIM)]

        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        x_data, y_data = transformer.transform(df['lon'].values, df['lat'].values)
        x_sim_min, y_sim_min = transformer.transform(LON_MIN_SIM, LAT_MIN_SIM)
        x_sim_max, y_sim_max = transformer.transform(LON_MAX_SIM, LAT_MAX_SIM)

        margin = 1000 
        x_view_min = np.percentile(x_data, 1) - margin
        x_view_max = np.percentile(x_data, 99) + margin
        y_view_min = np.percentile(y_data, 1) - margin
        y_view_max = np.percentile(y_data, 99) + margin

    except Exception as e:
        print(f"Errore: {e}")
        return
    
    _, ax = plt.subplots(figsize=(9, 7)) 

    ax.scatter(x_data, y_data, s=0.4, c='#003366', alpha=0.6, label='Copertura taxi', zorder=2)

    try:
        ctx.add_basemap(ax, crs="EPSG:3857", source=ctx.providers.OpenStreetMap.Mapnik, zoom=12, alpha=0.8)
    except: pass

    w_sim = x_sim_max - x_sim_min
    h_sim = y_sim_max - y_sim_min
    bbox = patches.Rectangle((x_sim_min, y_sim_min), w_sim, h_sim, linewidth=2.5, edgecolor='#D32F2F', facecolor='none', linestyle='--', label='Confine simulazione', zorder=3)
    ax.add_patch(bbox)

    landmarks = {
        "Termini": (12.5018, 41.9009, 12.508, 41.905),
        "Colosseo": (12.4922, 41.8902, 12.495, 41.885),
        "Vaticano": (12.4534, 41.9029, 12.445, 41.910),
        "EUR": (12.4663, 41.8364, 12.475, 41.8364),
        "P.za Popolo": (12.4763, 41.9109, 12.476, 41.918),
        "Trastevere": (12.4690, 41.8890, 12.460, 41.880),
    }

    for name, coords in landmarks.items():
        lon, lat, t_lon, t_lat = coords
        lx, ly = transformer.transform(lon, lat)
        tx, ty = transformer.transform(t_lon, t_lat)
        
        if x_view_min <= lx <= x_view_max and y_view_min <= ly <= y_view_max:
            ax.plot(lx, ly, marker='o', color='#D32F2F', markersize=6, markeredgecolor='white', markeredgewidth=1, zorder=4)
            ax.text(tx, ty, name, fontsize=10, fontweight='bold', color='#333333', ha='center', va='center', bbox=dict(facecolor='white', alpha=0.85, edgecolor='#aaaaaa', boxstyle='round,pad=0.2'), zorder=5)

    ax.set_xlim(x_view_min, x_view_max)
    ax.set_ylim(y_view_min, y_view_max)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title("Distribuzione taxi a Roma", fontsize=14, fontweight='bold', pad=10)

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#003366', label='Copertura taxi'),
        Line2D([0], [0], color='#D32F2F', lw=2, linestyle='--', label='Confine simulazione'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#D32F2F', markeredgecolor='white', label='Landmark')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10, framealpha=0.95)

    plt.tight_layout()
    outfile = "../docs/Stesura/Immagini/figura_5_1_mappa_roma.jpg"
    plt.savefig(outfile, dpi=300, bbox_inches='tight')
    print(f"Mappa salvata: {outfile}")
    #plt.show()

if __name__ == "__main__":
    generate_rome_map()
