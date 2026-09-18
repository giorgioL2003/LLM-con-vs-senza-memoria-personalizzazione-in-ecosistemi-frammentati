# Completezza e supporto delle risposte

**Versione:** `completezza-supporto-1`, 18 settembre 2026.

Chiarimento operativo adottato durante la revisione dei risultati, dopo aver
osservato SC02-Q5/F. Esplicita come leggere insieme le classi di
`EXPERIMENT.md` §9.3, gli indicatori separati di §9.4 e la richiesta di risposte
«complete e supportate» di §10.3. Non è un criterio dichiarato prima delle prove.

## Regola comune

1. Valutare l'intera risposta rispetto all'oracle e alle conversazioni originali.
   Se contraddice l'oracle o usa come valida un'informazione superata, la classe
   è `errata`, anche quando alcuni fatti richiesti sono presenti.
2. Se contiene tutti i fatti obbligatori e non contiene contraddizioni, la
   classe è `completa`. Una precisazione aggiunta, assente dalle fonti ma non
   in contraddizione con esse, viene segnalata separatamente con
   `unsupported_claim: true`.
3. Se omette parte dei fatti richiesti e ne contiene almeno uno corretto,
   senza gli errori del punto 1, la classe è `parziale`. Anche questa classe
   può avere un'aggiunta non supportata.
4. L'astensione corretta mantiene la definizione del protocollo. Le risposte
   senza fatti utili o i casi ambigui si valutano secondo l'oracle e i criteri
   esistenti, documentando l'eventuale giudizio sospeso.

Non confondere «non supportato» con «dimostrato falso». Una contraddizione,
inclusa un'alterazione del resoconto delle attività, incide sulla classe; un
dettaglio aggiuntivo non verificabile incide sul supporto.

## Metriche

La classe `completa` misura la completezza rispetto alla richiesta e l'assenza
di contraddizioni. Non basta, da sola, per contare una risposta come successo.

`counts_as_complete_and_supported` è vero soltanto se la classe è `completa`
e tutta la risposta è supportata dalle conversazioni originali. Se il supporto
non è stato verificato, l'esito resta non disponibile.

- **Complete Answer Rate:** risposte complete e supportate / tutte le prove.
- **Answer Success condizionato al recupero:** risposte complete e supportate
  con evidenza completa nel contesto / prove con evidenza completa nel contesto.
- **Unsupported Claim Rate:** risposte con almeno un'affermazione non
  supportata / tutte le prove. Specificare separatamente l'origine dell'errore.

La fedeltà al contesto ricevuto resta distinta dal supporto rispetto alle
conversazioni: un fatto alterato nell'estrazione può essere ripetuto fedelmente
dal generatore e restare non supportato dalle fonti originali.

## Applicazione a SC02

| Caso | Classe | Supporto | Effetto sulle metriche |
|---|---|---|---|
| Q3/F: un test e il suo esito presentati come due verifiche | errata | affermazione non supportata | esclusa dai successi completi e supportati |
| Q4/F: test mobile completato presentato come ancora aperto | errata | informazione obsoleta | esclusa dai successi completi e supportati |
| Q5/F: tutti i fatti richiesti, più una data non fornita | completa | affermazione non supportata, introdotta nell'estrazione | esclusa dai successi completi e supportati |

La revisione r3 chiude la sospensione di Q5/F. F ha 3 risposte nella classe
`completa`, ma soltanto 2 complete e supportate: il tasso principale resta 2/7.

## Versioni e riuso

La regola è il riferimento comune per le successive schede RQ2 e RQ3. Le
valutazioni esistenti degli altri scenari devono essere confrontate con essa
prima di essere aggregate; non vengono riclassificate né approvate
automaticamente. Le metriche del pilot e i documenti originali restano nella
versione storica. Eventuali riallineamenti vanno documentati separatamente.

La precedente scheda SC02 è conservata in `SC02/archivio/r2/`. La chiusura del
caso sospeso non equivale al congelamento del protocollo o all'approvazione
scientifica delle prove di sviluppo.
