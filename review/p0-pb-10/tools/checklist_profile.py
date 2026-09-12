"""Compile RICO's Markdown checklist into the established normalized manifest."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .execution_identity import sha256_file
from .profile import MANTRA_PHASE0_PROFILE, ChecklistProfile

DEFAULT_MASTER_CHECKLIST_VALIDATOR = (
    Path.home() / ".agents/scripts/validate-master-checklist.py"
)
_ROW_ID = re.compile(r'^<a id="status-([a-z0-9_.-]+)"></a>`([^`]+)`$')
_LINK = re.compile(r"^\[[^]]+\]\(([^)#]+)(?:#([^)]+))?\)$")


class PairBlockGateError(RuntimeError):
    """Report a RICO profile, validation, or gate-transition violation."""


@dataclass(frozen=True, slots=True)
class PairBlockRow:
    """Represent one authoritative PairBlock lifecycle row in the checklist."""

    line_index: int
    pair_block_id: str
    gate: str
    status: str
    dependencies: tuple[str, ...]
    declaration: str
    proposed_code: str


@dataclass(frozen=True, slots=True)
class ProposalContract:
    """Represent one proposed code boundary and its contract-declared command."""

    path: Path
    command: str
    source_paths: tuple[Path, ...]


def _split_row(line: str) -> list[str]:
    """Split one pipe-delimited Markdown table row into stripped cells."""

    return [cell.strip() for cell in line.strip().strip("|").split("|")]


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
    profile: ChecklistProfile = MANTRA_PHASE0_PROFILE,
) -> dict[str, PairBlockRow]:
    """Parse the status table and reject duplicate or cyclic PairBlocks."""

    lines = checklist_text.splitlines()
    try:
        header_index = lines.index(profile.pair_block_table_header)
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
        pair_block_id = match.group(2)
        if not profile.accepts_pair_block_id(pair_block_id):
            raise PairBlockGateError(f"invalid PairBlock ID: {pair_block_id}")
        if match.group(1) != pair_block_id.lower():
            raise PairBlockGateError(f"status anchor differs for {pair_block_id}")
        if pair_block_id in rows:
            raise PairBlockGateError(f"duplicate PairBlock row: {pair_block_id}")
        rows[pair_block_id] = PairBlockRow(
            line_index=line_index,
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


def _proposal_section(text: str, pair_block_id: str) -> str:
    """Return one PairBlock's complete proposed-code section."""

    marker = f"#### `{pair_block_id}` proposed code"
    start = text.find(marker)
    if start < 0:
        raise PairBlockGateError(
            f"proposed-code section is missing for {pair_block_id}"
        )
    remainder = text[start + len(marker) :]
    next_heading = re.search(r"(?m)^#{3,4} ", remainder)
    end = len(text) if next_heading is None else start + len(marker) + next_heading.start()
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


def _ownership_row(contract_text: str, anchor: str, pair_block_id: str) -> list[str]:
    """Return the unique ownership row for one contract declaration."""

    marker = f'<a id="{anchor}"></a>'
    matches = [
        line
        for line in contract_text.splitlines()
        if marker in line and line.startswith("|")
    ]
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
        raise PairBlockGateError(f"declaration anchor is missing for {row.pair_block_id}")
    _ownership_row(
        contract_path.read_text(encoding="utf-8"),
        anchor,
        row.pair_block_id,
    )


def load_proposal_contract(
    repository: Path,
    checklist_path: Path,
    row: PairBlockRow,
    profile: ChecklistProfile = MANTRA_PHASE0_PROFILE,
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
        raise PairBlockGateError(f"declaration anchor is missing for {row.pair_block_id}")
    _ownership_row(contract_text, declaration_anchor, row.pair_block_id)

    proposed_path, proposed_fragment = _resolve_link(
        checklist_path.parent, row.proposed_code
    )
    if proposed_path != contract_path:
        raise PairBlockGateError(
            f"proposed-code link leaves the governing contract for {row.pair_block_id}"
        )
    expected_fragment = f"{row.pair_block_id.lower()}-proposed-code"
    if proposed_fragment != expected_fragment:
        raise PairBlockGateError(f"proposed-code link differs for {row.pair_block_id}")

    proposal = _proposal_section(contract_text, row.pair_block_id)
    if f"#status-{row.pair_block_id.lower()}" not in proposal:
        raise PairBlockGateError(
            f"proposed-code section lacks the checklist status link for {row.pair_block_id}"
        )
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
        raise PairBlockGateError(f"proposal repeats a source path for {row.pair_block_id}")
    source_paths = tuple(
        (contract_path.parent / linked_path).resolve() for linked_path in linked_paths
    )
    relative_sources: list[Path] = []
    for source_path in source_paths:
        if not source_path.is_relative_to(repository):
            raise PairBlockGateError("proposed source path escapes the repository")
        if not source_path.is_file():
            raise PairBlockGateError(f"proposed source is missing: {source_path}")
        relative_sources.append(source_path.relative_to(repository))
    code_sources = relative_sources[: len(code_links)]
    if not any(path.name.startswith("test_") for path in code_sources):
        raise PairBlockGateError(f"code boundary lacks a test for {row.pair_block_id}")
    for relative_source_path in code_sources:
        relative_source = relative_source_path.as_posix()
        if relative_source_path.name.startswith("test_") and relative_source not in command:
            raise PairBlockGateError(
                f"focused check does not name observing test {relative_source}"
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
) -> list[dict[str, object]]:
    """Compile requirement-assignment rows without reproducing global validation."""

    rows = _table_rows(
        checklist_text,
        profile.requirement_table_header,
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
            item
            for item in dependencies
            if not profile.accepts_requirement_id(item)
        ]
        if invalid_dependencies:
            raise PairBlockGateError(
                f"invalid requirement dependency IDs: {invalid_dependencies}"
            )
        records.append(
            {
                "requirement_id": requirement_id,
                "contract_id": profile.contract_id,
                "phase": phase,
                "order": order,
                "depends_on": dependencies,
                "state": _normalized_state(cells[1], profile),
                "gate": {"kind": "external", "target": cells[4]},
                "completion_evidence": [],
            }
        )
    return records


def _contract_requirement_map(
    contract_text: str,
    profile: ChecklistProfile,
) -> tuple[list[str], dict[str, list[str]]]:
    """Compile requirement IDs and their PairBlock declaration links."""

    rows = _table_rows(
        contract_text,
        profile.requirement_map_header,
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
            if anchor != f"{block_id.lower()}-declaration":
                raise PairBlockGateError(f"requirement-map link differs for {block_id}")
            requirements_by_block.setdefault(block_id, []).append(requirement_id)
    return requirement_ids, requirements_by_block


def _pair_block_section(checklist_text: str, pair_block_id: str) -> str:
    """Resolve one PairBlock marker to its unique checklist section."""

    marker = f"<!-- pair-block: {pair_block_id} -->"
    lines = checklist_text.splitlines()
    matches = [index for index, line in enumerate(lines) if marker in line]
    if len(matches) != 1:
        raise PairBlockGateError(
            f"{pair_block_id} must map to one checklist checkbox"
        )
    for line in reversed(lines[: matches[0]]):
        if line.startswith("## "):
            return line.removeprefix("## ")
    raise PairBlockGateError(f"checklist section is missing for {pair_block_id}")


def _validate_block_inventory(
    contract_text: str,
    rows: dict[str, PairBlockRow],
    profile: ChecklistProfile,
) -> None:
    """Require the contract declarations and status rows to name the same blocks."""

    anchors = re.findall(
        r'<a id="([a-z0-9_.-]+)-declaration"></a>',
        contract_text,
    )
    declared = {block_id.upper() for block_id in anchors}
    invalid = [item for item in declared if not profile.accepts_pair_block_id(item)]
    if invalid:
        raise PairBlockGateError(f"invalid declared PairBlock IDs: {invalid}")
    if declared != set(rows):
        raise PairBlockGateError(
            "PairBlock inventory differs: "
            f"missing_status={sorted(declared - set(rows))}, "
            f"unknown_status={sorted(set(rows) - declared)}"
        )


def compile_normalized_manifest(
    repository: Path,
    checklist_text: str,
    rows: dict[str, PairBlockRow],
    profile: ChecklistProfile = MANTRA_PHASE0_PROFILE,
) -> dict[str, object]:
    """Compile RICO-owned fields into schema version 2 of the global manifest."""

    contract_path = repository / profile.contract_path
    contract_text = contract_path.read_text(encoding="utf-8")
    _validate_block_inventory(contract_text, rows, profile)
    requirement_ids, requirements_by_block = _contract_requirement_map(
        contract_text,
        profile,
    )
    requirements = _requirement_records(checklist_text, profile)
    pair_blocks = [
        {
            "pair_block_id": row.pair_block_id,
            "contract_id": profile.contract_id,
            "section": _pair_block_section(checklist_text, row.pair_block_id),
            "requirement_ids": requirements_by_block.get(row.pair_block_id, []),
            "state": _normalized_state(row.status, profile),
            "gate": {"kind": "external", "target": row.gate},
            "completion_evidence": [],
        }
        for row in rows.values()
    ]
    states = [record["state"] for record in requirements + pair_blocks]
    if states and all(state == "complete" for state in states):
        contract_state = "complete"
    elif states and all(state == "planned" for state in states):
        contract_state = "planned"
    elif states and all(state == "deferred" for state in states):
        contract_state = "deferred"
    else:
        contract_state = "in_progress"
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
    profile: ChecklistProfile = MANTRA_PHASE0_PROFILE,
) -> tuple[dict[str, PairBlockRow], dict[str, object]]:
    """Validate RICO-owned links, then delegate normalized contract semantics."""

    repository = repository.resolve()
    checklist_path = repository / profile.checklist_path
    checklist_text = checklist_path.read_text(encoding="utf-8")
    rows = parse_pair_block_rows(checklist_text, profile)
    for row in rows.values():
        validate_declaration(repository, checklist_path, row)
        if row.proposed_code.startswith(profile.proposed_code_link_prefix):
            load_proposal_contract(repository, checklist_path, row, profile)
    manifest = compile_normalized_manifest(
        repository,
        checklist_text,
        rows,
        profile,
    )
    validate_normalized_manifest(repository, manifest, validator_path.resolve())
    return rows, manifest
