import pandas as pd
import numpy as np
import sys
import os
from pathlib import Path

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)
    
BASELINE_KPI_FILE = Path("experiments_radius_2500/day_2014-02-01/2014-02-01_hourly_kpi.csv")

def analyze_correlations(kpi_file: Path):
    print("=" * 70)
    print(f"Analisi correlazioni")
    print(f"Dati: {kpi_file}")
    print("=" * 70)

    try:
        df = pd.read_csv(kpi_file)
    except FileNotFoundError:
        print(f"File non trovato: {kpi_file}")
        print("Esegui 'run_experiments.sh' prima di procedere.")
        sys.exit(1)
    except Exception as e:
        print(f"Errore caricamento: {e}")
        sys.exit(1)

    df['efficiency'] = df['u0'] / df['vS'].replace(0, np.nan)
    df.dropna(subset=['efficiency'], inplace=True)

    if df.empty:
        print("Nessun dato valido trovato.")
        return

    print("\nCorrelazione di Pearson (lineare)")
    corr_winners_eff_p = df['winners'].corr(df['efficiency'], method='pearson')
    print(f"Vincitori ↔ efficienza: {corr_winners_eff_p:+.3f}")

    corr_vS_eff_p = df['vS'].corr(df['efficiency'], method='pearson')
    print(f"v(S) ↔ efficienza:      {corr_vS_eff_p:+.3f}")
    
    print("\nCorrelazione di Spearman (monotona)")
    corr_winners_eff_s = df['winners'].corr(df['efficiency'], method='spearman')
    print(f"Vincitori ↔ efficienza: {corr_winners_eff_s:+.3f}")

    corr_vS_eff_s = df['vS'].corr(df['efficiency'], method='spearman')
    print(f"v(S) ↔ efficienza:      {corr_vS_eff_s:+.3f}")
    
    print("\n" + "=" * 70)
    print("Analisi completata.")
    print("=" * 70)

if __name__ == "__main__":
    analyze_correlations(BASELINE_KPI_FILE)