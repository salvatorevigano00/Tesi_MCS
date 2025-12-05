# 2.1 Introduzione al Mobile Crowdsensing (MCS)

## 2.1.1 Contesto storico-tecnologico e limiti dei paradigmi classici
Nel campo dell'intelligenza ambientale (Ambient Intelligence) e delle Smart City, la raccolta pervasiva di dati territoriali in tempo reale è emersa come sfida rilevante dalla fine degli anni '90. I paradigmi classici, costituiti dalle **Wireless Sensor Network (WSN)**, sono tipicamente implementati come insiemi di nodi statici, dispiegati fisicamente sul territorio con un notevole sforzo logistico ed economico. Tali applicazioni spaziano dalla sensoristica industriale per la prevenzione sismica fino ai sistemi di monitoraggio strutturale (*Structural Health Monitoring*) di ponti, gallerie e infrastrutture critiche [17].

Il **modello architetturale WSN** si fonda su una topologia prevalentemente statica (nodi stazionari e sincronizzati), una comunicazione di tipo *point-to-sink* e un deployment vincolato da severi problemi di copertura radio e consumo energetico. Analisi approfondite di letteratura hanno dimostrato che la densità di campionamento e la scalabilità dei sistemi WSN rimangono limitate dagli elevati costi di installazione (CAPEX) e manutenzione (OPEX), inducendo spesso **coperture frammentate** e un'intrinseca difficoltà nell'adeguarsi ai pattern dinamici e imprevedibili della società urbana [18][19].

L'avvento di dispositivi mobili multimodali (smartphone, wearables, tablet), equipaggiati con un ampio insieme di sensori eterogenei — GPS, accelerometri, magnetometri, barometri, sensori di prossimità, microfoni MEMS, fotocamere ad alta risoluzione — e interfacce di comunicazione a banda larga (Wi-Fi, BLE, LTE, 5G), ha rivoluzionato questa prospettiva. A partire dal 2010, secondo le stime dell'ITU, si contano miliardi di dispositivi in uso attivo: ciascuno di essi costituisce in potenza un "nodo sensoriale mobile" distribuito casualmente e capillarmente sull'intero pianeta [17][18].

È fondamentale osservare che la differenza sostanziale tra WSN e MCS non riguarda solo l'architettura di rete, ma anche la *natura della fonte del dato*. Le WSN raccolgono dati "ambientali" tramite hardware proprietario dedicato; le reti MCS, al contrario, acquisiscono dati "sociali", "comportamentali" e "spazio-temporali" sfruttando come vettore la mobilità naturale e la *agency* della popolazione urbana. Questo cambio di paradigma introduce sfide specifiche — eterogeneità dei profili comportamentali, imprevedibilità dei pattern di copertura spazio-temporale e stringenti vincoli di *privacy-by-design* — che il paradigma MCS deve costantemente indirizzare per garantire l'affidabilità del servizio [19].

## 2.1.2 Definizione rigorosa di Mobile Crowdsensing
**Definizione 2.1 (Mobile Crowdsensing):**
Il **Mobile Crowdsensing** (**MCS**) è un paradigma di sensing partecipativo in cui una piattaforma digitale, generalmente centralizzata (cloud-based), coordina e incentiva la raccolta, la trasmissione e l'aggregazione di dati provenienti dal multilivello sensoriale di una vasta popolazione di dispositivi mobili. Tali dispositivi sono detenuti da utenti umani (gli *agenti*) che compiono azioni volontarie o semi-automatiche (misurazioni, fotografie, logging, annotazioni semantiche). L'MCS sfrutta la capillarità e la mobilità intrinseca della popolazione per massimizzare sia la granularità informativa sia la copertura spazio-temporale delle osservazioni, superando i limiti di scalabilità delle reti fisse [18][19].

Tale definizione evidenzia l'aspetto non invasivo e la "scalabilità sociale" del MCS: la *crowd*, composta da utenti reali e portatori naturali di *mobile devices*, può essere sfruttata — **previo un adeguato meccanismo di incentivazione** — per raccogliere informazioni ad altissima risoluzione su fenomeni urbani complessi che tradizionalmente richiederebbero investimenti proibitivi in hardware dedicato (si veda Cap. 1, Sezione 1.1, sulla democratizzazione della sensoristica).

## 2.1.3 Architettura e tassonomia dei sistemi MCS
### 2.1.3.1 Tassonomia architetturale
I sistemi di raccolta dati wireless possono essere classificati in tre macro-architetture principali, come sistematizzato nelle survey più recenti [19]:

**Figura 2.1: Tassonomia delle architetture di raccolta dati mobili**
![Figura 2.1: Tassonomia delle architetture di raccolta dati mobili](./Immagini/figura_2_1_differenze_architetture_raccolta_dati.png)
*Confronto tra i principali paradigmi di raccolta dati wireless. La **WSN tradizionale** si basa su una topologia a stella o mesh con nodi statici e un concentratore centrale (Sink) [17]. Il **Peer-to-peer Sensing** prevede la negoziazione e condivisione dati diretta tra dispositivi pari, senza l'ausilio di un backend centralizzato (es. tracciamento di prossimità via Bluetooth). Il **Mobile Crowdsensing (MCS)** implementa un coordinamento cloud-centrico con un workflow completo: emissione del task, raccolta dati, validazione e fornitura di servizi a stakeholder pubblici e privati [18]. La figura evidenzia la progressione dall'architettura strettamente centralizzata e statica (WSN), passando per forme decentralizzate, fino alla completa orchestrazione cloud-based tipica dei sistemi MCS moderni.*

### 2.1.3.2 Modello a tre livelli (Three-Tier MCS Architecture)
Nei framework MCS più avanzati, la letteratura identifica una struttura stratificata a tre livelli distinti [19]:

1.  **Layer Piattaforma:** Costituisce il livello centrale del sistema e implementa le logiche di orchestrazione, scheduling dei task, assegnazione agli utenti (task assignment), aggregazione dati, gestione dei pagamenti, filtri reputazionali e gestione della privacy [18].
2.  **Layer Task:** Definisce i parametri operativi della missione: area di interesse, intervallo temporale, tipologia di sensore richiesto, valore economico/credito associato e policy di privacy.
3.  **Layer Utenti:** Costituito dalla popolazione di agenti (sistema umano+device). Ogni agente è caratterizzato da una posizione mutevole, costi operativi privati (batteria, dati, sforzo), un profilo di affidabilità storico e pattern di partecipazione.

Questa stratificazione risulta essenziale per disaccoppiare la logica di orchestrazione (residente nel cloud/server) dalla granularità eterogenea della sensoristica e dai pattern locali dei singoli agenti, garantendo così modularità, tracciabilità e scalabilità orizzontale delle piattaforme.

![Figura 2.2: Architettura a tre livelli di un sistema Mobile Crowdsensing](./Immagini/figura_2_2_architettura_mcs_three_tier.png)
*Rappresentazione architetturale di uno scenario MCS reale. Nel **layer inferiore**, gli utenti mobili ricevono task, raccolgono dati tramite sensori integrati e trasmettono pacchetti cifrati verso la piattaforma centrale. Il **layer centrale** ospita il cloud server che processa e valida i dati attraverso algoritmi di outlier detection, gestisce i pagamenti agli utenti e redistribuisce dati/servizi aggregati. Il **layer superiore** rappresenta gli stakeholder finali: enti pubblici, privati e cittadini. Nel modello MCS, la piattaforma agisce come regista e aggregatore.*

## 2.1.4 Modalità operative: Participatory vs Opportunistic Sensing
La letteratura distingue due paradigmi operativi per l'acquisizione del dato nei sistemi MCS [19]:
  * **Participatory Sensing:**
    L'utente è parte attiva, consapevole e intenzionale del processo ("User-in-the-loop"). L'individuo seleziona, accetta e riceve una missione dal sistema, o addirittura elabora/filtra il dato prima di inviarlo.
    *Esempi:* Scattare una foto di una buca stradale per una campagna di manutenzione comunale; inserire una nota soggettiva sull'affollamento di un mezzo pubblico tramite app dedicata [17].
  * **Opportunistic Sensing:**
    Il dispositivo esegue il campionamento in modo automatico, trasparente o con minimo intervento umano; le misurazioni sono essenzialmente delle conseguenze indirette (*byproduct*) della routine di spostamento dell'utente.
    *Esempi:* Logging continuo della traccia GPS delle corse dei taxi (come nel dataset CRAWDAD utilizzato in questa tesi); raccolta dei livelli di rumore ambientale o della qualità dell'aria tramite *background service* durante gli spostamenti quotidiani [17][21].

## 2.1.5 Casi applicativi emblematici e impatto sulle policy
Le applicazioni MCS documentate in letteratura hanno dimostrato un impatto tangibile in diversi settori:
  * **Smart City e Infomobilità:**
    Piattaforme come *Waze* rappresentano uno dei casi di maggior successo del campo MCS: integrano dati provenienti da milioni di utenti per fornire routing urbano adattivo, segnalazione istantanea di incidenti, lavori in corso e gestione dinamica della viabilità. Questi sistemi validano il potenziale del crowdsensing su vasta scala per la mobilità intelligente [17][20].
  * **Monitoraggio Ambientale:**
    Progetti come *NoiseTube* trasformano gli smartphone in fonometri mobili per generare mappe di inquinamento acustico partecipative. Questo approccio introduce nuovi paradigmi di *citizen science*, consentendo agli utenti di contribuire attivamente alla mappatura di fenomeni ambientali con una densità spaziale impossibile per le reti fisse tradizionali [21].
  * **Pianificazione dei Trasporti:**
    L'analisi dei pattern spazio-temporali attraverso dataset di mobilità (taxi, autobus, ride-sharing) permette di identificare colli di bottiglia infrastrutturali e ottimizzare le reti di trasporto pubblico basandosi su dati reali di utilizzo [18].
  * **Sanità Pubblica (m-Health):**
    L'MCS viene impiegato per monitorare comportamenti a rischio, pattern di mobilità durante epidemie e fenomeni sanitari distribuiti, integrando spesso logiche avanzate di *privacy-preserving data collection* [19].

**Tabella 2.1:** *Confronto paradigmatico fra le architetture di raccolta dati mobili.*
| Paradigma | Deployment | Scalabilità | Tipi di dato | Coinvolgimento utente | Esempi operativi |
|:---------:|:----------:|:-----------:|:------------:|:---------------------:|:----------------:|
| **WSN** | Installazione fissa con costi elevati | Limitata (migliaia di nodi) | Fisici, ambientali, oggettivi | Nessuno (automatico) | Monitoraggio ponti, Smart Dust, IoT industriale |
| **Peer-to-peer Sensing** | Spontanea, senza infrastruttura dedicata | Moderata (decine di migliaia) | Locali, di prossimità, contestuali | Prevalentemente passivo | Tracciamento COVID-19, reti mesh, edge computing |
| **Mobile Crowdsensing** | Basato su mobilità naturale, costi ridotti | Molto alta (milioni di nodi) | Ambientali, sensoriali, contestuali, soggettivi | Attivo o passivo secondo il contesto | Waze, NoiseTube, OpenSense, Google Maps |

*I tre paradigmi rappresentano un'evoluzione progressiva nella raccolta dati distribuita. Le WSN tradizionali richiedono installazioni fisse con costi iniziali elevati, ma offrono controllo diretto sull'hardware. I sistemi peer-to-peer rimuovono l'infrastruttura centralizzata migliorando la privacy, a scapito però della scalabilità complessiva. Il Mobile Crowdsensing sfrutta la naturale mobilità degli utenti per ottenere una copertura geografica estesa e raccogliere dati sia oggettivi (misurazioni fisiche) che soggettivi (percezioni, annotazioni). Quest'ultimo approccio introduce tuttavia sfide significative nella gestione della qualità dei dati, nella tutela della privacy e nel mantenimento della motivazione dei partecipanti.*[19]

## 2.1.6 Limiti principali e implicazioni per la sostenibilità delle piattaforme
Nonostante i vantaggi, l'MCS presenta criticità intrinseche che richiedono soluzioni algoritmiche specifiche:
1.  **Qualità e affidabilità del dato (Data Trustworthiness):**
    Non esistendo un controllo diretto sulla manutenzione dell'hardware, sulla calibrazione o sull'onestà delle rilevazioni, la garanzia della qualità è affidata a strategie di aggregazione robusta (es. *Truth Discovery*, scoring reputazionale). La variabilità dei sensori *consumer-grade* e l'eterogeneità dei comportamenti umani introducono rumore e bias significativi [17][19].
2.  **Privacy e Sicurezza:**
    I dataset MCS (es. tracce GPS, dati acustici) contengono informazioni altamente sensibili che possono rivelare abitudini e identità degli utenti. La mancanza di strategie di *privacy-preserving*, anonimizzazione robusta e controllo degli accessi espone i partecipanti a rischi reali. L'architettura deve quindi integrare principi di *privacy-by-design* [19].
3.  **Sostenibilità della partecipazione (Incentive Mechanism):**
    Senza incentivi economici reali, tarati sul trade-off tra costi (batteria, dati, tempo) e benefici, l'adozione e il mantenimento dei contributi volontari si riducono rapidamente (fenomeno della *user fatigue*). Lo studio delle **aste inverse**, dell'**auction design** e delle **economie comportamentali** rappresenta una delle linee di ricerca principali del settore — nonché uno dei focus centrali di questa tesi [18].

## 2.1.7 Collegamento con l'architettura della tesi
Questa trattazione introduce la motivazione empirica del lavoro e la necessità di un approfondimento rigoroso sulla **teoria dei meccanismi di incentivazione**. La loro implementazione, test e validazione costituiscono il nucleo dei capitoli successivi. Ogni soluzione di MCS realmente implementabile (*deployable*) richiede infatti un equilibrio dinamico tra efficienza economica (budget), qualità dei dati (copertura/accuratezza), rispetto per la privacy ed equità nella distribuzione dei compensi [18][19].

Questi punti verranno ripresi e formalizzati nel prosieguo del capitolo; la storia critica dei modelli esistenti e i "gap" della letteratura attuale giustificano il focus sullo sviluppo di soluzioni innovative (come il meccanismo **IMCU** e l'algoritmo **GAP**) che rappresentano il cuore del contributo scientifico di questa tesi.

# 2.2 Fondamenti di Teoria dei Giochi Applicati al Mobile Crowdsensing
La **Teoria dei Giochi** fornisce il framework matematico e metodologico necessario per modellare le interazioni strategiche tra agenti razionali — utenti e piattaforma — nei sistemi di Mobile Crowdsensing (MCS). L'applicazione di tali modelli consente di indirizzare il problema dell'allocazione ottima delle risorse e di progettare meccanismi di incentivazione (*Mechanism Design*) capaci di soddisfare simultaneamente il vincolo di partecipazione (*Individual Rationality*) e la veridicità delle informazioni dichiarate (*Incentive Compatibility*).

Formalmente, un sistema MCS può essere modellato come una tupla $G = (N, S, u)$, dove:
* $N = \{1, 2, ..., n\}$ è l'insieme finito degli agenti (o *giocatori*), corrispondente alla popolazione di utenti mobili o alla piattaforma stessa;
* $S = S_1 \times S_2 \times ... \times S_n$ rappresenta lo spazio dei profili di strategia, in cui $S_i$ denota l'insieme delle azioni ammissibili per l'agente $i$ (ad esempio, la decisione binaria di accettare un task o il valore continuo dell'offerta $b_i$ in un'asta);
* $u = (u_1, u_2, ..., u_n)$ è il vettore delle funzioni di utilità $u_i: S \rightarrow \mathbb{R}$, che mappano un profilo di strategie nel *payoff* (guadagno netto) percepito dall'agente. In un contesto MCS, l'utilità è tipicamente formulata come la differenza tra la ricompensa ricevuta ($r_i$) e il costo sostenuto ($c_i$) per l'esecuzione del task: $u_i = r_i - c_i$.

## 2.2.1 Modelli di Gioco Cooperativi vs Non-Cooperativi
Una distinzione preliminare nella letteratura MCS riguarda la capacità degli agenti di sottoscrivere accordi vincolanti (*binding agreements*).

Nei **Giochi Cooperativi**, gli agenti hanno facoltà di formare coalizioni e stipulare accordi per ridistribuire il valore generato (utilità trasferibile), con l'obiettivo di massimizzare il valore della coalizione $v(C)$ dove $C \subseteq N$. L'analisi di questi scenari si concentra sulla stabilità della coalizione e sull'equità (*fairness*) nella ripartizione dei guadagni, ricorrendo a concetti di soluzione quali il **Core** o il **Valore di Shapley**, il quale assegna a ciascun giocatore un payoff pari al suo contributo marginale medio. Sebbene ideale per il *sensing collaborativo* (es. calcolo distribuito), questo approccio risulta spesso oneroso nelle reti mobili dinamiche a causa degli elevati costi di coordinamento e comunicazione (*overhead*) [17][19].

Al contrario, i **Giochi Non-Cooperativi** costituiscono il modello dominante nella progettazione dei sistemi MCS, specialmente nelle aste. In questo paradigma, ogni agente $i$ agisce in modo egoistico (*selfish*) per massimizzare esclusivamente la propria funzione di utilità $u_i$, assumendo l'assenza di accordi vincolanti esterni. Si assume che la razionalità dei partecipanti sia conoscenza comune (*common knowledge*). Tuttavia, l'interazione competitiva converge spesso verso equilibri non Pareto-efficienti; tale perdita di efficienza sociale è quantificata in letteratura attraverso il "Prezzo dell'Anarchia" (PoA) [19][22].

Per chiarire la distinzione, si consideri una campagna di monitoraggio del traffico: in uno scenario cooperativo, i tassisti potrebbero coalizzarsi per coprire l'intera area urbana e negoziare collettivamente un premio aggregato; in uno scenario non-cooperativo (*User-Centric*), ogni tassista compete individualmente in un'asta inversa per aggiudicarsi i task, guidando l'efficienza allocativa attraverso la pura competizione di prezzo.

## 2.2.2 Struttura Informativa: Giochi Bayesiani
La struttura informativa del gioco rappresenta la variabile critica per il *Mechanism Design*. Mentre i modelli teorici semplificati assumono spesso un'**Informazione Completa** (tutti conoscono le funzioni di utilità altrui), la realtà operativa del MCS è caratterizzata da **Informazione Incompleta**.

In tale contesto, si adottano i **Giochi Bayesiani**. Almeno un giocatore (tipicamente la piattaforma) non conosce alcune caratteristiche fondamentali degli altri, definite come il "tipo" dell'agente $\theta_i$ (che include informazioni private come il vero costo di sensing $c_i$ o la qualità del sensore). La piattaforma può solamente formulare stime probabilistiche (*beliefs*) sulla distribuzione dei tipi. Questa asimmetria informativa introduce il problema centrale del design: come incentivare gli utenti a rivelare veridicamente il proprio tipo privato? In assenza di meccanismi robusti, gli utenti razionali adotteranno comportamenti strategici (*market manipulation*) per massimizzare il profitto a scapito dell'efficienza del sistema [20][21].

## 2.2.3 Equilibrio di Nash e Strategie Dominanti
L'analisi della stabilità delle strategie si fonda sul concetto di **Equilibrio di Nash (NE)**. Un profilo di strategie $s^* = (s_1^*, ..., s_n^*)$ costituisce un NE se nessun giocatore ha incentivo a deviare unilateralmente dalla propria strategia, assumendo invariate quelle degli avversari:
$$
u_i(s_i^*, s_{-i}^*) \geq u_i(s_i, s_{-i}^*) \quad \forall i \in N, \forall s_i \in S_i
$$

Tuttavia, calcolare un NE richiede che gli agenti effettuino previsioni complesse sulle strategie altrui, un'ipotesi spesso irrealistica per utenti umani. Per questo motivo, i meccanismi MCS robusti mirano a implementare soluzioni in **Strategie Dominanti**. Una strategia è dominante se massimizza l'utilità dell'agente *indipendentemente* dalle azioni degli altri.

Un meccanismo d'asta è definito **Truthful** (o *Strategy-Proof*) se la rivelazione veritiera del proprio costo $c_i$ (ovvero porre l'offerta $b_i = c_i$) costituisce una strategia dominante. La proprietà di **Dominant Strategy Incentive Compatibility (DSIC)** garantisce che:
$$
u_i(c_i, b_{-i}) \geq u_i(b_i', b_{-i}) \quad \forall b_i' \neq c_i, \forall b_{-i}
$$

Questo risultato, supportato dal **Revelation Principle** di Myerson, riduce drasticamente il carico cognitivo per l'utente, il quale non deve speculare sulle offerte altrui ma limitarsi a riportare il proprio costo reale [21].

## 2.2.4 Giochi di Stackelberg
Per descrivere l'interazione asimmetrica tra piattaforma e utenti, si ricorre ai **Giochi di Stackelberg** (*Leader-Follower*).
La piattaforma agisce come *Leader*, muovendo per prima e anticipando la reazione razionale degli utenti (decisione su budget o prezzi). Gli utenti (*Followers*) osservano la mossa del leader e reagiscono scegliendo la *Best Response* per massimizzare la propria utilità.

La soluzione del gioco, o **Equilibrio di Stackelberg (SE)**, si ottiene tramite induzione a ritroso (*Backward Induction*), risolvendo un problema di ottimizzazione a due livelli (*bi-level optimization*):
$$
\max_{s_L} u_L(s_L, s_F^*(s_L))
$$

dove $s_F^*(s_L)$ rappresenta la funzione di risposta ottima dei follower alla strategia del leader. Questo approccio modella efficacemente i sistemi **Platform-Centric**, offrendo un controllo granulare sul budget, a differenza delle aste che caratterizzano gli approcci User-Centric [23].

## 2.2.5 Approfondimento Teorico: La garanzia di Truthfulness nel meccanismo VCG
Per comprendere matematicamente come sia possibile garantire la veridicità delle dichiarazioni, analizziamo il meccanismo **Vickrey-Clarke-Groves (VCG)**. Esso rappresenta la generalizzazione dell'asta di Vickrey e garantisce contemporaneamente efficienza allocativa (massimizzazione del benessere sociale) e truthfulness.

Consideriamo un'asta inversa MCS con un insieme di utenti $N$. Ogni utente $i$ ha un costo privato $c_i$ e dichiara un'offerta (*bid*) $b_i$. La piattaforma seleziona un insieme di vincitori $S \subseteq N$ per massimizzare il **Social Welfare (SW)**, definito come la valutazione $V(S)$ al netto dei costi dichiarati:
$$
SW(b) = \max_{S \subseteq N} \left( V(S) - \sum_{j \in S} b_j \right)
$$

Sia $S^*$ l'insieme ottimale di vincitori dato il vettore delle offerte $b$.

Secondo la **regola pivot di Clarke**, ogni vincitore $i \in S^*$ riceve un pagamento $p_i$ pari all'esternalità negativa che la sua assenza causerebbe al sistema:
$$
p_i = \underbrace{\left[ \max_{S' \subseteq N \setminus \{i\}} \left( V(S') - \sum_{j \in S', j \neq i} b_j \right) \right]}_{\text{SW ottimo senza l'agente } i} - \underbrace{\left[ V(S^*) - \sum_{j \in S^*, j \neq i} b_j \right]}_{\text{SW degli altri agenti con } i \text{ presente}}
$$

**Dimostrazione della Dominanza della Verità:**
L'utilità dell'utente $i$ è $u_i = p_i - c_i$. Sostituendo la formula del pagamento $p_i$, possiamo isolare i termini che non dipendono dalla strategia $b_i$ in una funzione $h(b_{-i})$:
$$
h(b_{-i}) = \max_{S' \subseteq N \setminus \{i\}} \left( V(S') - \sum_{j \in S', j \neq i} b_j \right)
$$

L'equazione dell'utilità si riscrive dunque come:
$$
u_i(b_i, b_{-i}) = h(b_{-i}) + \left[ V(S^*) - \sum_{j \in S^*, j \neq i} b_j - c_i \right]
$$

Analizzando il termine tra parentesi quadre, si nota che esso corrisponde esattamente al Social Welfare calcolato utilizzando il costo reale $c_i$ per l'utente $i$. Poiché il meccanismo VCG è progettato per massimizzare il termine $SW$ e $h(b_{-i})$ è una costante rispetto alle decisioni di $i$, ne consegue che l'agente massimizza la propria utilità $u_i$ se e solo se dichiara $b_i = c_i$, allineando il proprio obiettivo egoistico con l'ottimo sociale. Tale strategia risulta pertanto dominante.

# 2.3 Meccanismi di Incentivazione per il MCS
La progettazione di meccanismi di incentivazione (*Incentive Mechanisms*) robusti ed efficaci rappresenta una condizione essenziale per la sostenibilità operativa dei sistemi di Mobile Crowdsensing. In assenza di adeguati schemi di ricompensa, gli utenti razionali — dovendo sostenere costi certi in termini di consumo energetico, traffico dati e impegno cognitivo senza garanzie sui benefici — tenderebbero a non partecipare o ad abbandonare la piattaforma (*user attrition*).

Questa sezione analizza le principali classi di meccanismi proposti in letteratura, focalizzandosi sulle **aste inverse** e sul framework **IMCU**, che costituiscono lo stato dell'arte per i sistemi *User-Centric*. Prima di analizzare i modelli specifici, è utile definire formalmente le proprietà teoriche desiderabili che un meccanismo ideale dovrebbe soddisfare (Tabella 2.2).

**Tabella 2.2:** *Proprietà desiderabili dei meccanismi di incentivazione nel MCS.*

| Proprietà | Definizione Formale | Rilevanza nel MCS |
|:---|:---|:---|
| **Individual Rationality (IR)** | $u_i \geq 0$ | Garantisce che l'utente non subisca perdite partecipando (il reward copre almeno i costi). Fondamentale per la *retention*. |
| **Incentive Compatibility (IC)** | $u_i(c_i) \geq u_i(b_i')$ | Assicura che la strategia migliore per l'utente sia dichiarare i propri costi reali (Truthfulness), prevenendo manipolazioni di mercato. |
| **Computational Efficiency** | Tempo polinomiale $P$ | Il meccanismo deve calcolare vincitori e pagamenti rapidamente, anche con migliaia di utenti (scalabilità). |
| **Budget Balance (BB)** | $\sum p_i \leq B$ | La somma dei pagamenti erogati non deve superare il budget fissato dalla piattaforma (o il valore generato dai dati). |

## 2.3.1 Classificazione dei Meccanismi: Platform-Centric vs User-Centric
La tassonomia dominante in letteratura categorizza i meccanismi in base alla ripartizione del potere decisionale sul *pricing* [24].

### 2.3.1.1 Modelli Platform-Centric (o Crowdsourcer-Centric)
In questo approccio, la piattaforma agisce come *Leader* in un gioco di Stackelberg, fissando unilateralmente il reward unitario $r$ o il budget totale $B$. Essa pubblica un'offerta di tipo *take-it-or-leave-it*: l'utente $i$ accetta il task solo se il compenso proposto soddisfa il vincolo di razionalità individuale ($r \geq c_i$).

Sebbene questo modello garantisca un controllo rigoroso sul budget e una complessità computazionale minima (spesso lineare), soffre di una marcata **inefficienza allocativa** dovuta all'asimmetria informativa. Non conoscendo i costi reali degli utenti, la piattaforma rischia di incorrere in *over-payment* (remunerando eccessivamente utenti con costi bassi) o *under-payment* (fallendo nel reclutare utenti con costi elevati ma necessari per la copertura spaziale).

### 2.3.1.2 Modelli User-Centric (Auction-Based)
In questo paradigma, gli utenti assumono un ruolo attivo dichiarando le proprie aspettative di compenso tramite offerte (*bids*). La piattaforma agisce come banditore d'asta, raccogliendo le tuple $(task, b_i)$ e risolvendo il problema di *Winner Determination* per massimizzare l'utilità della campagna.

Il vantaggio primario risiede nella **Price Discovery**: il meccanismo permette di rivelare il vero valore di mercato dei dati, allocando i task agli utenti più efficienti e massimizzando il welfare sociale. Tuttavia, ciò introduce incertezza sul budget finale e sposta la complessità sul piano computazionale: i problemi di selezione ottima sono spesso riconducibili a varianti del *Knapsack Problem* o *Set Cover*, noti per essere NP-hard.

**Confronto Sintetico:**
Il modello Platform-Centric risulta preferibile in scenari con budget rigidi e task omogenei; il modello User-Centric è superiore quando l'obiettivo è massimizzare la qualità dei dati in ambienti eterogenei [24].

## 2.3.2 Aste Inverse (Reverse Auctions)
Nel contesto MCS, l'asta si configura come **inversa**: la piattaforma è il *buyer* e gli utenti sono i *sellers*.

Le aste tradizionali presentano limiti notevoli. Nella **First-Price Sealed-Bid Auction**, il vincitore riceve esattamente l'importo offerto ($p_i = b_i$). Questo meccanismo non è *truthful*: gli agenti razionali applicano strategie di *bid shading* (dichiarando $b_i > c_i$) per assicurarsi un profitto, introducendo inefficienze. Al contrario, l'asta di Vickrey (**Second-Price**) disaccoppia il pagamento dall'offerta, rendendo la veridicità una strategia dominante, ma è applicabile solo ad oggetti singoli.

Per scenari combinatori complessi, il riferimento teorico è il meccanismo **VCG (Vickrey-Clarke-Groves)**. Come dimostrato nella Sezione 2.2.5, il VCG garantisce simultaneamente efficienza sociale e *Truthfulness*. Tuttavia, il calcolo dei pagamenti VCG richiede la risoluzione esatta del problema di ottimizzazione. Poiché nel MCS la selezione dei vincitori è un problema NP-hard, l'uso di algoritmi approssimati (necessari per la scalabilità) rompe le proprietà del VCG standard. È quindi necessario ricorrere a meccanismi specifici come IMCU [20][25].

## 2.3.3 Il Meccanismo IMCU (Incentive Mechanism for Crowdsensing Users)
Il meccanismo **IMCU**, formalizzato da Yang et al. [25], rappresenta lo stato dell'arte per le aste inverse *User-Centric*. Esso risolve il dilemma tra efficienza computazionale e compatibilità degli incentivi, garantendo *Truthfulness* e *Individual Rationality* pur utilizzando algoritmi di selezione approssimati.

Il funzionamento del meccanismo è illustrato nello schema seguente:

**Figura 2.3: Workflow del Meccanismo IMCU**
*Il diagramma mostra il flusso logico del meccanismo. In input, la piattaforma riceve i profili utente e i bid. La Fase 1 seleziona i vincitori in modo iterativo (Greedy). La Fase 2 calcola per ciascun vincitore il "Critical Payment", ovvero il valore massimo che avrebbe potuto offrire rimanendo vincitore. L'output finale è l'insieme $S^*$ e il vettore dei pagamenti $P$.*

### 2.3.3.1 Fase 1: Winner Determination (Algoritmo Greedy)
Dato che il problema di selezione ottima è intrattabile, IMCU adotta un approccio *Greedy* sfruttando la **sottomodularità** della funzione di utilità $v(\cdot)$ (rendimenti marginali decrescenti). Ad ogni iterazione, l'algoritmo seleziona l'utente $i$ che massimizza il **guadagno marginale netto**:

$$
i^* = \arg \max_{i \in \mathcal{U} \setminus S} \left[ v(S \cup \{i\}) - v(S) - b_i \right]
$$

Il processo termina quando il budget è esaurito o il guadagno marginale diventa non positivo. La complessità è polinomiale ($O(n \cdot |S| \cdot m)$), rendendo il sistema altamente scalabile.

### 2.3.3.2 Fase 2: Calcolo dei Pagamenti Critici
Per ripristinare la proprietà di *truthfulness* persa abbandonando l'ottimizzazione esatta, i pagamenti non sono basati sul bid dichiarato, ma sul **valore critico** (o soglia), secondo la caratterizzazione di Myerson [21]. Il pagamento $p_i$ è definito come il bid più alto che l'utente $i$ avrebbe potuto dichiarare pur continuando a essere selezionato nell'insieme dei vincitori:

$$
p_i = \sup \{ b'_i : i \in S^*(b'_i, b_{-i}) \}
$$

Algoritmicamente, questo valore si calcola identificando il punto esatto nella lista ordinata dei candidati in cui l'utente $i$, aumentando la propria offerta, verrebbe "scavalcato" da un concorrente ed escluso dalla selezione.

Poiché il pagamento è indipendente dal bid dichiarato (purché $b_i < p_i$) e l'algoritmo di allocazione è monotono, IMCU garantisce che dire la verità sia una strategia dominante (**DSIC**) e che l'utilità sia sempre non negativa (**IR**), con un rapporto di approssimazione dell'efficienza pari a $(1 - 1/e) \approx 63.2\%$.

## 2.3.4 Altri Approcci nella Letteratura
Oltre alle aste, la letteratura esplora modelli alternativi per indirizzare vincoli specifici. Gli **All-pay Contests** premiano solo i primi classificati a fronte di uno sforzo collettivo, massimizzando la partecipazione ma rischiando di scoraggiare utenti con risorse limitate. La **Contract Theory** è impiegata per risolvere problemi di asimmetria informativa tramite menù di contratti autoselettivi. Infine, l'integrazione di sistemi di **Reputation & Gamification** mira a sfruttare la motivazione intrinseca degli utenti, spesso ibridando incentivi monetari e sociali per garantire la qualità del dato nel lungo termine (*Long-term Quality Assurance*) [19].

# 2.4 Sfide Operative nel MCS Reale
L'applicazione pratica dei modelli di Teoria dei Giochi e *Mechanism Design*, discussi nelle sezioni precedenti, deve confrontarsi con la complessità intrinseca degli scenari di *deployment* reale. Mentre i modelli matematici tendono ad assumere condizioni idealizzate — sensori perfetti, disponibilità costante e razionalità illimitata — un sistema MCS operativo deve affrontare sfide stocastiche legate alla qualità del dato, alla sicurezza, ai vincoli energetici e alle dinamiche spazio-temporali della folla.

### 2.4.1 Qualità dei Dati (Quality of Information - QoI)
La **Quality of Information (QoI)** costituisce la metrica fondamentale per valutare l'utilità di una campagna di sensing. In un ambiente partecipativo non controllato, la QoI è minacciata da vettori di degradazione eterogenei. In primo luogo, i sensori *consumer-grade* integrati negli smartphone non sono calibrati professionalmente e risultano soggetti a *drift* (deriva) delle misurazioni e rumore termico. A ciò si aggiunge il fattore umano: l'inesperienza degli utenti può portare a errori di acquisizione macroscopici (es. foto sfocate, ostruzione del microfono, errato orientamento del magnetometro). Infine, le condizioni ambientali avverse, come il rumore di fondo o la scarsa luminosità, possono inficiare la rilevazione anche in presenza di hardware funzionante e operatori attenti.

Un principio controintuitivo nel MCS è che il semplice aumento del numero di partecipanti non garantisce linearmente un aumento della QoI ("More is not always better"). Senza filtri adeguati, l'iniezione di dati rumorosi può degradare l'aggregato finale. Per mitigare questi rischi, la letteratura propone due approcci complementari: l'adozione di algoritmi di **Truth Discovery** (come il *Bayesian Truth Serum*), che stimano la "verità" pesando i contributi in base alla loro convergenza statistica senza conoscere il *ground truth* a priori, e l'implementazione di sistemi di **Reputation Scoring**, che storicizzano l'affidabilità dell'utente per modularne il peso nelle aggregazioni future.

### 2.4.2 Trustworthiness e Privacy
La fiducia (*Trust*) in un sistema MCS è un concetto bidimensionale che abbraccia sia l'affidabilità tecnica del dispositivo (*Trust by Reliability*) sia l'onestà comportamentale dell'agente (*Trust by Decision*). Il sistema è vulnerabile a diversi attacchi malevoli, tra cui i **Sybil Attacks**, in cui un singolo utente crea identità fittizie multiple per alterare l'aggregazione dei dati o accaparrarsi indebitamente le ricompense, e il **Data Poisoning**, che consiste nell'invio intenzionale di dati falsi per distorcere le mappe di sensing.

Parallelamente, la raccolta di tracce spazio-temporali solleva criticità severe in ambito **Privacy**, esponendo gli utenti a rischi di re-identificazione e profilazione (*inference attacks*). Le contromisure architetturali più robuste includono la **Differential Privacy**, che inietta rumore matematico controllato (Laplaciano o Gaussiano) nei dati per rendere indistinguibile il contributo del singolo individuo, e protocolli di **Secure Multi-party Computation (SMPC)**, che consentono alla piattaforma di calcolare statistiche aggregate (es. la media del rumore in un quartiere) senza mai decifrare i singoli input grezzi.

### 2.4.3 Consumo Energetico
L'energia rappresenta la risorsa critica (*scarce resource*) per eccellenza dal punto di vista dell'utente. Il "costo energetico" della partecipazione si ripartisce su tre fronti: l'attivazione dei sensori (particolarmente onerosa per GPS e giroscopio), l'elaborazione locale dei dati (es. crittografia o compressione) e, soprattutto, la trasmissione dati. L'upload tramite interfacce radio (LTE/5G) costituisce spesso la voce dominante di consumo.

Per garantire la sostenibilità a lungo termine, i meccanismi di selezione devono essere **Battery-Aware**, privilegiando utenti con carica residua elevata o in fase di ricarica. Inoltre, l'adozione di strategie di **Piggybacking** permette di ottimizzare il consumo marginale accodando la trasmissione dei dati di sensing a sessioni di comunicazione già attive (come chiamate vocali o navigazione web) [19].

### 2.4.4 Copertura Spaziale e Mobilità
La natura dinamica della folla introduce sfide significative nell'assegnazione dei task. La distribuzione spaziale degli utenti segue tipicamente leggi di potenza (*power laws*), creando una forte eterogeneità: altissima densità nei centri urbani e scarsità nelle periferie. I meccanismi di incentivazione devono quindi guidare attivamente lo spostamento verso queste aree "fredde" per evitare buchi informativi. Per i task dipendenti dalla posizione (*Location-Dependent*), la piattaforma necessita di modelli predittivi avanzati. Mentre le simulazioni teoriche si affidano spesso a modelli sintetici come il *Random Waypoint*, i sistemi reali utilizzano tracce GPS storiche per addestrare modelli (es. catene di Markov) capaci di anticipare la disponibilità di un sensore in una specifica cella spaziale [18].

### 2.4.5 Equità distributiva e indice di Gini
Un aspetto cruciale, spesso trascurato dai meccanismi focalizzati sulla pura efficienza, è l'**equità distributiva** (*Fairness*). Se un algoritmo premia sistematicamente solo gli utenti più efficienti (quelli con costi marginali minimi), si genera un fenomeno di "starvation" per la maggioranza dei partecipanti, che finiranno per abbandonare il sistema riducendone la resilienza.

Per quantificare la disuguaglianza nella distribuzione dei ricompensi, si ricorre alla **Curva di Lorenz** e al derivato **Coefficiente di Gini**.

![Figura 2.4: Curva di Lorenz e indice di Gini](./Immagini/figura_2_4_curva_lorenz_indice_gini.png)
*Rappresentazione grafica dell'equità distributiva. L'asse delle ascisse rappresenta la percentuale cumulativa degli utenti (ordinati per guadagno crescente), mentre l'asse delle ordinate rappresenta la percentuale cumulativa del budget totale distribuito. La linea tratteggiata a 45° rappresenta la perfetta equità ($G=0$). La Curva di Lorenz (linea continua) mostra la distribuzione reale. Il Coefficiente di Gini è calcolato come il rapporto tra l'area $A$ (compresa tra la linea di equità e la curva) e l'area totale $A+B$. Un indice $G$ elevato indica una forte concentrazione delle ricompense nelle mani di pochi utenti.*

Matematicamente, il coefficiente di Gini $G$ è definito come:

$$
G = \frac{A}{A + B}
$$

Il coefficiente varia nell'intervallo $G \in [0, 1]$, dove $0$ indica perfetta equità (tutti ricevono lo stesso compenso) e $1$ massima disuguaglianza (un solo utente ottiene tutto il budget). Nel MCS, l'analisi del Gini evidenzia il trade-off fondamentale tra **Efficienza ed Equità**: meccanismi di selezione ottima tendono ad avere un Gini alto. Mantenere questo indice controllato è essenziale per la **sostenibilità sociale** della piattaforma.

### 2.4.6 Analisi dei Pattern Temporali

I sistemi MCS sono soggetti a forti fluttuazioni temporali (cicli giorno/notte, giorni feriali/festivi). Comprendere questi pattern è essenziale per l'adattamento dinamico degli algoritmi. Attraverso tecniche di *Clustering* (come il **K-Means**), è possibile segmentare l'operatività del sistema in regimi temporali distinti:

  * **Regime On-Peak (Alta Domanda):** Caratterizzato da alta densità di utenti e competizione elevata, dove le risorse sono abbondanti.
  * **Regime Off-Peak (Bassa Domanda):** Caratterizzato da scarsità di utenti e rischio di monopoli locali, rendendo difficile la copertura dei task.

La qualità del raggruppamento viene validata tramite metriche come il **Silhouette Score**. Questa analisi è propedeutica all'**adattamento dinamico**: come si vedrà nel Capitolo 3, l'algoritmo **GAP** sfrutterà proprio il riconoscimento di questi regimi per modulare i prezzi in tempo reale.

# 2.5 Razionalità Limitata (Bounded Rationality)
La modellazione classica dei meccanismi d'asta e della Teoria dei Giochi si fonda sull'assunto neoclassico di **Razionalità Perfetta** (*Homo Economicus*). Secondo tale paradigma, gli agenti sono considerati decisori infallibili, dotati di capacità computazionale illimitata, onniscienza rispetto alle regole del gioco e coerenza assoluta nelle preferenze. Tuttavia, nei sistemi MCS reali — dove gli agenti sono esseri umani che operano in contesti urbani dinamici tramite smartphone — tale assunzione costituisce un'astrazione eccessivamente semplificatrice che rischia di invalidare le previsioni teoriche.

### 2.5.1 Il Modello di Herbert Simon e i Bias Cognitivi
Nel 1955, Herbert Simon introdusse il concetto di **Razionalità Limitata** (*Bounded Rationality*) per correggere il modello di ottimizzazione globale [27]. La teoria postula che la razionalità degli individui sia vincolata da tre fattori strutturali: i **limiti cognitivi** della mente umana (memoria di lavoro e attenzione finite), l'**informazione imperfetta** (incertezza sui costi futuri o sulle strategie altrui) e i stringenti **vincoli temporali** che precludono un'analisi esaustiva delle alternative.

Di conseguenza, gli agenti reali abbandonano la ricerca della soluzione ottima in favore del criterio di **Satisficing** (crasi di *satisfy* e *suffice*): essi ricercano una soluzione che sia "abbastanza buona" da soddisfare le loro soglie di aspirazione minime, arrestando il processo decisionale appena tale soglia viene raggiunta.
Per navigare la complessità con risorse limitate, gli utenti si affidano a euristiche (*fast-and-frugal heuristics*), ovvero scorciatoie mentali che, pur essendo efficienti, introducono deviazioni sistematiche dalla razionalità note come **Cognitive Biases** [28]. Nel contesto MCS, i più rilevanti includono:
  * **Anchoring Bias:** La tendenza a basare la propria valutazione del task eccessivamente sulla prima informazione ricevuta (es. un prezzo suggerito dalla piattaforma).
  * **Loss Aversion:** La percezione asimmetrica per cui la disutilità di una perdita è psicologicamente superiore all'utilità di un guadagno equivalente, portando gli utenti a comportamenti conservativi nel bidding.
  * **Overconfidence:** La sovrastima delle proprie capacità di previsione dei costi o delle probabilità di vittoria.

### 2.5.2 Fast-and-Frugal Trees (FFTs)
Per modellare operativamente il processo decisionale degli utenti in condizioni di razionalità limitata, la letteratura propone l'uso dei **Fast-and-Frugal Trees (FFTs)** [29].
Un FFT è un albero di decisione caratterizzato da una struttura **lessicografica** e non compensatoria: l'agente non valuta tutti i pro e i contro simultaneamente (come in una regressione logistica o in una funzione di utilità complessa), ma esamina una serie di indizi (*cues*) in un ordine sequenziale predeterminato. Ogni nodo dell'albero rappresenta una verifica su un singolo attributo e possiede almeno un'uscita che porta a una decisione finale immediata.

Un esempio tipico di euristica per l'accettazione di un task MCS è illustrato nella Figura 2.5.

![Figura 2.5: Modello decisionale Fast-and-Frugal Tree (FFT)](./Immagini/figura_2_5_fft.png)
*Rappresentazione di un'euristica decisionale per l'accettazione di un task. L'utente valuta sequenzialmente: la distanza fisica dal task, l'entità della ricompensa monetaria, la reputazione della piattaforma. A differenza dei modelli di utilità attesa, il mancato soddisfacimento di un criterio prioritario (es. distanza eccessiva) porta all'immediato rifiuto, indipendentemente dal valore degli altri attributi (es. ricompensa altissima).*

L'adozione di modelli FFT nel design della piattaforma permette di calibrare gli incentivi affinché superino le soglie euristiche della maggioranza degli utenti, riducendo il carico cognitivo necessario per valutare l'offerta e migliorando il tasso di conversione (*task uptake*).

### 2.5.3 Implicazioni sui Meccanismi d'Asta
L'impatto della razionalità limitata sui meccanismi d'asta si manifesta attraverso deviazioni significative dal comportamento teorico di equilibrio, che devono essere considerate nelle simulazioni:
1.  **Stima Rumorosa dei Costi ($\hat{c}_i$):** Nella realtà, quantificare esattamente il costo energetico e il costo opportunità del tempo è complesso. Gli utenti operano quindi su una stima affetta da errore $\hat{c}_i = c_i + \epsilon$, dove $\epsilon$ è un rumore percettivo.
2.  **Overbidding Strategico (Risk Aversion):** Anche in meccanismi *truthful* (dove $b_i = c_i$ è dominante), l'avversione al rischio spinge gli utenti a dichiarare un bid $b_i > c_i$. Questo "margine di sicurezza" serve a proteggersi dall'incertezza dei costi ex-post, ma ha l'effetto sistemico di aumentare i costi per la piattaforma e ridurre il numero di vincitori.
3.  **Underbidding Opportunistico:** Utenti inesperti possono erroneamente dichiarare $b_i < c_i$ nella speranza di aumentare le probabilità di vincita. Questo comportamento porta alla violazione della *Individual Rationality* empirica (l'utente opera in perdita), causando insoddisfazione e abbandono del sistema (*churn*).

Queste deviazioni dimostrano che le garanzie teoriche di *Truthfulness* potrebbero non reggere interamente di fronte al fattore umano. Diventa quindi imperativo non solo progettare meccanismi teoricamente corretti, ma anche **quantificare empiricamente** la loro resilienza rispetto a popolazioni con razionalità limitata, come verrà effettuato nelle simulazioni del **Capitolo 4**.

## 2.6 Funzioni Submodulari e Algoritmi Greedy
La trattazione dei meccanismi di incentivazione e dei problemi di allocazione delle risorse nel Mobile Crowdsensing (MCS) richiede la risoluzione di problemi di ottimizzazione combinatoria complessi. La maggior parte dei problemi di *Winner Determination* (selezione dei vincitori) in questo ambito è riconducibile alla massimizzazione di una funzione obiettivo sotto vincoli di budget o di cardinalità. Poiché la ricerca della soluzione ottima esatta è spesso computazionalmente intrattabile (NP-hard), la teoria delle **Funzioni Submodulari** fornisce le fondamenta matematiche per l'utilizzo di algoritmi di approssimazione efficienti.

### 2.6.1 Definizione Formale di Submodularità
Nel contesto del MCS, la funzione di valutazione $v(S)$ — che esprime la qualità dei dati, la copertura spaziale o il benessere sociale generato da un insieme di utenti $S$ — gode spesso della proprietà di submodularità.

**Definizione 2.2 (Funzione Submodulare):**
Data una funzione d'insieme $f: 2^{\mathcal{U}} \to \mathbb{R}$, dove $\mathcal{U}$ è l'insieme universo degli utenti, $f$ è detta submodulare se, per ogni sottoinsieme $A \subseteq B \subseteq \mathcal{U}$ e per ogni elemento $x \in \mathcal{U} \setminus B$, vale la seguente disuguaglianza:

$$
f(A \cup \{x\}) - f(A) \geq f(B \cup \{x\}) - f(B)
$$

Questa proprietà formalizza il concetto economico di **rendimenti marginali decrescenti** (*diminishing returns*). In termini intuitivi, il valore aggiunto (*marginal gain*) apportato da un nuovo utente $x$ è tanto maggiore quanto più piccolo è l'insieme a cui viene aggiunto, come illustrato nella Figura 2.6.

![Figura 2.6: Proprietà dei rendimenti decrescenti nelle funzioni submodulari](./Immagini/figura_2_6_rendimenti_decrescenti_submodularita.png)
*Rappresentazione grafica della submodularità. L'area azzurra rappresenta l'utilità totale accumulata $v(S)$ al crescere del numero di utenti. Le barre verticali evidenziano il guadagno marginale ($\Delta$) ottenuto aggiungendo un singolo utente in momenti diversi. Si osserva chiaramente che il contributo $\Delta_1$ (aggiunta in fase iniziale) è significativamente maggiore del contributo $\Delta_2$ (aggiunta a saturazione avvenuta), illustrando il principio economico dei rendimenti decrescenti.*

Un esempio applicativo chiarisce il concetto: consideriamo un task di copertura fotografica urbana. Se l'insieme di utenti selezionati $A$ è ridotto, l'aggiunta di un nuovo utente $x$ in una zona scoperta apporta un grande valore informativo. Se invece l'insieme $B$ è già esteso e copre gran parte dell'area di interesse, l'aggiunta dello stesso utente $x$ (che potrebbe trovarsi in una zona già mappata) apporterà un valore marginale inferiore o nullo.
Tale comportamento è strettamente legato alla proprietà di **Monotonicità**, per cui l'aggiunta di elementi non riduce mai il valore totale dell'insieme ($A \subseteq B \implies f(A) \leq f(B)$). Nel MCS, le funzioni di utilità sono tipicamente modellate come monotone e submodulari: più dati si raccolgono, maggiore è la qualità complessiva, ma con incrementi via via minori.

### 2.6.2 Algoritmi di Approssimazione Greedy
Dato che massimizzare una funzione submodulare sotto vincoli è un problema NP-hard, la ricerca dell'allocazione ottima $S^*$ richiederebbe l'esplorazione di uno spazio delle soluzioni esponenziale ($2^n$), rendendola inapplicabile per sistemi MCS con migliaia di utenti. Tuttavia, è possibile utilizzare **algoritmi Greedy** che costruiscono la soluzione iterativamente, compiendo ad ogni passo la scelta localmente ottima.

Il risultato teorico fondamentale che giustifica l'uso di tali algoritmi è il teorema di Nemhauser, Wolsey e Fisher.

**Teorema 2.1 (Nemhauser-Wolsey-Fisher, 1978):**
Per una funzione obiettivo $f$ monotona e submodulare, un algoritmo Greedy che seleziona iterativamente l'elemento che massimizza il guadagno marginale garantisce una soluzione $S_{\text{greedy}}$ tale che:

$$
f(S_{\text{greedy}}) \geq \left(1 - \frac{1}{e}\right) \cdot f(S^*) \approx 0.632 \cdot f(S^*)
$$

dove $S^*$ è la soluzione ottima globale ed $e$ è la base del logaritmo naturale [26].

Questo teorema stabilisce un *lower bound* teorico fondamentale: l'algoritmo Greedy, pur riducendo la complessità a tempi polinomiali (tipicamente $O(n \cdot k \cdot m)$), garantisce che la soluzione trovata non sia mai inferiore al \~63% dell'ottimo teorico, offrendo un eccellente trade-off tra efficienza computazionale e qualità della soluzione.

### 2.6.3 Applicazioni nel Winner Determination
Nel problema di *Winner Determination* per aste inverse (come nel meccanismo IMCU), l'algoritmo Greedy viene implementato massimizzando il Social Welfare marginale. La procedura inizia con un insieme vuoto $S_0 = \emptyset$ e, ad ogni iterazione $t$, seleziona l'utente $i$ che massimizza il **guadagno marginale netto** $\delta_i$, definito come:

$$
\delta_i(S_{t-1}) = v(S_{t-1} \cup \{i\}) - v(S_{t-1}) - b_i
$$

L'utente $i^*$ che massimizza $\delta_i$ viene aggiunto all'insieme solo se il contributo è positivo, terminando quando il budget è esaurito.

Per gestire dataset massivi, l'implementazione naive può essere ottimizzata sfruttando ulteriormente la submodularità. Tecniche come la **Lazy Evaluation** (o *Accelerated Greedy*) evitano di ricalcolare il guadagno marginale di tutti gli utenti ad ogni passo: poiché i guadagni marginali possono solo decrescere, se il valore "vecchio" di un utente è già inferiore al valore corrente del miglior candidato, l'aggiornamento è superfluo. L'utilizzo combinato di **Priority Queues** per mantenere i candidati ordinati permette di accedere al miglior candidato in tempo costante, velocizzando drasticamente la fase di selezione [26].

## 2.7 Modelli di Costo e Routing
Per stimare i costi operativi degli utenti ($c_i$) e calcolare metriche di efficienza del sistema, è necessario definire un modello geometrico e di mobilità che traduca le coordinate geografiche in distanze percorribili. Poiché la risoluzione di problemi di routing stradale reale tramite API esterne (es. Google Maps o OSRM) sarebbe computazionalmente proibitiva nelle simulazioni su larga scala, si adottano modelli analitici robusti.

### 2.7.1 Calcolo delle Distanze Geodetiche e Fattore di Tortuosità
Per calcolare la distanza tra due punti sulla superficie terrestre (ad esempio tra la posizione attuale dell'utente e il centroide di un task), si utilizza la **formula dell’Haversine**. Tale formula restituisce la distanza ortodromica (“great circle distance”) assumendo la Terra come sfera perfetta. Siano $P_1(\phi_1, \lambda_1)$ e $P_2(\phi_2, \lambda_2)$ due punti noti in latitudine e longitudine, la distanza $d_H$ è calcolata come:

$$
a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)
$$

$$
d_H(P_1, P_2) = 2R \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right)
$$

dove $R \approx 6371$ km è il raggio medio terrestre.

Poiché la distanza geodetica $d_H$ rappresenta il percorso in linea d’aria e sottostima la distanza reale su strada, si applica un fattore correttivo noto come **fattore di tortuosità urbano ($\eta_{urban}$)**:

$$
d_{effettivo} \approx \eta_{urban} \cdot d_H(P_1, P_2)
$$

La letteratura stima per le città europee dense e storiche un valore di $\eta_{urban}$ compreso tra 1.2 e 1.4. In questa tesi si utilizza il valore conservativo $\eta_{urban} = 1.30$, calibrato sulla topologia stradale di Roma.

### 2.7.2 Modellazione dei Percorsi: Star Routing vs TSP
Una volta definita la metrica di distanza, è necessario modellare la strategia di percorso che l’utente segue per visitare i task assegnati. La letteratura distingue due approcci principali:

Il primo è lo **Star Routing** (o *Radial Routing*), un modello semplificato che assume che l'utente serva ogni task partendo dalla propria posizione iniziale come se fossero viaggi indipendenti (andata e ritorno).

$$
D_{star} = \eta_{urban} \sum_{j \in \Gamma_i} 2\times d_H(pos_i, pos_j)
$$

Questo approccio è computazionalmente leggero (O(N)) e fornisce una stima prudente (*upper bound*) dei costi, assumendo che ogni task richieda un viaggio dedicato di andata e ritorno dalla posizione base. Sebbene sovrastimi la distanza rispetto a un percorso sequenziale ottimizzato, questa scelta garantisce la robustezza del vincolo di Individual Rationality: l'utente viene compensato per il caso peggiore di routing.

Il secondo è basato sul **Traveling Salesman Problem (TSP)**. Questo modello pianifica il percorso che visita la sequenza di task minimizzando la distanza totale. Essendo il TSP un problema NP-hard, per istanze reali si ricorre a euristiche come *Nearest Neighbor* o l'algoritmo di Christofides. Sebbene più accurato, il calcolo del TSP per ogni utente in ogni iterazione della simulazione introdurrebbe un *overhead* eccessivo.

**Scelta implementativa:**
In questa tesi, per garantire la robustezza del vincolo di *Individual Rationality*, i costi stimati dalla piattaforma (e quindi i pagamenti minimi garantiti) sono basati sul modello **Star Routing**. Questa scelta cautelativa assicura che, anche nel caso peggiore di routing inefficiente, l'utente non operi in perdita. Gli agenti simulati, tuttavia, sono liberi di ottimizzare i propri spostamenti reali (approssimando un TSP) per massimizzare il proprio margine di profitto netto.

### 2.8.2 Assunzioni Irrealistiche di Razionalità Perfetta
**Problema:**  
Gran parte della letteratura assume agenti perfettamente razionali (omniscienti, privi di bias), sempre veritieri in presenza di meccanismi truthful.

**Limite:**  
La realtà, come discusso nella sezione 2.5, è dominata dalla *Bounded Rationality* (Simon, 1955): la letteratura non quantifica empiricamente quanto le deviazioni cognitive (errori di stima, avversione al rischio, euristiche) influiscano sulle garanzie teoriche dei meccanismi. Non è noto in che misura il sistema degradi se gli utenti non si comportano come previsto.

**Contributo della tesi:**  
Viene simulata una popolazione eterogenea, con agenti dotati di livelli diversi di razionalità, per misurare la resilienza del meccanismo (ad esempio rispetto a overbidding/underbidding strategici).

### 2.8.3 Sensibilità ai Parametri di Configurazione

**Gap:**  
Pochi lavori hanno analizzato sistematicamente come la variazione dei parametri (ad esempio il **raggio di copertura del task** $r$) influenzi il trade-off tra efficienza ed equità. Un raggio ampio può consentire che pochi "super-utenti" coprano molte regioni (massimizzando efficienza ma riducendo l’equità e la partecipazione a lungo termine).

**Contributo della tesi:**  
Si esegue un’analisi di sensitività rispetto al raggio $r \in \{1.5, 2.5, 4.0\}$ km, per tracciare la frontiera di Pareto tra efficienza ed equità.

### 2.8.4 Mancanza di Meccanismi Adattivi

**Problema:**  
I principali meccanismi in letteratura sono statici: applicano le medesime regole e parametri a prescindere dal contesto operativo o dalla storia degli utenti.

**Gap:**  
L’assenza di feedback e apprendimento rende il sistema vulnerabile a manipolazioni e non consente ottimizzazione in regime di scarsità. Non esistono framework che integrino reputation scoring e correzione dei bias comportamentali nel processo allocativo in modo dinamico.

**Contributo della tesi:**  
Viene proposto e validato il nuovo approccio **GAP (Game-theoretical Adaptive Pricing)**. Questo introduce un livello di intelligenza adattiva, apprendendo dai regimi operativi e dai profili utente per modulare dinamicamente prezzi e selezioni, superando così i limiti dei modelli tradizionali.

## Riferimenti Bibliografici
[17] N. D. Lane et al., "A survey of mobile phone sensing," *IEEE Comm. Mag.*, vol. 48, no. 9, 2010.

[18] R. K. Ganti et al., "Mobile crowdsensing: current state and future challenges," *IEEE Comm. Mag.*, vol. 49, no. 11, 2011.

[19] A. Capponi et al., "A survey on mobile crowdsensing systems," *IEEE Comm. Surveys & Tutorials*, vol. 21, no. 3, 2019.

[20] V. Krishna, *Auction Theory*, 2nd ed. Academic Press, 2009.

[21] R. B. Myerson, "Optimal Auction Design," *Mathematics of Operations Research*, vol. 6, no. 1, 1981.

[22] D. Fudenberg and J. Tirole, *Game Theory*. MIT Press, 1991.

[23] J. Nie et al., "A Stackelberg Game Approach Toward Socially-Aware Incentive Mechanisms," *IEEE Trans. Wireless Comm.*, 2019.

[24] X. Zhang et al., "Incentives for mobile crowd sensing: A survey," *IEEE Comm. Surveys & Tutorials*, vol. 18, no. 1, 2016.

[25] G. Yang, Q. He, X. Zhang, Y. Zhang, and F. Chen, "Incentive mechanisms for mobile crowd sensing: A survey," *IEEE Comm. Surveys & Tutorials*, vol. 18, no. 1, pp. 54–67, 2016.

[26] G. L. Nemhauser, L. A. Wolsey, and M. L. Fisher, "An analysis of approximations for maximizing submodular set functions—I," *Mathematical Programming*, vol. 14, no. 1, 1978.