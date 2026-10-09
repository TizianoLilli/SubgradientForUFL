import gurobipy as gp

def main():

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

    # creazione del modello
    model = gp.Model()

    # creazione delle variabili
    x = model.addVars(facilities, vtype=gp.GRB.BINARY, name="x")
    y = model.addVars(facilities, clients, vtype=gp.GRB.BINARY, name="y")

    # creazione dei vincoli
    service_constraints = model.addConstrs((y.sum('*', c) == 1 for c in clients), name="service")
    opening_constraints = model.addConstrs((y[f, c] <= x[f] for c in clients for f in facilities), name="opening")

    # creazione della funzione obiettivo
    of = sum(x[f] * opening_cost[f] for f in facilities)
    of += sum(y[f, c] * service_cost[(f, c)] for c in clients for f in facilities)
    model.setObjective(of, gp.GRB.MINIMIZE)

    # scrittura della formulazione su un file
    model.write("ufl.lp")

    # lettura del numero di variabili e vincoli
    num_vars = model.numVars
    num_constrs = model.numConstrs
    print(f"Problem has {num_vars} variables and {num_constrs} constraintsi\n")

    # configurazione di alcuni parametri del solver.
    model.params.TimeLimit = 120
    model.params.MIPGap = 0.001

    # risoluzione del problema
    model.optimize()

    def print_solution(model, x, y):
        # lettura del costo della soluzione ottima
        print("Solution cost  = ", model.objVal)

        # stampa delle facility aperte
        print("Open facilities:")
        for f in facilities:
            # accesso al valore contenuto in x[f]
            if x[f].x > 0.5:
                n_clients = 0
                for c in clients:
                    if y[f, c].x > 0.5:
                        n_clients += 1
                print(f'\t - {f}, with {n_clients} clients')

    # accesso allo status (motivo dell'arresto dell'algoritmo)
    status = model.Status
    if status == gp.GRB.OPTIMAL or status == gp.GRB.TIME_LIMIT:

        if status == gp.GRB.TIME_LIMIT:
            print('Time limit exceeded!')

        # recupero del tempo impiegato da Gurobi per risolvere il modello
        runtime = model.Runtime
        # numero di nodi B&B esplorati
        BBnodes = model.NodeCount

        # visualizzo massimo 3 cifre decimali
        print('Running times:', round(runtime, 3))
        print('Nodes:', int(BBnodes))
        print_solution(model, x, y)
    else:
        print('Status code:', status)

if __name__ == '__main__':
    main()


