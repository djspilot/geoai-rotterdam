"""Maak een presentabele PDF voor bestuurlijke bespreking afvalbakken."""

from __future__ import annotations

from pathlib import Path
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.image import imread


PROJECT = Path(__file__).resolve().parents[1]
OUT = PROJECT / "output"
ASSETS = OUT / "report_assets"

MAP_IMG = OUT / "kaart_afvalbakken_vergelijking_centrum_hillegersberg.png"
PHOTO_CENTRUM = ASSETS / "rotterdam_centrum.jpg"
PHOTO_HIL = ASSETS / "hillegersberg.jpg"
PDF_OUT = OUT / "rapport_prullenbakken_rotterdam_ruud_raak.pdf"

COUNT_CENTRUM = 1196
COUNT_HIL = 509
RATIO = COUNT_CENTRUM / COUNT_HIL
DIFF = COUNT_CENTRUM - COUNT_HIL


def draw_wrapped_text(ax, text: str, x: float, y: float, width: int = 90, line_height: float = 0.05, fontsize: int = 12):
    wrapped = textwrap.fill(text, width=width)
    for i, line in enumerate(wrapped.splitlines()):
        ax.text(x, y - i * line_height, line, fontsize=fontsize, va="top", ha="left")


def make_page_1(pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))  # A4 landscape
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    ax.text(0.05, 0.92, "Kort rapport: prullenbakken in Rotterdam", fontsize=26, fontweight="bold", ha="left")
    ax.text(0.05, 0.87, "Voor wethouder | Opsteller: Ruud Raak, manager Stedelijk Beheer | Datum: 16 april 2026", fontsize=11, color="#444")

    ax.text(0.05, 0.78, "1. Samenvatting afvalbeleid (in gewone taal)", fontsize=16, fontweight="bold")

    p1 = "Rotterdam wil een schone stad met minder zwerfafval en minder restafval. Daarom zet de gemeente in op afval scheiden, goed opruimen en duidelijke voorzieningen in de wijk."
    p2 = "Afvalbakken op straat zijn een belangrijk onderdeel van dat beleid. Ze helpen om afval direct weg te gooien en houden straten, pleinen en winkelgebieden schoner."
    p3 = "De gemeente stuurt op de plekken waar de druk het hoogst is, zoals drukke centra en locaties met veel bezoekers."

    draw_wrapped_text(ax, p1, 0.06, 0.72, width=105, line_height=0.05, fontsize=13)
    draw_wrapped_text(ax, p2, 0.06, 0.61, width=105, line_height=0.05, fontsize=13)
    draw_wrapped_text(ax, p3, 0.06, 0.50, width=105, line_height=0.05, fontsize=13)

    ax.text(0.05, 0.38, "2. Kerncijfers vergelijking", fontsize=16, fontweight="bold")
    ax.text(0.07, 0.32, f"• Rotterdam Centrum: {COUNT_CENTRUM} afvalbakken", fontsize=14)
    ax.text(0.07, 0.27, f"• Hillegersberg-Schiebroek: {COUNT_HIL} afvalbakken", fontsize=14)
    ax.text(0.07, 0.22, f"• Verschil: {DIFF}", fontsize=14)
    ax.text(0.07, 0.17, f"• Verhouding Centrum / Hillegersberg-Schiebroek: {RATIO:.2f}", fontsize=14)

    ax.text(0.05, 0.08, "Duiding: Rotterdam Centrum heeft ruim twee keer zoveel afvalbakken als Hillegersberg-Schiebroek.", fontsize=12, color="#333")

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def make_page_2(pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    ax.text(0.05, 0.94, "Kaart en vergelijking", fontsize=18, fontweight="bold")

    if MAP_IMG.exists():
        img = imread(MAP_IMG)
        ax_img = fig.add_axes([0.05, 0.11, 0.90, 0.78])
        ax_img.imshow(img)
        ax_img.axis("off")
    else:
        ax.text(0.05, 0.80, "Kaartafbeelding niet gevonden.", fontsize=12, color="red")

    ax.text(0.05, 0.04, "Bron data: Gemeente Rotterdam SB_Infra/Afvalbak + TIR gebieden (analyse in EPSG:28992).", fontsize=10, color="#555")

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def make_page_3(pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")

    ax.text(0.05, 0.94, "Beeld van de gebieden", fontsize=18, fontweight="bold")

    if PHOTO_CENTRUM.exists():
        img1 = imread(PHOTO_CENTRUM)
        ax1 = fig.add_axes([0.05, 0.22, 0.42, 0.66])
        ax1.imshow(img1)
        ax1.axis("off")
        ax.text(0.05, 0.17, "Rotterdam Centrum", fontsize=12, fontweight="bold")

    if PHOTO_HIL.exists():
        img2 = imread(PHOTO_HIL)
        ax2 = fig.add_axes([0.53, 0.22, 0.42, 0.66])
        ax2.imshow(img2)
        ax2.axis("off")
        ax.text(0.53, 0.17, "Hillegersberg", fontsize=12, fontweight="bold")

    ax.text(
        0.05,
        0.08,
        "Fotobronnen: Wikimedia Commons (CC BY-SA).\n"
        "- https://commons.wikimedia.org/wiki/File:Rot_street.JPG\n"
        "- https://commons.wikimedia.org/wiki/File:Hillegersberg_Rotterdam_007.jpg",
        fontsize=9,
        color="#555",
    )

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    with PdfPages(PDF_OUT) as pdf:
        make_page_1(pdf)
        make_page_2(pdf)
        make_page_3(pdf)

    print(f"PDF opgeslagen: {PDF_OUT}")


if __name__ == "__main__":
    main()
