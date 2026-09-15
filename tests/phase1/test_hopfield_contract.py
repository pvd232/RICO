"""Verify the typed Phase 1 boundary against retained Phase 0 evidence."""

from __future__ import annotations

import json
import unittest
from itertools import pairwise
from pathlib import Path

import tomllib

ROOT = Path(__file__).parents[2]
CONTRACT = ROOT / "contracts/mantra-hopfield-reconstruction.toml"
CHECKLIST = ROOT / "checklists/mantra-rebuild.toml"
EXECUTION_CONTRACT = ROOT / "contracts/mantra-execution-foundation.toml"
MIL_CONTRACT = ROOT / "contracts/mantra-mil-reconstruction.toml"
DATA_CONTRACT = ROOT / "contracts/mantra-data-foundation.toml"
PRIOR_CONTRACT = ROOT / "contracts/mantra-prior-reconstruction.toml"
RESPONSE_CONTRACT = ROOT / "contracts/mantra-response-reconstruction.toml"
FIRST_PRINCIPLES_CONTRACT = ROOT / "contracts/mantra-first-principles-models.toml"
GRAPH_CONTRACT = ROOT / "contracts/mantra-graph-encoder-v1.toml"
PHASE0_EVIDENCE = ROOT / "archive/mantra-rebuild-phase-0/evidence"
PHASE0_INDEX = PHASE0_EVIDENCE / "phase0/index.json"
EXPECTED_ENCODER_SHA256 = (
    "2433527c3b23b66a16cedc0f7bc43867e4298af4d7a0733b202a8018ba876610"
)
EXPECTED_PREDICTION_SHA256 = (
    "d7180c4669a11b0b2fb184814aafb48ebafe75b02e4bd07998c337aa64dc59b7"
)
EXPECTED_HOLD_PEARSON_DELTA = "0.5861640938949398"
MODERN_ENCODER_SHA256 = (
    "af1f62c4c315c65e7379b97c57646b49b35c7f3fc3f69fcf6f94f0c8df276da9"
)
MODERN_PREDICTION_SHA256 = (
    "f8e8e6a6fe291143debd3d8e8b3ab9c4e2aed5afd3b2391e7856c7d8fd7e262b"
)
MODERN_HOLD_PEARSON_DELTA = "0.5861640983697456"
PRIOR_PACKAGE_BLOCK_IDS = [
    "P4-PB-04",
    *[f"P4-PB-05{suffix}" for suffix in "ABCDEFGHIJKLMNOPQSTUVWXYZ"],
]
COMPRESSED_PRIOR_BLOCK_IDS = [f"P4-PB-06{suffix}" for suffix in "ABCDEFGHIJK"]


def verify_selected_baseline(
    claim: str,
    receipt: dict[str, object],
    encoder_sha256: str,
) -> None:
    """Require one declaration claim to name the retained Phase 0 result."""
    prediction_sha256 = receipt["raw_gene_predictions_sha256"]
    scores = receipt["scores"]
    if not isinstance(prediction_sha256, str) or not isinstance(scores, dict):
        raise TypeError("Phase 0 receipt has an invalid result shape")
    hold_score = scores["hold_PearsonDelta"]
    identities_match = (
        EXPECTED_ENCODER_SHA256 in claim
        and encoder_sha256 == EXPECTED_ENCODER_SHA256
        and prediction_sha256 in claim
        and str(hold_score) in claim
    )
    if not identities_match:
        raise AssertionError("Phase 1 declaration names another Hopfield result")


def archived_phase0_path(recorded_path: str) -> Path:
    """Resolve retained Phase 0 receipt paths through the archive."""
    prefix = "evidence/"
    if not recorded_path.startswith(prefix):
        raise ValueError(f"unexpected Phase 0 evidence path: {recorded_path}")
    return PHASE0_EVIDENCE / recorded_path.removeprefix(prefix)


class HopfieldContractTests(unittest.TestCase):
    """Keep the first Phase 1 plan attached to the selected Phase 0 result."""

    def test_names_selected_phase0_baseline(self) -> None:
        """Require the contract and retained index to name the trusted replay."""
        contract_text = CONTRACT.read_text(encoding="utf-8")
        contract = tomllib.loads(contract_text)
        phase0 = json.loads(PHASE0_INDEX.read_text(encoding="utf-8"))

        self.assertEqual(contract["contract_id"], "mantra-hopfield-reconstruction")
        self.assertIn(EXPECTED_ENCODER_SHA256, contract_text)
        self.assertIn(EXPECTED_PREDICTION_SHA256, contract_text)
        self.assertIn(EXPECTED_HOLD_PEARSON_DELTA, contract_text)
        replay = phase0["evidence"]["hopfield_replay_receipt"]
        self.assertEqual(
            replay["path"],
            "evidence/phase0/mantra/hopfield_output_parity_receipt.json",
        )
        replay_path = archived_phase0_path(replay["path"])
        self.assertTrue(replay_path.is_file())
        receipt = json.loads(replay_path.read_text(encoding="utf-8"))
        restoration = phase0["evidence"]["restoration_bindings"]
        restoration_bindings = json.loads(
            archived_phase0_path(restoration["path"]).read_text(encoding="utf-8")
        )
        encoder_binding = next(
            binding
            for binding in restoration_bindings
            if binding["destination"].endswith("BASE_STEP01_MODEL_WEIGHTS.npz")
        )
        verify_selected_baseline(
            contract["requirements"][0]["claim"],
            receipt,
            encoder_binding["expected"]["sha256"],
        )

    def test_rejects_changed_prediction_identity(self) -> None:
        """Demonstrate that changing the selected prediction breaks the boundary."""
        contract = tomllib.loads(CONTRACT.read_text(encoding="utf-8"))
        changed_claim = contract["requirements"][0]["claim"].replace(
            EXPECTED_PREDICTION_SHA256,
            "0" * 64,
        )

        receipt = json.loads(
            archived_phase0_path(
                "evidence/phase0/mantra/hopfield_output_parity_receipt.json"
            ).read_text(encoding="utf-8")
        )

        with self.assertRaisesRegex(AssertionError, "another Hopfield result"):
            verify_selected_baseline(
                changed_claim,
                receipt,
                EXPECTED_ENCODER_SHA256,
            )

    def test_places_replay_requirements_with_their_first_consumers(self) -> None:
        """Keep replay foundations early and defer modular kernels until use."""
        checklist = tomllib.loads(CHECKLIST.read_text(encoding="utf-8"))
        phase = next(phase for phase in checklist["phases"] if phase["number"] == 1)

        self.assertEqual(
            phase,
            {
                "number": 1,
                "title": "GPU foundation and Hopfield reconstruction",
                "requirement_ids": [
                    "E0-REQ-01",
                    "E0-REQ-02",
                    "E0-REQ-03",
                    "E0-REQ-12",
                    "E0-REQ-09",
                    *[f"H1-REQ-{index:02d}" for index in range(1, 8)],
                    "H1-REQ-10",
                    "H1-REQ-11",
                    "H1-REQ-08",
                ],
            },
        )

    def test_separates_control_and_response_ieg_policies(self) -> None:
        """Keep nuisance removal out of the response target gene axis."""
        data = tomllib.loads(DATA_CONTRACT.read_text(encoding="utf-8"))
        response = tomllib.loads(RESPONSE_CONTRACT.read_text(encoding="utf-8"))
        data_claim = next(
            item["claim"] for item in data["requirements"] if item["id"] == "D3-REQ-07"
        )
        claims = {item["id"]: item["claim"] for item in response["requirements"]}

        self.assertIn("core immediate-early genes", data_claim)
        self.assertIn("retaining the core immediate-early genes", data_claim)
        self.assertIn(
            "excludes the core immediate-early-gene blacklist", claims["R5-REQ-01"]
        )
        self.assertIn("regress the immediate-early-gene score", claims["R5-REQ-02"])
        self.assertIn("complete GEARS target axis", claims["R5-REQ-04"])

    def test_registers_every_roadmap_contract_and_phase(self) -> None:
        """Require the master workspace to encode the complete roadmap."""
        checklist = tomllib.loads(CHECKLIST.read_text(encoding="utf-8"))
        phases = checklist["phases"]

        self.assertEqual(checklist["checklist_id"], "mantra-rebuild")
        self.assertEqual(
            checklist["contract_paths"],
            [
                "contracts/mantra-execution-foundation.toml",
                "contracts/mantra-hopfield-reconstruction.toml",
                "contracts/mantra-mil-reconstruction.toml",
                "contracts/mantra-data-foundation.toml",
                "contracts/mantra-prior-reconstruction.toml",
                "contracts/mantra-response-reconstruction.toml",
                "contracts/mantra-first-principles-models.toml",
                "contracts/mantra-graph-encoder-v1.toml",
            ],
        )
        self.assertEqual(
            {phase["number"]: phase["requirement_ids"] for phase in phases},
            {
                1: [
                    "E0-REQ-01",
                    "E0-REQ-02",
                    "E0-REQ-03",
                    "E0-REQ-12",
                    "E0-REQ-09",
                    *[f"H1-REQ-{index:02d}" for index in range(1, 8)],
                    "H1-REQ-10",
                    "H1-REQ-11",
                    "H1-REQ-08",
                ],
                2: [
                    "E0-REQ-10",
                    *[f"M2-REQ-{index:02d}" for index in range(1, 7)],
                    "H1-REQ-09",
                ],
                3: [f"D3-REQ-{index:02d}" for index in range(1, 8)],
                4: [
                    "E0-REQ-11",
                    *[f"P4-REQ-{index:02d}" for index in range(1, 7)],
                    *[f"P4-REQ-10{suffix}" for suffix in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"],
                    *[f"P4-REQ-20{suffix}" for suffix in "ABCDEFGHIJK"],
                ],
                5: [
                    "E0-REQ-04",
                    "E0-REQ-05",
                    "E0-REQ-06",
                    "E0-REQ-08",
                    *[f"R5-REQ-{index:02d}" for index in range(1, 8)],
                ],
                6: [
                    "E0-REQ-07",
                    *[f"S6-REQ-{index:02d}" for index in range(1, 10)],
                ],
                7: [f"H7-REQ-{index:02d}" for index in range(1, 6)],
                8: [f"M8-REQ-{index:02d}" for index in range(1, 7)],
                9: [f"B9-REQ-{index:02d}" for index in range(1, 3)],
                10: ["GE-REQ-01", "GE-REQ-02"],
                11: ["GE-REQ-03", "GE-REQ-04"],
                12: ["GE-REQ-05", "GE-REQ-06", "GE-REQ-07"],
            },
        )

        execution = tomllib.loads(EXECUTION_CONTRACT.read_text(encoding="utf-8"))
        contract = tomllib.loads(CONTRACT.read_text(encoding="utf-8"))
        mil = tomllib.loads(MIL_CONTRACT.read_text(encoding="utf-8"))
        data = tomllib.loads(DATA_CONTRACT.read_text(encoding="utf-8"))
        prior = tomllib.loads(PRIOR_CONTRACT.read_text(encoding="utf-8"))
        response = tomllib.loads(RESPONSE_CONTRACT.read_text(encoding="utf-8"))
        first_principles = tomllib.loads(
            FIRST_PRINCIPLES_CONTRACT.read_text(encoding="utf-8")
        )
        graph = tomllib.loads(GRAPH_CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(
            [requirement["id"] for requirement in execution["requirements"]],
            [f"E0-REQ-{index:02d}" for index in range(1, 13)],
        )
        self.assertEqual(
            [requirement["id"] for requirement in contract["requirements"]],
            [
                *[f"H1-REQ-{index:02d}" for index in range(1, 10)],
                "H1-REQ-10",
                "H1-REQ-11",
            ],
        )
        self.assertEqual(
            [requirement["id"] for requirement in mil["requirements"]],
            [f"M2-REQ-{index:02d}" for index in range(1, 7)],
        )
        self.assertEqual(
            [requirement["id"] for requirement in data["requirements"]],
            [f"D3-REQ-{index:02d}" for index in range(1, 8)],
        )
        self.assertEqual(
            [requirement["id"] for requirement in prior["requirements"]],
            [
                *[f"P4-REQ-{index:02d}" for index in range(1, 7)],
                *[f"P4-REQ-10{suffix}" for suffix in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"],
                *[f"P4-REQ-20{suffix}" for suffix in "ABCDEFGHIJK"],
            ],
        )
        self.assertEqual(
            [requirement["id"] for requirement in response["requirements"]],
            [f"R5-REQ-{index:02d}" for index in range(1, 8)],
        )
        self.assertEqual(
            [requirement["id"] for requirement in first_principles["requirements"]],
            [
                *[f"S6-REQ-{index:02d}" for index in range(1, 10)],
                *[f"H7-REQ-{index:02d}" for index in range(1, 6)],
                *[f"M8-REQ-{index:02d}" for index in range(1, 7)],
                *[f"B9-REQ-{index:02d}" for index in range(1, 3)],
            ],
        )
        self.assertEqual(
            [requirement["id"] for requirement in graph["requirements"]],
            [f"GE-REQ-{index:02d}" for index in range(1, 8)],
        )

    def test_orders_input_convergence_before_modular_substitution(self) -> None:
        """Freeze both replay results before changing inputs or model code."""
        execution = tomllib.loads(EXECUTION_CONTRACT.read_text(encoding="utf-8"))
        hopfield = tomllib.loads(CONTRACT.read_text(encoding="utf-8"))
        data = tomllib.loads(DATA_CONTRACT.read_text(encoding="utf-8"))
        models = tomllib.loads(FIRST_PRINCIPLES_CONTRACT.read_text(encoding="utf-8"))

        hopfield_requirements = {
            requirement["id"]: requirement for requirement in hopfield["requirements"]
        }
        hopfield_blocks = {block["id"]: block for block in hopfield["pair_blocks"]}
        data_requirements = {
            requirement["id"]: requirement for requirement in data["requirements"]
        }
        model_requirements = {
            requirement["id"]: requirement for requirement in models["requirements"]
        }
        execution_requirements = {
            requirement["id"]: requirement for requirement in execution["requirements"]
        }

        self.assertEqual(
            hopfield_requirements["H1-REQ-09"]["depends_on"],
            ["H1-REQ-08", "M2-REQ-06", "E0-REQ-08", "E0-REQ-09"],
        )
        self.assertEqual(
            hopfield_blocks["H1-PB-09"]["depends_on"],
            ["H1-PB-08", "M2-PB-06", "E0-PB-08", "E0-PB-09"],
        )
        self.assertIn(
            "input-width binding from 187 to 267",
            hopfield_requirements["H1-REQ-09"]["claim"],
        )
        self.assertIn(
            "seeded scikit-learn Lloyd KMeans",
            execution_requirements["E0-REQ-08"]["claim"],
        )
        self.assertIn(
            "full-dataset training",
            execution_requirements["E0-REQ-09"]["claim"],
        )
        self.assertIn(
            "128-row optimizer batches only through device-side indices",
            execution_requirements["E0-REQ-10"]["claim"],
        )
        self.assertEqual(
            data_requirements["D3-REQ-01"]["depends_on"],
            ["H1-REQ-09", "M2-REQ-06"],
        )
        self.assertEqual(
            model_requirements["S6-REQ-09"]["depends_on"],
            ["S6-REQ-08", "E0-REQ-09", "E0-REQ-10"],
        )
        self.assertEqual(
            model_requirements["S6-REQ-08"]["depends_on"],
            ["S6-REQ-07", "E0-REQ-08"],
        )
        self.assertIn(
            "H1-REQ-09 MIL-stack bridge baseline",
            model_requirements["S6-REQ-08"]["claim"],
        )
        self.assertEqual(
            model_requirements["H7-REQ-01"]["depends_on"][0],
            "S6-REQ-09",
        )
        self.assertEqual(
            model_requirements["M8-REQ-01"]["depends_on"][0],
            "S6-REQ-09",
        )

    def test_reconstructs_inputs_after_freezing_the_modern_replay(self) -> None:
        """Require one-at-a-time source rebuilds before rebuilt-only replay."""
        contract = tomllib.loads(CONTRACT.read_text(encoding="utf-8"))
        contract_text = CONTRACT.read_text(encoding="utf-8")
        requirements = {
            requirement["id"]: requirement for requirement in contract["requirements"]
        }
        blocks = {block["id"]: block for block in contract["pair_blocks"]}

        self.assertIn(MODERN_ENCODER_SHA256, contract_text)
        self.assertIn(MODERN_PREDICTION_SHA256, contract_text)
        self.assertIn(MODERN_HOLD_PEARSON_DELTA, contract_text)
        self.assertEqual(requirements["H1-REQ-10"]["depends_on"], ["H1-REQ-07"])
        self.assertEqual(requirements["H1-REQ-11"]["depends_on"], ["H1-REQ-10"])
        self.assertEqual(requirements["H1-REQ-08"]["depends_on"], ["H1-REQ-11"])
        self.assertIn("FutureInputRefs", requirements["H1-REQ-11"]["claim"])

        reconstruction_blocks = [f"H1-PB-05{suffix}" for suffix in "ABCDEFGHIJKLM"]
        self.assertEqual(blocks[reconstruction_blocks[0]]["depends_on"], ["H1-PB-07"])
        for previous, current in pairwise(reconstruction_blocks):
            self.assertEqual(blocks[current]["depends_on"], [previous])
            self.assertEqual(blocks[current]["requirement_ids"], ["H1-REQ-10"])
        self.assertEqual(blocks["H1-PB-05"]["depends_on"], ["H1-PB-05M"])
        self.assertEqual(
            blocks["H1-PB-05"]["requirement_ids"],
            ["H1-REQ-05", "H1-REQ-11"],
        )
        self.assertEqual(blocks["H1-PB-08"]["depends_on"], ["H1-PB-05"])

    def test_decomposes_prior_reconstruction_into_monitorable_blocks(self) -> None:
        """Give every source package and compressed array its own lifecycle row."""
        contract = tomllib.loads(PRIOR_CONTRACT.read_text(encoding="utf-8"))
        blocks = {block["id"]: block for block in contract["pair_blocks"]}

        self.assertEqual(len(PRIOR_PACKAGE_BLOCK_IDS), 26)
        self.assertEqual(len(COMPRESSED_PRIOR_BLOCK_IDS), 11)
        self.assertEqual(set(PRIOR_PACKAGE_BLOCK_IDS) - blocks.keys(), set())
        self.assertEqual(set(COMPRESSED_PRIOR_BLOCK_IDS) - blocks.keys(), set())
        self.assertEqual(
            set(blocks["P4-PB-05"]["depends_on"]),
            set(PRIOR_PACKAGE_BLOCK_IDS),
        )
        self.assertEqual(
            set(blocks["P4-PB-06"]["depends_on"]),
            set(COMPRESSED_PRIOR_BLOCK_IDS),
        )


if __name__ == "__main__":
    unittest.main()
