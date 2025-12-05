import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from kneed import KneeLocator
import sys
from pathlib import Path

plt.rcParams.update({'font.family': 'serif', 'font.serif': ['Times New Roman', 'DejaVu Serif'], 'font.size': 11, 'axes.labelsize': 12, 'axes.titlesize': 14, 'xtick.labelsize': 10, 'ytick.labelsize': 10, 'legend.fontsize': 10, 'figure.dpi': 300, 'savefig.dpi': 300})

BASELINE_KPI_FILE = Path("experiments_radius_2500/day_2014-02-01/2014-02-01_hourly_kpi.csv")
OUTPUT_DIR = Path('comparative_figures')
OUTPUT_DIR.mkdir(exist_ok=True)

try:
    df = pd.read_csv(BASELINE_KPI_FILE)
except FileNotFoundError:
    print(f"File non trovato. Esegui 'run_experiments.sh' prima.")
    sys.exit(1)

df['efficiency'] = df['u0'] / df['vS'].replace(0, np.nan)
df['payment_ratio'] = df['sumP'] / df['vS'].replace(0, np.nan)
df.dropna(inplace=True) 

print("=" * 70)
print("Analisi statistica avanzata")
print("=" * 70)

print("\nAnalisi descrittiva")

stat, p_shapiro = stats.shapiro(df['efficiency'])
print(f"\nTest normalità (Shapiro-Wilk) per efficienza:")
print(f"  W = {stat:.4f}, p-value = {p_shapiro:.4f}")
if p_shapiro > 0.05:
    print("  Ipotesi normalità non rigettata (p > 0.05)")
else:
    print("  Ipotesi normalità rigettata (p <= 0.05)")

print("\nCorrelazioni con efficienza:")
for var in ['winners', 'vS', 'sumP']:
    pearson_corr, pearson_p = stats.pearsonr(df[var], df['efficiency'])
    spearman_corr, spearman_p = stats.spearmanr(df[var], df['efficiency'])
    print(f"  {var}:")
    print(f"    Pearson:  r = {pearson_corr:+.3f}, p = {pearson_p:.4f}")
    print(f"    Spearman: ρ = {spearman_corr:+.3f}, p = {spearman_p:.4f}")

print("\nOttimizzazione K-means (metodo elbow)")

features = df[['vS', 'efficiency', 'winners']].values
scaler = StandardScaler()
features_scaled = scaler.fit_transform(features)

inertia = [] 
K_range = range(1, 8) 

for k in K_range:
    kmeans_test = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans_test.fit(features_scaled)
    inertia.append(kmeans_test.inertia_)

kl = KneeLocator(K_range, inertia, curve="convex", direction="decreasing")
optimal_k = kl.elbow

if optimal_k is None:
    print("  Gomito non rilevato. Default K=3.")
    optimal_k = 3
else:
    print(f"  K ottimale: {optimal_k}")

plt.figure(figsize=(8, 5))
plt.plot(K_range, inertia, 'bo-', markersize=8)
plt.xlabel("Numero di cluster (K)")
plt.ylabel("Inerzia")
plt.title("Metodo elbow per K-means")
plt.grid(True, linestyle='--', alpha=0.6)
plt.axvline(x=optimal_k, color='red', linestyle='--', label=f'K ottimale = {optimal_k}')
plt.legend()
elbow_filename = OUTPUT_DIR / "advanced_analysis_elbow_method.png"
plt.savefig(elbow_filename, dpi=300)
plt.close()

print(f"  Grafico salvato: {elbow_filename}")
print(f"\nClustering K-means (K={optimal_k})")

kmeans_final = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
df['cluster'] = kmeans_final.fit_predict(features_scaled)

print(f"\nRisultati clustering:")
for c in range(optimal_k):
    cluster_subset = df[df['cluster'] == c]
    if cluster_subset.empty:
        continue
        
    cluster_hours = sorted(cluster_subset['hour'].values)
    cluster_eff = cluster_subset['efficiency'].mean()
    cluster_vS = cluster_subset['vS'].mean()
    cluster_winners = cluster_subset['winners'].mean()
    
    print(f"  Cluster {c}:")
    print(f"    Ore: {cluster_hours}")
    print(f"    Media: eff={cluster_eff:.3f}, vS={cluster_vS:,.0f}€, vincitori={cluster_winners:.1f}")

print("\nRegressione lineare esplorativa")
print("Attenzione: rischio overfitting con N ridotto")

X = df[['vS', 'winners']].values
y = df['efficiency'].values

model = LinearRegression()
model.fit(X, y)

print(f"\nModello: efficienza ~ β₁*v(S) + β₂*vincitori + ε")
print(f"  Coefficiente v(S) (β₁):      {model.coef_[0]:.6f}")
print(f"  Coefficiente vincitori (β₂): {model.coef_[1]:.6f}")
print(f"  Intercetta:                  {model.intercept_:.4f}")
print(f"  R²:                          {model.score(X, y):.4f}")

print("\nGenerazione visualizzazioni")

fig, axes = plt.subplots(2, 2, figsize=(15, 12))
fig.suptitle("Analisi statistica avanzata", fontsize=16, fontweight='bold')

corr_vS_spearman = stats.spearmanr(df['vS'], df['efficiency']).correlation
scatter1 = axes[0,0].scatter(df['vS'], df['efficiency'], c=df['cluster'], cmap='viridis', s=120, alpha=0.8, edgecolors='k', linewidth=0.5)
axes[0,0].set_xlabel("Valore piattaforma v(S) (€)")
axes[0,0].set_ylabel("Efficienza u₀/v(S)")
axes[0,0].set_title(f"Efficienza vs. valore piattaforma (ρ={corr_vS_spearman:.3f})")
axes[0,0].grid(True, linestyle='--', alpha=0.5)
legend1 = axes[0,0].legend(*scatter1.legend_elements(), title="Cluster")
axes[0,0].add_artist(legend1)

corr_winners_spearman = stats.spearmanr(df['winners'], df['efficiency']).correlation
scatter2 = axes[0,1].scatter(df['winners'], df['efficiency'], c=df['cluster'], cmap='viridis', s=120, alpha=0.8, edgecolors='k', linewidth=0.5)
axes[0,1].set_xlabel("Numero vincitori")
axes[0,1].set_ylabel("Efficienza u₀/v(S)")
axes[0,1].set_title(f"Efficienza vs. numero vincitori (ρ={corr_winners_spearman:.3f})")
axes[0,1].grid(True, linestyle='--', alpha=0.5)
legend2 = axes[0,1].legend(*scatter2.legend_elements(), title="Cluster")
axes[0,1].add_artist(legend2)

for c in range(optimal_k):
    cluster_data = df[df['cluster'] == c]['efficiency']
    if len(cluster_data) > 0:
        axes[1,0].hist(cluster_data, alpha=0.6, label=f"Cluster {c} (N={len(cluster_data)})", bins=5, density=True)
axes[1,0].set_xlabel("Efficienza u₀/v(S)")
axes[1,0].set_ylabel("Densità di frequenza")
axes[1,0].set_title("Distribuzione efficienza per cluster")
axes[1,0].legend()
axes[1,0].grid(True, linestyle='--', alpha=0.5)

corr_matrix = df[['vS', 'sumP', 'u0', 'winners', 'efficiency']].corr(method='spearman')
im = axes[1,1].imshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
labels = ['v(S)', 'Σpᵢ', 'u₀', 'Vincitori', 'Efficienza']
axes[1,1].set_xticks(np.arange(len(labels)))
axes[1,1].set_yticks(np.arange(len(labels)))
axes[1,1].set_xticklabels(labels, rotation=45, ha="right")
axes[1,1].set_yticklabels(labels)
axes[1,1].set_title("Matrice correlazione (Spearman)")

for i in range(len(labels)):
    for j in range(len(labels)):
        val = corr_matrix.iloc[i, j]
        text_color = "white" if abs(val) > 0.6 else "black"
        axes[1,1].text(j, i, f"{val:.2f}", ha="center", va="center", color=text_color, fontsize=10, weight='bold')

plt.tight_layout(rect=(0, 0, 1, 0.96))
output_filename = OUTPUT_DIR / "advanced_analysis_summary.png"
plt.savefig(output_filename, dpi=300)

print(f"\nFigura salvata: {output_filename}")
print("=" * 70)
