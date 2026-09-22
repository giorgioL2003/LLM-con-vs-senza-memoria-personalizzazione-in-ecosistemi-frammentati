# Verifica dei modelli locali — 22 settembre 2026

**Esito:** Gemma 3 4B e Llama 3.2 3B sono già installati e hanno completato una generazione locale sul Mac. È un controllo di avvio, non una valutazione RQ5.

## Ambiente

- MacBook Air, Apple M5, GPU 10 core, memoria unificata 24 GB.
- macOS 27.0 (26A428).
- Ollama client/server 0.34.2.
- Spazio libero rilevato: circa 216 GiB.

## Copie verificate

| Modello | Tag Ollama | Quantizzazione | Dimensione su disco indicata da Ollama |
|---|---|---|---|
| Gemma 3 4B IT, Google | `gemma3:4b` | Q4_K_M | 3,3 GB |
| Llama 3.2 3B Instruct, Meta | `llama3.2:3b` | Q4_K_M | 2,0 GB |

Q4_K_M indica la variante quantizzata: una rappresentazione dei pesi che riduce memoria e dimensione del modello. Le dimensioni su disco non rappresentano il consumo di RAM durante una prova.

## Controllo eseguito

Una richiesta per modello, uno alla volta, tramite API locale Ollama: «Rispondi soltanto con la parola OK.». Parametri: temperatura 0, seed 42, contesto 2048, massimo 16 token generati. Nessun dato del dataset è stato usato.

- Gemma: `OK` seguito da a capo.
- Llama: `OK.`. Ha aggiunto un punto: la generazione funziona, ma non corrisponde letteralmente all'istruzione. Non è stato corretto né rigenerato l'output.
- Entrambe le risposte sono terminate normalmente.
- Durante il caricamento Ollama ha riportato `size_vram == size` per entrambi. Le allocazioni sono conservate nei JSON e non equivalgono a una misura del picco RAM.
- I modelli sono stati scaricati dalla memoria dopo il controllo; rimangono installati sul disco.

## Decisione per il passo successivo

I due candidati sono tecnicamente utilizzabili per la piccola prova di sviluppo RQ5. Usarli uno alla volta. Contesto, parametri di generazione e misura delle risorse dell'esperimento restano da fissare. Il controllo non dimostra ancora qualità su VERIS né prestazioni su conversazioni lunghe.

Per confrontare solo il modello di risposta occorre conservare lo stesso testo recuperato e la stessa domanda; i token effettivi e i template interni possono differire. I digest delle copie locali sono in `summary.json`.

## Fonti ufficiali

- [Gemma 3 4B in Ollama](https://ollama.com/library/gemma3:4b)
- [Llama 3.2 3B in Ollama](https://ollama.com/library/llama3.2:3b)
- [Supporto macOS di Ollama](https://docs.ollama.com/macos)
- [API chat](https://docs.ollama.com/api/chat)
- [API modelli caricati](https://docs.ollama.com/api/ps)

Le richieste, le risposte e le allocazioni originali sono conservate accanto a questo file.
