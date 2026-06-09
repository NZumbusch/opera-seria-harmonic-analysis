from pathlib import Path

import plotly.graph_objects as go

from analysis.chord_distribution.chord_distribution_rolling_time_windows import (
    export_public_chord_distribution_windows,
)
from src.paths import OUTPUT_FIGURES_INTERACTIVE_DIR


def draw_interactive_public_chord_distribution_timeline(
    public_data: dict[str, dict[str, int | float]],
    output_path: Path = OUTPUT_FIGURES_INTERACTIVE_DIR
    / "interactive_chord_timeline.html",
    title: str = "Chord distribution over time",
) -> None:
    if not public_data:
        return

    window_labels = sorted(public_data.keys(), key=lambda s: int(s.split("-")[0]))

    chord_names = [
        key for key in public_data[window_labels[0]].keys() if key != "n_works"
    ]

    fig = go.Figure()

    max_pct = max(
        float(row.get(chord, 0.0))
        for row in public_data.values()
        for chord in chord_names
    )

    for i, window_label in enumerate(window_labels):
        row = public_data[window_label]
        y_values = [float(row.get(chord, 0.0)) for chord in chord_names]
        n_works = row.get("n_works", 0)

        fig.add_trace(
            go.Bar(
                x=chord_names,
                y=y_values,
                name=window_label,
                visible=(i == 0),
                marker_color="#2a6f97",
                hovertemplate=(
                    "Chord: %{x}<br>"
                    "Share: %{y:.2f}%<br>"
                    f"Window: {window_label}<br>"
                    f"Works: {n_works}"
                    "<extra></extra>"
                ),
            )
        )

    steps = []
    for i, window_label in enumerate(window_labels):
        n_works = public_data[window_label].get("n_works", 0)
        steps.append(
            dict(
                method="update",
                args=[
                    {"visible": [j == i for j in range(len(window_labels))]},
                    {"title": f"{title} — {window_label} (n={n_works})"},
                ],
                label=window_label,
            )
        )

    fig.update_layout(
        title=f"{title} — {window_labels[0]} (n={public_data[window_labels[0]].get('n_works', 0)})",
        xaxis_title="Chord",
        yaxis_title="Share of chord tokens (%)",
        xaxis=dict(
            categoryorder="array",
            categoryarray=chord_names,
            tickangle=-45,
        ),
        yaxis=dict(
            range=[0, max_pct * 1.08],
            ticksuffix="%",
            tickformat=".1f",
            rangemode="tozero",
        ),
        sliders=[
            {
                "active": 0,
                "currentvalue": {"prefix": "Window: "},
                "pad": {"t": 40},
                "steps": steps,
            }
        ],
        template="plotly_white",
        width=1300,
        height=750,
        bargap=0.18,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(output_path, include_plotlyjs="cdn", full_html=True)


if __name__ == "__main__":
    draw_interactive_public_chord_distribution_timeline(
        export_public_chord_distribution_windows()
    )
