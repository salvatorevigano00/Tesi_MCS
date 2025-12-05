# Capitolo 3: Modello Matematico del Sistema e degli Agenti

## 3.1. Introduzione al Modello Computazionale

La validazione empirica di un meccanismo di incentivazione richiede innanzitutto una definizione formale dell'ambiente in cui esso opera e degli agenti che vi interagiscono. In questa tesi, si adotta il modello **User-Centric** proposto da Yang et al.[10], adattandolo però a uno scenario realistico di mobilità urbana basato su flussi di taxi nella città di Roma.[12]

Il sistema è modellato come un mercato elettronico (*e-market*) composto da tre entità principali:

1. La **Piattaforma (Crowdsourcer)**: L'ente che richiede dati di sensing e gestisce l'asta inversa per allocare i task agli utenti.
2. I **Task** ($\mathcal{T}$): L'insieme delle richieste di acquisizione dati, caratterizzate da valore economico e posizione geografica.
3. Gli **Utenti** ($\mathcal{U}$): La popolazione di agenti mobili (tassisti) che offrono servizi di sensing in cambio di una compensazione monetaria.

Questo capitolo formalizza le proprietà di queste entità, le relazioni tra di esse e le assunzioni comportamentali che governano le decisioni degli agenti, fornendo le definizioni formali necessarie per l'algoritmo IMCU descritto nel Capitolo 4.

## 3.2 L'Entità Task: Formalizzazione della Domanda

Un task di sensing rappresenta l'unità atomica di domanda all'interno del sistema. Diversamente da molti modelli teorici basati su grafi sintetici, in questo lavoro ogni task è ancorato a coordinate geospaziali specifiche derivate dall'analisi del dataset taxi Roma.

**Definizione 3.1 (Task di Sensing)** Un task $\tau_j$ è definito dalla tupla:
$$
\tau_j = \langle id_j, \text{pos}_j, \nu_j \rangle
$$
dove:
- $id_j \in \mathbb{N}^+$ è un identificatore univoco.
- $\text{pos}_j = (\phi_j, \lambda_j)$ rappresenta le coordinate geografiche (latitudine, longitudine) nel sistema di riferimento WGS84 (EPSG:4326).
- $\nu_j \in \mathbb{R}^+_0$ è il **valore** (*valuation*) del task, che quantifica l'utilità marginale che la piattaforma ottiene dal completamento di $\tau_j$.

**Definizione 3.2 (Distribuzione del Valore dei Task)** Il valore $\nu_j$ di un task è modellato come una variabile aleatoria con distribuzione **uniforme** nel range $[\nu_{\min}, \nu_{\max}]$. La funzione di densità di probabilità (PDF) è data da:

$$
f(\nu) = \begin{cases} 
\frac{1}{\nu_{\max} - \nu_{\min}} & \text{se } \nu \in [\nu_{\min}, \nu_{\max}] \\
0 & \text{altrimenti}
\end{cases}
$$

Per la Fase 1, i parametri sono stati calibrati empiricamente per bilanciare l'economia del sistema con i costi operativi realistici dei taxi:
$$
\begin{aligned}
\nu_{\min} &= 1.8 \text{ €} \\
\nu_{\max} &= 15.0 \text{ €}
\end{aligned}
$$

Questa scelta garantisce che il valore medio atteso $\mathbb{E}[V] = \frac{1.8\ € + 15.0\ €}{2} = 8.4$ € sia superiore al costo medio di spostamento stimato (circa 5.75 € per 5 task a 2 km con $\kappa = 0.575$ €/km), rendendo economicamente vantaggiosa la partecipazione degli utenti. Il rapporto $\mathbb{E}[V]/\text{costo medio} \approx 1.46$ garantisce una **margine di profittabilità** sufficiente per incentivare la partecipazione anche considerando la variabilità dei costi individuali. La distribuzione uniforme mantiene la **comparabilità metodologica** con la baseline teorica di Yang et al., pur con parametri adattati al contesto taxi Roma[10].

## 3.3. L'Entità Utente: L'Agente Razionale

Gli utenti sono modellati come agenti economici autonomi dotati di razionalità (perfetta in Fase 1, limitata nelle fasi successive). Nel contesto di questa sperimentazione, essi corrispondono ai tassisti operanti nell'area metropolitana di Roma, come documentato nel dataset di mobilità utilizzato.[12]

**Definizione 3.3 (Utente/Agente)** Un utente $u_i$ è definito dalla tupla:
$$
u_i = \langle id_i, \text{pos}_i, \kappa_i, \Gamma_i \rangle
$$
dove:
- $id_i \in \mathbb{N}^+$ è un identificatore univoco.
- $\text{pos}_i \in \mathbb{R}^2$ sono le coordinate geografiche proiettate della sua posizione iniziale (ultima posizione registrata nel dataset).
- $\kappa_i \in \mathbb{R}^+$ è il **costo operativo per chilometro** (€/km), un parametro privato che rappresenta il costo marginale sostenuto dall'utente per ogni chilometro percorso.
- $\Gamma_i \subseteq \mathcal{T}$ è il **bundle di task** (insieme di task ammissibili) che l'utente $i$ può considerare per l'esecuzione, determinato dal vincolo di raggio di copertura.

Il parametro $\kappa_i$ cattura l'eterogeneità della flotta di agenti, includendo consumo di carburante, costi di manutenzione, ammortamento del veicolo e oneri fiscali. Sulla base dell'analisi dei costi operativi del trasporto pubblico non di linea nella città di Roma (anno di riferimento 2014), $\kappa_i$ è modellato come una variabile aleatoria estratta da una distribuzione uniforme:

$$
\kappa_i \sim \mathcal{U}[0.45, 0.70] \text{ €/km}
$$

Questo range riflette la variabilità reale tra veicoli più efficienti (es. motorizzazioni diesel Euro 5) e veicoli meno efficienti (es. motorizzazioni benzina più datate).

**Nota:** L'insieme $\Gamma_i$ non è un parametro intrinseco dell'utente, ma viene **determinato dinamicamente** in base alla prossimità geografica tra l'utente e i task disponibili. La formalizzazione precisa di questo processo di assegnazione è descritta nella Sezione 5.7 (Capitolo 5), dove viene introdotto il **vincolo di raggio di copertura** $r$ che limita i task ammissibili a quelli entro una distanza massima dalla posizione dell'utente.

## 3.4. Modello di Costo e Strategie di Bidding

Il comportamento dell'agente si basa sulla valutazione del costo per l'esecuzione di un insieme di task e sulla conseguente formulazione di un'offerta (bid) da sottomettere alla piattaforma.

### 3.4.1. Funzione di Costo Privato ($c_i$)

Il costo privato $c_i$ per un utente $i$ che si impegna a completare un insieme di task $\Gamma_i$ è direttamente proporzionale alla distanza totale stimata per visitare i task.

**Definizione 3.4 (Funzione di Costo Privato)** Il costo $c_i$ per l'utente $u_i$ per servire l'insieme di task $\Gamma_i$ è definito come:
$$
c_i(\Gamma_i) = \kappa_i \cdot D_i(\Gamma_i)
$$
dove $D_i(\Gamma_i)$ è la distanza totale di servizio stimata.

Per questa fase teorica, si adotta un modello di routing semplificato denominato **Star Routing**, dove si assume che l'utente parta dalla sua posizione base $\text{pos}_i$ per servire ogni task in $\Gamma_i$ individualmente.

**Definizione 3.5 (Distanza di Servizio con Correzione Urbana)** La distanza totale $D_i(\Gamma_i)$ è calcolata come la somma delle distanze geodetiche tra la posizione dell'utente e ciascun task, corretta da un fattore di tortuosità urbano:

$$
D_i(\Gamma_i) = \eta_{\text{urban}} \cdot \sum_{\tau_j \in \Gamma_i} d_H(\text{pos}_i, \text{pos}_j)
$$

dove:
- $d_H(\cdot, \cdot)$ è la **distanza geodetica di Haversine**, che calcola la distanza ortodromica tra due punti su una superficie sferica (raggio Terra $R = 6{,}371$ km):
  $$
  a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_i)\cos(\phi_j)\sin^2\left(\frac{\Delta\lambda}{2}\right)
  $$
  $$
  d_H = 2R \cdot \text{atan2}(\sqrt{a}, \sqrt{1-a})
  $$
- $\eta_{\text{urban}}$ è il **fattore di correzione urbano**. Studi empirici sulle reti stradali urbane indicano che la distanza stradale effettiva è superiore alla distanza geodetica a causa della topologia urbana (strade non rettilinee, sensi unici, ostacoli). Per la città di Roma, caratterizzata da un centro storico con viabilità complessa, è stato adottato un fattore conservativo $\eta_\text{urban} = 1.30$. Questo valore è coerente con range tipici per reti stradali urbane europee (1.2-1.4) documentati in letteratura per città con topologia irregolare[13], e rappresenta una stima conservativa che tiene conto della tortuosità media delle strade romane, caratterizzate da un sistema viario misto radiale-anulare con centro storico irregolare.

La Figura 3.1 illustra graficamente la differenza tra i due approcci di routing: nel modello star (A), l'utente parte dalla posizione base per raggiungere ogni task individualmente, mentre nel TSP ottimale (B) l'utente percorre un tour che minimizza la distanza totale.

![Figura 3.1: Confronto tra il modello Star Routing adottato (A) e un routing ottimale TSP (B). Nel modello Star, l'utente parte dalla posizione base (cerchio blu) per raggiungere ogni task (stelle rosse) individualmente, sovrastimando la distanza totale rispetto a un tour ottimizzato. Questa sovrastima garantisce che i costi calcolati siano un limite superiore conservativo ("upper bound"), preservando la proprietà di Individual Rationality anche in presenza di routing subottimale nella pratica.](./Immagini/figura_3_1_confronto_routing_star_vs_tsp.jpg)

**Nota sulle Limitazioni del Star Routing:**

Il modello di star routing utilizzato è una **semplificazione conservativa** rispetto al routing ottimale (Traveling Salesman Problem, TSP). Questa scelta metodologica comporta una sovrastima sistematica dei costi. La letteratura su algoritmi di approssimazione TSP indica che il routing stella sovrastima le distanze rispetto al tour ottimale con fattori tipici di 2-4× per cluster di 3-8 nodi, dipendendo dalla configurazione spaziale.

**Impatto sul meccanismo IMCU:**

1. **Bid più alti** → selezione più conservativa (numero di vincitori ridotto rispetto a routing ottimale)
2. **Pagamenti critici mai sottostimati** → Proprietà di Individual Rationality garantita anche in caso di routing subottimale nella realtà
3. **Efficienza complessiva ridotta**, ma **robustezza aumentata** (sistema fail-safe)

**Giustificazione della scelta:**

L'implementazione di un modulo di routing ottimale richiederebbe algoritmi di approssimazione TSP con complessità computazionale elevata. In assenza di tale modulo, l'algoritmo star routing garantisce che nessun utente operi in perdita anche se adotta un percorso subottimale nella pratica. Questo trade-off efficienza/robustezza è critico per la validazione delle proprietà teoriche in Fase 1: si preferisce un sistema che **garantisce formalmente** la proprietà di Individual Rationality (nessun utente opera in perdita) piuttosto che uno teoricamente più efficiente ma potenzialmente instabile in presenza di routing subottimale nella pratica.

La letteratura sulla mobilità taxi documenta inoltre che i percorsi reali spesso deviano dalle rotte ottimali a causa di vincoli di traffico, preferenze del conducente e opportunità di corse intermedie. Il modello star routing, pur sovrastimando le distanze, rappresenta quindi una approssimazione conservativa più vicina al comportamento effettivo rispetto a un TSP ideale che assumerebbe perfetta ottimizzazione.

### 3.4.2. Strategia di Bidding in Regime di Razionalità Perfetta

La Fase 1 dello studio si fonda sull'assunzione di **Razionalità Perfetta**. Gli agenti conoscono perfettamente le regole del meccanismo d'asta IMCU e agiscono strategicamente per massimizzare la propria utilità attesa.

Il meccanismo IMCU è progettato per essere **Incentivo-Compatibile in Strategie Dominanti (DSIC)**, o *truthful*.

**Teorema 3.1 (Veridicità del Meccanismo IMCU - da Yang et al.)**
*In un'asta IMCU user-centric, per qualsiasi utente $i$ con costo privato $c_i(\Gamma_i)$ per servire un insieme di task $\Gamma_i$, la strategia di sottomettere un'offerta (bid) veritiera $b_i = c_i(\Gamma_i)$ è una **strategia dominante**. Ciò significa che tale strategia massimizza l'utilità dell'utente $i$ indipendentemente dalle offerte sottomesse da tutti gli altri utenti.*

**Dimostrazione.** Dimostriamo il teorema in tre passi: (1) definizione della regola di pagamento critico, (2) analisi delle deviazioni dalla strategia veritiera, (3) dimostrazione che nessuna deviazione può migliorare l'utilità attesa.

**Passo 1: Regola di Pagamento Critico.** Nel meccanismo IMCU, se l'utente $i$ viene selezionato come vincitore, il pagamento $p_i$ che riceve non è semplicemente uguale al suo bid $b_i$, ma è determinato dal **valore critico** (*critical payment*), definito come il minimo valore che l'utente $i$ avrebbe dovuto dichiarare per essere comunque selezionato dato l'insieme delle offerte degli altri utenti.

Formalmente, sia $S^*$ l'insieme dei vincitori selezionati dall'algoritmo greedy (descritto nel Capitolo 4) quando l'utente $i$ dichiara $b_i$. Il pagamento critico $p_i$ è definito come:
$$
p_i = \min\{b'_i : i \in S^*(b'_i, \mathbf{b}_{-i})\}
$$
dove $\mathbf{b}_{-i}$ denota il vettore delle offerte di tutti gli utenti escluso $i$, e $S^*(b'_i, \mathbf{b}_{-i})$ è l'insieme dei vincitori quando $i$ dichiara $b'_i$.[10]

**Proprietà chiave:** Per costruzione dell'algoritmo greedy basato sul marginal value, vale sempre:
$$
p_i \geq b_i \text{ se } i \in S^*
$$
Questo perché il valore critico rappresenta la "soglia di competitività" dell'utente $i$.

**Passo 2: Analisi delle Deviazioni - Overbidding.** Supponiamo che l'utente $i$ dichiari $b_i > c_i$ (sovrastima del costo). Consideriamo due casi:

*Caso 2a:* $i$ viene selezionato con $b_i > c_i$.  
In questo caso, l'utilità è:
$$
u_i = p_i - c_i
$$
Ma se avesse dichiarato $b_i = c_i$, avrebbe ottenuto la stessa utilità (perché $p_i$ dipende solo dalle offerte degli altri e dalla soglia critica, non dal valore esatto di $b_i$ finché $b_i \leq p_i$). Quindi: **nessun guadagno** dall'overbidding quando si vince.

*Caso 2b:* $i$ non viene selezionato con $b_i > c_i$, ma sarebbe stato selezionato con $b_i = c_i$.  
Questo accade quando $c_i < p_i < b_i$. In questo caso:
- Con bid veritiero: $u_i = p_i - c_i > 0$ (utilità positiva)
- Con overbidding: $u_i = 0$ (non selezionato)

Quindi: **perdita di utilità** dall'overbidding.

**Passo 3: Analisi delle Deviazioni - Underbidding.** Supponiamo che l'utente $i$ dichiari $b_i < c_i$ (sottostima del costo). Consideriamo due casi:

*Caso 3a:* $i$ non viene selezionato con $b_i < c_i$.  
In questo caso $u_i = 0$, identico al caso veritiero se il vero costo $c_i$ avrebbe comunque escluso $i$. **Nessun guadagno** dall'underbidding quando non si vince.

*Caso 3b:* $i$ viene selezionato con $b_i < c_i$, ma non sarebbe stato selezionato con $b_i = c_i$.  
Questo accade quando $b_i < p_i < c_i$. In questo caso:
- Con underbidding: $u_i = p_i - c_i < 0$ (utilità negativa!)
- Con bid veritiero: $u_i = 0$ (non selezionato)

Quindi: **perdita di utilità** (addirittura negativa) dall'underbidding.

**Conclusione:** In tutti i casi analizzati, la deviazione dalla strategia veritiera $b_i = c_i$ porta a un'utilità attesa debolmente inferiore (o uguale nel caso migliore) rispetto alla strategia veritiera. Pertanto, $b_i = c_i$ è una **strategia debolmente dominante**, e in assenza di tie-breaking patologici, è una **strategia dominante stretta**[14].

**Corollario 3.1 (Comportamento di Bidding Assunto in Fase 1)** *Data l'assunzione di razionalità perfetta e il Teorema 3.1, il modello di comportamento per ogni utente $u_i$ nella Fase 1 impone che l'offerta sottomessa alla piattaforma sia identica al suo costo privato calcolato:*
$$
b_i(\Gamma_i) = c_i(\Gamma_i)
$$

**Dimostrazione.** Per definizione di razionalità perfetta, ogni agente:
1. Conosce la propria funzione di utilità $u_i(b_i, \mathbf{b}_{-i})$
2. Conosce le regole del meccanismo (inclusa la regola di pagamento critico)
3. Ha capacità computazionale illimitata per calcolare la strategia ottimale

Dal Teorema 3.1, sappiamo che $b_i = c_i$ è una strategia dominante. Per definizione di strategia dominante, questa è la migliore risposta indipendentemente dalle strategie degli altri giocatori. Un agente perfettamente razionale non ha alcun incentivo a deviare da una strategia dominante.

Formalmente, sia $U_i(b_i | \mathbf{b}_{-i})$ l'utilità attesa dell'utente $i$ data la strategia $b_i$ e le strategie degli altri utenti $\mathbf{b}_{-i}$. Dal Teorema 3.1:
$$
U_i(c_i | \mathbf{b}_{-i}) \geq U_i(b'_i | \mathbf{b}_{-i}) \quad \forall b'_i \neq c_i, \, \forall \mathbf{b}_{-i}
$$

Quindi, l'unica strategia consistente con la razionalità perfetta è $b_i = c_i$. Questa uguaglianza costituisce la **Ground Truth** comportamentale della Fase 1 (descritto nel Capitolo 5): non stiamo dimostrando empiricamente che gli utenti *scelgono* di essere veritieri (questo è già garantito teoricamente), ma piuttosto stiamo **simulando l'equilibrio di Nash** del gioco assumendo che tutti gli agenti abbiano già convergito al comportamento ottimale.

### 3.4.3. Funzione di Utilità dell'Agente

L'utilità di un agente è il guadagno netto ottenuto dalla partecipazione all'asta, dopo aver sottratto il costo sostenuto dal pagamento ricevuto.

**Definizione 3.6 (Utilità dell'Utente)** L'utilità $u_i$ per l'utente $u_i$ è definita come funzione quasi-lineare:
$$
u_i = \begin{cases} 
p_i - c_i(\Gamma_i) & \text{se } u_i \in S^* \text{ (vincitore)} \\
0 & \text{se } u_i \notin S^* \text{ (non vincitore)}
\end{cases}
$$
dove $p_i$ è il pagamento ricevuto dalla piattaforma e $S^*$ è l'insieme dei vincitori selezionati.

**Assunzione 3.1 (Utilità di Riserva Nulla)** Si assume che l'utilità di riserva di ogni utente (il payoff che ottiene non partecipando all'asta) sia pari a zero. Questa è un'assunzione standard nei meccanismi di crowdsensing, che riflette il fatto che gli utenti non sostengono costi se non vengono selezionati.

Il meccanismo d'asta deve garantire la **Razionalità Individuale** per essere sostenibile a lungo termine.

**Proposizione 3.2 (Razionalità Individuale del Meccanismo IMCU)** *Un meccanismo d'asta è individualmente razionale (IR) se l'utilità di ogni partecipante è non negativa, ovvero $u_i \geq 0$ per ogni utente $i$. Il meccanismo IMCU soddisfa questa proprietà per costruzione.*

**Dimostrazione.** Dobbiamo dimostrare che $u_i \geq 0$ per ogni utente $i$, sia esso vincitore o meno.

**Caso 1: Utente non selezionato ($i \notin S^*$).** Per definizione (Definizione 3.6), $u_i = 0 \geq 0$.

**Caso 2: Utente selezionato ($i \in S^*$).** Per un utente selezionato, l'utilità è:
$$
u_i = p_i - c_i
$$

Dalla proprietà della regola di pagamento critico dimostrata nel Teorema 3.1 (Passo 1), sappiamo che:
$$
p_i \geq b_i
$$
per ogni vincitore $i$.

Inoltre, dal Corollario 3.1, in regime di razionalità perfetta (Fase 1), ogni utente dichiara $b_i = c_i$. Quindi:
$$
p_i \geq b_i = c_i
$$

Sostituendo nella funzione di utilità:
$$
u_i = p_i - c_i \geq c_i - c_i = 0
$$

Quindi $u_i \geq 0$ per ogni vincitore.

**Conclusione:** In entrambi i casi (vincitore e non vincitore), l'utilità di ogni partecipante è non negativa. Pertanto, il meccanismo IMCU soddisfa la proprietà di **Individual Rationality**, garantendo che nessun agente razionale ha incentivo a non partecipare all'asta.[10][14]

**Corollario 3.2 (Condizione di Partecipazione Volontaria)** *Data la proprietà di Individual Rationality (Proposizione 3.2) e l'utilità di riserva nulla (Assunzione 3.1), ogni utente razionale ha un incentivo debole (o nullo nel caso peggiore) a partecipare all'asta IMCU.*

**Dimostrazione.** Sia $U_i^{\text{partecipa}}$ l'utilità attesa dell'utente $i$ se partecipa all'asta, e $U_i^{\text{non partecipa}} = 0$ l'utilità se non partecipa (Assunzione 3.1).

Dalla proposizione 3.2, sappiamo che:
$$
U_i^{\text{partecipa}} \geq 0
$$

Quindi:
$$
U_i^{\text{partecipa}} \geq 0 = U_i^{\text{non partecipa}}
$$

Un agente razionale che massimizza l'utilità attesa sceglierà quindi di partecipare, poiché nel caso peggiore ottiene la stessa utilità del non partecipare ($u_i = 0$ se non viene selezionato), mentre nel caso migliore ottiene un'utilità strettamente positiva ($u_i > 0$ se viene selezionato con $p_i > c_i$).

Questa proposizione giustifica l'assunzione che tutti gli utenti disponibili (identificati nel dataset taxi Roma) partecipino all'asta sottomettendo le proprie offerte: non c'è alcun rischio di perdita, quindi la partecipazione è sempre razionale.

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