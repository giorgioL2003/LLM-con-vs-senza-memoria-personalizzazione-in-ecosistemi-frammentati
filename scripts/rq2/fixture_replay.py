#!/usr/bin/env python3
"""Riproduzione di risposte finte gia' scritte, al posto di una chiamata reale.

Serve a un solo scopo: far girare offline i costruttori di U e di G senza
chiamare Claude. Le risposte vengono da file di fixture dichiarati sotto
`tests/fixtures/rq2/` e **non sono uscite del modello**.

Non va usato per produrre risultati sperimentali: chi lo usa deve etichettare
gli output come `fixture`.
"""

from __future__ import annotations

import json
from pathlib import Path


def load_answers(path):
    with open(path, "r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not document.get("fixture"):
        raise ValueError("%s non e' dichiarato come fixture" % path)
    return document["answers"]


def make_runner(path, model="fixture (nessuna chiamata al modello)"):
    """Runner compatibile con i costruttori: restituisce le risposte in ordine.

    Se le chiamate sono piu' delle risposte previste, l'ultima chiamata riceve
    un errore esplicito invece di una risposta inventata.
    """
    answers = list(load_answers(Path(path)))
    state = {"index": 0}

    def runner(_prompt):
        if state["index"] >= len(answers):
            return None, None, "fixture esaurita: attese %d chiamate" % len(answers)
        answer = answers[state["index"]]
        state["index"] += 1
        return answer, model, None

    runner.answers = answers
    runner.state = state
    return runner
