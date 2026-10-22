"""Offline cell checks: python -m unittest discover -s tests -v.

Requires pandas and matplotlib; no energy-market or taxi data is downloaded.
"""

import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def code_cell_containing(text):
    notebook = json.loads(
        (Path(__file__).resolve().parents[1] / "scaling_up_python.ipynb").read_text()
    )
    source = next(
        "".join(cell["source"])
        for cell in notebook["cells"]
        if cell["cell_type"] == "code" and text in "".join(cell["source"])
    )
    if source.startswith("%%time\n"):
        source = source.split("\n", 1)[1]
    return compile(source, "scaling_up_python.ipynb:compatibility-cell", "exec")


class NotebookCompatibilityTests(unittest.TestCase):
    def test_monthly_urls_preserve_month_end_dates(self):
        # Freeze the clock without replacing pandas' date-range implementation.
        pandas = SimpleNamespace(
            date_range=pd.date_range,
            offsets=pd.offsets,
            Timestamp=SimpleNamespace(today=lambda: pd.Timestamp("2020-11-05")),
        )
        namespace = {"pd": pandas}
        exec(code_cell_containing("date_range = pd.date_range("), namespace)
        dates = namespace["date_range"]
        urls = namespace["csv_file_list"]
        self.assertEqual(len(dates), 170)
        self.assertEqual(dates[0], pd.Timestamp("2006-09-30"))
        self.assertEqual(dates[-1], pd.Timestamp("2020-10-31"))
        self.assertIn(pd.Timestamp("2020-02-29"), dates)
        self.assertEqual(len(set(urls)), len(urls))
        self.assertTrue(urls[0].endswith("facility-scada-2006-09.csv"))
        self.assertTrue(urls[-1].endswith("facility-scada-2020-10.csv"))

    def test_energy_plot_renders_and_keeps_daily_cumulative_totals(self):
        frame = pd.DataFrame(
            {"Generator A": [1.0, 2.0, 4.0], "Generator B": [2.0, 3.0, 5.0]},
            index=pd.to_datetime(
                ["2020-01-01 00:00", "2020-01-01 12:00", "2020-01-02 00:00"]
            ),
        )
        namespace = {
            "plt": plt,
            "aemo_scada_pivot_df": frame,
            "top_10_generators": frame.columns,
        }
        self.addCleanup(plt.close, "all")
        exec(code_cell_containing("with plt.style.context("), namespace)
        ax = namespace["ax"]
        ax.figure.canvas.draw()
        self.assertEqual(ax.get_title(), "Energy Generated")
        self.assertEqual(ax.get_xlabel(), "Time")
        self.assertEqual(ax.get_ylabel(), "Energy Generated (GWh)")
        self.assertEqual(list(ax.lines[0].get_ydata()), [3.0, 7.0])
        self.assertEqual(list(ax.lines[1].get_ydata()), [5.0, 10.0])


if __name__ == "__main__":
    unittest.main()
