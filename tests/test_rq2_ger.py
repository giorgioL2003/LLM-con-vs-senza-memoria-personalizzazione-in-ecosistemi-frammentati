#!/usr/bin/env python3
"""Verifiche mirate della memoria gerarchica GER.

Si controllano le proprieta' che, se saltassero, renderebbero il confronto
U/GER privo di senso:

  - la recenza dipende dalla sessione della voce, non dal fatto di essere stata
    recuperata e nemmeno dal suo stato;
  - il ranking e' calcolato prima della divisione, quindi i punteggi coincidono
    con quelli di U voce per voce;
  - quote, riutilizzo dello spazio, assenza di doppioni e di troncamenti;
  - il budget conta la riga formattata, etichetta di livello compresa;
  - U, la matrice e i confronti gia' eseguiti non cambiano.
"""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rq2"))

import rq2_common as rq2  # noqa: E402
import build_memory_updates as memory  # noqa: E402
import hierarchical_memory as ger  # noqa: E402
import run_retrieval_rq2 as retrieval_rq2  # noqa: E402
import fixture_replay  # noqa: E402

FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "rq2"
SC05_FACTS = FIXTURE_DIR / "scenario_05_facts_fixture.jsonl"
SC05_UPDATES = FIXTURE_DIR / "scenario_05_update_answers_fixture.json"
SC03_STATE = REPO_ROOT / "results" / "rq2" / "memory_repair_v3" / "scenario_03_state.json"
SC03_FACTS = REPO_ROOT / "results" / "rq2" / "facts" / "scenario_03_facts.jsonl"
SC03_RETRIEVAL = REPO_ROOT / "results" / "rq2" / "retrieval_repair_v3" / "retrieval_sc03_u.jsonl"
SC04_STATE = REPO_ROOT / "results" / "rq2" / "sc04_repair_v3" / "scenario_04_state.json"
SESSIONI_SC03 = 4
RUN_CONFIG = REPO_ROOT / "data" / "rq2" / "config" / "run_sc05_ger_dev.json"


def voce(entry_id, session_order, order, value, status=rq2.STATE_ACTIVE, superseded=None):
    return {
        "entry_id": entry_id, "claim_key": entry_id.lower(), "value": value, "status": status,
        "source_fact_ids": ["F-%s" % entry_id], "source_message_ids": ["M-%s" % entry_id],
        "session_id": "S%d" % session_order, "session_order": session_order, "order": order,
        "created_by_op": "OP-%s" % entry_id, "superseded_by_op": None,
        "superseded_by_entry": superseded,
    }


def elemento(item_id, level, score, tokens, rank):
    """Elemento gia' classificato, con il costo che serve al caso in prova."""
    return {
        "item_id": item_id, "level": level, "score": score, "tokens": tokens, "rank": rank,
        "content_tokens": tokens - 5, "overhead_tokens": 5,
        "render": "[%s] testo" % item_id, "text": "testo", "unit": "fatto con stato e livello",
        "session_order": 1, "item_order": rank, "source_message_ids": [], "state": rq2.STATE_ACTIVE,
    }


def classifica(*elementi):
    return list(elementi)


class TestRecenza(unittest.TestCase):
    """R1: quale sessione conta, e che cosa non conta."""

    def setUp(self):
        self.entries = [
            voce("M1", 1, 1, "decisione lontana ancora valida"),
            voce("M2", 2, 2, "versione vecchia", status=rq2.STATE_SUPERSEDED, superseded="M5"),
            voce("M3", 3, 3, "evidenza ritirata", status=rq2.STATE_RETRACTED),
            voce("M4", 8, 4, "attivita' recente"),
            voce("M5", 9, 5, "versione corretta"),
        ]

    def test_finestra_di_due_sessioni(self):
        ultima, origine = ger.session_reached(self.entries)
        self.assertEqual(ultima, 9)
        self.assertEqual(origine, ger.SESSION_SOURCE_FALLBACK)
        livelli = {e["entry_id"]: ger.entry_level(e, ultima) for e in self.entries}
        self.assertEqual(livelli["M4"], ger.LEVEL_RECENT)
        self.assertEqual(livelli["M5"], ger.LEVEL_RECENT)
        self.assertEqual(livelli["M1"], ger.LEVEL_ARCHIVE)
        self.assertEqual(livelli["M2"], ger.LEVEL_ARCHIVE)
        self.assertEqual(livelli["M3"], ger.LEVEL_ARCHIVE)

    def test_vecchio_non_significa_superato(self):
        """Posizione e validita' sono assi indipendenti."""
        ultima, _ = ger.session_reached(self.entries)
        vecchia = [e for e in self.entries if ger.entry_level(e, ultima) == ger.LEVEL_ARCHIVE]
        self.assertIn(rq2.STATE_ACTIVE, [e["status"] for e in vecchia])
        # e la voce superata non torna recente per il fatto di essere stata sostituita
        superata = next(e for e in self.entries if e["entry_id"] == "M2")
        self.assertEqual(ger.entry_level(superata, ultima), ger.LEVEL_ARCHIVE)
        self.assertIn("creazione", ger.recency_basis(superata))

    def test_sessione_senza_nuove_voci_fa_avanzare_la_finestra(self):
        """Le sessioni 10 e 11 non producono voci: la finestra deve comunque scorrere."""
        raggiunta, origine = ger.session_reached(self.entries, declared=11)
        self.assertEqual((raggiunta, origine), (11, ger.SESSION_SOURCE_DECLARED))
        livelli = {e["entry_id"]: ger.entry_level(e, raggiunta) for e in self.entries}
        # nessuna voce e' piu' recente: le ultime due sessioni sono la 10 e la 11
        self.assertEqual(set(livelli.values()), {ger.LEVEL_ARCHIVE})
        traccia = ger.retrieve("versione corretta", self.entries, 200, current_session=11)
        self.assertEqual(traccia["session_reached"], 11)
        self.assertEqual(traccia["recency_window"], [10, 11])
        self.assertEqual(traccia["level_sizes"][ger.LEVEL_RECENT], 0)
        # senza dichiarazione la finestra resterebbe ferma alla 9
        ripiego = ger.retrieve("versione corretta", self.entries, 200)
        self.assertEqual(ripiego["recency_window"], [8, 9])
        self.assertEqual(ripiego["session_reached_source"], ger.SESSION_SOURCE_FALLBACK)

    def test_stato_intermedio_non_usa_le_sessioni_future(self):
        """Valutando lo stato dopo la sessione 3, la finestra e' 2-3, non 8-9."""
        intermedio = [e for e in self.entries if e["session_order"] <= 3]
        # domanda storica (marcatore «superat»), cosi' anche la voce superata
        # rientra fra i candidati e se ne puo' leggere il livello
        traccia = ger.retrieve("quale versione e' stata superata?", intermedio, 200,
                               current_session=3)
        self.assertEqual(traccia["recency_window"], [2, 3])
        livelli = {i["item_id"]: i["level"] for i in traccia["items"]}
        self.assertEqual(livelli["M2"], ger.LEVEL_RECENT)
        self.assertEqual(livelli["M1"], ger.LEVEL_ARCHIVE)
        # dichiarare una sessione precedente alle voci salvate e' un errore
        with self.assertRaises(ValueError):
            ger.session_reached(self.entries, declared=3)

    def test_ritiro_non_datato_e_dichiarato(self):
        ritirata = next(e for e in self.entries if e["entry_id"] == "M3")
        self.assertIn("ritiro", ger.recency_basis(ritirata))

    def test_recuperare_non_ringiovanisce(self):
        prima = copy.deepcopy(self.entries)
        for _ in range(3):
            traccia = ger.retrieve("decisione lontana ancora valida", self.entries, 200)
            self.assertTrue(traccia["selection"]["selected"])
        self.assertEqual(self.entries, prima)
        dopo = ger.retrieve("decisione lontana ancora valida", self.entries, 200)
        self.assertEqual(dopo["level_sizes"], {ger.LEVEL_RECENT: 2, ger.LEVEL_ARCHIVE: 1})


class TestQuoteERiempimento(unittest.TestCase):
    """R3, R4, R5: quote, riutilizzo, voci troppo grandi."""

    def test_quote_meta_e_meta(self):
        self.assertEqual(ger.quotas(200), {ger.LEVEL_RECENT: 100, ger.LEVEL_ARCHIVE: 100})
        # budget dispari: il token in piu' va all'archivio, non alla memoria recente
        self.assertEqual(ger.quotas(201), {ger.LEVEL_RECENT: 100, ger.LEVEL_ARCHIVE: 101})

    def test_ogni_livello_resta_nella_propria_quota(self):
        ranked = classifica(
            elemento("R1", ger.LEVEL_RECENT, 0.9, 60, 1),
            elemento("R2", ger.LEVEL_RECENT, 0.8, 60, 2),
            elemento("A1", ger.LEVEL_ARCHIVE, 0.7, 60, 3),
            elemento("A2", ger.LEVEL_ARCHIVE, 0.6, 60, 4),
        )
        risultato = ger.select_hierarchical(ranked, 200)
        # In fase 1 ogni livello spende una sola voce: la seconda non entra
        # nella quota di 100 token. Poi i 80 token avanzati tornano disponibili
        # e R2 rientra in fase 2; A2 no, perche' il residuo e' finito.
        self.assertEqual(risultato["levels"][ger.LEVEL_RECENT]["used_tokens"], 60)
        self.assertEqual(risultato["levels"][ger.LEVEL_ARCHIVE]["used_tokens"], 60)
        fase = {d["item_id"]: (d["outcome"], d["phase"]) for d in risultato["decisions"]}
        self.assertEqual(fase["R1"], ("selezionato", 1))
        self.assertEqual(fase["A1"], ("selezionato", 1))
        self.assertEqual(fase["R2"], ("selezionato", 2))
        self.assertEqual(fase["A2"][0], "escluso")
        self.assertEqual([e["item_id"] for e in risultato["selected"]], ["R1", "R2", "A1"])
        self.assertEqual(risultato["context_tokens"], 180)
        self.assertLessEqual(risultato["context_tokens"], 200)

    def test_spazio_inutilizzato_passa_all_altro_livello(self):
        """Nessun candidato recente: l'archivio puo' superare la propria quota."""
        ranked = classifica(
            elemento("A1", ger.LEVEL_ARCHIVE, 0.9, 60, 1),
            elemento("A2", ger.LEVEL_ARCHIVE, 0.8, 60, 2),
            elemento("A3", ger.LEVEL_ARCHIVE, 0.7, 60, 3),
        )
        risultato = ger.select_hierarchical(ranked, 200)
        self.assertEqual([e["item_id"] for e in risultato["selected"]], ["A1", "A2", "A3"])
        self.assertEqual(risultato["reuse"]["used_tokens"], 120)
        self.assertLessEqual(risultato["context_tokens"], 200)

    def test_voce_oltre_la_quota_puo_entrare_con_lo_spazio_residuo(self):
        ranked = classifica(
            elemento("R1", ger.LEVEL_RECENT, 0.9, 30, 1),
            elemento("A1", ger.LEVEL_ARCHIVE, 0.8, 130, 2),
        )
        risultato = ger.select_hierarchical(ranked, 200)
        decisione = next(d for d in risultato["decisions"] if d["item_id"] == "A1")
        self.assertEqual(decisione["outcome"], "selezionato")
        self.assertEqual(decisione["phase"], 2)
        self.assertEqual(risultato["context_tokens"], 160)

    def test_voce_oltre_il_budget_esclusa_non_troncata(self):
        """R5, regole 0.2: nessuna voce puo' far superare il budget."""
        ranked = classifica(elemento("A1", ger.LEVEL_ARCHIVE, 0.9, 240, 1))
        risultato = ger.select_hierarchical(ranked, 200)
        self.assertEqual(risultato["selected"], [])
        self.assertEqual(risultato["context_tokens"], 0)
        self.assertFalse(risultato["budget_exceeded_by_first_item"])
        self.assertEqual(risultato["excluded_over_budget"], ["A1"])
        decisione = next(d for d in risultato["decisions"] if d["item_id"] == "A1")
        self.assertEqual(decisione["outcome"], "escluso")
        self.assertIn(ger.REASON_OVER_BUDGET, decisione["reason"])

    def test_contesto_vuoto_quando_nessuna_voce_entra(self):
        ranked = classifica(
            elemento("R1", ger.LEVEL_RECENT, 0.9, 260, 1),
            elemento("A1", ger.LEVEL_ARCHIVE, 0.8, 300, 2),
        )
        risultato = ger.select_hierarchical(ranked, 200)
        self.assertEqual(risultato["selected"], [])
        self.assertEqual(risultato["context_tokens"], 0)
        self.assertEqual(risultato["content_tokens"], 0)
        self.assertEqual(sorted(risultato["excluded_over_budget"]), ["A1", "R1"])
        for decisione in risultato["decisions"]:
            self.assertEqual(decisione["outcome"], "escluso")

    def test_voce_troppo_grande_chiude_la_fase_come_in_u(self):
        """Comportamento dichiarato delle voci successive: vale la regola di prefisso."""
        ranked = classifica(
            elemento("A1", ger.LEVEL_ARCHIVE, 0.9, 240, 1),
            elemento("A2", ger.LEVEL_ARCHIVE, 0.8, 30, 2),
            elemento("R1", ger.LEVEL_RECENT, 0.7, 30, 3),
        )
        risultato = ger.select_hierarchical(ranked, 200)
        # R1 sta in un altro livello e non e' toccato dall'arresto dell'archivio;
        # A2 resta fuori perche' la classifica dell'archivio si e' fermata su A1.
        self.assertEqual([e["item_id"] for e in risultato["selected"]], ["R1"])
        self.assertLessEqual(risultato["context_tokens"], 200)
        self.assertIn("A1", risultato["excluded_over_budget"])

    def test_il_contesto_sta_sempre_nel_budget(self):
        """Nessuna combinazione di taglie puo' far sforare il budget."""
        for taglia in (10, 45, 99, 100, 101, 199, 200, 201, 500):
            ranked = classifica(
                elemento("R1", ger.LEVEL_RECENT, 0.9, taglia, 1),
                elemento("A1", ger.LEVEL_ARCHIVE, 0.8, taglia, 2),
                elemento("R2", ger.LEVEL_RECENT, 0.7, taglia, 3),
                elemento("A2", ger.LEVEL_ARCHIVE, 0.6, taglia, 4),
            )
            risultato = ger.select_hierarchical(ranked, 200)
            self.assertLessEqual(risultato["context_tokens"], 200, "taglia %d" % taglia)
            self.assertEqual(
                risultato["context_tokens"],
                sum(e["tokens"] for e in risultato["selected"]), "taglia %d" % taglia)

    def test_nessun_doppione(self):
        ranked = classifica(
            elemento("R1", ger.LEVEL_RECENT, 0.9, 30, 1),
            elemento("A1", ger.LEVEL_ARCHIVE, 0.8, 30, 2),
            elemento("A2", ger.LEVEL_ARCHIVE, 0.7, 30, 3),
        )
        risultato = ger.select_hierarchical(ranked, 200)
        scelti = [e["item_id"] for e in risultato["selected"]]
        self.assertEqual(len(scelti), len(set(scelti)))
        self.assertEqual(len(risultato["decisions"]), len(ranked))

    def test_punteggio_nullo_escluso_come_in_u(self):
        ranked = classifica(
            elemento("R1", ger.LEVEL_RECENT, 0.9, 30, 1),
            elemento("A1", ger.LEVEL_ARCHIVE, 0.0, 30, 2),
        )
        risultato = ger.select_hierarchical(ranked, 200)
        self.assertEqual([e["item_id"] for e in risultato["selected"]], ["R1"])
        decisione = next(d for d in risultato["decisions"] if d["item_id"] == "A1")
        self.assertEqual(decisione["reason"], ger.REASON_ZERO_SCORE)

    def test_ogni_candidato_ha_un_motivo(self):
        ranked = classifica(
            elemento("R1", ger.LEVEL_RECENT, 0.9, 120, 1),
            elemento("R2", ger.LEVEL_RECENT, 0.8, 120, 2),
            elemento("A1", ger.LEVEL_ARCHIVE, 0.7, 120, 3),
            elemento("A2", ger.LEVEL_ARCHIVE, 0.1, 120, 4),
        )
        risultato = ger.select_hierarchical(ranked, 200)
        for decisione in risultato["decisions"]:
            self.assertTrue(decisione["reason"])
            self.assertIn(decisione["outcome"], ("selezionato", "escluso"))


class TestContestoDiGer(unittest.TestCase):
    """R2 e R6: stesse voci leggibili di U, etichetta dentro il budget."""

    def setUp(self):
        self.entries = [
            voce("M1", 1, 1, "il rapporto deve restare interno al gruppo di risposta"),
            voce("M2", 9, 2, "resta aperta la revisione delle regole"),
        ]

    def test_stesse_voci_leggibili_di_u(self):
        for scope in (memory.SCOPE_CURRENT, memory.SCOPE_HISTORY):
            self.assertEqual(
                [i["item_id"] for i in ger.ger_items(self.entries, scope)],
                [i["item_id"] for i in memory.state_items(self.entries, scope)],
            )

    def test_etichetta_di_livello_conta_nel_budget(self):
        u_item = memory.state_items(self.entries, memory.SCOPE_CURRENT)[0]
        g_item = ger.ger_items(self.entries, memory.SCOPE_CURRENT)[0]
        self.assertIn(ger.LEVEL_ARCHIVE, g_item["render"])
        self.assertGreater(g_item["tokens"], u_item["tokens"])
        self.assertEqual(g_item["content_tokens"], u_item["content_tokens"])
        self.assertEqual(g_item["tokens"], rq2.count_tokens(g_item["render"]))

    def test_nessun_troncamento(self):
        for item in ger.ger_items(self.entries, memory.SCOPE_CURRENT):
            self.assertIn(item["text"], item["render"])


@unittest.skipUnless(SC03_STATE.exists(), "stato di U non disponibile")
class TestSuStatoReale(unittest.TestCase):
    """GER sullo stato gia' salvato di U per SC03, senza ricostruirlo."""

    @classmethod
    def setUpClass(cls):
        cls.entries = memory.load_state(SC03_STATE)
        cls.questions = rq2.load_questions("scenario_03")
        cls.budget = rq2.budget_tokens()
        # lo stato copre tutte le sessioni della conversazione: la sessione
        # raggiunta e' l'ultima dello scenario, e viene dichiarata a GER.
        assert ger.last_session_order(cls.entries) == SESSIONI_SC03

    def test_stessi_punteggi_di_u(self):
        """Il ranking e' calcolato prima della divisione: nessuna voce cambia punteggio."""
        for question in self.questions:
            scope = memory.question_scope(question["text"])
            u_ranked = rq2.rank_items(question["text"], memory.state_items(self.entries, scope))
            g_ranked = ger.retrieve(question["text"], self.entries, self.budget)["ranked"]
            u_scores = {i["item_id"]: i["score"] for i in u_ranked}
            g_scores = {i["item_id"]: i["score"] for i in g_ranked}
            self.assertEqual(set(u_scores), set(g_scores), question["question_id"])
            for item_id, score in u_scores.items():
                self.assertAlmostEqual(score, g_scores[item_id], places=6)

    def test_budget_e_partizione(self):
        for question in self.questions:
            traccia = ger.retrieve(question["text"], self.entries, self.budget,
                                   current_session=SESSIONI_SC03)
            self.assertEqual(traccia["session_reached_source"], ger.SESSION_SOURCE_DECLARED)
            selezione = traccia["selection"]
            blocco = rq2.context_block(selezione["selected"])
            self.assertEqual(rq2.count_tokens(blocco), selezione["context_tokens"])
            self.assertLessEqual(selezione["context_tokens"], self.budget)
            self.assertEqual(set(traccia["level_sizes"]), set(ger.LEVELS))
            for livello, report in selezione["levels"].items():
                self.assertEqual(report["quota_tokens"], self.budget // 2)
                self.assertLessEqual(report["used_tokens"], self.budget)

    def test_lo_stato_non_viene_scritto(self):
        prima = copy.deepcopy(self.entries)
        for question in self.questions:
            ger.retrieve(question["text"], self.entries, self.budget)
        self.assertEqual(self.entries, prima)


class TestFixtureSc05(unittest.TestCase):
    """Le fixture di SC05 si dichiarano e producono la memoria con il codice vero."""

    def test_fixture_dichiarate(self):
        with open(SC05_UPDATES, "r", encoding="utf-8") as handle:
            document = json.load(handle)
        self.assertTrue(document["fixture"])
        for row in rq2.read_jsonl(SC05_FACTS):
            self.assertTrue(row["fixture"])

    def test_stato_costruito_senza_rifiuti_ed_esercita_l_archivio(self):
        scenario = rq2.load_scenario(rq2.GER_SCENARIO_ID)
        facts = rq2.read_jsonl(SC05_FACTS)
        runner = fixture_replay.make_runner(SC05_UPDATES)
        operations, entries, log = memory.run(scenario, facts, rq2.load_config(), runner=runner)
        self.assertEqual(log["rejected_count"], 0)
        ultima = ger.last_session_order(entries)
        livelli = [ger.entry_level(e, ultima) for e in entries]
        self.assertIn(ger.LEVEL_RECENT, livelli)
        self.assertIn(ger.LEVEL_ARCHIVE, livelli)
        # una decisione lontana ancora valida e una voce superata dentro la
        # finestra recente: i due assi restano indipendenti
        self.assertTrue(any(ger.entry_level(e, ultima) == ger.LEVEL_ARCHIVE
                            and e["status"] == rq2.STATE_ACTIVE for e in entries))
        self.assertTrue(any(e["status"] == rq2.STATE_RETRACTED for e in entries))

    def test_la_storia_supera_il_budget(self):
        scenario = rq2.load_scenario(rq2.GER_SCENARIO_ID)
        storia = sum(item["tokens"] for item in rq2.message_items(scenario))
        self.assertGreater(storia, 3 * rq2.budget_tokens())

    def test_le_domande_coprono_i_casi_previsti(self):
        questions = rq2.load_questions(rq2.GER_SCENARIO_ID)
        categorie = {q["category"] for q in questions}
        for attesa in ("goal", "update_obsolete", "pending_activity", "completed_activity",
                       "cross_session_link", "local_information", "absent_information"):
            self.assertIn(attesa, categorie)
        astensioni = [q for q in questions if q["expected_behavior"] == rq2.BEHAVIOR_ABSTAIN]
        self.assertEqual(len(astensioni), 1)


class TestPreparazioneProvaSc05(unittest.TestCase):
    """Che i comandi della prova reale reggano SC05 e GER, e la configurazione dica il vero."""

    def test_i_costruttori_accettano_scenario_05(self):
        """Senza questo, i due comandi si fermano sul controllo degli argomenti."""
        import extract_facts
        for modulo in (extract_facts, memory):
            args = modulo.parse_args(["--scenario", rq2.GER_SCENARIO_ID, "--dry-run"])
            self.assertEqual(args.scenario, rq2.GER_SCENARIO_ID)
            # gli scenari precedenti restano accettati e i default non cambiano
            self.assertEqual(modulo.parse_args([]).scenario,
                             "scenario_02" if modulo is extract_facts else "scenario_03")

    def test_scheda_di_valutazione_legge_la_memoria_di_ger_come_quella_di_u(self):
        """GER parte dallo stesso stato di U: la sua memoria non sono i messaggi."""
        import build_annotation_template_rq2 as scheda
        scenario = rq2.load_scenario(rq2.GER_SCENARIO_ID)
        runner = fixture_replay.make_runner(SC05_UPDATES)
        _, entries, _ = memory.run(scenario, rq2.read_jsonl(SC05_FACTS), rq2.load_config(),
                                   runner=runner)
        parziali = [e for e in entries if e["session_order"] <= 3]
        attesi = {m for e in parziali for m in e["source_message_ids"]}
        tutti = {m["message_id"] for m in rq2.user_messages(scenario)}
        self.assertLess(len(attesi), len(tutti))

        with tempfile.TemporaryDirectory() as cartella:
            percorso = Path(cartella) / "stato_parziale.json"
            rq2.write_json(memory.state_document(rq2.GER_SCENARIO_ID, parziali,
                                                 rq2.load_config(), "prova"), percorso)
            sorgenti = {"state": str(percorso)}
            self.assertEqual(scheda.memory_provenance("GER", rq2.GER_SCENARIO_ID, sorgenti), attesi)
            self.assertEqual(scheda.memory_provenance("U", rq2.GER_SCENARIO_ID, sorgenti), attesi)
            # senza stato si ripiega sui messaggi, come per T e FULL_HISTORY
            self.assertEqual(scheda.memory_provenance("GER", rq2.GER_SCENARIO_ID, {}), tutti)

    def test_la_configurazione_della_prova_dice_il_vero(self):
        """L'artefatto di configurazione non deve allontanarsi dal codice."""
        with open(RUN_CONFIG, "r", encoding="utf-8") as handle:
            run = json.load(handle)
        config = rq2.load_config()
        budget = rq2.budget_tokens(config)
        scenario = rq2.load_scenario(rq2.GER_SCENARIO_ID)
        sessioni = len(scenario["sessions"])
        domande = rq2.load_questions(rq2.GER_SCENARIO_ID)

        self.assertFalse(run["frozen"])
        self.assertEqual(run["base"]["config_id"], config["config_id"])
        self.assertEqual(run["ger"]["rules_version"], ger.RULES_VERSION)
        self.assertEqual(run["ger"]["finestra_di_recenza_sessioni"], ger.RECENCY_WINDOW_SESSIONS)
        self.assertEqual(run["ger"]["quote_token"], ger.quotas(budget))
        self.assertEqual(run["ger"]["sessione_raggiunta"], sessioni)
        self.assertEqual(run["retrieval"]["budget_tokens"], budget)
        self.assertEqual(run["retrieval"]["metodo"], config["retrieval"]["method"])
        self.assertEqual(run["modelli"]["risposte"]["model"], config["models"]["answer"]["model"])
        self.assertEqual(run["modelli"]["risposte"]["effort"], config["models"]["answer"]["effort"])
        self.assertEqual(run["versioni_del_codice"]["u_instructions_version"],
                         memory.INSTRUCTIONS_VERSION)
        self.assertEqual(
            run["versioni_del_codice"]["u_instructions_sha256"],
            hashlib.sha256((memory.UPDATE_INSTRUCTIONS + memory.REPAIR_INSTRUCTIONS)
                           .encode("utf-8")).hexdigest()[:16])
        self.assertEqual(run["versioni_del_codice"]["repair_attempts"],
                         memory.DEFAULT_REPAIR_ATTEMPTS)
        chiamate = run["chiamate_al_modello_previste"]
        self.assertEqual(chiamate["estrazione_dei_fatti"], sessioni)
        self.assertEqual(chiamate["costruzione_di_U"], sessioni)
        self.assertEqual(chiamate["risposte"], len(domande) * len(run["modalita"]["confrontate_a_parita_di_budget"]
                                                                 + run["modalita"]["controllo_diagnostico"]))
        self.assertEqual(chiamate["totale_minimo"], sessioni * 2 + len(domande) * 3)
        # a prova eseguita, i conteggi dichiarati devono corrispondere agli artefatti
        cartella = REPO_ROOT / run["uscite"]["cartella"]
        if not run["executed"]:
            self.assertFalse((cartella / "generation_dev_sc05.jsonl").exists())
            return
        eseguite = run["esecuzione"]["chiamate_effettive"]
        risposte = rq2.read_jsonl(cartella / "generation_dev_sc05.jsonl")
        self.assertEqual(len(risposte), eseguite["risposte"])
        self.assertEqual({r["model_used"] for r in risposte},
                         {config["models"]["answer"]["model"]})
        self.assertEqual([r for r in risposte if r["error"]], [])
        log = json.loads((cartella / "memory" / "scenario_05_update_log.json").read_text(encoding="utf-8"))
        self.assertEqual(log["model_calls"], eseguite["costruzione_di_U"] + eseguite["riparazioni"])
        self.assertEqual(log["rejected_count"], 0)
        self.assertEqual(log["instructions_version"], memory.INSTRUCTIONS_VERSION)
        self.assertEqual(eseguite["totale_esperimento"],
                         eseguite["estrazione_dei_fatti"] + eseguite["costruzione_di_U"]
                         + eseguite["riparazioni"] + eseguite["risposte"])


class TestNessunaRegressione(unittest.TestCase):
    """I confronti gia' eseguiti devono restare identici."""

    def test_sc05_fuori_dalla_matrice(self):
        config = rq2.load_config()
        self.assertNotIn(rq2.GER_SCENARIO_ID, config["matrix"])
        self.assertEqual(len(rq2.SCENARIO_IDS), 4)
        self.assertNotIn(rq2.GER_SCENARIO_ID, rq2.SCENARIO_IDS)
        for scenario_id in rq2.SCENARIO_IDS:
            self.assertNotIn("GER", rq2.planned_modes(scenario_id, config))
            self.assertNotIn("GER", rq2.runnable_modes(scenario_id, config))

    def test_eccezione_di_u_non_attiva_nei_casi_di_confronto(self):
        """U conserva la propria garanzia minima; GER no.

        L'eccezione di U resta dov'era per non cambiare i risultati gia'
        prodotti. Qui si verifica che sui casi usati per confrontare U e GER non
        si attivi mai: nessuna voce di memoria arriva, da sola, a 200 token.
        """
        budget = rq2.budget_tokens()
        stati = {}
        scenario = rq2.load_scenario(rq2.GER_SCENARIO_ID)
        runner = fixture_replay.make_runner(SC05_UPDATES)
        _, entries, _ = memory.run(scenario, rq2.read_jsonl(SC05_FACTS), rq2.load_config(),
                                   runner=runner)
        stati[rq2.GER_SCENARIO_ID] = entries
        for scenario_id, path in (("scenario_03", SC03_STATE), ("scenario_04", SC04_STATE)):
            if path.exists():
                stati[scenario_id] = memory.load_state(path)

        for scenario_id, entries in stati.items():
            for question in rq2.load_questions(scenario_id):
                scope = memory.question_scope(question["text"])
                ranked = rq2.rank_items(question["text"], memory.state_items(entries, scope))
                selezione = rq2.select_within_budget(ranked, budget)
                self.assertFalse(selezione["budget_exceeded_by_first_item"],
                                 "%s %s" % (scenario_id, question["question_id"]))
                self.assertLessEqual(selezione["context_tokens"], budget)
                # e GER, sugli stessi candidati, non supera mai il budget
                traccia = ger.retrieve(question["text"], entries, budget,
                                       current_session=ger.last_session_order(entries))
                self.assertLessEqual(traccia["selection"]["context_tokens"], budget)

    def test_u_non_cambia(self):
        """La regola di selezione di U resta un prefisso del ranking."""
        ranked = [elemento("I1", ger.LEVEL_RECENT, 0.9, 60, 1),
                  elemento("I2", ger.LEVEL_ARCHIVE, 0.8, 60, 2),
                  elemento("I3", ger.LEVEL_ARCHIVE, 0.7, 120, 3)]
        risultato = rq2.select_within_budget(ranked, 200)
        self.assertEqual([e["item_id"] for e in risultato["selected"]], ["I1", "I2"])
        self.assertEqual(risultato["stopped_by"]["item_id"], "I3")

    @unittest.skipUnless(SC03_RETRIEVAL.exists() and SC03_STATE.exists() and SC03_FACTS.exists(),
                         "artefatti di SC03 non disponibili")
    def test_retrieval_di_u_identico_alla_prova_salvata(self):
        config = rq2.load_config()
        paths = {"scenario_03": {"facts": str(SC03_FACTS), "state": str(SC03_STATE)}}
        rows, _ = retrieval_rq2.run(["scenario_03"], config, paths, "controllo", modes=["U"])
        salvate = {r["question_id"]: r for r in rq2.read_jsonl(SC03_RETRIEVAL) if r["mode"] == "U"}
        self.assertEqual(len(rows), len(salvate))
        for row in rows:
            atteso = salvate[row["question_id"]]
            self.assertEqual(row["selected_item_ids"], atteso["selected_item_ids"])
            self.assertEqual(row["context_tokens"], atteso["context_tokens"])
            self.assertEqual(row["reading_scope"], atteso["reading_scope"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
