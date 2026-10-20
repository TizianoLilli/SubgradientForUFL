import gurobipy as gp
import time

class Solver:
    def __init__(self, n_clients, facilities, clients, opening_cost, service_cost):

        # Dati del problema
        self.n_clients = n_clients
        self.facilities = facilities
        self.clients = clients
        self.opening_cost = opening_cost
        self.service_cost = service_cost

    def _build_model(self, time_limit):
        # creazione del modello UFL; formulazione debole
        model = gp.Model()
        model.Params.OutputFlag = 0
        model.Params.TimeLimit = time_limit

        return model

    @staticmethod
    def _model_result(model, elapsed):
        result = {
            "status": int(model.Status),
            "runtime": elapsed,
            "objective": None,
            "bound": None,
            "gap_solver": None,
        }

        if model.SolCount > 0:
            result["objective"] = float(model.ObjVal)

            if model.IsMIP:
                try:
                    result["gap_solver"] = float(model.MIPGap)
                except (gp.GurobiError, AttributeError):
                    pass

        return result

    def solve_pli(self, time_limit):
        start = time.perf_counter()
        model = self._build_model(time_limit)

        # creazione delle variabili
        x = model.addVars(self.facilities, vtype=gp.GRB.BINARY, name="x")
        y = model.addVars(self.facilities, self.clients, vtype=gp.GRB.BINARY, name="y")
        return self._solve(model, x, y, start)

    def solve_rc(self, time_limit):
        start = time.perf_counter()
        model = self._build_model(time_limit)

        # creazione delle variabili
        x = model.addVars(self.facilities, lb = 0, ub = 1, vtype=gp.GRB.CONTINUOUS, name="x")
        y = model.addVars(self.facilities, self.clients, lb = 0, ub = 1, vtype=gp.GRB.CONTINUOUS, name="y")
        return self._solve(model, x, y, start)

    def _solve(self, model, x, y, start):
        # creazione dei vincoli
        model.addConstrs((y.sum('*', c) == 1 for c in self.clients), name="service")
        model.addConstrs((y.sum(f, '*') <= self.n_clients * x[f] for f in self.facilities), name="opening")

        # creazione della funzione obiettivo
        of = gp.quicksum(x[f] * self.opening_cost[f] for f in self.facilities)
        of += gp.quicksum(y[f, c] * self.service_cost[(f, c)] for c in self.clients for f in self.facilities)
        model.setObjective(of, gp.GRB.MINIMIZE)

        # lettura del numero di variabili e vincoli
        num_vars = model.numVars
        num_constrs = model.numConstrs
        print(f"Problem has {num_vars} variables and {num_constrs} constraints\n")

        # risoluzione del problema
        model.optimize()

        result = self._model_result(
            model, time.perf_counter() - start
        )

        if model.SolCount > 0:
            result["open_facilities"] = [
                i for i in self.facilities if x[i].X > 0.5
            ]
        else:
            result["open_facilities"] = None

        # rilascio delle risorse per prevenire memory leak
        model.dispose()

        return result

    @staticmethod
    def _step(q, norm2, upper_bound, k, alpha0):
        # utilizzo uno stepsize di Polyak se è disponibile un upper bound
        if norm2 <= 1e-12:
            return 0.0

        if upper_bound is not None and upper_bound > q:
            return (upper_bound - q) / norm2

        return alpha0 / (k + 1)

    def lagrangian_opening(self, upper_bound=None, time_limit=300, alpha0=1.0, tol=1e-7):
        # rilassamento dei vincoli di coerenza: mu è maggiore o uguale di 0
        start = time.perf_counter()

        # inizializzazione di un dizionario con |n_facilities| elementi con valore 0.0
        mu = {f: 0.0 for f in self.facilities}
        best_lb = float("-inf")
        best_iter = 0
        stop_reason = None
        trace = []

        k = 0
        elapsed = 0

        while elapsed < time_limit:
            x_hat = {
                # la tolleranza tol evita di trattare piccoli valori numerici negativi come se fossero significativi
                f: int(self.opening_cost[f] - self.n_clients * mu[f] < -tol)
                for f in self.facilities
            }

            assigned = {f: 0 for f in self.facilities}

            # per ogni client si cerca la facility con costo di allocazione minore
            for c in self.clients:
                f_best = min(
                    self.facilities,
                    # tra tutte le facility si cerca quella che minimizza la seguente somma
                    key=lambda f: self.service_cost[f, c] + mu[f]
                )
                # viene incrementato il numero di client che attingono a una specifica facility
                assigned[f_best] += 1

            q = sum(
                min(0.0, self.opening_cost[f] - self.n_clients * mu[f])
                for f in self.facilities
            )
            q += sum(
                min(self.service_cost[f, c] + mu[f] for f in self.facilities)
                for c in self.clients
            )

            # memorizzazione del miglior bound
            if q > best_lb:
                best_lb = q
                best_iter = k + 1

            # calcolo del subgradiente
            subgrad = {
                f: assigned[f] - self.n_clients * x_hat[f]
                for f in self.facilities
            }
            # ricavo della norma al quadrato per calcolare alpha
            norm2 = sum(v * v for v in subgrad.values())

            trace.append({
                "iteration": k + 1,
                "dual_value": q,
                "best_lb": best_lb,
                "subgradient_norm": norm2 ** 0.5,
            })

            # corrisponde a vedere se norm2 == 0, ovvero non c'è una direzione d'aggiornamento
            if norm2 <= tol * tol:
                stop_reason = "zero_subgradient"
                break

            alpha = self._step(
                q, norm2, upper_bound, k, alpha0
            )

            # passo piccolo indica aggiornamenti trascurabili
            if alpha <= tol:
                stop_reason = "small_step"
                break

            for f in self.facilities:
                mu[f] = max(0.0, mu[f] + alpha * subgrad[f])

            k = k + 1
            elapsed = time.perf_counter() - start

            if elapsed >= time_limit:
                stop_reason = "time_limit"

        return {
            "method": "LR_opening",
            "best_lb": best_lb,
            "best_iteration": best_iter,
            "iterations": len(trace),
            "runtime": time.perf_counter() - start,
            "multipliers": mu,
            "trace": trace,
            "stop_reason": stop_reason,
        }

    def lagrangian_service(self, upper_bound=None, time_limit=300, alpha0=1.0, tol=1e-7):
        # rilassamento dei vincoli di domanda; lambda è libero
        start = time.perf_counter()

        lam = {j: 0.0 for j in self.clients}
        best_lb = float("-inf")
        best_iter = 0
        stop_reason = None
        trace = []

        k = 0
        elapsed = 0

        while elapsed < time_limit:
            reduced = {
                (f, c): self.service_cost[f, c] - lam[c]
                for f in self.facilities for c in self.clients
            }

            x_hat = {}
            y_hat = {}

            for f in self.facilities:
                value = self.opening_cost[f] + sum(
                    min(0.0, reduced[f, c]) for c in self.clients
                )

                x_hat[f] = int(value < -tol)

                for c in self.clients:
                    # vincolo: y == 1 solo se x == 1 e reduced è negativo
                    y_hat[f, c] = int(
                        x_hat[f] == 1 and reduced[f, c] < -tol
                    )

            q = sum(lam.values())
            q += sum(
                min(
                    0.0,
                    self.opening_cost[f] + sum(
                        min(0.0, reduced[f, c])
                        for c in self.clients
                    )
                )
                for f in self.facilities
            )

            if q > best_lb:
                best_lb = q
                best_iter = k + 1

            # calcolo del subgradiente
            subgrad = {
                c: 1 - sum(y_hat[f, c] for f in self.facilities)
                for c in self.clients
            }
            # ricavo della norma al quadrato per calcolare alpha
            norm2 = sum(v * v for v in subgrad.values())

            trace.append({
                "iteration": k + 1,
                "dual_value": q,
                "best_lb": best_lb,
                "subgradient_norm": norm2 ** 0.5,
            })

            # corrisponde a vedere se norm2 == 0, ovvero non c'è una direzione d'aggiornamento
            if norm2 <= tol * tol:
                stop_reason = "zero_subgradient"
                break

            alpha = self._step(
                q, norm2, upper_bound, k, alpha0
            )

            # passo piccolo indica aggiornamenti trascurabili
            if alpha <= tol:
                stop_reason = "small_step"
                break

            for c in self.clients:
                # non si fa il max tra questo valore e 0 perché lam è una variabile libera
                lam[c] += alpha * subgrad[c]

            k = k + 1
            elapsed = time.perf_counter() - start

            if elapsed >= time_limit:
                stop_reason = "time_limit"

        return {
            "method": "LR_demand",
            "best_lb": best_lb,
            "best_iteration": best_iter,
            "iterations": len(trace),
            "runtime": time.perf_counter() - start,
            "multipliers": lam,
            "trace": trace,
            "stop_reason": stop_reason,
        }