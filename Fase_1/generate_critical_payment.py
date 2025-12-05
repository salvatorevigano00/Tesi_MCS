import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_critical_payment():
    _, ax = plt.subplots(figsize=(14, 5.5))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 5.5)
    ax.axis('off')

    lc, lw = 'black', 1.8
    fc_proc = '#e3f2fd'
    fc_dec = '#fff9c4'
    fc_term = '#eeeeee'
    fc_fin = '#e8f5e9'
    font_formula = 14
    font_title = 15
    font_label = 12
    y_main = 4.0
    y_sub = 1.5
    w_box = 2.2
    h_box = 1.4
    w_round = 1.2
    h_round = 0.7
    w_diamond = 2.4
    h_diamond = 2.0
    w_fin = 2.6
    h_fin = 1.4
    w_ret = 1.6
    h_ret = 0.7
    gap = 3.0
    x1 = 1.2
    x2 = x1 + gap
    x3 = x2 + gap
    x4 = x3 + gap
    x5 = x4 + gap - 0.5

    def draw_rect(x, y, w, h, color, title, text, text2=""):
        ax.add_patch(patches.Rectangle((x - w/2 + 0.06, y - h/2 - 0.06), w, h, fc='#aaaaaa', zorder=1))
        ax.add_patch(patches.Rectangle((x - w/2, y - h/2), w, h, fc=color, ec=lc, lw=lw, zorder=2))
        ax.text(x, y + 0.35, title, ha='center', va='center', fontsize=font_title, fontweight='bold', zorder=3)
        ax.text(x, y - 0.05, text, ha='center', va='center', fontsize=font_formula, zorder=3)
        if text2:
            ax.text(x, y - 0.45, text2, ha='center', va='center', fontsize=font_formula, zorder=3)
        return x, y

    def draw_diamond(x, y, w, h, color, title, text):
        verts = [(x, y + h/2), (x + w/2, y), (x, y - h/2), (x - w/2, y)]
        poly = patches.Polygon(verts, fc=color, ec=lc, lw=lw, zorder=2)
        ax.add_patch(poly)
        ax.text(x, y + 0.25, title, ha='center', va='center', fontsize=font_title, fontweight='bold', zorder=3)
        ax.text(x, y - 0.25, text, ha='center', va='center', fontsize=font_formula, zorder=3)
        return x, y

    def draw_round(x, y, w, h, color, text):
        box = patches.FancyBboxPatch((x - w/2, y - h/2), w, h, boxstyle="round,pad=0.08", fc=color, ec=lc, lw=lw, zorder=2)
        ax.add_patch(box)
        ax.text(x, y, text, ha='center', va='center', fontsize=font_title, fontweight='bold', zorder=3)
        return x, y

    draw_round(x1, y_main, w_round, h_round, fc_term, "Inizio")
    draw_rect(x2, y_main, w_box, h_box, fc_proc, "Inizializ.", r"$p_i \leftarrow b_i$", r"$T \leftarrow \emptyset$")
    draw_diamond(x3, y_main, w_diamond, h_diamond, fc_dec, "Competitor?", r"$\exists \delta_j > 0$")
    draw_rect(x4, y_main, w_box, h_box, fc_proc, "Selezione", r"$j^* = \arg\max(\delta_j)$", r"$\hat{p}_i = mv_i - \delta_{j^*}$")
    draw_rect(x5, y_main, w_box, h_box, fc_proc, "Aggiorna", r"$p_i \leftarrow \max(p_i, \hat{p}_i)$", r"$T \leftarrow T \cup \{j^*\}$")
    draw_rect(x3, y_sub, w_fin, h_fin, fc_fin, "Calcolo finale", r"$p_i \leftarrow \max(p_i, mv_i^{\mathrm{fin}})$")
    draw_round(x4, y_sub, w_ret, h_ret, fc_term, r"Return $p_i$")

    ap = dict(arrowstyle="->, head_width=0.5, head_length=0.6", lw=2.2, color='black')
    start_edge = x1 + w_round / 2 + 0.08
    ax.annotate("", xy=(x2 - w_box/2, y_main), xytext=(start_edge, y_main), arrowprops=ap)
    ax.annotate("", xy=(x3 - w_diamond/2, y_main), xytext=(x2 + w_box/2, y_main), arrowprops=ap)
    ax.annotate("", xy=(x4 - w_box/2, y_main), xytext=(x3 + w_diamond/2, y_main), arrowprops=ap)
    x_arrow_mid = (x3 + w_diamond/2 + x4 - w_box/2) / 2
    ax.text(x_arrow_mid, y_main + 0.25, "Sì", fontsize=font_label, fontweight='bold', ha='center', va='bottom')
    ax.annotate("", xy=(x5 - w_box/2, y_main), xytext=(x4 + w_box/2, y_main), arrowprops=ap)
    y_top = y_main + 1.4
    ax.plot([x5, x5], [y_main + h_box/2, y_top], color='black', lw=2.2)
    ax.plot([x5, x3], [y_top, y_top], color='black', lw=2.2)
    ax.annotate("", xy=(x3, y_main + h_diamond/2), xytext=(x3, y_top), arrowprops=ap)
    ax.annotate("", xy=(x3, y_sub + h_fin/2), xytext=(x3, y_main - h_diamond/2), arrowprops=ap)
    y_arrow_mid = (y_main - h_diamond/2 + y_sub + h_fin/2) / 2
    ax.text(x3 - 0.35, y_arrow_mid, "No", fontsize=font_label, fontweight='bold', ha='right', va='center')
    return_edge = x4 - w_ret / 2 - 0.08
    ax.annotate("", xy=(return_edge, y_sub), xytext=(x3 + w_fin/2, y_sub), arrowprops=ap)

    plt.tight_layout()
    plt.savefig("../docs/Stesura/Immagini/figura_4_1_critical_payment.jpg", dpi=300)
    #plt.show()

draw_critical_payment()
