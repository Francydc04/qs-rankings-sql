"""Charts for the QS rankings study."""

import matplotlib.pyplot as plt

INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#b4b2a9"


def _style(ax, grid_axis="x"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=MUTED, labelsize=10)
    if grid_axis:
        ax.grid(True, axis=grid_axis, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def correlation_bars(df, path=None):
    d = df.sort_values("pearson_r")
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [BLUE if "reputation" in i.lower() else GREY for i in d.indicator]
    bars = ax.barh(d.indicator, d.pearson_r, color=colors, height=0.6)
    for b, v in zip(bars, d.pearson_r):
        ax.text(v + 0.01, b.get_y() + b.get_height() / 2, f"{v:.2f}", va="center", fontsize=10, color=INK)
    ax.set_xlim(0, 1)
    ax.set_xlabel("Pearson correlation with the overall QS score (602 scored universities)", color=MUTED)
    ax.set_title("Correlation of each indicator with the overall QS score",
                 loc="left", fontsize=13, color=INK, pad=10)
    ax.tick_params(axis="y", colors=INK, length=0)
    _style(ax)
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


def reputation_scatter(df, labels, path=None):
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.scatter(df.academic_rep, df.employer_rep, s=14, color=GREY, alpha=0.6, edgecolors="none", label="Top-500 universities")
    hi = df[df.institution_name.isin(labels)]
    ax.scatter(hi.academic_rep, hi.employer_rep, s=40, color=ORANGE, edgecolors="white", linewidths=1,
               label="Largest employer-over-academic gap")
    for _, r in hi.iterrows():
        ax.annotate(r.short_name, (r.academic_rep, r.employer_rep), xytext=(6, -3), textcoords="offset points",
                    fontsize=9, color=INK)
    ax.plot([0, 100], [0, 100], color=MUTED, linewidth=1, linestyle="--")
    ax.text(70, 64, "equal reputation", color=MUTED, fontsize=9, rotation=40)
    ax.set_xlim(0, 102)
    ax.set_ylim(0, 102)
    ax.set_xlabel("Academic reputation score", color=MUTED)
    ax.set_ylabel("Employer reputation score", color=MUTED)
    ax.set_title("Employer vs academic reputation, top-500 universities", loc="left", fontsize=13, color=INK, pad=10)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc="lower right")
    _style(ax, grid_axis="both")
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig


def country_bars(df, path=None):
    d = df.sort_values("top_100")
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(d.country_name, d.top_500, color=GREY, height=0.6, label="Top 500")
    ax.barh(d.country_name, d.top_100, color=BLUE, height=0.6, label="Top 100")
    for i, (t1, t5) in enumerate(zip(d.top_100, d.top_500)):
        ax.text(t5 + 1, i, f"{t1} / {t5}", va="center", fontsize=9, color=INK)
    ax.set_xlabel("Universities in the 2024 ranking", color=MUTED)
    ax.set_title("Universities in the top 100 and top 500, by country", loc="left", fontsize=13, color=INK, pad=10)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK, loc="lower right")
    ax.tick_params(axis="y", colors=INK, length=0)
    _style(ax)
    ax.spines["left"].set_visible(False)
    fig.tight_layout()
    if path:
        fig.savefig(path, dpi=150, bbox_inches="tight")
    return fig
