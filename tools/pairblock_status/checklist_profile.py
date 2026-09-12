"""Compile RICO's Markdown checklist into the established normalized manifest."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from .execution_identity import sha256_file
from .profile import MANTRA_PHASE0_PROFILE, ChecklistProfile

DEFAULT_MASTER_CHECKLIST_VALIDATOR = (
    Path.home() / ".agents/scripts/validate-master-checklist.py"
)
_ROW_ID = re.compile(r"^`([^`]+)`$")
_LINK = re.compile(r"^\[[^]]+\]\(([^)#]+)(?:#([^)]+))?\)$")
_DOCUMENT_LINK = re.compile(r"\[[^]]+\]\(([^)#\s]+)#([^)\s]+)\)")
_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")
_RECEIPT_LINK = re.compile(r"\[receipt\]\(([^)]+)\)")
_MARKDOWN_LINK = re.compile(r"\[([^]]+)\]\(([^)]+)\)")
_CHECKBOX = re.compile(r"^\s*- \[([ xX])\] ")


class PairBlockGateError(RuntimeError):
    """Report a RICO profile, validation, or gate-transition violation."""


@dataclass(frozen=True, slots=True)
class PairBlockRow:
    """Represent one authoritative PairBlock lifecycle row in the checklist."""

    pair_block_id: str
    gate: str
    status: str
    dependencies: tuple[str, ...]
    declaration: str
    proposed_code: str


@dataclass(frozen=True, slots=True)
class PairBlockPlacement:
    """Locate one PairBlock checkbox and record whether it is checked."""

    section: str
    checkbox_line: int
    checked: bool


@dataclass(frozen=True, slots=True)
class ProposalContract:
    """Represent one proposed code boundary and its contract-declared command."""

    path: Path
    command: str
    source_paths: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class MarkdownChecklistDialect:
    """Describe the RICO tables that extend the standard checklist markers.

    Attributes:
        pair_block_table_header: Exact PairBlock status-table header.
        requirement_table_header: Exact requirement-assignment table header.
        requirement_map_header: Exact contract requirement-map table header.
        contract_table_header: Exact checklist contract-coverage table header.
        contract_link_prefix: Link cell that selects this profile's contract.
        proposed_code_link_prefix: Link text that identifies runnable code.
    """

    pair_block_table_header: str
    requirement_table_header: str
    requirement_map_header: str
    contract_table_header: str
    contract_link_prefix: str
    proposed_code_link_prefix: str

    def __post_init__(self) -> None:
        """Reject empty Markdown markers when the adapter is configured."""

        for name, value in (
            ("pair_block_table_header", self.pair_block_table_header),
            ("requirement_table_header", self.requirement_table_header),
            ("requirement_map_header", self.requirement_map_header),
            ("contract_table_header", self.contract_table_header),
            ("contract_link_prefix", self.contract_link_prefix),
            ("proposed_code_link_prefix", self.proposed_code_link_prefix),
        ):
            if not value.strip():
                raise ValueError(f"{name} must not be empty")


@dataclass(frozen=True, slots=True)
class MarkdownChecklistAdapter:
    """Translate one project checklist between Markdown and core records.

    Attributes:
        profile: Project identities, paths, and lifecycle policy.
        dialect: RICO Markdown tables layered on the standard checklist markers.
    """

    profile: ChecklistProfile
    dialect: MarkdownChecklistDialect

    def parse_pair_block_rows(self, checklist_text: str) -> dict[str, PairBlockRow]:
        """Parse the configured PairBlock status table."""

        return parse_pair_block_rows(checklist_text, self.profile, self.dialect)

    def has_proposed_code(self, row: PairBlockRow) -> bool:
        """Return whether a status row links to runnable proposed code."""

        return self.dialect.proposed_code_link_prefix in row.proposed_code

    def current_receipt(self, row: PairBlockRow) -> str | None:
        """Return the receipt linked from a PairBlock row, when present."""

        links = _RECEIPT_LINK.findall(row.gate)
        if len(links) > 1:
            raise PairBlockGateError(f"{row.pair_block_id} gate links several receipts")
        return links[0] if links else None

    def load_proposal_contract(
        self,
        repository: Path,
        checklist_path: Path,
        row: PairBlockRow,
    ) -> ProposalContract:
        """Resolve one runnable proposal through this Markdown dialect."""

        return load_proposal_contract(
            repository,
            checklist_path,
            row,
            self.profile,
        )

    def compile_normalized_manifest(
        self,
        repository: Path,
        checklist_text: str,
        rows: dict[str, PairBlockRow],
    ) -> dict[str, object]:
        """Compile the Markdown records into the core manifest structure."""

        return compile_normalized_manifest(
            repository,
            checklist_text,
            rows,
            self.profile,
            self.dialect,
        )

    def record_gate_result(
        self,
        repository: Path,
        checklist_text: str,
        row: PairBlockRow,
        *,
        test_count: int,
        receipt_path: str,
        status: str,
    ) -> bytes:
        """Render one gate result into the configured PairBlock table."""

        gate = f"Passed: `{test_count}` tests ([receipt]({receipt_path}))"
        rendered = _replace_status_row(
            checklist_text,
            pair_block_id=row.pair_block_id,
            gate=gate,
            status=status,
        )
        return _render_derived_states(
            repository,
            rendered,
            self.profile,
            self.dialect,
        ).encode("utf-8")

    def render_transition(
        self,
        repository: Path,
        checklist_text: str,
        row: PairBlockRow,
        *,
        receipt_path: str,
        status: str,
    ) -> bytes:
        """Render one lifecycle transition and every derived checklist state."""

        return render_transition(
            repository,
            checklist_text,
            row,
            receipt_path=receipt_path,
            status=status,
            profile=self.profile,
            dialect=self.dialect,
        )

    def validate_traceability(
        self,
        repository: Path,
        *,
        validator_path: Path = DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    ) -> tuple[dict[str, PairBlockRow], dict[str, object]]:
        """Validate Markdown links and the compiled core manifest."""

        return validate_traceability(
            repository,
            validator_path=validator_path,
            profile=self.profile,
            dialect=self.dialect,
        )


def _split_row(line: str) -> list[str]:
    """Split one pipe-delimited Markdown table row into stripped cells."""

    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _replace_status_row(
    checklist_text: str,
    *,
    pair_block_id: str,
    gate: str,
    status: str,
    proposed_code: str | None = None,
) -> str:
    """Replace lifecycle-owned cells in one parsed PairBlock row."""

    lines = checklist_text.splitlines()
    matches: list[tuple[int, list[str]]] = []
    for line_index, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = _split_row(line)
        match = _ROW_ID.fullmatch(cells[0])
        if match is not None and match.group(1) == pair_block_id:
            matches.append((line_index, cells))
    if len(matches) != 1:
        raise PairBlockGateError(
            f"expected one rendered status row for {pair_block_id}"
        )
    line_index, cells = matches[0]
    cells[1] = gate
    cells[2] = status
    if proposed_code is not None:
        cells[5] = proposed_code
    lines[line_index] = "| " + " | ".join(cells) + " |"
    suffix = "\n" if checklist_text.endswith("\n") else ""
    return "\n".join(lines) + suffix


def _active_code_links(
    row: PairBlockRow,
    dialect: MarkdownChecklistDialect,
) -> str:
    """Map one accepted proposal's staging links to its active code paths."""

    links = _MARKDOWN_LINK.findall(row.proposed_code)
    marker_label = dialect.proposed_code_link_prefix.removeprefix("[").removesuffix("]")
    has_marker = any(label == marker_label for label, _ in links)
    if "/staging/" not in row.proposed_code and not has_marker:
        return row.proposed_code
    active_links: list[str] = []
    staging_segment = f"/staging/{row.pair_block_id.lower()}/"
    for label, target in links:
        if label == marker_label:
            continue
        if "/staging/" in target and staging_segment not in target:
            raise PairBlockGateError(
                f"{row.pair_block_id} proposal link does not use {staging_segment}"
            )
        active_target = target.replace(staging_segment, "/", 1)
        active_links.append(f"[{label}]({active_target})")
    if not active_links:
        raise PairBlockGateError(
            f"{row.pair_block_id} has no staging source links to activate"
        )
    return " · ".join(active_links)


def _replace_checkbox(
    checklist_text: str,
    placement: PairBlockPlacement,
    *,
    checked: bool,
) -> str:
    """Render one PairBlock checkbox from its lifecycle completion state."""

    lines = checklist_text.splitlines()
    line = lines[placement.checkbox_line]
    match = _CHECKBOX.match(line)
    if match is None:
        raise PairBlockGateError("PairBlock marker is not preceded by a checkbox")
    mark = "x" if checked else " "
    lines[placement.checkbox_line] = (
        line[: match.start(1)] + mark + line[match.end(1) :]
    )
    suffix = "\n" if checklist_text.endswith("\n") else ""
    return "\n".join(lines) + suffix


def _replace_requirement_states(
    checklist_text: str,
    states: dict[str, str],
    dialect: MarkdownChecklistDialect,
) -> str:
    """Render all requirement states derived from their mapped PairBlocks."""

    lines = checklist_text.splitlines()
    try:
        header_index = lines.index(dialect.requirement_table_header)
    except ValueError as error:
        raise PairBlockGateError("requirement table header is missing") from error
    seen: set[str] = set()
    for line_index in range(header_index + 2, len(lines)):
        if not lines[line_index].startswith("|"):
            break
        cells = _split_row(lines[line_index])
        requirement_id = cells[0].strip("`")
        if requirement_id not in states:
            continue
        cells[1] = states[requirement_id]
        lines[line_index] = "| " + " | ".join(cells) + " |"
        seen.add(requirement_id)
    if seen != set(states):
        raise PairBlockGateError(
            f"requirement rows differ: missing={sorted(set(states) - seen)}"
        )
    suffix = "\n" if checklist_text.endswith("\n") else ""
    return "\n".join(lines) + suffix


def _replace_contract_state(
    checklist_text: str,
    state: str,
    dialect: MarkdownChecklistDialect,
) -> str:
    """Render the derived contract state in its coverage-table row."""

    lines = checklist_text.splitlines()
    try:
        header_index = lines.index(dialect.contract_table_header)
    except ValueError as error:
        raise PairBlockGateError("contract table header is missing") from error
    matches: list[tuple[int, list[str]]] = []
    for line_index in range(header_index + 2, len(lines)):
        if not lines[line_index].startswith("|"):
            break
        cells = _split_row(lines[line_index])
        if cells[0].startswith(dialect.contract_link_prefix):
            matches.append((line_index, cells))
    if len(matches) != 1:
        raise PairBlockGateError("expected one contract coverage row")
    line_index, cells = matches[0]
    cells[1] = state
    lines[line_index] = "| " + " | ".join(cells) + " |"
    suffix = "\n" if checklist_text.endswith("\n") else ""
    return "\n".join(lines) + suffix


def _rendered_contract_state(
    checklist_text: str,
    profile: ChecklistProfile,
    dialect: MarkdownChecklistDialect,
) -> str:
    """Read the project contract's state from the coverage table."""

    matches = [
        cells
        for cells in _table_rows(checklist_text, dialect.contract_table_header)
        if cells[0].startswith(dialect.contract_link_prefix)
    ]
    if len(matches) != 1:
        raise PairBlockGateError("expected one contract coverage row")
    return _normalized_state(matches[0][1], profile)


def _display_state(state: str) -> str:
    """Return the checklist label for one normalized global state."""

    return {
        "planned": "Planned",
        "in_progress": "In progress",
        "complete": "Complete",
        "deferred": "Deferred",
    }[state]


def _contract_state(states: list[str]) -> str:
    """Derive one contract state from its requirement and PairBlock states."""

    if all(state == "complete" for state in states):
        return "complete"
    if all(state == "planned" for state in states):
        return "planned"
    if all(state == "deferred" for state in states):
        return "deferred"
    return "in_progress"


def _parse_dependencies(
    value: str,
    profile: ChecklistProfile,
) -> tuple[str, ...]:
    """Parse the exact comma-separated PairBlock dependency syntax."""

    if value == "None":
        return ()
    dependencies = tuple(re.findall(r"`([^`]+)`", value))
    expected = ", ".join(f"`{item}`" for item in dependencies)
    if not dependencies or value != expected:
        raise PairBlockGateError(f"invalid dependency cell: {value}")
    invalid = [item for item in dependencies if not profile.accepts_pair_block_id(item)]
    if invalid:
        raise PairBlockGateError(f"invalid dependency IDs: {invalid}")
    return dependencies


def parse_pair_block_rows(
    checklist_text: str,
    profile: ChecklistProfile,
    dialect: MarkdownChecklistDialect,
) -> dict[str, PairBlockRow]:
    """Parse the status table and reject duplicate or cyclic PairBlocks."""

    lines = checklist_text.splitlines()
    try:
        header_index = lines.index(dialect.pair_block_table_header)
    except ValueError as error:
        raise PairBlockGateError("PairBlock status table header is missing") from error

    rows: dict[str, PairBlockRow] = {}
    for line_index in range(header_index + 2, len(lines)):
        line = lines[line_index]
        if not line.startswith("|"):
            break
        cells = _split_row(line)
        if len(cells) != 6:
            raise PairBlockGateError("PairBlock status row must contain six cells")
        match = _ROW_ID.fullmatch(cells[0])
        if match is None:
            raise PairBlockGateError(f"invalid PairBlock status cell: {cells[0]}")
        pair_block_id = match.group(1)
        if not profile.accepts_pair_block_id(pair_block_id):
            raise PairBlockGateError(f"invalid PairBlock ID: {pair_block_id}")
        if pair_block_id in rows:
            raise PairBlockGateError(f"duplicate PairBlock row: {pair_block_id}")
        rows[pair_block_id] = PairBlockRow(
            pair_block_id=pair_block_id,
            gate=cells[1],
            status=cells[2],
            dependencies=_parse_dependencies(cells[3], profile),
            declaration=cells[4],
            proposed_code=cells[5],
        )
    if not rows:
        raise PairBlockGateError("PairBlock status table contains no rows")
    _validate_dependency_graph(rows)
    return rows


def _validate_dependency_graph(rows: dict[str, PairBlockRow]) -> None:
    """Reject missing, self-referential, or cyclic PairBlock dependencies."""

    for row in rows.values():
        for dependency in row.dependencies:
            if dependency not in rows:
                raise PairBlockGateError(
                    f"{row.pair_block_id} names unknown dependency {dependency}"
                )
            if dependency == row.pair_block_id:
                raise PairBlockGateError(f"{row.pair_block_id} depends on itself")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(pair_block_id: str) -> None:
        """Depth-first visit one dependency branch and expose a back edge."""

        if pair_block_id in visiting:
            raise PairBlockGateError("PairBlock dependency graph contains a cycle")
        if pair_block_id in visited:
            return
        visiting.add(pair_block_id)
        for dependency in rows[pair_block_id].dependencies:
            visit(dependency)
        visiting.remove(pair_block_id)
        visited.add(pair_block_id)

    for pair_block_id in rows:
        visit(pair_block_id)


def _resolve_link(base: Path, value: str) -> tuple[Path, str | None]:
    """Resolve one Markdown link relative to its declaring document."""

    match = _LINK.fullmatch(value)
    if match is None:
        raise PairBlockGateError(f"expected one Markdown link, received: {value}")
    return (base / match.group(1)).resolve(), match.group(2)


def _resolve_named_link(
    base: Path,
    value: str,
    link_prefix: str,
) -> tuple[Path, str | None]:
    """Resolve the one Markdown link introduced by ``link_prefix``."""

    matches = re.findall(
        re.escape(link_prefix) + r"\(([^)#]+)(?:#([^)]+))?\)",
        value,
    )
    if len(matches) != 1:
        raise PairBlockGateError(
            f"expected one {link_prefix} link, received: {value}"
        )
    target, fragment = matches[0]
    return (base / target).resolve(), fragment or None


def _proposal_section(text: str, pair_block_id: str) -> str:
    """Return one PairBlock's complete proposed-code section."""

    marker = f"##### `{pair_block_id}` proposed code"
    start = text.find(marker)
    if start < 0:
        raise PairBlockGateError(
            f"proposed-code section is missing for {pair_block_id}"
        )
    remainder = text[start + len(marker) :]
    next_heading = re.search(r"(?m)^#{3,5} ", remainder)
    end = (
        len(text)
        if next_heading is None
        else start + len(marker) + next_heading.start()
    )
    return text[start:end]


def _proposal_boundary(
    proposal: str,
    label: str,
    *,
    required: bool,
) -> str:
    """Return one bold-labeled proposal boundary or an empty optional boundary."""

    marker = f"**{label}:**"
    start = proposal.find(marker)
    if start < 0:
        if required:
            raise PairBlockGateError(f"proposal lacks its {label.lower()}")
        return ""
    remainder = proposal[start + len(marker) :]
    next_label = re.search(r"(?m)^\*\*[^*\n]+:\*\*", remainder)
    if next_label is None:
        return remainder
    return remainder[: next_label.start()]


def _declaration_heading(contract_text: str, pair_block_id: str) -> None:
    """Require one renderer-visible heading for a PairBlock."""

    heading = f"#### {pair_block_id}"
    if contract_text.splitlines().count(heading) != 1:
        raise PairBlockGateError(
            f"contract must contain one native PairBlock heading for {pair_block_id}"
        )


def _heading_fragments(markdown: str) -> set[str]:
    """Return renderer-visible fragments for the document's native headings."""

    fragments = set()
    for line in markdown.splitlines():
        match = _HEADING.fullmatch(line)
        if match is None:
            continue
        title = match.group(1).lower().replace("`", "")
        title = re.sub(r"[^a-z0-9 _-]", "", title)
        fragments.add(re.sub(r"[ ]+", "-", title.strip()))
    return fragments


def _allowed_owner_roots(
    repository: Path,
    profile: ChecklistProfile,
) -> tuple[Path, ...]:
    """Resolve the checklist repository and each approved source repository."""

    return (repository,) + tuple(
        (repository / root).resolve() for root in profile.proposal_source_roots
    )


def validate_document_fragments(
    repository: Path,
    document_path: Path,
    profile: ChecklistProfile,
) -> None:
    """Require each relative fragment to name a heading in an approved owner."""

    document = document_path.read_text(encoding="utf-8")
    allowed_roots = _allowed_owner_roots(repository, profile)
    for relative_target, fragment in _DOCUMENT_LINK.findall(document):
        parsed_target = urlsplit(relative_target)
        if parsed_target.scheme or parsed_target.netloc:
            continue
        target = (document_path.parent / relative_target).resolve()
        if not any(target.is_relative_to(root) for root in allowed_roots):
            raise PairBlockGateError(
                f"document link escapes the approved owner roots: {target}"
            )
        if not target.is_file():
            raise PairBlockGateError(f"document link target does not exist: {target}")
        if fragment not in _heading_fragments(target.read_text(encoding="utf-8")):
            raise PairBlockGateError(
                f"document link fragment does not name a native heading: "
                f"{relative_target}#{fragment}"
            )


def _ownership_row(contract_text: str, pair_block_id: str) -> list[str]:
    """Return the unique ownership row for one contract declaration."""

    marker = f"[`{pair_block_id}`]("
    matches = []
    for line in contract_text.splitlines():
        if not line.startswith("|"):
            continue
        cells = _split_row(line)
        if len(cells) == 5 and cells[0].startswith(marker):
            matches.append(line)
    if len(matches) != 1:
        raise PairBlockGateError(
            f"contract must contain one ownership row for {pair_block_id}"
        )
    cells = _split_row(matches[0])
    if len(cells) != 5 or not cells[2]:
        raise PairBlockGateError(f"implementation owner is missing for {pair_block_id}")
    return cells


def validate_declaration(
    repository: Path,
    checklist_path: Path,
    row: PairBlockRow,
) -> None:
    """Connect one status row to exactly one contract owner declaration."""

    contract_path, anchor = _resolve_link(checklist_path.parent, row.declaration)
    if not contract_path.is_relative_to(repository):
        raise PairBlockGateError("contract path escapes the repository")
    if anchor is None:
        raise PairBlockGateError(
            f"declaration anchor is missing for {row.pair_block_id}"
        )
    expected_anchor = row.pair_block_id.lower()
    if anchor != expected_anchor:
        raise PairBlockGateError(
            f"declaration link differs for {row.pair_block_id}"
        )
    contract_text = contract_path.read_text(encoding="utf-8")
    _declaration_heading(contract_text, row.pair_block_id)
    _ownership_row(contract_text, row.pair_block_id)


def load_proposal_contract(
    repository: Path,
    checklist_path: Path,
    row: PairBlockRow,
    profile: ChecklistProfile,
) -> ProposalContract:
    """Resolve a runnable proposal from its status row and governing contract."""

    if not profile.accepts_pair_block_id(row.pair_block_id):
        raise PairBlockGateError(f"invalid PairBlock ID: {row.pair_block_id}")
    contract_path, declaration_anchor = _resolve_link(
        checklist_path.parent, row.declaration
    )
    if not contract_path.is_relative_to(repository):
        raise PairBlockGateError("contract path escapes the repository")
    contract_text = contract_path.read_text(encoding="utf-8")
    if declaration_anchor is None:
        raise PairBlockGateError(
            f"declaration anchor is missing for {row.pair_block_id}"
        )
    expected_declaration = row.pair_block_id.lower()
    if declaration_anchor != expected_declaration:
        raise PairBlockGateError(
            f"declaration link differs for {row.pair_block_id}"
        )
    _declaration_heading(contract_text, row.pair_block_id)
    _ownership_row(contract_text, row.pair_block_id)

    proposed_path, proposed_fragment = _resolve_named_link(
        checklist_path.parent,
        row.proposed_code,
        "[Source and tests]",
    )
    if proposed_path != contract_path:
        raise PairBlockGateError(
            f"proposed-code link leaves the governing contract for {row.pair_block_id}"
        )
    expected_fragment = f"{row.pair_block_id.lower()}-proposed-code"
    if proposed_fragment != expected_fragment:
        raise PairBlockGateError(f"proposed-code link differs for {row.pair_block_id}")

    proposal = _proposal_section(contract_text, row.pair_block_id)
    if "**Code boundary:**" not in proposal or "**Gate:**" not in proposal:
        raise PairBlockGateError(
            f"proposed-code section lacks its code boundary or gate for {row.pair_block_id}"
        )

    focused = re.search(
        r"\*\*Focused check:\*\*\s*```bash\n(.*?)\n```",
        proposal,
        flags=re.DOTALL,
    )
    if focused is None:
        raise PairBlockGateError(f"focused check is missing for {row.pair_block_id}")
    command = focused.group(1).strip()

    code_boundary = _proposal_boundary(proposal, "Code boundary", required=True)
    fixture_boundary = _proposal_boundary(
        proposal,
        "Fixture boundary",
        required=False,
    )
    code_links = re.findall(r"\[[^]]+\]\(([^)#]+)\)", code_boundary)
    fixture_links = re.findall(r"\[[^]]+\]\(([^)#]+)\)", fixture_boundary)
    if not code_links:
        raise PairBlockGateError(f"code boundary is empty for {row.pair_block_id}")
    linked_paths = code_links + fixture_links
    if len(linked_paths) != len(set(linked_paths)):
        raise PairBlockGateError(
            f"proposal repeats a source path for {row.pair_block_id}"
        )
    source_paths = tuple(
        (contract_path.parent / linked_path).resolve() for linked_path in linked_paths
    )
    allowed_source_roots = _allowed_owner_roots(repository, profile)
    validated_sources: list[Path] = []
    for source_path in source_paths:
        if not any(source_path.is_relative_to(root) for root in allowed_source_roots):
            raise PairBlockGateError(
                f"proposed source is outside an allowed owner root: {source_path}"
            )
        if not source_path.is_file():
            raise PairBlockGateError(f"proposed source is missing: {source_path}")
        validated_sources.append(source_path)
    code_sources = validated_sources[: len(code_links)]
    if not any(path.name.startswith("test_") for path in code_sources):
        raise PairBlockGateError(f"code boundary lacks a test for {row.pair_block_id}")
    for source_path in code_sources:
        command_names = {source_path.as_posix()}
        command_names.update(
            source_path.relative_to(root).as_posix()
            for root in allowed_source_roots
            if source_path.is_relative_to(root)
        )
        if (
            source_path.name.startswith("test_")
            and not any(name in command for name in command_names)
        ):
            raise PairBlockGateError(
                f"focused check does not name observing test {source_path}"
            )
    return ProposalContract(
        path=contract_path,
        command=command,
        source_paths=source_paths,
    )


def _table_rows(text: str, header: str) -> list[list[str]]:
    """Return every contiguous data row following one exact table header."""

    lines = text.splitlines()
    try:
        header_index = lines.index(header)
    except ValueError as error:
        raise PairBlockGateError(f"table header is missing: {header}") from error
    rows: list[list[str]] = []
    for line in lines[header_index + 2 :]:
        if not line.startswith("|"):
            break
        rows.append(_split_row(line))
    return rows


def _normalized_state(value: str, profile: ChecklistProfile) -> str:
    """Translate one project lifecycle label into the global state vocabulary."""

    try:
        return profile.lifecycle.normalize(value)
    except ValueError as error:
        raise PairBlockGateError(str(error)) from error


def _phase_number(value: str, profile: ChecklistProfile) -> int:
    """Map one profile phase label to the integer expected by the global schema."""

    match = re.fullmatch(profile.phase_pattern, value)
    if match is None:
        raise PairBlockGateError(f"invalid checklist phase: {value}")
    return int(match.group(1)) * 26 + ord(match.group(2)) - ord("A")


def _requirement_records(
    checklist_text: str,
    profile: ChecklistProfile,
    dialect: MarkdownChecklistDialect,
    states: dict[str, str],
    evidence: dict[str, list[dict[str, str]]],
) -> list[dict[str, object]]:
    """Compile requirement rows and require their rendered states to agree."""

    rows = _table_rows(
        checklist_text,
        dialect.requirement_table_header,
    )
    phase_orders: dict[int, int] = {}
    records: list[dict[str, object]] = []
    for cells in rows:
        if len(cells) != 5:
            raise PairBlockGateError("requirement row must contain five cells")
        phase = _phase_number(cells[2], profile)
        order = phase_orders.get(phase, 0)
        phase_orders[phase] = order + 1
        dependencies = re.findall(r"`([^`]+)`", cells[3])
        if cells[3] == "None":
            dependencies = []
        requirement_id = cells[0].strip("`")
        if not profile.accepts_requirement_id(requirement_id):
            raise PairBlockGateError(f"invalid requirement ID: {requirement_id}")
        invalid_dependencies = [
            item for item in dependencies if not profile.accepts_requirement_id(item)
        ]
        if invalid_dependencies:
            raise PairBlockGateError(
                f"invalid requirement dependency IDs: {invalid_dependencies}"
            )
        try:
            expected_state = states[requirement_id]
        except KeyError as error:
            raise PairBlockGateError(
                f"requirement {requirement_id} has no mapped PairBlock"
            ) from error
        rendered_state = _normalized_state(cells[1], profile)
        if rendered_state != expected_state:
            raise PairBlockGateError(
                f"requirement {requirement_id} state must be {expected_state}"
            )
        records.append(
            {
                "requirement_id": requirement_id,
                "contract_id": profile.contract_id,
                "phase": phase,
                "order": order,
                "depends_on": dependencies,
                "state": expected_state,
                "gate": {"kind": "external", "target": cells[4]},
                "completion_evidence": evidence[requirement_id],
            }
        )
    return records


def _contract_requirement_map(
    contract_text: str,
    profile: ChecklistProfile,
    dialect: MarkdownChecklistDialect,
) -> tuple[list[str], dict[str, list[str]]]:
    """Compile requirement IDs and their PairBlock declaration links."""

    rows = _table_rows(
        contract_text,
        dialect.requirement_map_header,
    )
    requirement_ids: list[str] = []
    requirements_by_block: dict[str, list[str]] = {}
    for cells in rows:
        if len(cells) != 3:
            raise PairBlockGateError("requirement-map row must contain three cells")
        requirement_id = cells[0].strip("`")
        if not profile.accepts_requirement_id(requirement_id):
            raise PairBlockGateError(f"invalid requirement ID: {requirement_id}")
        requirement_ids.append(requirement_id)
        block_links = re.findall(
            r"`([^`]+)`\]\(#([a-z0-9_.-]+)\)",
            cells[2],
        )
        for block_id, anchor in block_links:
            if not profile.accepts_pair_block_id(block_id):
                raise PairBlockGateError(f"invalid PairBlock ID: {block_id}")
            if anchor != block_id.lower():
                raise PairBlockGateError(f"requirement-map link differs for {block_id}")
            requirements_by_block.setdefault(block_id, []).append(requirement_id)
    return requirement_ids, requirements_by_block


def _completion_evidence(
    repository: Path,
    checklist_path: Path,
    row: PairBlockRow,
    state: str,
    profile: ChecklistProfile,
) -> list[dict[str, str]]:
    """Load the final lifecycle receipt for one completed PairBlock."""

    if state != "complete":
        return []
    links = _RECEIPT_LINK.findall(row.gate)
    if len(links) != 1:
        raise PairBlockGateError(
            f"complete PairBlock {row.pair_block_id} needs one receipt link"
        )
    receipt_path = (checklist_path.parent / links[0]).resolve()
    if not receipt_path.is_relative_to(repository) or not receipt_path.is_file():
        raise PairBlockGateError(
            f"completion receipt is missing for {row.pair_block_id}"
        )
    receipt = _validate_completion_chain(
        repository,
        checklist_path,
        receipt_path,
        row.pair_block_id,
        profile,
    )
    revision = receipt.get("repository_head")
    if not isinstance(revision, str) or not revision:
        raise PairBlockGateError(
            f"completion receipt lacks repository_head for {row.pair_block_id}"
        )
    return [
        {
            "kind": "artifact",
            "target": receipt_path.relative_to(repository).as_posix(),
            "revision": revision,
        }
    ]


def _load_receipt(
    repository: Path, checklist_path: Path, link: str
) -> dict[str, object]:
    """Load one repository-owned receipt linked from the checklist directory."""

    path = (checklist_path.parent / link).resolve()
    if not path.is_relative_to(repository) or not path.is_file():
        raise PairBlockGateError(f"lifecycle receipt is missing: {link}")
    try:
        receipt = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PairBlockGateError(f"lifecycle receipt is invalid: {link}") from error
    if not isinstance(receipt, dict):
        raise PairBlockGateError(f"lifecycle receipt is not an object: {link}")
    return receipt


def _validate_completion_chain(
    repository: Path,
    checklist_path: Path,
    receipt_path: Path,
    pair_block_id: str,
    profile: ChecklistProfile,
) -> dict[str, object]:
    """Require the declared lifecycle receipts and passing proposal gate in order."""

    try:
        current = json.loads(receipt_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PairBlockGateError(
            f"completion receipt is invalid for {pair_block_id}"
        ) from error
    if not isinstance(current, dict):
        raise PairBlockGateError(
            f"completion receipt is not an object for {pair_block_id}"
        )
    final = current
    try:
        transitions = profile.lifecycle.completion_transitions(current.get("event"))
    except ValueError as error:
        raise PairBlockGateError(
            f"completion receipt chain differs for {pair_block_id}: {error}"
        ) from error
    requires_proposal_gate = transitions == profile.lifecycle.transitions
    reverse_transitions = tuple(reversed(transitions))
    for index, (event, status_before, status_after) in enumerate(reverse_transitions):
        if (
            current.get("pair_block_id") != pair_block_id
            or current.get("event") != event
            or current.get("result") != "applied"
            or current.get("status_before") != status_before
            or current.get("status_after") != status_after
        ):
            raise PairBlockGateError(
                f"completion receipt chain differs for {pair_block_id} at {event}"
            )
        evidence = current.get("evidence")
        if not isinstance(evidence, dict) or set(evidence) != {
            "kind",
            "target",
            "revision",
        }:
            raise PairBlockGateError(
                f"completion receipt lacks evidence for {pair_block_id} at {event}"
            )
        if (
            evidence["kind"] not in {"artifact", "command", "external", "test"}
            or not isinstance(evidence["target"], str)
            or not evidence["target"].strip()
            or not isinstance(evidence["revision"], str)
            or not evidence["revision"].strip()
        ):
            raise PairBlockGateError(
                f"completion receipt has invalid evidence for {pair_block_id} at {event}"
            )
        previous = current.get("previous_receipt")
        expects_previous = index < len(reverse_transitions) - 1 or requires_proposal_gate
        if expects_previous:
            if not isinstance(previous, str) or not previous:
                raise PairBlockGateError(
                    f"completion receipt chain ends before {event} for {pair_block_id}"
                )
            current = _load_receipt(repository, checklist_path, previous)
        elif previous is not None:
            raise PairBlockGateError(
                f"non-code receipt chain has an unexpected predecessor for {pair_block_id}"
            )
    if requires_proposal_gate and (
        current.get("pair_block_id") != pair_block_id
        or current.get("result") != "passed"
        or current.get("status_after") != profile.lifecycle.review_status
    ):
        raise PairBlockGateError(
            f"completion receipt chain lacks a passing proposal gate for {pair_block_id}"
        )
    return final


def _derive_requirement_records(
    requirement_ids: list[str],
    requirements_by_block: dict[str, list[str]],
    pair_blocks: list[dict[str, object]],
) -> tuple[dict[str, str], dict[str, list[dict[str, str]]]]:
    """Derive each requirement state and evidence from its mapped PairBlocks."""

    blocks_by_requirement: dict[str, list[dict[str, object]]] = {
        requirement_id: [] for requirement_id in requirement_ids
    }
    for block in pair_blocks:
        block_id = str(block["pair_block_id"])
        for requirement_id in requirements_by_block.get(block_id, []):
            blocks_by_requirement[requirement_id].append(block)

    states: dict[str, str] = {}
    evidence: dict[str, list[dict[str, str]]] = {}
    for requirement_id, blocks in blocks_by_requirement.items():
        if not blocks:
            raise PairBlockGateError(
                f"requirement {requirement_id} has no mapped PairBlock"
            )
        block_states = [str(block["state"]) for block in blocks]
        if all(state == "complete" for state in block_states):
            state = "complete"
        elif all(state == "planned" for state in block_states):
            state = "planned"
        elif all(state == "deferred" for state in block_states):
            state = "deferred"
        else:
            state = "in_progress"
        states[requirement_id] = state
        records: list[dict[str, str]] = []
        if state == "complete":
            for block in blocks:
                records.extend(block["completion_evidence"])  # type: ignore[arg-type]
        evidence[requirement_id] = records
    return states, evidence


def _pair_block_placement(
    checklist_text: str,
    pair_block_id: str,
    contract_path: Path,
) -> PairBlockPlacement:
    """Resolve one standard PairBlock marker to its checkbox and section."""

    marker = f"<!-- pair-block: {pair_block_id} -->"
    lines = checklist_text.splitlines()
    matches = [index for index, line in enumerate(lines) if marker in line]
    if len(matches) != 1:
        raise PairBlockGateError(f"{pair_block_id} must map to one checklist checkbox")
    contract_marker = (
        f"<!-- pair-block-contract: {pair_block_id} "
        f"contract={contract_path.as_posix()} -->"
    )
    marker_index = matches[0]
    checkbox_line = -1
    checkbox_match: re.Match[str] | None = None
    for candidate_index in range(marker_index - 1, -1, -1):
        if lines[candidate_index].startswith("## "):
            break
        candidate = _CHECKBOX.match(lines[candidate_index])
        if candidate is not None:
            checkbox_line = candidate_index
            checkbox_match = candidate
            break
    if checkbox_match is None:
        raise PairBlockGateError(
            f"{pair_block_id} marker is not preceded by a checkbox"
        )
    following_lines = [
        line.strip() for line in lines[marker_index + 1 : marker_index + 3]
    ]
    if contract_marker not in following_lines:
        raise PairBlockGateError(f"{pair_block_id} lacks its standard contract marker")
    for line in reversed(lines[:marker_index]):
        if line.startswith("## "):
            return PairBlockPlacement(
                section=line.removeprefix("## "),
                checkbox_line=checkbox_line,
                checked=checkbox_match.group(1).lower() == "x",
            )
    raise PairBlockGateError(f"checklist section is missing for {pair_block_id}")


def _validate_block_inventory(
    contract_text: str,
    rows: dict[str, PairBlockRow],
    profile: ChecklistProfile,
) -> None:
    """Require the contract declarations and status rows to name the same blocks."""

    headings = re.findall(
        r"(?m)^#### ([A-Za-z0-9_.-]+)$",
        contract_text,
    )
    declared = set(headings)
    invalid = [item for item in declared if not profile.accepts_pair_block_id(item)]
    if invalid:
        raise PairBlockGateError(f"invalid declared PairBlock IDs: {invalid}")
    if declared != set(rows):
        raise PairBlockGateError(
            "PairBlock inventory differs: "
            f"missing_status={sorted(declared - set(rows))}, "
            f"unknown_status={sorted(set(rows) - declared)}"
        )


def _release_ready_rows(
    checklist_text: str,
    profile: ChecklistProfile,
    dialect: MarkdownChecklistDialect,
) -> str:
    """Move dependency-ready waiting rows into drafting."""

    rows = parse_pair_block_rows(checklist_text, profile, dialect)
    rendered = checklist_text
    for row in rows.values():
        if not row.status.startswith(profile.lifecycle.waiting_prefix):
            continue
        if all(
            rows[dependency].status in profile.lifecycle.resolved_dependency_states
            for dependency in row.dependencies
        ):
            rendered = _replace_status_row(
                rendered,
                pair_block_id=row.pair_block_id,
                gate=row.gate,
                status=profile.lifecycle.drafting_status,
            )
    return rendered


def _render_derived_states(
    repository: Path,
    checklist_text: str,
    profile: ChecklistProfile,
    dialect: MarkdownChecklistDialect,
) -> str:
    """Render readiness, requirement states, and contract state from blocks."""

    rendered = _release_ready_rows(checklist_text, profile, dialect)
    rows = parse_pair_block_rows(rendered, profile, dialect)
    contract_text = (repository / profile.contract_path).read_text(encoding="utf-8")
    requirement_ids, requirements_by_block = _contract_requirement_map(
        contract_text,
        profile,
        dialect,
    )
    pair_blocks = _pair_block_records(
        repository,
        rendered,
        rows,
        requirements_by_block,
        profile,
    )
    requirement_states, _ = _derive_requirement_records(
        requirement_ids,
        requirements_by_block,
        pair_blocks,
    )
    display_states = {
        requirement_id: _display_state(state)
        for requirement_id, state in requirement_states.items()
    }
    rendered = _replace_requirement_states(rendered, display_states, dialect)
    contract_state = _contract_state(
        list(requirement_states.values())
        + [str(block["state"]) for block in pair_blocks]
    )
    return _replace_contract_state(
        rendered,
        _display_state(contract_state),
        dialect,
    )


def render_transition(
    repository: Path,
    checklist_text: str,
    row: PairBlockRow,
    *,
    receipt_path: str,
    status: str,
    profile: ChecklistProfile,
    dialect: MarkdownChecklistDialect,
) -> bytes:
    """Render one lifecycle receipt and all states derived from its block."""

    proposed_code = None
    if status in profile.lifecycle.resolved_dependency_states:
        proposed_code = _active_code_links(row, dialect)
    rendered = _replace_status_row(
        checklist_text,
        pair_block_id=row.pair_block_id,
        gate=f"Lifecycle ([receipt]({receipt_path}))",
        status=status,
        proposed_code=proposed_code,
    )
    placement = _pair_block_placement(
        rendered,
        row.pair_block_id,
        profile.contract_path,
    )
    rendered = _replace_checkbox(
        rendered,
        placement,
        checked=status == profile.lifecycle.complete_status,
    )
    return _render_derived_states(
        repository,
        rendered,
        profile,
        dialect,
    ).encode("utf-8")


def _pair_block_records(
    repository: Path,
    checklist_text: str,
    rows: dict[str, PairBlockRow],
    requirements_by_block: dict[str, list[str]],
    profile: ChecklistProfile,
) -> list[dict[str, object]]:
    """Compile PairBlock rows, checkboxes, placements, and final receipts."""

    checklist_path = repository / profile.checklist_path
    records: list[dict[str, object]] = []
    for row in rows.values():
        state = _normalized_state(row.status, profile)
        placement = _pair_block_placement(
            checklist_text,
            row.pair_block_id,
            profile.contract_path,
        )
        if placement.checked != (state == "complete"):
            expected = "checked" if state == "complete" else "unchecked"
            raise PairBlockGateError(f"{row.pair_block_id} checkbox must be {expected}")
        records.append(
            {
                "pair_block_id": row.pair_block_id,
                "contract_id": profile.contract_id,
                "section": placement.section,
                "requirement_ids": requirements_by_block.get(
                    row.pair_block_id,
                    [],
                ),
                "state": state,
                "gate": {"kind": "external", "target": row.gate},
                "completion_evidence": _completion_evidence(
                    repository,
                    checklist_path,
                    row,
                    state,
                    profile,
                ),
            }
        )
    return records


def compile_normalized_manifest(
    repository: Path,
    checklist_text: str,
    rows: dict[str, PairBlockRow],
    profile: ChecklistProfile,
    dialect: MarkdownChecklistDialect,
) -> dict[str, object]:
    """Compile RICO-owned fields into schema version 2 of the global manifest."""

    contract_path = repository / profile.contract_path
    contract_text = contract_path.read_text(encoding="utf-8")
    _validate_block_inventory(contract_text, rows, profile)
    requirement_ids, requirements_by_block = _contract_requirement_map(
        contract_text,
        profile,
        dialect,
    )
    pair_blocks = _pair_block_records(
        repository,
        checklist_text,
        rows,
        requirements_by_block,
        profile,
    )
    requirement_states, requirement_evidence = _derive_requirement_records(
        requirement_ids,
        requirements_by_block,
        pair_blocks,
    )
    requirements = _requirement_records(
        checklist_text,
        profile,
        dialect,
        requirement_states,
        requirement_evidence,
    )
    states = [str(record["state"]) for record in requirements + pair_blocks]
    contract_state = _contract_state(states)
    if _rendered_contract_state(checklist_text, profile, dialect) != contract_state:
        raise PairBlockGateError(f"contract state must be {contract_state}")
    return {
        "schema_version": 2,
        "checklist_id": profile.checklist_id,
        "project": profile.project_name,
        "revision": "working-tree",
        "contracts": [
            {
                "contract_id": profile.contract_id,
                "path": contract_path.relative_to(repository).as_posix(),
                "revision": "working-tree",
                "sha256": sha256_file(contract_path),
                "requirement_ids": requirement_ids,
                "state": contract_state,
            }
        ],
        "requirements": requirements,
        "pair_blocks": pair_blocks,
    }


def validate_normalized_manifest(
    repository: Path,
    manifest: dict[str, object],
    validator_path: Path,
) -> None:
    """Invoke the existing global validator on one compiled temporary manifest."""

    if not validator_path.is_file():
        raise PairBlockGateError(
            f"master-checklist validator is missing: {validator_path}"
        )
    with tempfile.TemporaryDirectory() as temporary_directory:
        manifest_path = Path(temporary_directory) / "checklist.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(validator_path),
                str(manifest_path),
                "--root",
                str(repository),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise PairBlockGateError(f"master-checklist validation failed: {detail}")


def validate_traceability(
    repository: Path,
    *,
    validator_path: Path = DEFAULT_MASTER_CHECKLIST_VALIDATOR,
    profile: ChecklistProfile,
    dialect: MarkdownChecklistDialect,
) -> tuple[dict[str, PairBlockRow], dict[str, object]]:
    """Validate RICO-owned links, then delegate normalized contract semantics."""

    repository = repository.resolve()
    checklist_path = repository / profile.checklist_path
    checklist_text = checklist_path.read_text(encoding="utf-8")
    rows = parse_pair_block_rows(checklist_text, profile, dialect)
    for row in rows.values():
        validate_declaration(repository, checklist_path, row)
        if (
            row.status in profile.lifecycle.proposal_gate_states
            and dialect.proposed_code_link_prefix in row.proposed_code
        ):
            load_proposal_contract(repository, checklist_path, row, profile)
    validate_document_fragments(repository, checklist_path, profile)
    validate_document_fragments(
        repository,
        repository / profile.contract_path,
        profile,
    )
    manifest = compile_normalized_manifest(
        repository,
        checklist_text,
        rows,
        profile,
        dialect,
    )
    validate_normalized_manifest(repository, manifest, validator_path.resolve())
    return rows, manifest


MANTRA_PHASE0_DIALECT = MarkdownChecklistDialect(
    pair_block_table_header=(
        "| PairBlock | Proposal gate | Resolution status | Depends on | "
        "Contract block | Proposed code |"
    ),
    requirement_table_header="| Requirement | State | Phase | Depends on | Gate |",
    requirement_map_header=("| ID | Contract boundary | Blocks |"),
    contract_table_header=(
        "| Work unit | Current state | Owning phase | Completion evidence |"
    ),
    contract_link_prefix="[Phase 0 contract]",
    proposed_code_link_prefix="[Source and tests]",
)

MANTRA_PHASE0_ADAPTER = MarkdownChecklistAdapter(
    profile=MANTRA_PHASE0_PROFILE,
    dialect=MANTRA_PHASE0_DIALECT,
)
