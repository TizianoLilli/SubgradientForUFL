import argparse
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from compare import compare_instance, _to_csv, _to_plot


def _read_instance(file):
    # legge un'istanza e restituisce i dati necessari al solver
    with open(file) as fl:
        lines = [line.split() for line in fl]

    n_facilities = int(lines[0][0])
    n_clients = int(lines[0][1])

    facilities = list(range(1, n_facilities + 1))
    clients = list(range(1, n_clients + 1))

    opening_cost = {
        f: float(lines[f][1])
        for f in facilities
    }

    cost_start = n_facilities + 2
    cost_values = [
        float(value)
        for line in lines[cost_start:]
        for value in line
    ]

    service_cost = {
        (f, c): cost_values[(f - 1) * n_clients + (c - 1)]
        for f in facilities
        for c in clients
    }

    return {
        "n_facilities": n_facilities,
        "n_clients": n_clients,
        "facilities": facilities,
        "clients": clients,
        "opening_cost": opening_cost,
        "service_cost": service_cost,
    }


def _solve_instance(task):
    # worker eseguito in un processo separato
    instance_index, data, time_limit = task

    print(
        f"Avvio istanza {instance_index}: "
        f"{data['n_facilities']} facilities, {data['n_clients']} clienti"
    )

    result = compare_instance(
        n_clients=data["n_clients"],
        facilities=data["facilities"],
        clients=data["clients"],
        opening_cost=data["opening_cost"],
        service_cost=data["service_cost"],
        time_limit=time_limit,
    )

    return instance_index, result


def _positive_int(value):
    """Restituisce un intero positivo, altrimenti segnala l'errore."""
    try:
        value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("deve essere un intero") from error

    if value <= 0:
        raise argparse.ArgumentTypeError("deve essere maggiore di zero")

    return value


def main():
    parser = argparse.ArgumentParser(
        description="Esegue il confronto sulle istanze UFL in parallelo."
    )
    parser.add_argument(
        "time_limit",
        nargs="?",
        type=_positive_int,
        default=120,
        help="tempo massimo in secondi per ogni istanza (default: 120)",
    )
    parser.add_argument(
        "workers",
        nargs="?",
        type=_positive_int,
        default=2,
        help="numero di processi paralleli (default: 2)",
    )
    args = parser.parse_args()

    # accesso alla directory contenente le istanze del problema
    directory_data = Path("data2")
    files = sorted(fl for fl in directory_data.iterdir() if fl.is_file())
    tasks = [
        (instance_index, _read_instance(file), args.time_limit)
        for instance_index, file in enumerate(files, start=1)
    ]

    if not tasks:
        print("Nessuna istanza trovata.")
        return

    # Due processi sono un punto di partenza prudente; aumentare solo se il
    # computer dispone di core e memoria sufficienti.
    max_workers = min(args.workers, len(tasks))

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_solve_instance, tasks))

    # La scrittura avviene solo qui, evitando accessi concorrenti al CSV.
    for instance_index, result in sorted(results):
        print(f"--- CONFRONTO ISTANZA {instance_index} ---\n")
        _to_csv(result, instance_name=instance_index)

    _to_plot()

if __name__ == '__main__':
    main()
