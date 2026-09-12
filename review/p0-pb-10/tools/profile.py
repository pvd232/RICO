"""Define project-owned syntax and lifecycle policy for checklist profiles."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_GLOBAL_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*")
_GLOBAL_STATES = frozenset({"planned", "in_progress", "complete", "deferred"})


@dataclass(frozen=True, slots=True)
class LifecyclePolicy:
    """Map project status labels to global states and legal transitions.

    Attributes:
        normalized_states: Project labels paired with global checklist states.
        waiting_prefix: Prefix that marks a dependency-wait status.
        drafting_status: Status assigned while Codex prepares a proposal.
        review_status: Status assigned after the proposal gate passes.
        proposal_gate_states: Statuses from which the proposal gate may run.
        resolved_dependency_states: Statuses that satisfy another PairBlock's
            dependency.
    """

    normalized_states: tuple[tuple[str, str], ...]
    waiting_prefix: str
    drafting_status: str
    review_status: str
    proposal_gate_states: frozenset[str]
    resolved_dependency_states: frozenset[str]

    def __post_init__(self) -> None:
        """Reject ambiguous labels and transitions when the profile is created."""

        labels = [label for label, _ in self.normalized_states]
        if len(labels) != len(set(labels)):
            raise ValueError("lifecycle status labels must be unique")
        invalid_states = [
            state
            for _, state in self.normalized_states
            if state not in _GLOBAL_STATES
        ]
        if invalid_states:
            raise ValueError(f"invalid normalized lifecycle states: {invalid_states}")
        declared = set(labels)
        referenced = (
            set(self.proposal_gate_states)
            | set(self.resolved_dependency_states)
            | {self.drafting_status, self.review_status}
        )
        if not referenced <= declared:
            raise ValueError(
                f"lifecycle policy references undeclared statuses: "
                f"{sorted(referenced - declared)}"
            )
        if self.drafting_status == self.review_status:
            raise ValueError("drafting and review statuses must differ")
        if {self.drafting_status, self.review_status} - self.proposal_gate_states:
            raise ValueError("proposal gate states must include drafting and review")
        if not self.waiting_prefix:
            raise ValueError("waiting prefix must not be empty")

    def normalize(self, status: str) -> str:
        """Return the global checklist state represented by one project status."""

        if status.startswith(self.waiting_prefix):
            return "planned"
        states = dict(self.normalized_states)
        try:
            return states[status]
        except KeyError as error:
            raise ValueError(f"unknown lifecycle status: {status}") from error


@dataclass(frozen=True, slots=True)
class ChecklistProfile:
    """Own one project's paths, identifiers, Markdown syntax, and lifecycle.

    Attributes:
        checklist_path: Repository-relative Markdown checklist to compile.
        contract_path: Repository-relative contract governed by the profile.
        checklist_id: Stable checklist identity emitted in the manifest.
        project_name: Human-readable name emitted in the manifest.
        contract_id: Stable contract identity used by requirements and blocks.
        pair_block_pattern: Full-match expression for PairBlock identifiers.
        requirement_pattern: Full-match expression for requirement identifiers.
        phase_pattern: Expression whose two capture groups order phases.
        pair_block_table_header: Exact PairBlock status-table header.
        requirement_table_header: Exact requirement-assignment table header.
        requirement_map_header: Exact contract requirement-map table header.
        proposed_code_link_prefix: Link text that identifies runnable code.
        lifecycle: Project status vocabulary and legal gate transitions.
    """

    checklist_path: Path
    contract_path: Path
    checklist_id: str
    project_name: str
    contract_id: str
    pair_block_pattern: str
    requirement_pattern: str
    phase_pattern: str
    pair_block_table_header: str
    requirement_table_header: str
    requirement_map_header: str
    proposed_code_link_prefix: str
    lifecycle: LifecyclePolicy

    def __post_init__(self) -> None:
        """Reject invalid paths, identities, expressions, and Markdown markers."""

        for label, path in (
            ("checklist_path", self.checklist_path),
            ("contract_path", self.contract_path),
        ):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"{label} must be repository-relative")
        for label, value in (
            ("checklist_id", self.checklist_id),
            ("contract_id", self.contract_id),
        ):
            if _GLOBAL_ID.fullmatch(value) is None:
                raise ValueError(f"{label} is not a global checklist identifier")
        for label, pattern in (
            ("pair_block_pattern", self.pair_block_pattern),
            ("requirement_pattern", self.requirement_pattern),
        ):
            try:
                re.compile(pattern)
            except re.error as error:
                raise ValueError(f"{label} is not a valid expression") from error
        try:
            phase_expression = re.compile(self.phase_pattern)
        except re.error as error:
            raise ValueError("phase_pattern is not a valid expression") from error
        if phase_expression.groups != 2:
            raise ValueError("phase_pattern must capture numeric and letter groups")
        for label, value in (
            ("project_name", self.project_name),
            ("pair_block_table_header", self.pair_block_table_header),
            ("requirement_table_header", self.requirement_table_header),
            ("requirement_map_header", self.requirement_map_header),
            ("proposed_code_link_prefix", self.proposed_code_link_prefix),
        ):
            if not value.strip():
                raise ValueError(f"{label} must not be empty")

    def accepts_pair_block_id(self, value: str) -> bool:
        """Return whether an identifier belongs to this profile's PairBlocks."""

        return (
            _GLOBAL_ID.fullmatch(value) is not None
            and re.fullmatch(self.pair_block_pattern, value) is not None
        )

    def accepts_requirement_id(self, value: str) -> bool:
        """Return whether an identifier belongs to this profile's requirements."""

        return (
            _GLOBAL_ID.fullmatch(value) is not None
            and re.fullmatch(self.requirement_pattern, value) is not None
        )


MANTRA_PHASE0_PROFILE = ChecklistProfile(
    checklist_path=Path("docs/checklists/mantra-rebuild.md"),
    contract_path=Path("docs/contracts/mantra-rebuild-phase-0.md"),
    checklist_id="mantra-rebuild",
    project_name="MANTRA rebuild",
    contract_id="mantra-rebuild-phase-0",
    pair_block_pattern=r"P0-PB-[0-9A-Z]+",
    requirement_pattern=r"P0-REQ-[0-9]+",
    phase_pattern=r"([0-9]+)([A-Z])",
    pair_block_table_header=(
        "| PairBlock | Proposal gate | Resolution status | Depends on | "
        "Contract declaration | Proposed code |"
    ),
    requirement_table_header="| Requirement | State | Phase | Depends on | Gate |",
    requirement_map_header=(
        "| ID | Contract boundary | Owning block declarations |"
    ),
    proposed_code_link_prefix="[Source and tests]",
    lifecycle=LifecyclePolicy(
        normalized_states=(
            ("Planned", "planned"),
            ("In progress", "in_progress"),
            ("Complete", "complete"),
            ("Deferred", "deferred"),
            ("Codex drafting", "planned"),
            ("Codex tracing", "in_progress"),
            ("Awaiting user review", "in_progress"),
            ("Artifact table approved; graph freeze open", "in_progress"),
            ("Approved for MANTRA implementation", "in_progress"),
            ("Implemented; awaiting applied-code review", "in_progress"),
            ("Accepted; awaiting VIPER registration", "in_progress"),
        ),
        waiting_prefix="Waiting for ",
        drafting_status="Codex drafting",
        review_status="Awaiting user review",
        proposal_gate_states=frozenset(
            {"Codex drafting", "Awaiting user review"}
        ),
        resolved_dependency_states=frozenset(
            {
                "Approved for MANTRA implementation",
                "Implemented; awaiting applied-code review",
                "Accepted; awaiting VIPER registration",
                "Complete",
            }
        ),
    ),
)
