# Scenario 01 — Disegno narrativo dell'incidente

**Stato:** bozza v0.1, non congelata  
**Dominio:** cybersecurity difensiva  
**Tipo di attività:** gestione multi-sessione di un incidente  
**Scopo del documento:** definire i fatti e la loro distribuzione prima di scrivere dialoghi e domande.

## 1. Confine del caso

Lo scenario riguarda la continuità dell'indagine tra conversazioni. Non valuta la competenza generale del modello in cybersecurity e non contiene procedure offensive.

Tutti i nomi, gli account, gli indirizzi e gli eventi saranno sintetici. La correttezza delle risposte dipenderà soltanto dalle informazioni contenute nello scenario.

## 2. Contesto narrativo

Una società fittizia gestisce una piattaforma online per la condivisione di documenti. Il gruppo di sicurezza rileva un accesso anomalo effettuato attraverso un account di servizio con privilegi elevati.

L'indagine viene condotta in quattro sessioni separate con un assistente AI. Durante l'indagine, l'ipotesi iniziale viene superata da nuove evidenze, vengono completate alcune azioni di contenimento e rimane aperta una verifica sulla causa dell'esposizione.

## 3. Stato che deve evolvere

| Elemento | Stato previsto |
|---|---|
| Obiettivo | Capire come è stato usato `svc-reporting` e mettere in sicurezza la generazione dei report mensili senza interromperne la consultazione |
| Ipotesi iniziale | Compromissione della password dell'account di servizio |
| Evidenza successiva | L'accesso anomalo risulta autenticato tramite un token API, non tramite password |
| Ipotesi aggiornata | Esposizione del vecchio token API |
| Informazione obsoleta | La password compromessa come spiegazione corrente dell'accesso |
| Azione completata | Revoca di `reporting-v1` e attivazione di `reporting-v2`, limitato alla lettura di `monthly-reports` |
| Attività in sospeso | Individuare l'origine dell'esposizione e verificare se siano stati consultati documenti |
| Informazione locale | Scadenza del rapporto e scelta della verifica prioritaria comunicate nell'ultima sessione |
| Informazione mai fornita | Identità dell'autore dell'accesso anomalo |

## 4. Distribuzione tra le sessioni

### Sessione 1 — Apertura dell'indagine

Funzione narrativa:

- introdurre l'accesso anomalo;
- dichiarare l'obiettivo dell'indagine;
- formulare l'ipotesi iniziale della password compromessa;
- stabilire che i log di autenticazione devono essere controllati.

La sessione non deve anticipare l'esistenza del token esposto.

### Sessione 2 — Aggiornamento dell'ipotesi

Funzione narrativa:

- comunicare che i log non mostrano un'autenticazione riuscita tramite password;
- comunicare che l'accesso è stato effettuato tramite il vecchio token API;
- abbandonare esplicitamente l'ipotesi della password compromessa;
- decidere di revocare il token e sostituirlo con privilegi ridotti.

La sostituzione dell'ipotesi deve essere esplicita, in modo che l'oracle non dipenda da un'interpretazione implicita.

### Sessione 3 — Contenimento e attività pendente

Funzione narrativa:

- confermare la revoca del vecchio token;
- confermare l'attivazione del nuovo token a privilegi ridotti;
- registrare che gli accessi anomali sono cessati dopo il contenimento;
- lasciare in sospeso due verifiche: l'origine dell'esposizione e l'eventuale consultazione di documenti.

La cessazione degli accessi è un'osservazione dello scenario, non una dimostrazione generale della causa.

### Sessione 4 — Informazione locale e collegamento

Funzione narrativa:

- comunicare la scadenza del rapporto preliminare;
- specificare che il rapporto preliminare deve includere la verifica sull'origine dell'esposizione;
- stabilire che la verifica sull'eventuale consultazione di documenti può attendere il rapporto finale;
- non aggiungere il risultato delle verifiche ancora pendenti;
- preparare una domanda che richieda di collegare la priorità locale ai controlli definiti nella sessione 3.

## 5. Controlli di qualità prima dei dialoghi

- L'ipotesi iniziale e quella aggiornata non devono risultare entrambe valide.
- La revoca del token deve essere chiaramente completata.
- Le due verifiche devono essere chiaramente incomplete e distinguibili.
- La scadenza deve comparire soltanto nella sessione 4.
- L'identità dell'autore non deve comparire in nessuna sessione.
- I messaggi non devono richiedere conoscenze esterne per essere interpretati.
- Nessuna domanda di valutazione deve modificare lo stato dello scenario.
- Ogni domanda verrà eseguita su una copia indipendente dello stato al termine della sessione 4.

## 6. Passo successivo

Dopo la revisione di questo disegno verranno scritti:

1. i messaggi effettivi delle quattro sessioni;
2. le 5–7 domande di valutazione;
3. l'oracle manuale;
4. la matrice di raggiungibilità per C0, C1 e C2.

Il caso rimarrà una bozza modificabile fino alla verifica con l'oracle e alle prime esecuzioni del pilot.
