import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)
    
plt.rcParams.update({'font.family': 'serif', 'font.size': 10, 'axes.labelsize': 11, 'axes.titlesize': 12, 'xtick.labelsize': 9, 'ytick.labelsize': 9, 'legend.fontsize': 9, 'figure.dpi': 300, 'savefig.dpi': 300, 'savefig.bbox': 'tight'})

EXPERIMENTS = {'1500m': Path('experiments_radius_1500/day_2014-02-01'), '2500m': Path('experiments_radius_2500/day_2014-02-01'), '4000m': Path('experiments_radius_4000/day_2014-02-01')}
OUTPUT_DIR = Path('comparative_figures')
OUTPUT_DIR.mkdir(exist_ok=True)
COLORS = {'1500m': '#1f77b4', '2500m': '#ff7f0e', '4000m': '#2ca02c'}

def load_data(base_path: Path, file_type: str = 'hourly') -> pd.DataFrame | None:
    file_name = f"2014-02-01_{file_type}_kpi.csv"
    full_path = base_path / file_name
    if not full_path.exists():
        print(f"File non trovato: {full_path}", file=sys.stderr)
        return None
    try:
        return pd.read_csv(full_path)
    except Exception as e:
        print(f"Errore lettura {full_path}: {e}", file=sys.stderr)
        return None

def plot_kpi_timeseries_overlay(data: dict):
    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    all_hours = sorted(list(set(h for df in data.values() for h in df['hour'])))
    if not all_hours:
        print("Nessun dato orario disponibile", file=sys.stderr)
        plt.close(fig)
        return
        
    min_hour = all_hours[0]
    max_hour = all_hours[-1]
    
    for radius, df in data.items():
        color = COLORS[radius]
        df_plot = pd.DataFrame({'hour': all_hours}).merge(df, on='hour', how='left')
        axes[0].plot(df_plot['hour'], df_plot['vS'], marker='o', linewidth=2, label=f'Raggio {radius}', color=color, markersize=4)
        axes[1].plot(df_plot['hour'], df_plot['u0'], marker='s', linewidth=2, label=f'Raggio {radius}', color=color, markersize=4)
        axes[2].plot(df_plot['hour'], df_plot['efficiency'], marker='^', linewidth=2, label=f'Raggio {radius}', color=color, markersize=4)
    
    axes[0].set_ylabel("Valore piattaforma v(S) (€)", fontsize=11)
    axes[0].legend(loc='upper left', fontsize=9)
    axes[0].grid(True, alpha=0.2)
    axes[0].set_title("Confronto metriche orarie per raggio di assegnazione task", fontsize=12, fontweight='bold', pad=10)
    axes[1].set_ylabel("Utilità piattaforma u₀ (€)", fontsize=11)
    axes[1].legend(loc='upper left', fontsize=9)
    axes[1].grid(True, alpha=0.2)
    axes[2].set_ylabel("Efficienza u₀/v(S)", fontsize=11)
    axes[2].set_xlabel("Ora del giorno", fontsize=11)
    axes[2].legend(loc='lower left', fontsize=9)
    axes[2].grid(True, alpha=0.2)
    axes[2].set_xticks(range(min_hour, max_hour + 1, 2))
    axes[2].set_xlim(min_hour - 0.5, max_hour + 0.5)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "radius_comparison_kpi_timeseries.png", dpi=300)
    print("Figura salvata: radius_comparison_kpi_timeseries.png")
    plt.close()

def plot_efficiency_boxplot(data: dict):
    _, ax = plt.subplots(figsize=(8, 6))
    labels = sorted(data.keys())
    data_by_radius = [data[r]['efficiency'].dropna().values for r in labels]
    bp = ax.boxplot(data_by_radius, tick_labels=labels, patch_artist=True, showmeans=True, meanline=True, widths=0.6)
    
    for patch, radius in zip(bp['boxes'], labels):
        patch.set_facecolor(COLORS[radius])
        patch.set_alpha(0.7)
    
    ax.set_ylabel("Efficienza u₀/v(S)", fontsize=11)
    ax.set_xlabel("Raggio di assegnazione task", fontsize=11)
    ax.set_title("Distribuzione efficienza oraria per raggio", fontsize=12, fontweight='bold', pad=10)
    ax.grid(True, alpha=0.2, axis='y')
    
    for i, radius_data in enumerate(data_by_radius):
        if len(radius_data) > 0:
            mean_eff = radius_data.mean()
            ax.text(i + 1, mean_eff + 0.01, f"{mean_eff:.3f}", ha='center', va='bottom', fontsize=9, fontweight='bold', bbox=dict(facecolor='white', alpha=0.5, pad=0.1, edgecolor='none'))
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "radius_comparison_efficiency_boxplot.png", dpi=300)
    print("Figura salvata: radius_comparison_efficiency_boxplot.png")
    plt.close()

def plot_aggregates_barchart(data_agg: dict):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    radii = sorted(data_agg.keys())
    x = np.arange(len(radii))
    width = 0.6
    
    vS_values = [data_agg[r]['vS'] for r in radii]
    bars = axes[0,0].bar(x, vS_values, width, color=[COLORS[r] for r in radii], alpha=0.8)
    axes[0,0].set_ylabel("Valore piattaforma v(S) (€)", fontsize=10)
    axes[0,0].set_title("Valore totale piattaforma", fontsize=11, fontweight='bold')
    axes[0,0].set_xticks(x)
    axes[0,0].set_xticklabels(radii)
    axes[0,0].grid(True, alpha=0.2, axis='y')
    for bar in bars:
        height = bar.get_height()
        axes[0,0].text(bar.get_x() + bar.get_width()/2., height, f'{int(height):,}€', ha='center', va='bottom', fontsize=9)
    
    u0_values = [data_agg[r]['u0'] for r in radii]
    bars = axes[0,1].bar(x, u0_values, width, color=[COLORS[r] for r in radii], alpha=0.8)
    axes[0,1].set_ylabel("Utilità piattaforma u₀ (€)", fontsize=10)
    axes[0,1].set_title("Utilità totale piattaforma", fontsize=11, fontweight='bold')
    axes[0,1].set_xticks(x)
    axes[0,1].set_xticklabels(radii)
    axes[0,1].grid(True, alpha=0.2, axis='y')
    for bar in bars:
        height = bar.get_height()
        axes[0,1].text(bar.get_x() + bar.get_width()/2., height, f'{int(height):,}€', ha='center', va='bottom', fontsize=9)
    
    eff_values = [data_agg[r]['efficiency'] for r in radii]
    bars = axes[1,0].bar(x, eff_values, width, color=[COLORS[r] for r in radii], alpha=0.8)
    axes[1,0].set_ylabel("Efficienza u₀/v(S)", fontsize=10)
    axes[1,0].set_title("Efficienza media", fontsize=11, fontweight='bold')
    axes[1,0].set_xticks(x)
    axes[1,0].set_xticklabels(radii)
    axes[1,0].set_ylim(0, max(0.6, max(eff_values) * 1.15))
    axes[1,0].grid(True, alpha=0.2, axis='y')
    for bar in bars:
        height = bar.get_height()
        axes[1,0].text(bar.get_x() + bar.get_width()/2., height, f'{height:.3f}', ha='center', va='bottom', fontsize=9)
    
    winners_values = [data_agg[r]['winners'] for r in radii]
    bars = axes[1,1].bar(x, winners_values, width, color=[COLORS[r] for r in radii], alpha=0.8)
    axes[1,1].set_ylabel("Vincitori totali", fontsize=10)
    axes[1,1].set_title("Numero vincitori", fontsize=11, fontweight='bold')
    axes[1,1].set_xticks(x)
    axes[1,1].set_xticklabels(radii)
    axes[1,1].grid(True, alpha=0.2, axis='y')
    for bar in bars:
        height = bar.get_height()
        axes[1,1].text(bar.get_x() + bar.get_width()/2., height, f'{int(height)}', ha='center', va='bottom', fontsize=9)
    
    fig.suptitle("Confronto metriche aggregate per raggio di assegnazione task", fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout(rect=(0, 0, 1, 0.96))
    plt.savefig(OUTPUT_DIR / "radius_comparison_aggregates.png", dpi=300)
    print("Figura salvata: radius_comparison_aggregates.png")
    plt.close()

def main():
    print("=" * 70)
    print("Generazione figure comparative")
    print("=" * 70)
    
    hourly_data = {}
    daily_data_agg = {}
    all_data_loaded = True
    sorted_experiments = sorted(EXPERIMENTS.items(), key=lambda item: item[0])
    
    for radius, path in sorted_experiments:
        df_hourly = load_data(path, 'hourly')
        df_daily = load_data(path, 'daily')
        
        if df_hourly is None or df_daily is None:
            all_data_loaded = False
            continue
        
        df_hourly['efficiency'] = df_hourly['u0'] / df_hourly['vS'].replace(0, np.nan)
        hourly_data[radius] = df_hourly.sort_values(by='hour')
        
        vS_total = df_daily['vS_total'].iloc[0]
        u0_total = df_daily['vS_total'].iloc[0]
        daily_data_agg[radius] = {'vS': vS_total, 'u0': u0_total, 'winners': df_daily['winners_total'].iloc[0], 'efficiency': u0_total / vS_total if vS_total != 0 else 0}

    if not all_data_loaded:
        print("\nUno o più file mancanti. Verifica esecuzione esperimenti.")
        if not hourly_data:
            print("Nessun dato disponibile. Terminazione.")
            sys.exit(1)
        print("Proseguo con dati parziali...")
    
    print("\nDati caricati. Generazione figure...\n")
    all_hourly_dfs = []
    
    for radius, df in hourly_data.items():
        df_copy = df[['efficiency']].copy()
        df_copy['radius'] = radius
        all_hourly_dfs.append(df_copy)
    df_long_format = pd.concat(all_hourly_dfs).dropna()
    
    try:
        plot_kpi_timeseries_overlay(hourly_data)
        plot_efficiency_boxplot(hourly_data)
        plot_aggregates_barchart(daily_data_agg)
    except Exception as e:
        print(f"\nErrore generazione figure: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print(f"Figure salvate in: {OUTPUT_DIR}/")
    print("=" * 70)
    print("\nFigure generate:")
    print(f"  1. {OUTPUT_DIR / 'radius_comparison_kpi_timeseries.png'}")
    print(f"  2. {OUTPUT_DIR / 'radius_comparison_efficiency_boxplot.png'}")
    print(f"  3. {OUTPUT_DIR / 'radius_comparison_aggregates.png'}")
    print("=" * 70)

if __name__ == "__main__":
    main()
