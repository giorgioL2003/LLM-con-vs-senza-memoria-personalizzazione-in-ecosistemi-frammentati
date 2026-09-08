# Traccia di GER su SC05 — verifica offline

**Non sono risultati sperimentali.** La memoria di SC05 e' costruita da fixture dichiarate (`tests/fixtures/rq2/scenario_05_*`), non dal modello, e nessuna risposta e' stata generata.

Regole `ger-rules-0.1`, finestra 2 sessioni, budget 200 token, quote 100/100.

La corrispondenza di provenienza **non** dimostra che il contenuto necessario sia nel contesto: le righe selezionate sono riportate per intero proprio per poterle leggere.

## SC05-Q1 — goal

**Domanda:** Qual è l'obiettivo dichiarato del caso ARD-19 sul portale fornitori?

Ambito di lettura: `current` | voci leggibili: 22 | recenti 5, in archivio 17 | quote: 100 / 100 token

Consumo: recente 91/100, archivio 70/100, spazio riutilizzato 35 (disponibile 39), totale 196/200 token.

| rango | elemento | livello | stato | punt. | token | esito | motivo |
|---:|---|---|---|---:|---:|---|---|
| 1 | `SC05-M002` | archivio | attivo | 0.520 | 38 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 2 | `SC05-M003` | archivio | attivo | 0.516 | 32 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 3 | `SC05-M001` | archivio | attivo | 0.485 | 35 | **selezionato** (fase 2) | entra nello spazio residuo lasciato dall'altro livello |
| 4 | `SC05-M005` | archivio | - | 0.190 | 35 | escluso | non entra nello spazio residuo: 35 token, residuo 4 |
| 5 | `SC05-M018` | archivio | - | 0.144 | 31 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 6 | `SC05-M030` | recente | attivo | 0.134 | 30 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 7 | `SC05-M010` | archivio | - | 0.131 | 26 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 8 | `SC05-M027` | recente | attivo | 0.108 | 29 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 9 | `SC05-M020` | archivio | - | 0.103 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 10 | `SC05-M028` | recente | attivo | 0.083 | 32 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 11 | `SC05-M007` | archivio | - | 0.083 | 33 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 12 | `SC05-M004` | archivio | - | 0.081 | 41 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 13 | `SC05-M021` | archivio | - | 0.057 | 37 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 14 | `SC05-M008` | archivio | - | 0.053 | 35 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |

8 elementi con punteggio nullo, esclusi come in U.

**Confronto con U** (stesso stato, stesse voci leggibili, stesso budget): U 6 elementi / 189 token, GER 6 elementi / 196 token. Solo in U: `SC05-M005`, `SC05-M018`. Solo in GER: `SC05-M027`, `SC05-M028`.

**Evidenze richieste** (la provenienza e' automatica, il contenuto va letto):

- *l'obiettivo del caso è stabilire quali dati dei fornitori siano stati esposti* — attesa dal livello indicato nell'annotazione, da `SC05-S1-U1`:
  - U: `SC05-M002` → [SC05-M002 | attivo | da: SC05-S1-U1] L'obiettivo del caso ARD-19 è riportare il portale in servizio senza interruzioni per i fornitori attivi.
  - U: `SC05-M003` → [SC05-M003 | attivo | da: SC05-S1-U1] È stato aperto il caso ARD-19 sul portale fornitori di Ardesia Mobilità.
  - U: `SC05-M001` → [SC05-M001 | attivo | da: SC05-S1-U1] L'obiettivo del caso ARD-19 è stabilire quali dati dei fornitori siano stati esposti.
  - GER: `SC05-M002` → [SC05-M002 | archivio | attivo | da: SC05-S1-U1] L'obiettivo del caso ARD-19 è riportare il portale in servizio senza interruzioni per i fornitori attivi.
  - GER: `SC05-M003` → [SC05-M003 | archivio | attivo | da: SC05-S1-U1] È stato aperto il caso ARD-19 sul portale fornitori di Ardesia Mobilità.
  - GER: `SC05-M001` → [SC05-M001 | archivio | attivo | da: SC05-S1-U1] L'obiettivo del caso ARD-19 è stabilire quali dati dei fornitori siano stati esposti.
- *l'obiettivo del caso è riportare il portale in servizio senza interruzioni per i fornitori attivi* — attesa dal livello indicato nell'annotazione, da `SC05-S1-U1`:
  - U: `SC05-M002` → [SC05-M002 | attivo | da: SC05-S1-U1] L'obiettivo del caso ARD-19 è riportare il portale in servizio senza interruzioni per i fornitori attivi.
  - U: `SC05-M003` → [SC05-M003 | attivo | da: SC05-S1-U1] È stato aperto il caso ARD-19 sul portale fornitori di Ardesia Mobilità.
  - U: `SC05-M001` → [SC05-M001 | attivo | da: SC05-S1-U1] L'obiettivo del caso ARD-19 è stabilire quali dati dei fornitori siano stati esposti.
  - GER: `SC05-M002` → [SC05-M002 | archivio | attivo | da: SC05-S1-U1] L'obiettivo del caso ARD-19 è riportare il portale in servizio senza interruzioni per i fornitori attivi.
  - GER: `SC05-M003` → [SC05-M003 | archivio | attivo | da: SC05-S1-U1] È stato aperto il caso ARD-19 sul portale fornitori di Ardesia Mobilità.
  - GER: `SC05-M001` → [SC05-M001 | archivio | attivo | da: SC05-S1-U1] L'obiettivo del caso ARD-19 è stabilire quali dati dei fornitori siano stati esposti.


## SC05-Q2 — update_obsolete

**Domanda:** Quale server era stato indicato inizialmente come esposto e quale risulta corretto dopo la revisione?

Ambito di lettura: `history` | voci leggibili: 26 | recenti 6, in archivio 20 | quote: 100 / 100 token

Consumo: recente 97/100, archivio 100/100, spazio riutilizzato 0 (disponibile 3), totale 197/200 token.

| rango | elemento | livello | stato | punt. | token | esito | motivo |
|---:|---|---|---|---:|---:|---|---|
| 1 | `SC05-M014` | archivio | attivo | 0.347 | 32 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 2 | `SC05-M006` | archivio | superato | 0.227 | 34 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 3 | `SC05-M013` | archivio | attivo | 0.225 | 34 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 4 | `SC05-M029` | recente | attivo | 0.202 | 36 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 5 | `SC05-M026` | recente | superato | 0.197 | 30 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 6 | `SC05-M024` | recente | attivo | 0.135 | 31 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 7 | `SC05-M012` | archivio | - | 0.118 | 36 | escluso | non entra nello spazio residuo: 36 token, residuo 3 |
| 8 | `SC05-M028` | recente | - | 0.116 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M012) |
| 9 | `SC05-M009` | archivio | - | 0.105 | 28 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M012) |
| 10 | `SC05-M003` | archivio | - | 0.094 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M012) |
| 11 | `SC05-M018` | archivio | - | 0.062 | 31 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M012) |
| 12 | `SC05-M005` | archivio | - | 0.058 | 35 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M012) |
| 13 | `SC05-M022` | archivio | - | 0.055 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M012) |
| 14 | `SC05-M004` | archivio | - | 0.042 | 41 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M012) |

12 elementi con punteggio nullo, esclusi come in U.

**Confronto con U** (stesso stato, stesse voci leggibili, stesso budget): U 6 elementi / 185 token, GER 6 elementi / 197 token. Solo in U: nessuno. Solo in GER: nessuno.

**Evidenze richieste** (la provenienza e' automatica, il contenuto va letto):

- *il server esposto era stato indicato in SRV-12* — attesa dal livello indicato nell'annotazione, da `SC05-S2-U1`:
  - U: `SC05-M006` → [SC05-M006 | superato | da: SC05-S2-U1] Il server esposto è SRV-12, che ospita il modulo di autenticazione del portale.
  - GER: `SC05-M006` → [SC05-M006 | archivio | superato | da: SC05-S2-U1] Il server esposto è SRV-12, che ospita il modulo di autenticazione del portale.
- *il server esposto è SRV-14, che ospita il modulo di esportazione delle anagrafiche* — attesa dal livello indicato nell'annotazione, da `SC05-S4-U1`:
  - U: `SC05-M014` → [SC05-M014 | attivo | da: SC05-S4-U1] SRV-12 era stato indicato per un errore di lettura dell'inventario.
  - U: `SC05-M013` → [SC05-M013 | attivo | da: SC05-S4-U1] Il server esposto è SRV-14, che ospita il modulo di esportazione delle anagrafiche.
  - GER: `SC05-M014` → [SC05-M014 | archivio | attivo | da: SC05-S4-U1] SRV-12 era stato indicato per un errore di lettura dell'inventario.
  - GER: `SC05-M013` → [SC05-M013 | archivio | attivo | da: SC05-S4-U1] Il server esposto è SRV-14, che ospita il modulo di esportazione delle anagrafiche.


## SC05-Q3 — pending_activity

**Domanda:** Quali verifiche restano aperte in questo momento sul caso ARD-19?

Ambito di lettura: `current` | voci leggibili: 22 | recenti 5, in archivio 17 | quote: 100 / 100 token

Consumo: recente 30/100, archivio 67/100, spazio riutilizzato 70 (disponibile 103), totale 167/200 token.

| rango | elemento | livello | stato | punt. | token | esito | motivo |
|---:|---|---|---|---:|---:|---|---|
| 1 | `SC05-M003` | archivio | attivo | 0.414 | 32 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 2 | `SC05-M001` | archivio | attivo | 0.358 | 35 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 3 | `SC05-M002` | archivio | attivo | 0.285 | 38 | **selezionato** (fase 2) | entra nello spazio residuo lasciato dall'altro livello |
| 4 | `SC05-M030` | recente | attivo | 0.123 | 30 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 5 | `SC05-M020` | archivio | attivo | 0.112 | 32 | **selezionato** (fase 2) | entra nello spazio residuo lasciato dall'altro livello |
| 6 | `SC05-M005` | archivio | - | 0.075 | 35 | escluso | non entra nello spazio residuo: 35 token, residuo 33 |
| 7 | `SC05-M004` | archivio | - | 0.055 | 41 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |

15 elementi con punteggio nullo, esclusi come in U.

**Confronto con U** (stesso stato, stesse voci leggibili, stesso budget): U 6 elementi / 190 token, GER 5 elementi / 167 token. Solo in U: `SC05-M005`. Solo in GER: nessuno.

**Evidenze richieste** (la provenienza e' automatica, il contenuto va letto):

- *resta aperta soltanto la revisione delle regole di esportazione su SRV-14* — attesa dal livello indicato nell'annotazione, da `SC05-S9-U1`:
  - U: nessun elemento con quella provenienza.
  - GER: nessun elemento con quella provenienza.


## SC05-Q4 — cross_session_link

**Domanda:** Quali verifiche restano da completare e il rapporto può già essere condiviso fuori dal gruppo di risposta?

Ambito di lettura: `current` | voci leggibili: 22 | recenti 5, in archivio 17 | quote: 100 / 100 token

Consumo: recente 93/100, archivio 76/100, spazio riutilizzato 0 (disponibile 31), totale 169/200 token.

| rango | elemento | livello | stato | punt. | token | esito | motivo |
|---:|---|---|---|---:|---:|---|---|
| 1 | `SC05-M004` | archivio | attivo | 0.563 | 41 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 2 | `SC05-M001` | archivio | attivo | 0.118 | 35 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 3 | `SC05-M005` | archivio | - | 0.115 | 35 | escluso | non entra nello spazio residuo: 35 token, residuo 31 |
| 4 | `SC05-M024` | recente | attivo | 0.112 | 31 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 5 | `SC05-M017` | archivio | - | 0.094 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 6 | `SC05-M022` | archivio | - | 0.073 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 7 | `SC05-M013` | archivio | - | 0.072 | 34 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 8 | `SC05-M021` | archivio | - | 0.064 | 37 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 9 | `SC05-M003` | archivio | - | 0.054 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 10 | `SC05-M028` | recente | attivo | 0.051 | 32 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 11 | `SC05-M018` | archivio | - | 0.047 | 31 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 12 | `SC05-M008` | archivio | - | 0.040 | 35 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 13 | `SC05-M009` | archivio | - | 0.031 | 28 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 14 | `SC05-M014` | archivio | - | 0.025 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 15 | `SC05-M030` | recente | attivo | 0.025 | 30 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 16 | `SC05-M020` | archivio | - | 0.023 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 17 | `SC05-M007` | archivio | - | 0.022 | 33 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 18 | `SC05-M002` | archivio | - | 0.021 | 38 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |
| 19 | `SC05-M029` | recente | - | 0.021 | 36 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M005) |

3 elementi con punteggio nullo, esclusi come in U.

**Confronto con U** (stesso stato, stesse voci leggibili, stesso budget): U 6 elementi / 194 token, GER 5 elementi / 169 token. Solo in U: `SC05-M005`, `SC05-M017`, `SC05-M022`. Solo in GER: `SC05-M028`, `SC05-M030`.

**Evidenze richieste** (la provenienza e' automatica, il contenuto va letto):

- *resta aperta la revisione delle regole di esportazione su SRV-14* — attesa dal livello indicato nell'annotazione, da `SC05-S9-U1`:
  - U: nessun elemento con quella provenienza.
  - GER: `SC05-M028` → [SC05-M028 | recente | attivo | da: SC05-S9-U1] La verifica del registro del bilanciatore è completata e conferma una sola sessione anomala.
- *prima della chiusura formale del caso il rapporto deve restare interno al gruppo di risposta e non può essere condiviso con altri reparti* — attesa dal livello indicato nell'annotazione, da `SC05-S1-U1`:
  - U: `SC05-M004` → [SC05-M004 | attivo | da: SC05-S1-U1] Prima della chiusura formale del caso il rapporto deve restare interno al gruppo di risposta e non può essere condiviso con altri reparti.
  - U: `SC05-M001` → [SC05-M001 | attivo | da: SC05-S1-U1] L'obiettivo del caso ARD-19 è stabilire quali dati dei fornitori siano stati esposti.
  - GER: `SC05-M004` → [SC05-M004 | archivio | attivo | da: SC05-S1-U1] Prima della chiusura formale del caso il rapporto deve restare interno al gruppo di risposta e non può essere condiviso con altri reparti.
  - GER: `SC05-M001` → [SC05-M001 | archivio | attivo | da: SC05-S1-U1] L'obiettivo del caso ARD-19 è stabilire quali dati dei fornitori siano stati esposti.


## SC05-Q5 — completed_activity

**Domanda:** Quali verifiche tecniche risultano completate sul caso ARD-19?

Ambito di lettura: `current` | voci leggibili: 22 | recenti 5, in archivio 17 | quote: 100 / 100 token

Consumo: recente 0/100, archivio 90/100, spazio riutilizzato 73 (disponibile 110), totale 163/200 token.

| rango | elemento | livello | stato | punt. | token | esito | motivo |
|---:|---|---|---|---:|---:|---|---|
| 1 | `SC05-M003` | archivio | attivo | 0.395 | 32 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 2 | `SC05-M001` | archivio | attivo | 0.342 | 35 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 3 | `SC05-M023` | archivio | attivo | 0.232 | 23 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 4 | `SC05-M002` | archivio | attivo | 0.172 | 38 | **selezionato** (fase 2) | entra nello spazio residuo lasciato dall'altro livello |
| 5 | `SC05-M005` | archivio | attivo | 0.072 | 35 | **selezionato** (fase 2) | entra nello spazio residuo lasciato dall'altro livello |
| 6 | `SC05-M004` | archivio | - | 0.053 | 41 | escluso | non entra nello spazio residuo: 41 token, residuo 37 |

16 elementi con punteggio nullo, esclusi come in U.

**Confronto con U** (stesso stato, stesse voci leggibili, stesso budget): U 6 elementi / 192 token, GER 5 elementi / 163 token. Solo in U: `SC05-M004`. Solo in GER: nessuno.

**Evidenze richieste** (la provenienza e' automatica, il contenuto va letto):

- *la verifica di integrità dei backup è completata e il risultato è regolare* — attesa dal livello indicato nell'annotazione, da `SC05-S8-U1`:
  - U: nessun elemento con quella provenienza.
  - GER: nessun elemento con quella provenienza.
- *la verifica del registro del bilanciatore è completata e conferma una sola sessione anomala* — attesa dal livello indicato nell'annotazione, da `SC05-S9-U1`:
  - U: nessun elemento con quella provenienza.
  - GER: nessun elemento con quella provenienza.


## SC05-Q6 — local_information

**Domanda:** Entro quanto tempo il cliente chiede di sapere se i dati dei fornitori sono stati esportati?

Ambito di lettura: `current` | voci leggibili: 22 | recenti 5, in archivio 17 | quote: 100 / 100 token

Consumo: recente 90/100, archivio 70/100, spazio riutilizzato 35 (disponibile 40), totale 195/200 token.

| rango | elemento | livello | stato | punt. | token | esito | motivo |
|---:|---|---|---|---:|---:|---|---|
| 1 | `SC05-M008` | archivio | attivo | 0.876 | 35 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 2 | `SC05-M001` | archivio | attivo | 0.263 | 35 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 3 | `SC05-M030` | recente | attivo | 0.146 | 30 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 4 | `SC05-M005` | archivio | attivo | 0.134 | 35 | **selezionato** (fase 2) | entra nello spazio residuo lasciato dall'altro livello |
| 5 | `SC05-M002` | archivio | - | 0.124 | 38 | escluso | non entra nello spazio residuo: 38 token, residuo 5 |
| 6 | `SC05-M027` | recente | attivo | 0.122 | 29 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 7 | `SC05-M024` | recente | attivo | 0.109 | 31 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 8 | `SC05-M003` | archivio | - | 0.097 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 9 | `SC05-M021` | archivio | - | 0.096 | 37 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 10 | `SC05-M017` | archivio | - | 0.084 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 11 | `SC05-M020` | archivio | - | 0.078 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 12 | `SC05-M010` | archivio | - | 0.074 | 26 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 13 | `SC05-M013` | archivio | - | 0.064 | 34 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 14 | `SC05-M018` | archivio | - | 0.042 | 31 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 15 | `SC05-M004` | archivio | - | 0.029 | 41 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 16 | `SC05-M009` | archivio | - | 0.028 | 28 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 17 | `SC05-M014` | archivio | - | 0.023 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 18 | `SC05-M022` | archivio | - | 0.020 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 19 | `SC05-M007` | archivio | - | 0.020 | 33 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |
| 20 | `SC05-M029` | recente | - | 0.019 | 36 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M002) |

2 elementi con punteggio nullo, esclusi come in U.

**Confronto con U** (stesso stato, stesse voci leggibili, stesso budget): U 6 elementi / 190 token, GER 6 elementi / 195 token. Solo in U: `SC05-M002`. Solo in GER: `SC05-M024`.

**Evidenze richieste** (la provenienza e' automatica, il contenuto va letto):

- *il cliente chiede di sapere entro dieci giorni lavorativi se i dati dei fornitori sono stati esportati* — attesa dal livello indicato nell'annotazione, da `SC05-S2-U2`:
  - U: `SC05-M008` → [SC05-M008 | attivo | da: SC05-S2-U2] Il cliente chiede di sapere entro dieci giorni lavorativi se i dati dei fornitori sono stati esportati.
  - GER: `SC05-M008` → [SC05-M008 | archivio | attivo | da: SC05-S2-U2] Il cliente chiede di sapere entro dieci giorni lavorativi se i dati dei fornitori sono stati esportati.


## SC05-Q7 — absent_information

**Domanda:** Quale fornitore esterno gestisce i backup del portale?

Ambito di lettura: `current` | voci leggibili: 22 | recenti 5, in archivio 17 | quote: 100 / 100 token

Consumo: recente 90/100, archivio 95/100, spazio riutilizzato 0 (disponibile 15), totale 185/200 token.

| rango | elemento | livello | stato | punt. | token | esito | motivo |
|---:|---|---|---|---:|---:|---|---|
| 1 | `SC05-M002` | archivio | attivo | 0.268 | 38 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 2 | `SC05-M030` | recente | attivo | 0.245 | 30 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 3 | `SC05-M024` | recente | attivo | 0.242 | 31 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 4 | `SC05-M018` | archivio | attivo | 0.202 | 31 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 5 | `SC05-M010` | archivio | attivo | 0.183 | 26 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 6 | `SC05-M027` | recente | attivo | 0.151 | 29 | **selezionato** (fase 1) | entra nella quota del proprio livello |
| 7 | `SC05-M020` | archivio | - | 0.144 | 32 | escluso | non entra nello spazio residuo: 32 token, residuo 15 |
| 8 | `SC05-M008` | archivio | - | 0.118 | 35 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M020) |
| 9 | `SC05-M028` | recente | - | 0.116 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M020) |
| 10 | `SC05-M003` | archivio | - | 0.090 | 32 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M020) |
| 11 | `SC05-M001` | archivio | - | 0.062 | 35 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M020) |
| 12 | `SC05-M005` | archivio | - | 0.059 | 35 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M020) |
| 13 | `SC05-M004` | archivio | - | 0.043 | 41 | escluso | spazio residuo gia' chiuso su un elemento precedente (SC05-M020) |

9 elementi con punteggio nullo, esclusi come in U.

**Confronto con U** (stesso stato, stesse voci leggibili, stesso budget): U 6 elementi / 173 token, GER 6 elementi / 185 token. Solo in U: nessuno. Solo in GER: nessuno.

**Evidenze richieste** (la provenienza e' automatica, il contenuto va letto):

- nessuna: la risposta corretta e' un'astensione.

