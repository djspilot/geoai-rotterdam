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

    n = len(lines)
    line_in = fs / 72.0 * 1.7               # physical line pitch (inches)
    base = 0.02                             # bottom line baseline (figure fraction)

    # Draw lines stacked upward from the bottom with a fixed physical pitch (so the
    # spacing survives fit_figure_to_data resizing the figure height). i=0 is top.
    for i, ln in enumerate(lines):
        off = (n - 1 - i) * line_in
        tr = fig.transFigure + ScaledTranslation(0, off, fig.dpi_scale_trans)
        fig.text(0.05, base, ln, transform=tr, fontsize=fs,
                 color=STYLE["footer_color"], ha="left")
    top_off = (n - 1) * line_in
    trp = fig.transFigure + ScaledTranslation(0, top_off, fig.dpi_scale_trans)
    fig.text(0.95, base, publisher, transform=trp, fontsize=fs,
             color=STYLE["footer_color"], ha="right")

    # Separator just above the top footer line (0.04 for a single line; rises with
    # extra lines). The map bottom margin grows by the extra footer height.
    sep_y = max(0.04, base + (top_off + 0.55 * line_in) / figh)
    sep = mlines.Line2D([0.05, 0.95], [sep_y, sep_y],
                        color=STYLE["separator_color"], lw=0.5,
                        transform=fig.transFigure, figure=fig)
    fig.lines.append(sep)

    bottom = (0.05 if tight_bottom else 0.08) + (n - 1) * line_in / figh
    fig.subplots_adjust(left=pad, right=1 - pad, top=top, bottom=bottom)


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
    h_frac = sp.top - sp.bottom
    if w_frac <= 0 or h_frac <= 0 or data_aspect <= 0:
        return
    figw, _ = fig.get_size_inches()
    fig.set_size_inches(figw, figw * w_frac / (data_aspect * h_frac))


