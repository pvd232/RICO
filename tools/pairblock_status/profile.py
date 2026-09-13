"""Define project-owned syntax and lifecycle policy for checklist profiles."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeGuard

_GLOBAL_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]*")
_GLOBAL_STATES = frozenset({"planned", "in_progress", "complete", "deferred"})

type EvidenceKind = Literal["artifact", "command", "external", "test"]
EVIDENCE_KINDS: frozenset[EvidenceKind] = frozenset(
    {"artifact", "command", "external", "test"}
)


def is_evidence_kind(value: object) -> TypeGuard[EvidenceKind]:
    """Return whether ``value`` names a global gate or evidence category."""

    return isinstance(value, str) and value in EVIDENCE_KINDS


class PairBlockGateError(RuntimeError):
    """Report a declaration, validation, or lifecycle violation."""


@dataclass(frozen=True, slots=True)
class LifecycleEvidenceRule:
    """Assign one accepted evidence category to a lifecycle event.

    Attributes:
        event: Lifecycle event governed by the rule.
        kind: Evidence category accepted for that event.
    """

    event: str
    kind: EvidenceKind

    def __post_init__(self) -> None:
        """Reject empty event names and unsupported evidence categories."""

        if not self.event:
            raise ValueError("lifecycle evidence event must not be empty")
        if not is_evidence_kind(self.kind):
            raise ValueError(f"invalid lifecycle evidence kind: {self.kind}")


@dataclass(frozen=True, slots=True)
class LifecyclePolicy:
    """Map project status labels to global states and legal transitions.

    Attributes:
        normalized_states: Project labels paired with global checklist states.
        waiting_prefix: Prefix that marks a dependency-wait status.
        drafting_status: Status assigned while Codex prepares a proposal.
        review_status: Status assigned after the proposal gate passes.
        proposal_gate_states: Statuses from which the proposal gate may run.
        non_code_review_event: Event that submits a documentation-only block.
        non_code_complete_event: Event that accepts that reviewed block.
        transitions: Evidence events paired with their required current and
            resulting statuses.
        resolved_dependency_states: Statuses that make a dependent PairBlock
            ready for drafting.
        legacy_certification_event: Event that closes an applied block whose
            preserved receipts predate the active lifecycle policy.
        evidence_rules: Evidence categories required by executable events.
    """

    normalized_states: tuple[tuple[str, str], ...]
    waiting_prefix: str
    drafting_status: str
    review_status: str
    proposal_gate_states: frozenset[str]
    non_code_review_event: str
    non_code_complete_event: str
    transitions: tuple[tuple[str, str, str], ...]
    resolved_dependency_states: frozenset[str]
    legacy_certification_event: str | None = None
    evidence_rules: tuple[LifecycleEvidenceRule, ...] = ()

    def __post_init__(self) -> None:
        """Reject ambiguous labels and transitions when the profile is created."""

        labels = [label for label, _ in self.normalized_states]
        if len(labels) != len(set(labels)):
            raise ValueError("lifecycle status labels must be unique")
        invalid_states = [
            state for _, state in self.normalized_states if state not in _GLOBAL_STATES
        ]
        if invalid_states:
            raise ValueError(f"invalid normalized lifecycle states: {invalid_states}")
        declared = set(labels)
        transition_events = [
            self.non_code_review_event,
            self.non_code_complete_event,
            *(event for event, _, _ in self.transitions),
        ]
        if self.legacy_certification_event is not None:
            transition_events.append(self.legacy_certification_event)
        if len(transition_events) != len(set(transition_events)):
            raise ValueError("lifecycle transition events must be unique")
        if any(not event for event in transition_events):
            raise ValueError("lifecycle transition event must not be empty")
        transition_statuses = {
            status
            for _, before, after in self.transitions
            for status in (before, after)
        }
        referenced = (
            set(self.proposal_gate_states)
            | set(self.resolved_dependency_states)
            | transition_statuses
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
        expected_before = self.review_status
        for event, before, after in self.transitions:
            if before != expected_before:
                raise ValueError(
                    f"lifecycle transition chain expected {expected_before}, "
                    f"received {before}"
                )
            expected_before = after
        if self.normalize(expected_before) != "complete":
            raise ValueError("lifecycle transition chain must end at complete")
        executable_events = {event for event, _, _ in self.transitions}
        evidence_events = [rule.event for rule in self.evidence_rules]
        if len(evidence_events) != len(set(evidence_events)):
            raise ValueError("lifecycle evidence events must be unique")
        if set(evidence_events) != executable_events:
            raise ValueError(
                "lifecycle evidence rules must cover every executable event"
            )

    def normalize(self, status: str) -> str:
        """Return the global checklist state represented by one project status."""

        if status.startswith(self.waiting_prefix):
            return "planned"
        states = dict(self.normalized_states)
        try:
            return states[status]
        except KeyError as error:
            raise ValueError(f"unknown lifecycle status: {status}") from error

    def advance(self, status: str, event: str) -> str:
        """Return the next status for one evidence-backed lifecycle event."""

        transitions = {
            transition_event: (before, after)
            for transition_event, before, after in self.transitions
        }
        transitions[self.non_code_review_event] = (
            self.drafting_status,
            self.review_status,
        )
        transitions[self.non_code_complete_event] = (
            self.review_status,
            self.complete_status,
        )
        if self.legacy_certification_event is not None:
            transitions[self.legacy_certification_event] = (
                self.transitions[-1][1],
                self.complete_status,
            )
        try:
            before, after = transitions[event]
        except KeyError as error:
            raise ValueError(f"unknown lifecycle event: {event}") from error
        if status != before:
            raise ValueError(f"{event} cannot advance {status}; expected {before}")
        return after

    def required_evidence_kind(self, event: str) -> EvidenceKind:
        """Return the evidence category assigned to one executable event."""

        try:
            return next(
                rule.kind for rule in self.evidence_rules if rule.event == event
            )
        except StopIteration as error:
            raise ValueError(f"event has no evidence rule: {event}") from error

    @property
    def complete_status(self) -> str:
        """Return the project label that normalizes to the completed state."""

        return self.transitions[-1][2]

    @property
    def transition_events(self) -> tuple[str, ...]:
        """Return legal evidence events in lifecycle order."""

        events = (
            self.non_code_review_event,
            self.non_code_complete_event,
            *(event for event, _, _ in self.transitions),
        )
        if self.legacy_certification_event is None:
            return events
        return (*events, self.legacy_certification_event)

    @property
    def non_code_transitions(self) -> tuple[tuple[str, str, str], ...]:
        """Return the external-review route for a documentation-only block."""

        return (
            (
                self.non_code_review_event,
                self.drafting_status,
                self.review_status,
            ),
            (
                self.non_code_complete_event,
                self.review_status,
                self.complete_status,
            ),
        )

    def completion_transitions(
        self,
        final_event: object,
    ) -> tuple[tuple[str, str, str], ...]:
        """Return the complete lifecycle route selected by its final event."""

        if final_event == self.non_code_complete_event:
            return self.non_code_transitions
        if final_event == self.transitions[-1][0]:
            return self.transitions
        if (
            self.legacy_certification_event is not None
            and final_event == self.legacy_certification_event
        ):
            return (
                (
                    self.legacy_certification_event,
                    self.transitions[-1][1],
                    self.complete_status,
                ),
            )
        raise ValueError(f"unknown completion event: {final_event}")


@dataclass(frozen=True, slots=True)
class ChecklistProfile:
    """Own one project's paths, identifiers, and lifecycle policy.

    Attributes:
        checklist_path: Repository-relative Markdown checklist to compile.
        contract_path: Repository-relative contract governed by the profile.
        checklist_id: Stable checklist identity emitted in the manifest.
        project_name: Human-readable name emitted in the manifest.
        contract_id: Stable contract identity used by requirements and blocks.
        pair_block_pattern: Full-match expression for PairBlock identifiers.
        requirement_pattern: Full-match expression for requirement identifiers.
        phase_pattern: Expression whose two capture groups order phases.
        lifecycle: Project status vocabulary and legal gate transitions.
        proposal_source_roots: Paths, resolved from the checklist repository,
            that may own reviewed proposal files.
        declaration_path: Repository-relative typed declaration manifest.
        repository_roots: Repository IDs paired with paths resolved from the
            checklist repository.
        legacy_certifiable_pair_blocks: Applied blocks permitted to use the
            lifecycle policy's exceptional certification event.
    """

    checklist_path: Path
    contract_path: Path
    checklist_id: str
    project_name: str
    contract_id: str
    pair_block_pattern: str
    requirement_pattern: str
    phase_pattern: str
    lifecycle: LifecyclePolicy
    proposal_source_roots: tuple[Path, ...] = ()
    declaration_path: Path | None = None
    repository_roots: tuple[tuple[str, Path], ...] = ()
    legacy_certifiable_pair_blocks: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        """Reject invalid paths, identities, and identifier expressions."""

        for label, path in (
            ("checklist_path", self.checklist_path),
            ("contract_path", self.contract_path),
        ):
            if path.is_absolute() or ".." in path.parts:
                raise ValueError(f"{label} must be repository-relative")
        for source_root in self.proposal_source_roots:
            if source_root.is_absolute():
                raise ValueError("proposal_source_roots must be repository-relative")
        if self.declaration_path is not None and (
            self.declaration_path.is_absolute() or ".." in self.declaration_path.parts
        ):
            raise ValueError("declaration_path must be repository-relative")
        repository_ids = [repository_id for repository_id, _ in self.repository_roots]
        if len(repository_ids) != len(set(repository_ids)):
            raise ValueError("repository_roots IDs must be unique")
        for repository_id, repository_root in self.repository_roots:
            if _GLOBAL_ID.fullmatch(repository_id) is None:
                raise ValueError(f"invalid repository ID: {repository_id}")
            if repository_root.is_absolute():
                raise ValueError("repository_roots paths must be repository-relative")
        invalid_legacy_ids = sorted(
            value
            for value in self.legacy_certifiable_pair_blocks
            if not self.accepts_pair_block_id(value)
        )
        if invalid_legacy_ids:
            raise ValueError(
                f"invalid legacy-certifiable PairBlock IDs: {invalid_legacy_ids}"
            )
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
        if not self.project_name.strip():
            raise ValueError("project_name must not be empty")

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

    def require_declaration_path(self) -> Path:
        """Return the declaration path required by manifest-native operations."""

        if self.declaration_path is None:
            raise PairBlockGateError("profile has no declaration_path")
        return self.declaration_path


MANTRA_PHASE0_PROFILE = ChecklistProfile(
    checklist_path=Path("docs/checklists/mantra-rebuild.md"),
    contract_path=Path("docs/contracts/mantra-rebuild-phase-0.md"),
    checklist_id="mantra-rebuild",
    project_name="MANTRA rebuild",
    contract_id="mantra-rebuild-phase-0",
    pair_block_pattern=r"P0-PB-[0-9A-Z]+",
    requirement_pattern=r"P0-REQ-[0-9]+",
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
        non_code_review_event="submit",
        non_code_complete_event="confirm",
        transitions=(
            ("approve", "Review", "Approved"),
            ("accept", "Approved", "Applied"),
            ("register", "Applied", "Complete"),
        ),
        resolved_dependency_states=frozenset({"Applied", "Complete"}),
        legacy_certification_event="certify",
        evidence_rules=(
            LifecycleEvidenceRule("approve", "external"),
            LifecycleEvidenceRule("accept", "artifact"),
            LifecycleEvidenceRule("register", "artifact"),
        ),
    ),
    proposal_source_roots=(Path("../mantra"), Path("../viper")),
    declaration_path=Path("docs/contracts/mantra-rebuild.declarations.toml"),
    repository_roots=(
        ("rico", Path(".")),
        ("mantra", Path("../mantra")),
        ("viper", Path("../viper")),
    ),
    legacy_certifiable_pair_blocks=frozenset(
        {"P0-PB-01", "P0-PB-04A", "P0-PB-04B", "P0-PB-05A"}
    ),
)
