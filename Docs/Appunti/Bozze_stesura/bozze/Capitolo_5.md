# Capitolo 5: Metodologia Sperimentale e Preparazione dei Dati

## 5.1. Introduzione alla Metodologia

La validazione empirica di un meccanismo di incentivazione richiede un ambiente di simulazione che sia al contempo controllabile e rappresentativo della realtà. Molti studi adottano modelli di mobilità sintetici come il *Random Waypoint*, che però falliscono nel catturare le correlazioni spazio-temporali tipiche del movimento umano in contesti urbani. Questa tesi segue invece un approccio *data-driven*, basato su tracce GPS reali.

Il capitolo descrive la metodologia completa utilizzata per trasformare dati grezzi di mobilità in scenari di simulazione realistici. In particolare, vengono affrontati quattro aspetti:

1. L'acquisizione e il processamento del dataset di mobilità urbana
2. La selezione della finestra temporale di analisi e la sua giustificazione
3. La discretizzazione dello spazio geografico continuo in un modello a griglia
4. La generazione sintetica delle popolazioni di task e utenti

## 5.2. Il Dataset CRAWDAD `roma/taxi`

L'analisi si fonda sul dataset pubblico **CRAWDAD `roma/taxi`**, che raccoglie le tracce GPS di una flotta di taxi operanti nel centro di Roma durante Febbraio 2014.[12]

### Caratteristiche del dataset

Il dataset copre un periodo di 30 giorni (dal 1 Febbraio al 2 Marzo 2014) e registra la mobilità di circa 320 tassisti unici, identificati tramite ID anonimizzati. La posizione GPS di ciascun veicolo viene campionata con una frequenza media di 7 secondi, generando un flusso continuo di osservazioni spazio-temporali.

I dati grezzi sono distribuiti in formato testuale compresso (`taxi_february.txt.gz`, circa 392 MB). Ogni riga del file rappresenta un singolo record GPS nel formato:

```
DRIVER_ID; TIMESTAMP; POSITION
```

Ad esempio:
```
123; 2014-02-01 08:15:32.456; POINT(12.4922 41.8902)
```

dove le coordinate geografiche sono codificate nel formato standard WKT (*Well-Known Text*), con **longitudine precedente alla latitudine** secondo la convenzione ISO 19125.

Questo dataset è stato scelto per la sua alta risoluzione temporale e per la copertura di un'area urbana densa e complessa, caratteristiche ideali per testare algoritmi di crowdsensing in scenari realistici. A differenza di dataset sintetici, le tracce catturano pattern di mobilità reali come le zone calde (Stazione Termini, Centro Storico) e le aree periferiche a bassa densità.

## 5.3. Selezione della Finestra Temporale

L'analisi si concentra su una singola giornata: il **1 Febbraio 2014** (sabato). Questa scelta è motivata dalla necessità di analizzare un giorno con **pattern di mobilità eterogenei**: il sabato presenta sia picchi di attività (ore centrali, zona shopping e turistica) che periodi di bassa domanda (mattina presto, sera), garantendo una distribuzione rappresentativa della domanda senza bias dovuti ai flussi pendolari tipici dei giorni feriali (es. Lunedì-Venerdì).

### Costi computazionali

Le procedure di verifica formale adottate in questo studio hanno un costo computazionale elevato. In particolare, i test Monte Carlo per la validazione della *truthfulness* richiedono migliaia di simulazioni controfattuali per ogni vincitore dell'asta. L'analisi di sensitività sui raggi di copertura aggiunge un ulteriore livello di complessità. Estendere questi calcoli all'intero mese avrebbe reso intrattabile la verifica puntuale delle proprietà economiche del meccanismo.

### Focus algoritmico

L'obiettivo della tesi è validare la robustezza del meccanismo IMCU e misurare il differenziale di performance tra scenari di razionalità perfetta e limitata. Questo tipo di analisi riguarda le proprietà intrinseche dell'algoritmo, non trend stagionali o variazioni di calendario. Le proprietà teoriche del meccanismo (veridicità, razionalità individuale, profittabilità) dipendono dalla sua logica interna, non dalla data specifica di esecuzione.

Un giorno rappresentativo è quindi sufficiente per dimostrare la validità delle garanzie teoriche. Il Sabato scelto presenta una densità di rilevamenti adeguata, con sia picchi di attività (ore centrali) che fasi di bassa domanda, garantendo significatività statistica senza introdurre bias stagionali.

## 5.4. Pipeline ETL (Extract, Transform, Load)

Data l'elevata dimensione del dataset grezzo, è stata sviluppata una pipeline ETL customizzata (implementata nel modulo `data_manager.py`) per ottimizzare le prestazioni delle simulazioni.

### Estrazione e pulizia dei dati

Il primo stadio della pipeline si occupa di leggere il flusso di dati grezzi e applicare filtri di qualità. Il file originale contiene milioni di record GPS, molti dei quali inutilizzabili a causa di errori di misurazione o anomalie del sistema di rilevamento.

**Parsing delle coordinate.** Le coordinate geografiche vengono estratte dal formato WKT tramite espressioni regolari ottimizzate. Ad esempio, il pattern regex `POINT\(([^ ]+) ([^ ]+)\)` identifica e cattura le coppie latitudine-longitudine.

**Filtraggio spaziale.** Tutti i punti GPS che ricadono al di fuori dell'area metropolitana di Roma vengono scartati. L'area valida è definita dalla bounding box:

$$
\text{Lat} \in [41.78, 42.04], \quad \text{Lon} \in [12.30, 12.72]
$$

Questo passaggio elimina artefatti GPS comuni (come coordinate nulle `POINT(0.0 0.0)`) e viaggi extra-urbani non rilevanti per l'analisi.

**Normalizzazione temporale.** I timestamp, spesso eterogenei nel formato originale, vengono convertiti in formato standard ISO 8601 e in *epoch milliseconds* per facilitare operazioni di ordinamento e filtraggi temporali.

### Partizionamento dei dati

L'accesso casuale al file grezzo da 392 MB sarebbe computazionalmente inefficiente. La pipeline riorganizza quindi i dati in una struttura gerarchica di file CSV partizionati per giorno e ora (es. `2014-02-01_08.csv`, `2014-02-01_09.csv`).

Questa strategia di *sharding* temporale permette al simulatore di caricare in memoria solo i dati pertinenti alla finestra di simulazione corrente, riducendo drasticamente l'occupazione di RAM e i tempi di I/O. Durante la fase di test, ad esempio, per simulare l'ora 8:00-9:00 viene caricato solo il file `2014-02-01_08.csv`, che tipicamente contiene poche migliaia di record invece di milioni.

## 5.5. Discretizzazione dello Spazio Geografico

Per trasformare le coordinate GPS continue in un dominio discreto computabile, l'area di interesse viene mappata su una griglia regolare. Questo passaggio è necessario per definire concetti come "task localizzato in una posizione" e "utente che copre un'area".

### Definizione del modello a griglia

**Definizione 5.1 (Griglia Spaziale)**  
L'area definita dalla bounding box viene suddivisa in celle quadrate di lato $d_{\text{cell}} = 500$ metri. La mappatura da coordinate geografiche $(\phi, \lambda)$ a indici di cella $(i_y, i_x)$ avviene tramite proiezione locale equirettangolare:

$$
i_y = \left\lfloor \frac{(\phi - \phi_{\min}) \cdot M_{\text{LAT}}}{d_{\text{cell}}} \right\rfloor, \quad i_x = \left\lfloor \frac{(\lambda - \lambda_{\min}) \cdot M_{\text{LON}}(\phi)}{d_{\text{cell}}} \right\rfloor
$$

dove:
- $M_{\text{LAT}} \approx 111{,}320$ m/grado è la costante di conversione latitudinale (valida a tutte le latitudini)
- $M_{\text{LON}}(\phi) = M_{\text{LAT}} \cdot \cos(\phi)$ è la conversione longitudinale, che dipende dalla latitudine per compensare la convergenza dei meridiani

![Figura 5.1: Distribuzione spaziale reale degli utenti (tassisti) sovrapposta alla mappa di Roma. I punti blu rappresentano le posizioni GPS estratte dal dataset, evidenziando la copertura delle arterie principali e del centro storico. Il riquadro rosso delimita l'area di simulazione.](./Immagini/figura_5_1_mappa_roma.jpg)

### Esempio pratico

Consideriamo un punto GPS registrato in Piazza Venezia: `POINT(12.4833 41.8960)` (longitudine 12.4833°, latitudine 41.8960°).

Applicando la formula con $\phi = 41.8960$, $\lambda = 12.4833$, $\phi_{\min} = 41.78$, $\lambda_{\min} = 12.30$ e $d_{\text{cell}} = 500$:

$$
i_y = \left\lfloor \frac{(41.8960 - 41.78) \cdot 111320}{500} \right\rfloor = \left\lfloor 25.83 \right\rfloor = 25
$$

$$
i_x = \left\lfloor \frac{(12.4833 - 12.30) \cdot 111320 \cdot \cos(41.8960°)}{500} \right\rfloor \approx \left\lfloor 27.18 \right\rfloor = 27
$$

Il punto viene quindi assegnato alla cella $(25, 27)$, che rappresenta un'area di $500 \times 500$ metri centrata approssimativamente in quella posizione.

## 5.6. Generazione delle Istanze di Simulazione

Per ogni finestra temporale di simulazione (tipicamente 1 ora), il sistema genera popolazioni di task e utenti derivate direttamente dalle osservazioni GPS reali.

### Generazione dei task

La domanda di sensing è modellata come funzione diretta della densità di presenza umana. Il processo si articola in tre fasi:

**1. Aggregazione spaziale.** Si calcola la densità di punti GPS per ogni cella della griglia nella finestra temporale. Ad esempio, se nell'ora 8:00-9:00 la cella $(25, 27)$ contiene 150 osservazioni GPS, la sua densità è $c_{25,27} = 150$.

**2. Istanziazione dei task.** Per ogni cella con densità $c > 0$ viene creato un task $\tau_j$ posizionato nel centroide geometrico della cella. Il numero totale di task generati corrisponde quindi al numero di celle "attive" in quella fascia oraria.

**3. Assegnazione del valore.** Il valore economico $\nu_j$ del task viene estratto da una distribuzione uniforme nell'intervallo $[1.8, 15.0]$ (valori in unità monetarie arbitrarie), come discusso nel Capitolo 2. Questo modello baseline assume che tutti i task abbiano importanza comparabile per la piattaforma. In scenari avanzati, il valore può essere modulato dalla densità $c$ secondo un modello logaritmico (*demand-log*).

### Generazione degli utenti

L'offerta di sensing è derivata dalla posizione effettiva dei tassisti nel momento della simulazione.

**1. Snapshot temporale.** Per ogni autista unico attivo nella finestra temporale, si estrae la sua ultima posizione GPS valida registrata. Questo approccio simula la disponibilità istantanea dell'agente ed evita duplicazioni (lo stesso autista non può essere in due posizioni contemporaneamente).

**2. Campionamento.** Se il numero di autisti supera un limite configurato ($N_{\max} = 316$, che rappresenta il numero di tassisti con id univoco), viene applicato un campionamento casuale uniforme; in alternativa, si può usare un campionamento stratificato per mantenere la distribuzione spaziale originale.

**3. Assegnazione dei costi.** Ad ogni utente viene assegnato un profilo di costo per chilometro $\kappa_i \in [0.45, 0.70]$ €/km, estratto da una distribuzione uniforme. Il costo totale per eseguire un task viene poi calcolato moltiplicando $\kappa_i$ per la distanza euclidea (con fattore di correzione urbana 1.30, come descritto nel Capitolo 2).

La Tabella 5.1 riassume i principali parametri di configurazione utilizzati per la generazione degli scenari nella Fase 1.

**Tabella 5.1: Parametri di configurazione della simulazione (Fase 1)**

| Parametro | Simbolo | Valore / Range | Descrizione |
| :--- | :---: | :--- | :--- |
| **_Parametri Spaziali_** | | | |
| Bounding Box (Lat) | $\phi$ | $[41.78, 42.04]$ | Copertura Latitudinale (Roma) |
| Bounding Box (Lon) | $\lambda$ | $[12.30, 12.72]$ | Copertura Longitudinale (Roma) |
| Dimensione Cella | $d_{\text{cell}}$ | $500$ m | Risoluzione della griglia |
| Raggio Baseline | $r$ | $2.5 $ km | Raggio di assegnazione baseline (Fase 1) |
| **_Parametri Economici_** | | | |
| Valore Task | $\nu_j$ | $U[1.8, 15.0]$ € | Distribuzione Uniforme |
| Costo Utente | $\kappa_i$ | $U[0.45, 0.70]$ €/km | Costo operativo |
| **_Parametri Popolazione_** | | | |
| Max Utenti | $N_{\max}$ | $316$ | Soglia campionamento orario |
| Strategia | $b_i$ | $b_i = c_i$ | Razionalità Perfetta (Truthful) |
| Fattore Urbano | $\eta_{\text{urban}}$ | $1.30$ | Correzione tortuosità strade |

### Realismo degli scenari

Questa metodologia garantisce che gli esperimenti non siano eseguiti su topologie astratte o casuali, ma riflettano la struttura reale della mobilità urbana romana. Le simulazioni preservano naturalmente le caratteristiche "a macchia di leopardo" tipiche delle città:

- **Zone calde** (es. Stazione Termini, Centro Storico): alta densità di task e utenti
- **Periferie sparse**: pochi task e utenti isolati
- **Eterogeneità spaziale**: alcune celle hanno decine di osservazioni, altre zero

Questo approccio data-driven migliora significativamente la validità esterna dei risultati rispetto a modelli sintetici, rendendo le conclusioni più rilevanti per deployment reali di sistemi MCS.

## 5.7. Assegnazione Task agli Utenti via Prossimità Geografica

Dopo la generazione delle popolazioni di task e utenti, è necessario definire quale sottoinsieme di task $\Gamma_i \subseteq \mathcal{T}$ ciascun utente $u_i$ è in grado e disposto a eseguire. Questo processo modella le preferenze e i vincoli geografici degli agenti mobili.

### Motivazione del modello di prossimità

Nel contesto taxi, un autista razionale preferisce task vicini alla propria posizione corrente, per minimizzare i costi di trasferimento (carburante, tempo) e massimizzare i guadagni orari. A differenza di scenari con agenti dedicati al crowdsensing, i tassisti hanno un obiettivo primario (trasporto passeggeri) e considerano il sensing come attività secondaria da svolgere opportunisticamente durante le attese o tra corse.

Si assume quindi che un utente consideri solo task entro un **raggio di servizio massimo** $r$ dalla sua posizione iniziale. Task oltre questo raggio comporterebbero costi di spostamento eccessivi rispetto ai potenziali guadagni offerti dal meccanismo d'asta.

### Definizione formale

**Definizione 5.2 (Task Assignment via Radius)**  
Dato un utente $u_i$ con posizione iniziale $\text{pos}_i = (\phi_i, \lambda_i)$ e un raggio massimo di servizio $r$ (espresso in metri), l'insieme di task candidati (*task bundle*) $\Gamma_i$ assegnato all'utente è definito come:

$$
\Gamma_i = \left\{ \tau_j \in \mathcal{T} \mid d_H(\text{pos}_i, \text{pos}_j) \leq r \right\}
$$

dove $d_H(\cdot, \cdot)$ è la distanza geodetica di Haversine (Definizione 3.5) e $\text{pos}_j$ è la posizione del task $\tau_j$.

In altre parole, l'utente $i$ può "vedere" e sottomettere offerte solo per i task che ricadono entro un cerchio di raggio $r$ centrato sulla sua posizione.

### Calibrazione del parametro radius

Il parametro $r$ introduce un trade-off multi-dimensionale che influenza direttamente le performance del sistema:

1. **Copertura task:** Un radius grande aumenta il numero di task accessibili da ciascun utente, incrementando il valore potenziale della piattaforma (più task coperti). Tuttavia, se $r$ è troppo elevato, utenti periferici possono selezionare task centrali con costi di spostamento proibitivi, riducendo l'efficienza complessiva.

2. **Competizione tra utenti:** Radius ampi causano forte sovrapposizione tra i bundle $\Gamma_i$ di utenti vicini, aumentando la competizione nell'asta e potenzialmente riducendo i pagamenti critici. Al contrario, radius ristretti creano "monopoli locali" con pagamenti elevati ma minor copertura.

3. **Efficienza operativa:** Un radius contenuto garantisce che gli utenti selezionino solo task realmente convenienti (basso rapporto costo/valore), riducendo sprechi. Tuttavia, aree con bassa densità di utenti possono rimanere scoperte.

Per esplorare questo trade-off, nella Fase 1 vengono testati tre valori di $r$:

**Tabella 5.2: Calibrazione del parametro radius e impatti previsti**

| **Radius $r$** | **Tempo Guida¹** | **Scenario**  | **Copertura Task** | **Competizione** | **Efficienza Utente** |
|:----------------:|:----------------:|:-------------:|:------------------:|:----------------:|:---------------------:|
| 1.5 km           | ~3 min           | Conservativo  | Bassa              | Bassa            | Alta                  |
| **2.5 km**       | **~5 min**       | **Bilanciato**| **Media**          | **Media**        | **Media**             |
| 4.0 km           | ~8 min           | Aggressivo    | Alta               | Alta             | Bassa                 |

¹ Tempo di guida stimato a velocità media urbana (30 km/h) per raggiungere il task più lontano nel raggio.

La configurazione **baseline** per la Fase 1 adotta $r = 2500$ metri, che rappresenta un compromesso ragionevole: consente una copertura sufficiente senza imporre costi di trasferimento eccessivi (circa 5 minuti di guida nel caso peggiore).

### Implementazione e filtering

L'assegnazione viene calcolata nella fase di inizializzazione della simulazione, prima dell'esecuzione del meccanismo IMCU. Per ogni utente:

1. Si calcola la distanza di Haversine tra $\text{pos}_i$ e ogni task $\tau_j \in \mathcal{T}$
2. Si selezionano solo i task con $d_H \leq r$
3. Si costruisce l'insieme $\Gamma_i$

**Filtering post-assignment:** Utenti con $\Gamma_i = \emptyset$ (nessun task nel raggio) vengono esclusi dalla partecipazione all'asta, poiché non possono contribuire utilità positiva alla piattaforma né ricevere pagamenti. Questo riduce il carico computazionale ed evita comportamenti degeneri (bid su insiemi vuoti).

### Nota metodologica

Il paper di riferimento di Yang et al. specifica che "each user selects a subset of tasks based on its preference and submits a bid", ma non dettagli il meccanismo di selezione dei task. Il modello di prossimità geografica qui adottato è una scelta implementativa ragionevole per il contesto taxi, coerente con l'assunzione di razionalità economica: un agente minimizza i costi di spostamento selezionando task vicini.[10]

In scenari alternativi (es. crowdsensing con agenti dedicati, non vincolati da un'attività primaria), si potrebbero adottare modelli di selezione diversi basati su preferenze tematiche, capacità sensoriali, o availability temporale. La flessibilità del framework IMCU permette di integrare tali estensioni senza modificare il meccanismo d'asta centrale.

Questa metodologia viene adottata sistematicamente in tutte le simulazioni di Fase 1, garantendo risultati su uno scenario urbano reale e riproducibile. Nel prossimo capitolo analizzeremo gli outcome sperimentali ottenuti con questi dati.

## Riferimenti Bibliografici

[1] N. D. Lane, E. Miluzzo, H. Lu, D. Peebles, T. Choudhury, and A. T. Campbell, "A survey of mobile phone sensing," *IEEE Communications Magazine*, vol. 48, no. 9, pp. 140–150, 2010.

[2] R. K. Ganti, F. Ye, and H. Lei, "Mobile crowdsensing: current state and future challenges," *IEEE Communications Magazine*, vol. 49, no. 11, pp. 32–39, 2011.

[3] A. Capponi, C. Fiandrino, B. Kantarci, L. Foschini, D. Kliazovich, and P. Bouvry, "A survey on mobile crowdsensing systems: Challenges, solutions, and opportunities," *IEEE Communications Surveys & Tutorials*, vol. 21, no. 3, pp. 2419–2465, 2019.

[4] J. White, C. Thompson, H. Turner, B. Dougherty, and D. C. Schmidt, "Waze: a community-based traffic and navigation app," in *Proceedings of the International Conference on Mobile Computing, Applications, and Services*, 2010.

[5] N. Maisonneuve, M. Stevens, M. E. Niessen, and L. Steels, "NoiseTube: Measuring and mapping noise pollution with mobile phones," in *Information Technologies in Environmental Engineering*, Springer, 2009, pp. 215–228.

[6] F. Restuccia, N. Ghosh, S. Bhattacharjee, S. K. Das, and T. Melodia, "Quality of information in mobile crowdsensing: Survey and research challenges," *ACM Transactions on Sensor Networks (TOSN)*, vol. 13, no. 4, pp. 1–43, 2017.

[7] D. Christin, A. Reinhardt, S. S. Kanhere, and M. Hollick, "A survey on privacy in mobile participatory sensing applications," *Journal of Systems and Software*, vol. 84, no. 11, pp. 1928–1946, 2011.

[8] L. G. Jaimes, I. J. Vergara-Laurens, and A. Raij, "A survey of incentive techniques for mobile crowd sensing," *IEEE Internet of Things Journal*, vol. 2, no. 5, pp. 370–380, 2015.

[9] X. Zhang, Z. Yang, W. Sun, Y. Liu, S. Tang, K. Xing, and X. Mao, "Incentives for mobile crowd sensing: A survey," *IEEE Communications Surveys & Tutorials*, vol. 18, no. 1, pp. 54–67, 2015.

[10] D. Yang, G. Xue, X. Fang, and J. Tang, "Incentive mechanisms for crowdsensing: Crowdsourcing with smartphones," *IEEE/ACM Transactions on Networking*, vol. 24, no. 3, pp. 1732–1744, 2015.

[11] H. A. Simon, "A behavioral model of rational choice," *The Quarterly Journal of Economics*, vol. 69, no. 1, pp. 99–118, 1955.

[12] Lorenzo Bracciale, Marco Bonola, Pierpaolo Loreti, Giuseppe Bianchi, Raul Amici, Antonello Rabuffi, "CRAWDAD roma/taxi", IEEE Dataport, December 2, 2022, doi:10.15783/C7QC7M

[13] M. Barthelemy, "Spatial networks," *Physics Reports*, vol. 499, no. 1-3, pp. 1–101, 2011.

[14] V. Krishna, *Auction Theory*, 2nd ed. Academic Press, 2009.

[15] R. B. Myerson, "Optimal Auction Design," *Mathematics of Operations Research*, vol. 6, no. 1, pp. 58–73, 1981.

[16] G. L. Nemhauser, L. A. Wolsey, and M. L. Fisher, "An analysis of approximations for maximizing submodular set functions—I," *Mathematical Programming*, vol. 14, no. 1, pp. 265–294, 1978.