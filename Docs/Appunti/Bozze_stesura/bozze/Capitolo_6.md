# Capitolo 6: Analisi dei Risultati - La Baseline Teorica

## 6.1. Validazione Formale del Meccanismo

Prima di analizzare le performance economiche, è necessario verificare che l'implementazione software del meccanismo IMCU rispetti le proprietà teoriche dimostrate nel Capitolo 3. Durante le simulazioni, il sistema ha eseguito controlli automatici su ogni asta per garantire la conformità alle garanzie formali.

La Tabella 6.1 riassume l'esito di queste verifiche per la giornata del 1 Febbraio 2014 (12 ore di simulazione, dalle 08:00 alle 20:00).

**Tabella 6.1: Esito della Validazione delle Proprietà Teoriche**

| Proprietà                    | Definizione                                                        | Test Eseguiti                                            | Violazioni Rilevate |
|:-----------------------------|:-------------------------------------------------------------------|:---------------------------------------------------------|:-------------------|
| **Razionalità Individuale**  | $p_i \geq c_i$ $\forall i \in S$                                  | 175 vincitori (raggio 2.5 km, configurazione baseline)   | 0                  |
| **Profittabilità**           | $\sum_{i \in S} p_i \leq v(S)$                                    | 12 aste orarie                                           | 0                  |
| **Veridicità**               | $u_i(c_i) \geq u_i(b'_i)$ $\forall b'_i \neq c_i$                 | 17.500 simulazioni Monte Carlo                           | 0                  |
| **Monotonicità**             | $i \in S(b_i) \implies i \in S(b'_i < b_i)$                       | Test controfattuali                                      | 0                  |

Tutti i test hanno dato esito positivo. In particolare:
- **Razionalità Individuale:** Ogni vincitore ha ricevuto un pagamento pari o superiore al proprio costo dichiarato, garantendo utilità non negativa ($u_i \geq 0$).
- **Profittabilità:** In tutte le 12 ore simulate, la somma dei pagamenti non ha mai superato il valore totale generato, assicurando utilità positiva alla piattaforma.
- **Veridicità:** I test Monte Carlo (100 simulazioni controfattuali per ciascuno dei 175 vincitori) confermano che nessun utente avrebbe potuto aumentare la propria utilità dichiarando un costo falso.

Questi risultati confermano che l'implementazione è corretta e che, in condizioni di razionalità perfetta, il meccanismo si comporta esattamente come previsto dalla teoria.

## 6.2. Performance Economica dello Scenario Baseline

Lo scenario di riferimento (*baseline*) utilizza un raggio di assegnazione $R_{\text{task}} = 2.5$ km. Questa configurazione rappresenta un compromesso ragionevole tra accessibilità dei task (raggio abbastanza ampio) e costi di spostamento (non eccessivi).

### Risultati aggregati giornalieri

L'analisi delle 12 ore di simulazione produce i seguenti valori cumulativi:

- **Valore totale generato:** $v(S) = 32.481,88$ €  
  Questo è il valore economico complessivo dei task completati dai vincitori.
- **Pagamenti totali agli utenti:** $\sum_{i \in S} p_i = 16.470,36$ €  
  La spesa sostenuta dalla piattaforma per compensare i partecipanti.
- **Utilità netta della piattaforma:** $u_0 = 16.011,52$ €  
  Il "profitto" del sistema dopo aver pagato gli utenti.

Il sistema riesce a trattenere circa il **59,58%** del valore generato come margine netto:

$$
\eta = \frac{u_0}{v(S)} \times 100 = \frac{16.011,52}{32.481,88$} \times 100 \approx 49,21\%
$$

Il restante ~50% viene redistribuito agli utenti, coprendo i loro costi operativi ($c_i$) e fornendo un surplus ($p_i - c_i$) che incentiva la partecipazione.

### Variazione temporale delle prestazioni

La Figura 6.1 visualizza l'andamento orario delle tre metriche principali ($v(S)$, $\sum p_i$, $u_0$), evidenziando chiaramente il picco delle 13:00 e la correlazione tra densità di domanda e performance del sistema.

![Figura 6.1: Performance orarie del meccanismo IMCU nello scenario baseline (R=2.5km). Si osserva un picco di attività alle ore 13:00, dove il sistema massimizza sia il valore generato ($v(S)$) che l'utilità netta ($u_0$).](../Fase_1/experiments_fase1_baseline/day_2014-02-01/figures/2014-02-01_kpi_timeseries.png)

Il picco si registra alle **ore 13:00**:

- $v(S) = 3.938,32$ € (massimo giornaliero)
- $\eta = 54,36\%$ (efficienza più alta)
- 14 vincitori selezionati

Questa fascia oraria coincide con la maggiore disponibilità di utenti e task, permettendo all'algoritmo greedy di identificare combinazioni più efficienti. Al contrario, nelle ore con attività ridotta (es. 11:00 o 17:00), l'efficienza scende intorno al 53%, probabilmente a causa della minore competizione tra utenti e della dispersione spaziale dei task.

La Figura 6.2 mostra la distribuzione cumulativa dei pagamenti per l'intera giornata.

![Figura 6.2: Funzione di Distribuzione Cumulativa (CDF) dei pagamenti giornalieri. La curva mostra che la maggior parte dei pagamenti si concentra nella fascia medio-bassa, con una coda lunga di pagamenti elevati per gli utenti più competitivi.](../Fase_1/experiments_fase1_baseline/day_2014-02-01/figures/2014-02-01_payments_cdf.png)

## 6.3. Analisi di Sensitività: Impatto del Raggio di Assegnazione

Per comprendere come il vincolo di distanza influenzi il comportamento del sistema, sono state condotte simulazioni comparative con tre configurazioni di raggio: 1.5 km, 2.5 km (baseline) e 4.0 km. La Tabella 6.2 confronta i risultati aggregati.

**Tabella 6.2: Confronto Prestazionale per Raggio di Assegnazione**

| Raggio  | Efficienza Media | Utilità Piattaforma ($u_0$) | Vincitori Totali | Indice di Gini |
|:-------:|:----------------:|:---------------------------:|:----------------:|:--------------:|
| 1.5 km  | 48,79%           | 13.113,67 €                 | 257              | 0,32           |
| **2.5 km** | **49,21%** | **16.011,52 €** | **150** | **0,30** |
| 4.0 km  | 45,11%           | 15.964,79 €                 | 84               | 0,36           |

### Trade-off emersi

**1. Efficienza vs Partecipazione**  
Contrariamente ai modelli semplificati, l'efficienza non cresce linearmente con il raggio. Si osserva un picco (49,21%) nella configurazione baseline a 2.5 km. Estendendo il raggio a 4.0 km, l'efficienza cala al 45,11%. Ciò è dovuto al modello di costo realistico (Star Routing A/R): per coprire task molto distanti, gli utenti sostengono costi di spostamento che erodono gran parte del valore aggiunto, rendendo l'allocazione meno efficiente per la piattaforma nonostante l'aumento del valore lordo. Parallelamente, il numero di vincitori crolla drasticamente (da 257 a 84), evidenziando un forte carattere elitario nei raggi ampi.

**2. Concentrazione dei guadagni**  
L'Indice di Gini rivela un comportamento non lineare. Il valore minimo (massima equità) si ottiene a 2.5 km (G=0,30). Passando a 4.0 km, l'indice risale a 0,36. Questo indica che un raggio eccessivo favorisce l'emergere di pochi "super-utenti" centrali che monopolizzano i task migliori, lasciando gli altri partecipanti a secco. La configurazione a 2.5 km si conferma quindi il sweet spot (punto ottimo) che bilancia efficienza ed equità sociale.

La Figura 6.3 visualizza l'equità distributiva dello scenario baseline tramite la Curva di Lorenz.

![Figura 6.3: Curva di Lorenz e indice di Gini per la distribuzione dei pagamenti. Un valore di Gini pari a 0.330 indica una distribuzione delle risorse relativamente equa, lontana da scenari di disuguaglianza estrema.](../Fase_1/experiments_fase1_baseline/day_2014-02-01/figures/2014-02-01_payments_lorenz.png)

**3. Sostenibilità economica**  
L'utilità netta della piattaforma raggiunge la saturazione attorno ai 2.5 km (16.011 €), per poi stagnare o decrescere leggermente a 4.0 km (15.964 €). Questo dimostra che, oltre una certa soglia, l'espansione dell'area di ricerca aumenta solo i costi logistici $sum_{p_i}$ senza generare profitto aggiuntivo reale per il sistema.

### Clustering delle ore di servizio

Applicando K-Means clustering ai dati orari (features: $v(S)$, $\eta$, numero vincitori), emergono tre pattern distintivi:

- **Cluster 1 (Alta Domanda):** Ore 13:00–14:00 (picco). Alto valore, alta efficienza, molti vincitori competitivi.
- **Cluster 2 (Transizione):** Ore 08:00, 19:00 (inizio e fine giornata). Domanda in crescita/decremento, efficienza intermedia.
- **Cluster 3 (Standard):** Ore 10:00–12:00, 15:00–18:00. Domanda stabile, efficienza media attorno al 56%.

Questo suggerisce che il meccanismo ha "regimi operativi" diversi a seconda della densità spazio-temporale della domanda.

## 6.4. Interpretazione e Limiti della Baseline

I risultati della Fase 1 stabiliscono il **limite superiore** delle prestazioni raggiungibili dal sistema MCS. In condizioni ideali (razionalità perfetta, dichiarazioni veritiere, nessun comportamento strategico), il meccanismo IMCU:

- **Mantiene sempre** le garanzie teoriche (IR, veridicità, profittabilità)
- **Genera efficienza** intorno al 49% nello scenario di riferimento
- **Distribuisce i guadagni** in modo relativamente equo (Gini ~0,30 nella baseline 2,5 km)

Tuttavia, questa baseline assume comportamenti irrealistici:

1. **Tutti gli utenti dichiarano i costi veri** → Nella realtà, potrebbero sovrastimare per ottenere pagamenti più alti
2. **Tutti accettano qualsiasi task assegnato** → Nella realtà, potrebbero rifiutare task scomodi
3. **Nessun costo cognitivo** → Nella realtà, valutare complessi trade-off richiede sforzo mentale

Questi aspetti verranno affrontati nelle fasi successive, dove si introdurranno modelli di razionalità limitata per quantificare il **gap** tra teoria e pratica.

**Questa baseline, pur rappresentando il limite superiore teorico, costituisce il termine di paragone quantitativo fondamentale per misurare il gap di robustezza che verrà analizzato nei capitoli successivi.**

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