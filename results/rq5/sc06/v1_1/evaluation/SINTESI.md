# RQ5 / SC06 — sintesi (evaluation)

Configurazione `rq5-sc06-v1.1`. Celle attese: 8064; con risposta: 8064; errori di formato: 23; mancanti: 0.

Le due condizioni restano separate: non esiste un punteggio unico di SC06 e SC06 non viene mediato con SC01-SC05.

## Metriche principali

| Condizione | Metrica | Modello | Tasso | Numeratore | Denominatore |
|---|---|---|---:|---:|---:|
| sufficient | exact_match | Gemma 3 4B IT | 80.0% | 1613 | 2016 |
| sufficient | exact_match | Llama 3.2 3B Instruct | 79.6% | 1604 | 2016 |
| insufficient | correct_abstention | Gemma 3 4B IT | 85.4% | 1721 | 2016 |
| insufficient | correct_abstention | Llama 3.2 3B Instruct | 75.7% | 1527 | 2016 |

## Confronto appaiato fra i due modelli

Differenza assoluta in punti percentuali, Gemma 3 4B IT meno Llama 3.2 3B Instruct. Intervallo al 95% da bootstrap di 10000 campioni di episodi interi; nessun p-value.

| Condizione | Metrica | Famiglia | Differenza (pp) | IC 95% |
|---|---|---|---:|---|
| sufficient | exact_match | tutte | +0.4 | [-1.8, +2.7] |
| sufficient | exact_match | asset | +12.1 | [+4.9, +19.2] |
| sufficient | exact_match | data | -15.0 | [-18.6, -11.7] |
| sufficient | exact_match | variety | +0.6 | [-2.0, +3.0] |
| sufficient | exact_match | vector | +4.4 | [+2.1, +6.9] |
| insufficient | correct_abstention | tutte | +9.6 | [+7.2, +12.0] |
| insufficient | correct_abstention | asset | +34.3 | [+30.0, +38.5] |
| insufficient | correct_abstention | data | +24.1 | [+19.4, +28.7] |
| insufficient | correct_abstention | variety | -4.6 | [-9.1, +0.0] |
| insufficient | correct_abstention | vector | -13.9 | [-18.2, -9.6] |

## Metriche secondarie

| Condizione | Metrica | Modello | Tasso | Num. | Den. | Denominatore |
|---|---|---|---:|---:|---:|---|
| sufficient | format_error | Gemma 3 4B IT | 0.0% | 0 | 2016 | celle attese |
| sufficient | unsupported_value | Gemma 3 4B IT | 19.7% | 397 | 2016 | celle con output conforme |
| sufficient | cross_case_intrusion | Gemma 3 4B IT | 0.1% | 1 | 1310 | celle con output conforme e confusione rilevabile |
| sufficient | label_precision | Gemma 3 4B IT | 78.1% | 2056 | 2634 | etichette, celle con output conforme |
| sufficient | label_recall | Gemma 3 4B IT | 73.7% | 2056 | 2789 | etichette, celle con output conforme |
| insufficient | format_error | Gemma 3 4B IT | 0.0% | 0 | 2016 | celle attese |
| insufficient | unsupported_value | Gemma 3 4B IT | 14.6% | 295 | 2016 | celle con output conforme |
| insufficient | cross_case_intrusion | Gemma 3 4B IT | 11.4% | 149 | 1310 | celle con output conforme e confusione rilevabile |
| sufficient | format_error | Llama 3.2 3B Instruct | 0.7% | 14 | 2016 | celle attese |
| sufficient | unsupported_value | Llama 3.2 3B Instruct | 19.6% | 393 | 2002 | celle con output conforme |
| sufficient | cross_case_intrusion | Llama 3.2 3B Instruct | 1.8% | 23 | 1297 | celle con output conforme e confusione rilevabile |
| sufficient | label_precision | Llama 3.2 3B Instruct | 75.6% | 2139 | 2829 | etichette, celle con output conforme |
| sufficient | label_recall | Llama 3.2 3B Instruct | 77.6% | 2139 | 2755 | etichette, celle con output conforme |
| insufficient | format_error | Llama 3.2 3B Instruct | 0.4% | 9 | 2016 | celle attese |
| insufficient | unsupported_value | Llama 3.2 3B Instruct | 23.9% | 480 | 2007 | celle con output conforme |
| insufficient | cross_case_intrusion | Llama 3.2 3B Instruct | 24.1% | 313 | 1301 | celle con output conforme e confusione rilevabile |

## Prestazioni locali

Risultato secondario ed esplorativo; il riscaldamento e' escluso.

| Modello | Mediana (s) | 95º percentile (s) | Token/s (mediana) | Risposte |
|---|---:|---:|---:|---:|
| Gemma 3 4B IT | 0.85 | 1.10 | 36.5 | 4032 |
| Llama 3.2 3B Instruct | 0.40 | 0.75 | 44.0 | 4032 |

## Limiti dichiarati

- Il confronto riguarda due copie quantizzate eseguite in locale, non le famiglie Gemma e Llama in generale.
- Una generazione deterministica per cella non e' una replica stocastica.
- La confusione fra casi e' riportata solo sul sottoinsieme in cui e' rilevabile; le altre domande non dimostrano la sua assenza.
- `size_vram` di Ollama e' un'allocazione dichiarata dal runtime, non il picco di RAM misurato.
- Tokenizzazione e template interni restano propri di ogni modello.
