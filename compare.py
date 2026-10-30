from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

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

    # ordina le istanze prima per clienti, poi per facility
    df = df.sort_values(
        by=["n_clients", "n_facilities", "instance"]
    )

    # crea una tabella con una riga per istanza
    instances = (
        df[["instance", "n_clients", "n_facilities"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # etichette asse X: nome istanza e dimensioni
    instances["label"] = instances.apply(
        lambda row: (
            f"{row['instance']}\n"
            f"({row['n_clients']}C, {row['n_facilities']}F)"
        ),
        axis=1
    )

    # posizione numerica di ogni istanza
    instances["x"] = range(len(instances))

    # associa ogni risultato alla posizione della sua istanza
    df = df.merge(
        instances[["instance", "x"]],
        on="instance",
        how="left"
    )

    # directory in cui salvare i grafici
    output_dir = Path("plots")
    output_dir.mkdir(exist_ok=True)

    # 1. GRAFICO VALORI OBIETTIVO
    fig, ax = plt.subplots(figsize=(12, 6))

    for method in methods:
        data = df[df["method"] == method].sort_values("x")

        ax.plot(
            data["x"],
            data["objective"],
            marker="o",
            label=method
        )

    ax.set_title("Objective values and lower bounds")
    ax.set_xlabel("Instances")
    ax.set_ylabel("Objective / Lower Bound")
    ax.set_xticks(instances["x"])
    ax.set_xticklabels(instances["label"], rotation=45, ha="right")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_dir / "objective.png", dpi=300)

    # 2. GRAFICO GAP PERCENTUALI
    fig, ax = plt.subplots(figsize=(12, 6))

    for method in methods:
        if method == "PLI":
            continue

        data = df[df["method"] == method].sort_values("x")

        ax.plot(
            data["x"],
            data["GAP_percent"],
            marker="o",
            label=method
        )

    ax.set_title("Gap percentage")
    ax.set_xlabel("Instances")
    ax.set_ylabel("Gap (%)")
    ax.set_xticks(instances["x"])
    ax.set_xticklabels(instances["label"], rotation=45, ha="right")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_dir / "gap.png", dpi=300)

    # 3. GRAFICO TEMPI DI ESECUZIONE
    fig, ax = plt.subplots(figsize=(12, 6))

    for method in methods:
        data = df[df["method"] == method].sort_values("x")

        ax.plot(
            data["x"],
            data["runtime"],
            marker="o",
            label=method
        )

    ax.set_title("Execution time")
    ax.set_xlabel("Instances")
    ax.set_ylabel("Time (seconds)")
    ax.set_xticks(instances["x"])
    ax.set_xticklabels(instances["label"], rotation=45, ha="right")
    ax.legend()
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_dir / "runtime.png", dpi=300)

    # 4. GRAFICO STATUS
    status_counts = pd.crosstab(
        df["method"],
        df["status"]
    ).reindex(methods, fill_value=0)

    fig, ax = plt.subplots(figsize=(10, 6))

    status_counts.plot(
        kind="bar",
        stacked=True,
        ax=ax
    )

    ax.set_title("Solver status distribution")
    ax.set_xlabel("Method")
    ax.set_ylabel("Number of instances")
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title="Status")
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_dir / "status.png", dpi=300)