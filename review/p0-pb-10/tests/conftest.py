"""Build isolated repositories from structured checklist scenarios."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
from tools.checklist_profile import MarkdownChecklistAdapter, MarkdownChecklistDialect
from tools.profile import ChecklistProfile, LifecyclePolicy

FIXTURE_ROOT = Path(__file__).parent / "fixtures/minimal_profile"
PROPOSAL_ROOT = Path(__file__).parents[1]
PAIR_BLOCK_ID = "PB-GATE"
DEPENDENCY_PAIR_BLOCK_ID = "PB-DEPENDENCY"
UNKNOWN_PAIR_BLOCK_ID = "PB-UNKNOWN"
REQUIREMENT_ID = "REQ-GATE"
CHECKLIST_PATH = Path("docs/checklists/checklist.md")
CONTRACT_PATH = Path("docs/contracts/contract.md")
SOURCE_PATH = Path("review/gate/tools/checklist_profile.py")
TEST_PATH = Path("review/gate/tests/test_pairblock_controller.py")
FIXTURE_SOURCE_PATH = Path("review/gate/fixtures/profile.md")
SOURCE_COPIES = {
    PROPOSAL_ROOT / "tools/checklist_profile.py": SOURCE_PATH,
    PROPOSAL_ROOT / "tests/test_pairblock_controller.py": TEST_PATH,
}

TEST_PROFILE = ChecklistProfile(
    checklist_path=CHECKLIST_PATH,
    contract_path=CONTRACT_PATH,
    checklist_id="test-checklist",
    project_name="Checklist profile test",
    contract_id="test-contract",
    pair_block_pattern=r"PB-[A-Z]+",
    requirement_pattern=r"REQ-[A-Z]+",
    phase_pattern=r"([0-9]+)([A-Z])",
    lifecycle=LifecyclePolicy(
        normalized_states=(
            ("Planned", "planned"),
            ("In progress", "in_progress"),
            ("Complete", "complete"),
            ("Deferred", "deferred"),
            ("Drafting", "in_progress"),
            ("Review", "in_progress"),
            ("Approved", "in_progress"),
            ("Applied", "in_progress"),
        ),
        waiting_prefix="Waiting for ",
        drafting_status="Drafting",
        review_status="Review",
        proposal_gate_states=frozenset({"Drafting", "Review"}),
        transitions=(
            ("approve", "Review", "Approved"),
            ("accept", "Approved", "Applied"),
            ("register", "Applied", "Complete"),
        ),
        resolved_dependency_states=frozenset({"Applied", "Complete"}),
    ),
)

TEST_DIALECT = MarkdownChecklistDialect(
    pair_block_table_header=(
        "| PairBlock | Proposal gate | Resolution status | Depends on | "
        "Contract declaration | Proposed code |"
    ),
    requirement_table_header="| Requirement | State | Phase | Depends on | Gate |",
    requirement_map_header=("| ID | Contract boundary | Owning block declarations |"),
    contract_table_header=(
        "| Work unit | Current state | Owning phase | Completion evidence |"
    ),
    contract_link_prefix="[Contract]",
    proposed_code_link_prefix="[Source and tests]",
)

TEST_ADAPTER = MarkdownChecklistAdapter(
    profile=TEST_PROFILE,
    dialect=TEST_DIALECT,
)


@dataclass(frozen=True, slots=True)
class PairBlockFixture:
    """Represent one PairBlock rendered into an isolated test repository."""

    pair_block_id: str
    status: str


def _relative_link(source: Path, target: Path) -> str:
    """Return one POSIX link from a Markdown document to a repository path."""

    return Path(os.path.relpath(target, source.parent)).as_posix()


def _dependency_cell(dependencies: tuple[str, ...]) -> str:
    """Render the checklist's exact dependency-cell syntax."""

    if not dependencies:
        return "None"
    return ", ".join(f"`{item}`" for item in dependencies)


def _pair_block_row(
    block: PairBlockFixture,
    *,
    dependencies: tuple[str, ...],
    proposed: bool,
) -> str:
    """Render one PairBlock status row from structured values."""

    contract_link = _relative_link(CHECKLIST_PATH, CONTRACT_PATH)
    declaration = (
        f"[Block]({contract_link}#{block.pair_block_id.lower()})"
    )
    proposed_code = "Pending"
    if proposed:
        proposed_code = (
            f"[Source and tests]({contract_link}#"
            f"{block.pair_block_id.lower()}-proposed-code)"
        )
    return (
        f"| `{block.pair_block_id}` | Pending | {block.status} | "
        f"{_dependency_cell(dependencies)} | {declaration} | {proposed_code} |"
    )


def _ownership_row(block: PairBlockFixture, *, proposed: bool) -> str:
    """Render one contract ownership row from structured values."""

    checklist_link = _relative_link(CONTRACT_PATH, CHECKLIST_PATH)
    proposed_code = (
        f"[Source and tests](#{block.pair_block_id.lower()}-proposed-code)"
        if proposed
        else "Pending"
    )
    return (
        f"| [`{block.pair_block_id}`]({checklist_link}#pairblock-resolution) | "
        "Exercise the gate. | "
        f"Test author. | {proposed_code} | Test gate. |"
    )


def _checkbox(block: PairBlockFixture) -> str:
    """Render one globally validated PairBlock checkbox marker."""

    mark = "x" if block.status == TEST_PROFILE.lifecycle.complete_status else " "
    return (
        f"- [{mark}] Exercise `{block.pair_block_id}`.\n"
        f"      <!-- pair-block: {block.pair_block_id} -->\n"
        f"      <!-- pair-block-contract: {block.pair_block_id} "
        f"contract={CONTRACT_PATH.as_posix()} -->"
    )


@dataclass(frozen=True, slots=True)
class RepositoryFactory:
    """Create one Git repository containing a rendered checklist scenario."""

    temporary_root: Path

    def __call__(
        self,
        *,
        command: str,
        status: str | None = None,
        dependencies: tuple[str, ...] = (),
        dependency: PairBlockFixture | None = None,
    ) -> Path:
        """Render one scenario, copy the reviewed source, and commit the result."""

        repository = self.temporary_root / "repository"
        shutil.copytree(FIXTURE_ROOT, repository)
        for source, relative_destination in SOURCE_COPIES.items():
            destination = repository / relative_destination
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)

        target = PairBlockFixture(
            PAIR_BLOCK_ID,
            status or TEST_PROFILE.lifecycle.drafting_status,
        )
        blocks = [target] if dependency is None else [dependency, target]
        normalized_states = [
            TEST_PROFILE.lifecycle.normalize(block.status) for block in blocks
        ]
        if all(state == "planned" for state in normalized_states):
            requirement_state = "Planned"
        elif all(state == "complete" for state in normalized_states):
            requirement_state = "Complete"
        else:
            requirement_state = "In progress"
        pair_block_rows = []
        ownership_rows = []
        declaration_headings = []
        block_links = []
        checkboxes = []
        for block in blocks:
            is_target = block.pair_block_id == target.pair_block_id
            block_dependencies = dependencies if is_target else ()
            pair_block_rows.append(
                _pair_block_row(
                    block,
                    dependencies=block_dependencies,
                    proposed=is_target,
                )
            )
            ownership_rows.append(_ownership_row(block, proposed=is_target))
            declaration_headings.append(f"#### {block.pair_block_id}")
            block_links.append(
                f"[`{block.pair_block_id}`](#{block.pair_block_id.lower()})"
            )
            checkboxes.append(_checkbox(block))

        replacements = {
            CHECKLIST_PATH: {
                "{{PAIR_BLOCK_ROWS}}": "\n".join(pair_block_rows),
                "{{REQUIREMENT_ID}}": REQUIREMENT_ID,
                "{{REQUIREMENT_STATE}}": requirement_state,
                "{{CONTRACT_STATE}}": requirement_state,
                "{{CHECKBOXES}}": "\n\n".join(checkboxes),
            },
            CONTRACT_PATH: {
                "{{REQUIREMENT_ID}}": REQUIREMENT_ID,
                "{{BLOCK_LINKS}}": ", ".join(block_links),
                "{{OWNERSHIP_ROWS}}": "\n".join(ownership_rows),
                "{{DECLARATION_HEADINGS}}": "\n\n".join(declaration_headings),
                "{{PAIR_BLOCK_ID}}": target.pair_block_id,
                "{{STATUS_LINK}}": (
                    f"{_relative_link(CONTRACT_PATH, CHECKLIST_PATH)}"
                    "#pairblock-resolution"
                ),
                "{{SOURCE_LINK}}": _relative_link(CONTRACT_PATH, SOURCE_PATH),
                "{{TEST_LINK}}": _relative_link(CONTRACT_PATH, TEST_PATH),
                "{{COMMAND}}": command,
            },
        }
        for relative_path, values in replacements.items():
            path = repository / relative_path
            text = path.read_text(encoding="utf-8")
            for marker, value in values.items():
                if text.count(marker) != 1:
                    raise ValueError(
                        f"{relative_path} must contain one {marker} marker"
                    )
                text = text.replace(marker, value)
            path.write_text(text, encoding="utf-8")

        subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
        subprocess.run(
            ["git", "config", "user.name", "PairBlock Test"],
            cwd=repository,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "pairblock@example.invalid"],
            cwd=repository,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=repository, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "fixture"],
            cwd=repository,
            check=True,
        )
        return repository


@pytest.fixture
def repository_factory(tmp_path: Path) -> RepositoryFactory:
    """Return a scenario factory rooted in one temporary directory."""

    return RepositoryFactory(tmp_path)
