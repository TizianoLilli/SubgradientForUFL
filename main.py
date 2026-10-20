import sys
from compare import compare_instance, save_summaries_csv


def main():

    # se l'utente non specifica il tempo max di run per il programma, questo si arresta dopo 120 sec
    if len(sys.argv) > 1:
        time_limit = int(sys.argv[1])
    else:
        time_limit = 120

    # costruzione delle strutture dati che contengono i dati del problema
    # *facilities* è una lista di lunghezza m
    # *clients* è una lista di lunghezza n
    # *opening_cost* è un dizionario indicizzato su facilities
    # *service_cost* è un dizionario indicizzato su clients e facilities

    # vedi la struttura dei data file contenenti le istanze in data/Readme.txt
    with open('data/cap61') as file:
        lines = [line.split() for line in file]

    # numero di facility location potenziali e clienti
    n_facilities = int(lines[0][0])
    n_clients = int(lines[0][1])

    facilities = list(range(1, n_facilities + 1))
    clients = list(range(1, n_clients + 1))

    # costi di setup
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

    print('Facilities:', len(facilities))
    print('Clients:', len(clients))
    print()

    result = compare_instance(
        n_clients=n_clients,
        facilities=facilities,
        clients=clients,
        opening_cost=opening_cost,
        service_cost=service_cost,
        time_limit=time_limit
    )

    target = {"n_clients", "PLI_gap_solver", "RC_time", "LR_demand_iter", "LR_linking_iter"}

    print("\n--- CONFRONTO ---")
    for name, value in result["summary"].items():
        print(f"{name}: {value}")
        if name in target:
            print()

    print("\nMiglior LB rilassamento domanda:", result["lr_demand"]["best_lb"])

if __name__ == '__main__':
    main()


