# Foundational reproducibility formalism

This document defines the VIPER 0.1 protocol: its mathematical objects,
serialized documents, state transitions, and verification relationships.

## Contents

- [1. Model family and estimator](#1-model-family-and-estimator)
- [2. Construction of the run plan](#2-construction-of-the-run-plan)
- [3. Permitted runtime states](#3-permitted-runtime-states)
- [4. Initial training state](#4-initial-training-state)
- [5. Training-state transition](#5-training-state-transition)
- [6. Estimator and strict reproducibility](#6-estimator-and-strict-reproducibility)
- [7. Stage outputs and terminal training checkpoints](#7-stage-outputs-and-terminal-training-checkpoints)
- [8. Artifact partition of a training checkpoint](#8-artifact-partition-of-a-training-checkpoint)
- [9. File representation of an artifact](#9-file-representation-of-an-artifact)
- [10. Boundary rules](#10-boundary-rules)
- [11. Complete dependency chain](#11-complete-dependency-chain)
- [12. Protocol record roles](#12-protocol-record-roles)
- [13. File, artifact, and stage-result records](#13-file-artifact-and-stage-result-records)
- [14. Run, input, and attempt records](#14-run-input-and-attempt-records)
- [15. Environment, reproducibility, and execution records](#15-environment-reproducibility-and-execution-records)
- [16. Experiment, variant, replicate, and measurement records](#16-experiment-variant-replicate-and-measurement-records)
- [17. Concrete stage records](#17-concrete-stage-records)
- [18. Training checkpoint mapping](#18-training-checkpoint-mapping)
- [19. Evaluation stage](#19-evaluation-stage)
- [20. Benchmark specification and confirmation](#20-benchmark-specification-and-confirmation)
- [21. Validation and external verification](#21-validation-and-external-verification)
- [22. Execution and publication sequence](#22-execution-and-publication-sequence)
- [23. Repository layout](#23-repository-layout)
- [Appendix A. Complete training-state transition](#appendix-a-complete-training-state-transition)
- [Appendix B. DataLoader iteration and RNG state](#appendix-b-dataloader-iteration-and-rng-state)

## 1. Model family and estimator

A family specification $\alpha$ determines:

```math
\alpha
\longmapsto
\left(
\Theta_\alpha,
I_\alpha,
\mathcal{G}_\alpha
\right),
```

where:

- $\Theta_\alpha$ is the parameter space.
- $I_\alpha$ maps a parameter value to its prediction function.
- $\mathcal{G}_\alpha$ is the resulting family of prediction functions.

Thus:

```math
I_\alpha
:
\Theta_\alpha
\longrightarrow
\mathcal{G}_\alpha.
```

The estimator specification $\beta$ determines the map from datasets to
parameter values:

```math
T_{\alpha,\beta}
:
\mathcal{D}
\longrightarrow
\Theta_\alpha.
```

The run plan $q$ fixes:

- The family specification $\alpha$.
- The estimator specification $\beta$.
- The dataset selection $D_q$.

The selected dataset is a member of the estimator's dataset space:

```math
D_q
\in
\mathcal{D}.
```

The exact dataset artifacts selected by the stage inputs, together with the
stage callables and typed parameters that select samples, features, quality
controls, and transformations, determine $D_q$.

The final parameter value produced by the run is denoted:

```math
\widehat{\theta}_q
\in
\Theta_\alpha.
```

Its fitted prediction function is:

```math
\widehat{g}_q
=
I_\alpha
\left(
\widehat{\theta}_q
\right).
```

## 2. Construction of the run plan

The experiment records and experiment decisions determine $q$:

```text
ExperimentSpec
├── factors and permitted levels
├── replicates and seeds
└── metric identities

VariantSpec
├── selected level for every factor
└── typed stage parameters

ReplicateSpec
└── selected seed
        │
        ▼
experiment decisions
├── run metadata
├── reproducibility controls
├── shared environment
└── ordered stage specifications
        │
        ▼
run plan q
```

Define:

- $\mathcal{M}$ as the set of possible run-metadata records.
- $\mathcal{C}$ as the set of possible reproducibility specifications.
- $\mathcal{H}$ as the set of possible shared-environment specifications.
- $\Omega$ as the set of valid stage specifications.
- $\Omega^+$ as the set of nonempty ordered sequences with members in $\Omega$.

The run-plan space is:

```math
\mathcal{Q}
=
\mathcal{M}
\times
\mathcal{C}
\times
\mathcal{H}
\times
\Omega^+.
```

A run plan is:

```math
q
=
\left(
m_q,
c_q,
h_q,
\boldsymbol{\omega}_q
\right)
\in
\mathcal{Q}.
```

### Run metadata

The metadata $m_q$ identifies the run, experiment, variant, replicate, source,
estimator output, and optional benchmark. Each experiment replicate has one
seed. The run uses the selected replicate's seed, denoted $\zeta_q$, as its
global seed.

### Reproducibility controls

The executor applies $\zeta_q$ to every stage's random-number generators. The
run-wide specification $c_q$ fixes the deterministic-algorithm, precision, and
parallelism controls applied to every stage.

### Shared environment

The shared environment is:

```math
h_q\in\mathcal{H}.
```

It supplies the requested environment for each stage that uses the shared environment.

### Ordered stage specifications

The stage sequence is:

```math
\boldsymbol{\omega}_q
=
\left\langle
\omega_1,\ldots,\omega_m
\right\rangle
\in
\Omega^+,
\qquad
m\geq 1.
```

The index $j\in\{1,\ldots,m\}$ identifies a stage’s position in the execution order.

Each $\omega_j$ declares:

- Stage kind.
- Implementation callable.
- Inputs.
- Parameters.
- Outputs.
- Optional environment override.

The selected `VariantSpec` supplies the typed parameters implemented by the corresponding stage specs.

The complete plan is:

```text
run plan q
├── metadata m_q
│   └── identifies the run, experiment, variant, replicate, source,
│       estimator output, optional benchmark, and global seed ζq
├── reproducibility c_q
│   └── fixes deterministic-algorithm, precision, and parallelism controls
├── environment h_q
│   └── shared environment
└── stages ω_q = ⟨ω₁, …, ωₘ⟩
    └── exact ordered stage specifications that complete α, β, and Dq
```

Together, the experiment, variant, replicate, and experiment decisions determine
$q$.

## 3. Permitted runtime states

Each stage uses the shared environment $h_q$ or an environment override declared
by its stage specification. Let $h_{q,j}$ denote the environment selected for
stage $j$.

Let $E_j$ be the set of possible runtime states for stage $j$. The states
permitted by $q$ are:

```math
E_{q,j}
=
\left\{
e_j\in E_j:
e_j\text{ satisfies }h_{q,j}
\text{ and }c_q
\right\}.
```

The complete permitted runtime-state set is:

```math
E_q
=
E_{q,1}
\times
\cdots
\times
E_{q,m}.
```

The stage specifications in $q$ fix the computation. The selected environments
and $c_q$ define $E_q$, the runtime variation permitted while executing that
fixed computation. Section 6 requires $T_{\alpha,\beta,q}$ to have the same
value for every member of $E_q$.

One execution realizes:

```math
e
=
\left(
e_1,\ldots,e_m
\right)
\in
E_q.
```

A valid run plan requires:

```math
E_q
\neq
\varnothing.
```

```text
q
├── shared environment
├── global reproducibility controls
└── exact stage specifications
        │
        ▼
permitted stage states E_q,1, …, E_q,m
        │
        ▼
permitted complete run states E_q
        │
        ▼
one execution realizes e ∈ E_q
```

## 4. Initial training state

The index $j\in\{1,\ldots,m\}$ continues to identify a stage position. Let
$\Omega_{\mathrm{train}}\subseteq\Omega$ be the set of valid training-stage
specifications. Fix one position $k$ such that:

```math
\omega_k
\in
\Omega_{\mathrm{train}}.
```

The stage $\omega_k$ is therefore a training stage. Let
$N_k\in\mathbb{N}_{>0}$ be its number of optimizer updates. The index
$t\in\{0,\ldots,N_k\}$ identifies a training state within $\omega_k$.
For each $t$, let $\mathcal{S}_{k,t}$ be the set of possible training states
after $t$ updates in $\omega_k$.

Its realized runtime state is:

```math
e_k
\in
E_{q,k}.
```

When $\omega_k$ begins from initialization, one initialization operation
produces the initial training state:

```math
s_k^{(0)}
=
I^{\mathrm{init}}_{\alpha,\beta,q}
\left(
\omega_k,
D_q,
\zeta_q,
e_k
\right)
=
\left(
\theta_k^{(0)},
o_k^{(0)},
r_k^{(0)},
b_k^{(0)}
\right)
\in
\mathcal{S}_{k,0}.
```

This joint definition preserves the dependencies created during
initialization. Random parameter initialization advances the generator it
uses. The optimization state is constructed for the initialized
parameters. The random-number-generator state $r_k^{(0)}$ is the state after
initialization completes, and $b_k^{(0)}$ is the resulting sampler and batch
state.

Here, $\theta_k^{(t)}$ contains every parameter and persistent model buffer
required by the fitted prediction function. The optimization state
$o_k^{(t)}$ contains every mutable optimizer, learning-rate-scheduler, and
gradient-scaler value used by $\beta$. The state $r_k^{(t)}$ contains every
random-number-generator state, and $b_k^{(t)}$ contains the sampler and batch
progress required to select the next training examples.

```text
ωₖ + Dq + ζq + eₖ
          │
          ▼ initialization
sₖ⁽⁰⁾ = (θₖ⁽⁰⁾, oₖ⁽⁰⁾, rₖ⁽⁰⁾, bₖ⁽⁰⁾)
```

When $\omega_k$ continues from an earlier checkpoint, Section 7 defines
$s_k^{(0)}$ as the state reconstructed from that checkpoint.

## 5. Training-state transition

For the fixed training stage $\omega_k$, one completed optimizer update is the
transition:

```math
U_{\alpha,\beta,q,t}
\left(
\omega_k,
\cdot,
\cdot,
\cdot
\right)
:
\mathcal{D}
\times
E_{q,k}
\times
\mathcal{S}_{k,t}
\longrightarrow
\mathcal{S}_{k,t+1},
```

where:

```math
s_k^{(t+1)}
=
U_{\alpha,\beta,q,t}
\left(
\omega_k,
D_q,
e_k,
s_k^{(t)}
\right).
```

The transition selects the data for update $t+1$, performs the forward and
backward computations, applies the optimizer update, and returns:

```math
s_k^{(t+1)}
=
\left(
\theta_k^{(t+1)},
o_k^{(t+1)},
r_k^{(t+1)},
b_k^{(t+1)}
\right).
```

The returned model state includes parameter changes from the optimizer and
persistent-buffer changes from the forward computation. The returned generator
and batch states include every change made while selecting and processing the
data for that update. Appendix A defines these internal operations in causal
order.

Repeated application for $t=0,\ldots,N_k-1$ produces the training-state
sequence:

```math
s_k^{(0)}
\longmapsto
s_k^{(1)}
\longmapsto
\cdots
\longmapsto
s_k^{(N_k)}.
```

The stage sequence $\boldsymbol{\omega}_q$ is a component of $q$.
Its $k$th member $\omega_k$ is the fixed stage-specification argument of every
transition in this training stage.

## 6. Estimator and strict reproducibility

Let $k_*$ be the position of the training stage whose `parameters`
artifact is selected as the estimator output by $q$. The run estimator is:

```math
T_{\alpha,\beta,q}
:
E_q
\longrightarrow
\Theta_\alpha.
```

It applies the stages fixed by $q$ and returns the terminal model-parameter
value produced by $\omega_{k_*}$:

```math
T_{\alpha,\beta,q}(e)
=
\theta_{k_*}^{(N_{k_*})}.
```

The plan provides strict parameter reproducibility exactly when:

```math
\forall e,e'\in E_q,
\qquad
T_{\alpha,\beta,q}(e)
=
T_{\alpha,\beta,q}(e').
```

The common value is:

```math
\widehat{\theta}_q.
```

Therefore:

```math
\forall e\in E_q,
\qquad
T_{\alpha,\beta,q}(e)
=
\widehat{\theta}_q.
```

The protocol represents equality of two terminal parameter values by equality
of their `parameters` artifacts: identical relative paths, SHA-256
values, byte counts, and bundle membership under the loader fixed by $q$.

Because $\alpha$ is fixed by $q$, strict parameter reproducibility also gives:

```math
I_\alpha
\left(
T_{\alpha,\beta,q}(e)
\right)
=
I_\alpha
\left(
\widehat{\theta}_q
\right)
=
\widehat{g}_q.
```

## 7. Stage outputs and terminal training checkpoints

The ordered sequence $\boldsymbol{\omega}_q$ defines the stages of the run. For
each $j\in\{1,\ldots,m\}$, let $y_j$ denote the declared output state produced
by $\omega_j$. A later stage may consume one or more artifacts from $y_j$.

```text
stages of the run

ω₁ ──→ y₁
ω₂ ──→ y₂
⋮
ωₘ ──→ yₘ
```

VIPER permits replay from a training state when a later stage or attempt may
consume that state as its initial state. A training stage is the maximal
contiguous sequence of updates ending at the next permitted replay state.

The training stage $\omega_k$ therefore has the sequence:

```text
training stage ωₖ

sₖ⁽⁰⁾ → sₖ⁽¹⁾ → ··· → sₖ⁽ᴺᵏ⁾
```

Its single checkpoint is its terminal state:

```math
s_k^{(N_k)}.
```

The artifacts representing $s_k^{(N_k)}$ belong to the declared stage output
$y_k$. A later training stage $\omega_\ell$ that continues from this checkpoint
begins from the reconstructed state:

```math
s_\ell^{(0)}
=
s_k^{(N_k)}.
```

If $q$ permits replay from $s_k^{(t)}$ for some $0<t<N_k$, that state terminates
$\omega_k$ and the remaining updates belong to another training stage. Each
run plan contains finitely many stages, and $m$ ranges over the positive
integers across the run-plan space.

```text
training stage ωₖ
├── begins at sₖ⁽⁰⁾
├── applies Nₖ updates
└── ends at checkpoint sₖ⁽ᴺᵏ⁾
    └── represented by artifacts in yₖ
```

For a training stage, the stage boundary and terminal checkpoint identify the
same replay boundary.

## 8. Artifact partition of a training checkpoint

An artifact is one named value that a required use can load independently. Let
$\mathcal{A}(y_j)$ be the set of artifact names in stage output $y_j$. Each
$a\in\mathcal{A}(y_j)$ identifies one value $v_a^{(j)}$.

For the checkpoint of training stage $\omega_k$, let
$a_\theta$ denote the `parameters` artifact and let $a_c$ denote the
`resume_state` artifact. Then:

```math
\mathcal{A}
\left(
s_k^{(N_k)}
\right)
=
\left\{
a_\theta,
a_c
\right\}
\subseteq
\mathcal{A}(y_k).
```

Their values are:

```math
v_{a_\theta}^{(k)}
=
\theta_k^{(N_k)},
```

and:

```math
v_{a_c}^{(k)}
=
\left(
o_k^{(N_k)},
r_k^{(N_k)},
b_k^{(N_k)}
\right).
```

```text
sₖ⁽ᴺᵏ⁾
├── parameters
│   └── θₖ⁽ᴺᵏ⁾
│       └── sufficient for evaluation
│
└── resume_state
    └── (oₖ⁽ᴺᵏ⁾, rₖ⁽ᴺᵏ⁾, bₖ⁽ᴺᵏ⁾)
        └── combined with parameters for exact resumption
```

The `resume_state` artifact loads as:

```python
class PythonRNGState(ProtocolModel):
    version: int = Field(ge=0)
    internal_state: tuple[int, ...] = Field(min_length=1)
    gaussian_cache: float | None


UInt32 = Annotated[int, Field(ge=0, lt=2**32)]
UInt128 = Annotated[int, Field(ge=0, lt=2**128)]


class PCG64InternalState(ProtocolModel):
    state: UInt128
    inc: UInt128


class PCG64GeneratorState(ProtocolModel):
    bit_generator: Literal["PCG64"] = "PCG64"
    state: PCG64InternalState
    has_uint32: Literal[0, 1]
    uinteger: UInt32


class LegacyNumPyRNGState(ProtocolModel):
    bit_generator: Literal["MT19937"] = "MT19937"
    keys: tuple[UInt32, ...] = Field(min_length=624, max_length=624)
    position: int = Field(ge=0, le=624)
    has_gaussian: Literal[0, 1]
    cached_gaussian: float = Field(allow_inf_nan=False)


class NumPyRNGState(ProtocolModel):
    generators: dict[HumanId, PCG64GeneratorState]
    legacy_global: LegacyNumPyRNGState | None


class MainProcessRNGState(ProtocolModel):
    python: PythonRNGState
    numpy: NumPyRNGState
    torch_cpu: bytes = Field(min_length=1)
    torch_cuda: tuple[bytes, ...]


class DataLoaderResumeState(ProtocolModel):
    configuration: DataLoaderConfiguration
    state_dict: dict[str, object] = Field(min_length=1)


class ResumeState(ProtocolModel):
    schema_version: Literal[1] = 1
    optimizer_state: dict[str, object] = Field(min_length=1)
    main_process_rng: MainProcessRNGState
    dataloader: DataLoaderResumeState
```

`ResumeState.optimizer_state` records $o_k^{(N_k)}$.
`main_process_rng` records the Python, named NumPy, legacy NumPy, and PyTorch
generator states held by the training process. `dataloader.state_dict` records
the state returned by the stateful loader, including the position from which
data loading continues. Together, `main_process_rng` and `dataloader` represent
$r_k^{(N_k)}$ and $b_k^{(N_k)}$.

The verifier requires `dataloader.configuration` to equal the run-wide
`DataLoaderConfiguration`. It also requires the saved NumPy generator names
and the presence of `legacy_global` to match `NumPyRandomnessSpec`.

This is the coarsest artifact partition satisfying the two required uses:

- Evaluation loads `parameters`.
- Exact resumption loads `parameters` and `resume_state`.

## 9. File representation of an artifact

For artifact $a\in\mathcal{A}(y_j)$, let:

```math
F_j(a)
=
\left\{
f_1,\ldots,f_n
\right\},
\qquad
n\geq 1,
```

be the files assigned to that artifact.

Let $L_{j,a}$ be the loader selected for artifact $a$ by stage $\omega_j$.
The files must reconstruct the artifact value:

```math
L_{j,a}
\left(
F_j(a)
\right)
=
v_a^{(j)}.
```

Here, $v_a^{(j)}$ denotes the value returned by the frozen loader. Generic
artifact verification establishes representation identity and loadability.
The reserved `resume_state` artifact also passes the protocol-owned
`ResumeState` validator.

The protocol assigns physical form by cardinality. A single-file artifact has:

```math
\left|F_j(a)\right|
=
1,
```

A bundle artifact preserves one declared directory root and the relative path
of each member. It has:

```math
\left|F_j(a)\right|
\geq
2.
```

The verifier enumerates every regular file beneath a declared bundle root and
requires exact agreement with the resolved member list. It then checks the
identity of every listed file and invokes the frozen loader. These checks prove
bundle completeness, file identity, and loadability for the representation
selected by the author.

Artifact minimality is an authoring condition: removing any member either
prevents loading or changes the reconstructed value. The verifier checks the
selected representation. The author establishes minimality during plan design.

```text
artifact name a
└── artifact value v_a⁽ʲ⁾
    ▲
    │ loader L_j,a
    │
    └── files F_j(a)
        ├── one file: single-file artifact
        └── two or more named members beneath a root: bundle artifact
```

## 10. Boundary rules

The protocol applies completeness and parsimony at three nested boundaries:

1. Every state from which $q$ permits replay creates a stage boundary. A
   training stage ends at its single terminal checkpoint $s_k^{(N_k)}$.
2. A separate artifact exists for every value that a required use loads
   independently.
3. An author includes a file in an artifact exactly when its loader requires
   that file to reconstruct the artifact value.

These rules supply direct parsimony tests:

- A permitted replay state requires a training-stage boundary. An author can
  remove another training-stage boundary when the merged stage preserves every
  declared input, environment, operation, output, and required replay state.
- Two artifacts can be merged exactly when every required use loads both
  values together.
- A file can be removed from $F_j(a)$ exactly when $L_{j,a}$ still reconstructs
  $v_a^{(j)}$ from the remaining files.

Experiment design declares the required replay positions and independently
loadable uses. Plan authoring applies these tests before $q$ is frozen. Once
$q$ is frozen, its stage boundaries and artifact declarations are fixed.
Execution resolves each declared artifact to its exact file set. Pydantic and
the external verifier enforce that selected representation.

When authoring satisfies all three parsimony tests, the resulting stage
sequence, artifact partition, and file sets form the coarsest complete
representation for the declared replay states and required uses.

## 11. Complete dependency chain

```text
ExperimentSpec + VariantSpec + ReplicateSpec
+ experiment decisions
                │
                ▼
run plan q
├── metadata m_q, including the selected replicate and global seed ζq
├── reproducibility c_q, applied to every stage
├── shared environment h_q
└── ordered stage specs ⟨ω₁, …, ωₘ⟩
                │
                ▼
permitted runtime states E_q
                │
                ▼
one execution realizes e = (e₁, …, eₘ) ∈ E_q
                │
                ▼
           stage ωⱼ ∈ Ω
                │
        produces output yⱼ
                │
                ▼
     artifact partition 𝒜(yⱼ)
                │
                ▼
    file representation F_j(a)

If ωⱼ = ωₖ ∈ Ω_train:

       training stage ωₖ
                │
     sₖ⁽⁰⁾ → ··· → sₖ⁽ᴺᵏ⁾
                │
                ▼
 terminal checkpoint sₖ⁽ᴺᵏ⁾
                │
                ▼
artifact partition 𝒜(sₖ⁽ᴺᵏ⁾)
                │
                ▼
  file representation F_k(a)
                │
                ▼
Tα,β,q(e) = θₖ*⁽ᴺₖ*⁾ = θ̂q
                │
                ▼
          Iα(θ̂q) = ĝq
```

## 12. Protocol record roles

Protocol files contain records validated by Pydantic models. Their names state
their roles:

| Form | Role |
|---|---|
| `*Spec` | Declares requested state. |
| `Resolved*` | Records realized state. |
| `*Ref` | Identifies another protocol object. |
| `ArtifactPointer` | Selects one promoted artifact. |
| `ResolvedArtifact` | Records the files representing one named artifact. |
| `Measurement` | Records one metric value. |
| `RunAttempt` | Records one execution attempt. |
| `ResolvedRun` | Records the terminal run result. |

```text
Spec
└── declares requested state and contributes to q
        │
        ▼
q induces E_q

Resolved
└── records one realized e ∈ E_q

Verifier
├── checks e ∈ E_q
└── verifies every referenced file against its recorded identity
```

The protocol identifies exact files in two forms:

```text
standalone file
└── ResolvedFileRef
    ├── stored_at
    ├── sha256
    └── bytes

file in a stage-result snapshot
├── StageResultSnapshotRef
│   └── repository + commit
└── SnapshotFileRef
    ├── path
    ├── sha256
    └── bytes
```

A role-specific file reference states the record type expected from the
retrieved bytes. For example, `ResolvedRunRef` identifies a standalone file
that parses as `ResolvedRun`.

`ArtifactPointer`, `ArtifactPointerRef`, and `ResolvedArtifactPointerRef` have
separate roles:

```text
ArtifactPointer
└── selects one artifact from one successful run

ArtifactPointerRef
└── identifies the Git file containing that ArtifactPointer

ResolvedArtifactPointerRef
├── stored_at: ArtifactPointerRef
├── sha256
└── bytes
```

## 13. File, artifact, and stage-result records

Every protocol record is closed and immutable after validation:

```python
class ProtocolModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ParameterSet(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)
    __pydantic_extra__: dict[str, JsonValue] = Field(init=False)
    schema_version: Literal[1] = 1


class Build(ParameterSet): ...
class Embed(ParameterSet): ...
class Train(ParameterSet): ...
class Evaluate(ParameterSet): ...
class Metric(ParameterSet): ...
class Http(ParameterSet): ...
```

`ParameterSet` and its six public categories belong to
`viper.parameters`. Project code specializes the category that matches the
consumer of its values.

The records below use these shared types:

| Type | Accepted value |
|---|---|
| `HumanId` | A lowercase identifier matching `^[a-z][a-z0-9_]*$`. |
| `RepoRelPath` | A normalized POSIX path relative to the repository root, composed of named segments and free of dot segments, parent traversal, backslashes, and control characters. |
| `PythonRepoRelPath` | A `RepoRelPath` ending in `.py`. |
| `PythonSymbol` | A top-level Python identifier selected from one module. |
| `NormalizedDistributionName` | A Python distribution name normalized under the PyPA name-normalization rule. |
| `HttpHeaderName` | A lowercase HTTP field name accepted by the controlled retriever and selected HTTP implementation. |
| `SHA256` | A 64-character lowercase hexadecimal digest. |
| `GitCommit` | A 40- or 64-character lowercase hexadecimal commit ID. |
| `NonEmptyStr` | A string containing at least one character. |

`RunId`, `StageId`, `ExperimentId`, `VariantId`, `ReplicateId`, `FactorId`,
`LevelId`, `MetricId`, `InputName`, `EvaluationId`, and `BenchmarkId` are
role-specific aliases of `HumanId`.

### Exact file identity

A standalone file is stored at an immutable Git, Hugging Face, or
repository-local VIPER revision:

```python
class GitSource(ProtocolModel):
    kind: Literal["git"] = "git"
    repository: HttpUrl
    commit: GitCommit


class GitFileRef(GitSource):
    path: RepoRelPath


class HuggingFaceFileRef(ProtocolModel):
    kind: Literal["huggingface"] = "huggingface"
    repository: NonEmptyStr
    commit: GitCommit
    path: RepoRelPath
    repo_type: Literal["model", "dataset", "space"]


class LocalFileRef(ProtocolModel):
    kind: Literal["local"] = "local"
    store: RepoRelPath = ".viper/store"
    commit: SHA256
    path: RepoRelPath


StorageModel = GitFileRef | HuggingFaceFileRef | LocalFileRef

StorageRef = Annotated[
    StorageModel,
    Field(discriminator="kind"),
]
```

A standalone file records its storage location and content identity:

```python
class ResolvedFileRef(ProtocolModel):
    sha256: SHA256
    bytes: int = Field(ge=0)
    stored_at: StorageRef
```

A completed stage is published as one immutable snapshot:

```python
class StageResultSnapshotRef(ProtocolModel):
    kind: Literal["huggingface"] = "huggingface"
    repository: NonEmptyStr
    commit: GitCommit
    repo_type: Literal["model", "dataset", "space"]


class LocalStageResultSnapshotRef(ProtocolModel):
    kind: Literal["local"] = "local"
    store: RepoRelPath = ".viper/store"
    commit: SHA256


StageResultSnapshot = Annotated[
    StageResultSnapshotRef | LocalStageResultSnapshotRef,
    Field(discriminator="kind"),
]
```

Each file within that snapshot records its repository-relative path and content
identity:

```python
class SnapshotFileRef(ProtocolModel):
    path: RepoRelPath
    sha256: SHA256
    bytes: int = Field(ge=0)
```

The exact storage location of a snapshot file is determined by one branch:

```text
Hugging Face snapshot
└── repository + commit + SnapshotFileRef.path

local snapshot
└── store + commit + SnapshotFileRef.path
```

The verifier retrieves that file and requires equality with
`SnapshotFileRef.sha256` and `SnapshotFileRef.bytes`.

### Artifact declarations

```python
ArtifactName = HumanId
DataRole = Literal["training", "validation", "evaluation", "benchmark"]


class ArtifactLoaderRef(ProtocolModel):
    path: PythonRepoRelPath
    symbol: PythonSymbol = "load"
    sha256: SHA256
    bytes: int = Field(gt=0)


class StageImplementationRef(ProtocolModel):
    path: PythonRepoRelPath
    symbol: PythonSymbol
    sha256: SHA256
    bytes: int = Field(gt=0)


class ParameterModelRef(ProtocolModel):
    path: PythonRepoRelPath
    symbol: PythonSymbol
    sha256: SHA256
    bytes: int = Field(gt=0)


class StageContextBinding(ProtocolModel):
    schema_version: Literal[1] = 1
    run_id: RunId
    attempt_id: int = Field(ge=1)
    stage_id: StageId
    parameter_model: ParameterModelRef
    parameter_digest: SHA256
    inputs: dict[InputName, RepoRelPath]
    artifacts: dict[ArtifactName, RepoRelPath]
    metric_ids: tuple[MetricId, ...]
    numpy_generator_names: tuple[HumanId, ...]


class StageInvocationReceipt(ProtocolModel):
    implementation: StageImplementationRef
    context: StageContextBinding
    context_digest: SHA256
    started_at: AwareDatetime
    completed_at: AwareDatetime
    outcome: Literal["succeeded", "failed", "cancelled", "preempted"]


class ResolvedStageInvocationRef(ResolvedFileRef):
    kind: Literal["stage_invocation"] = "stage_invocation"


class SingleFileArtifactSpec(ProtocolModel):
    kind: Literal["file"] = "file"
    path: RepoRelPath
    loader: ArtifactLoaderRef
    data_role: DataRole


class BundleArtifactSpec(ProtocolModel):
    kind: Literal["bundle"] = "bundle"
    path: RepoRelPath
    loader: ArtifactLoaderRef
    data_role: DataRole


ArtifactSpec = Annotated[
    SingleFileArtifactSpec | BundleArtifactSpec,
    Field(discriminator="kind"),
]


class BaseSpec(ProtocolModel):
    kind: str
    schema_version: Literal[1] = 1
    environment: EnvironmentSpec | None = None
    metric_ids: tuple[MetricId, ...] = ()
    artifacts: dict[ArtifactName, ArtifactSpec] = Field(min_length=1)
```

The parameter and context digests use `document_digest()`. This function hashes
the model's JSON value with mapping keys sorted and compact separators, so the
digest is independent of source-field order.

For a single-file artifact, `path` identifies its file. For a bundle artifact,
`path` identifies its directory root. Every artifact path has the form:

```text
experiments/<experiment_id>/runs/<variant_id>/<run_id>/artifacts/
    <category>/<entity_id>/<file_or_bundle_path>
```

The artifact category is `datasets` for a download stage, `priors` for a build
stage, `models` for an embed or train stage, and `evaluations` for an evaluate
stage. A single-file artifact includes a filename after `<entity_id>`. A bundle
root may equal the identity directory or a directory beneath it.

`ParameterizedSpec.implementation`, `MetricSpec.implementation`, and
`ArtifactSpec.loader` identify one top-level symbol in one exact Python file.
Each reference stores the repository-relative path, symbol, SHA-256 digest, and
byte count. `RunSpec.source` fixes the repository revision containing each
file. VIPER accepts every project package name and source-directory layout that
the frozen repository-relative paths identify.

An artifact loader defines:

```python
def load(path: Path) -> object:
    ...
```

For a single-file artifact, the executor supplies the materialized file path.
For a bundle artifact, the executor supplies the materialized directory path.

### Resolved artifacts

```python
class ResolvedSingleFileArtifact(ProtocolModel):
    kind: Literal["file"] = "file"
    file: SnapshotFileRef


class ResolvedBundleMember(ProtocolModel):
    relative_path: RepoRelPath
    file: SnapshotFileRef


class ResolvedBundleArtifact(ProtocolModel):
    kind: Literal["bundle"] = "bundle"
    members: tuple[ResolvedBundleMember, ...] = Field(min_length=2)


ResolvedArtifact = Annotated[
    ResolvedSingleFileArtifact | ResolvedBundleArtifact,
    Field(discriminator="kind"),
]


class ResolvedBaseSpec(ProtocolModel):
    schema_version: Literal[1] = 1
    kind: str
    spec: BaseSpec
    environment: ResolvedEnvironment
    execution_context: ExecutionContext
    artifacts: dict[ArtifactName, ResolvedArtifact] = Field(min_length=1)
    completed_at: AwareDatetime
```

The artifact-name sets are equal:

```text
keys(ResolvedBaseSpec.spec.artifacts)
==
keys(ResolvedBaseSpec.artifacts)
```

The cardinality of $F_j(a)$ determines the resolved form:

```math
\left|F_j(a)\right|
=
1
\quad\Longleftrightarrow\quad
\text{ResolvedSingleFileArtifact},
```

and:

```math
\left|F_j(a)\right|
\geq
2
\quad\Longleftrightarrow\quad
\text{ResolvedBundleArtifact}.
```

For a single-file artifact:

```text
ResolvedSingleFileArtifact.file.path
==
SingleFileArtifactSpec.path
```

For every bundle member:

```text
ResolvedBundleMember.file.path
==
BundleArtifactSpec.path / ResolvedBundleMember.relative_path
```

Bundle-member paths are unique, pairwise non-overlapping, remain beneath the
bundle root, and appear in canonical `relative_path` order. Artifact roots
within one stage are pairwise non-overlapping. Artifact paths may recur in
distinct stage-result snapshots because each snapshot has its own immutable
commit.

The verifier lists the published bundle root and requires exact agreement with
the resolved member list. It then verifies every file in $F_j(a)$, materializes
the representation, and invokes the loader in a dedicated worker. A successful
generic loader invocation establishes `artifact.loadability`:

```math
L_{j,a}
\left(
F_j(a)
\right)
=
v_a^{(j)}.
```

### Stage-result snapshot

```python
class ResolvedStageRef(ProtocolModel):
    stage_id: StageId
    snapshot: StageResultSnapshot
    resolved_spec: SnapshotFileRef
```

`ResolvedStageRef.snapshot` contains:

```text
one resolved stage-spec file
+ every retrieved response body for a download stage
+ every file in every resolved artifact
```

`ResolvedStageRef.resolved_spec` identifies the resolved stage-spec file within
that snapshot. The loaded resolved spec identifies every artifact file through
its `artifacts` mapping. A `ResolvedDownloadSpec` also identifies every
retrieved response body through its `retrievals` mapping.

```text
ResolvedStageRef
├── snapshot
├── resolved_spec
│   └── loads one ResolvedBaseSpec subtype
└── snapshot + paths loaded from the resolved spec
    ├── identifies every physical artifact file
    └── identifies every retrieved body for a download stage
```

A completed stage has one `ResolvedStageRef`. Its snapshot commit therefore
binds the resolved execution document, every file representing the stage's
declared output $y_j$, and each response body consumed by a download stage.

## 14. Run, input, and attempt records

### Run plan

```python
RNGSeed = Annotated[int, Field(ge=0, le=2**32 - 1)]


class StageArtifactRef(ProtocolModel):
    stage_id: StageId
    artifact_name: ArtifactName


class RunStageRef(ProtocolModel):
    stage_id: StageId
    spec: RepoRelPath
    sha256: SHA256
    bytes: int = Field(ge=0)


class RunSpec(ProtocolModel):
    schema_version: Literal[1] = 1
    run_id: RunId
    experiment_id: ExperimentId
    variant_id: VariantId
    replicate_id: ReplicateId
    benchmark_id: BenchmarkId | None = None

    seed: RNGSeed
    source: GitSource
    environment: EnvironmentSpec
    reproducibility: ReproducibilitySpec

    stages: tuple[RunStageRef, ...] = Field(min_length=1)
    estimator: StageArtifactRef
```

`RunSpec.seed` is the global seed $\zeta_q$ assigned to the selected replicate.
`RNGSeed` restricts it to integers from zero through $2^{32}-1$, inclusive.
The executor applies this value to every recorded generator according to
`RunSpec.reproducibility`.

`RunSpec.environment` supplies $h_q$. For stage $\omega_j$:

```text
BaseSpec.environment is present
→ h_q,j = BaseSpec.environment

BaseSpec.environment is absent
→ h_q,j = RunSpec.environment
```

`RunSpec.reproducibility` supplies $c_q$ to every stage. A stage environment
override changes $h_{q,j}$ and leaves $c_q$ unchanged.

The ordered `RunStageRef` records identify the exact stage-spec files in
$\boldsymbol{\omega}_q$. Stage IDs and stage-spec paths are unique. Each stage
spec path equals:

```text
experiments/<experiment_id>/runs/<variant_id>/<run_id>/stages/<stage_id>/spec.yaml
```

The `RunSpec` file and the stage-spec files it identifies constitute $q$.
The run-plan snapshot and `RunSpec.source` belong to one Git repository.
The shared lockfile, each stage-override lockfile, and every stored-input
pointer belong to the repository and commit identified by `RunSpec.source`.

### Artifact selection and promotion

The terminal run record and run-plan record use role-specific file references:

```python
class ResolvedRunSpecRef(ResolvedFileRef):
    kind: Literal["run_spec"] = "run_spec"
    stored_at: GitFileRef


class ResolvedRunRef(ResolvedFileRef):
    kind: Literal["resolved_run"] = "resolved_run"


class ResolvedBenchmarkResultRef(ResolvedFileRef):
    kind: Literal["benchmark_result"] = "benchmark_result"
```

An `ArtifactPointer` selects one artifact accepted for reuse:

```python
class ArtifactPointer(ProtocolModel):
    schema_version: Literal[1] = 1
    run: ResolvedRunRef
    artifact: StageArtifactRef
    benchmark_result: ResolvedBenchmarkResultRef | None = None


class ArtifactPointerRef(GitFileRef):
    pass


class ResolvedArtifactPointerRef(ResolvedFileRef):
    kind: Literal["artifact_pointer"] = "artifact_pointer"
    stored_at: ArtifactPointerRef
```

The selection path is:

```text
ArtifactPointer.run
→ ResolvedRun
→ successful RunAttempt
→ ResolvedStageRef selected by StageArtifactRef.stage_id
→ loaded ResolvedBaseSpec
→ ResolvedBaseSpec.artifacts[StageArtifactRef.artifact_name]
→ exact artifact files
```

Every `ArtifactPointerRef.path` has the form:

```text
inputs/<category>/<entity_id>/<selection_name>.pointer.yaml
```

The permitted categories are `benchmarks`, `datasets`, `models`, and `priors`.

When the selected run names a benchmark and `ArtifactPointer.artifact` equals
`RunSpec.estimator`, `ArtifactPointer.benchmark_result` identifies the passed
`BenchmarkResult` that authorizes promotion.

### Stage inputs

A stored input selects an artifact promoted from a completed run:

```python
class StoredInputRef(ProtocolModel):
    kind: Literal["stored"] = "stored"
    pointer: ArtifactPointerRef
    path: RepoRelPath
    data_role: DataRole


class ResolvedStoredInputRef(ProtocolModel):
    kind: Literal["stored"] = "stored"
    pointer: ResolvedArtifactPointerRef
```

The planned and resolved pointer locations are equal:

```text
ResolvedStoredInputRef.pointer.stored_at
==
StoredInputRef.pointer
```

`StoredInputRef.path` identifies the local file path or bundle root supplied to
the consuming stage. Its category and entity ID equal those in
`StoredInputRef.pointer.path`. The materialization path and pointer-file path
are disjoint. The materialization path uses a suffix other than
`.pointer.yaml`.

A same-run input selects one artifact from an earlier stage:

```python
class FutureInputRef(ProtocolModel):
    kind: Literal["future"] = "future"
    producer_stage_id: StageId
    name: ArtifactName


class ResolvedFutureInputRef(ProtocolModel):
    kind: Literal["future"] = "future"
    producer: ResolvedStageRef
```

For a consumer at stage position $j$, the producer occurs at a position
$i<j$. The verifier requires:

```text
ResolvedFutureInputRef.producer.stage_id
==
FutureInputRef.producer_stage_id

FutureInputRef.name
in
keys(producer ResolvedBaseSpec.artifacts)
```

The selected artifact's declared path is its local file path or bundle root.

### Data-use roles

Every stored input and produced artifact carries one data-use role:

```python
DataRole = Literal["training", "validation", "evaluation", "benchmark"]
```

The roles are ordered by downstream restriction:

```math
\mathrm{training}
\prec
\mathrm{validation}
\prec
\mathrm{evaluation}
\prec
\mathrm{benchmark}.
```

The role of a source artifact is assigned when that artifact enters the
provenance graph. VIPER records and propagates that declaration. Scientific use
comes exclusively from the declared role.

A stored input declares the role of the artifact selected by its pointer. The
verifier retrieves the producer stage spec and requires equality between the
stored-input declaration and the selected artifact declaration. A
`FutureInputRef` inherits the role of the producer artifact it selects.

For every stage input $x$ and every artifact $a$ produced by that stage:

```math
\operatorname{role}(x)
\preceq
\operatorname{role}(a).
```

This rule propagates the strongest input restriction to every derived output.
A training stage accepts only `training` and `validation` inputs. An ordinary
evaluation uses `evaluation` for its dataset, splits, and outputs. An
evaluation governed by a `BenchmarkSpec` uses `benchmark` for those records.
The `parameters` input to either evaluation has role `training` or
`validation`.

These rules enforce stage-level access and artifact lineage. A stage callable
is user code fixed by `RunSpec.source`. Project tests establish how that
callable uses a permitted validation input.

### Attempts and terminal run result

```python
AttemptStatus = Literal[
    "succeeded",
    "failed",
    "preempted",
    "cancelled",
]


AttemptPurpose = Literal["run", "benchmark_confirmation"]


AttemptFailureCode = Literal[
    "preflight_failed",
    "execution_failed",
    "verification_failed",
    "publication_failed",
    "cancelled",
    "preempted",
    "coordinator_lost",
    "internal_error",
]


class AttemptFailure(ProtocolModel):
    code: AttemptFailureCode
    stage_id: StageId | None
    message: NonEmptyStr
    occurred_at: AwareDatetime


class AttemptJournalRef(ResolvedFileRef):
    kind: Literal["attempt_journal"] = "attempt_journal"


class RunAttempt(ProtocolModel):
    schema_version: Literal[1] = 1
    attempt_id: int = Field(ge=1)
    purpose: AttemptPurpose
    status: AttemptStatus
    started_at: AwareDatetime
    completed_at: AwareDatetime

    resolved_stages: tuple[ResolvedStageRef, ...]
    invocations: tuple[ResolvedStageInvocationRef, ...]
    journal: AttemptJournalRef
    measurement_files: tuple[ResolvedFileRef, ...]
    metric_verification_files: tuple[ResolvedFileRef, ...] = ()
    log_files: tuple[ResolvedFileRef, ...]
    failure: AttemptFailure | None


class ResolvedAttemptRef(ResolvedFileRef):
    kind: Literal["resolved_attempt"] = "resolved_attempt"


class ResolvedRun(ProtocolModel):
    schema_version: Literal[1] = 1
    spec: ResolvedRunSpecRef
    status: Literal["succeeded", "failed", "cancelled"]
    attempts: tuple[ResolvedAttemptRef, ...] = Field(min_length=1)
    successful_attempt_id: int | None
    completed_at: AwareDatetime
```

Each `ResolvedAttemptRef` retrieves one `RunAttempt` from the canonical path:

```text
experiments/<experiment_id>/runs/<variant_id>/<run_id>/
    attempts/<attempt_id>/resolved.yaml
```

Its journal occurs at:

```text
experiments/<experiment_id>/runs/<variant_id>/<run_id>/
    attempts/<attempt_id>/journal.jsonl
```

Measurements, metric-verification receipts, and logs occupy subdirectories of
the same `attempts/<attempt_id>/` directory.

Invocation receipts occupy `attempts/<attempt_id>/invocations/`. Every started
stage produces one receipt, including a stage that fails before producing a
resolved stage snapshot.

Attempt IDs are unique and strictly increasing across the run workspace. Each
attempt has an ordered `resolved_stages` prefix of `RunSpec.stages`. Its stage
snapshots are unique. The journal, measurement, metric-verification, and log
paths are unique and pairwise disjoint. They belong to one immutable attempt
revision $D_i$. Distinct attempts use distinct stage-result snapshots and distinct
$D_i$ revisions. Every $D_i$ differs from every stage-result snapshot.
Attempt intervals are disjoint. A successful run attempt closes the ordinary
run history. A later benchmark-confirmation attempt can use the same frozen
plan and a greater attempt ID. `ResolvedRun.completed_at` is at or after every
run attempt's completion time.

A successful attempt satisfies:

1. Its `failure` value is null.
2. Its `resolved_stages` is nonempty and contains every declared stage exactly
   once and in order.
3. Every `ResolvedStageRef` identifies a verified stage-result snapshot.

A failed, preempted, or cancelled attempt records one typed `AttemptFailure`.
Its log files may identify completed stages and the next declared stage whose
execution failed, was preempted, or was cancelled before producing a
`ResolvedStageRef`. A successful attempt's logs identify its completed stages.

The coordinator maps `SIGINT` to `cancelled` and `SIGTERM` to `preempted`. It
records the received signal before stopping the active child and closing the
attempt. A later coordinator maps an abandoned nonterminal journal to
`failed` with code `coordinator_lost`.

Attempt durability assumes continued access to the configured workspace and
store. A surviving nonterminal journal supplies the evidence needed for later
reconciliation.

A successful `ResolvedRun` identifies exactly one successful attempt through
`successful_attempt_id`. A failed or cancelled `ResolvedRun` sets
`successful_attempt_id` to null. A terminal preempted attempt yields a failed
run result. `ResolvedRun.spec` identifies the exact `RunSpec` file whose stages
govern every attempt.

Explicit retry accepts a failed or cancelled `ResolvedRun` and rejects a
successful one. Benchmark confirmation uses its separate operation.

Every attempt referenced by `ResolvedRun.attempts` has `purpose="run"`. A
`BenchmarkResult` identifies its separate attempt through
`confirmation`; that attempt has `purpose="benchmark_confirmation"`.

```text
ResolvedRun.spec
→ RunSpec
→ ordered RunStageRef records

ResolvedRun.attempts
→ ordered ResolvedAttemptRef records
→ immutable RunAttempt documents
→ ordered ResolvedStageRef prefixes

ResolvedRun.successful_attempt_id
→ complete successful RunAttempt
```

## 15. Environment, reproducibility, and execution records

### Requested environment

```python
class GCEBootImageRef(ProtocolModel):
    kind: Literal["boot_image"] = "boot_image"
    project: NonEmptyStr
    name: NonEmptyStr
    id: NonEmptyStr


class GCEMachineImageRef(ProtocolModel):
    kind: Literal["machine_image"] = "machine_image"
    project: NonEmptyStr
    name: NonEmptyStr
    id: NonEmptyStr


GCEProvisioningRef = Annotated[
    GCEBootImageRef | GCEMachineImageRef,
    Field(discriminator="kind"),
]


class PythonDistributionSpec(ProtocolModel):
    name: NormalizedDistributionName
    version: NonEmptyStr


class PythonEnvironmentSpec(ProtocolModel):
    python_version: NonEmptyStr
    distributions: tuple[PythonDistributionSpec, ...] = Field(min_length=1)


class CPUComputeSpec(ProtocolModel):
    kind: Literal["cpu"] = "cpu"


class CUDAComputeSpec(ProtocolModel):
    kind: Literal["cuda"] = "cuda"
    model: NonEmptyStr
    count: int = Field(ge=1)


ComputeSpec = Annotated[
    CPUComputeSpec | CUDAComputeSpec,
    Field(discriminator="kind"),
]


class GCEEnvironmentSpec(ProtocolModel):
    kind: Literal["gce"] = "gce"
    provisioning: GCEProvisioningRef
    machine_type: NonEmptyStr
    compute: ComputeSpec
    lockfile: GitFileRef
    python_environment: PythonEnvironmentSpec


class LocalEnvironmentSpec(ProtocolModel):
    kind: Literal["local"] = "local"
    compute: ComputeSpec = Field(default_factory=CPUComputeSpec)
    lockfile: GitFileRef
    python_environment: PythonEnvironmentSpec


EnvironmentSpec = Annotated[
    GCEEnvironmentSpec | LocalEnvironmentSpec,
    Field(discriminator="kind"),
]
```

`RunSpec.environment` supplies the shared `EnvironmentSpec`. A stage-level
`BaseSpec.environment` supplies the selected stage's environment override.
Distribution names are unique and sorted after PyPA normalization. The
resolved Python version and distribution tuple equal the selected
`PythonEnvironmentSpec`.

### Run-wide reproducibility controls

```python
class TorchDeterminismSpec(ProtocolModel):
    deterministic_algorithms: bool
    deterministic_warn_only: bool
    cudnn_deterministic: bool
    cudnn_benchmark: bool
    cublas_workspace_config: Literal[":16:8", ":4096:8"] | None


class TorchPrecisionSpec(ProtocolModel):
    float32_matmul_precision: Literal["highest", "high", "medium"]
    cudnn_allow_tf32: bool
    autocast_enabled: bool
    autocast_dtype: Literal["float16", "bfloat16"] | None


class DataLoaderConfiguration(ProtocolModel):
    workers: int = Field(ge=0)
    prefetch_factor: int | None = Field(default=None, ge=1)
    persistent_workers: bool = False
    in_order: Literal[True] = True


class ParallelismSpec(ProtocolModel):
    process_count: int = Field(ge=1)
    torch_intraop_threads: int = Field(ge=1)
    torch_interop_threads: int = Field(ge=1)
    dataloader: DataLoaderConfiguration


class NumPyRandomnessSpec(ProtocolModel):
    generators: dict[HumanId, Literal["PCG64"]] = Field(default_factory=dict)
    capture_legacy_global: bool = False


class ReproducibilitySpec(ProtocolModel):
    determinism: TorchDeterminismSpec
    precision: TorchPrecisionSpec
    parallelism: ParallelismSpec
    numpy_randomness: NumPyRandomnessSpec
```

`TorchPrecisionSpec.autocast_dtype` is present exactly when
`autocast_enabled` is true.

The global seed occurs once in `RunSpec.seed`. `ReproducibilitySpec` records
the remaining numerical controls shared by every stage.
`NumPyRandomnessSpec.generators` names each PCG64 generator initialized from
that seed. `capture_legacy_global` states whether execution also uses and
captures NumPy's global MT19937 generator.

### Realized environment and runtime state

```python
class ResolvedGitFileRef(ResolvedFileRef):
    stored_at: GitFileRef


class ResolvedGCEEnvironment(ProtocolModel):
    kind: Literal["gce"] = "gce"
    provisioning: GCEProvisioningRef
    machine_type: NonEmptyStr
    compute: ComputeSpec
    lockfile: ResolvedGitFileRef
    python_environment: PythonEnvironmentSpec


class ResolvedLocalEnvironment(ProtocolModel):
    kind: Literal["local"] = "local"
    compute: ComputeSpec = Field(default_factory=CPUComputeSpec)
    lockfile: ResolvedGitFileRef
    python_environment: PythonEnvironmentSpec


ResolvedEnvironment = Annotated[
    ResolvedGCEEnvironment | ResolvedLocalEnvironment,
    Field(discriminator="kind"),
]


class GCEHostContext(ProtocolModel):
    provider: Literal["gce"] = "gce"
    project_id: NonEmptyStr
    provisioning: GCEProvisioningRef
    machine_type: NonEmptyStr
    zone: NonEmptyStr
    guest_os_name: NonEmptyStr
    guest_os_version: NonEmptyStr
    kernel_release: NonEmptyStr


class LocalHostContext(ProtocolModel):
    provider: Literal["local"] = "local"
    operating_system: NonEmptyStr
    release: NonEmptyStr
    architecture: NonEmptyStr


HostContext = Annotated[
    GCEHostContext | LocalHostContext,
    Field(discriminator="provider"),
]


class CPUContext(ProtocolModel):
    architecture: NonEmptyStr
    model: NonEmptyStr
    instruction_features: tuple[NonEmptyStr, ...] = Field(min_length=1)


class CPUBackendContext(ProtocolModel):
    kind: Literal["cpu"] = "cpu"
    device: Literal["cpu"] = "cpu"


class CUDADeviceContext(ProtocolModel):
    ordinal: int = Field(ge=0)
    model: NonEmptyStr
    compute_capability_major: int = Field(ge=0)
    compute_capability_minor: int = Field(ge=0)
    memory_bytes: int = Field(gt=0)


class CUDABackendContext(ProtocolModel):
    kind: Literal["cuda"] = "cuda"
    gpu_devices: tuple[CUDADeviceContext, ...] = Field(min_length=1)
    nvidia_driver_version: NonEmptyStr
    pytorch_cuda_version: NonEmptyStr
    cudnn_version: NonEmptyStr


ComputeBackendContext = Annotated[
    CPUBackendContext | CUDABackendContext,
    Field(discriminator="kind"),
]


class NativeLibraryContext(ProtocolModel):
    implementation: NonEmptyStr
    version: NonEmptyStr


class NativeThreadPoolContext(NativeLibraryContext):
    threads: int = Field(ge=1)


class NumericalRuntimeContext(ProtocolModel):
    python_version: NonEmptyStr
    pytorch_version: NonEmptyStr
    numpy_version: NonEmptyStr
    blas: NativeLibraryContext
    lapack: NativeLibraryContext
    native_thread_pools: tuple[NativeThreadPoolContext, ...]


class ExecutionContext(ProtocolModel):
    host: HostContext
    cpu: CPUContext
    backend: ComputeBackendContext
    numerical_runtime: NumericalRuntimeContext


GeneratorFamily = Literal[
    "python",
    "numpy_generator",
    "numpy_legacy",
    "torch_cpu",
    "torch_cuda",
]


class GeneratorInitializationReceipt(ProtocolModel):
    family: GeneratorFamily
    seed: RNGSeed
    name: HumanId | None = None
    device_index: int | None = Field(default=None, ge=0)
    state_sha256: SHA256


StartupVariable = Literal[
    "CUBLAS_WORKSPACE_CONFIG",
    "CUDA_VISIBLE_DEVICES",
    "MKL_NUM_THREADS",
    "OMP_NUM_THREADS",
    "PYTHONHASHSEED",
]


class ProcessStartupReceipt(ProtocolModel):
    environment: dict[StartupVariable, str]
    reproducibility: ReproducibilitySpec
    generators: tuple[GeneratorInitializationReceipt, ...]
```

CUDA device ordinals are unique within one `CUDABackendContext`.

For stage $\omega_j$, let $\widetilde{h}_j$ denote its resolved environment and
let $x_j$ denote its execution context. The realized runtime state recorded by
the protocol is:

```math
e_j
=
\left(
\widetilde{h}_j,
x_j
\right).
```

The verifier establishes $e_j\in E_{q,j}$ through these equalities:

```text
ResolvedGCEEnvironment.provisioning
== selected GCEEnvironmentSpec.provisioning

ResolvedGCEEnvironment.python_environment
== selected GCEEnvironmentSpec.python_environment

ResolvedGCEEnvironment.machine_type
== selected GCEEnvironmentSpec.machine_type
== ExecutionContext.host.machine_type

ResolvedGCEEnvironment.compute
== selected GCEEnvironmentSpec.compute

ResolvedGCEEnvironment.lockfile.stored_at
== selected GCEEnvironmentSpec.lockfile

ResolvedLocalEnvironment.compute
== selected LocalEnvironmentSpec.compute

ResolvedLocalEnvironment.python_environment
== selected LocalEnvironmentSpec.python_environment

ResolvedLocalEnvironment.lockfile.stored_at
== selected LocalEnvironmentSpec.lockfile

ProcessStartupReceipt.reproducibility
== RunSpec.reproducibility

set(receipt.seed for receipt in ProcessStartupReceipt.generators)
== {RunSpec.seed}

StageContextBinding.numpy_generator_names
== tuple(sorted(RunSpec.reproducibility.numpy_randomness.generators))

set(
    receipt.name
    for receipt in ProcessStartupReceipt.generators
    if receipt.family == "numpy_generator"
)
== set(StageContextBinding.numpy_generator_names)
```

Generator receipts are unique by family, name, and device index. The named
NumPy receipts equal `NumPyRandomnessSpec.generators`; the optional legacy
receipt follows `capture_legacy_global`. A CUDA stage records one `torch_cuda`
receipt for each exposed device. A CPU stage records Python, configured NumPy,
and `torch_cpu` receipts. `ProcessStartupReceipt.environment` equals the
canonical allowlisted startup mapping derived for the selected stage.
`name` is present exactly for `numpy_generator`, and `device_index` is present
exactly for `torch_cuda`.

The child retains each configured `numpy.random.Generator` created while
applying the run controls. Immediately before stage invocation, the child
places those objects in the read-only `Context.numpy_generators` mapping.
The mapping keys equal `StageContextBinding.numpy_generator_names`. The
corresponding `GeneratorInitializationReceipt` values contain the states hashed
immediately after generator initialization. The child constructs the receipts
and runtime mapping from one name-to-object mapping. A key mismatch terminates
startup before callable invocation.

The executor records `ResolvedEnvironment`, `ExecutionContext`, and
`ProcessStartupReceipt`. The verifier establishes the requested-to-realized
equalities shown above.

For a CPU environment, `ExecutionContext.backend.kind` is `cpu`. For a CUDA
environment, the backend is `cuda`, its number of devices equals
`CUDAComputeSpec.count`, and each device model equals `CUDAComputeSpec.model`.

Every resolved environment records the exact Python environment and verified
lockfile reference. A resolved GCE environment also records the immutable
provisioning-source identity. `ExecutionContext` records the runtime library
implementations and versions used by the stage.

### Parameterized-stage source and invocation

`ResolvedParameterizedSpec.source` identifies the file containing the callable
selected by `ParameterizedSpec.implementation` at `RunSpec.source`:

```text
ResolvedParameterizedSpec.source.stored_at.repository
== RunSpec.source.repository

ResolvedParameterizedSpec.source.stored_at.commit
== RunSpec.source.commit

ResolvedParameterizedSpec.source.stored_at.path
== ResolvedParameterizedSpec.spec.implementation.path

ResolvedParameterizedSpec.source.sha256
== ResolvedParameterizedSpec.spec.implementation.sha256

ResolvedParameterizedSpec.source.bytes
== ResolvedParameterizedSpec.spec.implementation.bytes
```

The process-startup layer records the actual child-process command in
`ResolvedParameterizedSpec.command`. The stage worker imports the selected symbol and
passes it the typed context reconstructed from the coordinator-supplied
`StageContextBinding`. After the child terminates, the coordinator places that
same binding in `StageInvocationReceipt.context`.

```text
ParameterizedSpec.implementation
-> exact callable

StageContextBinding
-> exact run, attempt, stage, parameters, inputs, artifacts, metrics, and named generators

exact callable(Context)
-> one recorded invocation
```

## 16. Experiment, variant, replicate, and measurement records

### Experiment and replicate declarations

```python
class FactorSpec(ProtocolModel):
    factor_id: FactorId
    levels: tuple[LevelId, ...] = Field(min_length=2)


class ReplicateSpec(ProtocolModel):
    replicate_id: ReplicateId
    seed: RNGSeed


MetricKind = Literal["training", "evaluation", "diagnostic"]
MetricMode = Literal["stateful", "stateless"]


class FloatComparator(ProtocolModel):
    mode: Literal["exact", "absolute", "relative"] = "exact"
    tolerance: float = Field(default=0.0, ge=0, allow_inf_nan=False)


class MetricImplementationRef(ProtocolModel):
    path: PythonRepoRelPath
    symbol: PythonSymbol
    sha256: SHA256
    bytes: int = Field(gt=0)


class MetricDependency(ProtocolModel):
    source: Literal["input", "artifact"]
    name: HumanId
    required_data_role: DataRole


class MetricSpec(ProtocolModel):
    schema_version: Literal[1] = 1
    metric_id: MetricId
    kind: MetricKind
    implementation: MetricImplementationRef
    params: viper.parameters.Metric
    mode: MetricMode
    dependencies: tuple[MetricDependency, ...] = ()
    comparator: FloatComparator | None = None


class ResolvedMetricDependency(ProtocolModel):
    dependency: MetricDependency
    files: tuple[ResolvedFileRef, ...] = Field(min_length=1)


class MetricHandle:
    def update(self, *args: Any, **kwargs: Any) -> None:
        ...

    def record(
        self,
        *args: Any,
        epoch: int | None = None,
        step: int | None = None,
        **kwargs: Any,
    ) -> Measurement:
        ...


class ExperimentSpec(ProtocolModel):
    schema_version: Literal[1] = 1
    experiment_id: ExperimentId
    factors: tuple[FactorSpec, ...]
    variant_ids: tuple[VariantId, ...] = Field(min_length=1)
    replicates: tuple[ReplicateSpec, ...] = Field(min_length=1)
    metrics: tuple[MetricSpec, ...]
```

Factor IDs are unique. Level IDs are unique within each factor. Variant IDs,
replicate IDs, replicate seeds, and `MetricSpec.metric_id` values are unique
within the experiment. Each implementation reference identifies the exact
metric file and top-level symbol within `RunSpec.source`.

`mode="stateful"` selects a `StatefulMetric` class. The class accumulates
observations through `update()` and returns its current value from `compute()`.
`mode="stateless"` selects a function that computes each value directly from
its current arguments or declared files.

A stateless metric with dependencies and a comparator executes in a dedicated
worker after the stage completes. Verification launches a second worker with
the same immutable dependencies. A stage-recorded metric has an empty
dependency set, omits the comparator, and enters the stage through a
runner-owned `MetricHandle`. Evaluation metrics are stateless and declare the
files needed for recomputation.

An exact comparator has zero tolerance. An absolute or relative comparator has
a positive tolerance.

The experiment file and its variant files occur at:

```text
experiments/<experiment_id>/spec.yaml
experiments/<experiment_id>/variants/<variant_id>.spec.yaml
```

`RunSpec.source` identifies the exact repository revision containing these
files.

### Variant declaration

```python
class BuildVariantStageParams(ProtocolModel):
    kind: Literal["build"] = "build"
    stage_id: StageId
    params: viper.params.Build


class EmbedVariantStageParams(ProtocolModel):
    kind: Literal["embed"] = "embed"
    stage_id: StageId
    params: viper.params.Embed


class TrainVariantStageParams(ProtocolModel):
    kind: Literal["train"] = "train"
    stage_id: StageId
    params: viper.params.Train


class EvalVariantStageParams(ProtocolModel):
    kind: Literal["eval"] = "eval"
    stage_id: StageId
    params: viper.params.Eval


VariantStageParams = Annotated[
    BuildVariantStageParams
    | EmbedVariantStageParams
    | TrainVariantStageParams
    | EvalVariantStageParams,
    Field(discriminator="kind"),
]


class VariantSpec(ProtocolModel):
    schema_version: Literal[1] = 1
    experiment_id: ExperimentId
    variant_id: VariantId
    levels: dict[FactorId, LevelId]
    stage_params: tuple[VariantStageParams, ...] = Field(min_length=1)
```

The factor names in `VariantSpec.levels` equal the factor names in the selected
`ExperimentSpec`. Each selected level belongs to its factor's permitted level
set. Stage IDs are unique within `VariantSpec.stage_params`.

The verifier requires:

```text
RunSpec.experiment_id
== ExperimentSpec.experiment_id
== VariantSpec.experiment_id

RunSpec.variant_id
== VariantSpec.variant_id

RunSpec.variant_id
in ExperimentSpec.variant_ids

set(VariantSpec.stage_params.stage_id)
== set(stage IDs whose loaded stage specs contain params)

VariantSpec.stage_params[stage_id].params
== loaded stage spec.params
```

The selected level IDs state the experimental assignment. The typed parameter
records state how the selected variant is implemented by its stage specs.

### Seed authority

`RunSpec.replicate_id` selects one `ReplicateSpec`. Its seed is the run's global
seed:

```text
RunSpec.seed
== selected ReplicateSpec.seed
== ζq
```

The executor applies this value before every stage. Section 15 defines the
corresponding `ProcessStartupReceipt.generators` equalities.

### Measurements

```python
class Measurement(ProtocolModel):
    run_id: RunId
    attempt_id: int = Field(ge=1)
    stage_id: StageId
    metric_id: MetricId
    value: float = Field(allow_inf_nan=False)
    measured_at: AwareDatetime
    epoch: int | None = Field(default=None, ge=0)
    step: int | None = Field(default=None, ge=0)


class MetricExecutionReceipt(ProtocolModel):
    schema_version: Literal[1] = 1
    run_id: RunId
    attempt_id: int = Field(ge=1)
    metric_id: MetricId
    stage_id: StageId
    purpose: Literal["measurement", "verification"]
    implementation: MetricImplementationRef
    params: viper.parameters.Metric
    dependencies: tuple[ResolvedMetricDependency, ...] = Field(min_length=1)
    startup: ProcessStartupReceipt
    execution_context: ExecutionContext
    python_environment: PythonEnvironmentSpec
    value: float = Field(allow_inf_nan=False)
    started_at: AwareDatetime
    completed_at: AwareDatetime
    outcome: Literal["succeeded"] = "succeeded"


class MetricVerificationReceipt(ProtocolModel):
    schema_version: Literal[1] = 1
    metric_id: MetricId
    stage_id: StageId
    measurement: Measurement
    production: MetricExecutionReceipt
    recomputation: MetricExecutionReceipt
    comparator: FloatComparator
    passed: bool
    completed_at: AwareDatetime
```

Each file in `RunAttempt.measurement_files` contains `Measurement` rows. For
every row, the verifier requires:

```text
Measurement.run_id
== RunSpec.run_id

Measurement.attempt_id
== containing RunAttempt.attempt_id

Measurement.stage_id
in completed stage IDs of that attempt

Measurement.metric_id
in ExperimentSpec.metrics.metric_id

Measurement.metric_id
in named stage spec.metric_ids

RunAttempt.started_at
<= Measurement.measured_at
<= RunAttempt.completed_at

Measurement.measured_at
<= named ResolvedBaseSpec.completed_at
```

Measurement JSON objects have unique field names. A successful evaluation stage
records exactly one row for each metric in `EvaluateSpec.metric_ids`.

Each recomputed metric produces one `MetricVerificationReceipt`. Its
`production` receipt records the worker that created the measurement. Its
`recomputation` receipt records the independent verification worker. Both
receipts contain the exact implementation, parameters, resolved dependencies,
startup evidence, observed execution context, value, and execution interval.
The coordinator supplies the active run, attempt, stage, and metric identities
to both workers. The worker owns every receipt identity field. Metric code
returns the scalar value.

The embedded measurement equals one row in the containing attempt's
measurement file. Both execution receipts contain run, attempt, stage, and
metric identities equal to the embedded measurement. The production value
equals the measurement value. The recomputation value satisfies `comparator`
against the measurement value. The containing attempt identifies the immutable
receipt file through `RunAttempt.metric_verification_files`.

```text
MetricVerificationReceipt.production.run_id
== MetricVerificationReceipt.recomputation.run_id
== MetricVerificationReceipt.measurement.run_id

MetricVerificationReceipt.production.attempt_id
== MetricVerificationReceipt.recomputation.attempt_id
== MetricVerificationReceipt.measurement.attempt_id

MetricVerificationReceipt.production.stage_id
== MetricVerificationReceipt.recomputation.stage_id
== MetricVerificationReceipt.measurement.stage_id

MetricVerificationReceipt.production.metric_id
== MetricVerificationReceipt.recomputation.metric_id
== MetricVerificationReceipt.measurement.metric_id
```

## 17. Concrete stage records

### Planned stage inputs

```python
class HttpOrigin(ProtocolModel):
    scheme: Literal["http", "https"]
    host: NonEmptyStr
    port: int = Field(ge=1, le=65535)


class EnvironmentSecretRef(ProtocolModel):
    kind: Literal["environment"] = "environment"
    variable: NonEmptyStr
    header: HttpHeaderName
    prefix: str = ""
    authorized_origins: frozenset[HttpOrigin] = Field(min_length=1)


class HttpRequestSpec(ProtocolModel):
    kind: Literal["http"] = "http"
    method: Literal["GET"] = "GET"
    url: HttpUrl
    headers: dict[HttpHeaderName, NonEmptyStr] = Field(default_factory=dict)
    version: NonEmptyStr
    expected_body_sha256: SHA256
    expected_body_bytes: int = Field(gt=0)
    credentials: EnvironmentSecretRef | None = None


class HttpRetrievalPolicy(ProtocolModel):
    allowed_schemes: frozenset[Literal["http", "https"]] = Field(min_length=1)
    allowed_hosts: frozenset[NonEmptyStr] = Field(min_length=1)
    allowed_ports: frozenset[
        Annotated[int, Field(ge=1, le=65535)]
    ] = Field(min_length=1)
    accepted_statuses: frozenset[
        Annotated[int, Field(ge=100, le=599)]
    ] = frozenset({200})
    max_redirects: int = Field(ge=0)
    max_body_bytes: int = Field(gt=0)
    timeout_seconds: float = Field(gt=0, allow_inf_nan=False)


class HttpImplementationRef(ProtocolModel):
    path: PythonRepoRelPath
    symbol: PythonSymbol
    sha256: SHA256
    bytes: int = Field(gt=0)


class ExternalExecutableSpec(ProtocolModel):
    executable_id: HumanId
    command: NonEmptyStr
    sha256: SHA256
    bytes: int = Field(gt=0)


class BuiltinHttpImplementationSpec(ProtocolModel):
    kind: Literal["builtin"] = "builtin"
    id: Literal["httpx"] = "httpx"


class ProjectHttpImplementationSpec(ProtocolModel):
    kind: Literal["project"] = "project"
    id: HumanId
    implementation: HttpImplementationRef
    parameter_model: ParameterModelRef
    params: viper.parameters.Http
    executables: tuple[ExternalExecutableSpec, ...] = ()


HttpImplementationSpec = Annotated[
    BuiltinHttpImplementationSpec | ProjectHttpImplementationSpec,
    Field(discriminator="kind"),
]


InputRef = Annotated[
    ExternalInputRef | StoredInputRef | FutureInputRef,
    Field(discriminator="kind"),
]
```

A download stage consumes one or more frozen HTTP requests. Build, embed, and
train stages consume stored or same-run artifacts.

`EnvironmentSecretRef` places the value of its named environment variable in
the selected request header after applying the public prefix. The persisted
request retains the reference and redacts the value. `HttpRequestSpec.headers`
excludes the selected secret header. The credential can reach only the origins
listed in `authorized_origins`. `HttpRetrievalPolicy` constrains each frozen
request and redirect target. Host matching uses normalized, lower-case names
and exact equality. Body size and timeout apply to each retrieval.

Origin comparison lowercases the scheme and host, removes a trailing DNS dot,
and uses the scheme's default port when a URL omits it. Each `HttpOrigin`
stores the resulting effective port.

`expected_body_sha256` and `expected_body_bytes` fix the bytes selected by the
experimental run plan. Dynamic discovery and scraping publish observed content
before a later experimental run selects it.

`BuiltinHttpImplementationSpec` selects the HTTPX implementation shipped with
VIPER. `ProjectHttpImplementationSpec` selects one decorated callable from the
project source and binds its project-defined parameter class, parameter values,
and external executable requirements.

### Stage specifications

```python
ParamsT = TypeVar("ParamsT", bound=viper.parameters.ParameterSet)


@dataclass(frozen=True)
class Context(Generic[ParamsT]):
    run_id: RunId
    attempt_id: int
    stage_id: StageId
    params: ParamsT
    inputs: Mapping[InputName, Path]
    artifacts: Mapping[ArtifactName, Path]
    metrics: Mapping[MetricId, MetricHandle]
    numpy_generators: Mapping[HumanId, np.random.Generator]


class ParameterizedSpec(BaseSpec):
    implementation: StageImplementationRef
    parameter_model: ParameterModelRef


class DownloadSpec(BaseSpec):
    kind: Literal["download"] = "download"
    inputs: dict[InputName, HttpRequestSpec] = Field(min_length=1)
    http: HttpImplementationSpec = Field(
        default_factory=BuiltinHttpImplementationSpec
    )
    policy: HttpRetrievalPolicy


class ObservedHttpResponse(ProtocolModel):
    response_url: HttpUrl
    status: int = Field(ge=100, le=599)
    response_headers: dict[HttpHeaderName, str]


HttpParamsT = TypeVar(
    "HttpParamsT",
    bound=viper.parameters.Http,
)


@dataclass(frozen=True)
class RuntimeHttpCredential:
    header: HttpHeaderName
    prefix: str
    value: str


@dataclass(frozen=True)
class HttpContext(Generic[HttpParamsT]):
    request: HttpRequestSpec
    credential: RuntimeHttpCredential | None
    workspace: Path
    destination: Path
    policy: HttpRetrievalPolicy
    params: HttpParamsT
    executables: Mapping[HumanId, Path]


@dataclass(frozen=True)
class HttpResult:
    body: Path
    response: ObservedHttpResponse


class InternalSpec(ParameterizedSpec):
    inputs: dict[InputName, InputRef] = Field(min_length=1)


class BuildSpec(InternalSpec):
    kind: Literal["build"] = "build"
    params: viper.parameters.Build


class EmbedSpec(InternalSpec):
    kind: Literal["embed"] = "embed"
    params: viper.parameters.Embed


class TrainSpec(InternalSpec):
    kind: Literal["train"] = "train"
    params: viper.parameters.Train


class EvaluateSpec(InternalSpec):
    kind: Literal["evaluate"] = "evaluate"
    evaluation_id: EvaluationId
    metric_ids: tuple[MetricId, ...] = Field(min_length=1)
    split_inputs: tuple[InputName, ...] = Field(min_length=1)
    params: viper.parameters.Evaluate


ParameterizedStageSpec = BuildSpec | EmbedSpec | TrainSpec | EvaluateSpec


Spec = Annotated[
    DownloadSpec | ParameterizedStageSpec,
    Field(discriminator="kind"),
]
```

`StageImplementationRef` identifies a project stage callable. The runner validates
`ParameterizedSpec.params` through `ParameterModelRef`, constructs one
`Context`, and passes it as the callable's sole argument:

```text
stage implementation reference
-> exact callable

stage spec + active attempt
-> typed Context

exact callable(Context)
-> StageInvocationReceipt
```

The runtime context contains absolute attempt-workspace paths and the named
NumPy generator objects initialized by the child. Its persisted
`StageContextBinding` contains the canonical repository-relative paths, the
metric IDs bound to runner-owned handles, and the sorted generator names.
Download stages run inside the attempt process and therefore do not create a
`StageContextBinding` or `StageInvocationReceipt`.

`http()` from `viper.http` decorates one project HTTP callable. Freezing
resolves its repository-relative path, symbol, SHA-256, byte count, parameter
class, and parameter values into `ProjectHttpImplementationSpec`. During
execution, the runner constructs one `HttpContext`, invokes the selected HTTP
implementation, hashes the returned body, and constructs
`ResolvedHttpRetrieval`.

The runner assigns each `HttpContext` a dedicated retrieval workspace and an
exact destination within it. A selected implementation may use the workspace
for temporary transfer files and returns only after the completed body exists
at the destination.

The runner publishes each verified response directly as the same-named
single-file download artifact. The experimental plan fixes one expected body
identity for each request. Dynamic acquisition publishes observed content
before a later experimental run selects it.

Each core parameter class preserves a versioned JSON mapping. Every stage
selects a project-owned Pydantic subclass through `parameter_model`.
The subclass may declare fields, types, defaults, constraints, and
cross-field validators for that stage implementation.

`ParameterModelRef` binds the class to one repository-relative file, top-level
class symbol, SHA-256 digest, and byte count. `RunSpec.source` supplies the
repository and commit. Together, these values identify the exact validator.

VIPER verifies the local file against the selected source commit and invokes
the class in a dedicated worker during plan freezing, preflight, and stage
execution. Run verification retrieves the same source bytes and checks their
identity and declared class symbol. The selected `VariantSpec` and stage spec
must contain the same serialized parameter mapping. Validation uses strict
types, and the class output must equal that frozen mapping. Every effective
default therefore appears explicitly in `params`.

Within one stage spec:

1. Input names are unique.
2. Artifact names are unique.
3. Stored-input paths are pairwise non-overlapping.
4. Artifact roots are pairwise non-overlapping.
5. Input paths, artifact roots, and `ParameterizedSpec.implementation.path` are pairwise
   non-overlapping.
6. `parameters` and `resume_state` occur only as training-stage
   artifacts.
7. `predictions` occurs only as an evaluation-stage artifact.

After resolving same-run inputs, the external verifier applies the same path
checks to their materialized paths. Same-run inputs consumed by one stage are
pairwise non-overlapping. It also requires every artifact role to be at least
as restrictive as every input role and permits a training stage to consume
only `training` and `validation` inputs.

### Resolved stage inputs

```python
ResolvedInputRef = Annotated[
    ResolvedStoredInputRef | ResolvedFutureInputRef | ResolvedExternalInputRef,
    Field(discriminator="kind"),
]
```

The resolved input-name set equals the planned input-name set. Each resolved
input has the same discriminated kind as its planned input. Section 14 defines
the pointer equality for stored inputs and the producer equality for same-run
inputs. Section 14 also defines the captured source and file identity for
external inputs.

### Resolved stage specifications

```python
class ResolvedExternalExecutable(ProtocolModel):
    spec: ExternalExecutableSpec
    path: Path


class ResolvedHttpImplementation(ProtocolModel):
    spec: HttpImplementationSpec
    external_executables: tuple[ResolvedExternalExecutable, ...] = ()


class ResolvedHttpRetrieval(ProtocolModel):
    input_name: InputName
    request: HttpRequestSpec
    http: ResolvedHttpImplementation
    response: ObservedHttpResponse
    body: SnapshotFileRef
    started_at: AwareDatetime
    completed_at: AwareDatetime


class ResolvedDownloadSpec(ResolvedBaseSpec):
    kind: Literal["download"] = "download"
    spec: DownloadSpec
    retrievals: dict[InputName, ResolvedHttpRetrieval]


class ResolvedParameterizedSpec(ResolvedBaseSpec):
    spec: ParameterizedSpec
    source: ResolvedGitFileRef
    startup: ProcessStartupReceipt
    invocation: ResolvedStageInvocationRef
    command: tuple[str, ...] = Field(min_length=1)


class ResolvedInternalSpec(ResolvedParameterizedSpec):
    spec: InternalSpec
    inputs: dict[InputName, ResolvedInputRef]


class ResolvedBuildSpec(ResolvedInternalSpec):
    kind: Literal["build"] = "build"
    spec: BuildSpec


class ResolvedEmbedSpec(ResolvedInternalSpec):
    kind: Literal["embed"] = "embed"
    spec: EmbedSpec


class ResolvedTrainSpec(ResolvedInternalSpec):
    kind: Literal["train"] = "train"
    spec: TrainSpec


class ResolvedEvaluateSpec(ResolvedInternalSpec):
    kind: Literal["evaluate"] = "evaluate"
    spec: EvaluateSpec


ResolvedSpec = Annotated[
    ResolvedDownloadSpec
    | ResolvedBuildSpec
    | ResolvedEmbedSpec
    | ResolvedTrainSpec
    | ResolvedEvaluateSpec,
    Field(discriminator="kind"),
]
```

For each download input:

```text
keys(ResolvedDownloadSpec.retrievals)
== keys(ResolvedDownloadSpec.spec.inputs)

ResolvedHttpRetrieval.request
== ResolvedDownloadSpec.spec.inputs[ResolvedHttpRetrieval.input_name]

ResolvedHttpRetrieval.http.spec
== ResolvedDownloadSpec.spec.http
```

Each retrieval interval lies within the containing attempt and precedes stage
completion. `ResolvedHttpRetrieval.body` and the same-named
`ResolvedSingleFileArtifact.file` contain the same `SnapshotFileRef`. A
download artifact can then serve as a same-run or stored input selected by a
later stage.

Redirects and segmented range requests remain internal to one HTTP
invocation. Dynamic pagination and scraping belong to discovery work that
publishes immutable files before an experimental plan selects them.

VIPER 0.1 trusts project-owned stage source identified by `RunSpec.source` not
to bypass the runner-owned download path. A future confinement contract will
restrict direct outbound network access by project code.

For every resolved stage:

```text
ResolvedStageRef.resolved_spec
→ loads the matching ResolvedSpec subtype

ResolvedBaseSpec.spec
== stage spec identified by the matching RunStageRef

keys(ResolvedBaseSpec.spec.artifacts)
== keys(ResolvedBaseSpec.artifacts)
```

## 18. Training checkpoint mapping

The terminal checkpoint of every training stage is represented by two reserved
artifacts:

```python
PARAMETERS: ArtifactName = "parameters"
RESUME_STATE: ArtifactName = "resume_state"
```

The first artifact reconstructs $\theta_k^{(N_k)}$. The second reconstructs:

```math
\left(
o_k^{(N_k)},
r_k^{(N_k)},
b_k^{(N_k)}
\right).
```

Together they reconstruct the single terminal checkpoint $s_k^{(N_k)}$.
Additional artifact names identify auxiliary outputs of the same stage.

### Training request

`TrainSpec.artifacts` must contain both reserved names exactly once. A
`TrainSpec` validator enforces:

```python
{
    PARAMETERS,
    RESUME_STATE,
} <= set(train_spec.artifacts)
```

Each name maps to one `SingleFileArtifactSpec` or `BundleArtifactSpec`. The
artifact loaders define how their verified files reconstruct the two checkpoint
values.

A training stage that continues from an earlier checkpoint declares two
reserved inputs:

```python
PARAMETERS_INPUT: InputName = "parameters"
RESUME_STATE_INPUT: InputName = "resume_state"
```

The two inputs must occur together and must have the same input kind. For
same-run resumption, they satisfy:

```text
TrainSpec.inputs[parameters]
├── producer_stage_id = producer stage ID
└── name = parameters

TrainSpec.inputs[resume_state]
├── producer_stage_id = producer stage ID
└── name = resume_state
```

Their common `producer_stage_id` identifies the single checkpoint-producing
stage. Stored checkpoint inputs use `inputs/models`. A fresh training stage
omits both reserved inputs.

### Resolved stage result

The `RunStageRef` at position $k$ identifies the exact `TrainSpec` $\omega_k$.
The corresponding successful stage result satisfies:

```text
ResolvedStageRef.stage_id
==
RunStageRef.stage_id

ResolvedTrainSpec.spec
==
TrainSpec loaded through RunStageRef.spec
```

The successful execution of $\omega_k$ publishes one stage-result snapshot:

```text
ResolvedStageRef
├── stage_id
├── snapshot
└── resolved_spec
    └── loads ResolvedTrainSpec
        └── artifacts
            ├── parameters
            ├── resume_state
            └── auxiliary artifacts, when declared
```

The resolved artifact names satisfy:

```text
keys(ResolvedTrainSpec.spec.artifacts)
==
keys(ResolvedTrainSpec.artifacts)
```

`ResolvedStageRef.snapshot` identifies the immutable commit containing the
resolved stage spec, every file reached through its resolved artifacts, and
every response body reached through a download stage's resolved retrievals.
The executor adds the stage to `RunAttempt.resolved_stages` after that complete
snapshot has been published and verified.

### Continuation

For same-run resumption from $\omega_k$ to $\omega_\ell$, the external
verifier requires $k<\ell$ and:

```text
ResolvedTrainSpec.inputs[parameters].producer
==
ResolvedTrainSpec.inputs[resume_state].producer
==
ResolvedStageRef for ωₖ
```

The verifier retrieves the producer's resolved spec, selects the two reserved
artifacts, verifies every file and loader identity, and invokes both loaders.
Their returned values define:

```math
L_{k,a_\theta}
\left(
F_k(a_\theta)
\right)
=
\theta_k^{(N_k)},
```

and:

```math
L_{k,a_c}
\left(
F_k(a_c)
\right)
=
\left(
o_k^{(N_k)},
r_k^{(N_k)},
b_k^{(N_k)}
\right).
```

The continuing stage receives the two verified artifact paths through
`Context.inputs`. Its frozen project implementation restores the initial
state of $\omega_\ell$ from the loader values. A project that claims exact
resumption establishes:

```math
s_\ell^{(0)}
=
s_k^{(N_k)}.
```

For stored resumption from an earlier run, both `ArtifactPointer` records
must select the same resolved run, successful attempt, and producer stage. One
pointer selects `parameters`; the other selects `resume_state`.

### Estimator selection

`RunSpec.estimator` must select the `parameters` artifact of a training
stage. The verifier loads the selected producer spec, confirms its `train`
kind, and verifies the artifact files and loader identity. The replay executor
invokes the loader and obtains:

```text
RunSpec.estimator.artifact_name
==
parameters

RunSpec.estimator.stage_id
==
producer ResolvedStageRef.stage_id
```

```math
\widehat{\theta}_q
=
\theta_{k_*}^{(N_{k_*})}.
```

The enforcement path is:

```text
TrainSpec validator
└── enforces one reserved checkpoint pair

ResolvedTrainSpec validator
└── enforces equality between declared and resolved artifact names

external verifier
├── verifies both artifacts belong to one producer snapshot
├── verifies every referenced file
├── verifies both artifact-loader identities
├── verifies `resume_state` against its protocol-owned schema
└── verifies the resume-input and estimator selectors

stage invocation
└── delivers both verified paths to the frozen continuation callable

parity check
└── project acceptance compares the resumed and uninterrupted terminal states
```

## 19. Evaluation stage

Evaluation applies a fitted prediction function to fixed evaluation inputs. It
uses the same stage, input, artifact, snapshot, measurement, and runtime records
defined above.

The reserved names are:

```python
PARAMETERS_INPUT: InputName = "parameters"
EVALUATION_DATASET_INPUT: InputName = "evaluation_dataset"
PREDICTIONS: ArtifactName = "predictions"
```

An `EvaluateSpec` satisfies:

```text
parameters
in EvaluateSpec.inputs

evaluation_dataset
in EvaluateSpec.inputs

set(EvaluateSpec.split_inputs)
is a subset of
set(EvaluateSpec.inputs)

predictions
in EvaluateSpec.artifacts
```

The split-input names are unique and differ from `parameters` and
`evaluation_dataset`. The evaluation dataset and every split input are
`StoredInputRef` records. The model, dataset, and split pointer paths use
`inputs/models`, `inputs/datasets`, and `inputs/benchmarks`, respectively.
Their data-use roles follow Section 14. The evaluation dataset and every split
have one shared role. That role is `evaluation` for an ordinary evaluation and
`benchmark` for an evaluation selected by a `BenchmarkSpec`. Every declared
evaluation artifact has the same role.

The `parameters` input is a `FutureInputRef` or `StoredInputRef`. A
same-run model input selects:

```text
FutureInputRef.name
== parameters
```

A stored model input resolves through its `ArtifactPointer` to a
`parameters` artifact. The evaluation dataset and every declared split
are stored inputs selected before execution. The parameters artifact has role
`training` or `validation`.

The executor materializes every evaluation input as read-only. Its artifact
mapping contains `predictions` and may contain additional evaluation outputs.

```text
parameters artifact
+ evaluation_dataset artifact
+ split artifacts
        │
        ▼
    EvaluateSpec
        │
        ├── predictions artifact
        └── Measurement rows
```

`EvaluateSpec.metric_ids` contains unique metric IDs and satisfies:

```text
set(EvaluateSpec.metric_ids)
is a subset of
set(ExperimentSpec.metrics.metric_id)
```

Every measurement produced by the evaluation stage uses one of those metric
IDs. The `predictions` declaration may be a file or bundle beneath:

```text
artifacts/evaluations/<evaluation_id>/
```

Its declared loader reconstructs the prediction value from the verified file
set. The project selects the physical format and defines its schema in that
loader.

The resolved artifact and stage-result snapshot verify the prediction bytes.
Metric values remain `Measurement` records.

The resolved record is `ResolvedEvaluateSpec`. It embeds the exact
`EvaluateSpec`, resolves every input, records the selected environment and
runtime state, and records the `predictions` artifact in the same snapshot as
the resolved spec.

## 20. Benchmark specification and confirmation

An evaluation measures one candidate. A benchmark standardizes that evaluation
across candidates and requires a reproducible, threshold-qualified result.

`EvaluateSpec` is the executable request within one candidate run plan. It
binds the candidate parameters, evaluation inputs, metrics, execution
parameters, and declared outputs. `BenchmarkSpec` is the reusable qualification
policy. It fixes the evaluation dataset, splits, metric thresholds, and
required execution count applied to candidate run plans.

```text
BenchmarkSpec
├── fixes the evaluation ID, dataset, splits, and metrics
├── adds a threshold for each metric and the required execution count
└── constrains each candidate EvaluateSpec
    ├── binds that candidate's parameters
    ├── supplies its evaluation execution parameters
    └── declares predictions and any additional outputs
```

The evaluation ID, dataset, splits, and metric IDs occur in both records. The
verifier requires them to match exactly. This overlap allows one
`BenchmarkSpec` to govern multiple candidate run plans.

```python
BenchmarkId = HumanId


class MetricCriterion(ProtocolModel):
    metric_id: MetricId
    comparison: Literal["ge", "le"]
    threshold: float = Field(allow_inf_nan=False)


class BenchmarkSpec(ProtocolModel):
    schema_version: Literal[1] = 1
    benchmark_id: BenchmarkId
    evaluation_id: EvaluationId
    evaluation_dataset: ArtifactPointerRef
    splits: dict[InputName, ArtifactPointerRef] = Field(min_length=1)
    metrics: tuple[MetricCriterion, ...] = Field(min_length=1)
    execution_count: Literal[2] = 2
```

Benchmark split names and metric IDs are unique. The benchmark file is:

```text
benchmarks/<benchmark_id>.spec.yaml
```

`RunSpec.source` identifies the exact benchmark file. A benchmark run satisfies:

```text
RunSpec.benchmark_id
== BenchmarkSpec.benchmark_id

EvaluateSpec.evaluation_id
== BenchmarkSpec.evaluation_id

exactly one loaded stage spec has kind evaluate

EvaluateSpec.inputs[evaluation_dataset].pointer
== BenchmarkSpec.evaluation_dataset

EvaluateSpec.inputs[parameters].producer_stage_id
== RunSpec.estimator.stage_id

EvaluateSpec.inputs[parameters].name
== RunSpec.estimator.artifact_name

set(EvaluateSpec.split_inputs)
== set(BenchmarkSpec.splits)

EvaluateSpec.inputs[split_name].pointer
== BenchmarkSpec.splits[split_name]

set(EvaluateSpec.metric_ids)
== set(BenchmarkSpec.metrics.metric_id)
```

The evaluation dataset, every split, and every artifact produced by this
evaluation have the `benchmark` data-use role. The model parameters have role
`training` or `validation`.

The benchmark executor completes one successful `ResolvedRun` and one separate
confirmation execution of the same frozen $q$. The successful attempt selected
by `ResolvedRun.successful_attempt_id` and the confirmation attempt use the same
`RunSpec`, exact stage-spec files, source, seed, reproducibility controls,
shared environment, stage overrides, and inputs.

The confirmation record is:

```python
class ResolvedBenchmarkSpecRef(ResolvedFileRef):
    kind: Literal["benchmark_spec"] = "benchmark_spec"
    stored_at: GitFileRef


class ArtifactComparisonReceipt(ProtocolModel):
    artifact: StageArtifactRef
    candidate_stage: ResolvedStageRef
    confirmation_stage: ResolvedStageRef
    candidate_digest: SHA256
    confirmation_digest: SHA256
    passed: bool


class MetricCriterionReceipt(ProtocolModel):
    metric_id: MetricId
    candidate_verification: ResolvedFileRef
    confirmation_verification: ResolvedFileRef
    comparison: Literal["ge", "le"]
    threshold: float = Field(allow_inf_nan=False)
    passed: bool


class BenchmarkResult(ProtocolModel):
    schema_version: Literal[1] = 1
    benchmark: ResolvedBenchmarkSpecRef
    run: ResolvedRunRef
    confirmation: ResolvedAttemptRef
    artifacts: tuple[ArtifactComparisonReceipt, ...] = Field(min_length=2)
    metrics: tuple[MetricCriterionReceipt, ...] = Field(min_length=1)
    status: Literal["passed", "failed"]
    completed_at: AwareDatetime
```

The benchmark reference satisfies:

```text
ResolvedBenchmarkSpecRef.stored_at.repository
== RunSpec.source.repository

ResolvedBenchmarkSpecRef.stored_at.commit
== RunSpec.source.commit

ResolvedBenchmarkSpecRef.stored_at.path
== benchmarks/<RunSpec.benchmark_id>.spec.yaml
```

The selected run attempt and the attempt loaded through
`BenchmarkResult.confirmation` have distinct attempt IDs, `succeeded` status,
and purposes of `run` and `benchmark_confirmation`, respectively. Both contain
every stage declared by the shared `RunSpec`. Their stage-result snapshots
and attempt-file snapshots are distinct from each other and from all snapshots
in the selected run.
`BenchmarkResult.completed_at` is at or after the completion times of the
selected `ResolvedRun` and confirmation attempt. Every stored and same-run
input in the confirmation attempt passes the input-lineage checks in Section
21 before parity is evaluated.

Let their realized runtime states be $e,e'\in E_q$. Estimator parity requires:

```math
T_{\alpha,\beta,q}(e)
=
T_{\alpha,\beta,q}(e').
```

The verifier establishes this pairwise equality by reconstructing the
`ArtifactComparisonReceipt` for the artifact selected by `RunSpec.estimator`.
Each digest hashes the canonical `ResolvedArtifact` description, including
every file identity and bundle member. When $q$ satisfies the strict condition
in Section 6, both values equal $\widehat{\theta}_q$. The benchmark result
records the two-execution claim; Section 6 defines the universal claim over
$E_q$.

Prediction parity applies the same comparison to the `predictions` artifact
produced by each attempt's evaluation stage.

`BenchmarkResult.artifacts` contains exactly the estimator `parameters`
comparison and the evaluation `predictions` comparison. The metric-receipt IDs
equal the criterion IDs in `BenchmarkSpec.metrics`. Every referenced
`MetricVerificationReceipt.passed` value is true before threshold evaluation.

For every `MetricCriterion`, `BenchmarkResult.metrics` contains one
`MetricCriterionReceipt`. Its two file references load the immutable
`MetricVerificationReceipt` values for the candidate and confirmation. A `ge`
criterion requires both recomputed values to meet or exceed its threshold. An
`le` criterion requires both recomputed values to meet or fall below its
threshold.

`BenchmarkResult.status` is `passed` exactly when estimator parity, prediction
parity, and every metric criterion hold across both executions. A promoted
benchmark estimator uses an `ArtifactPointer` satisfying:

```text
ArtifactPointer.run
== BenchmarkResult.run

ArtifactPointer.artifact
== selected RunSpec.estimator

ArtifactPointer.benchmark_result
== ResolvedBenchmarkResultRef for the passed BenchmarkResult
```

## 21. Validation and external verification

Pydantic rejects a protocol record before publication when the record violates
its own schema or internal invariants. The external verifier retrieves every
referenced file, verifies its identity, parses its expected record type, and
checks relationships that cross file boundaries.

```text
Pydantic
└── establishes that each loaded record satisfies its model

external verifier
├── proves each reference identifies the recorded bytes
├── proves resolved state satisfies requested state
└── proves the complete provenance graph is internally consistent
```

### Pydantic validation

Pydantic enforces:

1. Closed, immutable records.
2. Identifier, path, SHA-256, commit, timestamp, and finite-number syntax.
3. Required fields, nonempty mappings, and discriminated unions.
4. Unique stage, artifact, factor, level, variant, replicate, seed, metric, and
   bundle-member identities within their containing records, plus unique stage
   snapshots and pairwise-disjoint journal, measurement, metric-verification,
   and log paths within an attempt.
5. Single-file cardinality of one and bundle cardinality of at least two.
6. Matching declared and resolved artifact-name sets inside one resolved stage
   spec.
7. Attempt status, typed failure, and timestamp relationships.
8. The training checkpoint input pair and training-stage ownership of the
   `parameters` and `resume_state` artifact names.
9. The evaluation model, dataset, split, and metric requirements and
   evaluation-stage ownership of the `predictions` artifact name, including
   equality among the evaluation dataset, split, and output roles.
10. The required data-use role on every stored input and artifact declaration.
11. Benchmark split, metric, execution-count, comparison-receipt, and result
    requirements.

### Run-plan verification

Starting from a `ResolvedRunSpecRef`, the verifier:

1. Retrieves the `RunSpec` bytes and checks SHA-256 and byte count.
2. Rejects duplicate YAML keys, requires the canonical run-spec path, and
   requires the run-plan and source snapshots to use one Git repository.
3. Loads `ExperimentSpec`, `VariantSpec`, and the optional `BenchmarkSpec` from
   `RunSpec.source`.
4. Checks the experiment, variant, replicate, global-seed, typed-parameter,
   metric, and benchmark equalities in Sections 16 and 20.
5. Retrieves every stage-spec file identified by `RunSpec.stages` and checks
   its SHA-256 and byte count.
6. Requires every lockfile and stored-input pointer to belong to
   `RunSpec.source`. Stage specs, artifact roots, and stored-input paths use the
   canonical repository locations defined in Section 23.
7. Parses each file through the `Spec` union.
8. Retrieves each stage implementation, parameter model, metric
   implementation, and artifact loader from `RunSpec.source`; checks its path,
   symbol, SHA-256 digest, and byte count.
9. Checks that every `FutureInputRef` selects an earlier stage and a declared
   producer artifact.
10. Checks input, implementation-file, and within-stage artifact-path
    disjointness after resolving every input path.
11. Resolves the role of every same-run input from its producer artifact,
    rejects evaluation and benchmark inputs to training, prevents output-role
    downgrades, and selects the required ordinary-evaluation or benchmark role.
12. Checks that `RunSpec.estimator` selects `parameters` from a training
   stage.

These checks reconstruct the complete frozen $q$ from its root record and exact
stage-spec files.

### Resolved-stage verification

For each `ResolvedStageRef`, the verifier:

1. Retrieves `ResolvedStageRef.resolved_spec` from
   `ResolvedStageRef.snapshot`.
2. Requires its canonical resolved-stage path and checks its SHA-256 and byte
   count.
3. Parses the file through the `ResolvedSpec` union.
4. Requires its embedded stage spec to equal the stage spec selected by the
   corresponding `RunStageRef`.
5. Resolves the selected stage environment and checks `ResolvedEnvironment`
   and `ExecutionContext` under Section 15.
6. For a parameterized stage, verifies `ResolvedParameterizedSpec.source`
   against `RunSpec.source` and `ParameterizedSpec.implementation`; verifies
   its `ProcessStartupReceipt`, `ResolvedStageInvocationRef`, and command; and
   reconstructs `StageContextBinding` from the invocation receipt.
7. Checks the parameter digest, input and artifact paths, metric IDs, named
   NumPy generator keys, canonical context digest, callable identity, and
   successful outcome for each parameterized stage.
8. Checks the resolved input names and kinds against the planned inputs.
9. Checks that `completed_at` lies within the containing attempt and is at or
    after the prior completed stage.
10. For a download stage, verifies each input-keyed retrieval, frozen request,
    HTTP implementation, implementation parameters, executable identity,
    terminal response, expected body identity, resolved body identity, and
    completion interval.

These checks establish that the recorded runtime state satisfies:

```math
e_j
\in
E_{q,j}.
```

### Artifact verification

For every artifact name in the loaded resolved stage spec, the verifier:

1. Selects the declared `ArtifactSpec` and matching `ResolvedArtifact`.
2. Checks single-file or bundle cardinality.
3. Checks every path equality, bundle-member order, bundle containment, and
   cross-artifact disjointness.
4. Lists every regular file beneath a bundle root and requires exact agreement
   with the resolved member list.
5. Retrieves every `SnapshotFileRef` from the stage-result snapshot.
6. Checks every file's SHA-256 and byte count.
7. Retrieves the loader from `RunSpec.source` and verifies the complete
   `ArtifactLoaderRef` identity.
8. Materializes the verified file or directory and invokes the selected loader
   symbol in a dedicated worker.
9. Reports `artifact.loadability` when a generic loader succeeds. For
   `resume_state`, it validates the loaded value as `ResumeState`, checks its
   run-wide DataLoader and NumPy controls, and reports
   `artifact.semantic.resume_state`.

For a generic artifact, this traversal establishes:

```math
L_{j,a}
\left(
F_j(a)
\right)
=
v_a^{(j)}.
```

### Metric verification

For a stateless metric with declared dependencies, the verifier:

1. Retrieves and verifies its `MetricImplementationRef`.
2. Resolves exactly the file dependencies declared by the metric.
3. Checks each dependency name, source, and data-use role against the selected
   stage.
4. Verifies the production worker's startup evidence and execution context.
5. Launches a second controlled worker with the frozen parameters and verified
   dependency paths.
6. Records the verification worker's startup evidence and execution context.
7. Applies `FloatComparator` to the recomputed and recorded values.
8. Verifies both worker receipts inside `MetricVerificationReceipt`, including
   equality of their run, attempt, stage, and metric identities with the
   embedded measurement.

For a metric recorded during the stage, the verifier establishes that the
active `Context` contained the frozen metric handle and that the measurement
was written through the attempt's measurement sink. A numerical recomputation
claim requires captured values or declared files that can reproduce the metric
call.

### Input-lineage verification

For a stored input, the verifier:

1. Retrieves and checks the `ArtifactPointer` file.
2. Retrieves the selected `ResolvedRun` and verifies its complete provenance
   graph, including every completed stage input.
3. Selects its successful attempt.
4. Selects the producer `ResolvedStageRef` and named artifact.
5. Verifies the complete artifact.
6. Requires the stored input's declared data-use role to equal the selected
   producer artifact's declared role.
7. Materializes the artifact at `StoredInputRef.path` and invokes its loader at
   that path.
8. For checkpoint inputs, requires both pointers to select one resolved run,
   one producer stage, `parameters`, and `resume_state`.
9. For a stored evaluation model, requires the pointer to select
   `parameters`.

For a same-run input, the verifier:

1. Selects the earlier `ResolvedStageRef` named by `producer_stage_id`.
2. Loads its resolved stage spec.
3. Selects `name` from its artifact mapping.
4. Inherits the selected artifact's declared data-use role.
5. Verifies and materializes the complete artifact.

For each attempt, the verifier requires its journal, measurements,
metric-verification receipts, and logs to belong to the immutable attempt
revision $D_i$. Distinct attempts use distinct stage-result and $D_i$
revisions. Measurement rows identify completed stages. Log paths identify
completed stages or the next interrupted stage of a non-successful attempt.

### Training-resume verification

For a training stage initialized from a checkpoint, the verifier establishes:

```text
parameters producer
== resume_state producer

parameters artifact
== parameters

resume_state artifact
== resume_state
```

The replay executor invokes both loaders and reconstructs:

```math
s_\ell^{(0)}
=
s_k^{(N_k)}.
```

### Run-result verification

For a `ResolvedRun`, the verifier:

1. Retrieves every `ResolvedAttemptRef` and checks its file identity, canonical
   path, attempt ID, order, timestamps, status, and typed failure.
2. Checks each attempt journal against the attempt's terminal state and
   failure.
3. Retrieves every invocation reference and requires one terminal receipt for
   each started stage.
4. Requires each attempt's resolved stages to form an ordered prefix of
   `RunSpec.stages`.
5. Requires the successful attempt to contain every stage exactly once and in
   order.
6. Requires stage-result and attempt-file snapshots to satisfy the
   disjointness rules above.
7. Verifies every stored and same-run input consumed by every completed stage
   in every attempt.
8. Verifies every journal, measurement, metric-verification, and log file.
9. Requires their canonical attempt-scoped paths.
10. Checks every measurement against the run, attempt, stage, experiment, and
   stage-specific metric identities and requires its timestamp to be at or
   before the named stage's completion.
11. Applies the metric-verification rules to every recomputed measurement.
12. Loads the estimator artifact selected by `RunSpec.estimator`.

For a `BenchmarkResult`, the verifier retrieves the confirmation through its
`ResolvedAttemptRef`, reconstructs every `ArtifactComparisonReceipt`, and
retrieves both `MetricVerificationReceipt` files named by each
`MetricCriterionReceipt`. It derives the expected benchmark status from those
receipts. The confirmation attempt ID exceeds every candidate run attempt ID,
its purpose is `benchmark_confirmation`, and it uses new snapshots. Its inputs
pass the same lineage verification applied to the selected run.

These operations implement `benchmark.plan`, `benchmark.confirmation`,
`benchmark.artifacts`, `benchmark.metrics`, and `benchmark.status` as defined
by the benchmark-execution contract.
Artifact-pointer verification separately establishes the promotion
relationships in Sections 14 and 20.

## 22. Execution and publication sequence

The protocol publishes immutable snapshots in dependency order:

| Snapshot | Repository | Contents |
|---|---|---|
| A | Git | Source, experiment records, benchmark specs, loaders, lockfile, and existing promotion pointers. |
| B | Git | One `RunSpec` and every stage-spec file identified by it. |
| $I_{i,j}$ | Artifact repository | The invocation receipt for parameterized stage $j$ of attempt $i$. Download stages do not create this snapshot. |
| $C_{i,j}$ | Artifact repository | The resolved spec and every artifact file for stage $j$ of attempt $i$; each download body is its same-named artifact file. |
| $D_i$ | Artifact repository | Attempt document, journal, invocation references, metric-verification receipts, measurements, and logs for attempt $i$. |
| E | Artifact repository | The terminal `ResolvedRun`. |
| F | Artifact repository | The optional `BenchmarkResult`. |
| G | Git | Optional promotion pointers. |

### Freeze the run plan

1. Publish source snapshot A.
2. Select the experiment, variant, replicate, optional benchmark, shared
   environment, reproducibility controls, and ordered stage specs.
3. Set `RunSpec.source` to snapshot A.
4. Validate and serialize every stage spec.
5. Calculate each stage-spec file's SHA-256 and byte count.
6. Construct and validate `RunSpec` with its ordered `RunStageRef` records.
7. Publish `RunSpec` and every stage-spec file together as snapshot B.
8. Retrieve and verify every file in snapshot B.

Snapshot B fixes $q$.

### Execute one attempt

For attempt $i$:

1. Allocate its `attempt_id` and record `started_at`.
2. Retrieve and verify snapshots A and B.
3. Materialize every stored input.
4. Execute stages in `RunSpec.stages` order.
5. Resolve each same-run input through an earlier `ResolvedStageRef`.
6. Apply `RunSpec.seed`, `RunSpec.reproducibility`, and the selected stage
   environment.
7. Launch the controlled child and record `ProcessStartupReceipt` and
   `ExecutionContext`.
8. For a download stage, invoke the selected `HttpImplementationSpec` for every
   frozen request and atomically publish each verified body as its same-named
   single-file artifact.
9. For a parameterized stage, validate the stage parameter model, bind the
   configured named NumPy generators, construct `Context`, and invoke the exact
   callable selected by `StageImplementationRef`.
10. For a parameterized stage, record and publish `StageInvocationReceipt` as
    snapshot $I_{i,j}$, then construct `ResolvedStageInvocationRef`.
11. Resolve every declared artifact and construct the resolved stage spec.
12. Publish the resolved stage spec and every artifact file together as
    snapshot $C_{i,j}$.
13. Retrieve and verify the complete snapshot, including the invocation
    reference for a parameterized stage.
14. Construct `ResolvedStageRef` from the returned snapshot commit and resolved
    stage-spec file identity.
15. Append the verified stage result and any invocation reference to the
    current attempt.

After the attempt reaches a terminal status:

1. Record `completed_at`, terminal status, and the typed failure when the
   status is unsuccessful.
2. Publish the active stage's terminal invocation receipt when execution ended
   before a successful stage snapshot.
3. Close the journal, metric-verification receipts, measurements, and logs.
4. Construct the complete `RunAttempt`.
5. Publish the attempt document and its files as revision $D_i$.
6. Retrieve and verify the complete revision.
7. Construct `ResolvedAttemptRef` from the published attempt document.

```text
stage execution
        │
        ▼
snapshot I_i,j (parameterized stages only)
└── invocation receipt
        │
        ▼
snapshot C_i,j
├── resolved stage spec
├── invocation reference → snapshot I_i,j (parameterized stages only)
└── every file in every named artifact
        │
        ▼
ResolvedStageRef
├── snapshot → repository + commit C_i,j
└── resolved_spec → path + SHA-256 + bytes
```

### Finalize the run

1. Determine the terminal run status and `successful_attempt_id`.
2. Construct `ResolvedRun` with the reference to snapshot B and every completed
   `ResolvedAttemptRef`.
3. Publish `ResolvedRun` as snapshot E.
4. Retrieve and verify the terminal record and its complete provenance graph.

### Confirm a benchmark

For a benchmark run:

1. Execute one additional successful confirmation attempt against the same
   snapshot B.
2. Publish and verify its stage-result snapshots $C_{i,j}$ and attempt files
   $D_i$.
3. Construct comparison receipts for the estimator and prediction artifacts.
4. Recompute each benchmark metric and construct its criterion receipt.
5. Construct and publish `BenchmarkResult` as snapshot F.
6. Retrieve every referenced receipt and verify the benchmark result.

### Promote an artifact

Promotion constructs an `ArtifactPointer` selecting:

```text
ResolvedRun at snapshot E
+ StageArtifactRef
+ passed BenchmarkResult at snapshot F, when benchmark approval is required
```

The pointer is published under `inputs/` in snapshot G. A later source snapshot
may select that pointer through a `StoredInputRef`.

## 23. Repository layout

Pointer filenames use:

```python
SelectionName = HumanId
```

VIPER reserves the paths shown below. Project source can occupy any other
repository-relative paths.

```text
repository/
├── viper.toml
├── <user-owned files and directories>
├── inputs/
│   ├── benchmarks/
│   │   └── <benchmark_id>/
│   │       └── <selection_name>.pointer.yaml
│   ├── datasets/
│   │   └── <dataset_id>/
│   │       └── <selection_name>.pointer.yaml
│   ├── priors/
│   │   └── <prior_id>/
│   │       └── <selection_name>.pointer.yaml
│   └── models/
│       └── <model_id>/
│           └── <selection_name>.pointer.yaml
├── benchmarks/
│   └── <benchmark_id>.spec.yaml
├── experiments/
    └── <experiment_id>/
        ├── spec.yaml
        ├── README.md
        ├── variants/
        │   └── <variant_id>.spec.yaml
        └── runs/
            └── <variant_id>/
                └── <run_id>/
                    ├── spec.yaml
                    ├── resolved.yaml
                    ├── benchmark.result.yaml
                    ├── attempts/
                    │   └── <attempt_id>/
                    │       ├── resolved.yaml
                    │       ├── journal.jsonl
                    │       ├── measurements/
                    │       │   └── <stage_id>.<metric_id>.jsonl
                    │       ├── metric_verification/
                    │       │   └── <stage_id>.<metric_id>.yaml
                    │       ├── invocations/
                    │       │   └── <stage_id>.yaml
                    │       └── logs/
                    │           ├── <stage_id>.stdout.log
                    │           └── <stage_id>.stderr.log
                    ├── stages/
                    │   └── <stage_id>/
                    │       ├── spec.yaml
                    │       ├── resolved.yaml
                    │       └── retrievals/
                    │           └── <input_name>/
                    │               └── body
                    ├── artifacts/
                    │   ├── datasets/
                    │   │   └── <dataset_id>/
                    │   │       └── <dataset file or bundle>
                    │   ├── priors/
                    │   │   └── <prior_id>/
                    │   │       └── <prior file or bundle>
                    │   ├── models/
                    │   │   └── <model_id>/
                    │   │       ├── <embedding file or bundle>
                    │   │       ├── <parameters file or bundle>
                    │   │       └── <resume-state file or bundle>
                    │   └── evaluations/
                    │       └── <evaluation_id>/
                    │           └── <prediction file or bundle>
└── .viper/
    ├── store/
    ├── workspaces/
    ├── journals/
    ├── catalog.sqlite3
    └── knowledge/
```

`viper init ROOT` selects `repository/` in this diagram. `ROOT/viper.toml`
marks the selected root. A later local command either receives `ROOT`
explicitly or discovers the nearest parent containing that marker. The
machine-specific absolute root remains local configuration outside frozen
protocol records.

The visible `inputs/`, `benchmarks/`, and `experiments/` paths hold authored
records, resolved records, and working artifacts. `.viper/store` holds separate
immutable local copies. Editing a working artifact makes the working tree
differ from its published snapshot. Verification and restore use the immutable
snapshot reference.

Each `ParameterizedSpec.implementation.path`, project
`HttpImplementationRef.path`, `MetricSpec.implementation.path`, and
`ArtifactSpec.loader.path` records its selected Python file as a
`PythonRepoRelPath` value. For example, each of these paths is valid:

```text
src/my_project/training/fit.py
pipelines/evaluate.py
analysis/metrics/correlation.py
transports/aria2.py
loaders/model_bundle.py
```

`RunSpec.source` fixes the exact bytes of every entrypoint, imported production
module, project HTTP implementation, metric, and artifact loader.

When a project uses `tools/`, that directory contains repository-maintenance,
migration, generation, and inspection utilities. A tool has one documented
purpose. `ParameterizedSpec.implementation` selects production stage source.

When a project uses `tests/`, that directory contains deterministic checks for
its entrypoints, metrics, and loaders. Test files may be present in the source
snapshot. Stage implementation references select the production entrypoints.

The run directory is the durable output root. Artifact files, measurements,
logs, resolved records, and benchmark results use stable repository-relative
paths.

A single-file artifact occupies its declared file path. A bundle artifact
occupies its declared directory root, and its loader defines the required
member filenames beneath that root.

## Appendix A. Complete training-state transition

This appendix expands the transition $U_{\alpha,\beta,q,t}$ defined in
Section 5 into batch selection, gradient computation, one optimizer update,
and state reassembly. The displayed optimizer factorization uses standard
PyTorch Adam, whose update preserves the generator state supplied by the
preceding gradient computation. The induction applies to single-process
loading with one selected batch per optimizer update. The final subsection
states the changes required for gradient accumulation and multiprocess
prefetching.

### A.1 Initial state

Initialization produces:

```math
\begin{aligned}
s_k^{(0)}
&=
I_{\alpha,\beta,q}^{\mathrm{init}}
\left(
\omega_k,
D_q,
\zeta_q,
e_k
\right) \\
&=
\left(
\theta_k^{(0)},
o_k^{(0)},
r_k^{(0)},
b_k^{(0)}
\right).
\end{aligned}
```

At this boundary:

1. $\theta_k^{(0)}$ contains the initialized model parameters and persistent
   buffers.
2. $o_k^{(0)}$ contains the initial optimization state.
3. $r_k^{(0)}$ contains every generator state after initialization.
4. $b_k^{(0)}$ records the initial sampler position.
5. The DataLoader configuration exists. Iterator creation and first-batch
   selection occur inside the first transition.

```text
global seed
    │
    ▼
initialize generators
    │
    ▼
initialize model state
    │
    ▼
initialize optimization state
    │
    ▼
construct DataLoader
    │
    ▼
sₖ⁽⁰⁾ = (θₖ⁽⁰⁾, oₖ⁽⁰⁾, rₖ⁽⁰⁾, bₖ⁽⁰⁾)
```

### A.2 Batch selection

Fix:

```math
t
\in
\left\{
0,\ldots,N_k-1
\right\}.
```

Let $d_k^{(t+1)}$ be the transformed and collated batch consumed by update
$t+1$. Define batch selection by:

```math
\begin{aligned}
&
\left(
d_k^{(t+1)},
r_{k,\mathrm{batch}}^{(t+1)},
b_{k,\mathrm{batch}}^{(t+1)}
\right)
\\
&\qquad =
B_{\alpha,\beta,q,t}
\left(
\omega_k,
D_q,
e_k,
r_k^{(t)},
b_k^{(t)}
\right).
\end{aligned}
```

The operation $B_{\alpha,\beta,q,t}$:

1. creates a DataLoader iterator at the start of a loader pass;
2. obtains the next index batch;
3. retrieves the selected observations;
4. applies the configured transformations and collation;
5. advances each generator consumed by these operations; and
6. records the resulting sampler and DataLoader position.

Let $r_{k,\mathrm{sampling}}^{(t+1)}$ contain the generator states after the
iterator and sampler have selected the index batch for update $t+1$. Retrieval,
transformation, and collation of those observations follow this boundary. The
generator-state transition inside $B_{\alpha,\beta,q,t}$ is:

```math
r_k^{(t)}
\longmapsto
r_{k,\mathrm{sampling}}^{(t+1)}
\longmapsto
r_{k,\mathrm{batch}}^{(t+1)}.
```

The first transition includes generator changes caused by iterator creation and
randomized index generation. The second includes generator changes caused by
stochastic dataset retrieval, transformations, or custom collation.

When index selection preserves the generator state:

```math
r_{k,\mathrm{sampling}}^{(t+1)}
=
r_k^{(t)}.
```

When retrieval, transformation, and collation preserve the generator state:

```math
r_{k,\mathrm{batch}}^{(t+1)}
=
r_{k,\mathrm{sampling}}^{(t+1)}.
```

For the first batch of a DataLoader pass:

```python
iterator = iter(loader)
batch = next(iterator)
```

For each later batch in the same pass:

```python
batch = next(iterator)
```

The value $r_{k,\mathrm{batch}}^{(t+1)}$ contains the generator states after
the batch has been materialized. The value
$b_{k,\mathrm{batch}}^{(t+1)}$ contains the sampler and DataLoader position
after that batch.

### A.3 Gradient computation

Using $d_k^{(t+1)}$, the training procedure clears the stored gradients, performs the forward computation, computes the loss, and performs backpropagation. Define:

```math
\begin{aligned}
&
\left(
\ell_k^{(t+1)},
g_k^{(t+1)},
\theta_{k,\mathrm{forward}}^{(t+1)},
r_{k,\mathrm{gradient}}^{(t+1)}
\right)
\\
&\qquad =
G_{\alpha,\beta,q,t}
\left(
\omega_k,
e_k,
\theta_k^{(t)},
d_k^{(t+1)},
r_{k,\mathrm{batch}}^{(t+1)}
\right).
\end{aligned}
```

Here:

1. $\ell_k^{(t+1)}$ is the loss computed for update $t+1$.
2. $g_k^{(t+1)}$ contains the resulting parameter gradients.
3. $\theta_{k,\mathrm{forward}}^{(t+1)}$ contains the model parameters and persistent buffers after the forward computation.
4. $r_{k,\mathrm{gradient}}^{(t+1)}$ contains the generator states after the stochastic operations used to compute the gradients.

**Generator state.** During training, Dropout samples a new Bernoulli mask during each forward call. Its sampling advances the applicable generator state:

```math
r_{k,\mathrm{batch}}^{(t+1)}
\longmapsto
r_{k,\mathrm{gradient}}^{(t+1)}.
```

This behavior is defined by the [PyTorch 2.13.0 `Dropout` implementation](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/nn/modules/dropout.py#L35-L72).

When the operations between batch materialization and completed gradient
computation preserve the generator state:

```math
r_{k,\mathrm{gradient}}^{(t+1)}
=
r_{k,\mathrm{batch}}^{(t+1)}.
```

**Persistent model buffers.** When the forward computation preserves every
persistent model buffer:

```math
\theta_{k,\mathrm{forward}}^{(t+1)}
=
\theta_k^{(t)}.
```

### A.4 Optimizer update

Update the optimization state:

```math
o_k^{(t+1)}
=
A_{\beta,q,t}
\left(
\omega_k,
e_k,
o_k^{(t)},
g_k^{(t+1)}
\right).
```

Update the model parameters:

```math
\theta_k^{(t+1)}
=
P_{\beta,q,t}
\left(
\omega_k,
e_k,
\theta_{k,\mathrm{forward}}^{(t+1)},
o_k^{(t+1)}
\right).
```

These equations separate the two state changes performed by one optimizer
update: the update to $o_k^{(t)}$ and the update to $\theta_k^{(t)}$. PyTorch
performs both inside [`Adam.step()`](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/optim/adam.py#L215-L264).

The completed-update boundary retains the data-selection state produced during
batch selection:

```math
b_k^{(t+1)}
=
b_{k,\mathrm{batch}}^{(t+1)}.
```

The operations $A_{\beta,q,t}$ and $P_{\beta,q,t}$ receive optimization and
model-state arguments only. The generator component of the completed state is
therefore:

```math
r_k^{(t+1)}
=
r_{k,\mathrm{gradient}}^{(t+1)}.
```

### A.5 Reassembly

The completed update produces:

```math
s_k^{(t+1)}
=
\left(
\theta_k^{(t+1)},
o_k^{(t+1)},
r_k^{(t+1)},
b_k^{(t+1)}
\right).
```

The complete transition is:

```math
\begin{aligned}
s_k^{(t)}
&\longmapsto
\left(
d_k^{(t+1)},
r_{k,\mathrm{batch}}^{(t+1)},
b_{k,\mathrm{batch}}^{(t+1)}
\right)
\\
&\longmapsto
\left(
\ell_k^{(t+1)},
g_k^{(t+1)},
\theta_{k,\mathrm{forward}}^{(t+1)},
r_{k,\mathrm{gradient}}^{(t+1)}
\right)
\\
&\longmapsto
\left(
\theta_k^{(t+1)},
o_k^{(t+1)}
\right)
\\
&\longmapsto
s_k^{(t+1)}.
\end{aligned}
```

This composition is the operation
$U_{\alpha,\beta,q,t}\left(\omega_k,D_q,e_k,s_k^{(t)}\right)$ defined in
Section 5.

### A.6 Boundary invariant

For every:

```math
t
\in
\left\{
0,\ldots,N_k
\right\},
```

$s_k^{(t)}$ contains the training state after exactly $t$ completed optimizer
updates and before any data are selected for update $t+1$. When $t=N_k$, the
stage terminates at that boundary and batch selection ends with update $N_k$.

**Base case.** Initialization produces $s_k^{(0)}$ before the first DataLoader
iterator is created and before the first batch is selected. The invariant holds
for $t=0$.

**Inductive step.** Assume the invariant holds for $t<N_k$. Starting from
$s_k^{(t)}$, the transition:

1. selects and materializes $d_k^{(t+1)}$;
2. computes $\ell_k^{(t+1)}$ and $g_k^{(t+1)}$;
3. applies one optimizer update; and
4. reassembles $s_k^{(t+1)}$ before selecting another batch.

The resulting state contains the training state after exactly $t+1$ completed
optimizer updates and before any data are selected for update $t+2$. The
invariant therefore holds for $t+1$.

By induction, the invariant holds from $s_k^{(0)}$ through
$s_k^{(N_k)}$.

### A.7 Epoch indexing

Let $H_k\in\mathbb{N}_{>0}$ be the number of epochs in training stage $k$.
For each epoch index $h\in\{0,\ldots,H_k-1\}$, let
$M_{k,h}\in\mathbb{N}_{>0}$ be the number of optimizer updates completed in
that epoch. Under the one-batch-per-update scope of this appendix, $M_{k,h}$ is
also the number of batches consumed in epoch $h$.

Define the cumulative update index at each epoch boundary by:

```math
\begin{aligned}
\tau_{k,0}
&= 0, \\
\tau_{k,h+1}
&= \tau_{k,h} + M_{k,h}.
\end{aligned}
```

Epoch $h$ contains the transitions whose starting indices satisfy:

```math
t
\in
\left\{
\tau_{k,h},
\ldots,
\tau_{k,h+1}-1
\right\}.
```

It begins at $s_k^{(\tau_{k,h})}$ and ends at
$s_k^{(\tau_{k,h+1})}$. Consequently:

```math
N_k
=
\tau_{k,H_k}
=
\sum_{h=0}^{H_k-1} M_{k,h}.
```

If every epoch contains $M_k$ optimizer updates, then:

```math
N_k
=
H_k M_k.
```

### A.8 Scope extensions

#### Gradient accumulation

The derivation above uses one selected batch and one optimizer update in each
transition. If $\beta$ uses gradient accumulation, batch selection and gradient
computation repeat several times before the optimizer update. The index $t$
continues to count completed optimizer updates:

```math
s_k^{(t)}
\longmapsto
s_k^{(t+1)}.
```

#### Multiprocess prefetching

With `num_workers > 0`, Appendix B shows that the DataLoader can select and
prepare later batches before the current optimizer update completes. The clause
"before any data are selected for update $t+1$" applies exclusively to the
single-process boundary.

For multiprocess loading, $s_k^{(t)}$ contains the training state after exactly
$t$ completed optimizer updates and every DataLoader action completed by that
boundary. Consequently:

1. $r_k^{(t)}$ contains the main-process and worker generator states.
2. $b_k^{(t)}$ contains the sampler permutation and position, dispatched index
   batches, prepared batches, and delivery order.

Exact resumption reconstructs both values before the next optimizer update.


## Appendix B. DataLoader iteration and RNG state

This appendix expands the batch-selection operation
$B_{\alpha,\beta,q,t}$ from Appendix A.2. A training stage supplies one
explicit `torch.Generator` to a map-style DataLoader with shuffled sampling and
automatic batching. The same generator supplies the DataLoader base seed and
the `RandomSampler` permutation. `BatchSampler` groups indices deterministically.
The diagrams assume `persistent_workers=False`.

The generator states after iterator creation and randomized index generation
form $r_{k,\mathrm{sampling}}^{(t+1)}$. The generator states after retrieval,
transformation, and collation form $r_{k,\mathrm{batch}}^{(t+1)}$. The shuffled
index sequence, its unread position, and any prefetched work are components of
$b_{k,\mathrm{batch}}^{(t+1)}$.

### Single-process loading

```python
generator = torch.Generator().manual_seed(run_seed)

loader = DataLoader(
    dataset,
    batch_size=batch_size,
    shuffle=True,
    generator=generator,
    num_workers=0,
    persistent_workers=False,
)
```

The DataLoader and its `RandomSampler` hold the same generator object:

```text
loader.generator ───────┐
                        ├── generator g, initially in state G₀
RandomSampler.generator ┘
```

One pass proceeds as follows:

```text
DataLoader loader already exists
│
└── iterator = iter(loader)
    ├── creates the DataLoader iterator
    ├── creates an iterator over BatchSampler
    └── draws the DataLoader base seed from g
        └── G₀ → G₁
            │
            ▼
first next(iterator)
├── BatchSampler creates an iterator over RandomSampler
├── first demand for sample indices
├── RandomSampler generates the shuffled index sequence using g
│   └── G₁ → G₂
├── BatchSampler consumes the first batch_size indices
│   └── creates index batch 1
├── sampling-state boundary
├── dataset retrieves those observations
├── transformations process those observations
├── collation combines them
├── batch-state boundary
└── returns batch 1
            │
            ▼
second next(iterator)
├── BatchSampler consumes the next batch_size indices
│   └── uses the existing shuffled sequence
├── sampling-state boundary; no sampler draw occurs
├── dataset retrieves those observations
├── transformations process those observations
├── collation combines them
├── batch-state boundary
└── returns batch 2
            │
            ▼
subsequent next(iterator) calls
└── repeat index grouping, retrieval, transformation, and collation
    using the existing shuffled sequence
            │
            ▼
all indices consumed
├── RandomSampler iterator ends
├── BatchSampler iterator ends
└── DataLoader iterator raises StopIteration
            │
            ▼
iterator = iter(loader)
├── begins the next pass
├── draws another base seed from g
└── the next demand for indices generates a new permutation using g
```

An index batch is the complete list of dataset indices for one returned batch.
For example:

```text
shuffled index sequence
[41, 7, 93, 12, 56, 4, 81, 29, ...]

BatchSampler
├── index batch 1: [41, 7, 93, 12]
└── index batch 2: [56, 4, 81, 29]
```

Dataset retrieval loads the observations named by one index batch.
Transformations process those observations. Collation combines the processed
observations into the batch returned by `next(iterator)`. Index selection is
complete before collation begins.

`BatchSampler` maintains a position in the sampler's index stream. In this
single-process view, each `next(iterator)` consumes the next index batch from
that stream. Position is the complete `BatchSampler` state.

For the first batch, the shared generator state after the base-seed draw and
shuffled-permutation generation belongs to
$r_{k,\mathrm{sampling}}^{(t+1)}$. Any generator changes caused by dataset
retrieval, transformations, or custom collation occur between the sampling-state
and batch-state boundaries. When those operations preserve generator state, the
two states are equal.

### Multiprocess loading

With `num_workers > 0`, sampling remains in the main process. Worker processes
retrieve, transform, and collate the observations selected by the sampler.

```text
main process

shared generator g in state G₀
│
└── iterator = iter(loader)
    ├── draws the DataLoader base seed from g
    │   └── G₀ → G₁
    │
    ├── starts worker processes
    │   ├── worker 0 initializes its worker RNG states
    │   ├── worker 1 initializes its worker RNG states
    │   └── ...
    │
    └── primes the prefetch queue
        ├── BatchSampler requests the first index batch
        │   └── RandomSampler generates the permutation using g
        │       └── G₁ → G₂
        ├── index batch 1 → worker 0
        ├── index batch 2 → worker 1
        └── additional index batches are prefetched
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
worker 0                    worker 1
├── retrieve observations  ├── retrieve observations
├── apply transformations  ├── apply transformations
├── collate batch 1        ├── collate batch 2
└── return batch 1         └── return batch 2
        │                       │
        └───────────┬───────────┘
                    ▼
main process

first next(iterator)
└── returns prepared batch 1

second next(iterator)
└── returns prepared batch 2

continued retrieval
└── dispatches additional index batches until the sequence is exhausted
```

Prefetching requests index batches while `iter(loader)` creates the
multiprocess iterator. The shared generator can therefore supply both the base
seed and the shuffled permutation before the caller's first
`next(iterator)`.

In this case, $r_{k,\mathrm{sampling}}^{(t+1)}$ includes the main-process
generator state after every index-generation operation completed by the
boundary, including work performed for prefetched batches.
$r_{k,\mathrm{batch}}^{(t+1)}$ also includes the worker generator states after
every retrieval, transformation, and collation operation completed by that
boundary.

For worker $i$, PyTorch sets the worker's Python and PyTorch seeds to the
DataLoader base seed plus $i$. PyTorch derives the worker's NumPy seed from the
base seed and $i$. Random transformations executed by that worker advance the
worker RNG states used by their implementations.

### Separate generators

#### Explicitly assigned generators

The following configuration gives the DataLoader and `RandomSampler` different
generator objects:

```python
loader_generator = torch.Generator().manual_seed(run_seed)
sampler_generator = torch.Generator().manual_seed(run_seed)

sampler = RandomSampler(
    dataset,
    generator=sampler_generator,
)

loader = DataLoader(
    dataset,
    sampler=sampler,
    batch_size=batch_size,
    generator=loader_generator,
)
```

The two states advance independently:

```text
loader generator L₀
│
└── iter(loader) draws the DataLoader base seed
    └── L₀ → L₁


sampler generator S₀
│
└── first demand for indices generates the permutation
    └── S₀ → S₁
```

Equal numeric seeds still produce two independently advancing generator states.

#### Default generator path

When the generator argument is omitted, PyTorch uses its default CPU generator
to draw the DataLoader base seed and a seed for a private `RandomSampler`
generator. The private generator then produces the shuffled permutation:

```text
default PyTorch CPU generator
├── supplies the DataLoader base seed
└── supplies a seed for a private RandomSampler generator
        │
        ▼
private RandomSampler generator
└── generates the shuffled permutation
```

Both variants use distinct generator states for DataLoader base-seed generation
and shuffled-permutation generation. The protocol uses one shared generator so
replay captures and restores one DataLoader sampling state.

### Epoch boundary

When the training procedure defines one epoch as one complete DataLoader pass:

```text
one epoch
├── begins with iterator = iter(loader)
├── consumes batches through repeated next(iterator)
└── ends when the iterator raises StopIteration
```

The next epoch begins with another `iter(loader)` call.

This appendix follows the PyTorch 2.13.0 implementations of:

- [`DataLoader` iterator and base-seed construction](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/dataloader.py#L639-L644);
- [`RandomSampler`](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/sampler.py#L146-L170);
- [`BatchSampler`](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/sampler.py#L306-L316);
- [multiprocess prefetching](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/dataloader.py#L1274-L1276);
- [worker-queue index dispatch](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/dataloader.py#L1531-L1557); and
- [worker RNG initialization](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/_utils/worker.py#L274-L281).
