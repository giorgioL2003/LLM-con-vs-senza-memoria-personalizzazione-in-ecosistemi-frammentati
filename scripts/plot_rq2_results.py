#!/usr/bin/env python3
"""Genera manualmente un grafico a barre verticali per lo scenario scelto.

Esecuzione dalla cartella del progetto:
    .venv-grafici/bin/python scripts/plot_rq2_results.py --scenario SC02

Le sorgenti e le metriche sono le stesse di verify_rq2_tables.py.
Nessuna chiamata al modello e nessuna modifica ai giudizi.
"""

import argparse
import os
from pathlib import Path

import verify_rq2_tables as tables

PROJECT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT / ".matplotlib-cache"))

try:
    # Lascia a PyCharm/Matplotlib la scelta del backend per mostrare il grafico.
    import matplotlib.pyplot as plt
except ImportError:
    raise SystemExit(
        "Matplotlib manca in questo Python. Usa .venv-grafici/bin/python oppure "
        "installa la dipendenza con: python -m pip install matplotlib"
    )






# Da PyCharm: cambia questa riga e premi Run.
SCENARIO = "SC05"  # SC02, SC03, SC04 oppure SC05







MODES = {
    "SC02": ("T", "F", "FULL_HISTORY"),
    "SC03": ("F", "U", "FULL_HISTORY"),
    "SC04": ("T", "U", "G", "FULL_HISTORY"),
    "SC05": ("T", "U", "GER", "FULL_HISTORY"),
}
LABELS = {
    "T": "Turn-level RAG",
    "F": "Fact-based RAG",
    "U": "Fact-based RAG\ncon aggiornamenti",
    "G": "Graph-based Memory",
    "GER": "Memoria gerarchica",
    "FULL_HISTORY": "Full history\n(controllo diagnostico)",
}
# Ogni architettura mantiene lo stesso colore in tutti gli scenari.
COLORS = {
    "T": "#0072B2",           # blu
    "F": "#E69F00",           # arancione
    "U": "#009E73",           # verde
    "G": "#CC79A7",           # viola
    "GER": "#D55E00",         # vermiglio
    "FULL_HISTORY": "#C62828", # rosso
}


def draw_scenario(ax, scenario, values):
    modes = MODES[scenario]
    positions = [i + (0.5 if mode == "FULL_HISTORY" else 0)
                 for i, mode in enumerate(modes)]
    counts = [int(values[scenario, mode]["complete_e_supportate"].split("/")[0])
              for mode in modes]
    totals = [int(values[scenario, mode]["n_risposte"]) for mode in modes]
    colors = [COLORS[mode] for mode in modes]
    ax.bar(positions, counts, width=0.6, color=colors, zorder=3)
    for x, count, total in zip(positions, counts, totals):
        ax.text(x, count + 0.12, f"{count}/{total}", ha="center", va="bottom",
                fontsize=13, fontweight="bold")
    ax.axvline((positions[-2] + positions[-1]) / 2,
               color="#B2B8BF", linestyle="--")
    ax.set_xticks(positions, [LABELS[m] for m in modes])
    ax.set_ylim(0, 7)
    ax.set_yticks(range(8))
    ax.set_ylabel("Risposte complete e supportate")
    ax.set_xlabel("Architettura / controllo diagnostico", labelpad=12)
    ax.grid(axis="y", color="#E5E7EB", zorder=0)
    ax.spines[["top", "right"]].set_visible(False)
    title = f"{scenario} — Budget di 200 token" if scenario == "SC05" else scenario
    ax.set_title(title, pad=18)


def decorate(fig):
    fig.subplots_adjust(left=0.1, right=0.97, top=0.87, bottom=0.22)


def save(fig, folder, name):
    for extension in ("png", "svg"):
        path = folder / f"{name}.{extension}"
        fig.savefig(path, dpi=300, facecolor="white")
        print(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=tables.VARIANT / "grafici",
                        help="cartella di destinazione delle immagini")
    parser.add_argument("--scenario", choices=tuple(MODES), default=SCENARIO)
    args = parser.parse_args()
    if args.scenario not in MODES:
        parser.error("SCENARIO deve essere SC02, SC03, SC04 oppure SC05")

    # 1. Ricalcola e verifica i numeri prima di disegnarli.
    checked = tables.verify()
    values = {(scenario, mode): row for scenario, mode, row in checked}

    # 2. Genera SOLO lo scenario scelto, quando esegui manualmente lo script.
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                         "svg.fonttype": "none", "axes.labelcolor": "#374151",
                         "text.color": "#172A3A"})
    args.out.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    draw_scenario(ax, args.scenario, values)
    decorate(fig)
    save(fig, args.out, f"complete_{args.scenario.lower()}")
    plt.show()  # Visualizza il grafico nel pannello Plots o in una finestra.
    plt.close(fig)


if __name__ == "__main__":
    main()
