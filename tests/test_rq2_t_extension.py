#!/usr/bin/env python3
"""Verifiche dell'estensione della matrice con Turn-level RAG (T).

L'estensione aggiunge T come baseline anche a SC04 e SC05:

    SC01  T                SC04  T / U / G
    SC02  T / F            SC05  T / U / GER
    SC03  F / U

con FULL_HISTORY come controllo diagnostico di ogni scenario, fuori dal budget.

Si controllano le proprieta' che, se saltassero, renderebbero il confronto privo
di senso o rovinerebbero quello gia' fatto:

  - la matrice estesa aggiunge e non sostituisce: la matrice della roadmap, le
    77 celle e i confronti T/F, F/U e U/G restano identici;
  - T pesca dagli stessi messaggi sorgente temporalmente accessibili delle altre
    modalita' dello scenario, e da nessun altro;
  - T non dipende da fatti, stato di U o grafo: e' per questo che le risposte
    gia' generate per U, G, GER e FULL_HISTORY restano riusabili;
  - budget, conteggio dei token, regola di selezione e prompt comune sono quelli
    gia' in uso, non una configurazione nuova.
"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rq2"))

import rq2_common as rq2  # noqa: E402
import validate_rq2 as validator  # noqa: E402
import run_retrieval_rq2 as retrieval_rq2  # noqa: E402
import build_generation_inputs_rq2 as generation_inputs  # noqa: E402
import run_t_extension_check as t_ext  # noqa: E402

RUN_CONFIG = REPO_ROOT / "data" / "rq2" / "config" / "run_t_ext_sc04_sc05.json"

MATRICE_ATTESA = {
    "scenario_01": ["T"],
    "scenario_02": ["T", "F"],
    "scenario_03": ["F", "U"],
    "scenario_04": ["T", "U", "G"],
    "scenario_05": ["T", "U", "GER"],
}


def _codici(errors):
    return [e.split("]")[0].strip("[") for e in errors]


class TestMatriceEstesa(unittest.TestCase):
    def setUp(self):
        self.config = rq2.load_config()

    def test_righe_come_richiesto(self):
        for scenario_id, atteso in MATRICE_ATTESA.items():
            self.assertEqual(rq2.extension_budgeted_modes(scenario_id, self.config), atteso, scenario_id)

    def test_full_history_e_il_controllo_diagnostico_di_ogni_scenario(self):
        for scenario_id in rq2.EXTENSION_SCENARIO_IDS:
            self.assertEqual(rq2.extension_diagnostic_modes(scenario_id, self.config),
                             [rq2.FULL_HISTORY], scenario_id)
            self.assertNotIn(rq2.FULL_HISTORY,
                             rq2.extension_budgeted_modes(scenario_id, self.config), scenario_id)

    def test_aggiunge_solo_t_e_solo_dove_serve(self):
        self.assertEqual(rq2.extension_added_modes("scenario_04", self.config), ["T"])
        for scenario_id in ("scenario_01", "scenario_02", "scenario_03"):
            self.assertEqual(rq2.extension_added_modes(scenario_id, self.config), [], scenario_id)
        # SC05 non era nella roadmap: l'intera riga e' nuova.
        self.assertEqual(rq2.extension_added_modes(rq2.GER_SCENARIO_ID, self.config),
                         ["T", "U", "GER"])

    def test_la_matrice_originale_non_cambia(self):
        for scenario_id, modes in validator.ROADMAP_MATRIX.items():
            self.assertEqual(rq2.planned_modes(scenario_id, self.config), modes, scenario_id)
        self.assertEqual(self.config["expected_generations_when_complete"]["total"],
                         validator.ROADMAP_TOTAL_GENERATIONS)
        self.assertNotIn(rq2.GER_SCENARIO_ID, self.config["matrix"])
        for scenario_id in rq2.SCENARIO_IDS:
            self.assertNotIn("GER", rq2.planned_modes(scenario_id, self.config), scenario_id)

    def test_la_riga_estesa_contiene_quella_della_roadmap(self):
        for scenario_id in rq2.SCENARIO_IDS:
            roadmap = [m for m in rq2.planned_modes(scenario_id, self.config) if m != rq2.FULL_HISTORY]
            estesa = rq2.extension_budgeted_modes(scenario_id, self.config)
            self.assertTrue(set(roadmap) <= set(estesa), scenario_id)

    def test_celle_nuove_e_chiamate_dichiarate(self):
        aggiunte = self.config["matrix_extension"]["added_cells"]
        self.assertEqual(aggiunte["total_answer_calls"], 14)
        self.assertEqual(aggiunte["total_memory_calls"], 0)
        for scenario_id in ("scenario_04", rq2.GER_SCENARIO_ID):
            self.assertEqual(aggiunte[scenario_id]["modes"], ["T"])
            self.assertEqual(aggiunte[scenario_id]["answer_calls"], 7)
            self.assertEqual(aggiunte[scenario_id]["memory_calls"], 0)

    def test_ogni_modalita_della_matrice_estesa_e_implementata(self):
        for scenario_id in rq2.EXTENSION_SCENARIO_IDS:
            for mode in rq2.extension_modes(scenario_id, self.config):
                self.assertTrue(self.config["modes"][mode]["implemented"], "%s %s" % (scenario_id, mode))


class TestValidatoreDellEstensione(unittest.TestCase):
    def setUp(self):
        self.config = rq2.load_config()

    def _run(self, config):
        errors = []
        validator.validate_matrix_extension(config, errors)
        return errors

    def test_configurazione_vera_ok(self):
        self.assertEqual(self._run(self.config), [])

    def test_riga_che_perde_una_modalita_della_roadmap(self):
        config = copy.deepcopy(self.config)
        config["matrix_extension"]["rows"]["scenario_04"]["budgeted"] = ["T", "U"]
        self.assertIn("E-EXT", _codici(self._run(config)))

    def test_riga_che_aggiunge_qualcosa_di_diverso_da_t(self):
        config = copy.deepcopy(self.config)
        config["matrix_extension"]["rows"]["scenario_03"]["budgeted"] = ["F", "U", "G"]
        self.assertIn("E-EXT", _codici(self._run(config)))

    def test_full_history_fra_le_modalita_a_budget(self):
        config = copy.deepcopy(self.config)
        config["matrix_extension"]["rows"]["scenario_02"]["budgeted"] = ["T", "F", rq2.FULL_HISTORY]
        self.assertIn("E-EXT", _codici(self._run(config)))

    def test_controllo_diagnostico_mancante(self):
        config = copy.deepcopy(self.config)
        config["matrix_extension"]["rows"]["scenario_05"]["diagnostic"] = []
        self.assertIn("E-EXT", _codici(self._run(config)))

    def test_conteggio_delle_chiamate_incoerente(self):
        config = copy.deepcopy(self.config)
        config["matrix_extension"]["added_cells"]["total_answer_calls"] = 21
        self.assertIn("E-EXT", _codici(self._run(config)))

    def test_t_dichiarato_con_chiamate_di_memoria(self):
        config = copy.deepcopy(self.config)
        config["matrix_extension"]["added_cells"]["scenario_04"]["memory_calls"] = 4
        self.assertIn("E-EXT", _codici(self._run(config)))

    def test_estensione_che_tocca_la_matrice_originale(self):
        config = copy.deepcopy(self.config)
        config["matrix"]["scenario_04"]["planned"] = ["T", "U", "G", rq2.FULL_HISTORY]
        self.assertIn("E-EXT", _codici(self._run(config)))

    def test_validazione_completa_senza_errori(self):
        self.assertEqual(validator.validate_all(config=self.config), [])


class TestPerimetroDiT(unittest.TestCase):
    """T deve pescare dagli stessi messaggi delle altre modalita' dello scenario."""

    def test_t_indicizza_tutti_e_soli_i_messaggi_utente(self):
        for scenario_id in ("scenario_04", rq2.GER_SCENARIO_ID):
            scenario = rq2.load_scenario(scenario_id)
            attesi = [entry["message_id"] for entry in rq2.user_messages(scenario)]
            items = rq2.message_items(scenario)
            self.assertEqual([item["item_id"] for item in items], attesi, scenario_id)
            index = rq2.message_index(scenario)
            for item in items:
                self.assertEqual(index[item["item_id"]]["role"], rq2.INDEXED_ROLE)

    def test_il_controllo_del_perimetro_non_segnala_errori(self):
        for scenario_id in t_ext.NEW_SCENARIOS:
            errors = []
            t_ext.check_perimeter(scenario_id, errors)
            self.assertEqual(errors, [], scenario_id)

    def test_stato_intermedio_segnalato(self):
        """Se lo stato di U si fermasse prima, T vedrebbe messaggi mai visti."""
        errors = []
        t_ext.check_perimeter("scenario_04", errors)
        self.assertEqual(errors, [])
        scenario = rq2.load_scenario("scenario_04")
        self.assertEqual(len(scenario["sessions"]), 4)


class TestRetrievalDiT(unittest.TestCase):
    def setUp(self):
        self.config = rq2.load_config()
        self.budget = rq2.budget_tokens(self.config)
        self.rows, self.skipped = retrieval_rq2.run(
            list(t_ext.NEW_SCENARIOS), self.config, {}, "prova", modes=["T"])

    def test_sette_prove_per_scenario_senza_salti(self):
        self.assertEqual(self.skipped, [])
        for scenario_id in t_ext.NEW_SCENARIOS:
            righe = [r for r in self.rows if r["scenario_id"] == scenario_id]
            self.assertEqual(len(righe), 7, scenario_id)
            self.assertEqual({r["mode"] for r in righe}, {"T"})

    def test_budget_rispettato_e_unita_dichiarata(self):
        for row in self.rows:
            self.assertEqual(row["budget_tokens"], self.budget)
            self.assertEqual(row["memory_unit"], "messaggio")
            if not row["budget_exceeded_by_first_item"]:
                self.assertLessEqual(row["context_tokens"], self.budget,
                                     "%s %s" % (row["scenario_id"], row["question_id"]))

    def test_contesto_fatto_solo_di_messaggi_dello_scenario(self):
        for scenario_id in t_ext.NEW_SCENARIOS:
            ammessi = {e["message_id"] for e in rq2.user_messages(rq2.load_scenario(scenario_id))}
            for row in [r for r in self.rows if r["scenario_id"] == scenario_id]:
                self.assertTrue(set(row["selected_item_ids"]) <= ammessi)
                self.assertTrue(set(row["context_provenance_message_ids"]) <= ammessi)

    def test_t_non_dipende_da_fatti_stato_o_grafo(self):
        """La stessa T con percorsi di memoria diversi da' righe identiche.

        E' la ragione per cui le risposte gia' generate per U, G, GER e
        FULL_HISTORY restano riusabili accanto a T senza rieseguirle.
        """
        altri_percorsi = {
            "scenario_04": {"facts": "/percorso/inesistente.jsonl",
                            "state": "/percorso/inesistente.json",
                            "graph": "/percorso/inesistente.json"},
            rq2.GER_SCENARIO_ID: {"state": "/percorso/inesistente.json", "session_reached": 3},
        }
        altre, skipped = retrieval_rq2.run(list(t_ext.NEW_SCENARIOS), self.config,
                                           altri_percorsi, "prova", modes=["T"])
        self.assertEqual(skipped, [])
        for prima, dopo in zip(self.rows, altre):
            self.assertEqual(prima["selected_item_ids"], dopo["selected_item_ids"])
            self.assertEqual(prima["context_tokens"], dopo["context_tokens"])
            self.assertEqual([i["render"] for i in prima["selected"]],
                             [i["render"] for i in dopo["selected"]])

    def test_ranking_identico_a_quello_gia_usato_da_t_su_sc02(self):
        """Stesso codice, stesso metodo: T non e' stato riscritto per l'estensione."""
        salvate = rq2.read_jsonl(rq2.RQ2_RESULTS_DIR / "retrieval_sc02.jsonl")
        salvate = [r for r in salvate if r["mode"] == "T"]
        rifatte, _ = retrieval_rq2.run(["scenario_02"], self.config, {}, "esecuzione", modes=["T"])
        for prima, dopo in zip(salvate, rifatte):
            self.assertEqual(prima["question_id"], dopo["question_id"])
            self.assertEqual(prima["selected_item_ids"], dopo["selected_item_ids"])
            self.assertEqual(prima["context_tokens"], dopo["context_tokens"])


class TestPromptDiT(unittest.TestCase):
    def setUp(self):
        self.config = rq2.load_config()
        self.rows, _ = retrieval_rq2.run(list(t_ext.NEW_SCENARIOS), self.config, {}, "prova",
                                         modes=["T"])
        self.inputs, _ = generation_inputs.build(list(t_ext.NEW_SCENARIOS), self.config, self.rows,
                                                 modes_override=["T"])

    def test_controlli_dello_script_superati(self):
        for scenario_id in t_ext.NEW_SCENARIOS:
            righe = [r for r in self.inputs if r["scenario_id"] == scenario_id]
            self.assertEqual(generation_inputs.check(righe, [scenario_id], self.config, self.rows),
                             [], scenario_id)

    def test_istruzioni_identiche_a_quelle_gia_usate(self):
        atteso = t_ext.sha(generation_inputs.INSTRUCTIONS)
        for row in self.inputs:
            self.assertEqual(t_ext.sha(t_ext.instructions_block(row["prompt"])), atteso)
        for path in (rq2.RQ2_RESULTS_DIR / "sc04_repair_v3" / "generation_inputs_sc04_ug.jsonl",
                     rq2.RQ2_RESULTS_DIR / "sc05_dev_v1" / "generation_inputs_sc05.jsonl"):
            for row in rq2.read_jsonl(path):
                self.assertEqual(t_ext.sha(t_ext.instructions_block(row["prompt"])), atteso,
                                 rq2.relative(path))

    def test_una_sola_domanda_e_nessun_oracle(self):
        for scenario_id in t_ext.NEW_SCENARIOS:
            questions = {q["question_id"]: q for q in rq2.load_questions(scenario_id)}
            for row in [r for r in self.inputs if r["scenario_id"] == scenario_id]:
                question = questions[row["question_id"]]
                self.assertTrue(row["prompt"].endswith(question["text"]))
                self.assertEqual(row["prompt"].count("Domanda:"), 1)
                self.assertNotIn(question["expected_answer"], row["prompt"])
                self.assertIsNone(row["model_answer"])

    def test_il_contesto_e_quello_contato_dal_retrieval(self):
        salvato = {(r["scenario_id"], r["question_id"], r["mode"]): r for r in self.rows}
        for row in self.inputs:
            source = salvato[(row["scenario_id"], row["question_id"], row["mode"])]
            self.assertEqual(row["context_item_ids"], source["selected_item_ids"])
            self.assertEqual(row["context_tokens"], source["context_tokens"])
            self.assertTrue(row["budget_applies"])


class TestCompatibilitaDelleProveEsistenti(unittest.TestCase):
    """Che cosa si puo' leggere accanto a T senza mescolare configurazioni."""

    def setUp(self):
        self.config = rq2.load_config()
        self.rows, _ = retrieval_rq2.run(list(t_ext.NEW_SCENARIOS), self.config, {}, "prova",
                                         modes=["T"])

    def test_prove_di_riferimento_compatibili(self):
        for scenario_id in t_ext.NEW_SCENARIOS:
            riferimento = t_ext.REFERENCE_RUNS[scenario_id]
            righe_t = [r for r in self.rows if r["scenario_id"] == scenario_id]
            errors, warnings = [], []
            report = t_ext.compare_run(scenario_id, righe_t, riferimento["answers"],
                                       riferimento["modes"], riferimento["run_label"],
                                       self.config, errors, warnings)
            self.assertIsNotNone(report, scenario_id)
            self.assertTrue(report["compatible"], report["problems"])
            self.assertEqual(errors, [])

    def test_le_risposte_riusate_sono_del_modello_dichiarato(self):
        atteso = self.config["models"]["answer"]
        for scenario_id in t_ext.NEW_SCENARIOS:
            righe = rq2.read_jsonl(t_ext.REFERENCE_RUNS[scenario_id]["answers"])
            for row in righe:
                self.assertIsNone(row["error"])
                self.assertEqual(row["model_used"], atteso["model"])
                self.assertEqual(row["effort"], atteso["effort"])

    def test_sc04_full_history_viene_da_unaltra_esecuzione(self):
        """Va detto, non nascosto: e' un limite dichiarato della tabella di SC04."""
        riferimento = t_ext.REFERENCE_RUNS["scenario_04"]
        principale = {r["mode"] for r in rq2.read_jsonl(riferimento["answers"])}
        self.assertNotIn(rq2.FULL_HISTORY, principale)
        diagnostico = riferimento["diagnostic_from_other_run"]
        modi = {r["mode"] for r in rq2.read_jsonl(diagnostico["answers"])}
        self.assertIn(rq2.FULL_HISTORY, modi)

    def test_le_prove_gia_eseguite_non_cambiano(self):
        """Nessuna cella gia' prodotta viene rifatta dall'estensione."""
        attese = {
            rq2.RQ2_RESULTS_DIR / "sc04_repair_v3" / "generation_dev_sc04_ug.jsonl": {"U": 7, "G": 7},
            rq2.RQ2_RESULTS_DIR / "sc05_dev_v1" / "generation_dev_sc05.jsonl":
                {"U": 7, "GER": 7, rq2.FULL_HISTORY: 7},
        }
        for path, atteso in attese.items():
            conteggio = {}
            for row in rq2.read_jsonl(path):
                conteggio[row["mode"]] = conteggio.get(row["mode"], 0) + 1
            self.assertEqual(conteggio, atteso, rq2.relative(path))


class TestConfigurazioneDellaProva(unittest.TestCase):
    """`run_t_ext_sc04_sc05.json` deve dire il vero sulla prova che descrive."""

    def setUp(self):
        self.config = rq2.load_config()
        self.run = json.loads(RUN_CONFIG.read_text(encoding="utf-8"))

    def test_eredita_la_configurazione_di_sviluppo(self):
        self.assertEqual(self.run["base"]["config_id"], self.config["config_id"])
        self.assertEqual(self.run["base"]["estensione"].split(" ")[0],
                         self.config["matrix_extension"]["extension_id"])
        self.assertEqual(self.run["retrieval"]["budget_tokens"], rq2.budget_tokens(self.config))
        atteso = self.config["models"]["answer"]
        self.assertEqual(self.run["modelli"]["risposte"],
                         {"model": atteso["model"], "effort": atteso["effort"]})
        self.assertEqual(self.run["retrieval"]["metodo"], self.config["retrieval"]["method"])

    def test_chiamate_dichiarate_coerenti_con_la_matrice(self):
        chiamate = self.run["chiamate_al_modello_previste"]
        self.assertEqual(chiamate["costruzione_della_memoria"], 0)
        self.assertEqual(chiamate["riesecuzioni_previste"], 0)
        self.assertEqual(chiamate["risposte_scenario_04"] + chiamate["risposte_scenario_05"],
                         chiamate["totale"])
        self.assertEqual(chiamate["totale"],
                         self.config["matrix_extension"]["added_cells"]["total_answer_calls"])

    def test_matrice_della_prova_uguale_a_quella_dichiarata(self):
        for scenario_id, chiave in (("scenario_04", "scenario_04"),
                                    (rq2.GER_SCENARIO_ID, "scenario_05")):
            riga = self.run["matrice_di_questa_prova"][chiave]
            self.assertEqual(riga["a_parita_di_budget"],
                             rq2.extension_budgeted_modes(scenario_id, self.config))
            self.assertEqual(riga["controllo_diagnostico"],
                             rq2.extension_diagnostic_modes(scenario_id, self.config))
            self.assertEqual(riga["nuovo_qui"], ["T"])

    def test_perimetro_dichiarato_uguale_a_quello_reale(self):
        for scenario_id, chiave in (("scenario_04", "scenario_04"),
                                    (rq2.GER_SCENARIO_ID, "scenario_05")):
            scenario = rq2.load_scenario(scenario_id)
            atteso = self.run["perimetro"][chiave]
            self.assertEqual(atteso["sessioni"], len(scenario["sessions"]))
            self.assertEqual(atteso["messaggi_utente"], len(rq2.user_messages(scenario)))

    def test_uscite_in_una_cartella_propria(self):
        uscite = self.run["uscite"]
        self.assertEqual(uscite["cartella"], "results/rq2/t_ext_v1")
        for chiave in ("retrieval", "prompt", "risposte", "scheda_di_valutazione"):
            self.assertIn(uscite["cartella"], uscite[chiave])

    def test_eseguita_ma_non_congelata(self):
        self.assertTrue(self.run["executed"])
        self.assertFalse(self.run["frozen"])
        self.assertNotIn("relatore", self.run["autorizzazione"].split("Non è")[0])

    def test_chiamate_effettive_uguali_a_quelle_previste(self):
        eseguite = self.run["esecuzione"]["chiamate_effettive"]
        previste = self.run["chiamate_al_modello_previste"]
        self.assertEqual(eseguite["totale"], previste["totale"])
        self.assertEqual(eseguite["costruzione_della_memoria"], 0)
        self.assertEqual(eseguite["riesecuzioni"], 0)
        self.assertEqual(eseguite["risposte_scenario_04"] + eseguite["risposte_scenario_05"],
                         eseguite["totale"])
        self.assertEqual(self.run["esecuzione"]["errori"],
                         {"esecuzione": 0, "parsing": 0, "risposte_vuote": 0})


class TestProvaReale(unittest.TestCase):
    """Gli artefatti prodotti dalle 14 chiamate devono dire il vero."""

    OUT = REPO_ROOT / "results" / "rq2" / "t_ext_v1"
    SCENARI = (("scenario_04", "sc04"), ("scenario_05", "sc05"))

    def setUp(self):
        self.config = rq2.load_config()

    def test_quattordici_risposte_senza_errori(self):
        totale = 0
        atteso = self.config["models"]["answer"]
        for scenario_id, short in self.SCENARI:
            righe = rq2.read_jsonl(self.OUT / ("generation_dev_t_%s.jsonl" % short))
            self.assertEqual(len(righe), 7, scenario_id)
            for row in righe:
                self.assertEqual(row["mode"], "T")
                self.assertIsNone(row["error"])
                self.assertTrue(row["model_answer"])
                self.assertEqual(row["model_requested"], atteso["model"])
                self.assertEqual(row["model_used"], atteso["model"])
                self.assertEqual(row["effort"], atteso["effort"])
            totale += len(righe)
        self.assertEqual(totale, self.config["matrix_extension"]["added_cells"]["total_answer_calls"])

    def test_una_risposta_per_domanda_dello_scenario(self):
        for scenario_id, short in self.SCENARI:
            attese = {q["question_id"] for q in rq2.load_questions(scenario_id)}
            righe = rq2.read_jsonl(self.OUT / ("generation_dev_t_%s.jsonl" % short))
            self.assertEqual({r["question_id"] for r in righe}, attese, scenario_id)

    def test_il_retrieval_salvato_rispetta_il_budget(self):
        budget = rq2.budget_tokens(self.config)
        for _, short in self.SCENARI:
            for row in rq2.read_jsonl(self.OUT / ("retrieval_t_%s.jsonl" % short)):
                self.assertEqual(row["budget_tokens"], budget)
                self.assertFalse(row["budget_exceeded_by_first_item"])
                self.assertLessEqual(row["context_tokens"], budget)

    def test_i_prompt_inviati_superano_i_controlli(self):
        for scenario_id, short in self.SCENARI:
            rows = rq2.read_jsonl(self.OUT / ("retrieval_t_%s.jsonl" % short))
            inputs = rq2.read_jsonl(self.OUT / ("generation_inputs_t_%s.jsonl" % short))
            self.assertEqual(generation_inputs.check(inputs, [scenario_id], self.config, rows),
                             [], scenario_id)

    def test_template_di_annotazione_intatto(self):
        """Il template resta con i giudizi null: i giudizi vivono nella copia."""
        for _, short in self.SCENARI:
            for row in rq2.read_jsonl(self.OUT / ("annotation_template_t_%s.jsonl" % short)):
                for campo in ("answer_class", "obsolete_used", "unsupported_claim",
                              "wrong_abstention", "error_origin"):
                    self.assertIsNone(row[campo], "%s %s" % (row["question_id"], campo))

    def test_annotazione_compilata_coerente_con_le_risposte(self):
        for scenario_id, short in self.SCENARI:
            risposte = {r["question_id"]: r["model_answer"]
                        for r in rq2.read_jsonl(self.OUT / ("generation_dev_t_%s.jsonl" % short))}
            righe = rq2.read_jsonl(self.OUT / ("annotation_compilata_t_%s.jsonl" % short))
            self.assertEqual(len(righe), 7, scenario_id)
            for row in righe:
                self.assertEqual(row["model_answer"], risposte[row["question_id"]])
                self.assertIn(row["answer_class"], row["allowed_answer_class"])
                self.assertIn(row["error_origin"], row["allowed_error_origin"])
                for campo in ("obsolete_used", "unsupported_claim", "wrong_abstention"):
                    self.assertIsInstance(row[campo], bool)
                self.assertTrue(row["annotator_note"])
                # i giudizi di T non sono approvati: non vanno letti come tali
                self.assertIn("NON approvato", row["judgment_approval"]["stato"])

    def test_conteggi_dichiarati_uguali_a_quelli_annotati(self):
        atteso = {
            "sc04": {"completa": 4, "parziale": 2, "astensione corretta": 1},
            "sc05": {"completa": 3, "parziale": 1, "errata": 2, "astensione corretta": 1},
        }
        obsolete = {"sc04": 0, "sc05": 2}
        for _, short in self.SCENARI:
            righe = rq2.read_jsonl(self.OUT / ("annotation_compilata_t_%s.jsonl" % short))
            conta = {}
            for row in righe:
                conta[row["answer_class"]] = conta.get(row["answer_class"], 0) + 1
            self.assertEqual(conta, atteso[short], short)
            self.assertEqual(sum(1 for r in righe if r["obsolete_used"]), obsolete[short], short)
            self.assertEqual(sum(1 for r in righe if r["unsupported_claim"]), 0, short)
            self.assertEqual(sum(conta.values()), 7, short)

    def test_le_prove_precedenti_non_sono_state_toccate(self):
        """L'estensione aggiunge celle, non riscrive quelle gia' prodotte."""
        attese = {
            REPO_ROOT / "results/rq2/sc04_repair_v3/generation_dev_sc04_ug.jsonl": {"U": 7, "G": 7},
            REPO_ROOT / "results/rq2/sc05_dev_v1/generation_dev_sc05.jsonl":
                {"U": 7, "GER": 7, rq2.FULL_HISTORY: 7},
            REPO_ROOT / "results/rq2/generation_dev_sc04.jsonl":
                {"U": 7, "G": 7, rq2.FULL_HISTORY: 7},
        }
        for path, atteso in attese.items():
            conteggio = {}
            for row in rq2.read_jsonl(path):
                conteggio[row["mode"]] = conteggio.get(row["mode"], 0) + 1
            self.assertEqual(conteggio, atteso, rq2.relative(path))
            self.assertNotIn("T", conteggio, rq2.relative(path))


if __name__ == "__main__":
    unittest.main()
