"""Stampa le medie di GAP_percent e di runtime per dimensione dell'istanza e metodo."""

import argparse
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser(
        description="Calcola la media di GAP_percent e runtime dal CSV dei risultati."
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="subgradient_results.csv",
        help="file CSV dei risultati (default: subgradient_results.csv)",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_file)
    df = pd.read_csv(csv_path)
    df["GAP_percent"] = pd.to_numeric(df["GAP_percent"], errors="coerce")

    gap_means = (
        df.dropna(subset=["GAP_percent"])
        .groupby(["n_clients", "n_facilities", "method"], as_index=False)
        .agg(
            mean_gap_percent=("GAP_percent", "mean"),
            instances=("GAP_percent", "count"),
        )
        .sort_values(["n_clients", "n_facilities", "method"])
    )

    print("GAP---------------------------")
    print(gap_means.to_string(index=False))

    df["runtime"] = pd.to_numeric(df["runtime"], errors="coerce")

    time_means = (
        df.dropna(subset=["runtime"])
        .groupby(["n_clients", "n_facilities", "method"], as_index=False)
        .agg(
            mean_time=("runtime", "mean"),
            instances=("runtime", "count"),
        )
        .sort_values(["n_clients", "n_facilities", "method"])
    )

    print("TIME--------------------------")
    print(time_means.to_string(index=False))



if __name__ == "__main__":
    main()
