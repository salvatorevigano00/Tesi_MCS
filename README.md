# Progettazione e Implementazione di un Meccanismo di Incentivazione per Mobile Crowdsensing con Governance Adattiva

## Descrizione del Progetto
Questo progetto di tesi sperimentale ha l'obiettivo di progettare, implementare e validare un sistema di Mobile Crowdsensing (MCS) che integri i principi teorici presentati in letteratura, specificamente nel modello *Incentive Mechanisms for Mobile Crowdsensing* (IMCU), estendendoli a scenari operativi realistici.

Il lavoro affronta il passaggio da un contesto teorico ideale a uno scenario pratico caratterizzato da utenti a **razionalità limitata**. Per gestire le inefficienze derivanti da comportamenti umani non ottimali, il sistema introduce un livello esplicito di **governance adattiva**. Tale meccanismo si basa su sistemi di reputazione dinamica, vincoli di partecipazione individuale (IR) e metriche di monitoraggio della salute del sistema, con lo scopo di garantire robustezza e sostenibilità nel lungo periodo.

## Definizioni e Concetti Chiave
Per una corretta interpretazione del lavoro svolto, si riportano le definizioni dei concetti fondanti e degli acronimi utilizzati nel progetto:

**Mobile Crowdsensing (MCS)**
È il paradigma tecnologico alla base dello studio. Sfrutta la sensoristica diffusa nei dispositivi mobili personali (come smartphone e tablet) per creare una rete di monitoraggio capillare e distribuita. Questo approccio permette di raccogliere dati ambientali e urbani su larga scala senza i costi elevati necessari per dispiegare infrastrutture di sensori statiche dedicate.

**IMCU (Incentive Mechanisms for Mobile Crowdsensing)**
Rappresenta il framework teorico di riferimento (baseline) adottato in questa tesi. È un modello algoritmico progettato per gestire l'assegnazione dei compiti e i pagamenti agli utenti tramite un meccanismo di asta inversa. Il suo scopo, in condizioni ideali, è garantire che gli utenti siano incentivati a partecipare e a dichiarare i propri costi reali (veridicità), assicurando l'equilibrio economico del sistema.

**Razionalità Limitata (Bounded Rationality)**
Concetto economico-comportamentale introdotto nella Fase 2. A differenza della teoria classica che vede l'agente come un ottimizzatore perfetto, qui si assume che gli utenti reali abbiano limiti cognitivi, informazioni incomplete e possano commettere errori di valutazione o agire in modo opportunistico (es. defezioni, moral hazard), influenzando negativamente l'efficienza del meccanismo.

**GAP (Game-theoretic Adaptive Policy)**
È il contributo innovativo sviluppato in questo progetto. Si tratta di un modulo di governance algoritmica che estende l'IMCU per gestire l'incertezza derivante dalla razionalità limitata. Il GAP utilizza l'apprendimento bayesiano per stimare l'affidabilità degli utenti e adatta dinamicamente le regole di ingaggio (tramite reputazione e vincoli di partecipazione), sacrificando parte dell'efficienza teorica per guadagnare robustezza e stabilità operativa.

## Obiettivi e Fasi della Sperimentazione
Il lavoro si articola in tre fasi di sviluppo incrementale, supportate da una fase trasversale di validazione dei dati.

### Fase 1: Integrazione del Sistema MCS Teorico (Baseline)
Il primo obiettivo è la realizzazione di un sistema MCS pienamente conforme al modello teorico di riferimento. In questa fase si utilizza un dataset proprietario relativo a tassisti operanti nella città di Roma, assumendo un contesto di **razionalità perfetta**.

Le caratteristiche principali di questa fase includono:
* Implementazione fedele dell'algoritmo IMCU e dei relativi meccanismi di selezione, offerta (bidding) e pagamento.
* Adozione di un modello di asta veritiera che rispetta i principi dell'equilibrio di Nash.
* Verifica empirica della stabilità del sistema, dimostrando che le scelte ottimali degli utenti coincidono con l'equilibrio previsto e che le metriche economiche (valore totale, utilità, efficienza) rispecchiano le previsioni teoriche.

### Fase 2: Introduzione della Razionalità Limitata
La seconda fase rimuove l'ipotesi di idealità, introducendo modelli comportamentali realistici. Gli utenti vengono classificati in profili differenziati (es. quasi-razionali, opportunisti) che possono commettere errori decisionali o adottare strategie di azzardo morale.

Gli obiettivi di questa fase sono:
* Modellare comportamenti sub-ottimali, inclusi tentativi di manipolazione del sistema, defezioni dopo il pagamento o completamento parziale delle attività.
* Quantificare matematicamente il deterioramento dell'efficienza del sistema.
* Dimostrare la vulnerabilità del modello teorico originale, evidenziando come il valore effettivo realizzato $v(S_{\text{eff}})$ risulti inferiore al valore teorico $v(S_{\text{mech}})$ e come aumenti il tasso di fallimento (breakdown) del meccanismo in assenza di correttivi.

### Fase 3: Meccanismo Adattivo basato su GAP (Game-theoretic Adaptive Policy)
In risposta alle criticità emerse nella Fase 2, viene progettato e integrato un meccanismo di governance adattiva (GAP). Questo modulo estende le logiche di base con componenti di apprendimento bayesiano e gestione della reputazione.

Le funzionalità chiave del meccanismo GAP includono:
* **Apprendimento comportamentale:** Aggiornamento costante di una stima bayesiana della razionalità utente $\hat\rho$ basata sullo storico delle attività completate.
* **Adattamento dinamico:** Modulazione degli incentivi tramite bonus e malus legati alla reputazione, con salvaguardie per rispettare il vincolo di partecipazione individuale (IR).
* **Filtraggio preventivo:** Applicazione di soglie di accesso per utenti e attività ad alto rischio, al fine di ridurre le defezioni.
* **Monitoraggio della salute:** Valutazione continua tramite metriche dedicate (Health Score, tasso di completamento, violazioni IR).

L'obiettivo di questa fase è rendere esplicito il compromesso tra efficienza economica e controllo. La configurazione adottata privilegia la robustezza e la stabilità del sistema (minore rischio regolatorio, maggiore qualità dei partecipanti) rispetto alla pura massimizzazione del profitto immediato.

### Validazione e Analisi dei Dati
Parallelamente alle fasi di sviluppo, il progetto include una procedura sistematica di validazione dell'intera pipeline sperimentale. Questa attività comprende:
* Esame critico dei moduli software e verifica della correttezza logica del codice.
* Controlli incrociati sulla consistenza numerica dei KPI prodotti (tabelle e grafici).
* Analisi di sensibilità ai parametri per confermare l'autenticità e la riproducibilità delle evidenze empiriche raccolte.

## Risultati Attesi
Il progetto mira a consegnare un sistema empiricamente verificato che dimostri:
1. **La correttezza formale del modello teorico** in condizioni ideali, confermando le proprietà dell'algoritmo in uno scenario controllato.
2. **L'instabilità e la perdita economica** causate dalla razionalità limitata, quantificando l'impatto dei comportamenti opportunistici sul valore generato.
3. **L'efficacia della soluzione adattiva (GAP)** nel recuperare governabilità e trasparenza, garantendo la sostenibilità del processo di crowdsensing attraverso un compromesso esplicito tra efficienza e controllo.