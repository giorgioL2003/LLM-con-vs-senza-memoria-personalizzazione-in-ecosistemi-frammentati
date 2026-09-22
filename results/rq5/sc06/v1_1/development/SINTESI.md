# RQ5 / SC06 — sintesi (development)

Configurazione `rq5-sc06-v1.1`. Celle attese: 432; con risposta: 432; errori di formato: 2; mancanti: 0.

Le due condizioni restano separate: non esiste un punteggio unico di SC06 e SC06 non viene mediato con SC01-SC05.

## Metriche principali

| Condizione | Metrica | Modello | Tasso | Numeratore | Denominatore |
|---|---|---|---:|---:|---:|
| sufficient | exact_match | Gemma 3 4B IT | 83.3% | 90 | 108 |
| sufficient | exact_match | Llama 3.2 3B Instruct | 82.4% | 89 | 108 |
| insufficient | correct_abstention | Gemma 3 4B IT | 86.1% | 93 | 108 |
| insufficient | correct_abstention | Llama 3.2 3B Instruct | 80.6% | 87 | 108 |

## Confronto appaiato fra i due modelli

Differenza assoluta in punti percentuali, Gemma 3 4B IT meno Llama 3.2 3B Instruct. Intervallo al 95% da bootstrap di 10000 campioni di episodi interi; nessun p-value.

| Condizione | Metrica | Famiglia | Differenza (pp) | IC 95% |
|---|---|---|---:|---|
| sufficient | exact_match | tutte | +0.9 | [-7.4, +8.3] |
| sufficient | exact_match | asset | -4.0 | [-44.0, +34.8] |
| sufficient | exact_match | data | -3.3 | [-10.3, +0.0] |
| sufficient | exact_match | variety | +0.0 | [-12.5, +10.7] |
| sufficient | exact_match | vector | +10.3 | [+0.0, +25.0] |
| insufficient | correct_abstention | tutte | +5.6 | [-4.6, +14.8] |
| insufficient | correct_abstention | asset | +24.0 | [+0.0, +45.8] |
| insufficient | correct_abstention | data | +16.7 | [-3.4, +35.3] |
| insufficient | correct_abstention | variety | -12.5 | [-35.0, +8.0] |
| insufficient | correct_abstention | vector | -6.9 | [-16.7, +0.0] |

## Metriche secondarie

| Condizione | Metrica | Modello | Tasso | Num. | Den. | Denominatore |
|---|---|---|---:|---:|---:|---|
| sufficient | format_error | Gemma 3 4B IT | 0.0% | 0 | 108 | celle attese |
| sufficient | unsupported_value | Gemma 3 4B IT | 15.7% | 17 | 108 | celle con output conforme |
| sufficient | cross_case_intrusion | Gemma 3 4B IT | 0.0% | 0 | 74 | celle con output conforme e confusione rilevabile |
| sufficient | label_precision | Gemma 3 4B IT | 80.9% | 110 | 136 | etichette, celle con output conforme |
| sufficient | label_recall | Gemma 3 4B IT | 78.6% | 110 | 140 | etichette, celle con output conforme |
| insufficient | format_error | Gemma 3 4B IT | 0.0% | 0 | 108 | celle attese |
| insufficient | unsupported_value | Gemma 3 4B IT | 13.9% | 15 | 108 | celle con output conforme |
| insufficient | cross_case_intrusion | Gemma 3 4B IT | 13.5% | 10 | 74 | celle con output conforme e confusione rilevabile |
| sufficient | format_error | Llama 3.2 3B Instruct | 0.9% | 1 | 108 | celle attese |
| sufficient | unsupported_value | Llama 3.2 3B Instruct | 16.8% | 18 | 107 | celle con output conforme |
| sufficient | cross_case_intrusion | Llama 3.2 3B Instruct | 1.4% | 1 | 74 | celle con output conforme e confusione rilevabile |
| sufficient | label_precision | Llama 3.2 3B Instruct | 80.1% | 113 | 141 | etichette, celle con output conforme |
| sufficient | label_recall | Llama 3.2 3B Instruct | 83.7% | 113 | 135 | etichette, celle con output conforme |
| insufficient | format_error | Llama 3.2 3B Instruct | 0.9% | 1 | 108 | celle attese |
| insufficient | unsupported_value | Llama 3.2 3B Instruct | 18.7% | 20 | 107 | celle con output conforme |
| insufficient | cross_case_intrusion | Llama 3.2 3B Instruct | 20.5% | 15 | 73 | celle con output conforme e confusione rilevabile |

## Prestazioni locali

Risultato secondario ed esplorativo; il riscaldamento e' escluso.

| Modello | Mediana (s) | 95º percentile (s) | Token/s (mediana) | Risposte |
|---|---:|---:|---:|---:|
| Gemma 3 4B IT | 0.48 | 0.61 | 51.1 | 216 |
| Llama 3.2 3B Instruct | 0.25 | 0.48 | 60.0 | 216 |

## Limiti dichiarati

- Il confronto riguarda due copie quantizzate eseguite in locale, non le famiglie Gemma e Llama in generale.
- Una generazione deterministica per cella non e' una replica stocastica.
- La confusione fra casi e' riportata solo sul sottoinsieme in cui e' rilevabile; le altre domande non dimostrano la sua assenza.
- `size_vram` di Ollama e' un'allocazione dichiarata dal runtime, non il picco di RAM misurato.
- Tokenizzazione e template interni restano propri di ogni modello.
