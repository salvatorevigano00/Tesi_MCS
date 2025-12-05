import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

PATHS = {"1500m": Path("experiments_radius_1500/day_2014-02-01"), "2500m": Path("experiments_radius_2500/day_2014-02-01"), "4000m": Path("experiments_radius_4000/day_2014-02-01")}

def load_kpi_data(base_path: Path, kpi_type: str) -> pd.DataFrame | None:
    file_path = base_path / f"2014-02-01_{kpi_type}_kpi.csv"
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File non trovato: {file_path}", file=sys.stderr)
        return None

def analyze_radius_comparison():
    print("=" * 80)
    print("Analisi comparativa aggregata (daily) e oraria (hourly) per raggio")
    print("=" * 80)
    
    results = {}
    all_ok = True

    for radius, path in PATHS.items():
        df_daily = load_kpi_data(path, "daily")
        df_hourly = load_kpi_data(path, "hourly")
        
        if df_daily is None or df_hourly is None:
            all_ok = False
            continue

        vS_total = df_daily['vS_total'][0]
        u0_total = df_daily['u0_total'][0]
        winners_total = df_daily['winners_total'][0]
        eff_daily_mean = u0_total / vS_total if vS_total != 0 else 0
        
        df_hourly['efficiency'] = df_hourly['u0'] / df_hourly['vS'].replace(0, np.nan)
        eff_hourly_mean = df_hourly['efficiency'].mean()
        eff_hourly_std = df_hourly['efficiency'].std()
        
        results[radius] = {"vS_total": vS_total, "u0_total": u0_total, "eff_daily_mean": eff_daily_mean, "winners_total": winners_total, "eff_hourly_mean": eff_hourly_mean, "eff_hourly_std": eff_hourly_std}

    if not all_ok:
        print("\nAlcuni file mancanti. Analisi parziale.")
        if not results:
            print("Nessun dato trovato. Uscita.")
            sys.exit(1)

    print("\nMetriche aggregate giornaliere")
    print(f"{'Raggio':<7} | {'vS totale':>12} | {'u0 totale':>12} | {'Effic. media':>12} | {'Vincitori':>9}")
    print("-" * 63)
    
    for radius, data in results.items():
        print(f"{radius:<7} | {data['vS_total']:12,.0f} | {data['u0_total']:12,.0f} | {data['eff_daily_mean']:12.3f} | {data['winners_total']:9d}")

    print("\nStatistiche efficienza oraria")
    print(f"{'Raggio':<7} | {'Effic. media':>12} | {'Dev. standard':>14} | {'Stabilità (CV)':>14}")
    print("-" * 63)
    
    for radius, data in results.items():
        cv = data['eff_hourly_std'] / data['eff_hourly_mean'] if data['eff_hourly_mean'] != 0 else np.nan
        print(f"{radius:<7} | {data['eff_hourly_mean']:12.3f} | {data['eff_hourly_std']:14.3f} | {cv:14.3f}")
    
    print("\nCV (coefficiente di variazione) = dev.std / media. Valori più bassi indicano maggiore stabilità.")
    print("=" * 80)

if __name__ == "__main__":
    analyze_radius_comparison()
