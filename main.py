import sys
from pathlib import Path

from compare import compare_instance, _to_csv


def main():

    # se l'utente non specifica il tempo max di run per il programma, questo si arresta dopo 120 sec
    if len(sys.argv) > 1:
        time_limit = int(sys.argv[1])
    else:
        time_limit = 120

    # accesso alla directory contenente le istanze del problema
    directory_data = Path("data")
    files = [fl for fl in directory_data.iterdir() if fl.is_file()]

    instance_index = 1

    for file in files:
        # vedi la struttura dei data file contenenti le istanze in data/Readme.txt
        with open(file) as fl:
            lines = [line.split() for line in fl]

        # costruzione delle strutture dati che contengono i dati del problema
        # *facilities* è una lista di lunghezza m
        # *clients* è una lista di lunghezza n
        # *opening_cost* è un dizionario indicizzato su facilities
        # *service_cost* è un dizionario indicizzato su clients e facilities

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

        print("--- CONFRONTO ---\n")
        _to_csv(result, instance_name = instance_index)

        instance_index += 1

if __name__ == '__main__':
    main()


