# SubgradientForUFL

Programma Python per lo studio del problema di localizzazione non capacitato (UFL, *Uncapacitated Facility Location*) tramite il confronto tra una formulazione intera, il suo rilassamento continuo e due rilassamenti lagrangiani risolti con metodo del subgradiente.

## Funzionalità

Per ogni istanza presente nella directory `data/`, il programma:

1. costruisce e risolve la formulazione di programmazione lineare intera (PLI);
2. costruisce e risolve il rilassamento continuo (RC);
3. rilassa i vincoli di domanda e calcola un lower bound lagrangiano (`LR_demand`);
4. rilassa i vincoli di coerenza apertura-assegnazione e calcola un lower bound lagrangiano (`LR_consistency`);
5. confronta valori obiettivo/lower bound, gap percentuali, tempi di esecuzione e stato di terminazione;
6. salva i risultati in `subgradient_results.csv`;
7. genera i grafici in `plots/`:
   - `objective.png`: valori obiettivo/lower bound medi;
   - `gap.png`: gap percentuali medi;
   - `runtime.png`: tempi medi di esecuzione;
   - `status.png`: distribuzione degli stati di terminazione.

Le istanze vengono elaborate in parallelo tramite processi separati. Ogni modello Gurobi usa un solo thread, così il numero di processi può essere controllato con l'argomento `workers`.

## Requisiti

- Python 3;
- una licenza Gurobi valida e configurata. È necessaria anche per l'uso di `gurobipy`;
- i pacchetti Python:
  - `gurobipy`;
  - `numpy`;
  - `pandas`;
  - `matplotlib`.

## Installazione

Dalla directory principale del progetto, crea un ambiente virtuale e installa le dipendenze:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install gurobipy numpy pandas matplotlib
```

Su Windows, per attivare l'ambiente virtuale usa invece:

```powershell
.venv\Scripts\Activate.ps1
```

Se Gurobi non è ancora configurato, installare `gurobipy` non è sufficiente: occorre anche configurare la licenza secondo il tipo di licenza disponibile (accademica, commerciale o trial). Il programma non contiene un solver alternativo a Gurobi.

## Esecuzione

Avvia il programma dalla root del repository:

```bash
python main.py
```

Il comando usa questi valori predefiniti:

- `time_limit = 300`: tempo massimo, in secondi, per ciascun metodo su ciascuna istanza;
- `workers = 2`: numero massimo di processi paralleli.

Gli argomenti sono posizionali e possono essere specificati così:

```bash
python main.py [time_limit] [workers]
```

Esempi:

```bash
# 60 secondi per istanza, 4 processi paralleli
python main.py 60 4

# 10 minuti per istanza, 1 processo alla volta
python main.py 600 1
```

Entrambi gli argomenti devono essere interi strettamente positivi. Per visualizzare l'help:

```bash
python main.py --help
```

Il programma cerca automaticamente i file nella directory `data/`; non è previsto un argomento CLI per selezionare una directory o una singola istanza. Se `data/` è vuota, viene mostrato un messaggio e l'esecuzione termina.

## Formato delle istanze

Ogni file in `data/` deve avere il formato seguente:

```text
n_facilities n_clients
capacity_1 fixed_cost_1 
capacity_2 fixed_cost_2 
...
capacity_n fixed_cost_n 
demand_1 demand_2 ... demand_n_clients
cost_1_1 cost_1_2 ... cost_1_n_clients
cost_2_1 cost_2_2 ... cost_2_n_clients
...
cost_n_facilities_1 ... cost_n_facilities_n_clients
```

Il programma usa il secondo valore di ogni riga come costo di apertura della facility; il primo valore viene letto ma non utilizzato, perché il problema implementato è non capacitated. Anche la domanda dei singoli clienti viene ignorata. Dopo le righe delle facility devono comparire `n_facilities x n_clients` costi di servizio, letti in ordine facility-cliente.

## Output e riesecuzioni

`subgradient_results.csv` viene aggiornato in modalità append: se si rilancia il programma, i nuovi risultati vengono aggiunti a quelli precedenti. I grafici vengono invece rigenerati e sovrascritti usando tutti i dati presenti nel CSV.

Per iniziare una nuova raccolta di risultati, elimina il CSV precedente prima dell'esecuzione:

```bash
rm -f subgradient_results.csv
python main.py
```

La directory `plots/` viene creata automaticamente se non esiste.

## Interpretazione dei metodi

- `PLI`: formulazione intera del problema UFL; fornisce il valore obiettivo della soluzione ammissibile trovata da Gurobi.
- `RC`: rilassamento continuo, nel quale le variabili di apertura e assegnazione sono comprese tra 0 e 1.
- `LR_demand`: rilassamento lagrangiano dei vincoli che impongono che ogni cliente sia assegnato una volta.
- `LR_consistency`: rilassamento lagrangiano dei vincoli che collegano l'apertura di una facility alle assegnazioni.

## Struttura principale

```text
main.py                  ingresso CLI e parallelizzazione
solver.py                modelli Gurobi e metodo del subgradiente
compare.py               confronto, CSV e grafici
data/                    istanze utilizzate dall'esecuzione
plots/                   grafici generati
subgradient_results.csv  risultati generati
analyze_gap.py           riassunto dati del csv
```
