# Capitolo 1: Introduzione

## 1.1. Contesto: Il Paradigma del Mobile Crowdsensing
Negli ultimi anni si è verificato un cambiamento radicale nel modo in cui raccogliamo dati sul mondo che ci circonda. Gli smartphone e i dispositivi mobili moderni integrano numerosi sensori — ricevitori GPS, accelerometri, giroscopi, magnetometri, microfoni, fotocamere ad alta risoluzione — supportati da capacità di calcolo e connettività in continua crescita. Questa infrastruttura sensoriale distribuita ha reso possibile un nuovo approccio alla raccolta dati territoriali.[1]

Su questa base tecnologica si è sviluppato il paradigma del **Mobile Crowdsensing (MCS)**, che sfrutta la mobilità degli utenti per raccogliere informazioni su larga scala senza dover installare infrastrutture dedicate. A differenza delle tradizionali reti di sensori wireless statici (WSN), che richiedono investimenti significativi per il dispiegamento e la manutenzione dell'hardware, l'MCS delega la raccolta dati alla "folla" (*crowd*), dove gli utenti contribuiscono attivamente alla generazione delle informazioni.[2]

La letteratura distingue due modalità operative principali:[3]

1. **Rilevamento Partecipativo (*Participatory Sensing*):** L'utente interviene attivamente nel processo (ad esempio, fotografando una buca stradale o segnalando manualmente il prezzo del carburante).
2. **Rilevamento Opportunistico (*Opportunistic Sensing*):** La raccolta avviene automaticamente in background durante le normali attività quotidiane (ad esempio, il campionamento delle reti Wi-Fi disponibili o il monitoraggio delle vibrazioni stradali durante la guida).

La Figura 1.1 illustra l'architettura generale di un sistema MCS: la piattaforma centrale (server cloud) pubblica task geolocalizzati, gli utenti mobili raccolgono dati tramite i sensori dei propri dispositivi e li trasmettono al server, che li aggrega e fornisce servizi ai consumatori finali (città, enti di ricerca, aziende).

![Figura 1.1: Architettura concettuale di un sistema di Mobile Crowdsensing. La piattaforma centrale coordina tre attori principali: (i) pubblica task geolocalizzati agli utenti mobili, (ii) raccoglie dati dai sensori dei dispositivi, (iii) aggrega le informazioni e fornisce servizi ai consumatori finali (amministrazioni pubbliche, enti di ricerca, aziende).](./Immagini/figura_1_1_sistema_mcs.jpg)

La piattaforma invia task o incentivi agli utenti, al fine di ottenere dati rilevati: dal monitoraggio del traffico in tempo reale alla mappatura dell'inquinamento acustico, dal controllo della qualità dell'aria alla verifica della copertura delle reti cellulari[4][5]. Roma, con la sua complessa topologia urbana — un centro storico medievale che si intreccia con quartieri moderni — e flussi di mobilità eterogenei, rappresenta un caso di studio significativo per analizzare le dinamiche di questi sistemi. Il dataset utilizzato in questo lavoro (febbraio 2014, CRAWDAD roma/taxi)[12] traccia continuativamente 316 veicoli per 28 giorni, generando circa 11 milioni di punti GPS su un'area di oltre 1200 km². La peculiarità di Roma — con la ZTL nel centro storico, il sistema viario radiale-anulare e zone periferiche a bassa densità — permette di testare il meccanismo in condizioni di domanda spazialmente eterogenea, dove la stessa distanza chilometrica può comportare costi operativi molto diversi a seconda della zona attraversata.

## 1.2. Il Problema: La Sfida degli Incentivi e della Razionalità
Nonostante il potenziale tecnologico, la sostenibilità a lungo termine di un sistema MCS dipende dalla partecipazione attiva e continuativa degli utenti. Si presenta un problema fondamentale: **la fornitura di dati di qualità comporta costi non trascurabili per i partecipanti**.[6]

Quando un utente partecipa a una campagna di sensing, sostiene diversi tipi di costi. Innanzitutto, ci sono i costi digitali: consumo di batteria (talvolta significativo, se i sensori GPS e accelerometri rimangono attivi per ore), utilizzo del piano dati mobile, potenza di calcolo. Nel caso di task che richiedono spostamenti fisici verso aree specifiche — quello che la letteratura definisce rilevamento *location-dependent* — i costi includono carburante, usura del veicolo e tempo impiegato. Un tassista che deve deviare dalla rotta ottimale sostiene costi aggiuntivi: accogliere dati in zone specifiche implica rinunciare a corse redditizie.

Anche la privacy costituisce una barriera significativa. Condividere tracce GPS dettagliate, registrazioni audio o fotografie geolocalizzate solleva legittime preoccupazioni: dove finiscono questi dati? Chi può accedervi? Possono essere utilizzati per ricostruire abitudini quotidiane e pattern comportamentali sensibili?[7]

La **gamification** (badge, classifiche, punteggi di reputazione) può funzionare inizialmente per attrarre utenti, ma diversi studi longitudinali evidenziano come questi incentivi intrinseci perdano efficacia quando i costi tangibili superano la gratificazione psicologica. Quando il rapporto costo-beneficio percepito diventa negativo — ad esempio, sostenere costi di carburante significativi per ottenere solo riconoscimenti virtuali — il tasso di abbandono aumenta drasticamente. La progettazione di **meccanismi di incentivazione monetaria** robusti ed efficienti diventa quindi fondamentale per garantire la sostenibilità economica di una piattaforma MCS professionale.[8]

Progettare questi meccanismi in un contesto reale solleva questioni complesse. Si identificano tre criticità fondamentali:

1. **Asimmetria Informativa:** La piattaforma conosce il valore dei dati che vuole raccogliere, ma non conosce i costi privati che ogni singolo utente deve sostenere per fornirli. Un tassista che opera nel centro storico ha costi operativi diversi da uno che lavora in periferia.
2. **Comportamento Strategico:** Gli utenti, agendo come agenti economici razionali (o tentando di farlo), potrebbero dichiarare costi gonfiati per massimizzare il proprio profitto a spese dell'efficienza globale.
3. **Vincoli di Budget:** La piattaforma opera con risorse finanziarie limitate e deve massimizzare l'utilità dei dati raccolti rispettando vincoli di bilancio.[9][10]

Per risolvere queste criticità, Yang et al. hanno proposto il meccanismo **IMCU (Incentive Mechanism for Crowdsensing Users)**, basato sulla teoria delle aste inverse (*Reverse Auctions*), che garantisce proprietà teoriche fondamentali come la Veridicità (*Truthfulness*) e la Razionalità Individuale. Tuttavia, la letteratura esistente si concentra prevalentemente su analisi teoriche o simulazioni in ambienti semplificati, trascurando le complessità comportamentali degli utenti reali. Questo lavoro affronta una domanda fondamentale: **in che misura le performance del meccanismo IMCU si mantengono quando il parametro di configurazione (raggio di copertura dei task) viene variato, e quali trade-off emergono tra efficienza economica e inclusività della partecipazione?**[10]

## 1.3. Obiettivi e Delimitazione della Tesi
Questo lavoro integra competenze di ingegneria del software, teoria dei giochi ed economia comportamentale. L'obiettivo principale è valutare quanto i meccanismi teorici di incentivazione mantengano le loro proprietà in scenari operativi reali, caratterizzati da parametri di configurazione che influenzano significativamente le dinamiche competitive.

È necessario definire i confini della ricerca. Sebbene la privacy e la sicurezza dei dati siano temi critici per l'MCS, questo lavoro non sviluppa tecniche crittografiche (come la privacy differenziale o la crittografia omomorfica). La privacy viene modellata implicitamente nel costo $c_i$ sostenuto dall'utente: assumiamo che gli utenti richiedano un compenso maggiore per task che espongono dati più sensibili (ad esempio, tracce GPS in zone residenziali rispetto a strade pubbliche). Questa astrazione economica permette di concentrarsi sulla dinamica di incentivazione senza affrontare le tecniche crittografiche, che costituirebbero un lavoro separato. L'attenzione è focalizzata esclusivamente sulla dinamica economica e algoritmica dell'allocazione dei task.

Questo lavoro si articola in **tre fasi sperimentali**, che corrispondono alle tre parti della struttura della tesi:

- **Fase 1 (Parte I - Capitoli 3-6): Validazione della Baseline Teorica**
- **Fase 2 (Parte II - Capitolo 7): Analisi della Robustezza alla Razionalità Limitata**
- **Fase 3 (Parte III - Capitolo 8): Progettazione di un Meccanismo Adattivo (GAP)**

Le sottosezioni seguenti descrivono in dettaglio ciascuna fase sperimentale.

### Fase 1: Validazione della Baseline Teorica
In questa prima fase, abbiamo progettato e implementato un simulatore MCS completo, calibrato su un dataset reale di mobilità taxi nella città di Roma (febbraio 2014, oltre 300 taxi tracciati). L'obiettivo è riprodurre fedelmente il meccanismo IMCU assumendo una popolazione di agenti a **razionalità perfetta**.

È opportuno chiarire operativamente il concetto di *razionalità perfetta* nel contesto della simulazione. Nel nostro caso, significa che ogni utente $i$ sottomette un bid $b_i$ esattamente uguale al proprio costo reale $c_i$. Questo rappresenta il comportamento di equilibrio previsto dalla teoria dei giochi quando tutti gli altri utenti agiscono razionalmente e il meccanismo è *truthful*: in queste condizioni, dire la verità sul proprio costo diventa la strategia dominante.

È importante sottolineare che in questa fase **non stiamo dimostrando** che gli utenti *scelgono spontaneamente* di essere veritieri — questo è già garantito teoricamente dalle proprietà del meccanismo IMCU[10]. Piuttosto, l'obiettivo è **validare empiricamente** che, *dato* il comportamento di equilibrio ($b_i = c_i$), il meccanismo mantiene le proprietà di Individual Rationality (nessun utente opera in perdita: $p_i \geq b_i$) e Profitability (la piattaforma non va in perdita: $u_0 \geq 0$).

Un aspetto metodologico rilevante di questa fase è l'analisi dell'impatto del parametro *raggio di copertura* dei task sull'efficienza del sistema. Attraverso tre configurazioni sperimentali (raggio 1.5 km, 2.5 km, 4.0 km), abbiamo quantificato empiricamente i trade-off che emergono: l'aumento del raggio incrementa l'efficienza economica ma riduce drasticamente il numero di partecipanti selezionati, con implicazioni significative per la sostenibilità sociale della piattaforma.

I risultati di questa fase costituiscono la baseline di riferimento per le fasi successive.

### Fase 2: Analisi della Robustezza alla Razionalità Limitata
Nella seconda fase introduciamo un elemento di realismo comportamentale ispirato alla teoria della *Bounded Rationality* di Herbert Simon. La letteratura sulla mobilità urbana documenta ampiamente che i tassisti, pur essendo professionisti esperti, adottano euristiche semplificate piuttosto che ottimizzazioni matematiche perfette nella scelta delle corse. Questa osservazione solleva una questione metodologica rilevante: se i tassisti manifestano comportamenti subottimali nelle operazioni quotidiane, è ragionevole assumere che adottino strategie perfettamente razionali in un contesto MCS?[11]

Gli agenti della Fase 2 presentano profili comportamentali eterogenei:
- **Errori nella stima dei costi** (sottostima o sovrastima sistematica delle distanze)
- **Euristiche decisionali semplificate** (strategie "sufficientemente buone" piuttosto che ottimali)
- **Comportamenti opportunistici non ottimali** (tentativi di manipolazione maldestri del sistema)

L'obiettivo proposto è quantificare, attraverso metriche rigorose, il deterioramento dell'efficienza del meccanismo IMCU quando le assunzioni di perfetta razionalità vengono meno. L'ipotesi è che questo deterioramento non sia trascurabile, dimostrando la fragilità dei modelli teorici classici in contesti reali.

### Fase 3: Progettazione di un Meccanismo Adattivo (GAP)
Per affrontare le criticità della Fase 2, la Fase 3 propone lo sviluppo di un nuovo meccanismo algoritmico denominato **Game-theoretic Adaptive Policy (GAP)**. Il meccanismo GAP si basa sull'apprendimento dinamico dei pattern comportamentali degli utenti per adattare le strategie di selezione e incentivazione.

Invece di assumere che tutti gli utenti siano razionali (Fase 1) o constatare passivamente che non lo sono (Fase 2), GAP stima in tempo reale i profili comportamentali individuali — reputazione, affidabilità, pattern di bidding — e ricalibrare le regole dell'asta di conseguenza. L'obiettivo proposto per la Fase 3 è ripristinare l'efficienza e la stabilità del sistema anche in presenza di utenti con razionalità limitata.

Sebbene le Fasi 2 e 3 costituiscano estensioni future del lavoro, la metodologia sperimentale sviluppata nella Fase 1 fornisce le basi per una valutazione rigorosa di tale approccio.

La Tabella 1.1 sintetizza le tre fasi sperimentali, evidenziando gli obiettivi, le assunzioni comportamentali e le metriche chiave.

| **Fase** | **Capitoli** | **Assunzione Utenti** | **Obiettivo** | **Metriche Chiave** |
| :---: | :---: | :---: | :---: | :---: |
| **Fase 1: Baseline** | 3-6 | Razionalità perfetta<br>($b_i = c_i$) | Validazione empirica proprietà IMCU su dati reali | Efficienza $u_0/v(S)$<br>Profitability<br>Gini index |
| **Fase 2: Bounded Rationality** | 7 | Razionalità limitata<br>(errori stima, euristiche) | Valutazione del calo di efficienza con comportamenti realistici | Tasso rottura contratti<br>Efficienza realizzata<br>Robustezza |
| **Fase 3: GAP Adattivo** | 8 | Eterogenei<br>(razionali + limitati) | Ripristino efficienza tramite apprendimento e adattamento | Recovery rate<br>Convergenza<br>Overhead computazionale |

*Tabella 1.1: Sintesi delle tre fasi sperimentali della tesi.*

## 1.4. Contributi Innovativi
I principali contributi di questo lavoro sono:

**Framework di Simulazione Data-Driven:** A differenza della maggior parte della letteratura MCS, che si basa su simulazioni con dati sintetici o scenari semplificati, questo lavoro ha sviluppato un ambiente di simulazione che integra dati di mobilità reale (tracce GPS di taxi romani), topologia urbana effettiva e modelli economici calibrati su dati storici (costi operativi taxi Roma 2014). Il dataset copre 316 veicoli tracciati per 28 giorni consecutivi (febbraio 2014), generando circa 11 milioni di punti GPS su un'area di oltre 1200 km². La validazione in un contesto urbano complesso come Roma — caratterizzato da traffico congestionato, ZTL nel centro storico e topologia stradale irregolare — fornisce evidenze quantitative dell'applicabilità operativa del meccanismo in scenari reali, colmando un significativo gap metodologico nella letteratura esistente.

**Quantificazione dell'Impatto del Raggio di Copertura:** Attraverso una campagna sperimentale sistematica su dati di mobilità reale, questo lavoro fornisce la prima quantificazione empirica dell'impatto del parametro di configurazione *raggio di copertura* sulle performance di un'asta inversa MCS. I risultati della Fase 1 (Sezione 6.3) evidenziano trade-off rilevanti: l'aumento del raggio da 1.5 km a 4.0 km porta a un incremento dell'efficienza economica del 12% (da 54.85% a 61.37%), al prezzo però di una drastica contrazione della partecipazione(da 280 a 100 vincitori), con implicazioni significative per la sostenibilità sociale della piattaforma. Questa quantificazione empirica colma un gap nella letteratura, che spesso assume configurazioni arbitrarie senza analizzarne sistematicamente l'impatto sulle dinamiche competitive. I risultati stabiliscono una baseline quantitativa contro cui misurare il degrado prestazionale indotto dalla razionalità limitata nella Fase 2.

**Approccio Adattivo GAP (Proposto):** L'approccio adattivo proposto non richiede assunzioni rigide sul comportamento degli utenti, ma stima dinamicamente i loro profili per ottimizzare le decisioni allocative. È un approccio pragmatico: non cerchiamo il meccanismo perfetto che funziona con qualsiasi tipo di utente, ma progettiamo un sistema che apprende dai comportamenti osservati e si adatta di conseguenza.

## 1.5. Organizzazione dell'Elaborato
La tesi è organizzata secondo una struttura tripartita che riflette il metodo scientifico sperimentale: dalla teoria alla validazione empirica, dall'analisi dei limiti alla proposta di soluzioni adattive.

- Il **Capitolo 2** fornisce una panoramica approfondita dello stato dell'arte sui meccanismi di incentivazione per Mobile Crowdsensing e i fondamenti teorici necessari per comprendere il lavoro. Include: (i) fondamenti di teoria dei giochi applicati al MCS (equilibrio di Nash, strategie dominanti, giochi di Stackelberg); (ii) meccanismi di incentivazione (aste inverse, meccanismo VCG, IMCU); (iii) sfide operative nel MCS reale (qualità dei dati, privacy, consumo energetico); (iv) modelli di razionalità limitata (*bounded rationality*, *fast-and-frugal trees*); (v) funzioni submodulari e algoritmi greedy; (vi) modelli di costo e routing. Conclude identificando i gap metodologici nella letteratura che motivano questo lavoro.
- Il **Capitolo 3** definisce formalmente il modello matematico del sistema, descrivendo le entità fondamentali (Task e Utenti), le funzioni di costo e le assunzioni economiche di base. Vengono introdotte le definizioni rigorose dei parametri economici (valore dei task, costo operativo utenti) e formalizzate le strategie di bidding in regime di razionalità perfetta. Viene inoltre giustificata la scelta metodologica dello *star routing* per il calcolo dei costi multi-task — una semplificazione conservativa rispetto al routing ottimale (TSP) che sovrastima i costi ma garantisce robustezza del meccanismo e trattabilità computazionale.
- Il **Capitolo 4** analizza in dettaglio il meccanismo IMCU *User-Centric*, formalizzando i due algoritmi fondamentali: la selezione greedy dei vincitori (basata sul guadagno marginale netto) e la determinazione dei pagamenti critici (critical payment computation). Vengono dimostrate le proprietà teoriche del meccanismo (efficienza computazionale, razionalità individuale, profittabilità, veridicità) e discusse le garanzie di approssimazione $$(1-1/e)$$ per problemi NP-hard.
- Il **Capitolo 5** illustra la metodologia sperimentale adottata per la Fase 1. Descrive il dataset CRAWDAD `roma/taxi`, il processo ETL (estrazione, pulizia, partizionamento), la discretizzazione dello spazio geografico mediante griglia regolare a 500 metri, e le tecniche per la generazione sintetica della domanda (task spaziali derivati dalla densità GPS) e dell'offerta (utenti disponibili estratti dai dati reali). Viene inoltre dettagliato il modello di assegnazione task agli utenti via prossimità geografica e la calibrazione del parametro *raggio di copertura* (1.5 km, 2.5 km, 4.0 km).
- Il **Capitolo 6** presenta i risultati sperimentali della Fase 1, validando empiricamente le proprietà teoriche del meccanismo IMCU in condizioni di razionalità perfetta. L'analisi quantifica le performance economiche del sistema (efficienza, utilità della piattaforma, distribuzione pagamenti) e studia sistematicamente l'impatto del parametro *raggio di copertura* sull'efficienza complessiva, evidenziando trade-off rilevanti tra massimizzazione del valore e inclusività della partecipazione (analisi Gini, clustering K-Means).
- I **capitoli 7-8** rappresenteranno rispettivamente la Fase 2 e la Fase 3, le quali estenderanno tale analisi introducendo modelli realistici di razionalità limitata (errori di stima, strategie subottimali, comportamenti opportunistici) per quantificare il deterioramento dell'efficienza, e proponendo un meccanismo adattivo GAP (Game-theoretic Adaptive Policy) basato su apprendimento multi-agente per ripristinare stabilità ed efficienza in presenza di utenti eterogenei.
- Il **Capitolo 9** riassumerà i risultati ottenuti, discuterà le implicazioni pratiche per la progettazione di futuri sistemi di crowdsensing e delineerà possibili direzioni di ricerca future, includendo l'estensione a finestre temporali multi-giorno, l'integrazione di modelli di routing ottimale, e l'applicazione a domini diversi dal trasporto urbano.

## Riferimenti bibliografici
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