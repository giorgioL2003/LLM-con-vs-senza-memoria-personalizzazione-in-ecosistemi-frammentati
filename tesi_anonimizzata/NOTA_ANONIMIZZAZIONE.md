# Nota sull'anonimizzazione dei materiali

I nomi delle organizzazioni fittizie presenti negli scenari sono stati
**sostituiti con denominazioni descrittive ai soli fini della presentazione
in tesi**.

**I risultati provengono dalle esecuzioni originali.** Nessun retrieval,
nessuna generazione e nessun calcolo di metrica è stato rieseguito: queste
copie sono una trasformazione puramente editoriale dei file prodotti dagli
esperimenti già svolti, che restano invariati nelle cartelle originali
(`data/`, `pilot/`, `results/`, `tests/`).

La sostituzione ha riguardato **esclusivamente le denominazioni** e gli
articoli e le preposizioni resi necessari dalla sostituzione. Non sono stati
modificati fatti, evidenze, classificazioni, giudizi, punteggi, metriche,
conteggi, configurazioni, identificatori di scenario, sessione, messaggio,
fatto o nodo, né alcuna porzione di codice.

## 1. Mappatura delle denominazioni

| Originale | Denominazione anonimizzata | Genere | Scenario e ruolo |
|---|---|---|---|
| Asteria Docs | il portale documentale | m. | scenario_01 (pilot) — piattaforma di condivisione documenti |
| Lumen Market | il servizio online | m. | scenario_02 (pilot) — piattaforma di commercio elettronico |
| Vesper Logistics | l'impresa logistica | f. | scenario_03 (RQ2) — azienda proprietaria dell'host `WS-114` |
| Corvara Servizi | l'azienda committente | f. | scenario_04 (RQ2) — organizzazione cliente, ufficio acquisti |
| RapidoPost | il corriere | m. | scenario_04 (RQ2) — servizio di consegna imitato dallo smishing |
| Ardesia Mobilità | la società di mobilità | f. | scenario_05 (RQ2, estensione GER) — titolare del portale fornitori |

Le sei denominazioni sono mutuamente distinte: `il corriere` resta separato da
`l'azienda committente` perché l'oracle di SC04 verifica che il gateway SMS
**non** venga attribuito al corriere imitato. Le due entità non vanno confuse.

### Nota su SC01 e SC02

Per questi due scenari la denominazione indica la **piattaforma**, non il suo
gestore, perché il testo sorgente le descrive come tali: «Asteria Docs, una
piattaforma di condivisione documenti» e «Lumen Market è una piattaforma di
commercio elettronico». Una designazione del tipo «gestore del portale»
avrebbe reso incoerenti quelle apposizioni, cambiando un fatto dello scenario.

### Esempi di resa

| Originale | Copia anonimizzata |
|---|---|
| un incidente per Asteria Docs, una piattaforma di condivisione documenti | un incidente per il portale documentale, una piattaforma di condivisione documenti |
| nel recupero password di Lumen Market | nel recupero password del servizio online |
| un caso sull'host `WS-114` di Vesper Logistics | un caso sull'host `WS-114` dell'impresa logistica |
| l'ufficio acquisti di Corvara Servizi | l'ufficio acquisti dell'azienda committente |
| imita il servizio di consegna RapidoPost | imita il servizio di consegna del corriere |
| sul portale fornitori di Ardesia Mobilità | sul portale fornitori della società di mobilità |

## 2. Identificatori derivati dai nomi

Tre identificatori tecnici di SC04 contenevano il nome aziendale. Sono stati
adeguati mantenendo forma, struttura e corrispondenza 1:1 (dominio, indirizzo
e URL restano gli stessi oggetti dello scenario):

| Originale | Anonimizzato |
|---|---|
| `acquisti-207@corvara.example` | `acquisti-207@sc04.example` |
| `accessi.corvara.example` | `accessi.sc04.example` |
| `hxxps://rapidopost-ritiro[.]example/track` | `hxxps://sc04b-ritiro[.]example/track` |

Tutti gli altri identificatori (`WS-114`, `UT-207`, `SMS-01`, `URL-01`,
`ACC-2`, `ARD-19`, `svc-reporting`, `reporting-v1`, `reset_audit`,
`account-portal`, la famiglia malware `Kelpie`, gli ID di fatto, nodo,
sessione e messaggio) sono invariati.

## 3. Verifiche eseguite

Su tutti i 110 file copiati:

- **Round-trip esatto**: applicando la mappatura inversa alle copie si
  riottiene l'originale byte per byte. Nessuna modifica oltre ai nomi.
- **Valori numerici**: 151.315 token numerici confrontati con un controllo
  indipendente dallo script di sostituzione, sequenza identica all'originale
  (punteggi, metriche, conteggi, rank, soglie, token).
- **Struttura dati**: tutti i file JSON/JSONL restano validi; chiavi e valori
  non testuali (numeri, booleani, null, giudizi codificati) identici.
- **Numero di righe** identico file per file.
- **Nessun residuo**: nessuna occorrenza dei nomi originali, in nessuna
  variante maiuscola/minuscola.

## 4. Materiali non trattati (binari)

I file binari non sono stati anonimizzati. Stato verificato:

| File | Nome presente | Azione |
|---|---|---|
| `slides/immagini/sc04_grafo_memoria.png` | sì — nodo `CASO-SC04` etichettato "Caso Corvara Servizi" | rigenerare con "Caso ufficio acquisti dell'azienda committente" |
| `come_è_fatto_il grafo.png` | sì — stessa immagine, stesso nodo | rigenerare |
| `diario_tirocinio_aggiornato.pdf` | sì — una occorrenza di "Asteria" | rigenerare dal sorgente |
| `slides/immagini/sc05_memoria_gerarchica.png` | no | utilizzabile così com'è |
| `RACCOLTA_RISULTATI/out/risultati.pdf` | no | utilizzabile così com'è |

L'estrazione di testo dai PDF non è esaustiva: prima della consegna conviene
una rilettura dei documenti rigenerati.

## 5. Riproducibilità

`anonimizza.py` in questa cartella rigenera le copie dagli originali e rifà
le verifiche del punto 3. Va eseguito dalla radice del progetto.
