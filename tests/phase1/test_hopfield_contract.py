"""Verify the typed Phase 1 boundary against retained Phase 0 evidence."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

import tomllib

ROOT = Path(__file__).parents[2]
CONTRACT = ROOT / "contracts/mantra-hopfield-reconstruction.toml"
CHECKLIST = ROOT / "checklists/mantra-rebuild.toml"
MIL_CONTRACT = ROOT / "contracts/mantra-mil-reconstruction.toml"
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

    def test_places_hopfield_requirements_in_roadmap_phase_one(self) -> None:
        """Keep every Hopfield requirement in roadmap Phase 1."""
        checklist = tomllib.loads(CHECKLIST.read_text(encoding="utf-8"))
        phase = next(phase for phase in checklist["phases"] if phase["number"] == 1)

        self.assertEqual(
            phase,
            {
                "number": 1,
                "title": "Hopfield reconstruction",
                "requirement_ids": [f"H1-REQ-{index:02d}" for index in range(1, 9)],
            },
        )

    def test_registers_every_roadmap_contract_and_phase(self) -> None:
        """Require the master workspace to encode the complete Phase 1-5 map."""
        checklist = tomllib.loads(CHECKLIST.read_text(encoding="utf-8"))
        phases = checklist["phases"]

        self.assertEqual(checklist["checklist_id"], "mantra-rebuild")
        self.assertEqual(
            checklist["contract_paths"],
            [
                "contracts/mantra-hopfield-reconstruction.toml",
                "contracts/mantra-mil-reconstruction.toml",
                "contracts/mantra-graph-encoder-v1.toml",
            ],
        )
        self.assertEqual(
            {phase["number"]: phase["requirement_ids"] for phase in phases},
            {
                1: [f"H1-REQ-{index:02d}" for index in range(1, 9)],
                2: [f"M2-REQ-{index:02d}" for index in range(1, 7)],
                3: ["GE-REQ-01", "GE-REQ-02"],
                4: ["GE-REQ-03", "GE-REQ-04"],
                5: ["GE-REQ-05", "GE-REQ-06", "GE-REQ-07"],
            },
        )

        mil = tomllib.loads(MIL_CONTRACT.read_text(encoding="utf-8"))
        graph = tomllib.loads(GRAPH_CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(
            [requirement["id"] for requirement in mil["requirements"]],
            [f"M2-REQ-{index:02d}" for index in range(1, 7)],
        )
        self.assertEqual(
            [requirement["id"] for requirement in graph["requirements"]],
            [f"GE-REQ-{index:02d}" for index in range(1, 8)],
        )


if __name__ == "__main__":
    unittest.main()
