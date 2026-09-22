# RQ5 / SC06 — sintesi (development)

Configurazione `rq5-sc06-v1.0`. Celle attese: 432; con risposta: 432; errori di formato: 2; mancanti: 0.

Le due condizioni restano separate: non esiste un punteggio unico di SC06 e SC06 non viene mediato con SC01-SC05.

## Metriche principali

| Condizione | Metrica | Modello | Tasso | Numeratore | Denominatore |
|---|---|---|---:|---:|---:|
| sufficient | exact_match | Gemma 3 4B IT | 85.2% | 92 | 108 |
| sufficient | exact_match | Llama 3.2 3B Instruct | 77.8% | 84 | 108 |
| insufficient | correct_abstention | Gemma 3 4B IT | 80.6% | 87 | 108 |
| insufficient | correct_abstention | Llama 3.2 3B Instruct | 81.5% | 88 | 108 |

## Confronto appaiato fra i due modelli

Differenza assoluta in punti percentuali, Gemma 3 4B IT meno Llama 3.2 3B Instruct. Intervallo al 95% da bootstrap di 10000 campioni di episodi interi; nessun p-value.

| Condizione | Metrica | Famiglia | Differenza (pp) | IC 95% |
|---|---|---|---:|---|
| sufficient | exact_match | tutte | +7.4 | [+0.0, +14.8] |
| sufficient | exact_match | asset | +16.0 | [-19.2, +51.9] |
| sufficient | exact_match | data | +3.3 | [+0.0, +11.1] |
| sufficient | exact_match | variety | +4.2 | [+0.0, +12.5] |
| sufficient | exact_match | vector | +6.9 | [+0.0, +15.6] |
| insufficient | correct_abstention | tutte | -0.9 | [-11.1, +9.3] |
| insufficient | correct_abstention | asset | +0.0 | [-20.0, +20.0] |
| insufficient | correct_abstention | data | +0.0 | [-21.4, +16.7] |
| insufficient | correct_abstention | variety | +4.2 | [-23.8, +36.0] |
| insufficient | correct_abstention | vector | -6.9 | [-20.7, +6.2] |

## Metriche secondarie

| Condizione | Metrica | Modello | Tasso | Num. | Den. | Denominatore |
|---|---|---|---:|---:|---:|---|
| sufficient | format_error | Gemma 3 4B IT | 0.0% | 0 | 108 | celle attese |
| sufficient | unsupported_value | Gemma 3 4B IT | 13.9% | 15 | 108 | celle con output conforme |
| sufficient | cross_case_intrusion | Gemma 3 4B IT | 0.0% | 0 | 74 | celle con output conforme e confusione rilevabile |
| sufficient | label_precision | Gemma 3 4B IT | 84.9% | 118 | 139 | etichette, celle con output conforme |
| sufficient | label_recall | Gemma 3 4B IT | 84.3% | 118 | 140 | etichette, celle con output conforme |
| insufficient | format_error | Gemma 3 4B IT | 0.0% | 0 | 108 | celle attese |
| insufficient | unsupported_value | Gemma 3 4B IT | 19.4% | 21 | 108 | celle con output conforme |
| insufficient | cross_case_intrusion | Gemma 3 4B IT | 18.9% | 14 | 74 | celle con output conforme e confusione rilevabile |
| sufficient | format_error | Llama 3.2 3B Instruct | 0.9% | 1 | 108 | celle attese |
| sufficient | unsupported_value | Llama 3.2 3B Instruct | 21.5% | 23 | 107 | celle con output conforme |
| sufficient | cross_case_intrusion | Llama 3.2 3B Instruct | 2.7% | 2 | 74 | celle con output conforme e confusione rilevabile |
| sufficient | label_precision | Llama 3.2 3B Instruct | 74.6% | 106 | 142 | etichette, celle con output conforme |
| sufficient | label_recall | Llama 3.2 3B Instruct | 78.5% | 106 | 135 | etichette, celle con output conforme |
| insufficient | format_error | Llama 3.2 3B Instruct | 0.9% | 1 | 108 | celle attese |
| insufficient | unsupported_value | Llama 3.2 3B Instruct | 17.8% | 19 | 107 | celle con output conforme |
| insufficient | cross_case_intrusion | Llama 3.2 3B Instruct | 21.6% | 16 | 74 | celle con output conforme e confusione rilevabile |

## Prestazioni locali

Risultato secondario ed esplorativo; il riscaldamento e' escluso.

| Modello | Mediana (s) | 95º percentile (s) | Token/s (mediana) | Risposte |
|---|---:|---:|---:|---:|
| Gemma 3 4B IT | 0.38 | 0.51 | 51.5 | 216 |
| Llama 3.2 3B Instruct | 0.26 | 0.52 | 58.9 | 216 |

## Limiti dichiarati

- Il confronto riguarda due copie quantizzate eseguite in locale, non le famiglie Gemma e Llama in generale.
- Una generazione deterministica per cella non e' una replica stocastica.
- La confusione fra casi e' riportata solo sul sottoinsieme in cui e' rilevabile; le altre domande non dimostrano la sua assenza.
- `size_vram` di Ollama e' un'allocazione dichiarata dal runtime, non il picco di RAM misurato.
- Tokenizzazione e template interni restano propri di ogni modello.
