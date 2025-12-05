# Capitolo 4: Il Meccanismo d'Asta IMCU User-Centric

## 4.1. Introduzione al Framework di Allocazione

In uno scenario di Mobile Crowdsensing *User-Centric*, la piattaforma non assegna direttamente i task agli agenti, ma gestisce un mercato elettronico in cui gli utenti competono per vendere le proprie risorse di sensing. Il problema di allocazione si configura come un'**asta inversa** (*reverse auction*), dove la piattaforma agisce come acquirente (*buyer*) unico e gli utenti come venditori (*sellers*) multipli.[10][14]

L'obiettivo della piattaforma è selezionare un sottoinsieme di utenti $S \subseteq \mathcal{U}$ tale da massimizzare la propria utilità, definita come la differenza tra il valore generato dai dati raccolti e il costo totale sostenuto per i pagamenti. Formalmente, il problema di ottimizzazione è:

$$
\max_{S \subseteq \mathcal{U}} u_0(S) = v(S) - \sum_{i \in S} p_i
$$

Tuttavia, la determinazione dei pagamenti $p_i$ è vincolata dalla necessità di incentivare la rivelazione veritiera dei costi privati. Il meccanismo utilizzato è **IMCU (Incentive Mechanism for Crowdsensing Users)**, proposto da Yang et al. Il meccanismo si articola in due fasi sequenziali algoritmiche: la **Selezione dei Vincitori** (*Winner Determination*) e la **Determinazione dei Pagamenti** (*Payment Determination*).[10]

Il meccanismo richiede che la funzione di valutazione della piattaforma $v: 2^\mathcal{U} \to \mathbb{R}^+$ sia **monotona** e **submodulare**. La funzione di copertura dei task adottata in questo studio (descritta nel Capitolo 5) soddisfa tali proprietà, garantendo la validità teorica degli algoritmi di approssimazione utilizzati.[16]

## 4.2. Proprietà Fondamentali delle Funzioni di Valutazione

Prima di descrivere gli algoritmi IMCU, formalizziamo le proprietà matematiche che garantiscono la correttezza e l'efficienza degli algoritmi greedy.

**Definizione 4.1 (Funzione Submodulare)** Una funzione $f: 2^\mathcal{U} \to \mathbb{R}$ definita sull'insieme delle parti di $\mathcal{U}$ è **submodulare** se per ogni $A \subseteq B \subseteq \mathcal{U}$ e per ogni elemento $x \in \mathcal{U} \setminus B$, vale la proprietà di **rendimento marginale decrescente**:

$f(A \cup \{x\}) - f(A) \geq f(B \cup \{x\}) - f(B)$

Dunque, l'incremento di valore ottenuto aggiungendo un elemento a un insieme piccolo è maggiore (o uguale) rispetto all'incremento ottenuto aggiungendo lo stesso elemento a un insieme più grande che contiene il primo.[16]

**Definizione 4.2 (Funzione Monotona)** Una funzione $f: 2^\mathcal{U} \to \mathbb{R}$ è **monotona non-decrescente** se per ogni $A \subseteq B \subseteq \mathcal{U}$:

$$
f(A) \leq f(B)
$$
Questa proprietà garantisce che aggiungere elementi all'insieme non diminuisca mai il valore della funzione.[16]

**Lemma 4.1 (Submodularità della Funzione di Valore della Piattaforma)** *La funzione di valore $v(S) = \sum_{j \in \bigcup_{i \in S} \Gamma_i} \nu_j$, dove $\Gamma_i$ è l'insieme dei task coperti dall'utente $i$, è submodulare e monotona non-decrescente.*

**Dimostrazione.** Consideriamo due insiemi di utenti $A \subseteq B \subseteq \mathcal{U}$ e un utente $x \in \mathcal{U} \setminus B$. Sia $T_A = \bigcup_{i \in A} \Gamma_i$ l'insieme dei task coperti da $A$, $T_B = \bigcup_{i \in B} \Gamma_i$ l'insieme dei task coperti da $B$, e $\Gamma_x$ l'insieme dei task coperti da $x$.

**Monotonicità:** Poiché $A \subseteq B$, abbiamo $T_A \subseteq T_B$. Quindi:

$$
v(A) = \sum_{j \in T_A} \nu_j \leq \sum_{j \in T_B} \nu_j = v(B)
$$

dato che tutti i $\nu_j \geq 0$ per definizione.

**Submodularità:** Il valore marginale di $x$ rispetto ad $A$ è:

$$
v(A \cup \{x\}) - v(A) = \sum_{j \in (T_A \cup \Gamma_x)} \nu_j - \sum_{j \in T_A} \nu_j = \sum_{j \in \Gamma_x \setminus T_A} \nu_j
$$

Analogamente, il valore marginale di $x$ rispetto a $B$ è:

$$
v(B \cup \{x\}) - v(B) = \sum_{j \in \Gamma_x \setminus T_B} \nu_j
$$

Poiché $T_A \subseteq T_B$, abbiamo $\Gamma_x \setminus T_B \subseteq \Gamma_x \setminus T_A$. Quindi:

$$
\sum_{j \in \Gamma_x \setminus T_B} \nu_j \leq \sum_{j \in \Gamma_x \setminus T_A} \nu_j
$$

Questo dimostra che $v(A \cup \{x\}) - v(A) \geq v(B \cup \{x\}) - v(B)$, verificando la submodularità.

## 4.3. Fase 1: Selezione dei Vincitori (Winner Determination)

Poiché il problema della massimizzazione dell'utilità con funzioni submodulari è noto essere NP-hard, IMCU adotta un approccio euristico di tipo *greedy* che offre garanzie di approssimazione computazionale.[16]

L'algoritmo costruisce iterativamente l'insieme dei vincitori $S$, partendo da un insieme vuoto. Ad ogni passo $k$, il meccanismo valuta il contributo potenziale di ogni utente $i \notin S$ ancora disponibile. Il criterio di selezione si basa sul **guadagno marginale netto**:

$$
\delta_i(S) = v(S \cup \{i\}) - v(S) - b_i
$$

dove $v(S \cup \{i\}) - v(S)$ rappresenta l'incremento di valore (o *valore marginale*) apportato dall'utente $i$ all'insieme corrente, e $b_i$ è l'offerta (*bid*) sottomessa dall'utente.

**Algoritmo 4.1: Selezione Greedy dei Vincitori**

**Input:** Insieme degli utenti $\mathcal{U} = \{u_1, u_2, \ldots, u_n\}$, ciascuno con bid $b_i$ e insieme di task $\Gamma_i$.

**Output:** Insieme dei vincitori $S \subseteq \mathcal{U}$.

1. **Inizializzazione:** $S \leftarrow \emptyset$, insieme dei candidati $C \leftarrow \mathcal{U}$, insieme dei task coperti $\mathcal{T}_{\text{covered}} \leftarrow \emptyset$.

2. **Mentre** $C \neq \emptyset$:

   a. Per ogni utente $i \in C$, calcolare il valore marginale:
   
   $$
   \text{mv}_i = \sum_{j \in \Gamma_i \setminus \mathcal{T}_{\text{covered}}} \nu_j
   $$
   
   b. Calcolare il guadagno marginale netto:
   
   $$
   \delta_i = \text{mv}_i - b_i
   $$
   
   c. Identificare l'utente $i^*$ che massimizza il guadagno:
   
   $$
   i^* = \arg \max_{i \in C} \delta_i
   $$
   
   In caso di pareggio ($\delta_i = \delta_j$), selezionare l'utente con ID minore (tie-breaking lessicografico).
   
   d. **Criterio di Arresto:** Se $\delta_{i^*} \leq 0$, terminare il processo e restituire $S$.
   
   e. Altrimenti:
   - Aggiornare $S \leftarrow S \cup \{i^*\}$
   - Aggiornare $\mathcal{T}_{\text{covered}} \leftarrow \mathcal{T}_{\text{covered}} \cup \Gamma_{i^*}$
   - Rimuovere $i^*$ dai candidati: $C \leftarrow C \setminus \{i^*\}$

3. **Return** $S$

**Teorema 4.1 (Garanzia di Approssimazione dell'Algoritmo Greedy)** *Sia $S^*$ l'insieme ottimale di vincitori che massimizza $u_0(S) = v(S) - \sum_{i \in S} b_i$, e sia $S_{\text{greedy}}$ l'insieme restituito dall'Algoritmo 4.1. Se la funzione $v$ è monotona e submodulare, allora:*

$$
u_0(S_{\text{greedy}}) \geq \left(1 - \frac{1}{e}\right) u_0(S^*)
$$

*dove $e$ è la base del logaritmo naturale ($e \approx 2.718$). Questo fornisce una garanzia di approssimazione del 63.2% rispetto alla soluzione ottimale.*

**Dimostrazione (Schema).** Questo risultato è una conseguenza diretta del teorema di Nemhauser, Wolsey e Fisher, che dimostra che un algoritmo greedy applicato a una funzione submodulare monotona fornisce un rapporto di approssimazione di almeno $(1 - 1/e)$.[16]

La dimostrazione si basa su due fatti chiave:

1. **Submodularità implica rendimento marginale decrescente:** Ad ogni iterazione, l'algoritmo seleziona l'elemento con il massimo guadagno marginale. La submodularità garantisce che i guadagni marginali non crescano mai, permettendo di limitare inferiormente il valore accumulato.

2. **Analisi del peggiore caso:** Si dimostra per induzione che dopo $k$ iterazioni, il valore accumulato soddisfa:

$$
v(S_k) \geq \left(1 - \left(1 - \frac{1}{|S^*|}\right)^k\right) v(S^*)
$$

Nel limite $k \to |S^*|$, si ottiene il fattore $(1 - 1/e)$.

**Complessità Computazionale:** L'Algoritmo 4.1 ha complessità $O(n \cdot |S| \cdot m)$, dove:
- $n = |\mathcal{U}|$ è il numero di utenti
- $|S|$ è il numero di vincitori (al più $m$ nel caso peggiore)
- $m$ è il numero totale di task

Poiché tipicamente $|S| \ll n$ e $m \ll n^2$, l'algoritmo è efficiente per istanze realistiche.

## 4.4. Fase 2: Determinazione dei Pagamenti (Critical Payment)

In un meccanismo veritiero, il pagamento $p_i$ corrisposto a un vincitore non può dipendere dalla sua offerta $b_i$, altrimenti l'agente avrebbe un incentivo a manipolare $b_i$ per influenzare $p_i$. IMCU adotta la logica del **Valore Critico** (*Critical Value*), derivata dalla caratterizzazione di Myerson per le aste.[15]

**Definizione 4.3 (Pagamento Critico)** Il pagamento critico per un vincitore $i \in S$ è definito come il **supremo** (limite superiore) dei bid che $i$ avrebbe potuto sottomettere rimanendo comunque un vincitore:

$$
p_i = \sup \{ b'_i \mid i \in \text{WinnerSet}(b'_i, \mathbf{b}_{-i}) \}
$$

dove $\mathbf{b}_{-i} = (b_1, \ldots, b_{i-1}, b_{i+1}, \ldots, b_n)$ rappresenta il vettore delle offerte di tutti gli altri partecipanti.

**Algoritmo 4.2: Calcolo del Pagamento Critico**

**Input:** Vincitore $i \in S$, insieme completo degli utenti $\mathcal{U}$, bid di tutti gli utenti $\{b_j\}_{j \in \mathcal{U}}$.

**Output:** Pagamento critico $p_i$.

1. **Inizializzazione:**
   - Considera l'insieme dei competitor: $\mathcal{U}_{-i} = \mathcal{U} \setminus \{i\}$
   - Inizializza il pagamento critico: $p_i \leftarrow b_i$ (per garantire Individual Rationality)
   - Inizializza il prefisso greedy: $T \leftarrow \emptyset$
   - Inizializza l'insieme dei task coperti: $\mathcal{T}_{\text{covered}} \leftarrow \emptyset$

2. **Simulazione Greedy sui Competitor:**

   **Mentre** esiste almeno un competitor $j \in \mathcal{U}_{-i} \setminus T$ con guadagno marginale positivo:
   
   a. Calcola il valore marginale di ciascun competitor $j \in \mathcal{U}_{-i} \setminus T$:
   
   $$
   \text{mv}_j = \sum_{k \in \Gamma_j \setminus \mathcal{T}_{\text{covered}}} \nu_k
   $$
   
   b. Calcola il guadagno marginale:
   
   $$
   \delta_j = \text{mv}_j - b_j
   $$
   
   c. Identifica il miglior competitor:
   
   $$
   j^* = \arg \max_{j \in \mathcal{U}_{-i} \setminus T} \delta_j
   $$
   
   Con tie-breaking lessicografico su ID in caso di pareggio.
   
   d. **Se** $\delta_{j^*} \leq 0$, **termina** il ciclo.
   
   e. **Altrimenti:**
   
   - Calcola il valore marginale di $i$ nello stato corrente:
     
     $$
     \text{mv}_i = \sum_{k \in \Gamma_i \setminus \mathcal{T}_{\text{covered}}} \nu_k
     $$
   
   - Calcola il **bid di soglia** che $i$ avrebbe dovuto battere per essere selezionato prima di $j^*$, vincolato al proprio valore marginale per garantire la profittabilità:
     
     $$
     \hat{p}_i = \min{\left(\text{mv}_i - (\text{mv}_{j^*} - b_{j^*}), \text{mv}_i\right)}
     $$
     
     Questa formula deriva dalla condizione di competizione:
     
     $$
     \text{mv}_i - b_i \geq \text{mv}_{j^*} - b_{j^*} \implies b_i \leq \text{mv}_i - (\text{mv}_{j^*} - b_{j^*})
     $$
   
   - Aggiorna il pagamento critico:
     
     $$
     p_i \leftarrow \max(p_i, \hat{p}_i)
     $$
   
   - Aggiungi $j^*$ al prefisso: $T \leftarrow T \cup \{j^*\}$
   
   - Aggiorna i task coperti: $\mathcal{T}_{\text{covered}} \leftarrow \mathcal{T}_{\text{covered}} \cup \Gamma_{j^*}$

3. **Calcolo del Valore Finale:**
   
   Dopo aver esaurito tutti i competitor con guadagno positivo, calcola il valore marginale residuo di $i$:
   
   $$
   \text{mv}_i^{\text{final}} = \sum_{k \in \Gamma_i \setminus \mathcal{T}_{\text{covered}}} \nu_k
   $$
   
   Aggiorna il pagamento critico:
   
   $$
   p_i \leftarrow \max(p_i, \text{mv}_i^{\text{final}})
   $$

4. **Return** $p_i$

La Figura 4.1 mostra il diagramma di flusso delle operazioni principali dell'algoritmo, evidenziando i passi di inizializzazione, selezione del competitor, aggiornamento del valore critico e il calcolo finale.

![Figura 4.1: Diagramma di flusso dell'Algoritmo 4.2 (Calcolo del Pagamento Critico). Il diagramma evidenzia: (1) inizializzazione con $p_i \leftarrow b_i$; (2) ciclo sui competitor per aggiornare la soglia critica con la regola di $\max$; (3) calcolo finale del valore marginale residuo. Il processo garantisce sempre $p_i \geq b_i$ e quindi Individual Rationality.](./Immagini/figura_4_1_critical_payment.jpg)

L'Algoritmo 4.2 procede iterativamente costruendo la sequenza di competitor $j_1, j_2, \ldots, j_K$ che verrebbero selezionati in assenza di $i$. Ad ogni passo $k$, il pagamento critico viene aggiornato con la regola $p_i \leftarrow \max(p_i, \hat{p}_{i,k})$, garantendo che $i$ riceva il minimo pagamento necessario per rimanere vincitore.

**Lemma 4.2 (Correttezza del Calcolo del Pagamento Critico)** *L'Algoritmo 4.2 calcola correttamente il pagamento critico $p_i$ per ogni vincitore $i \in S$.*

**Dimostrazione.** Dobbiamo dimostrare che $p_i$ è effettivamente il supremo dei bid che permettono a $i$ di rimanere vincitore.

**Passo 1:** L'algoritmo simula l'esecuzione dell'Algoritmo 4.1 senza l'utente $i$, generando una sequenza di competitor $j_1, j_2, \ldots, j_K$ che verrebbero selezionati in assenza di $i$.

**Passo 2:** Ad ogni posizione $k$ nella sequenza, calcola il bid massimo $\hat{p}_{i,k}$ che $i$ potrebbe sottomettere e comunque essere selezionato *prima* del competitor $j_k$. Questo è derivato dalla condizione di competizione greedy.

**Passo 3:** Il massimo tra tutti questi $\hat{p}_{i,k}$ rappresenta il valore critico, perché:

- Se $i$ offre un bid $b_i < p_i$, verrà selezionato prima di tutti i competitor (guadagno marginale netto superiore).
- Se $i$ offre un bid $b_i > p_i$, esisterà almeno un competitor $j_k$ che verrà selezionato prima di $i$, cambiando potenzialmente l'esito finale.

**Passo 4:** Il termine $\text{mv}_i^{\text{final}}$ gestisce il caso in cui, dopo aver esaurito tutti i competitor con guadagno positivo, $i$ porta ancora valore residuo. In questo caso, $i$ può offrire fino al suo valore marginale totale rimanendo vincitore.

**Complessità Computazionale:** Per ogni vincitore, l'Algoritmo 4.2 esegue una simulazione greedy completa sui competitor, con complessità $O(n \cdot m)$. Con $|S|$ vincitori, la complessità totale della fase di pagamento è $O(|S| \cdot n \cdot m)$.

## 4.5. Analisi delle Proprietà Teoriche

Il meccanismo IMCU soddisfa rigorosamente quattro proprietà economiche fondamentali, la cui validità è stata verificata empiricamente in ogni istanza della simulazione (cfr. Capitolo 7).

### 4.5.1. Efficienza Computazionale

**Teorema 4.2 (Complessità Polinomiale di IMCU)** *Il meccanismo IMCU ha complessità computazionale $O(|S| \cdot n \cdot m)$, dove $|S| \leq m$ è il numero di vincitori, $n$ è il numero di utenti, e $m$ è il numero di task. Pertanto, IMCU è computazionalmente efficiente.*

**Dimostrazione.** La complessità deriva dalla somma delle due fasi:

- **Fase 1 (Selezione):** $O(n \cdot |S| \cdot m)$ (dal Teorema 4.1).
- **Fase 2 (Pagamenti):** $O(|S| \cdot n \cdot m)$ (da Algoritmo 4.2).

Poiché $|S| \leq m$ (ogni vincitore copre almeno un task unico per essere selezionato), entrambe le fasi sono polinomiali.

### 4.5.2. Razionalità Individuale (Individual Rationality - IR)

**Teorema 4.3 (Razionalità Individuale di IMCU)** *Per ogni vincitore $i \in S$, il pagamento critico soddisfa $p_i \geq b_i$. Di conseguenza, l'utilità di ogni utente veritiero è non negativa: $u_i = p_i - c_i \geq 0$ (dato $b_i = c_i$ per veridicità).*

**Dimostrazione.** Dall'Algoritmo 4.2, il pagamento critico è inizializzato a $p_i = b_i$ (Step 1). Successivamente, $p_i$ viene aggiornato solo con l'operazione:

$$
p_i \leftarrow \max(p_i, \hat{p}_{i,k})
$$

che può solo aumentare (o lasciare invariato) il valore di $p_i$. Pertanto, $p_i \geq b_i$ sempre.

Se l'utente dichiara veritieramente $b_i = c_i$, allora:

$$
u_i = p_i - c_i \geq b_i - c_i = c_i - c_i = 0
$$

Questo garantisce che nessun utente veritiero operi in perdita.

### 4.5.3. Profittabilità (Profitability)

**Teorema 4.4 (Profittabilità di IMCU)** *L'utilità della piattaforma è sempre non negativa: $u_0(S) = v(S) - \sum_{i \in S} p_i \geq 0$.*

**Dimostrazione.** Dobbiamo dimostrare che la somma dei pagamenti critici non eccede il valore totale generato dai vincitori.

**Passo 1:** L'Algoritmo 4.1 seleziona utenti solo quando il loro guadagno marginale netto è positivo: $\delta_i = \text{mv}_i - b_i > 0$.

**Passo 2:** Sebbene $p_i > b_i$ in generale, la costruzione del pagamento critico garantisce che ogni $p_i$ sia limitato dal valore marginale che $i$ apporta al sistema.

**Passo 3 (Induzione sui vincitori):** Consideriamo i vincitori nell'ordine di selezione greedy: $i_1, i_2, \ldots, i_{|S|}$.

Per il primo vincitore $i_1$:

$$
p_{i_1} \leq \text{mv}_{i_1} \quad \text{(dall'Algoritmo 4.2, Step 3)}
$$

Quindi: $v(\{i_1\}) - p_{i_1} \geq 0$.

Assumiamo per ipotesi induttiva che dopo $k-1$ vincitori:

$$
v(S_{k-1}) - \sum_{j=1}^{k-1} p_{i_j} \geq 0
$$

Al passo $k$, il vincitore $i_k$ viene selezionato perché $\delta_{i_k} = \text{mv}_{i_k} - b_{i_k} > 0$. Il pagamento critico $p_{i_k}$ è costruito in modo tale che:

$$
p_{i_k} \leq \text{mv}_{i_k}
$$

Pertanto:

$$
v(S_k) - \sum_{j=1}^{k} p_{i_j} = v(S_{k-1}) + \text{mv}_{i_k} - \sum_{j=1}^{k-1} p_{i_j} - p_{i_k} \geq v(S_{k-1}) - \sum_{j=1}^{k-1} p_{i_j} \geq 0
$$

dove l'ultima disuguaglianza segue dall'ipotesi induttiva e dal fatto che, per la costruzione dell'Algoritmo 4.2, il pagamento critico $p_{i_k}$ non eccede mai il valore marginale effettivo $\text{mv}_{i_k}$ apportato dal vincitore corrente.

Per induzione, $u_0(S) \geq 0$ per l'insieme finale di vincitori.

### 4.5.4. Veridicità (Truthfulness)

**Teorema 4.5 (Veridicità di IMCU - Myerson's Characterization)** *Il meccanismo IMCU è **incentivo-compatibile in strategie dominanti** (DSIC), ovvero *truthful*. Per ogni utente $i$ e per ogni profilo di bid degli altri utenti $\mathbf{b}_{-i}$, la strategia di dichiarare il costo vero $b_i = c_i$ massimizza l'utilità di $i$.*

**Dimostrazione.** La dimostrazione si basa sul **Lemma di Myerson**, che fornisce una caratterizzazione completa dei meccanismi veritieri.[15]

**Lemma di Myerson (Adattato):** Un meccanismo d'asta è veritiero se e solo se soddisfa due condizioni:

1. **Monotonicità dell'allocazione:** Se un utente vince con bid $b_i$, deve vincere anche con qualsiasi bid $b'_i < b_i$ (dato fisso $\mathbf{b}_{-i}$).

2. **Pagamento a soglia critica:** Il pagamento a un vincitore è determinato esclusivamente dalle offerte degli altri e dalla funzione di valore, ed è indipendente dal bid del vincitore (purché inferiore alla soglia critica).

**Verifica della Condizione 1 (Monotonicità):**

Supponiamo che l'utente $i$ vinca con bid $b_i$, ovvero $i \in S(b_i, \mathbf{b}_{-i})$. Questo significa che durante l'esecuzione dell'Algoritmo 4.1, $i$ è stato selezionato perché il suo guadagno marginale netto era positivo e massimo tra i candidati rimanenti:

$$
\delta_i = \text{mv}_i - b_i > 0
$$

Se $i$ riduce il proprio bid a $b'_i < b_i$, il suo guadagno marginale netto diventa:

$$
\delta'_i = \text{mv}_i - b'_i > \text{mv}_i - b_i = \delta_i > 0
$$

Poiché $\delta'_i > \delta_i$, il rango di $i$ nella selezione greedy può solo migliorare (o rimanere invariato in caso di pareggi gestiti dal tie-breaking lessicografico). Pertanto, $i$ verrà selezionato anche con $b'_i$.

**Verifica della Condizione 2 (Pagamento Critico):**

Dall'Algoritmo 4.2, il pagamento $p_i$ è calcolato simulando l'asta senza l'utente $i$ e determinando il massimo bid che $i$ può sottomettere rimanendo vincitore. Questo valore è indipendente dal bid effettivo $b_i$ sottomesso da $i$ (purché $b_i \leq p_i$), dipendendo solo da:

- I bid degli altri utenti $\mathbf{b}_{-i}$
- I valori marginali di $i$ nei vari stati dell'asta
- La struttura dell'algoritmo greedy

Pertanto, $p_i$ è effettivamente un pagamento a soglia critica.

**Conclusione:** Poiché entrambe le condizioni del Lemma di Myerson sono soddisfatte, IMCU è veritiero. Per qualsiasi deviazione $b_i \neq c_i$:

- **Overbidding** ($b_i > c_i$): Rischio di perdere l'asta in situazioni in cui $c_i < p_i < b_i$, risultando in utilità $u_i = 0$ invece di $u_i = p_i - c_i > 0$.

- **Underbidding** ($b_i < c_i$): Rischio di vincere con pagamento $p_i < c_i$, risultando in utilità negativa $u_i = p_i - c_i < 0$.

Quindi, dichiarare $b_i = c_i$ è una strategia dominante.

**Nota:** L'analisi dettagliata dei casi di overbidding e underbidding è già stata presentata nel Teorema 3.1, Sezione 3.4.2. Qui è stato adottata la caratterizzazione generale di Myerson sulle aste veritiere, che fornisce una prospettiva complementare sulla proprietà di veridicità.

**Proposizione 4.1 (Unicità del Comportamento di Equilibrio)** *In regime di razionalità perfetta, il profilo di strategie in cui ogni utente dichiara il proprio costo vero costituisce l'unico equilibrio di Nash in strategie dominanti del gioco indotto dal meccanismo IMCU.*

**Dimostrazione.** Dal Teorema 4.5, dichiarare $b_i = c_i$ è una strategia dominante per ogni utente $i$. Per definizione, un equilibrio in strategie dominanti è unico: nessun giocatore può migliorare la propria utilità con una deviazione unilaterale, indipendentemente dalle strategie degli altri.

Pertanto, il profilo $(c_1, c_2, \ldots, c_n)$ è l'unico equilibrio di Nash del gioco.

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