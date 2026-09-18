#!/usr/bin/env python3
"""Copie anonimizzate dei materiali della tesi.

Sostituisce SOLO le denominazioni delle organizzazioni fittizie con
designazioni descrittive coerenti con il ruolo di ciascuna entita' nello
scenario, adattando articoli e preposizioni per rendere il testo naturale.

Verifica per round-trip: applicando la mappatura inversa alle copie si deve
riottenere l'originale byte per byte. Nient'altro puo' quindi essere cambiato.
"""
import os, re, shutil, sys, json

ROOT = "/Users/giorgiolai/Desktop/progetto_tirocinio"
DEST = os.path.join(ROOT, "tesi_anonimizzata")
SKIP_DIRS = {".git", ".idea", "tesi_anonimizzata"}
SKIP_PATHS = {"RACCOLTA_RISULTATI/out"}

NAMES = ["Asteria Docs", "Lumen Market", "Vesper Logistics",
         "Corvara Servizi", "Ardesia Mobilità", "RapidoPost"]
IDENT_MAP = [("corvara.example", "sc04.example"),
             ("rapidopost-ritiro", "sc04b-ritiro")]

# Denominazione descrittiva per scenario, con genere e articolo.
LABEL = {
    "Asteria Docs":     "portale documentale",     # SC01  m.  il / del
    "Lumen Market":     "servizio online",         # SC02  m.  il / del
    "Vesper Logistics": "impresa logistica",       # SC03  f.  l' / dell'
    "Corvara Servizi":  "azienda committente",     # SC04  f.  l' / dell'
    "Ardesia Mobilità": "corriere",                # SC04-B m. il / del
    "RapidoPost":       "corriere",
}

# (pattern forward, sostituzione, stringa inversa, ripristino)
# Ordinate dalla piu' specifica alla piu' generica.
RULES = [
    # --- SC01 / SC02 insieme: elenco nella roadmap ---
    (r"scenari, Asteria Docs e Lumen Market",
     "scenari, il portale documentale e il servizio online",
     "scenari, il portale documentale e il servizio online",
     "scenari, Asteria Docs e Lumen Market"),

    # --- SC01: portale documentale (m.) ---
    (r"incidente Asteria Docs", "incidente del portale documentale",
     "incidente del portale documentale", "incidente Asteria Docs"),
    (r"\bper Asteria Docs", "per il portale documentale",
     "per il portale documentale", "per Asteria Docs"),
    (r"SC01 - Asteria Docs", "SC01 - portale documentale",
     "SC01 - portale documentale", "SC01 - Asteria Docs"),
    (r"SC01 Asteria Docs", "SC01 portale documentale",
     "SC01 portale documentale", "SC01 Asteria Docs"),
    (r"Asteria Docs", "il portale documentale",
     "il portale documentale", "Asteria Docs"),

    # --- SC02: servizio online (m.) ---
    (r"Lumen Market è una piattaforma", "Il servizio online è una piattaforma",
     "Il servizio online è una piattaforma", "Lumen Market è una piattaforma"),
    (r"\bdi Lumen Market", "del servizio online",
     "del servizio online", "di Lumen Market"),
    (r"SC02 - Lumen Market", "SC02 - servizio online",
     "SC02 - servizio online", "SC02 - Lumen Market"),
    (r"SC02 Lumen Market", "SC02 servizio online",
     "SC02 servizio online", "SC02 Lumen Market"),
    (r"Lumen Market", "il servizio online",
     "il servizio online", "Lumen Market"),

    # --- SC03: impresa logistica (f., vocale) ---
    (r"\bdi Vesper Logistics", "dell'impresa logistica",
     "dell'impresa logistica", "di Vesper Logistics"),
    (r"Vesper Logistics", "l'impresa logistica",
     "l'impresa logistica", "Vesper Logistics"),

    # --- SC04: azienda committente (f., vocale) ---
    (r"Caso ufficio acquisti Corvara Servizi",
     "Caso ufficio acquisti dell'azienda committente",
     "Caso ufficio acquisti dell'azienda committente",
     "Caso ufficio acquisti Corvara Servizi"),
    (r"\bdi Corvara Servizi", "dell'azienda committente",
     "dell'azienda committente", "di Corvara Servizi"),
    (r"\bsu Corvara Servizi", "sull'azienda committente",
     "sull'azienda committente", "su Corvara Servizi"),
    (r"Corvara Servizi", "l'azienda committente",
     "l'azienda committente", "Corvara Servizi"),

    # --- SC04-B: corriere (m.) ---
    (r"il servizio di consegna RapidoPost", "il servizio di consegna del corriere",
     "il servizio di consegna del corriere", "il servizio di consegna RapidoPost"),
    (r"il servizio RapidoPost", "il servizio del corriere",
     "il servizio del corriere", "il servizio RapidoPost"),
    (r"\ba RapidoPost", "al corriere", "al corriere", "a RapidoPost"),
    (r"RapidoPost", "il corriere", "il corriere", "RapidoPost"),

    # --- SC05: societa' di mobilita' (f., consonante) ---
    (r"\bdi Ardesia Mobilità", "della società di mobilità",
     "della società di mobilità", "di Ardesia Mobilità"),
    (r"Ardesia Mobilità", "la società di mobilità",
     "la società di mobilità", "Ardesia Mobilità"),
]

INVERSE = sorted(RULES, key=lambda r: len(r[2]), reverse=True)


def anonymize(text):
    for src, dst in IDENT_MAP:
        text = text.replace(src, dst)
    for pat, rep, _, _ in RULES:
        text = re.sub(pat, rep, text)
    return text


def deanonymize(text):
    for _, _, ifrom, ito in INVERSE:
        text = text.replace(ifrom, ito)
    for src, dst in IDENT_MAP:
        text = text.replace(dst, src)
    return text


def main():
    targets = []
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.startswith("."):
                continue
            p = os.path.join(root, f)
            r = os.path.relpath(p, ROOT)
            if any(r.startswith(s) for s in SKIP_PATHS):
                continue
            try:
                t = open(p, encoding="utf-8").read()
            except (UnicodeDecodeError, OSError):
                continue
            if any(n in t for n in NAMES) or any(i in t for i, _ in IDENT_MAP):
                targets.append((r, p, t))

    if os.path.exists(DEST):
        shutil.rmtree(DEST)

    report, failures = [], []
    for r, p, orig in sorted(targets):
        new = anonymize(orig)
        if deanonymize(new) != orig:
            failures.append((r, "round-trip non esatto")); continue
        res = [n for n in NAMES if n in new] + \
              [w for w in ("Corvara", "Asteria", "Lumen", "Vesper", "Ardesia",
                           "RapidoPost", "corvara", "rapidopost") if w in new]
        if res:
            failures.append((r, "residuo: " + ",".join(sorted(set(res))))); continue
        try:
            if r.endswith(".json"):
                json.loads(new)
            elif r.endswith(".jsonl"):
                for line in new.splitlines():
                    if line.strip():
                        json.loads(line)
        except Exception as e:
            failures.append((r, "JSON non valido: %s" % e)); continue

        out = os.path.join(DEST, r)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(new)
        shutil.copystat(p, out)
        report.append((r, sum(orig.count(n) for n in NAMES)
                        + sum(orig.count(i) for i, _ in IDENT_MAP)))

    print("File anonimizzati:   %d" % len(report))
    print("Sostituzioni totali: %d" % sum(n for _, n in report))
    if failures:
        print("\n!!! FALLITI: %d" % len(failures))
        for r, why in failures:
            print("   %-62s %s" % (r, why))
        sys.exit(1)
    print("Verifica round-trip: OK su tutti i file")


if __name__ == "__main__":
    main()
