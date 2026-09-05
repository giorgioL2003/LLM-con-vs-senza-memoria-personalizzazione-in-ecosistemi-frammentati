# Prova di sviluppo — retrieval di U su SC03 con la memoria riparata

**Non sono i risultati dell'esperimento.** La cartella è nata con il solo
retrieval e i prompt (`generation_inputs_sc03_u.jsonl`, costruiti senza chiamare
il modello). Le 7 risposte U sono state generate in un secondo momento e stanno
in `generation_dev_sc03_u.jsonl`: il confronto è in fondo a questo file.

## Input e configurazione

| | |
|---|---|
| fatti candidati | `results/rq2/facts/scenario_03_facts.jsonl` (gli stessi di F e della prima prova) |
| stato di U | `results/rq2/memory_repair_v3/scenario_03_state.json` (istruzioni `u-instructions-0.3`) |
| configurazione | `data/rq2/config/experiment_rq2.json`, `rq2-dev-0.1` |
| budget | 200 token, invariato |
| ranking | TF-IDF / coseno, invariato |
| etichetta | `prova-riparazione-u-instructions-0.3` |

Il percorso alternativo è stato passato con il parametro `--state`, che esisteva
già: **nessuna modifica al codice del retrieval**. Verificato che senza `--state`
il comportamento predefinito resta identico alla prima prova (stessi elementi
selezionati, stessi token, stesso `state_source`).

## File

- `retrieval_sc03_u.jsonl` — 7 righe, una per domanda, modalità U
- `generation_inputs_sc03_u.jsonl` — 7 prompt pronti, mai inviati

## Confronto con la prima prova (`results/rq2/retrieval_sc03.jsonl`)

Gli `entry_id` sono **posizionali** e non stabili fra una prova e l'altra: lo
stesso `SC03-M023` indica voci diverse nelle due esecuzioni. Il confronto va
fatto sul **testo**, non sugli identificatori.

## Le 7 risposte U (`generation_dev_sc03_u.jsonl`)

Generate dai prompt di questa cartella, senza ricostruire memoria né retrieval.
`claude-sonnet-5`, effort `medium`: gli stessi parametri della prima prova SC03.
7 chiamate, 0 errori. Confronto con le sole risposte U di
`results/rq2/generation_dev_sc03.jsonl`.

**Una sola esecuzione:** le differenze sono osservazioni, non prove che ogni
cambiamento dipenda dalla modifica a U. Le risposte del modello variano anche a
parità di contesto.

| | esito | informazioni necessarie nel contesto? |
|---|---|---|
| Q1 obiettivo | **invariato**, entrambe complete | sì, entrambi gli obiettivi |
| Q2 classificazione superata | **invariato** nella sostanza | sì per infostealer e ransomware; «famiglia Kelpie» manca in entrambe |
| Q3 evidenza ritirata | **lieve peggioramento** | il motivo c'è solo a metà: «residuo dell'esercitazione» sì, «non ha alcuna relazione con l'incidente» no (era presente prima) |
| Q4 attività completate | **invariato**, entrambe parziali | no: isolamento, blocco del dominio, credenziali e verifica accessi non sono nel contesto |
| Q5 punti aperti e vincolo | **misto: migliora su una metà, peggiora sull'altra** | il vincolo sì e completo; il punto aperto vero (reinstallazione) no |
| Q6 catena di evidenze | **invariato**, entrambe si astengono | no: i 240 MB sono in memoria ma non nel contesto |
| Q7 informazione assente | **invariato**, astensione corretta | non applicabile |

### I due casi che contano

**Q5, il miglioramento.** Il vincolo sul rapporto ora è completo — «deve restare
interno **e non può essere diffuso fuori dal gruppo di risposta prima della
chiusura**» — mentre prima la risposta si fermava a «deve restare interno». È
l'effetto diretto della voce di memoria più completa prodotta dalla riparazione.

**Q5, il peggioramento.** Prima il modello si asteneva sui punti aperti; ora ne
elenca quattro, e **nessuno è un punto aperto**. Fra questi compare «l'ipotesi del
caso non è stata cambiata per adesso», cioè la voce recuperata dalla riparazione,
vera solo fino alla sessione 2 e rimasta `attivo` fuori dalla catena di
supersessione: **è informazione obsoleta usata in una risposta**, e nella prima
prova non poteva accadere perché la voce non esisteva. Aggiunge inoltre «(in
attesa di risultati)», che il contesto non dice: affermazione non supportata.
Il punto aperto vero è al rango 12, fuori budget; il vettore non determinato ha
punteggio nullo.

**Q6, l'assenza di cambiamento.** I 240 MB, recuperati in memoria, restano al
rango 18: entrambe le prove si astengono, con le stesse parole. Il problema si è
spostato dalla memoria al ranking, e lì è rimasto.

### Conclusione della verifica

La modifica a U fa quello per cui è stata fatta — nessuna operazione perde
contenuto — ma su queste 7 domande **non migliora le risposte**: un
miglioramento (metà di Q5), un peggioramento (l'altra metà di Q5), un lieve
peggioramento (Q3), quattro invariati. Nessun problema tecnico bloccante.
