# SC06 — esempio del formato proposto

Fatti derivati da VERIS; messaggi costruiti automaticamente. Nessuna risposta del modello è stata generata.

## SC06-E001

Memorizza le informazioni fornite sui tre casi di cybersecurity. I nomi Caso A, Caso B e Caso C identificano casi distinti. Le etichette tecniche provengono da VERIS: preservale come sono scritte.

### SC06-E001-S1

Caso A. Dati registrati nella scheda:
- Tipologie di hacking: Brute force

Caso B. Dati registrati nella scheda:
- Tipologie di ingegneria sociale: Pretexting

Caso C. Dati registrati nella scheda:
- Tipologie di malware: Ransomware
- Tipologie di ingegneria sociale: Phishing

### SC06-E001-S2

Caso B. Dati registrati nella scheda:
- Vettori di ingegneria sociale: Email

Caso C. Dati registrati nella scheda:
- Vettori di malware: Direct install
- Vettori di ingegneria sociale: Email

Caso A. Dati registrati nella scheda:
- Vettori di hacking: Web application

### SC06-E001-S3

Caso C. Dati registrati nella scheda:
- Categorie di dati: Personal

Caso A. Dati registrati nella scheda:
- Tipi di risorse coinvolte: S - Web application
- Categorie di dati: Bank

Caso B. Dati registrati nella scheda:
- Tipi di risorse coinvolte: P - Human resources
- Categorie di dati: Personal

### Sessione successiva: domande

Ogni domanda parte dalla stessa memoria finale, in una conversazione nuova. Le risposte attese qui sotto sono solo per la valutazione e non vanno mostrate al modello.

- **SC06-E001-A-Q1:** Per Caso A, quali valori erano stati riportati nel campo «Tipi di risorse coinvolte»? Riporta tutte e sole le etichette fornite, senza tradurle. Rispondi con JSON {"values": ["etichetta"]}; se non hai informazioni sufficienti, rispondi con {"values": []}.
  - Atteso: S - Web application
  - Evidenza: SC06-E001-S3-M2

- **SC06-E001-A-Q2:** Per Caso A, quali valori erano stati riportati nel campo «Categorie di dati»? Riporta tutte e sole le etichette fornite, senza tradurle. Rispondi con JSON {"values": ["etichetta"]}; se non hai informazioni sufficienti, rispondi con {"values": []}.
  - Atteso: Bank
  - Evidenza: SC06-E001-S3-M2

- **SC06-E001-A-Q3:** Per Caso A, quali valori erano stati riportati nel campo «Tipologie di hacking»? Riporta tutte e sole le etichette fornite, senza tradurle. Rispondi con JSON {"values": ["etichetta"]}; se non hai informazioni sufficienti, rispondi con {"values": []}.
  - Atteso: Brute force
  - Evidenza: SC06-E001-S1-M1

- **SC06-E001-B-Q1:** Per Caso B, quali valori erano stati riportati nel campo «Vettori di ingegneria sociale»? Riporta tutte e sole le etichette fornite, senza tradurle. Rispondi con JSON {"values": ["etichetta"]}; se non hai informazioni sufficienti, rispondi con {"values": []}.
  - Atteso: Email
  - Evidenza: SC06-E001-S2-M1

- **SC06-E001-B-Q2:** Per Caso B, quali valori erano stati riportati nel campo «Tipi di risorse coinvolte»? Riporta tutte e sole le etichette fornite, senza tradurle. Rispondi con JSON {"values": ["etichetta"]}; se non hai informazioni sufficienti, rispondi con {"values": []}.
  - Atteso: P - Human resources
  - Evidenza: SC06-E001-S3-M3

- **SC06-E001-B-Q3:** Per Caso B, quali valori erano stati riportati nel campo «Categorie di dati»? Riporta tutte e sole le etichette fornite, senza tradurle. Rispondi con JSON {"values": ["etichetta"]}; se non hai informazioni sufficienti, rispondi con {"values": []}.
  - Atteso: Personal
  - Evidenza: SC06-E001-S3-M3

- **SC06-E001-C-Q1:** Per Caso C, quali valori erano stati riportati nel campo «Tipologie di ingegneria sociale»? Riporta tutte e sole le etichette fornite, senza tradurle. Rispondi con JSON {"values": ["etichetta"]}; se non hai informazioni sufficienti, rispondi con {"values": []}.
  - Atteso: Phishing
  - Evidenza: SC06-E001-S1-M3

- **SC06-E001-C-Q2:** Per Caso C, quali valori erano stati riportati nel campo «Vettori di malware»? Riporta tutte e sole le etichette fornite, senza tradurle. Rispondi con JSON {"values": ["etichetta"]}; se non hai informazioni sufficienti, rispondi con {"values": []}.
  - Atteso: Direct install
  - Evidenza: SC06-E001-S2-M2

- **SC06-E001-C-Q3:** Per Caso C, quali valori erano stati riportati nel campo «Categorie di dati»? Riporta tutte e sole le etichette fornite, senza tradurle. Rispondi con JSON {"values": ["etichetta"]}; se non hai informazioni sufficienti, rispondi con {"values": []}.
  - Atteso: Personal
  - Evidenza: SC06-E001-S3-M1

## Provenienza dei tre casi

- Caso A: `95B8C160-47EC-4415-8504-A3F8D13ED9AC`, `data/json/validated/95B8C160-47EC-4415-8504-A3F8D13ED9AC.json`.
  - Riferimento registrato in VERIS: http://news.softpedia.com/news/More-Than-13-000-Bitcoins-Stolen-in-Linode-Hack-256467.shtml; http://status.linode.com/2012/03/manager-security-incident.html 

- Caso B: `349A6A42-9E69-4020-B8DC-9693BCE6A450`, `data/json/validated/C638A7C7-7D6B-4C63-8451-50A88A1CF25B.json`.
  - Riferimento registrato in VERIS: http://www.bizjournals.com/jacksonville/news/2016/04/27/landstars-data-breach-larger-than-initially.html

- Caso C: `8f722150-a118-11ea-878c-ff8a51fa1e8f`, `data/json/validated/2a074bee-5cae-4a2b-a7b4-28d9862f6a02.json`.
  - Riferimento registrato in VERIS: https://www.foxbusiness.com/technology/hacker-hits-magellan-health-with-ransomware-attack; https://www.infosecurity-magazine.com/news/us-health-giant-hooked-with/; https://www.scmagazine.com/home/security-news/magellan-health-warns-ransomware-attack-exposed-pii/
