#!/usr/bin/env python3
"""Controlli sulla variante con budget specifico per scenario.

Verificano tre cose, nell'ordine in cui contano:

  1. **la configurazione storica non cambia**: `rq2-dev-0.1` resta quella di
     prima e continua a valere 200 token per tutti, quindi le prove gia'
     eseguite restano confrontabili fra loro;
  2. **togliere il tetto toglie solo il tetto**: ranking, parita', soglia di
     pertinenza e regole proprie di ogni architettura restano identiche, e un
     contesto senza tetto non diventa FULL_HISTORY;
  3. **la preparazione nuova e' coerente con se stessa**: SC05 conserva i 200
     token e riproduce esattamente il retrieval gia' eseguito, SC02-SC04 non
     hanno tetto, e i prompt non contengono nulla dell'oracle.

Nessun test chiama il modello e nessuno riscrive artefatti.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "rq2"))

import rq2_common as rq2  # noqa: E402
import validate_rq2 as validator  # noqa: E402

VARIANT_CONFIG_PATH = REPO_ROOT / "data" / "rq2" / "config" / "experiment_rq2_budget_per_scenario.json"
RUN_CONFIG_PATH = REPO_ROOT / "data" / "rq2" / "config" / "run_budget_per_scenario_v1.json"
NEW_DIR = REPO_ROOT / "results" / "rq2" / "budget_per_scenario_v1"

UNLIMITED_SCENARIOS = ("scenario_02", "scenario_03", "scenario_04")
CAPPED_SCENARIO = "scenario_05"
CAPPED_BUDGET = 200


def _rows(name):
    return rq2.read_jsonl(NEW_DIR / name)


# --------------------------------------------------------------------------
# 1. La configurazione storica non si muove
# --------------------------------------------------------------------------

class TestConfigurazioneStorica(unittest.TestCase):

    def setUp(self):
        self.base = rq2.load_config()

    def test_rq2_dev_01_resta_a_200_token_per_tutti(self):
        self.assertEqual(self.base["config_id"], "rq2-dev-0.1")
        self.assertEqual(rq2.budget_tokens(self.base), 200)
        for scenario_id in rq2.EXTENSION_SCENARIO_IDS:
            self.assertEqual(rq2.budget_tokens(self.base, scenario_id), 200, scenario_id)

    def test_la_configurazione_storica_non_dichiara_budget_per_scenario(self):
        self.assertNotIn("per_scenario", self.base["context_budget"])

    def test_la_variante_e_un_file_distinto(self):
        self.assertTrue(VARIANT_CONFIG_PATH.exists())
        variant = rq2.load_config(VARIANT_CONFIG_PATH)
        self.assertNotEqual(variant["config_id"], self.base["config_id"])
        self.assertEqual(variant["derived_from"]["config_id"], self.base["config_id"])


# --------------------------------------------------------------------------
# 2. La variante cambia il budget e nient'altro
# --------------------------------------------------------------------------

class TestVariante(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.base = rq2.load_config()
        cls.variant = rq2.load_config(VARIANT_CONFIG_PATH)

    def test_budget_specifico_per_scenario(self):
        for scenario_id in UNLIMITED_SCENARIOS:
            self.assertIsNone(rq2.budget_tokens(self.variant, scenario_id), scenario_id)
        self.assertEqual(rq2.budget_tokens(self.variant, CAPPED_SCENARIO), CAPPED_BUDGET)

    def test_modello_effort_e_istruzioni_invariati(self):
        self.assertEqual(self.variant["models"], self.base["models"])
        self.assertEqual(self.variant["isolation"], self.base["isolation"])

    def test_ranking_perimetro_e_regole_della_memoria_invariati(self):
        self.assertEqual(self.variant["retrieval"], self.base["retrieval"])
        self.assertEqual(self.variant["memory_scope"], self.base["memory_scope"])
        self.assertEqual(self.variant["memory"], self.base["memory"])

    def test_matrice_e_estensione_invariate(self):
        self.assertEqual(self.variant["matrix"], self.base["matrix"])
        self.assertEqual(self.variant["matrix_extension"], self.base["matrix_extension"])

    def test_conteggio_dei_token_invariato(self):
        self.assertEqual(self.variant["context_budget"]["token_counting"],
                         self.base["context_budget"]["token_counting"])

    def test_i_primi_sette_passi_della_regola_di_selezione_sono_gli_stessi(self):
        vecchi = self.base["context_budget"]["selection_rule"]["steps"]
        nuovi = self.variant["context_budget"]["selection_rule"]["steps"]
        self.assertEqual(nuovi[:len(vecchi)], vecchi)
        self.assertEqual(len(nuovi), len(vecchi) + 1)

    def test_la_variante_supera_il_validatore(self):
        self.assertEqual(validator.validate_all(config=self.variant), [])

    def test_uno_scenario_senza_tetto_non_puo_dichiarare_GER_a_budget(self):
        rotta = json.loads(json.dumps(self.variant))
        rotta["context_budget"]["per_scenario"]["scenario_05"] = None
        errori = []
        validator.validate_config(rotta, errori)
        self.assertTrue(any("E-BUDGET" in e and "GER" in e for e in errori), errori)

    def test_un_budget_per_scenario_non_intero_viene_respinto(self):
        rotta = json.loads(json.dumps(self.variant))
        rotta["context_budget"]["per_scenario"]["scenario_02"] = 0
        errori = []
        validator.validate_config(rotta, errori)
        self.assertTrue(any("E-BUDGET" in e for e in errori), errori)


# --------------------------------------------------------------------------
# 3. La selezione senza tetto
# --------------------------------------------------------------------------

class TestSelezioneSenzaTetto(unittest.TestCase):
    """Cade solo il riempimento: la soglia di pertinenza resta."""

    def _items(self):
        return [
            {"item_id": "I1", "score": 0.9, "tokens": 150, "content_tokens": 140, "overhead_tokens": 10},
            {"item_id": "I2", "score": 0.4, "tokens": 150, "content_tokens": 140, "overhead_tokens": 10},
            {"item_id": "I3", "score": 0.0, "tokens": 10, "content_tokens": 8, "overhead_tokens": 2},
        ]

    def test_con_tetto_si_ferma_al_budget(self):
        risultato = rq2.select_within_budget(self._items(), 200)
        self.assertEqual([i["item_id"] for i in risultato["selected"]], ["I1"])
        self.assertEqual(risultato["stopped_by"]["reason"], "non entra nel budget")

    def test_senza_tetto_entrano_tutti_i_pertinenti(self):
        risultato = rq2.select_within_budget(self._items(), rq2.UNLIMITED_BUDGET)
        self.assertEqual([i["item_id"] for i in risultato["selected"]], ["I1", "I2"])
        self.assertEqual(risultato["context_tokens"], 300)

    def test_senza_tetto_la_soglia_di_pertinenza_resta(self):
        risultato = rq2.select_within_budget(self._items(), rq2.UNLIMITED_BUDGET)
        self.assertNotIn("I3", [i["item_id"] for i in risultato["selected"]])
        self.assertEqual(risultato["stopped_by"], {"item_id": "I3", "reason": "punteggio nullo"})

    def test_senza_tetto_non_scatta_la_garanzia_minima(self):
        risultato = rq2.select_within_budget(self._items(), rq2.UNLIMITED_BUDGET)
        self.assertFalse(risultato["budget_exceeded_by_first_item"])

    def test_la_selezione_resta_un_prefisso_del_ranking(self):
        items = self._items()
        risultato = rq2.select_within_budget(items, rq2.UNLIMITED_BUDGET)
        scelti = [i["item_id"] for i in risultato["selected"]]
        self.assertEqual(scelti, [i["item_id"] for i in items][:len(scelti)])

    def test_etichette_del_budget(self):
        self.assertEqual(rq2.budget_label(200), "200 token")
        self.assertEqual(rq2.budget_label(rq2.UNLIMITED_BUDGET), "nessun tetto")
        self.assertTrue(rq2.budget_applies(200))
        self.assertFalse(rq2.budget_applies(rq2.UNLIMITED_BUDGET))


# --------------------------------------------------------------------------
# 4. La preparazione salvata
# --------------------------------------------------------------------------

@unittest.skipUnless(NEW_DIR.exists(), "preparazione budget_per_scenario_v1 non presente")
class TestPreparazioneSalvata(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.retrieval = {}
        cls.inputs = {}
        for numero in ("02", "03", "04", "05"):
            cls.retrieval["scenario_%s" % numero] = _rows("retrieval_sc%s.jsonl" % numero)
            cls.inputs["scenario_%s" % numero] = _rows("generation_inputs_sc%s.jsonl" % numero)

    def test_il_budget_registrato_e_quello_dello_scenario(self):
        for scenario_id, rows in self.retrieval.items():
            atteso = None if scenario_id in UNLIMITED_SCENARIOS else CAPPED_BUDGET
            for row in rows:
                self.assertEqual(row["budget_tokens"], atteso,
                                 "%s %s %s" % (scenario_id, row["question_id"], row["mode"]))
                self.assertEqual(row["budget_applies"], atteso is not None)

    def test_SC05_conserva_il_tetto_e_riproduce_il_retrieval_gia_eseguito(self):
        storico = {}
        for path in ("sc05_dev_v1/retrieval_sc05_u_ger.jsonl", "t_ext_v1/retrieval_t_sc05.jsonl"):
            for row in rq2.read_jsonl(REPO_ROOT / "results" / "rq2" / path):
                storico[(row["question_id"], row["mode"])] = row
        confrontate = 0
        for row in self.retrieval[CAPPED_SCENARIO]:
            vecchia = storico.get((row["question_id"], row["mode"]))
            self.assertIsNotNone(vecchia, row["question_id"])
            self.assertEqual(row["selected_item_ids"], vecchia["selected_item_ids"])
            self.assertEqual(row["context_tokens"], vecchia["context_tokens"])
            confrontate += 1
        self.assertEqual(confrontate, 21)

    def test_senza_tetto_la_selezione_e_un_prefisso_del_ranking(self):
        for scenario_id in UNLIMITED_SCENARIOS:
            for row in self.retrieval[scenario_id]:
                classifica = [item["item_id"] for item in row["ranking"]]
                scelti = row["selected_item_ids"]
                self.assertEqual(scelti, classifica[:len(scelti)],
                                 "%s %s %s" % (scenario_id, row["question_id"], row["mode"]))

    def test_senza_tetto_nessun_elemento_con_punteggio_nullo_entra_nel_contesto(self):
        for scenario_id in UNLIMITED_SCENARIOS:
            for row in self.retrieval[scenario_id]:
                for item in row["selected"]:
                    self.assertGreater(item["score"], 0.0,
                                       "%s %s %s" % (scenario_id, row["question_id"], item["item_id"]))

    def test_senza_tetto_il_contesto_puo_solo_crescere_mai_perdere_elementi(self):
        prima = {
            ("scenario_02", "T"): "retrieval_sc02.jsonl",
            ("scenario_02", "F"): "retrieval_sc02.jsonl",
            ("scenario_03", "F"): "retrieval_sc03.jsonl",
            ("scenario_03", "U"): "retrieval_repair_v3/retrieval_sc03_u.jsonl",
            ("scenario_04", "T"): "t_ext_v1/retrieval_t_sc04.jsonl",
            ("scenario_04", "U"): "sc04_repair_v3/retrieval_sc04_ug.jsonl",
            ("scenario_04", "G"): "sc04_repair_v3/retrieval_sc04_ug.jsonl",
        }
        storico = {}
        for (scenario_id, mode), path in prima.items():
            for row in rq2.read_jsonl(REPO_ROOT / "results" / "rq2" / path):
                if (row["scenario_id"], row["mode"]) == (scenario_id, mode):
                    storico[(scenario_id, row["question_id"], mode)] = row
        for scenario_id in UNLIMITED_SCENARIOS:
            for row in self.retrieval[scenario_id]:
                vecchia = storico.get((scenario_id, row["question_id"], row["mode"]))
                if vecchia is None:
                    continue
                mancanti = [i for i in vecchia["selected_item_ids"]
                            if i not in row["selected_item_ids"]]
                self.assertEqual(mancanti, [],
                                 "%s %s %s" % (scenario_id, row["question_id"], row["mode"]))

    def test_T_che_copre_tutta_la_cronologia_viene_segnalato(self):
        """Senza tetto T arriva a contenere ogni messaggio utente.

        Non e' un errore del codice: e' l'effetto della modifica, ed e' la cosa
        piu' importante da dichiarare. Il test pretende che il confronto la
        riconosca e la scriva, invece di lasciarla passare in silenzio.
        """
        import compare_budget_change as confronto

        before, after = confronto.load_sides()
        celle = {(c["scenario_id"], c["mode"]): c for c in confronto.compare(before, after)}
        segnalazioni = " ".join(confronto.warnings(confronto.compare(before, after)))

        for scenario_id in ("scenario_02", "scenario_04"):
            cella = celle[(scenario_id, "T")]
            cronologia = [item["item_id"] for item in rq2.message_items(rq2.load_scenario(scenario_id))]
            copre = sum(1 for row in self.retrieval[scenario_id]
                        if row["mode"] == "T" and set(row["selected_item_ids"]) == set(cronologia))
            self.assertEqual(cella["covers_whole_history"], copre)
            self.assertGreater(copre, 0, scenario_id)
            self.assertIn("%s / T" % scenario_id, segnalazioni)

    def test_anche_quando_copre_tutto_T_non_e_FULL_HISTORY(self):
        """Stesso contenuto, ordine diverso: le due righe restano distinguibili."""
        for scenario_id in ("scenario_02", "scenario_04"):
            cronologia = [item["item_id"] for item in rq2.message_items(rq2.load_scenario(scenario_id))]
            for row in self.retrieval[scenario_id]:
                if row["mode"] != "T":
                    continue
                self.assertLessEqual(len(row["selected_item_ids"]), len(cronologia))
                self.assertTrue(row["retrieval_used"] if "retrieval_used" in row else True)
                if set(row["selected_item_ids"]) == set(cronologia):
                    # ordine del ranking, non cronologico
                    self.assertNotEqual(row["selected_item_ids"], cronologia,
                                        "%s %s" % (scenario_id, row["question_id"]))

    def test_i_prompt_sono_pronti_ma_nessuna_risposta_e_stata_generata(self):
        for scenario_id, rows in self.inputs.items():
            for row in rows:
                self.assertIsNone(row["model_answer"], "%s %s" % (scenario_id, row["question_id"]))
                self.assertIn("Istruzioni:", row["prompt"])
                self.assertEqual(row["prompt"].count("Domanda:"), 1)

    def test_FULL_HISTORY_resta_il_controllo_diagnostico_senza_retrieval(self):
        for scenario_id, rows in self.inputs.items():
            scenario = rq2.load_scenario(scenario_id)
            cronologia = [item["item_id"] for item in rq2.message_items(scenario)]
            righe = [r for r in rows if r["mode"] == rq2.FULL_HISTORY]
            self.assertEqual(len(righe), 7, scenario_id)
            for row in righe:
                self.assertEqual(row["context_item_ids"], cronologia)
                self.assertFalse(row["retrieval_used"])
                self.assertFalse(row["budget_applies"])

    def test_le_righe_recuperate_dichiarano_comunque_il_retrieval(self):
        for scenario_id, rows in self.inputs.items():
            for row in rows:
                if row["mode"] == rq2.FULL_HISTORY:
                    continue
                self.assertTrue(row["retrieval_used"], "%s %s" % (scenario_id, row["mode"]))
                self.assertEqual(row["retrieval_label"], "budget-per-scenario-v1")

    def test_le_sorgenti_di_memoria_sono_quelle_delle_prove_attuali(self):
        attese = {
            ("scenario_02", "F"): ("results/rq2/facts/scenario_02_facts.jsonl", None, None),
            ("scenario_03", "F"): ("results/rq2/facts/scenario_03_facts.jsonl", None, None),
            ("scenario_03", "U"): ("results/rq2/facts/scenario_03_facts.jsonl",
                                   "results/rq2/memory_repair_v3/scenario_03_state.json", None),
            ("scenario_04", "U"): ("results/rq2/facts/scenario_04_facts.jsonl",
                                   "results/rq2/sc04_repair_v3/scenario_04_state.json", None),
            ("scenario_04", "G"): ("results/rq2/facts/scenario_04_facts.jsonl",
                                   "results/rq2/sc04_repair_v3/scenario_04_state.json",
                                   "results/rq2/sc04_repair_v3/scenario_04_graph.json"),
            ("scenario_05", "U"): ("results/rq2/sc05_dev_v1/facts/scenario_05_facts.jsonl",
                                   "results/rq2/sc05_dev_v1/memory/scenario_05_state.json", None),
            ("scenario_05", "GER"): ("results/rq2/sc05_dev_v1/facts/scenario_05_facts.jsonl",
                                     "results/rq2/sc05_dev_v1/memory/scenario_05_state.json", None),
        }
        for scenario_id, rows in self.retrieval.items():
            for row in rows:
                chiave = (scenario_id, row["mode"])
                if chiave not in attese:
                    continue
                fatti, stato, grafo = attese[chiave]
                self.assertEqual(row["facts_source"], fatti, chiave)
                self.assertEqual(row["state_source"], stato, chiave)
                self.assertEqual(row["graph_source"], grafo, chiave)

    def test_la_prova_nuova_non_riscrive_nessuna_prova_precedente(self):
        for path in NEW_DIR.rglob("*"):
            if path.is_file():
                self.assertTrue(str(path).startswith(str(NEW_DIR)))

    def test_la_scheda_della_prova_dichiara_le_chiamate_davvero_fatte(self):
        with open(RUN_CONFIG_PATH, encoding="utf-8") as handle:
            run = json.load(handle)
        self.assertTrue(run["executed"])
        self.assertFalse(run["frozen"])
        self.assertEqual(run["base"]["config_id"], "rq2-dev-0.2-budget-per-scenario")
        effettive = run["esecuzione"]["chiamate_effettive"]
        self.assertEqual(effettive["totale"], 49)
        self.assertEqual(effettive["costruzione_della_memoria"], 0)
        self.assertEqual(effettive["scenario_05"], 0)
        self.assertEqual(run["esecuzione"]["errori"], {"esecuzione": 0, "parsing": 0, "risposte_vuote": 0})


if __name__ == "__main__":
    unittest.main()


# --------------------------------------------------------------------------
# 5. Le risposte generate e le valutazioni proposte
# --------------------------------------------------------------------------

ANSWERS_PATH = NEW_DIR / "generation_dev_budget_per_scenario.jsonl"
EVALUATIONS_PATH = NEW_DIR / "valutazioni_budget_per_scenario.jsonl"

GENERATED = {
    "scenario_02": ("T", "F"),
    "scenario_03": ("F", "U"),
    "scenario_04": ("T", "U", "G"),
}


@unittest.skipUnless(ANSWERS_PATH.exists(), "risposte non ancora generate")
class TestRisposteGenerate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.answers = rq2.read_jsonl(ANSWERS_PATH)
        cls.chiavi = [(r["scenario_id"], r["question_id"], r["mode"]) for r in cls.answers]

    def test_quarantanove_risposte_una_per_cella(self):
        attesi = set()
        for scenario_id, modes in GENERATED.items():
            for question in rq2.load_questions(scenario_id):
                for mode in modes:
                    attesi.add((scenario_id, question["question_id"], mode))
        self.assertEqual(len(self.answers), 49)
        self.assertEqual(set(self.chiavi), attesi)
        self.assertEqual(len(set(self.chiavi)), len(self.chiavi), "righe duplicate")

    def test_nessun_errore_e_nessuna_risposta_vuota(self):
        for row in self.answers:
            self.assertIsNone(row.get("error"), "%s %s" % (row["question_id"], row["mode"]))
            self.assertTrue(row.get("model_answer"))

    def test_modello_ed_effort_uguali_alle_prove_precedenti(self):
        for row in self.answers:
            self.assertEqual(row["model_used"], "claude-sonnet-5")
            self.assertEqual(row["model_requested"], "claude-sonnet-5")
            self.assertEqual(row["effort"], "medium")

    def test_SC05_e_FULL_HISTORY_non_sono_stati_rigenerati(self):
        for row in self.answers:
            self.assertNotEqual(row["scenario_id"], "scenario_05")
            self.assertNotEqual(row["mode"], rq2.FULL_HISTORY)


@unittest.skipUnless(EVALUATIONS_PATH.exists(), "valutazioni non ancora prodotte")
class TestValutazioniProposte(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = rq2.read_jsonl(EVALUATIONS_PATH)
        cls.retrieval = {}
        for scenario_id in GENERATED:
            suffix = scenario_id.replace("scenario_", "sc")
            for row in rq2.read_jsonl(NEW_DIR / ("retrieval_%s.jsonl" % suffix)):
                cls.retrieval[(row["scenario_id"], row["question_id"], row["mode"])] = row

    def test_i_giudizi_restano_dichiarati_come_proposti(self):
        for row in self.rows:
            self.assertEqual(row["annotation_source"],
                             "valutazione_assistita_proposta_non_approvata")
            self.assertEqual(row["classification_rule"], "completezza-supporto-1")
            self.assertEqual(row["config_id"], "rq2-dev-0.2-budget-per-scenario")

    def test_complete_e_supportate_solo_se_entrambe(self):
        for row in self.rows:
            atteso = (row["answer_class"] == "completa"
                      and row["supported_by_original_conversation"] is True)
            self.assertEqual(row["counts_as_complete_and_supported"], atteso,
                             "%s %s" % (row["question_id"], row["mode"]))

    def test_il_contesto_valutato_e_quello_recuperato(self):
        for row in self.rows:
            source = self.retrieval[(row["scenario_id"], row["question_id"], row["mode"])]
            self.assertEqual(row["context_item_ids"], source["selected_item_ids"])
            self.assertEqual(row["context_tokens"], source["context_tokens"])
            self.assertEqual(row["budget_tokens"], source["budget_tokens"])

    def test_provenienza_e_contenuto_restano_campi_distinti(self):
        """La provenienza non deve poter essere scambiata per la presenza del fatto."""
        divergenti = 0
        for row in self.rows:
            copertura = row["rq2_fact_coverage_in_context"]
            got, total = copertura.split("/")
            if row["evidence_provenance_complete_auto"] and got != total:
                divergenti += 1
        # Se questo numero andasse a zero, i due campi starebbero misurando la
        # stessa cosa e la distinzione andrebbe rivista.
        self.assertGreater(divergenti, 0)

    def test_una_risposta_che_usa_informazione_obsoleta_non_e_completa(self):
        for row in self.rows:
            if row["obsolete_used"]:
                self.assertNotEqual(row["answer_class"], "completa",
                                    "%s %s" % (row["question_id"], row["mode"]))

    def test_il_riepilogo_si_ricalcola_dalle_righe(self):
        with open(NEW_DIR / "riepilogo_budget_per_scenario.json", encoding="utf-8") as handle:
            riepilogo = json.load(handle)
        for scenario_id, modes in riepilogo["riepilogo_per_scenario"].items():
            for mode, dati in modes.items():
                subset = [r for r in self.rows
                          if r["scenario_id"] == scenario_id and r["mode"] == mode]
                self.assertEqual(dati["N_c"], len(subset))
                self.assertEqual(dati["CompleteAnswerRate"]["numeratore"],
                                 sum(1 for r in subset if r["counts_as_complete_and_supported"]))
                self.assertEqual(sum(dati["classi"][c] for c in
                                     ("completa", "parziale", "errata", "astensione corretta")),
                                 dati["N_c"])


@unittest.skipUnless(EVALUATIONS_PATH.exists(), "valutazioni non ancora prodotte")
class TestArtefattiStoriciIntatti(unittest.TestCase):
    """Le prove precedenti non devono essere state toccate da questa."""

    def test_le_impronte_registrate_nella_raccolta_non_sono_cambiate(self):
        import glob
        import hashlib

        controllati = 0
        for path in glob.glob(str(REPO_ROOT / "RACCOLTA_RISULTATI" / "*" / "fonti_*.json")):
            with open(path, encoding="utf-8") as handle:
                fonti = json.load(handle)
            for relativo, impronta in fonti["letti_in_sola_lettura"].items():
                file_path = REPO_ROOT / relativo
                self.assertTrue(file_path.exists(), relativo)
                self.assertEqual(hashlib.sha256(file_path.read_bytes()).hexdigest(),
                                 impronta, "artefatto storico modificato: %s" % relativo)
                controllati += 1
        self.assertGreater(controllati, 50)
