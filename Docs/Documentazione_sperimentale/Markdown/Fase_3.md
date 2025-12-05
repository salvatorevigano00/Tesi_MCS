# Capitolo 16: Il Modello Adattivo GAP: Teoria dell'Apprendimento e della Reputazione

## 16.1. Oltre i sistemi "Stateless": La necessità della memoria storica

L'indagine condotta nei capitoli precedenti ha portato alla luce un limite strutturale intrinseco e non trascurabile nei meccanismi di incentivazione classici per il Mobile Crowdsensing (MCS). I modelli statici, che trovano la loro massima espressione nella formulazione originale dell'IMCU [1], poggiano su un'ipotesi di lavoro teorica che difficilmente trova riscontro nella complessa realtà operativa: essi assumono un ambiente collaborativo ideale, asettico, in cui ogni interazione tra la piattaforma e l'utente si configura come un evento discreto e indipendente — un *one-shot game* — e dove l'identità o la storia pregressa dei partecipanti non esercitano alcun peso sulla strategia di allocazione ottimale.

Tuttavia, le evidenze empiriche emerse durante le simulazioni della Fase 2 raccontano una storia ben diversa e più allarmante. In scenari reali, inevitabilmente dominati dalla **razionalità limitata** degli agenti e dal rischio concreto di **azzardo morale** [8], continuare a trattare le aste come eventi isolati diviene una strategia economicamente insostenibile. In un sistema *stateless*, privo cioè di una memoria storica che traczi l'evoluzione comportamentale, manca la leva fondamentale per sanare l'asimmetria informativa *ex-post*: se un agente opportunista decide di defezionare, incassando il premio senza erogare il servizio pattuito, non subisce alcuna ripercussione nelle interazioni future. Si cristallizza in tal modo un equilibrio di Nash inefficiente, in cui la defezione non è più un'anomalia, ma diviene la scelta razionale dominante per gli agenti meno onesti, erodendo la marginalità della piattaforma con perdite di valore che le nostre analisi hanno stimato poter superare il 20%.

Per salvaguardare la resilienza economica del servizio e garantirne la sopravvivenza a lungo termine, è dunque imperativo un radicale cambio di paradigma, transitando verso un modello dinamico e *stateful*. In questo capitolo viene formalizzato il modello **GAP (Game-theoretic Adaptive Policy)**. L'obiettivo di tale framework è ridefinire il problema dell'allocazione dei task non più come una sequenza di aste indipendenti, bensì come un **gioco ripetuto a informazione incompleta** [22], dove le azioni passate determinano in modo causale le opportunità future.

Il funzionamento del modello GAP amplia e potenzia l'asta VCG classica operando su tre direttrici sinergiche e interdipendenti: l'**Inferenza Bayesiana della Razionalità**, strumento statistico necessario per stimare la distribuzione di probabilità della variabile nascosta $\rho_i$ (razionalità dell'agente); l'introduzione di una **Reputazione Multi-Dimensionale (MDR)**, un indice sintetico $R_i$ che funge da "memoria del sistema" aggregando lo storico delle performance in un unico scalare; e infine una strategia di **Selezione Meritocratica (Virtual Bidding)**, che internalizza il rischio penalizzando le offerte degli agenti inaffidabili tramite una trasformazione non lineare dei costi, ostacolandone l'accesso ai task critici e proteggendo così il valore della piattaforma.

## 16.2. Apprendimento Bayesiano della Razionalità

Nel contesto del Mobile Crowdsensing, il comportamento di un agente non è casuale, ma è governato da una variabile latente $\rho_i \in [\rho_{\min}, 1]$, che possiamo definire come il suo "livello di razionalità operativa". Tale parametro sintetizza la propensione intrinseca dell'agente a onorare i contratti stipulati, resistendo alle tentazioni opportunistiche del *free-riding*. Poiché $\rho_i$ rimane, per definizione, un'informazione privata dell'utente (inaccessibile all'osservazione diretta), la piattaforma si trova costretta ad operare in condizioni di strutturale incertezza.

Per gestire tale incertezza in modo rigoroso, il modello ricorre all'**inferenza statistica Bayesiana**. Considerando una sequenza temporale discreta $t = 1, 2, \dots, T$, ogni qualvolta all'utente $i$ viene assegnato un task al tempo $t$, la piattaforma registra un esito binario $y_{i,t}$, distribuito come segue:

$$
y_{i,t} \sim \text{Bernoulli}(\theta(\rho_i))
$$

Nello specifico, $y_{i,t}=1$ segnala la cooperazione dell'utente (task eseguito), mentre $y_{i,t}=0$ indica una defezione, con una probabilità di successo $\theta(\rho_i)$ che cresce funzionalmente e monotonicamente alla razionalità dell'utente stesso.

### 16.2.1. La Distribuzione di Credenza (Belief Distribution)
Non disponendo del valore puntuale di $\rho_i$, la piattaforma lavora su una densità di probabilità $f_t(\rho)$ che ne riflette la "convinzione" epistemica corrente. Per garantire efficienza computazionale nel ricalcolo continuo e trattabilità analitica, si modella tale credenza attraverso una **Distribuzione Beta**. Questa scelta non è arbitraria: la Beta è il coniugato naturale della verosimiglianza di Bernoulli [3], permettendo aggiornamenti algebrici semplici:

$$
\rho_i \mid \mathcal{H}_{i,t} \sim \text{Beta}(\alpha_{i,t}, \beta_{i,t})
$$

La variabile $\mathcal{H}_{i,t} = \{y_{i,1}, \dots, y_{i,t}\}$ rappresenta lo storico completo delle osservazioni fino all'istante $t$, mentre i iper-parametri $\alpha_{i,t}$ e $\beta_{i,t}$ assumono un significato fisico estremamente intuitivo, conteggiando rispettivamente i "successi" e i "fallimenti" virtuali accumulati dall'agente nel corso della sua storia.

Un aspetto cruciale nella progettazione del sistema è la gestione del cosiddetto **"Cold Start"**. Al tempo $t=0$, in assenza di dati pregressi, come deve comportarsi il sistema? Il modello GAP evita l'uso di un *prior* neutro (come la distribuzione uniforme, che implicherebbe totale ignoranza) in favore di un *prior* informativo calibrato sulla popolazione attesa. Fissando $\alpha_{i,0} = 6.5$ e $\beta_{i,0} = 3.5$, il sistema imposta un valore atteso iniziale $\mathbb{E}[\rho]_0 = 0.65$. Questa impostazione riflette un approccio filosofico di "cautela ottimistica": si presume che l'utente medio sia ragionevolmente affidabile, evitando pregiudizi negativi ingiustificati, ma mantenendo tuttavia un significativo margine di incertezza (varianza) in attesa di riscontri empirici fattuali.

### 16.2.2. La Dinamica di Aggiornamento Ricorsivo
Il processo di apprendimento è intrinsecamente ricorsivo e continuo: la distribuzione a posteriori calcolata al tempo $t$ diviene automaticamente il *prior* per il tempo $t+1$. Le regole di aggiornamento seguono una logica lineare additiva:

$$
\alpha_{i, t+1} = \alpha_{i, t} + y_{i,t} \cdot W_{\text{obs}}
$$
$$
\beta_{i, t+1} = \beta_{i, t} + (1 - y_{i,t}) \cdot W_{\text{obs}}
$$

Impostando il fattore di peso dell'osservazione $W_{\text{obs}}$ a 1.0, il meccanismo assicura due proprietà teoriche fondamentali. In primo luogo, la **convergenza asintotica**: per la Legge dei Grandi Numeri, al crescere del numero di interazioni $N$, la stima della piattaforma approssima con precisione arbitraria il valore reale $\rho_i$. In secondo luogo, un **adattamento dinamico**: il sistema non "smette" mai di imparare. Se un utente storicamente affidabile inizia improvvisamente a defezionare, il parametro $\beta$ aumenterà progressivamente, traslando la massa di probabilità verso valori di razionalità inferiori e segnalando il degrado comportamentale.

Tuttavia, per le necessità operative immediate — come decidere se ammettere un utente a un'asta — la distribuzione di probabilità deve essere sintetizzata in uno scalare. Definiamo quindi la **Stima Operativa ($\hat{\rho}_{i,t}$)**, calcolata come valore atteso della distribuzione:

$$
\hat{\rho}_{i,t} = \mathbb{E}[\rho_i \mid \mathcal{H}_{i,t}] = \frac{\alpha_{i,t}}{\alpha_{i,t} + \beta_{i,t}}
$$

Tale valore rappresenta, di fatto, la miglior previsione ("best guess") che la piattaforma possa formulare sulla razionalità dell'agente in quel preciso istante, minimizzando l'errore quadratico medio atteso.

## 16.3. Il Sistema di Reputazione Multi-Dimensionale (MDR)

Se l'inferenza Bayesiana ha lo scopo di stimare la natura intrinseca dell'utente (*chi è*), la gestione efficace del rischio operativo richiede anche una valutazione puntuale delle azioni recenti (*cosa ha fatto*). A tal fine, il modello GAP integra il sistema di **Reputazione Multi-Dimensionale (MDR)**, sintetizzando le performance osservate in un indice di affidabilità normalizzato $R_i \in [0, 1]$.

### 16.3.1. Calcolo dello Score di Performance
Superando la limitante dicotomia binaria onesto/disonesto, l'MDR valuta la qualità del contributo su più dimensioni simultaneamente. Per ogni interazione $t$, si calcola uno score composito $\mathcal{S}_{i,t}$:

$$
\mathcal{S}_{i,t} = w_{\text{rel}} \cdot I_{\text{compl}}(y_{i,t}) + w_{\text{qual}} \cdot Q_{\text{dato}}(i,t)
$$

La formula pondera due aspetti: il completamento effettivo del task ($I_{\text{compl}}$, variabile indicatrice binaria) e la qualità tecnica del dato prodotto ($Q_{\text{dato}} \in [0, 1]$, verificata dai moduli di controllo qualità ex-post). I pesi assegnati ($w_{\text{rel}} = 0.60$, $w_{\text{qual}}$ complementare) non sono casuali: la priorità assegnata all'affidabilità riflette l'obiettivo primario della piattaforma in questa fase, ovvero minimizzare il tasso di mancata esecuzione ("task failure rate"), che rappresenta il costo più oneroso.

### 16.3.2. Memoria e Decadimento Esponenziale
Per garantire la necessaria reattività ai cambiamenti di comportamento, la reputazione non viene calcolata come una semplice media aritmetica (che avrebbe un'inerzia eccessiva), bensì utilizzando una **Media Mobile Esponenziale (EMA)**:

$$
R_{i, t+1} = \lambda \cdot R_{i, t} + (1 - \lambda) \cdot \mathcal{S}_{i,t}
$$

Il fattore di decadimento $\lambda$, fissato sperimentalmente a 0.85, definisce la "lunghezza della memoria" del sistema. Questo valore rappresenta un punto di equilibrio ingegneristico tra stabilità e sensibilità: il sistema è sufficientemente robusto da tollerare un errore sporadico di un utente altrimenti valido ("perdono"), ma abbastanza sensibile da penalizzare rapidamente — facendo crollare $R_i$ — una sequenza ravvicinata di defezioni.

### 16.3.3. Il Filtro Rigido (Hard Filtering)
Quale estrema ratio per la protezione delle risorse economiche, il sistema implementa un meccanismo di **Hard Filter** basato su una soglia minima di tolleranza $R_{\min} = 0.30$:

$$
\text{Stato Utente}_i = 
\begin{cases} 
\text{ATTIVO} & \text{se } R_{i,t} \ge R_{\min} \\
\text{BLACKLIST} & \text{se } R_{i,t} < R_{\min}
\end{cases}
$$

La caduta dell'indice reputazionale sotto tale soglia critica comporta l'inserimento immediato in *Blacklist* e l'esclusione preventiva e automatica da qualsiasi futura allocazione ($\mathcal{T}_C = \emptyset$). Questa strategia di mitigazione del rischio non è punitiva fine a sé stessa, ma preventiva: tagliando la "coda sinistra" della distribuzione (gli *outliers* negativi), si abbatte drasticamente la probabilità aggregata di azzardo morale dell'intero sistema.

## 16.4. Selezione Meritocratica tramite Virtual Bidding

Il nucleo algoritmico innovativo del modello GAP risiede nella profonda ridefinizione del problema di *Winner Determination*. A differenza del modello classico utilizzato nella Fase 1, che massimizza il guadagno nominale ($v_i(S) - b_i$) ignorando totalmente il rischio di inadempienza, il GAP internalizza tale rischio direttamente nella funzione obiettivo tramite la tecnica del **Virtual Bidding** [19]. L'offerta economica $b_i$ presentata dall'utente viene trasformata in un'offerta "virtuale" $b'_i$, aggiustata per il rischio, prima ancora che l'asta abbia luogo.

### 16.4.1. La Trasformazione dell'Offerta
La trasformazione è governata dalla seguente relazione iperbolica:

$$
b'_{i} = \frac{b_i}{(R_i)^\kappa}
$$

Dove l'esponente $\kappa \ge 0$ (qui fissato a $1.0$) modula la sensibilità dell'algoritmo alla reputazione. Le implicazioni economiche di questa formula sono evidenti e potenti: per un utente affidabile ($R_i \approx 1.0$), il costo virtuale coincide con quello reale, permettendogli di competere ad armi pari. Al contrario, al calare della reputazione ($R_i \to 0$), il costo virtuale diverge rapidamente verso l'infinito ($b'_i \to \infty$), rendendo il costo percepito dall'algoritmo proibitivo ed estromettendo di fatto l'utente inaffidabile dalla competizione, indipendentemente da quanto bassa sia la sua offerta monetaria.

### 16.4.2. Selezione "Risk-Adjusted"
L'algoritmo di allocazione procede quindi a massimizzare il guadagno virtuale:

$$
\text{gain}'(i, S) = v_i(S) - b'_i
$$

Di conseguenza, un utente $i$ viene selezionato se e solo se soddisfa la condizione:
$$
v_i(S) > \frac{b_i}{(R_i)^\kappa} \iff v_i(S) \cdot (R_i)^\kappa > b_i
$$

Come formalmente dimostrato nel Teorema 16.1, questa disuguaglianza sancisce un principio economico fondamentale: il sistema accetta di assegnare un task a un utente con bassa reputazione solo qualora il valore generato dal task stesso ($v_i$) sia talmente elevato da giustificare e compensare il rischio di fallimento ("Risk Premium"). Tale meccanismo risolve alla radice il problema della **selezione avversa** osservato nella Fase 2, dove gli utenti peggiori vincevano le aste abbassando i prezzi.

## 16.5. Incentivi Dinamici: Il Premio di Fedeltà

In un contesto di interazioni ripetute, la sola minaccia di punizione (esclusione) può non essere sufficiente a garantire la cooperazione ottimale; la letteratura suggerisce la necessità di rinforzi positivi. Il modello GAP introduce pertanto un **Premio di Fedeltà** nel calcolo del pagamento finale $p_i^{\text{final}}$, arricchendo il compenso base determinato dalle regole VCG:

$$
p_i^{\text{final}} = p_i^{\text{vcg}} \cdot \left( 1 + \beta_{\text{trust}} \cdot \mathbb{I}(R_i > R_{\text{bonus}}) \right)
$$

Prevedendo un bonus massimo del 20% ($\beta_{\text{trust}} = 0.20$) riservato esclusivamente agli utenti "eccellenti" ($R_i > 0.90$), il meccanismo estende artificialmente quella che in Teoria dei Giochi è definita "Ombra del Futuro". L'utente razionale è disincentivato alla defezione non solo per il timore di sanzioni immediate, ma per non precludersi il flusso di guadagni extra futuri. Si ottiene così un allineamento degli incentivi: l'egoismo razionale dell'agente (massimizzare il profitto) coincide perfettamente con l'obiettivo sistemico della piattaforma (massimizzare l'affidabilità).

# Capitolo 17: Metodologia Sperimentale della Fase 3: Il Protocollo Stateful

## 17.1. Dalla simulazione statica all'ambiente persistente

La validazione empirica del modello GAP ha richiesto una revisione sostanziale e profonda dell'approccio metodologico rispetto alla Fase 2. Laddove l'analisi di vulnerabilità necessitava di isolare il rischio d'asta in un contesto "stateless" per purificarne la misurazione, la Fase 3 impone l'adozione di un ambiente *stateful*, ovvero un ecosistema dotato di memoria e capace di evolvere coerentemente nel tempo.

È stato pertanto progettato un protocollo sperimentale denominato **Simulazione a Coorte Persistente**, strutturato su tre livelli logici sequenziali:

1.  **Inizializzazione della Popolazione ($t=0$):** Alle ore 08:00 simulate viene istanziata una coorte $\mathcal{U}$ composta da $N=316$ agenti. Ogni utente $U_i$ viene generato con una razionalità $\rho_i$ immutabile (estratta dalla distribuzione *mixed*) e, aspetto cruciale, con uno stato epistemico "non informato". All'inizio, il sistema non possiede pregiudizi: assegna a tutti il Prior Bayesiano di default e una reputazione intatta ($R_i=1.0$).
2.  **Persistenza Temporale ($t \to t+1$):** A differenza della Fase 2, la coorte $\mathcal{U}$ non subisce alcun reset al termine di ogni slot orario. Lo storico delle azioni viene conservato integralmente. Se l'utente $U_k$ defeziona all'ora $h$, questa informazione viene registrata permanentemente nel database di simulazione e influenzerà il calcolo della reputazione (e quindi le probabilità di vittoria) per tutti i periodi successivi ($h+k$).
3.  **Dinamismo della Domanda:** A fronte di una forza lavoro stabile (gli utenti sono gli stessi per 12 ore), la domanda di task $\mathcal{T}_h$ viene rigenerata orariamente basandosi sui dati reali di mobilità. Questo simula fedelmente un mercato del lavoro reale, dove l'offerta è rigida nel breve periodo (es. una flotta di tassisti), mentre la domanda è fluida e varia spazialmente e temporalmente.

L'esperimento transita così dall'essere una serie di 12 istantanee indipendenti a un unico **processo evolutivo continuo** di 12 ore, configurazione ideale per osservare la convergenza degli algoritmi di apprendimento.

## 17.2. Segmentazione del Mercato: Strategia "High Value, High Trust"

Per tutelare ulteriormente il valore economico della piattaforma, è stata introdotta una segmentazione dei task basata sul rischio, classificando le attività in base al valore economico intrinseco $\nu_j$: **Task Standard** (che rientrano nei primi 4 quintili, sotto l'80° percentile) e **Task Critici** (il top 20% del mercato).

Per questi ultimi task, che sebbene numericamente inferiori concentrano una quota rilevante del valore totale scambiato, la piattaforma impone delle **Barriere all'Ingresso Adattive**. Nello specifico, vengono attivati due controlli: una **Soglia di Affidabilità ($R_{req} \in [0.70, 0.85]$)** e una **Soglia di Qualità ($\rho_{min}$)** basata sulla stima Bayesiana. Tale segmentazione crea un forte incentivo economico indiretto: declassando di fatto gli utenti inaffidabili al "mercato secondario" dei task a basso valore, si rende il mantenimento di un'alta reputazione l'unica via per accedere alle commesse più redditizie.

## 17.3. Chiusura del Loop: Il Feedback Qualitativo

Il ciclo adattivo si chiude trasformando i dati grezzi in conoscenza operativa attraverso una procedura a tre stadi eseguita al termine di ogni asta oraria:
1.  L'**Esecuzione ($y_{i,t}$)**, il cui esito è determinato dal modello probabilistico di azzardo morale descritto nei capitoli precedenti.
2.  La **Valutazione della Qualità ($Q_{dato}$)**. Qui, per massimizzare il realismo, la qualità è stata simulata come una variabile aleatoria correlata positivamente alla razionalità ($Q_{oss} \sim U(\rho_i - 0.1, \min(1.0, \rho_i + 0.1))$). Questa scelta modellistica riflette l'ipotesi che gli agenti poco razionali non siano solo propensi alla defezione, ma tendano a produrre dati mediocri anche quando collaborano.
3.  L'**Aggiornamento di Stato**, che ricalcola i parametri dell'utente (distribuzione Beta, $R_i$ e contatori Blacklist) in tempo reale, rendendoli immediatamente disponibili per l'asta dell'ora successiva.

# Capitolo 18: Analisi dei Risultati: Apprendimento e Resilienza del Sistema

## 18.1. La Curva di Apprendimento (Analisi del MAE)

Per quantificare oggettivamente la capacità del sistema GAP di colmare il divario informativo iniziale, è stato tracciato l'andamento orario dell'**Errore Medio Assoluto (MAE)**, calcolato come la media delle discrepanze tra la razionalità stimata ($\hat{\rho}_{i,t}$) e quella reale ($\rho_i$) dell'intera popolazione $\mathcal{U}$.

Dall'analisi dettagliata della serie temporale nello scenario *Mixed Rationality* (si faccia riferimento alla *Figura 1_confronto_apprendimento_mae.png*), emerge un chiaro e inequivocabile trend di convergenza. Partendo da un MAE iniziale di **0.2191** — un valore che riflette l'incertezza fisiologica del *prior* — l'errore si riduce progressivamente fino a toccare **0.1941** al termine delle 12 ore di simulazione. Questo decremento, pari all'**11.4%**, non è casuale: conferma che l'algoritmo di inferenza sta lavorando correttamente, "distillando" l'esperienza accumulata interazione dopo interazione per affinare la capacità di discriminazione tra collaboratori affidabili e opportunisti. La pendenza negativa della curva è la prova matematica che il sistema apprende.

## 18.2. L'Efficacia del "Filtro Attivo"

Una stima più precisa della razionalità si traduce direttamente in una migliore capacità di *targetizzazione* dei vincitori. Analizzando la composizione demografica dell'insieme $S_t$ (gli utenti che si aggiudicano i task), si nota una differenza sostanziale rispetto alla popolazione generale: i vincitori presentano una reputazione media $\bar{R}_{win} = 0.768$ e una razionalità stimata $\hat{\rho}_{win} = 0.693$, valori ben superiori alla media reale della popolazione ($\approx 0.595$).

Questo scarto statistico attesta l'efficacia della selezione meritocratica e dell'intervento chirurgico del **Filtro Rigido**: gli utenti che mostrano comportamenti opportunistici vedono la propria reputazione crollare rapidamente sotto la soglia critica $R_{\min}$, venendo automaticamente esclusi dal processo decisionale. Si realizza così una progressiva "bonifica" del mercato, dove le risorse vengono concentrate nelle mani degli attori più virtuosi.

## 18.3. Sostenibilità Economica: Il Costo della Sicurezza

L'adozione del modello GAP modifica inevitabilmente l'equilibrio economico della piattaforma: si passa dalla massimizzazione pura dei volumi (Fase 2) alla massimizzazione della sicurezza operativa. Nello scenario *Mixed - Fase 3*, l'**Utilità Netta ($u_{0, eff}$)** si attesta a **1.075,50 €**, a fronte di un **Valore Effettivo ($v_{eff}$)** di **8.970,02 €** e un costo per incentivi incrementato del 1.20% (**93,63 €**).

Sebbene l'utile netto risulti inferiore in termini assoluti rispetto alla Fase 2, tale contrazione non deve essere letta come un'inefficienza, bensì come il **"prezzo della stabilità"**. Esso deriva dalla somma di due fattori: il costo opportunità della selezione (la piattaforma preferisce lasciare un task insoddisfatto piuttosto che affidarlo a un utente a rischio) e l'investimento in fiducia (Trust Bonus), necessario per disincentivare la defezione nel lungo periodo. È un investimento assicurativo che protegge il valore del brand e la qualità del dato.

## 18.4. Deterrenza e Salute del Sistema

Un indicatore apparentemente controintuitivo è l'aumento del tasso di violazioni della Razionalità Individuale (IR) *ex-post*, che sale al **10.41%** (contro lo $\approx 0\%$ della Fase 2). In realtà, questo incremento è la prova che il sistema di controllo funziona: mentre nella Fase 2 le defezioni passavano inosservate (e impunite), nella Fase 3 il 10% dei vincitori ha tentato di defezionare, è stato "scoperto" e sanzionato, finendo con un'utilità negativa. La sanzione rende l'azzardo morale costoso, esercitando una potente funzione di deterrenza.

Parallelamente, l'**Health Score** si stabilizza su una media di **0.521** (cfr. *Figura gap_health_dashboard*). Nonostante la popolazione contenga un 65% di utenti intrinsecamente a rischio, il sistema riesce a mantenere un livello di servizio adeguato evitando il collasso qualitativo che aveva caratterizzato gli stress test della fase precedente, dimostrando una notevole resilienza sistemica.

# Capitolo 19: Analisi Comparativa: Stateless vs Stateful

## 19.1. Confronto delle Prestazioni

Il confronto diretto tra gli scenari *Mixed Rationality* delle due fasi sperimentali (riassunto nella Tabella 19.1) permette di isolare il valore aggiunto netto del modello GAP.

**Tabella 19.1: Confronto Prestazionale (12 Ore)**

| Metrica | Fase 2 (Stateless) | Fase 3 (GAP - Stateful) | Variazione ($\Delta\%$) |
| :--- | :--- | :--- | :--- |
| **Valore Nominale ($v_{mech}$)** | 13.396 € | 12.216 € | $-8.8\%$ |
| **Valore Effettivo ($v_{eff}$)** | 10.920 € | 8.970 € | $-17.9\%$ |
| **Utilità Netta ($u_{0, eff}$)** | 2.801 € | 1.075 € | $-61.6\%$ |
| **Tasso di Completamento** | 81.5% (Nominale) | 59.9% (Certificato) | $-26.5\%$ |
| **Violazioni IR Ex-Post** | $\approx 0\%$ | $10.41\%$ | N/A |
| **Health Score (Media)** | N/A (Degrado) | $0.521$ (Stabile) | N/A |

Il calo significativo dell'utile netto (-61.6%) e del volume operativo (-8.8%) registrato nella Fase 3 richiede una lettura critica attenta. Non si tratta di inefficienza tecnica, ma di una scelta strategica deliberata. Si transita da un modello "quantitativo" (Fase 2), che accetta indiscriminatamente rischi enormi pur di assegnare task e generare volume apparente, a un modello "qualitativo" (Fase 3). Quest'ultimo, tramite l'*Hard Filter*, riduce volutamente il volume per garantire la certezza dell'esecuzione. Il tasso di completamento del 59.9% nella Fase 3 rappresenta un "valore certificato" e affidabile, a differenza dell'80% "sporco" e inflazionato da defezioni nascoste della Fase 2.

## 19.2. Evidenze Grafiche dell'Adattamento

L'analisi grafica supporta ulteriormente la tesi della superiorità strutturale dell'approccio adattivo. In particolare, il grafico del MAE (*Figura confronto_apprendimento_f2_vs_f3.png*) evidenzia plasticamente la differenza tra i due approcci: la linea rossa della Fase 2 rimane piatta, sintomo di un sistema amnesico che "dimentica" tutto ogni ora; la linea verde della Fase 3 decresce monotonicamente, prova visiva di un sistema che trasforma l'esperienza grezza in capacità predittiva raffinata.

## 19.3. Resilienza sotto Stress

La vera prova di robustezza si osserva nelle ore di picco della domanda (13:00 - 14:00). Mentre la Fase 2 in questo frangente registrava il record negativo di defezioni assolute, esponendo la piattaforma a rischi reputazionali fatali verso i clienti finali, la Fase 3 reagisce attivamente. Proprio in quelle ore critiche si registra il picco di sanzioni (Violazioni IR al 16.67%) e una contrazione temporanea dell'utile. Tale dinamica reattiva dimostra la capacità del sistema di sacrificare il guadagno immediato per ristabilire l'ordine, preservando l'integrità e la credibilità del meccanismo nel lungo periodo.

# Capitolo 20: Conclusioni e Sviluppi Futuri

## 20.1. Sintesi del Lavoro

Questa tesi ha inteso affrontare e disarticolare il nodo cruciale della sostenibilità economica nei sistemi di Mobile Crowdsensing (MCS), focalizzandosi sulla progettazione di meccanismi di incentivo che siano robusti non solo in teoria, ma anche rispetto a comportamenti opportunistici in ambienti aperti e non controllati.

L'iter di ricerca si è sviluppato attraverso tre stadi fondamentali e logici: dall'analisi della baseline (Fase 1), che ha confermato la validità teorica ma la fragilità pratica dell'IMCU; alla verifica empirica della vulnerabilità (Fase 2), dove l'introduzione di bias cognitivi ha dimostrato il collasso inevitabile dei sistemi privi di memoria (con perdite di valore > 18%); fino alla proposta e validazione del modello GAP (Fase 3). Quest'ultimo, integrando inferenza Bayesiana e reputazione dinamica, ha dimostrato di poter ridurre l'errore di stima dell'11.4% e stabilizzare l'Health Score a 0.521, filtrando efficacemente le minacce interne.

## 20.2. Linee Guida per la Progettazione

I risultati conseguiti permettono di delineare alcune direttrici operative per la progettazione di future piattaforme di crowdsensing:
1.  **L'imprescindibilità della memoria storica:** Un sistema che non traccia la storia degli utenti è intrinsecamente vulnerabile all'azzardo morale.
2.  **Il Trade-off Qualità/Volume:** È necessario accettare una riduzione dei volumi nominali per garantire la qualità del dato, implementando filtri rigidi all'ingresso come costo necessario di protezione.
3.  **Incentivi Dinamici:** Le sole aste statiche non bastano; servono meccanismi (come i bonus di fedeltà) che estendano l'orizzonte temporale degli utenti, allineando gli obiettivi individuali a quelli sistemici.

## 20.3. Limiti e Prospettive

Lo studio, pur nei suoi risultati positivi, apre a ulteriori ambiti di indagine che meritano attenzione. In primis, il tema della **collusione**: il modello attuale assume agenti indipendenti, ma futuri sviluppi dovranno considerare gruppi di utenti coordinati (es. *Sybil attacks*), integrando analisi dei grafi sociali. In secondo luogo, la **privacy**: il tracciamento reputazionale granulare suggerisce l'esplorazione di tecniche di *Differential Privacy* per proteggere i dati sensibili. Infine, la **scalabilità**: per gestire milioni di utenti, un approccio decentralizzato basato su *Federated Learning* potrebbe offrire vantaggi significativi in termini di carico computazionale distribuito, superando i limiti dell'architettura centralizzata qui proposta.

In conclusione, il presente lavoro dimostra come l'incertezza comportamentale nel crowdsensing non rappresenti una fatalità ingovernabile, ma una variabile che può essere gestita, mitigata e infine neutralizzata attraverso un design algoritmico che sia al contempo consapevole, etico e adattivo.