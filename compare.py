from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from solver import Solver

def compare_instance(n_clients, facilities, clients, opening_cost, service_cost, time_limit=300):
    solver = Solver(n_clients, facilities, clients, opening_cost, service_cost)

    pli = solver.solve_pli(time_limit)
    rc = solver.solve_rc(time_limit)

    # upper bound ammissibile se disponibile
    ub = pli["objective"]

    lr_demand = solver.lagrangian_demand(upper_bound=ub, time_limit=time_limit)
    lr_consistency = solver.lagrangian_consistency(upper_bound=ub, time_limit=time_limit)

    summary = {
        "n_facilities": len(facilities),
        "n_clients": len(clients),
        "PLI_obj": pli["objective"],
        "PLI_status": pli["status"],
        "PLI_time": pli["runtime"],
        "RC_obj": rc["objective"],
        "RC_status": rc["status"],
        "RC_time": rc["runtime"],
        "LR_demand_LB": lr_demand["best_lb"],
        "LR_demand_status": lr_demand["stop_reason"],
        "LR_demand_time": lr_demand["runtime"],
        "LR_demand_iter": lr_demand["iterations"],
        "LR_consistency_LB": lr_consistency["best_lb"],
        "LR_consistency_status": lr_consistency["stop_reason"],
        "LR_consistency_time": lr_consistency["runtime"],
        "LR_consistency_iter": lr_consistency["iterations"],
    }

    for name, lb in [
        ("RC", rc["objective"]),
        ("LR_demand", lr_demand["best_lb"]),
        ("LR_consistency", lr_consistency["best_lb"]),
    ]:
        if ub is not None and lb is not None and abs(ub) > 1e-10:
            summary[name + "_gap_percent"] = (
                    100.0 * (ub - lb) / abs(ub)
            )
        else:
            summary[name + "_gap_percent"] = None

    return {
        "summary": summary,
        "pli": pli,
        "rc": rc,
        "lr_demand": lr_demand,
        "lr_consistency": lr_consistency,
    }

def _to_csv(result, instance_name, filename="subgradient_results.csv"):
    res = result["summary"]

    df = pd.DataFrame({
        "instance": [instance_name] * 4,
        "n_clients": [res["n_clients"]] * 4,
        "n_facilities": [res["n_facilities"]] * 4,
        "method": ["PLI", "RC", "LR_demand", "LR_consistency"],
        "objective": [res["PLI_obj"], res["RC_obj"], res["LR_demand_LB"], res["LR_consistency_LB"]],
        "GAP_percent": ["-", res["RC_gap_percent"], res["LR_demand_gap_percent"], res["LR_consistency_gap_percent"]],
        "runtime": [res["PLI_time"], res["RC_time"], res["LR_demand_time"], res["LR_consistency_time"]],
        "status": [res["PLI_status"], res["RC_status"], res["LR_demand_status"], res["LR_consistency_status"]],
        "iter": ["-", "-", res["LR_demand_iter"], res["LR_consistency_iter"]],
    })

    path = Path(filename)
    file_exists = path.exists() and path.stat().st_size > 0

    df.to_csv(
        path,
        mode="a" if file_exists else "w",
        header=not file_exists,
        index=False,
    )

    print(f"Risultati aggiunti per l'istanza {instance_name}")

    print(df)

def _to_plot():
    df = pd.read_csv("subgradient_results.csv")

    methods = ["PLI", "RC", "LR_demand", "LR_consistency"]
    colors = dict(zip(methods, plt.get_cmap("tab10").colors[:len(methods)]))
    handles = [Patch(facecolor=colors[method], label=method) for method in methods]

    # Le dimensioni identificano il gruppo di istanze da aggregare.
    dimensions = (
        df[["n_clients", "n_facilities"]]
        .drop_duplicates()
        .sort_values(["n_clients", "n_facilities"])
        .reset_index(drop=True)
    )
    dimensions["label"] = dimensions.apply(
        lambda row: f"{int(row['n_clients'])}C, {int(row['n_facilities'])}F",
        axis=1,
    )

    # Le colonne numeriche possono contenere '-' (ad esempio GAP per PLI).
    df["objective"] = pd.to_numeric(df["objective"], errors="coerce")
    df["GAP_percent"] = pd.to_numeric(df["GAP_percent"], errors="coerce")
    df["runtime"] = pd.to_numeric(df["runtime"], errors="coerce")

    # directory in cui salvare i grafici
    output_dir = Path("plots")
    output_dir.mkdir(exist_ok=True)

    def _aggregate(metric, plotted_methods):
        """Return mean and sample standard deviation by dimension and method."""
        index = pd.MultiIndex.from_frame(
            dimensions[["n_clients", "n_facilities"]]
        )
        result = {}
        for method in plotted_methods:
            result[method] = (
                df[df["method"] == method]
                .groupby(["n_clients", "n_facilities"])[metric]
                .agg(mean="mean", std="std")
                .reindex(index)
            )
        return result

    # 1. OBJECTIVE: media per dimensione con deviazione standard (±σ).
    fig, ax = plt.subplots(figsize=(13, 6))
    group_width = 0.82
    width = group_width / len(methods)
    x = np.arange(len(dimensions))
    objective_stats = _aggregate("objective", methods)

    for method_index, method in enumerate(methods):
        stats = objective_stats[method]
        offset = (method_index - (len(methods) - 1) / 2) * width
        ax.bar(
            x + offset,
            stats["mean"],
            width=width * 0.9,
            yerr=stats["std"].fillna(0),
            capsize=3,
            color=colors[method],
            alpha=0.8,
            label=method,
        )

    ax.set_title("Objective values by problem dimension")
    ax.set_xlabel("Problem dimension (clients, facilities)")
    ax.set_ylabel("Objective / Lower Bound")
    ax.set_xticks(x)
    ax.set_xticklabels(dimensions["label"])
    ax.legend(handles=handles, title="Method")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_dir / "objective.png", dpi=300)
    plt.close(fig)

    def _plot_mean_std_bars(metric, title, ylabel, filename, plotted_methods):
        """Plot means with sample standard deviation as error bars."""
        fig, ax = plt.subplots(figsize=(13, 6))
        width = 0.8 / len(plotted_methods)
        x = np.arange(len(dimensions))

        for method_index, method in enumerate(plotted_methods):
            grouped = _aggregate(metric, plotted_methods)[method]
            offset = (method_index - (len(plotted_methods) - 1) / 2) * width
            ax.bar(
                x + offset,
                grouped["mean"],
                width=width * 0.9,
                yerr=grouped["std"].fillna(0),
                capsize=3,
                color=colors[method],
                alpha=0.8,
                label=method,
            )

        ax.set_title(title)
        ax.set_xlabel("Problem dimension (clients, facilities)")
        ax.set_ylabel(ylabel)
        ax.set_xticks(x)
        ax.set_xticklabels(dimensions["label"])
        ax.legend(title="Method")
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        fig.savefig(output_dir / filename, dpi=300)
        plt.close(fig)

    # 2. GAP: media per dimensione e deviazione standard.
    _plot_mean_std_bars(
        "GAP_percent", "Mean gap by problem dimension", "Gap (%)", "gap.png",
        [method for method in methods if method != "PLI"],
    )

    # 3. RUNTIME: curve della media con deviazione standard, asse Y logaritmico.
    fig, ax = plt.subplots(figsize=(13, 6))
    runtime_stats = _aggregate("runtime", methods)
    for method in methods:
        stats = runtime_stats[method]
        mean = stats["mean"]
        ## std = stats["std"].fillna(0)
        ax.errorbar(
            x,
            mean,
            ## yerr=std,
            color=colors[method],
            marker="o",
            linewidth=2,
            capsize=3,
            label=method,
        )

    ax.set_yscale("log")
    ax.set_title("Mean execution time by problem dimension")
    ax.set_xlabel("Problem dimension (clients, facilities)")
    ax.set_ylabel("Time (seconds, logarithmic scale)")
    ax.set_xticks(x)
    ax.set_xticklabels(dimensions["label"])
    ax.legend(title="Method")
    ax.grid(True, which="both", axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_dir / "runtime.png", dpi=300)
    plt.close(fig)

    # 4. STATUS: ogni coppia metodo-status è una colonna distinta sull'asse X.
    status_order = [
        "optimal", "time_limit", "zero_subgradient", "infeasible",
        "unbounded", "infeasible_or_unbounded", "iteration_limit",
        "node_limit", "solution_limit", "interrupted", "suboptimal",
    ]
    observed_statuses = set(df["status"].dropna())
    statuses = [status for status in status_order if status in observed_statuses]
    statuses += sorted(observed_statuses.difference(statuses))
    status_pairs = [
        (method, status)
        for method in methods
        for status in statuses
        if ((df["method"] == method) & (df["status"] == status)).any()
    ]
    status_values = [
        int(((df["method"] == method) & (df["status"] == status)).sum())
        for method, status in status_pairs
    ]

    fig, ax = plt.subplots(figsize=(max(10, len(status_pairs) * 0.9), 6))
    ax.bar(
        range(len(status_pairs)),
        status_values,
        color=[colors[method] for method, _ in status_pairs],
    )
    ax.set_title("Solver status distribution")
    ax.set_xlabel("Method and status")
    ax.set_ylabel("Number of instances")
    ax.set_xticks(range(len(status_pairs)))
    ax.set_xticklabels(
        [f"{method}\n{status}" for method, status in status_pairs],
        rotation=45,
        ha="right",
    )
    ax.legend(handles=handles, title="Method")
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_dir / "status.png", dpi=300)
    plt.close(fig)
