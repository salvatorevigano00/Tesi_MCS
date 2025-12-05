import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

def calculate_distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def plot_routing_comparison_final():
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
    except:
        plt.style.use('ggplot')
        
    plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 12, 'axes.titlesize': 14, 'axes.titleweight': 'bold'})
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    user_pos = np.array([0.5, 0.1]) 
    tasks_pos = np.array([[0.15, 0.45], [0.25, 0.55], [0.1, 0.7], [0.4, 0.85], [0.5, 0.92], [0.65, 0.88], [0.85, 0.75], [0.92, 0.6], [0.8, 0.45], [0.65, 0.3], [0.5, 0.35], [0.3, 0.25]])

    c_user = '#D32F2F'
    c_task = '#1976D2'
    c_star = '#FF7043'
    c_tsp = '#388E3C'
    
    total_dist_star = 0
    ax1.set_title("Modello teorico: star routing\n(viaggi indipendenti andata/ritorno)", pad=15)
    
    for task in tasks_pos:
        d = calculate_distance(user_pos, task)
        total_dist_star += 2 * d
        ax1.plot([user_pos[0], task[0]], [user_pos[1], task[1]], linestyle='--', color=c_star, alpha=0.5, linewidth=1.5, zorder=1)

    tsp_order = [11, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    total_dist_tsp = 0
    current_pos = user_pos
    path_x = [user_pos[0]]
    path_y = [user_pos[1]]

    ax2.set_title("Scenario reale: TSP routing\n(percorso ottimizzato multi-stop)", pad=15)
    
    for idx in tsp_order:
        next_task = tasks_pos[idx]
        total_dist_tsp += calculate_distance(current_pos, next_task)
        path_x.append(next_task[0])
        path_y.append(next_task[1])
        current_pos = next_task
    
    total_dist_tsp += calculate_distance(current_pos, user_pos)
    path_x.append(user_pos[0])
    path_y.append(user_pos[1])

    ax2.plot(path_x, path_y, color=c_tsp, linewidth=2.5, alpha=0.8, zorder=2)
    
    for i in range(len(path_x)-1):
        mid_x = (path_x[i] + path_x[i+1]) / 2
        mid_y = (path_y[i] + path_y[i+1]) / 2
        ax2.annotate('', xy=(mid_x, mid_y), xytext=(path_x[i], path_y[i]), arrowprops=dict(arrowstyle="->", color=c_tsp, lw=2))

    for ax in [ax1, ax2]:
        ax.scatter(tasks_pos[:,0], tasks_pos[:,1], c=c_task, s=120, edgecolors='white', zorder=3)
        ax.scatter(user_pos[0], user_pos[1], c=c_user, s=200, marker='s', edgecolors='white', zorder=3)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect('equal')
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(True, color='#eeeeee', linestyle='-', linewidth=0.5)

    info_star = f"Assunzione conservativa:\n$D_{{Star}} = \sum 2 \cdot d(u, \\tau_i)$\n---------------------------\nDistanza totale: {total_dist_star:.2f} u"
    ax1.text(0.03, 0.97, info_star, transform=ax1.transAxes, fontsize=11, va='top', bbox=dict(facecolor='white', edgecolor=c_star, boxstyle='round,pad=0.6', linewidth=1.5))

    info_tsp = f"Comportamento reale:\n$D_{{TSP}} \ll D_{{Star}}$\n---------------------------\nDistanza totale: {total_dist_tsp:.2f} u"
    ax2.text(0.03, 0.97, info_tsp, transform=ax2.transAxes, fontsize=11, va='top', bbox=dict(facecolor='white', edgecolor=c_tsp, boxstyle='round,pad=0.6', linewidth=1.5))
   
    legend_elements = [
        Line2D([0], [0], marker='s', color='w', markerfacecolor=c_user, markersize=12, label='Utente (deposito)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor=c_task, markersize=10, label='Task (N=12)'),
        Line2D([0], [0], color=c_star, lw=2, linestyle='--', label='Percorso star'),
        Line2D([0], [0], color=c_tsp, lw=2, label='Percorso TSP')
    ]
    fig.legend(handles=legend_elements, loc='lower center', ncol=4, fontsize=12, bbox_to_anchor=(0.5, 0.08))

    sovrastima = (total_dist_star / total_dist_tsp - 1) * 100
    fig.suptitle(f"Confronto modelli di costo: star routing vs. ottimizzazione TSP", fontsize=16, fontweight='bold', y=0.98)
    
    fig.text(0.5, 0.03, f"Il modello teorico sovrastima il costo reale del +{sovrastima:.0f}% in questo scenario, garantendo un margine di sicurezza robusto.", ha='center', fontsize=12, fontweight='bold', color='#444444', bbox=dict(facecolor='#f0f0f0', edgecolor='none', boxstyle='round,pad=0.4'))

    plt.subplots_adjust(bottom=0.15, top=0.88, wspace=0.1)
    filename = "../docs/Stesura/Immagini/figura_3_1_confronto_routing_star_vs_tsp.jpg"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Grafico salvato con successo: {filename}")
    #plt.show()

if __name__ == "__main__":
    plot_routing_comparison_final()
