# PairBlock Lifecycle Evidence

The proposed architecture is worth implementing. It preserves the current
receipt-derived status system but replaces the weak generic evidence triple
with event-specific records that the controller can validate semantically.

This is not a move to a general event-sourcing framework. It is a targeted
repair to the three native PairBlock transitions:

```text
Review   --approve-->   Approved
Approved --accept---->  Applied
Applied  --register-->  Complete
```

## Fixed comparison

**User goal:** Complete a PairBlock only after the user approves it, its
implementation passes review, and VIPER registers the accepted implementation.

**Concrete case:** `P0-PB-10E`.

**Expected result:** `P0-PB-10E` reaches `Complete`, and every transition
points to evidence appropriate to that transition.

**Decision under review:** Replace the generic `EvidenceRef` used by every
lifecycle event with a discriminated union of event-specific evidence
references.

## How the current system works

### 1. The declaration defines the work

The structured declaration assigns requirements, dependencies, source files,
tests, and a gate to the PairBlock.

For `P0-PB-10E`, that definition begins in
[the declaration manifest](mantra-rebuild.declarations.toml):

```toml
[[pair_blocks]]
id = "P0-PB-10E"
requirement_ids = ["P0-REQ-29"]
depends_on = ["P0-PB-10D"]
repository = "rico"

source_paths = [
  "tools/pairblock_status/execution_identity.py",
  "tools/pairblock_status/receipt_validation.py",
  "tools/pairblock_status/pairblock_controller.py",
]

test_paths = [
  "tests/pairblock_status/test_receipt_integrity.py",
]
```

This part is sound. Markdown is a rendered human view; the TOML declaration
and receipts own the state.

### 2. The gate produces `Review`

The controller runs the declared command and saves a `GateReceipt`. That
receipt contains the command, output, repository identities, source identities,
declaration digest, and resulting status.

Conceptually:

```text
P0-PB-10E declaration
        |
        v
execute declared gate
        |
        v
GateReceipt(result="passed")
        |
        v
status = Review
```

The actual receipt is
[20260913T061228.145467Z.json](../../evidence/pairblock-gates/p0-pb-10e/20260913T061228.145467Z.json).

This receipt system should remain separate because a test execution contains
facts that approval and registration do not: process output, exit code,
executed command, and before/after execution identities.

### 3. Every later transition receives the same generic type

The current controller defines this in
[pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py):

```python
@dataclass(frozen=True, slots=True)
class EvidenceRef:
    kind: EvidenceKind
    target: str
    revision: str
```

`EvidenceKind` comes from
[profile.py](../../tools/pairblock_status/profile.py):

```python
type EvidenceKind = Literal[
    "artifact",
    "command",
    "external",
    "test",
]
```

The lifecycle profile associates events with these broad categories:

```python
transitions=(
    ("approve", "Review", "Approved"),
    ("accept", "Approved", "Applied"),
    ("register", "Applied", "Complete"),
),
evidence_rules=(
    LifecycleEvidenceRule("approve", "external"),
    LifecycleEvidenceRule("accept", "artifact"),
    LifecycleEvidenceRule("register", "artifact"),
),
```

Therefore:

```text
approve  requires external
accept   requires artifact
register requires artifact
```

The system knows that `accept` and `register` require files. It does not know
that the first file must be an implementation-review receipt and the second
must be a VIPER-registration receipt.

### 4. The CLI exposes the generic model directly

The current command accepts a category, arbitrary target string, and arbitrary
revision string:

```bash
python -m tools.pairblock_status.pairblock_controller \
  advance P0-PB-10E accept \
  --evidence-kind artifact \
  --evidence-target evidence/pairblock-reviews/p0-pb-10e/REVIEW.json \
  --evidence-revision SHA256
```

The generic CLI is defined in
[pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py).

The operator must already know:

- which category belongs to the event;
- which artifact schema belongs to the event;
- how to calculate its digest;
- whether the artifact actually describes this PairBlock; and
- whether it names the accepted implementation commit.

The controller should own those decisions.

### 5. The validator verifies bytes, not meaning

The current check in
[pairblock_controller.py](../../tools/pairblock_status/pairblock_controller.py)
is effectively:

```python
required_kind = profile.lifecycle.required_evidence_kind(event)

if evidence.kind != required_kind:
    raise PairBlockGateError(...)

if required_kind != "artifact":
    return

artifact = repository / evidence.target

if not artifact.is_file():
    raise PairBlockGateError(...)

if sha256_file(artifact) != evidence.revision:
    raise PairBlockGateError(...)
```

The persisted-receipt validator repeats the same boundary in
[receipt_validation.py](../../tools/pairblock_status/receipt_validation.py):

```python
if kind != expected_kind:
    raise ...

if kind == "artifact":
    require_repository_relative_path(target)
    require_existing_file(target)
    require_sha256(target, revision)
```

This establishes three useful facts:

1. the event received the configured broad evidence category;
2. the referenced file exists inside RICO; and
3. its current bytes match the saved SHA-256.

It does not establish:

```text
accept artifact   -> implementation-review schema
review receipt    -> this PairBlock
review result     -> accepted implementation commit

register artifact -> VIPER-registration schema
VIPER record      -> this PairBlock
VIPER record      -> accepted implementation commit
```

## The exact unsupported case

The existing test
[test_lifecycle_evidence.py](../../tests/pairblock_status/test_lifecycle_evidence.py)
proves that `accept` rejects `external` evidence and `register` rejects
`command` evidence.

It does not test this:

```bash
printf '{"unrelated": true}\n' > evidence/unrelated.json
DIGEST="$(shasum -a 256 evidence/unrelated.json | cut -d ' ' -f 1)"

python -m tools.pairblock_status.pairblock_controller \
  advance P0-PB-10E accept \
  --evidence-kind artifact \
  --evidence-target evidence/unrelated.json \
  --evidence-revision "$DIGEST"
```

Assuming the PairBlock is in `Approved`, that unrelated JSON satisfies the
current evidence check:

```text
kind == "artifact"       yes
repository-relative      yes
file exists              yes
SHA-256 matches          yes
review receipt           unchecked
PairBlock identity       unchecked
review verdict           unchecked
implementation commit    unchecked
```

Afterward, the same review receipt could be supplied to `register`. It is an
artifact with valid bytes, so its role remains unchecked.

That is the first missing connector.

## Contract-gap specification

**Contract status:** Approved for staged implementation

**Checklist variant:** Integrated with
[the MANTRA rebuild checklist](../checklists/mantra-rebuild.md)

### Required claim

`P0-REQ-38`:

> A native PairBlock lifecycle transition advances only when its evidence has
> the event-specific type and the referenced record verifies the PairBlock,
> accepted declaration, implementation commit, and required result for that
> event.

Formally:

```math
\operatorname{Advance}(b,e,r,s)=s'
\iff
\operatorname{Allowed}(s,e,s')
\land
\operatorname{Verify}_{e}(r,b,h,d)
```

Where:

- `b` is the PairBlock.
- `e` is `approve`, `accept`, or `register`.
- `r` is the event-specific evidence reference.
- `s` and `s'` are the previous and resulting statuses.
- `h` is the implementation repository commit.
- `d` is the accepted declaration identity.
- `Verify_e` is the verifier selected by the event's evidence type.

The practical consequence is that an unrelated file with a correct SHA-256
cannot advance a PairBlock.

### Guarantee boundary

This supports an **execution and custody** claim:

- the controller received the right kind of event record;
- the referenced bytes are immutable;
- the record describes the same PairBlock and implementation; and
- the record reports the result required by that event.

For user approval, the local controller can bind a supplied Codex message ID
to the exact PairBlock and declaration fingerprint. It cannot independently
prove the human meaning of that message unless Codex exposes a signed or
retrievable message record. The act of invoking the approval transition
remains the authorization boundary.

## Proposed event-specific model

The broad `EvidenceKind` should remain available for gates and the normalized
global checklist. It should stop serving as the authoritative
native-lifecycle schema.

A new module such as `tools/pairblock_status/lifecycle_evidence.py` would own
these types:

```python
from dataclasses import dataclass
from typing import Literal, TypeAlias


@dataclass(frozen=True, slots=True)
class RepositoryRecordRef:
    path: RepoRelativePath
    sha256: Sha256


@dataclass(frozen=True, slots=True)
class UserApprovalRef:
    kind: Literal["user_approval"]
    task_id: CodexTaskId
    message_id: CodexMessageId


@dataclass(frozen=True, slots=True)
class ImplementationReviewRef:
    kind: Literal["implementation_review"]
    receipt: RepositoryRecordRef


@dataclass(frozen=True, slots=True)
class ViperRegistrationRef:
    kind: Literal["viper_registration"]
    receipt: RepositoryRecordRef


LifecycleEvidenceRef: TypeAlias = (
    UserApprovalRef
    | ImplementationReviewRef
    | ViperRegistrationRef
)
```

The transition itself then carries the only legal evidence type:

```python
@dataclass(frozen=True, slots=True)
class ApprovalTransition:
    event: Literal["approve"]
    evidence: UserApprovalRef


@dataclass(frozen=True, slots=True)
class AcceptanceTransition:
    event: Literal["accept"]
    evidence: ImplementationReviewRef


@dataclass(frozen=True, slots=True)
class RegistrationTransition:
    event: Literal["register"]
    evidence: ViperRegistrationRef


NativeLifecycleTransition: TypeAlias = (
    ApprovalTransition
    | AcceptanceTransition
    | RegistrationTransition
)
```

This makes these combinations structurally invalid:

```python
ApprovalTransition(
    event="approve",
    evidence=ImplementationReviewRef(...),
)

RegistrationTransition(
    event="register",
    evidence=ImplementationReviewRef(...),
)
```

The lifecycle receipt should persist the transition as one discriminated
object:

```python
@dataclass(frozen=True, slots=True)
class LifecycleReceipt:
    schema_version: Literal[4]
    pair_block_id: PairBlockId
    transition: NativeLifecycleTransition
    status_before: LifecycleStatus
    status_after: LifecycleStatus
    declaration_sha256: Sha256
    pair_block_fingerprint: Sha256
    declaration_repository_head: GitCommit
    implementation_repository_head: GitCommit
    previous_receipt: RepoRelativePath
```

## Serialized form: before and after

### Current `accept`

```json
{
  "schema_version": 3,
  "pair_block_id": "P0-PB-10E",
  "event": "accept",
  "status_before": "Approved",
  "status_after": "Applied",
  "evidence": {
    "kind": "artifact",
    "target": "evidence/pairblock-reviews/p0-pb-10e/1ea7403b.json",
    "revision": "94ce3da8..."
  }
}
```

### Proposed `accept`

```json
{
  "schema_version": 4,
  "pair_block_id": "P0-PB-10E",
  "status_before": "Approved",
  "status_after": "Applied",
  "transition": {
    "event": "accept",
    "evidence": {
      "kind": "implementation_review",
      "receipt": {
        "path": "evidence/pairblock-reviews/p0-pb-10e/1ea7403b.json",
        "sha256": "94ce3da8..."
      }
    }
  }
}
```

### Proposed `register`

```json
{
  "schema_version": 4,
  "pair_block_id": "P0-PB-10E",
  "status_before": "Applied",
  "status_after": "Complete",
  "transition": {
    "event": "register",
    "evidence": {
      "kind": "viper_registration",
      "receipt": {
        "path": "evidence/viper-registrations/p0-pb-10e.json",
        "sha256": "4f1831f9..."
      }
    }
  }
}
```

The strings still exist on disk because JSON requires strings. Their meaning
now comes from their containing type and discriminator.

## Proposed verification

The controller would parse the discriminator and delegate to the corresponding
verifier:

```python
def verify_transition(
    *,
    block: PairBlock,
    transition: NativeLifecycleTransition,
    implementation_head: GitCommit,
) -> None:
    match transition:
        case ApprovalTransition(evidence=approval):
            verify_user_approval(
                approval,
                pair_block_id=block.id,
                pair_block_fingerprint=block.fingerprint,
            )

        case AcceptanceTransition(evidence=review_ref):
            review = load_implementation_review(review_ref.receipt)

            require_equal(review.pair_block_id, block.id)
            require_equal(review.requirement_ids, block.requirement_ids)
            require_equal(review.result_commit, implementation_head)
            require_equal(review.verdict, "Approve")

        case RegistrationTransition(evidence=registration_ref):
            registration = load_viper_registration(
                registration_ref.receipt
            )

            require_equal(registration.pair_block_id, block.id)
            require_equal(
                registration.implementation_commit,
                implementation_head,
            )
            require_true(registration.verification_passed)
```

The implementation-review receipt already contains the necessary fields:
`pair_block_id`, `requirement_ids`, `result_commit`, and `verdict`. The missing
piece is a programmatically generated PairBlock-specific VIPER registration
record. The current aggregate Phase 0 terminal receipt reports a successful
evidence bundle, but it does not identify one PairBlock and its accepted
implementation commit.

That record should look approximately like this:

```python
@dataclass(frozen=True, slots=True)
class PairBlockViperRegistration:
    schema_version: Literal[1]
    pair_block_id: PairBlockId
    implementation_repository: RepositoryIdentity
    implementation_commit: GitCommit
    viper_run: ViperRunRef
    verification_receipt: RepositoryRecordRef
    verification_passed: Literal[True]
```

A dedicated command should generate it from the declaration, current
implementation repository, and verified VIPER run. An operator should not
hand-author this JSON.

## Proposed CLI

The CLI should compute file digests and construct the correct type:

```bash
pairblock approve P0-PB-10E \
  --task-id TASK_ID \
  --message-id MESSAGE_ID

pairblock accept P0-PB-10E \
  --review-receipt evidence/pairblock-reviews/p0-pb-10e/REVIEW.json

pairblock register P0-PB-10E \
  --viper-receipt evidence/viper-registrations/p0-pb-10e.json
```

The generic command disappears for native executable blocks:

```bash
# Removed from the native workflow
pairblock advance BLOCK EVENT \
  --evidence-kind KIND \
  --evidence-target TARGET \
  --evidence-revision REVISION
```

The controller now chooses the type. The user supplies the record that exists.

## Exact delta

| Surface | Current | Proposed | Effect |
|---|---|---|---|
| Gate evidence | `GateReceipt` | `GateReceipt` | Preserved |
| Lifecycle evidence | One `EvidenceRef` | Three event-specific references | Invalid event/evidence combinations become unrepresentable |
| Policy | Event to broad category | Event encoded by transition type | Removes duplicated category mapping |
| CLI | Generic event and three evidence arguments | One command per event | Fewer manual decisions |
| Stored receipt | Separate `event` and generic `evidence` | Discriminated `transition` | Parser selects one exact schema |
| `accept` check | File exists and digest matches | Review schema, PairBlock, requirements, verdict, and commit match | Strengthened |
| `register` check | File exists and digest matches | VIPER registration schema, PairBlock, commit, and verification result match | Strengthened |
| Checklist projection | Generic completion evidence | Projection derived from typed record | Global format remains compatible |
| Historical receipts | Schema versions 1–3 | Read-only compatibility path | No receipt rewriting |
| New receipts | Schema version 3 | Schema version 4 | Explicit migration boundary |

## Propagation and PairBlocks

### `P0-PB-10K` — typed evidence and exact parsers

Owns:

- `LifecycleEvidenceRef`;
- the three evidence-reference types;
- the three transition types;
- exact JSON parsing; and
- canonical serialization.

Production targets:

```text
tools/pairblock_status/lifecycle_evidence.py
tests/pairblock_status/test_lifecycle_evidence_records.py
requirements.txt
```

The [source-backed plan](../../plans/pairblock-lifecycle-evidence/plan.toml)
contains the reviewed production-file candidates:

- [staged lifecycle model](../../plans/pairblock-lifecycle-evidence/add/tools/pairblock_status/lifecycle_evidence.py)
- [staged observing tests](../../plans/pairblock-lifecycle-evidence/add/tests/pairblock_status/test_lifecycle_evidence_records.py)
- [staged dependency declaration](../../plans/pairblock-lifecycle-evidence/replace/requirements.txt)
- [isolated plan checker](../../plans/pairblock-lifecycle-evidence/check.py)

The plan fixes Git commit `b3bdaa1b2e134b2a04a448dd279e8aeb1b064915` as
the reviewed baseline. Its checker extracts that commit before applying the
declared actions, so later production changes cannot alter the candidate being
verified.

Gate obligations:

```text
valid approval reference parses
valid implementation-review reference parses
valid VIPER-registration reference parses
unknown fields fail
wrong nested type fails
review receipt supplied to register fails
registration receipt supplied to accept fails
non-canonical repository path fails
malformed SHA-256 fails
generated schema describes every persisted field
validated records reject mutation
```

### `P0-PB-10L` — controller, CLI, persistence, and rendering

Depends on `P0-PB-10K`.

Owns:

```text
event-specific CLI commands
schema-version-4 receipt writer
typed lifecycle dispatch
implementation-review receipt validation
status projection
human-facing next-command rendering
declaration-revision approval reuse
```

Expected production targets:

```text
tools/pairblock_status/pairblock_controller.py
tools/pairblock_status/receipt_validation.py
tools/pairblock_status/markdown_renderer.py
tools/pairblock_status/checklist_profile.py
tests/pairblock_status/test_pairblock_controller.py
tests/pairblock_status/test_receipt_integrity.py
tests/pairblock_status/test_markdown_renderer.py
```

### `P0-PB-10M` — registration producer and migration audit

Depends on `P0-PB-10L`.

Owns:

```text
PairBlockViperRegistration schema
programmatic registration-receipt writer
VIPER-registration receipt validation
audit of existing schema-3 native receipts
mixed schema-3/schema-4 predecessor chains
P0-PB-07B completion through the new register command
```

This block is where the architecture proves itself against a real pending
transition. `P0-PB-07B` is currently `Applied`, with a valid
implementation-review receipt at
[181e2976....json](../../evidence/pairblock-reviews/p0-pb-07b/181e29768320a0d8f809428655972431e957d1c5.json).
Its next event is therefore the live acceptance case.

## Verification

`P0-VR-37` accepts the contract only when all three PairBlocks close these
conditions:

| Rule | Executable condition |
|---|---|
| Event type | Each serialized event parses into exactly one transition class and rejects every other evidence discriminator. |
| Review relationship | `accept` verifies the referenced review schema, digest, PairBlock ID, requirement IDs, approving verdict, and implementation commit. |
| Registration relationship | `register` verifies the referenced registration schema, digest, PairBlock ID, implementation commit, VIPER run, and passing verification result. |
| Persistence | New transitions write schema-version-4 receipts whose predecessor, declaration fingerprint, and repository identities validate. |
| Compatibility | Existing receipts remain unchanged; the compatibility audit reports each schema-3 native receipt that satisfies or falls outside the stronger relationship checks. |
| Projection | The contract and checklist derive the same status and event-specific next command from the validated receipt chain. |

## Acceptance cases

### Success

```text
P0-PB-07B is Applied
        |
        v
program generates PairBlockViperRegistration
        |
        v
registration names P0-PB-07B
registration names MANTRA commit 181e2976...
registration points to verified VIPER evidence
        |
        v
pairblock register P0-PB-07B --viper-receipt ...
        |
        v
schema-version-4 receipt is written
        |
        v
checklist and contract render Complete
```

### Rejection

```text
P0-PB-07B is Applied
        |
        v
operator supplies its implementation-review receipt to register
        |
        v
parser sees kind="implementation_review"
        |
        v
RegistrationTransition requires ViperRegistrationRef
        |
        v
reject before any receipt or Markdown write
```

Additional rejection cases:

- registration names `P0-PB-07A`;
- registration names a different MANTRA commit;
- VIPER verification reports failure;
- referenced receipt bytes have changed;
- a schema-3 `accept` artifact is not a valid implementation-review receipt;
- an unknown transition or evidence field appears.

## Invariant audit

- **Preserved:** TOML owns PairBlock declarations, dependencies, source, tests,
  and gates.
- **Preserved:** `GateReceipt` moves a passing proposal to `Review`.
- **Preserved:** receipt order determines lifecycle state.
- **Preserved:** declaration and implementation repository identities remain
  distinct.
- **Preserved:** projection transactions update the contract and checklist
  together.
- **Strengthened:** approval, acceptance, and registration each accept one
  semantic evidence type.
- **Strengthened:** referenced bytes must describe the same PairBlock and
  implementation commit.
- **Changed:** new lifecycle receipts use schema version 4.
- **Changed:** the native CLI exposes event-specific commands.
- **Introduced:** PairBlock-specific VIPER registration records are generated
  from verified runs.
- **Introduced:** mixed schema-3/schema-4 chains receive an explicit
  compatibility test.

## Compatibility decision

Do not rewrite the 132 historical lifecycle records.

The compatibility boundary should be:

```text
existing schema 1–3 receipts
    -> immutable historical reader
    -> retain their recorded state

new native transitions
    -> schema 4 only
    -> event-specific validation
```

Before activation, `P0-PB-10M` should audit the schema-3 native receipts and
report which can be interpreted under the stronger rules. That audit informs
us; it does not mutate the original records.

Phase 1 begins entirely under schema 4.

## Verdict

**Implement the proposal, split across `P0-PB-10K`, `10L`, and `10M`.**

The design closes a demonstrated gap without replacing the parts that already
work. It also reduces user friction: the user chooses the event and relevant
record, while the controller derives its type, digest, and required
relationships.

The first implementation action is `P0-PB-10K`. Its complete candidates live
in the source-backed plan. `P0-PB-07B` remains untouched until the new
registration path is ready.
