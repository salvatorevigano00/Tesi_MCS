import matplotlib.pyplot as plt

def create_fft_tree_diagonal():
    _, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(-1, 9)
    ax.set_ylim(0, 9)
    ax.axis('off')

    box_decision = dict(boxstyle="round,pad=0.5", fc="white", ec="#333333", lw=1.5)
    box_reject = dict(boxstyle="round,pad=0.4", fc="#ffe6e6", ec="#cc0000", lw=1.5)
    box_accept = dict(boxstyle="round,pad=0.4", fc="#e6ffe6", ec="#009900", lw=1.5)
    
    x1, y1 = 1.5, 8.0
    dx, dy = 2.5, 2.0
    
    ax.text(x1, y1, "Distanza\neccessiva?", ha="center", va="center", size=10, bbox=box_decision, zorder=10)
    
    ax.annotate("", xy=(x1 - 1.2, y1 - 1.2), xytext=(x1, y1 - 0.4), arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(x1 - 0.8, y1 - 0.8, "Sì", ha="right", va="bottom", size=9, style='italic', color="#cc0000")
    ax.text(x1 - 1.2, y1 - 1.5, "RIFIUTA", ha="center", va="top", size=9, weight="bold", bbox=box_reject)

    x2, y2 = x1 + dx, y1 - dy
    ax.annotate("", xy=(x2, y2 + 0.4), xytext=(x1, y1 - 0.4), arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(x1 + 0.8, y1 - 0.8, "No", ha="left", va="bottom", size=9, style='italic', color="#006600")

    ax.text(x2, y2, "Ricompensa\nsufficiente?", ha="center", va="center", size=10, bbox=box_decision, zorder=10)
    
    ax.annotate("", xy=(x2 - 1.2, y2 - 1.2), xytext=(x2, y2 - 0.4), arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(x2 - 0.8, y2 - 0.8, "No", ha="right", va="bottom", size=9, style='italic', color="#cc0000")
    ax.text(x2 - 1.2, y2 - 1.5, "RIFIUTA", ha="center", va="top", size=9, weight="bold", bbox=box_reject)

    x3, y3 = x2 + dx, y2 - dy
    ax.annotate("", xy=(x3, y3 + 0.4), xytext=(x2, y2 - 0.4), arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(x2 + 0.8, y2 - 0.8, "Sì", ha="left", va="bottom", size=9, style='italic', color="#006600")

    ax.text(x3, y3, "Piattaforma\naffidabile?", ha="center", va="center", size=10, bbox=box_decision, zorder=10)
    
    ax.annotate("", xy=(x3 - 1.2, y3 - 1.2), xytext=(x3, y3 - 0.4), arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(x3 - 0.8, y3 - 0.8, "No", ha="right", va="bottom", size=9, style='italic', color="#cc0000")
    ax.text(x3 - 1.2, y3 - 1.5, "RIFIUTA", ha="center", va="top", size=9, weight="bold", bbox=box_reject)

    x_final, y_final = x3 + dx, y3 - dy
    ax.annotate("", xy=(x_final, y_final + 0.4), xytext=(x3, y3 - 0.4), arrowprops=dict(arrowstyle="->", color="black", lw=1.5))
    ax.text(x3 + 0.8, y3 - 0.8, "Sì", ha="left", va="bottom", size=9, style='italic', color="#006600")
    ax.text(x_final, y_final, "ACCETTA\nTASK", ha="center", va="center", size=10, weight="bold", bbox=box_accept)

    plt.tight_layout()
    plt.savefig("../docs/Stesura/Immagini/figura_2_5_fft.png", bbox_inches="tight", dpi=300)
    #plt.show()

if __name__ == "__main__":
    create_fft_tree_diagonal()