from __future__ import annotations
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

OUTPUT_DIR = "./../Stesura/Immagini/"

def draw_box(ax, x, y, width, height, text, color='#E3F2FD', edge='#90CAF9'):
    box = FancyBboxPatch((x - width / 2, y - height / 2), width, height, boxstyle="round,pad=0.05", linewidth=1.5, edgecolor=edge, facecolor=color)
    ax.add_patch(box)
    ax.text(x, y, text, ha='center', va='center', fontsize=9, fontweight='normal', linespacing=1.4)
    return box

def draw_arrow(ax, x, y_start, y_end, style='->', ls='-', color='black'):
    ax.annotate('', xy=(x, y_end), xytext=(x, y_start), arrowprops=dict(arrowstyle=style, color=color, lw=1.5, ls=ls))

def generate_architecture_diagram():
    _, ax = plt.subplots(figsize=(10, 8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    y_cohort = 9.2
    y_h = 7.8
    y_r = 6.0
    y_a = 4.2
    y_d = 2.4
    x_col1 = 2.0
    x_col2 = 5.0
    x_col3 = 8.0
    draw_box(ax, 5.0, y_cohort, 8.0, 0.8, "Coorte persistente (316 utenti)\nGiornata 2014-02-01", color='#E3F2FD', edge='#2196F3')
    ax.plot([x_col1, x_col3], [y_cohort - 0.45, y_cohort - 0.45], color='black', lw=1.5)
    ax.plot([5.0, 5.0], [y_cohort - 0.4, y_cohort - 0.45], color='black', lw=1.5)
    draw_arrow(ax, x_col1, y_cohort - 0.45, y_h + 0.4)
    ax.plot([x_col2, x_col2], [y_cohort - 0.45, y_h + 0.4], color='black', ls='--', lw=1)
    draw_arrow(ax, x_col3, y_cohort - 0.45, y_h + 0.4)
    draw_box(ax, x_col1, y_h, 2.0, 0.6, "Ora 08", color='#BBDEFB', edge='#1976D2')
    draw_arrow(ax, x_col1, y_h - 0.3, y_r + 0.5)
    draw_box(ax, x_col1, y_r, 2.0, 0.8, "Reset stato\nR = 1.0", color='#FFCDD2', edge='#E57373')
    draw_arrow(ax, x_col1, y_r - 0.4, y_a + 0.5)
    draw_box(ax, x_col1, y_a, 2.0, 0.8, "Asta IMCU", color='#FFF9C4', edge='#FBC02D')
    draw_arrow(ax, x_col1, y_a - 0.4, y_d + 0.5)
    draw_box(ax, x_col1, y_d, 2.0, 0.8, "Defezioni\ne rilevamento", color='#F5F5F5', edge='#9E9E9E')
    ax.text(x_col2, y_h, "...", fontsize=20, ha='center', va='center')
    draw_arrow(ax, x_col2, y_h - 0.3, y_r + 0.3, style='-', ls=':')
    ax.text(x_col2, y_r, "...", fontsize=20, ha='center', va='center', color='#E57373')
    draw_arrow(ax, x_col2, y_r - 0.3, y_a + 0.3, style='-', ls=':')
    ax.text(x_col2, y_a, "...", fontsize=20, ha='center', va='center', color='#FBC02D')
    draw_arrow(ax, x_col2, y_a - 0.3, y_d + 0.3, style='-', ls=':')
    ax.text(x_col2, y_d, "...", fontsize=20, ha='center', va='center', color='#9E9E9E')
    draw_box(ax, x_col3, y_h, 2.0, 0.6, "Ora 19", color='#BBDEFB', edge='#1976D2')
    draw_arrow(ax, x_col3, y_h - 0.3, y_r + 0.5)
    draw_box(ax, x_col3, y_r, 2.0, 0.8, "Reset stato\nR = 1.0", color='#FFCDD2', edge='#E57373')
    draw_arrow(ax, x_col3, y_r - 0.4, y_a + 0.5)
    draw_box(ax, x_col3, y_a, 2.0, 0.8, "Asta IMCU", color='#FFF9C4', edge='#FBC02D')
    draw_arrow(ax, x_col3, y_a - 0.4, y_d + 0.5)
    draw_box(ax, x_col3, y_d, 2.0, 0.8, "Defezioni\ne rilevamento", color='#F5F5F5', edge='#9E9E9E')
    ax.text(5.0, 1.2, "Nessun apprendimento tra le ore", ha='center', fontsize=10, style='italic', weight='bold')
    arrow_left = FancyArrowPatch((x_col1, y_d - 0.4), (4.5, 1.0), connectionstyle="arc3,rad=0.5", arrowstyle='->', linestyle='--', color='#616161', lw=1.5)
    ax.add_patch(arrow_left)
    arrow_right = FancyArrowPatch((5.5, 1.0), (x_col3, y_d - 0.4), connectionstyle="arc3,rad=0.5", arrowstyle='->', linestyle='--', color='#616161', lw=1.5)
    ax.add_patch(arrow_right)
    plt.savefig(os.path.join(OUTPUT_DIR, 'figura_7_1_architettura.png'), dpi=300, bbox_inches='tight')
    plt.close()

def generate_profile_distribution():
    scenarios = ['HIGH', 'MIXED', 'LOW']
    data = np.array([
        [0, 0, 0, 100],
        [20, 30, 25, 25],
        [50, 50, 0, 0]
    ])
    _, ax = plt.subplots(figsize=(12, 7))
    bar_width = 0.55
    y_pos = np.arange(len(scenarios))
    c_rat = '#2c7bb6'
    c_hon = '#abd9e9'
    c_mod = '#fdae61'
    c_opp = '#d7191c'
    opportunistic = data[:, 0]
    moderate = data[:, 1]
    honest = data[:, 2]
    rational = data[:, 3]
    bars_opp = ax.barh(y_pos, opportunistic, bar_width, color=c_opp, edgecolor='white', linewidth=0.8)
    bars_mod = ax.barh(y_pos, moderate, bar_width, left=opportunistic, color=c_mod, hatch='////', edgecolor='white', linewidth=0.8)
    bars_hon = ax.barh(y_pos, honest, bar_width, left=opportunistic + moderate, color=c_hon, edgecolor='white', linewidth=0.8)
    bars_rat = ax.barh(y_pos, rational, bar_width, left=opportunistic + moderate + honest, color=c_rat, edgecolor='white', linewidth=0.8)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(scenarios, fontsize=16, fontweight='bold')
    ax.set_xlabel('Composizione della popolazione (%)', fontsize=13, labelpad=15)
    ax.set_xlim(0, 100)
    ax.xaxis.grid(True, linestyle='--', alpha=0.4, color='gray')
    ax.set_axisbelow(True)
    for spine in ['top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    def add_percentage_labels(bars, values, color):
        for i, bar in enumerate(bars):
            if values[i] > 5:
                x = bar.get_x() + bar.get_width() / 2
                y = bar.get_y() + bar.get_height() / 2
                ax.text(x, y, f'{int(values[i])}%', ha='center', va='center', color=color, fontweight='bold', fontsize=12)
    add_percentage_labels(bars_rat, rational, 'white')
    add_percentage_labels(bars_hon, honest, 'black')
    add_percentage_labels(bars_mod, moderate, 'black')
    add_percentage_labels(bars_opp, opportunistic, 'white')
    legend_elements = [
        mpatches.Patch(color=c_rat, label='Quasi-razionali (ρ ∈ [0.825, 0.90])'),
        mpatches.Patch(color=c_hon, label='Onesti (ρ ∈ [0.65, 0.825])'),
        mpatches.Patch(color=c_mod, hatch='////', label='Moderati (ρ ∈ [0.475, 0.65]) — a rischio'),
        mpatches.Patch(color=c_opp, label='Opportunisti (ρ ∈ [0.30, 0.475]) — alto rischio')
    ]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, -0.18), ncol=2, frameon=False, fontsize=11, columnspacing=1.5)
    ax.invert_yaxis()
    plt.title("Composizione popolazione per scenario", fontsize=16, pad=25, fontweight='bold')
    plt.subplots_adjust(left=0.08, right=0.97, top=0.92, bottom=0.24)
    plt.savefig(os.path.join(OUTPUT_DIR, 'figura_7_2_distribuzione_profili.png'), dpi=300, bbox_inches='tight')
    plt.close()

if __name__ == "__main__":
    generate_architecture_diagram()
    generate_profile_distribution()