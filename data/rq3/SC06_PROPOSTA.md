# SC06 — memoria su casi reali di cybersecurity

**Stato storico:** questa proposta ha preparato il dataset conversazionale. La scelta successiva ha associato SC06 a RQ5, fissando il confronto fra modelli a parità di contesto. Le sezioni sulle condizioni e sulla valutazione qui sotto documentano la fase precedente e sono superate. Il protocollo corrente è [RQ5_SC06_PROTOCOLLO.md](RQ5_SC06_PROTOCOLLO.md); nessuna generazione o valutazione SC06 è stata eseguita.

## 1. Che cosa vogliamo osservare

Quando informazioni su diversi casi reali di cybersecurity vengono distribuite tra sessioni, il sistema riesce a recuperare quelle del caso richiesto senza attribuirgli informazioni di un altro caso?

L'attività è consultare schede di incidenti: questa proposta misura la separazione fra **casi della stessa attività**. Non dimostra ancora la separazione fra attività diverse, come analisi di incidenti e pianificazione delle patch. Questa distinzione va conservata nella formulazione finale di RQ3.

## 2. Quanti dati abbiamo preparato

| Elemento | Quantità proposta |
|---|---:|
| Schede reali candidate dopo l'audit | 2.445 |
| Schede selezionate con contenuti tecnici diversificati | **708** |
| Gruppi indipendenti nell'esecuzione, da tre schede ciascuno | **236** |
| Sessioni di inserimento per gruppo | 3 |
| Domande per scheda | 3 |
| Domande per gruppo | 9 |
| Domande totali per condizione, modello e ripetizione | **2.124** |

“Indipendenti nell'esecuzione” significa che la memoria viene azzerata fra gruppi; non garantisce indipendenza statistica degli incidenti originali. La scala del dataset è 708 casi, mentre la quantità di casi presenti contemporaneamente nella memoria è tre. Aumentare il numero di gruppi non equivale ad aumentare la lunghezza della singola conversazione.

### Selezione riproducibile

Le 2.445 candidate vengono ordinate mediante SHA-256 di `SC06-design-v1:<incident_id>`. In quell'ordine si accetta una scheda solo se:

- la combinazione completa dei suoi campi tecnici utilizzabili non è già stata accettata;
- la descrizione normalizzata, se non vuota, non è già stata accettata.

Risultato: 708 accettate, 1.716 escluse per profilo tecnico ripetuto, altre 21 per descrizione ripetuta. Ogni decisione è registrata. È una selezione di **varietà informativa**, non un campione rappresentativo della frequenza reale degli attacchi, né una deduplicazione certificata delle campagne. Le 2.445 candidate e l'archivio originale rimangono disponibili.

La selezione non usa risultati dei modelli. Non si devono cambiare i casi dopo aver visto quali producono risposte migliori o peggiori.

## 3. Come funziona ogni gruppo

I tre incidenti assumono i nomi locali **Caso A, Caso B, Caso C**. I fatti e le etichette VERIS restano invariati. Il collegamento agli identificativi originali rimane in un file di provenienza, non nel contesto del modello.

| Momento | Informazioni presentate | Ordine dei casi |
|---|---|---|
| Sessione 1 | Tipologie delle azioni presenti nelle schede | A → B → C |
| Sessione 2 | Vettori delle azioni | B → C → A |
| Sessione 3 | Risorse coinvolte e categorie di dati | C → A → B |
| Sessione successiva | Una domanda su un campo di uno dei casi | Nuova conversazione per ogni domanda |

Se una famiglia manca, il messaggio corrispondente viene omesso: non si inventano dati. Tutti i campi disponibili vengono comunicati una volta. Il formato è breve e uniforme, con messaggi utente; eventuali risposte di presa in carico non devono aggiungere fatti alla memoria.

Le nove domande vengono eseguite separatamente sulla **stessa memoria finale congelata**. Le risposte alle domande precedenti non vengono reinserite nella memoria. Fra gruppi si azzera tutto: Caso A di un gruppo non deve incontrare Caso A di un altro.

Si scelgono tre famiglie diverse per ogni scheda. Se ne esistono quattro, quella omessa ruota secondo una regola deterministica. Se una famiglia contiene più campi, si sceglie un campo con la stessa procedura. Non si presume che i campi omessi dalla scheda siano falsi.

Esempio di domanda: «Per Caso A, quali valori erano stati riportati nel campo Categorie di dati?». L'output richiesto è una lista JSON delle etichette originali. Il campo chiesto e il nome del caso sono noti, ma i valori corretti non vengono ripetuti nella domanda.

L'[esempio completo](sc06_design_v1/ESEMPIO.md) mostra tre schede reali e le risposte attese separate.

## 4. Condizioni da confrontare — proposta minima

Per mantenere contenuto e costo gestibili, propongo inizialmente:

- **Senza memoria:** solo istruzione generale e domanda, per misurare quanto si riesce a indovinare dal campo richiesto.
- **Turn-level RAG:** recupero dei messaggi dalle sessioni precedenti.
- **Fact-based RAG:** recupero dei fatti estratti dagli stessi messaggi.
- **FULL_HISTORY:** tutte le sessioni dello stesso gruppo, come controllo diagnostico separato.

È una proposta, non una scelta già approvata delle architetture. Le altre memorie potranno essere incluse con una motivazione legata alla domanda sperimentale. Queste schede non contengono revisioni temporali esplicite: non sono un test specifico della capacità di aggiornare o ritirare fatti.

Per Turn-level RAG e Fact-based RAG servirà lo stesso budget di contesto recuperato e lo stesso modello di risposta; query e storie devono coincidere. FULL_HISTORY resta fuori dal confronto a budget uguale. Modello, budget, parametri, numero di ripetizioni e costo vanno fissati prima dell'esecuzione principale. La configurazione RQ2 non viene ereditata automaticamente.

Con tutte e quattro le condizioni si avrebbero **8.496 generazioni di risposta per modello e ripetizione**, oltre alle eventuali chiamate per costruire le memorie. Non sono chiamate già effettuate.

Prima dell'esecuzione principale serve una piccola verifica del formato e dei costi, usando gruppi dichiarati di sviluppo che saranno esclusi dal risultato principale. Il numero finale di casi di valutazione scenderà di conseguenza. Se si usa un sottoinsieme per costo, la selezione va fissata prima di osservare le prestazioni.

## 5. Come valutare

La risposta attesa è l'insieme esatto dei valori del campo VERIS comunicati nelle sessioni. Si ignorano ordine e duplicati nella lista e gli spazi esterni delle stringhe; le etichette restano quelle originali. Si richiede un oggetto JSON con un unico campo `values`, lista di stringhe. Un output non conforme viene registrato come errore di formato, senza correggerlo con un altro modello.

Registrare per ogni domanda:

1. **Risposta esatta:** tutti e soli i valori attesi.
2. **Astensione:** lista vuota. Tutte le domande attuali sono rispondibili dalla storia: l'astensione è mancato recupero della risposta, non “astensione corretta”.
3. **Risposta non esatta:** valori mancanti o aggiunti.
4. **Errore di formato.**

Come indicatore aggiuntivo, registrare se la risposta contiene valori non corretti per il caso richiesto ma presenti **nello stesso campo di un altro caso del gruppo**. Questo è un segnale compatibile con confusione fra casi, non una prova della sua causa.

Nel dataset preparato **1.384 domande su 2.124** hanno almeno un valore di un altro caso che consentirebbe di rilevare tale confusione. Le altre non vanno trattate come prove che la confusione non possa avvenire: valori uguali fra casi la rendono invisibile. Riportare questo indicatore sul sottoinsieme rilevabile, separatamente dall'esattezza complessiva.

Per le memorie, conservare anche il contesto recuperato e la provenienza: verificare se include le evidenze necessarie della scheda giusta permette di distinguere un errore di recupero da un errore di risposta. La copertura di un campo multivalore richiede tutti i valori attesi.

Riassumere l'esattezza per gruppo e per famiglia di domanda; le nove domande dello stesso gruppo non sono nove repliche indipendenti. Nessun risultato viene mediato insieme a SC01–SC05. Un'eventuale differenza fra strategie vale per questo disegno e questo campione.

## 6. Limiti da tenere espliciti

- Le fonti descrivono incidenti reali; conversazioni, nomi locali e ordine dei messaggi sono costruiti.
- La correttezza attesa è rispetto ai dati VERIS comunicati, non una nuova verifica forense dell'incidente.
- Identificativi locali e assenza dei nomi pubblici riducono gli indizi per riconoscere il caso, ma non eliminano conoscenze pregresse e risposte indovinate: serve la condizione senza memoria.
- Le etichette e gli elenchi brevi consentono una valutazione automatica precisa, ma non misurano la qualità di una spiegazione libera dell'incidente.
- Il disegno alterna tre casi; senza una condizione equivalente non alternata non dimostra che un errore sia causato dall'alternanza in sé.
- Profili e descrizioni diversi non garantiscono campagne diverse; la composizione va controllata prima di usare inferenze statistiche.

## 7. Artefatti e prossima decisione

Preparazione offline ripetibile dalla radice del progetto:

```sh
python3 scripts/rq3/prepare_sc06_design.py
```

Nella cartella `sc06_design_v1/`:

- `episodes.jsonl`: soli messaggi e istruzione di inserimento.
- `queries.jsonl`: sole domande da presentare al modello.
- `oracle_questions.jsonl`: risposte attese, evidenze e indicatori per la valutazione; **mai nel contesto del modello**.
- `case_mapping.jsonl`: provenienza e campi reali, per l'audit; **mai nel contesto del modello**.
- `selection_decisions.jsonl`: decisione per ciascuna delle 2.445 candidate.
- `manifest.json`: conteggi, hash dell'input, regole e stato proposto.
- `ESEMPIO.md`: formato leggibile di un gruppo, con soluzione separata.

Le decisioni successive sono state concluse nel protocollo RQ5/SC06 corrente. Questo file resta come traccia della preparazione iniziale del dataset e non deve guidare la realizzazione.
