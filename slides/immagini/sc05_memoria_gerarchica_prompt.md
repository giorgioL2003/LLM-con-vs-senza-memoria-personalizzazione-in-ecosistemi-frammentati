# Prompt immagine SC05

Modalità: strumento integrato ImageGen. Generazione dell'8 settembre 2026.

Il diagramma usa i dati di SC05-Q2 in `results/rq2/sc05_dev_v1/retrieval_sc05_u_ger.jsonl`. Il limite di 200 token riguarda il contesto recuperato, non la capacità dell'archivio né tutta la finestra di contesto del modello.

## Prompt di generazione

Create a clean Italian scientific infographic, 16:9, off-white background, navy text, teal and orange accents. Title 'Memoria Gerarchica: dalla memoria al contesto'. Subtitle 'SC05 · Ispirazione da MemGPT e dalla memoria virtuale'. Left group 'Memoria esterna — stato di U' has two stacked boxes: 'Memoria recente — Sessioni 8–9 · 8 voci' and 'Archivio — Sessioni 1–7 · 26 voci'. Both connect rightward to 'Selezione per la domanda — TF-IDF — Quote iniziali: 100 token per livello — Riutilizzo dello spazio residuo'. This connects rightward to 'Contesto recuperato — Massimo 200 token', then rightward to 'Claude', then downward to 'Risposta'. A small 'Domanda' above selection points down into selection. Recent and archive are both external storage, not RAM; 100 token is the retrieval quota, not storage capacity. No arrows back from Claude to memory. Bottom separate example: 'SC05: correzione SRV-12 → SRV-14'; 'Archivio: 83 token selezionati · Recente: 93 token selezionati'; 'Residuo: 24 token · Correzione: 37 token'; 'Conservata in memoria, esclusa dal contesto'. Footer 'Conteggio locale dei token. Analogia funzionale, non paginazione di un sistema operativo.' Large very legible text, ample spacing, restrained flat technical diagram. Exact arrows and quantities, no extra stages.
