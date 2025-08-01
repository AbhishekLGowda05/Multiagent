import base64
import io
from typing import Dict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def _is_number(value: str) -> bool:
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def generate_chart(data: Dict) -> str:
    """Generate a chart for the provided data.

    If all keys are numeric, a line chart is produced, otherwise a bar chart.
    The image is returned as a base64 encoded PNG string.
    """
    if not data:
        raise ValueError("Data for chart generation is empty")

    keys = list(data.keys())
    values = list(data.values())

    fig, ax = plt.subplots(figsize=(6, 4))

    if all(_is_number(k) for k in keys):
        # sort numeric keys for a consistent line plot
        sorted_items = sorted(((float(k), v) for k, v in data.items()), key=lambda x: x[0])
        x_vals = [item[0] for item in sorted_items]
        y_vals = [item[1] for item in sorted_items]
        ax.plot(x_vals, y_vals, marker="o")
    else:
        ax.bar(keys, values)
        ax.set_xticklabels(keys, rotation=45, ha="right")

    ax.set_ylabel("Value")
    ax.set_xlabel("" if all(_is_number(k) for k in keys) else "Category")
    plt.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    plt.close(fig)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return encoded
