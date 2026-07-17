"""Titel, subtitel, footer en het passen van de figuur op de data."""
from __future__ import annotations

from ._base import *
from .elements import add_scalebar, add_north_arrow

def style_map(ax, title: str, *, subtitle: str | None = None,
              scalebar: bool = False, north: "bool | str" = False,
              north_variant: str = "B", scalebar_variant: str = "B") -> None:
    """Apply Rotterdam cartographic styling to one axes.

    `north`: **default False** — een noordpijl is alleen nodig als het noorden niet
    recht naar boven wijst (gedraaide kaart) of bij een navigatiekaart (invariant
    13). Standaard noord-boven kaarten krijgen er dus géén. Zet `True` (pijl
    linksboven) of een hoek-string ('upper left'/'upper right') als een pijl wél
    nodig is — rechterhoek wanneer de linker bezet is.
    """
    _apply_rc()
    ax.set_axis_off()
    ax.set_facecolor(STYLE["ax_bg"])

    # Titel + subtitel staan ALTIJD boven de kaart, samen — nooit óver de kaart
    # (invariant "Titel en subtitel boven de kaart"). De subtitel komt net boven de
    # kaartrand (va="bottom", kleine fysieke marge) en de titel krijgt genoeg pad
    # om daar nog net boven te vallen.
    pad = 14
    if subtitle:
        from matplotlib.transforms import ScaledTranslation
        sub_gap_in = 3 / 72.0                     # subtitel-onderkant boven de kaartrand
        ax.text(
            0.0, 1.0, subtitle,
            transform=ax.transAxes
            + ScaledTranslation(0, sub_gap_in, ax.figure.dpi_scale_trans),
            ha="left", va="bottom",
            fontsize=STYLE["subtitle_size"], color=STYLE["subtitle_color"],
            weight=STYLE["subtitle_weight"],
        )
        pad = int(round(sub_gap_in * 72 + STYLE["subtitle_size"] + 8))  # titel boven de subtitel

    ax.set_title(
        title, fontsize=STYLE["title_size"], fontweight=STYLE["title_weight"],
        color=STYLE["title_color"], loc="left", pad=pad,
    )
    if scalebar:
        add_scalebar(ax, variant=scalebar_variant)
    if north:
        add_north_arrow(ax, corner=north if isinstance(north, str) else "upper left",
                        variant=north_variant)


def finalize_map(
    fig, ax=None, *,
    source: str = "Obsurv via diensten.rotterdam.nl",
    date: str | None = None,
    author: str | None = None,
    suptitle: str | None = None,
    suptitle_subtitle: str | None = None,
    pad: float = 0.04,
    tight_bottom: bool = False,
) -> None:
    """Figure-level polish: footer with source, optional suptitle, clean margins.

    Call as last step before `save_map`.

    `tight_bottom=True` shrinks the bottom margin so the footer sits right under
    the map — use it only when the scale bar is drawn *on* the map
    (`add_scalebar(ax, inside=True)`); with a below-map scale bar it would be
    clipped. Combine with `fit_figure_to_data` to also remove side/bottom
    whitespace from the aspect ratio.
    """
    from datetime import date as _date
    import matplotlib.lines as mlines
    _apply_rc()
    if date is None:
        date = _date.today().isoformat()

    fig.set_facecolor(STYLE["fig_bg"])

    if suptitle:
        # Stapel de suptitel (+ optionele subregel) met fysieke (inch) marges vanaf
        # de bovenrand, zodat de tussenruimte ook op een lage/brede figuur klopt —
        # vaste fracties (0.98/0.945) liepen daar over elkaar. De as-bovenrand `top`
        # zakt mee zodat de per-paneel titels vrij onder het suptitel-blok vallen.
        _fw, _fh = fig.get_size_inches()
        # Hoofdtitel groter dan de deelkaart-titels (STYLE["title_size"]) — zie de
        # invariant "Titelhiërarchie".
        sup_fs = STYLE["suptitle_size"]
        y_top_in = 0.16                                # marge boven de hoofdtitel (inch)
        fig.suptitle(suptitle, fontsize=sup_fs, fontweight=STYLE["suptitle_weight"],
                     color=STYLE["title_color"], x=0.05, ha="left",
                     y=1 - y_top_in / _fh, va="top")
        header_in = y_top_in + sup_fs / 72.0 + 0.10    # tot onder de suptitel + gap
        if suptitle_subtitle:
            fig.text(0.05, 1 - header_in / _fh, suptitle_subtitle,
                     fontsize=STYLE["subtitle_size"],
                     color=STYLE["subtitle_color"], ha="left", va="top")
            header_in += STYLE["subtitle_size"] / 72.0 + 0.14
        else:
            header_in += 0.10
        header_in += 0.42                              # ruimte voor de per-paneel titel
        top = 1 - header_in / _fh
    else:
        top = 0.94

    import matplotlib.text as mtext
    from matplotlib.transforms import ScaledTranslation

    footer_parts = [f"Bron: {source}", f"Datum: {date}"]
    if author:
        footer_parts.append(author)
    # Always disclose AI authorship in the footer.
    footer_parts.append("Disclaimer: deze kaart is gemaakt met AI.")
    publisher = "Gemeente Rotterdam"        # right-aligned at the map's right edge

    fs = STYLE["footer_size"]
    figw, figh = fig.get_size_inches()
    renderer = fig.canvas.get_renderer()

    def _wid(s):                            # rendered width of a footer string (inches)
        t = mtext.Text(0, 0, s, fontsize=fs)
        t.figure = fig
        return t.get_window_extent(renderer).width / fig.dpi

    joiner = "  ·  "
    avail = (0.95 - 0.05) * figw            # usable footer width (inches)
    gap = 0.15                              # min gap between left text and publisher
    raw = joiner.join(footer_parts)
    # Wrap units are the "·"-separated segments (also splits any "·" inside the
    # source itself, e.g. "Bron: … · Basiskaart: …"), so no single unit is too big.
    tokens = [t.strip() for t in raw.split("·") if t.strip()]

    if _wid(raw) + gap + _wid(publisher) <= avail:
        lines = [raw]                       # everything fits on one line
    else:
        # Not enough room -> wrap over multiple lines. The top line reserves space
        # for the right-aligned publisher; lower lines use the full width.
        lines, cur = [], ""
        budget = avail - _wid(publisher) - gap
        for tok in tokens:
            trial = tok if not cur else cur + joiner + tok
            if cur and _wid(trial) > budget:
                lines.append(cur)
                cur, budget = tok, avail
            else:
                cur = trial
        lines.append(cur)

    # De footer + ondermarge staan volledig in FYSIEKE millimeters vanaf de
    # figuur-onderrand. Zo verschuift de lay-out niet als fit_figure_to_data de
    # figuurhoogte aanpast — met figuur-fracties bewoog de witband tussen kaart en
    # footer namelijk mee met de hoogte (de terugkerende "witrand aan de onderzijde").
    n = len(lines)
    line_mm = fs / 72.0 * 25.4 * 1.7        # regelafstand (mm), afgeleid van de fontgrootte
    cap_mm = fs / 72.0 * 25.4 * 0.95        # ~hoogte van een footer-regel (mm)
    pad_bottom_mm = 2.5                     # onderste footer-regel boven de figuurrand
    sep_gap_mm = 1.3                        # scheidingslijn boven de bovenste regel
    map_gap_mm = 1.5 if tight_bottom else 2.5   # vaste witmarge kaart <-> scheidingslijn

    def _from_bottom(y_mm):                 # y_mm millimeter boven de figuur-onderrand
        return fig.transFigure + ScaledTranslation(0, y_mm * MM, fig.dpi_scale_trans)

    # Footer-regels van onder naar boven gestapeld (i=0 = bovenste regel).
    for i, ln in enumerate(lines):
        y_mm = pad_bottom_mm + (n - 1 - i) * line_mm
        fig.text(0.05, 0.0, ln, transform=_from_bottom(y_mm), fontsize=fs,
                 color=STYLE["footer_color"], ha="left", va="baseline")
    top_baseline_mm = pad_bottom_mm + (n - 1) * line_mm
    fig.text(0.95, 0.0, publisher, transform=_from_bottom(top_baseline_mm), fontsize=fs,
             color=STYLE["footer_color"], ha="right", va="baseline")

    # Scheidingslijn net boven de bovenste footer-regel; de kaart-onderrand houdt een
    # vaste fysieke marge (`map_gap_mm`) daarboven.
    sep_mm = top_baseline_mm + cap_mm + sep_gap_mm
    sep = mlines.Line2D([0.05, 0.95], [0.0, 0.0], color=STYLE["separator_color"],
                        lw=0.5, transform=_from_bottom(sep_mm), figure=fig)
    fig.lines.append(sep)

    bottom_mm = sep_mm + map_gap_mm
    fig.subplots_adjust(left=pad, right=1 - pad, top=top, bottom=bottom_mm * MM / figh)

    # Fysieke boven-/ondermarge (in mm) bewaren zodat fit_figure_to_data ze exact behoudt.
    fig._rot_top_mm = (1 - top) * figh / MM
    fig._rot_bottom_mm = bottom_mm


def fit_figure_to_data(fig, ax) -> None:
    """Resize the figure *height* so an equal-aspect map fills the plotting area
    with no top/bottom whitespace.

    Call **after** `finalize_map` (so the subplot margins are final). Uses the
    data extent's aspect and the current subplot margins (`fig.subplotpars`);
    the width is kept, the height is recomputed. If a legend/list box is
    measured against the axes, draw it *after* this call.
    """
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    dh = y1 - y0
    if dh <= 0:
        return
    data_aspect = (x1 - x0) / dh
    sp = fig.subplotpars
    w_frac = sp.right - sp.left
    if w_frac <= 0 or data_aspect <= 0:
        return
    figw, figh = fig.get_size_inches()
    # Behoud de FYSIEKE boven-/ondermarge (header met titel, footerblok) en pas alleen
    # de ashoogte aan zodat de gelijk-aspect kaart de plotruimte exact vult. De oude
    # aanpak hield de *fracties* gelijk, waardoor die marges — en dus de witband onder
    # de kaart — met de nieuwe figuurhoogte meebewogen. Marges in mm; matplotlib's
    # set_size_inches werkt in inch, dus reken om via MM.
    top_in = getattr(fig, "_rot_top_mm", (1 - sp.top) * figh / MM) * MM
    bot_in = getattr(fig, "_rot_bottom_mm", sp.bottom * figh / MM) * MM
    axes_h_in = figw * w_frac / data_aspect
    new_figh = top_in + axes_h_in + bot_in
    if new_figh <= 0:
        return
    fig.set_size_inches(figw, new_figh)
    fig.subplots_adjust(top=1 - top_in / new_figh, bottom=bot_in / new_figh)


