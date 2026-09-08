#!/usr/bin/env python3
"""Memoria gerarchica GER: partizione per recenza e budget ripartito.

GER **non e' una memoria nuova**: e' un modo diverso di scegliere che cosa
entra nel contesto a partire dagli **stessi stati salvati di U**. Estrazione dei
fatti, proposta delle operazioni, rifiuto atomico e politica corrente/storia
restano quelli di `build_memory_updates.py`, che questo modulo non tocca: qui lo
stato viene soltanto **letto**.

Che cosa aggiunge:

  - divide le voci leggibili in **memoria recente** (create nelle ultime `W`
    sessioni) e **archivio** (tutte le altre), senza eliminare nulla;
  - interroga **sempre** tutti e due i gruppi;
  - calcola il ranking TF-IDF/coseno **prima** della divisione, sull'intero
    insieme dei candidati ammessi, cosi' i punteggi coincidono voce per voce con
    quelli di U;
  - riserva meta' budget per gruppo e lascia che lo spazio non speso passi
    all'altro;
  - conta il budget sulla riga **davvero formattata**, etichetta di livello
    compresa, e **non lo supera mai**: una voce troppo grande viene esclusa, non
    troncata, e il contesto puo' restare vuoto;
  - riceve dall'esterno la **sessione raggiunta**, cosi' la finestra avanza anche
    quando una sessione non produce aggiornamenti.

Le regole deterministiche (R1-R7) sono scritte in `MEMORIA_GERARCHICA.md`,
versione `ger-rules-0.2`. Solo libreria standard, nessuna chiamata a modelli.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import rq2_common as rq2  # noqa: E402
import build_memory_updates as memory  # noqa: E402

RULES_VERSION = "ger-rules-0.2"

# R1: finestra di recenza. Valore iniziale da verificare, non tarato.
RECENCY_WINDOW_SESSIONS = 2

LEVEL_RECENT = "recente"
LEVEL_ARCHIVE = "archivio"
LEVELS = (LEVEL_RECENT, LEVEL_ARCHIVE)

# Motivi di esclusione, scritti una volta sola per non divergere fra codice e
# traccia leggibile.
REASON_ZERO_SCORE = "punteggio nullo: nessun termine in comune con la domanda"
REASON_QUOTA_FULL = "non entra nella quota del livello"
REASON_QUOTA_CLOSED = "quota del livello gia' chiusa su un elemento precedente"
REASON_REUSE_FULL = "non entra nello spazio residuo"
REASON_REUSE_CLOSED = "spazio residuo gia' chiuso su un elemento precedente"
REASON_PHASE_1 = "entra nella quota del proprio livello"
REASON_PHASE_2 = "entra nello spazio residuo lasciato dall'altro livello"
REASON_OVER_BUDGET = "supera da sola l'intero budget: esclusa, non troncata"


# --------------------------------------------------------------------------
# R1 — Livello di una voce
# --------------------------------------------------------------------------

def last_session_order(entries):
    """Ultima sessione rappresentata nello stato salvato.

    Si guarda lo stato, non il file dello scenario: GER deve dipendere soltanto
    dagli stessi stati salvati di U.
    """
    if not entries:
        return 0
    return max(entry["session_order"] for entry in entries)


SESSION_SOURCE_DECLARED = "dichiarata dal chiamante"
SESSION_SOURCE_FALLBACK = "ripiego: ultima sessione con voci salvate"


def session_reached(entries, declared=None):
    """R1: qual e' la sessione a cui la conversazione (o lo stato) e' arrivata.

    E' l'informazione che definisce «le ultime due sessioni», e **non** coincide
    con l'ultima sessione che ha prodotto voci: se la sessione 9 non genera
    nessun aggiornamento, la finestra deve comunque essere 8-9, altrimenti resta
    ferma indietro e l'archivio si gonfia da solo.

    Va quindi passata esplicitamente da chi valuta lo stato. Senza dichiarazione
    si ripiega sull'ultima sessione con voci salvate: e' il comportamento
    prudente (non inventa sessioni future) ma non fa avanzare la finestra, e la
    traccia registra che si tratta di un ripiego.

    Una dichiarazione piu' vecchia delle voci salvate e' un errore: vorrebbe dire
    che lo stato contiene sessioni successive a quella dichiarata.
    """
    ultima_con_voci = last_session_order(entries)
    if declared is None:
        return ultima_con_voci, SESSION_SOURCE_FALLBACK
    declared = int(declared)
    if declared < ultima_con_voci:
        raise ValueError(
            "sessione raggiunta dichiarata %d, ma lo stato contiene voci fino alla %d"
            % (declared, ultima_con_voci))
    return declared, SESSION_SOURCE_DECLARED


def entry_level(entry, current_session, window=RECENCY_WINDOW_SESSIONS):
    """R1: recente se prodotta nelle ultime `window` sessioni, altrimenti archivio.

    `current_session` e' la sessione raggiunta, non l'ultima che ha prodotto
    voci: una sessione senza aggiornamenti fa comunque scorrere la finestra.

    `session_order` e' la sessione dell'operazione che ha prodotto la voce. In U
    un UPDATE crea una voce nuova, quindi «creata o aggiornata» coincide con
    «prodotta»: la versione aggiornata e' recente, quella superata resta dove sta
    il suo contenuto. Posizione e validita' restano proprieta' distinte: qui non
    si guarda mai `status`.
    """
    if entry["session_order"] >= current_session - window + 1:
        return LEVEL_RECENT
    return LEVEL_ARCHIVE


def recency_basis(entry):
    """Su che cosa si basa la data della voce, per la traccia.

    Un DELETE marca la voce `ritirato` senza crearne una nuova e lo stato non
    registra la sessione del ritiro: la voce conserva la sessione di creazione.
    E' un limite dichiarato, non un caso trattato in silenzio.
    """
    if entry["status"] == rq2.STATE_RETRACTED:
        return "creazione (la sessione del ritiro non e' registrata nello stato)"
    if entry["status"] == rq2.STATE_SUPERSEDED:
        return "creazione (la versione successiva e' una voce a se')"
    return "creazione"


# --------------------------------------------------------------------------
# R6 — Elementi di contesto
# --------------------------------------------------------------------------

def render_ger_entry(entry_id, level, state_label, source_message_ids, text):
    """Riga di GER: quella di U piu' l'etichetta di livello.

    L'etichetta costa circa due token ed e' dentro il budget come tutto il
    resto: e' un costo dell'architettura, non un dettaglio di presentazione.
    """
    return "[%s | %s | %s | da: %s] %s" % (
        entry_id, level, state_label, ", ".join(source_message_ids), text
    )


def ger_items(entries, scope, window=RECENCY_WINDOW_SESSIONS, current_session=None):
    """Elementi di contesto di GER, con livello ed etichetta gia' scritti.

    Le voci leggibili sono **esattamente** quelle di U per lo stesso ambito
    (`readable_entries`): GER non allarga ne' restringe l'informazione
    accessibile, cambia solo come viene ripartito lo spazio.

    `current_session` e' la sessione raggiunta (vedi `session_reached`). Se non
    viene passata si ripiega sull'ultima sessione con voci salvate.
    """
    if current_session is None:
        current_session, _ = session_reached(entries)
    items = []
    for entry in memory.readable_entries(entries, scope):
        level = entry_level(entry, current_session, window)
        render = render_ger_entry(
            entry["entry_id"], level, entry["status"], entry["source_message_ids"], entry["value"]
        )
        items.append(
            rq2.make_item(
                item_id=entry["entry_id"],
                text=entry["value"],
                render=render,
                session_order=entry["session_order"],
                item_order=entry["order"],
                source_message_ids=entry["source_message_ids"],
                source_fact_ids=entry["source_fact_ids"],
                unit="fatto con stato e livello",
                state=entry["status"],
                extra={
                    "claim_key": entry["claim_key"],
                    "level": level,
                    "recency_basis": recency_basis(entry),
                },
            )
        )
    items.sort(key=lambda item: (item["session_order"], item["item_order"]))
    return items


# --------------------------------------------------------------------------
# R3 — Quote
# --------------------------------------------------------------------------

def quotas(budget):
    """Meta' budget per gruppo. Il token dispari va all'archivio (R3)."""
    recent = budget // 2
    return {LEVEL_RECENT: recent, LEVEL_ARCHIVE: budget - recent}


# --------------------------------------------------------------------------
# R4, R5 — Selezione in due fasi
# --------------------------------------------------------------------------

def _decision(entry, outcome, phase, reason):
    return {
        "item_id": entry["item_id"],
        "level": entry["level"],
        "rank": entry["rank"],
        "score": entry["score"],
        "tokens": entry["tokens"],
        "outcome": outcome,
        "phase": phase,
        "reason": reason,
    }


def select_hierarchical(ranked, budget, min_score_exclusive=0.0,
                        window=RECENCY_WINDOW_SESSIONS):
    """Riempimento a quote piu' riutilizzo dello spazio avanzato.

    Fase 1: ogni gruppo scorre la classifica globale limitata ai propri elementi
    e si ferma al primo che non entra nella propria quota. Dentro il gruppo la
    selezione resta un prefisso della classifica, come in U, e i due gruppi sono
    indipendenti fra loro.

    Fase 2: lo spazio non speso torna a essere uno solo e viene offerto a tutti
    gli elementi rimasti, di entrambi i livelli, sempre in ordine di classifica
    e sempre fermandosi al primo che non entra.

    **Budget rigoroso (R5, regole 0.2).** Nessuna voce puo' far superare il
    budget: una voce piu' grande dell'intero budget viene esclusa con il proprio
    motivo, non troncata, e non esiste piu' la «garanzia minima» che la faceva
    entrare lo stesso. Se nessuna voce entra, il contesto resta vuoto.

    Come ogni altro elemento che non entra, una voce troppo grande **chiude** la
    fase in cui viene incontrata (prefisso della classifica, la regola di U): in
    fase 1 chiude la quota del proprio livello, in fase 2 chiude il riutilizzo.
    Se capita al primo posto della classifica il contesto resta vuoto: e' una
    conseguenza voluta della regola di prefisso, non un caso non trattato.

    Nessun elemento entra due volte e nessuno viene troncato.
    """
    quota = quotas(budget)
    admitted = [entry for entry in ranked if entry["score"] > min_score_exclusive]

    decisions = {}
    for entry in ranked:
        if entry["score"] <= min_score_exclusive:
            decisions[entry["item_id"]] = _decision(entry, "escluso", None, REASON_ZERO_SCORE)

    selected = []
    selected_ids = set()
    used_total = 0
    level_report = {}
    over_budget = []

    # ---- Fase 1: le quote -------------------------------------------------
    for level in LEVELS:
        group = [entry for entry in admitted if entry["level"] == level]
        used = 0
        stopped_by = None
        closed = False
        for entry in group:
            if closed:
                decisions[entry["item_id"]] = _decision(
                    entry, "escluso", 1, "%s (%s)" % (REASON_QUOTA_CLOSED, stopped_by["item_id"]))
                continue
            if used + entry["tokens"] <= quota[level]:
                selected.append(entry)
                selected_ids.add(entry["item_id"])
                used += entry["tokens"]
                decisions[entry["item_id"]] = _decision(entry, "selezionato", 1, REASON_PHASE_1)
                continue
            if entry["tokens"] > budget:
                motivo = "%s (%d token su un budget di %d)" % (
                    REASON_OVER_BUDGET, entry["tokens"], budget)
                over_budget.append(entry["item_id"])
            else:
                motivo = "%s: %d token, liberi %d su %d" % (
                    REASON_QUOTA_FULL, entry["tokens"], quota[level] - used, quota[level])
            stopped_by = {"item_id": entry["item_id"], "reason": motivo}
            decisions[entry["item_id"]] = _decision(entry, "escluso", 1, stopped_by["reason"])
            closed = True
        used_total += used
        level_report[level] = {
            "candidates": len(group),
            "quota_tokens": quota[level],
            "used_tokens": used,
            "unused_tokens": quota[level] - used,
            "selected_item_ids": [e["item_id"] for e in selected if e["level"] == level],
            "stopped_by": stopped_by,
        }

    # ---- Fase 2: riutilizzo dello spazio avanzato -------------------------
    reuse_available = budget - used_total
    reuse_used = 0
    reuse_stopped_by = None
    closed = False
    for entry in admitted:
        if entry["item_id"] in selected_ids:
            continue
        if closed:
            decisions[entry["item_id"]] = _decision(
                entry, "escluso", 2, "%s (%s)" % (REASON_REUSE_CLOSED, reuse_stopped_by["item_id"]))
            continue
        if used_total + entry["tokens"] <= budget:
            selected.append(entry)
            selected_ids.add(entry["item_id"])
            used_total += entry["tokens"]
            reuse_used += entry["tokens"]
            decisions[entry["item_id"]] = _decision(entry, "selezionato", 2, REASON_PHASE_2)
            level_report[entry["level"]]["selected_item_ids"].append(entry["item_id"])
            continue
        if entry["tokens"] > budget:
            motivo = "%s (%d token su un budget di %d)" % (
                REASON_OVER_BUDGET, entry["tokens"], budget)
            if entry["item_id"] not in over_budget:
                over_budget.append(entry["item_id"])
        else:
            motivo = "%s: %d token, residuo %d" % (
                REASON_REUSE_FULL, entry["tokens"], budget - used_total)
        reuse_stopped_by = {"item_id": entry["item_id"], "reason": motivo}
        decisions[entry["item_id"]] = _decision(entry, "escluso", 2, reuse_stopped_by["reason"])
        closed = True

    # R5: nessuna garanzia minima. Se nessuna voce entra, il contesto resta
    # vuoto: meglio un contesto vuoto e dichiarato che un budget sforato.

    # Nel prompt gli elementi restano in ordine di classifica (R6).
    selected.sort(key=lambda entry: entry["rank"])

    return {
        "selected": selected,
        "context_tokens": used_total,
        "content_tokens": sum(e.get("content_tokens", e["tokens"]) for e in selected),
        "overhead_tokens": sum(e.get("overhead_tokens", 0) for e in selected),
        "budget_tokens": budget,
        "stopped_by": reuse_stopped_by,
        # Resta nello schema per compatibilita' con il retrieval delle altre
        # modalita', ma in GER e' sempre falso: il budget non viene mai superato.
        "budget_exceeded_by_first_item": False,
        "excluded_over_budget": over_budget,
        "examined": len(ranked),
        "rules_version": RULES_VERSION,
        "recency_window_sessions": window,
        "quota_tokens": quota,
        "levels": level_report,
        "reuse": {
            "available_tokens": reuse_available,
            "used_tokens": reuse_used,
            "stopped_by": reuse_stopped_by,
        },
        "decisions": [decisions[entry["item_id"]] for entry in ranked],
    }


# --------------------------------------------------------------------------
# Una domanda
# --------------------------------------------------------------------------

def retrieve(question_text, entries, budget, window=RECENCY_WINDOW_SESSIONS,
             current_session=None):
    """Traccia completa di una domanda in GER.

    1. politica corrente/storia di U, invariata;
    2. elementi leggibili divisi in recente e archivio, rispetto alla sessione
       **raggiunta** (`current_session`, vedi `session_reached`);
    3. ranking TF-IDF/coseno su **tutti** i candidati, prima della divisione;
    4. riempimento a quote e riutilizzo dello spazio, entro il budget rigoroso.

    Nulla viene scritto: recuperare una voce non la rende recente. La sessione
    raggiunta arriva da chi valuta lo stato, non dalla domanda.
    """
    sessione, origine = session_reached(entries, current_session)
    scope = memory.question_scope(question_text)
    items = ger_items(entries, scope, window, sessione)
    ranked = rq2.rank_items(question_text, items)
    selection = select_hierarchical(ranked, budget, window=window)
    return {
        "scope": scope,
        "items": items,
        "ranked": ranked,
        "selection": selection,
        "readable_items": len(items),
        "session_reached": sessione,
        "session_reached_source": origine,
        "last_session_order": last_session_order(entries),
        "recency_window": [max(1, sessione - window + 1), sessione],
        "level_sizes": {
            level: len([item for item in items if item["level"] == level]) for level in LEVELS
        },
    }
