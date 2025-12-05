## Efficacia meccanismo GAP: confronto breakdown
Confrontando i risultati della Fase 2 (razionalità limitata senza controllo) con quelli della Fase 3 (meccanismo adattivo GAP), emerge un quadro interessante. Nello scenario *Mixed*, le metriche economiche calano in termini assoluti: il valore effettivo scende del **9.8%** e l'utilità della piattaforma del **12.3%**.

Questo calo però non significa che il sistema funzioni peggio. Al contrario, è esattamente quello che ci aspettavamo: il GAP trasforma le perdite casuali e incontrollate in costi prevedibili. In pratica, il sistema ora "spende" per prevenire i problemi invece di subirli.

Il tasso di breakdown passa dal **10.41%** (Fase 2) al **24.30%** (Fase 3). Questi numeri però rappresentano cose diverse:
- **Fase 2 - Danno Vero**: Il sistema assegna task a tutti indiscriminatamente. Il 10.41% di breakdown sono task effettivamente assegnati ma non completati. Questi fallimenti creano danni concreti: dati persi, tempo sprecato, costi per gestire gli utenti che abbandonano.
- **Fase 3 - Rinuncia Preventiva**: Il GAP valuta gli utenti prima di assegnargli qualcosa. Quando trova profili con bassa reputazione o scarsa affidabilità, semplicemente non gli assegna il task. Il 24.30% è quindi composto principalmente da task che il sistema ha deciso di non assegnare per evitare rischi. È una scelta strategica: meglio non guadagnare che rischiare di perdere.

Il tasso di completamento scende dall'**87%** (Fase 2) al **73%** (Fase 3).

Nella Fase 2, l'87% era un dato falsato: il sistema accettava chiunque, e negli scenari peggiori (*Low*) questo portava a tassi di abbandono altissimi. Nella Fase 3, il calo è normale e sano: il GAP filtra gli utenti inaffidabili prima che causino problemi. Il numero totale di task rimane uguale, ma quelli effettivamente assegnati sono meno perché il sistema scarta preventivamente chi probabilmente non li completerebbe. Risultato: chi riceve un task ha molte più probabilità di finirlo.

Possiamo pensare al sistema come a una banca che decide a chi prestare soldi:
- La **Fase 2** presta a tutti senza verifiche: massimizza il volume dei prestiti, ma poi molti non restituiscono i soldi (utenti che abbandonano i task). Negli scenari critici, questo approccio porta al collasso.
- La **Fase 3** controlla i richiedenti e presta solo a chi è affidabile: questo riduce il volume totale dei prestiti del 9.8%, ma elimina quasi completamente le insolvenze. Il portafoglio è più piccolo ma molto più sicuro.

Dunque, il sistema non cerca di massimizzare il profitto a ogni costo, ma di funzionare in modo stabile nel tempo. La perdita del 12.3% di utilità è il **prezzo della sicurezza**: è quello che costa trasformare un sistema vulnerabile (dove chiunque può causare danni) in uno affidabile e controllato.