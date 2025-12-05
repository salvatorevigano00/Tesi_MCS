import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

BASE = Path(__file__).resolve().parent
EXPERIMENT_DIRS = {
    "HIGH": BASE / "esperimenti_fase2_high" / "giorno_2014-02-01_fase2",
    "MIXED": BASE / "esperimenti_fase2_mixed" / "giorno_2014-02-01_fase2",
    "LOW": BASE / "esperimenti_fase2_low" / "giorno_2014-02-01_fase2",
}

json_path = BASE / "esperimenti_fase2_mixed" / "giorno_2014-02-01_fase2" / "grafici" / "2014-02-01_distribuzione_profili.json"

def load_kpi_orari():
    frames = []
    for scen, folder in EXPERIMENT_DIRS.items():
        df = pd.read_csv(folder / "2014-02-01_kpi_orari_fase2.csv")
        df["scenario"] = scen
        frames.append(df)
    df_all = pd.concat(frames, ignore_index=True)
    df_all["scenario"] = df_all["scenario"].str.upper().str.strip()
    df_all["ora"] = df_all["ora"].astype(int)
    return df_all

def compute_kpi_giornalieri(df_orari):
    g = df_orari.groupby("scenario", as_index=False).agg(
        u0_mech=("u0_mech", "sum"),
        u0_eff=("u0_eff", "sum"),
    )
    g["scenario"] = g["scenario"].str.upper().str.strip()
    g = g.sort_values("scenario", key=lambda x: x.map({"HIGH": 0, "MIXED": 1, "LOW": 2}))
    return g.reset_index(drop=True)

def figura_7_3_breakdown(df_orari, output):
    sns.set(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(10, 5))
    
    scenario_colors = {"HIGH": "#1f77b4", "MIXED": "#ff7f0e", "LOW": "#2ca02c"}
    scenario_order = ["HIGH", "MIXED", "LOW"]
    
    for scen in scenario_order:
        g = df_orari[df_orari["scenario"] == scen].sort_values("ora")
        ax.plot(g["ora"], g["v_mech"], color=scenario_colors[scen], 
                linestyle="-", linewidth=2.5, alpha=0.9)
        ax.plot(g["ora"], g["v_eff"], color=scenario_colors[scen], 
                linestyle="--", linewidth=2.5, alpha=0.9)
    
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="gray", linestyle="-", linewidth=2, label="v_mech (teorico)"),
        Line2D([0], [0], color="gray", linestyle="--", linewidth=2, label="v_eff (effettivo)"),
        Line2D([0], [0], color=scenario_colors["HIGH"], linewidth=3, label="HIGH"),
        Line2D([0], [0], color=scenario_colors["MIXED"], linewidth=3, label="MIXED"),
        Line2D([0], [0], color=scenario_colors["LOW"], linewidth=3, label="LOW"),
    ]
    ax.legend(handles=legend_elements, fontsize=9, ncol=2, loc="upper right")
    
    ax.set_xlabel("Ora del giorno")
    ax.set_ylabel("Valore (€)")
    ax.set_xticks(range(8, 20))
    ax.set_title("Valore meccanismo vs effettivo")
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    plt.close(fig)

def figura_7_4_erosione_utilita(df_day, output):
    sns.set(style="whitegrid", context="talk")
    fig, ax = plt.subplots(figsize=(8, 5))
    
    df = df_day.copy()
    df["loss_abs"] = df["u0_mech"] - df["u0_eff"]
    df["loss_pct"] = 100 * df["loss_abs"] / df["u0_mech"]
    
    x = range(len(df))
    width = 0.35
    
    ax.bar([i - width/2 for i in x], df["u0_mech"], width=width,
           label="Utilità piattaforma (ex-ante) $u_{0,\\text{mech}}$", color="#1f77b4")
    ax.bar([i + width/2 for i in x], df["u0_eff"], width=width,
           label="Utilità piattaforma (ex-post) $u_{0,\\text{eff}}$", color="#aec7e8")
    
    offset_y = df["u0_mech"].max() * 0.025
    for i, row in df.iterrows():
        ax.text(i + width/2, row["u0_eff"] + offset_y, f"-{row['loss_pct']:.1f}%",
                ha="center", va="bottom", fontsize=9, fontweight="bold")
    
    ax.axhline(0, color="red", linestyle="--", linewidth=1, label="Soglia break-even")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["scenario"])
    ax.set_ylabel("Utilità (€)")
    ax.set_title("Erosione utilità piattaforma")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    plt.close(fig)

def figura_7_5_heatmap_defezioni(df_orari, output):
    def_col = "defezioni_totali"
    pivot = df_orari.pivot_table(
        index="scenario",
        columns="ora",
        values=def_col,
        aggfunc="sum",
    ).reindex(index=["HIGH", "MIXED", "LOW"])
    
    sns.set(style="white", context="talk")
    fig, ax = plt.subplots(figsize=(10, 4))
    
    sns.heatmap(
        pivot,
        ax=ax,
        cmap="YlOrRd",
        annot=True,
        fmt=".0f",
        linewidths=0.5,
        linecolor="white",
        cbar_kws={"label": "Defezioni totali per ora"},
        vmin=0,
        vmax=max(11, pivot.max().max()),
    )
    
    ax.set_xlabel("Ora del giorno")
    ax.set_ylabel("Scenario")
    ax.set_title("Heatmap defezioni (scenario × ora)")
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    plt.close(fig)
    
def figura_7_6_mixed_from_json(json_path, output):
    with open(json_path, "r") as f:
        meta = json.load(f)

    dist = meta["statistiche_dati"]["distribuzione_profili"]
    tot_vincitori = meta["statistiche_dati"]["totale_vincitori"]

    profili = ["Quasi-Rational", "Bounded Honest", "Bounded Moderate", "Bounded Opportunistic"]
    vincitori_counts = [dist[p] for p in profili]
    vincitori_pct = [100 * c / tot_vincitori for c in vincitori_counts]
    popolazione_pct = [25.0, 25.0, 30.0, 20.0]

    df = pd.DataFrame({
        "Profilo": profili,
        "Popolazione": popolazione_pct,
        "Vincitori": vincitori_pct,
    })

    sns.set(style="whitegrid", context="talk")
    # FIGURA PIÙ ALTA
    fig, ax = plt.subplots(figsize=(9, 6))

    x = range(len(df))
    width = 0.35

    ax.bar([i - width/2 for i in x], df["Popolazione"], width=width,
           label="Popolazione", color="#dddddd")
    ax.bar([i + width/2 for i in x], df["Vincitori"], width=width,
           label="Vincitori scenario", color="#1f77b4")

    # ETICHETTE PERCENTUALI PIÙ VICINE ALLE BARRE
    for i, row in df.iterrows():
        ax.text(i - width/2, row["Popolazione"] + 0.8, f"{row['Popolazione']:.1f}%",
                ha="center", va="bottom", fontsize=9)
        ax.text(i + width/2, row["Vincitori"] + 0.8, f"{row['Vincitori']:.1f}%",
                ha="center", va="bottom", fontsize=9)

    xtick_labels = [
        "Quasi-\nRational",
        "Bounded\nHonest",
        "Bounded\nModerate",
        "Bounded\nOpportunistic",
    ]
    ax.set_xticks(list(x))
    ax.set_xticklabels(xtick_labels, rotation=0)

    ax.set_ylabel("Percentuale (%)")
    ax.set_title("Distribuzione profili — Popolazione vs Vincitori (MIXED)")
    ax.set_ylim(0, 45)
    ax.legend(fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(output, dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    df_orari = load_kpi_orari()
    df_day = compute_kpi_giornalieri(df_orari)
    out_dir = Path("../Stesura/Immagini")
    out_dir.mkdir(exist_ok=True)
    figura_7_3_breakdown(df_orari, out_dir / "figura_7_3_breakdown.png")
    figura_7_4_erosione_utilita(df_day, out_dir / "figura_7_4_erosione_utilita.png")
    figura_7_5_heatmap_defezioni(df_orari, out_dir / "figura_7_5_heatmap_defezioni.png")
    figura_7_6_mixed_from_json(json_path, out_dir / "figura_7_6_distribuzione_profili_mixed.png")