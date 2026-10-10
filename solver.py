import gurobipy as gp

class Solver:
    def __init__(self, facilities, clients, opening_cost, service_cost):

        # Dati del problema
        self.facilities = facilities
        self.clients = clients
        self.opening_cost = opening_cost
        self.service_cost = service_cost

        # Modello e variabili
        self.model = None
        self.x = None
        self.y = None

    def setup(self):
        # creazione del modello
        self.model = gp.Model()

    def solve_pli(self):
        self.setup()
        # creazione delle variabili
        self.x = self.model.addVars(self.facilities, vtype=gp.GRB.BINARY, name="x")
        self.y = self.model.addVars(self.facilities, self.clients, vtype=gp.GRB.BINARY, name="y")
        self.solve()

    def solve_pl(self):

        self.setup()
        # creazione delle variabili
        self.x = self.model.addVars(self.facilities, lb = 0, ub = 1, vtype=gp.GRB.CONTINUOUS, name="x")
        self.y = self.model.addVars(self.facilities, self.clients, lb = 0, ub = 1, vtype=gp.GRB.CONTINUOUS, name="y")
        self.solve()

    def solve(self):

        # creazione dei vincoli
        self.model.addConstrs((self.y.sum('*', c) == 1 for c in self.clients), name="service")
        self.model.addConstrs((self.y[f, c] <= self.x[f] for c in self.clients for f in self.facilities), name="opening")

        # creazione della funzione obiettivo
        of = gp.quicksum(self.x[f] * self.opening_cost[f] for f in self.facilities)
        of += gp.quicksum(self.y[f, c] * self.service_cost[(f, c)] for c in self.clients for f in self.facilities)
        self.model.setObjective(of, gp.GRB.MINIMIZE)

        # scrittura della formulazione su un file
        self.model.write("ufl.lp")

        # lettura del numero di variabili e vincoli
        num_vars = self.model.numVars
        num_constrs = self.model.numConstrs
        print(f"Problem has {num_vars} variables and {num_constrs} constraints\n")

        # configurazione di alcuni parametri del solver.
        self.model.params.TimeLimit = 120
        self.model.params.MIPGap = 0.001

        # risoluzione del problema
        self.model.optimize()

        # accesso allo status (motivo dell'arresto dell'algoritmo)
        status = self.model.Status

        if status == gp.GRB.TIME_LIMIT:
            print("Time limit exceeded!")

        # se sono state trovate soluzioni ammissibili
        if self.model.SolCount > 0:
            # lettura del costo della soluzione ottima
            print("Solution cost:", self.model.ObjVal)
            print("Running time:", round(self.model.Runtime, 3))

            if self.model.IsMIP:
                print("Nodes:", int(self.model.NodeCount))

            self.print_solution()
        else:
            print("No feasible solution available.")
            print("Status code:", status)

    def print_solution(self):

        # stampa delle facility aperte
        print("Open facilities:")
        for f in self.facilities:
            # print(self.x[f].x)
            # accesso al valore contenuto in x[f]
            if self.x[f].x > 0.5:
                n_clients = 0
                for c in self.clients:
                    # print(self.y[f, c].x)
                    if self.y[f, c].x > 0.5:
                        n_clients += 1
                print(f'\t - {f}, with {n_clients} clients')