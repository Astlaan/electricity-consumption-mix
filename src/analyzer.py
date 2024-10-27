from data_fetcher import Data
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from typing import Dict
from config import SOURCE_COLORS, COUNTRY_COLORS, PSR_TYPE_MAPPING
from utils import get_active_psr_in_dataframe


def plot(data: Data):
    data.flow_pt_to_es["Power"]


def plot_source_country_pie(self, df: pd.DataFrame) -> None:
    plt.figure(figsize=(12, 10))

    # Clean and prepare data
    df = df.loc[:, (df != 0).any()]
    df = df.fillna(0)

    # Prepare data for plotting
    labels = []
    sizes = []
    colors = []

    for country in ["Portugal", "Spain"]:
        country_prefix = f"{country[:2]}_"
        country_columns = [col for col in df.columns if col.startswith(country_prefix)]

        for col in country_columns:
            source = col[3:]  # Remove country prefix
            value = df[col].mean()
            if value > 0:  # Only include non-zero values
                labels.append(f"{country}\n{source}")
                sizes.append(value)
                colors.append(
                    self.source_colors.get(source, self.source_colors["Other"])
                )

    if not sizes:
        print("No non-zero data to plot")
        return

    plt.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        textprops={"fontsize": 8},
    )
    plt.title("Electricity Mix by Source Type and Country")
    plt.axis("equal")
    plt.tight_layout()
    plt.show()


def plot_nested_pie(self, df: pd.DataFrame) -> None:
    plt.figure(figsize=(14, 12))

    # Clean and prepare data
    df = df.loc[:, (df != 0).any()]
    df = df.fillna(0)

    # Prepare outer ring (countries)
    pt_data = df[[col for col in df.columns if col.startswith("PT_")]].mean()
    es_data = df[[col for col in df.columns if col.startswith("ES_")]].mean()
    country_sizes = [pt_data.sum(), es_data.sum()]

    if sum(country_sizes) == 0:
        print("No non-zero data to plot")
        return

    country_colors = [self.country_colors[country] for country in ["Portugal", "Spain"]]

    # Prepare inner ring (sources)
    source_sizes = []
    source_colors = []
    source_labels = []

    for country_data, country in zip([pt_data, es_data], ["Portugal", "Spain"]):
        if not country_data.empty:
            for source, value in country_data.items():
                if value > 0:  # Only include non-zero values
                    source_sizes.append(value)
                    source_colors.append(
                        self.source_colors.get(source[3:], self.source_colors["Other"])
                    )
                    source_labels.append(f"{country}\n{source[3:]}")

    # Plot outer ring (countries)
    plt.pie(
        country_sizes,
        colors=country_colors,
        radius=1.3,
        labels=["Portugal", "Spain"],
        autopct="%1.1f%%",
        textprops={"fontsize": 10},
    )

    # Plot inner ring (sources)
    if source_sizes:
        plt.pie(
            source_sizes,
            colors=source_colors,
            radius=1.0,
            labels=source_labels,
            autopct="%1.1f%%",
            textprops={"fontsize": 8},
        )

    plt.title("Electricity Mix by Country and Source Type")
    plt.axis("equal")
    plt.tight_layout()
    plt.show()
