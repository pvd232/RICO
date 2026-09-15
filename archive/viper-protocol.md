# Foundational reproducibility formalism

This document defines VIPER's reproducibility model, persisted records, execution rules, and verification relationships. The implementation reference is revision `178653de710763d1f9d171b77d8eade89e498b10` of the [VIPER repository](../viper). The distribution is `viper-provenance` 0.1.0a3; individual records declare their own schema versions.

Sections 1–11 and Appendices A–B derive the mathematical model. Sections 12–23 connect it to the current Python types, persisted files, and verifier. A successful verification checks recorded evidence against the plan; it does not prove every possible execution produces identical model parameters. Section 6 states the additional assumptions needed for that conclusion.

The [source map](viper-protocol-source-map.json) records the defining files and their digests.

[Appendix C](viper-protocol-declarations.md) contains the Python declarations, grouped by protocol section and linked to their defining source.

**File trees:** [recommended workspace](#workspace-layout) · [VIPER package](#viper-package-layout).

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
- [Appendix C. Python declarations](viper-protocol-declarations.md)

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

For the fixed-data derivation below, immutable dataset artifacts and the stage callables/configurations selecting samples, features, and transformations determine $D_q$.

An ExternalInputRef freezes a workspace path and data role, not an expected byte digest. The current executor reads that path when it captures the input. Two executions can therefore observe different datasets, denoted $D_{q,e}$ and $D_{q,e'}$, under the same path declaration. Applying the fixed-$D_q$ derivation requires these datasets to agree, for example by consuming an immutable stored artifact. Snapshot verification authenticates the captured bytes; it does not retroactively establish a pre-execution content commitment. See [external input capture](../viper/src/viper/execution/_materialization.py).

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
fixed computation. Section 6 defines the additional condition under which $T_{\alpha,\beta,q}$ has the same value for every member of $E_q$. Selecting a runtime policy alone does not establish this condition.

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

Let $k_*$ be the position of the training stage whose `model`
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

The benchmark compares the recorded representations of the `model` artifacts using canonical content digests. Equal digests support equal file contents under the SHA-256 collision-resistance assumption. Interpreting equal contents as equal model state additionally requires a deterministic loader and complete serialization of that state. Equal mathematical parameters need not have byte-identical serializations.

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

### Sufficient conditions and proof

Assume both executions terminate after the same finite number of updates; their initial complete states agree; corresponding updates use identical inputs and a deterministic transition; and every mutable value influencing the update belongs to the recorded state. Fix two permitted runtimes $e,e'$. Equality of initial states is the induction base. If $s_k^{(t)}(e)=s_k^{(t)}(e')$, applying the same deterministic transition to equal arguments gives $s_k^{(t+1)}(e)=s_k^{(t+1)}(e')$. Induction yields equal terminal states, hence equal model state. Applying this argument in stage order also requires each predecessor output consumed by the next stage to agree.

This is a conditional mathematical result. Startup-control readings establish agreement at the observation point, not that user code preserves those controls throughout the invocation. Hidden randomness, unrecorded state, external observations, or runtime-dependent kernels can violate the premises. Two matching completed runs provide evidence about those executions, not a universal proof over $E_q$.

For byte reproducibility, additionally require deterministic serialization of the complete model state and identical bundle-member naming. File verification establishes consistency with recorded identities; it does not independently establish that a trusted writer recorded every scientific dependency.

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
$a_\theta$ denote the `model` artifact and let $a_c$ denote the
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
├── model
│   └── θₖ⁽ᴺᵏ⁾
│       └── sufficient for evaluation
│
└── resume_state
    └── (oₖ⁽ᴺᵏ⁾, rₖ⁽ᴺᵏ⁾, bₖ⁽ᴺᵏ⁾)
        └── combined with model for exact resumption
```

The `resume_state` artifact loads as [ResumeState](viper-protocol-declarations.md#resumestate). Its nested RNG and loader records are defined in [Appendix C](viper-protocol-declarations.md#8-artifact-partition-of-a-training-checkpoint).

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

- Evaluation loads `model`.
- Exact resumption loads `model` and `resume_state`.

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

The following design rules apply completeness and parsimony at three nested boundaries. They guide workspace decomposition; the verifier does not prove that an artifact contains the minimum possible files or that user code uses every declared input:

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

The authoring API constructs Python drafts. Compilation resolves callables to exact source references and writes stage specs plus a RunSpec. Execution publishes resolved records and file identities; verification traverses those references and checks their relationships.

| Object | Role |
|---|---|
| `RunPlanDraft` | Python declaration awaiting compilation. |
| `RunSpec` and `Spec` | Frozen run selection and discriminated stage requests. |
| `OutputSpec` | One named output's path, loader, representation kind, and declared data role. |
| `ResolvedSpec` | Completed stage record, including resolved output artifacts. |
| `ResolvedStageRef` | Snapshot location plus resolved-stage file identity. |
| `RunAttempt` | One attempt's timing, outcome, stage prefix, and evidence references. |
| `ResolvedRun` | Persisted terminal result and attempt references. |
| `RunResult` | Python execution return: `record`, `reference`, `path`, `journal_path`, and derived `status`. |
| `ArtifactPointer` | Reusable selection of one artifact from a successful run. |
| `BenchmarkResult` | Independent confirmation, artifact comparisons, and optional metric thresholds. |

A frozen Pydantic model prevents attribute reassignment; it does not recursively freeze every nested dictionary or arbitrary object. The immutable persisted identity is the serialized document plus its content identity in the selected store. Config classes intentionally permit validated JSON extension fields. The public plan() authoring path separately copies and recursively freezes supported nested declaration containers so caller edits do not change the returned draft.

A record's schema version is local to its type. RunSpec, ResolvedRun, stage specs, ExperimentSpec, VariantSpec, and Config currently use version 2; several metric, benchmark, and resume records use version 1. ExecutionPolicyRef.version identifies preset definitions, not the global protocol version. The literal in each declaration is authoritative.

[Python declarations](viper-protocol-declarations.md#12-protocol-record-roles).

## 13. File, artifact, and stage-result records

Run IDs are 26-character uppercase ULID-form strings matching `^[0-9A-HJKMNP-TV-Z]{26}$`. Human-authored experiment, variant, replicate, stage, input, output, metric, and eval IDs use lowercase identifiers matching `^[a-z][a-z0-9_]*$`. RunId is not a HumanId. Paths are normalized relative POSIX paths without empty, dot, parent, absolute, backslash, or control-character components. SHA-256 values contain 64 lowercase hexadecimal characters.

### File identity and logical document digests

A file SHA-256 hashes the exact stored bytes, and its byte count is the length of that byte sequence. By contrast, `document_digest()` first serializes a model to JSON values, then hashes UTF-8 JSON with sorted mapping keys, compact separators, and `ensure_ascii=False`. Thus config and context digests are independent of mapping insertion order. `serialize_document()` emits YAML with `sort_keys=False`; different YAML bytes can encode the same logical value. Verification uses the appropriate identity at each join rather than treating these hashes as interchangeable. See [serialization.py](../viper/src/viper/serialization.py).

A standalone file reference combines storage location, byte count, and SHA-256. SnapshotFileRef supplies the path and content identity within a separately selected stage-result snapshot. Storage includes Git, Hugging Face, local stores, and VIPER Cloud file references; the snapshot union has its own supported storage variants. These unions are defined in references.py.

The output declaration belongs to `BaseSpec.outputs`; realized output files belong to `ResolvedBaseSpec.artifacts`. Their output-name sets agree. `OutputSpec.kind` selects `file` or `bundle`. A single file has one identity; a bundle has at least two uniquely named members under its declared root. Verification checks member order, containment, non-overlap, exact membership, hashes, byte counts, and loader execution. A successful generic loader invocation demonstrates loadability of those bytes, not scientific correctness.

The compiler places each output beneath `experiments/<experiment_id>/runs/<variant_id>/<run_id>/artifacts/<stage_id>/<output_name>/<relative_path>`. Stage identity replaces the former category-based output directory scheme. Promoted output pointers use `.viper/pointers/<run_digest>/<stage_id>/<output_name>.pointer.yaml`, with run_digest identifying the referenced terminal run record.

[Python declarations](viper-protocol-declarations.md#13-file-artifact-and-stage-result-records).

## 14. Run, input, and attempt records

RunSpec selects one experiment, variant, and replicate, and freezes its seed, source revision, shared env, execution policy, complete reproducibility settings, ordered stage references, and estimator. `RunSpec.estimator` selects a declared training stage's `model` output. A stage's `env` overrides the shared env; run-wide reproducibility controls remain shared.

Inputs have three branches:

- `ExternalInputRef` declares a workspace-local source and role. The executor captures its file into the consuming stage snapshot; the resolved input binds the original source declaration to a SnapshotFileRef. The declaration alone has no prior-run lineage or expected content hash.
- `StoredInputRef` selects a promoted artifact through a Git pointer or resolved pointer reference. The verifier follows the pointer, run, successful attempt, producer stage, and selected artifact. Its materialization path must not overlap the pointer file.
- `FutureInputRef` selects a named output from an earlier stage of this run. The verifier checks producer order and output membership, then inherits the producer output's data role.

Data roles are `training < validation < eval < benchmark` in increasing restriction. Every produced output must be at least as restrictive as every input. Training accepts training and validation roles. Evaluation model inputs use training or validation; its stored `test` input uses eval or benchmark, and named split inputs use the same role as test. These are checks on declared roles and lineage, not an inference of the biological meaning of file contents. The current output() constructor requires data_role explicitly.

Attempts have strictly increasing IDs, terminal timing and status, an ordered completed-stage prefix, and attempt-scoped evidence. Success requires all planned stages. Failure, cancellation, or preemption records a typed failure; a preempted attempt yields a failed terminal run. SIGINT maps to cancellation and SIGTERM to preemption. An abandoned journal can be reconciled as coordinator_lost. This durability depends on continued access to the workspace and storage.

ResolvedRun.successful_attempt_id identifies the successful ordinary attempt exactly when status is succeeded. Benchmark confirmation uses a separate attempt with purpose benchmark_confirmation. Ordinary retry preserves the frozen plan; changed source or settings require a new plan.

[Python declarations](viper-protocol-declarations.md#14-run-input-and-attempt-records).

## 15. Environment, reproducibility, and execution records

`EnvSpec` discriminates LocalEnvSpec and GCEEnvSpec; `ResolvedEnv` records their realized counterparts. Requested lockfiles are source references; resolved lockfiles include verified content identities. `ExecutionContext` records host, compute backend, and numerical-runtime information. A requested environment is not a provisioning receipt by itself.

### Execution policy

| Setting | reproducible | relaxed |
|---|---|---|
| deterministic_algorithms | true | false |
| deterministic_warn_only | false | false |
| cudnn_deterministic | true | false |
| cudnn_benchmark | false | true |
| cublas_workspace_config | `:4096:8` | null |
| float32_matmul_precision | highest | highest |
| cudnn_allow_tf32 | false | false |
| autocast_enabled / dtype | false / null | false / null |

`resolve_execution_policy()` selects reproducible by default. An explicit ReproducibilitySpec selects custom. Parallelism is a separate selection; supplying it both through custom settings and a separate override is rejected. When parallelism is omitted, reproducible selects its fixed default resource settings; relaxed retains the authoring process's Torch thread counts. Both presets retain the same precision controls and enable legacy NumPy RNG capture; their named-generator mapping is initially empty. Relaxed permits nondeterministic algorithm selection; it does not promise faster execution for every workload.

### Runtime observation

Initialization applies settings and creates the named generators and seed records. Immediately before the user call, inside its autocast context, observe_process_startup constructs ProcessStartupReceipt with independently queried RuntimeControlsReceipt values. Keeping observation inside autocast captures the enabled state and dtype actually active at that point.

The verifier compares requested controls with those readings: determinism flags, matrix-multiplication precision, thread counts, and autocast state. CUDA checks additionally compare the cuDNN flags. The startup environment mapping supplies allowlisted process controls such as the cuBLAS setting; generator records supply initialized seed/state identities. Stage workers and independent metric workers carry this evidence. Reused stages lead back to their original execution evidence.

These observations establish startup agreement. User code can subsequently change process settings, consume undeclared randomness, or access external state. VIPER does not continuously monitor those actions or prove byte parity from startup receipts. Benchmark artifact comparison is a separate operation.

[Python declarations](viper-protocol-declarations.md#15-environment-reproducibility-and-execution-records).

## 16. Experiment, variant, replicate, and measurement records

ExperimentSpec declares factor levels, permitted variants, replicate IDs/seeds, and metric specifications. VariantSpec binds selected factor levels and stage configurations. Plan verification checks the selected experiment, variant, seed, configs, metric IDs, and estimator together. Human-authored stage names remain independent of stage kinds: two different stage IDs may both be training stages.

The Python authoring constructors support named declarations and sequences. `replicate(seed=7)` assigns seed_7 by default; an explicit name is optional. Inspect authoring.py for the exact draft signatures. Persisted specs retain explicit identities even when a Python constructor supplies them.

A metric identifies a computation, such as mean squared error between predictions and targets. A stateless metric computes one value per call. A StatefulMetric accumulates through update() and computes through compute(). StageContext.metrics provides declared MetricHandle objects; record() invokes the metric and appends a Measurement with run, attempt, stage, metric, time, and optional step/epoch identities.

MetricContext supplies config, declared input/artifact paths, IDs, and named generators. It is a different interface from StageContext because it executes a metric rather than the stage. A function receiving all numerical arguments directly may leave that required context unused.

Stateful metrics cannot declare dependencies or a comparator. Stateless metrics either record stage-supplied values with neither, or declare both file dependencies and a comparator for independent recomputation. Dependencies name an input or artifact and its required `data_role`. Production and recomputation workers each retain source/config identity, exact dependency files, runtime evidence, timing, and scalar value. MetricVerificationReceipt binds both to the recorded measurement and comparator.

A stage-recorded scalar without saved dependencies is not independently recomputed. Metric recomputation verifies repeatability of the selected metric over saved inputs, not that the selected metric measures the intended scientific property.

[Python declarations](viper-protocol-declarations.md#16-experiment-variant-replicate-and-measurement-records).

## 17. Concrete stage records

The Spec union has six kinds: download, build, embed, diagnostic, train, and eval. DownloadSpec is runner-owned HTTP retrieval; its input request names equal its single-file output names. Workspace stages identify exact callable and config-type sources and receive StageContext. Download bodies are verified against their frozen request identities and recorded retrieval evidence before publication.

Build, embed, diagnostic, train, and eval inherit the shared internal-input rules. TrainSpec requires an objective naming a declared metric and model/resume_state outputs. EvalSpec requires model, stored test, stored split inputs, predictions output, declared metrics, and an objective. DiagnosticSpec provides a workspace stage kind without pretending that diagnostic computation is model training or evaluation.

StageContext contains run_id, attempt_id, stage_id, config, inputs, outputs, metrics, and numpy_generators. StageContextBinding persists the serializable logical binding: config type/digest, paths, metric IDs, and generator names. StageInvocationReceipt records the implementation, binding digest, timestamps, and outcome.

Resolved workspace stages use a completion union. ExecutedStageCompletion contains source, env, execution_context, startup, invocation, and command. ReusedStageCompletion identifies a StageReuseReceipt. Therefore code inspecting startup evidence must branch on completion.kind and follow reused provenance; startup is not an unconditional top-level field on every resolved workspace stage.

Verified reuse compares a StageReuseKey covering source, implementation/config, effective environment, reproducibility, seed, and input identities. It verifies the source run and copied files and metric evidence. A reused result is not a fresh execution and must not be counted as an independent confirmation.

[Python declarations](viper-protocol-declarations.md#17-concrete-stage-records).

## 18. Training checkpoint mapping

The reserved output names are `model` and `resume_state`. TrainOutputs expresses that pair at authoring time; TrainSpec validates both names in outputs. The model loader reconstructs model parameters and persistent buffers. The resume-state loader reconstructs optimizer, main-process RNG, and stateful DataLoader state. Together they should reconstruct the state in Section 4.

Checkpoint inputs must declare both names, use the same input kind, and identify one consistent producer checkpoint. Future inputs select model and resume_state from the same producer stage. Stored checkpoint provenance is checked by following both pointers to the same producer.

`capture_resume_state()` saves optimizer.state_dict(), named/global RNG states, and StatefulDataLoader.state_dict() plus its configuration. `restore_resume_state()` checks DataLoader configuration, then restores optimizer, DataLoader, and main-process RNG after the caller restores model state. `load_resume_state()` uses torch.load with weights_only=True and validates ResumeState.

The formal optimizer-state component in Section 4 includes every scheduler/scaler/accumulation value used by the algorithm. The current convenience capture helper does not independently capture a scheduler or gradient scaler. A workspace using those components must explicitly serialize and restore the additional state in its checkpoint design. The generic verifier cannot infer that arbitrary user-defined training state is complete. Appendices A and B state the corresponding requirements.

[Python declarations](viper-protocol-declarations.md#18-training-checkpoint-mapping).

### Reconstruction condition

Let $L_m$ and $L_r$ be the selected model and resume loaders, and let $F_m,F_r$ be their verified file representations. A complete checkpoint requires

```math
L_m(F_m)=\theta_k^{(N_k)},\qquad
L_r(F_r)=(o_k^{(N_k)},r_k^{(N_k)},b_k^{(N_k)}).
```

After reconstruction, exact continuation additionally requires the same next input, restored generator and iterator position, and deterministic transition assumed in Section 6. A valid ResumeState schema alone does not prove these equalities for every workspace algorithm.

## 19. Evaluation stage

Evaluation consumes the estimator through the `model` input and evaluates fixed stored `test` and split artifacts. The split names are declared in EvalSpec.split_inputs and must differ from reserved names. Their roles agree with test. Evaluation writes `predictions`; its objective selects a declared metric. EvalConfig contains model-specific settings, while metric_ids and split_inputs belong to EvalSpec itself.

The evaluation function reads its declared inputs through StageContext and writes the declared predictions representation through outputs. File-dependent stateless metrics consume those predictions through MetricContext, with exact dependency identities and independent recomputation receipts. A benchmark fixes the pointers, metric IDs, and optional thresholds governing this evaluation. Choosing the test population and assessing statistical validity remain scientific responsibilities.

## 20. Benchmark specification and confirmation

BenchmarkSpec fixes test and split pointers, eval identity, metric IDs, optional threshold criteria, and execution_count=2. A completed candidate run is followed by an independent successful confirmation attempt against the same plan. ArtifactComparisonReceipt compares canonical digests of the candidate and confirmation artifacts. BenchmarkMetricResult links candidate and confirmation metric-verification evidence; optional MetricCriterionResult applies a finite threshold with ge or le.

The result status distinguishes verified comparisons without criteria, passed criteria, and failed comparisons or criteria. A saved passed Boolean is checked against its supporting values; it is not self-authenticating. A failed numerical comparison is a benchmark result, whereas execution or verification errors raise through the public execution API.

Artifact-pointer verification separately checks promotion eligibility. When a benchmark governs the selected estimator, the promoted pointer must carry the benchmark result required by the verifier. A passed comparison covers those observed runs and selected outputs; it is not the universal statement over all $E_q$ in Section 6.

[Python declarations](viper-protocol-declarations.md#20-benchmark-specification-and-confirmation).

## 21. Validation and external verification

Pydantic validation checks local shape, discriminators, finite values, identity syntax, name uniqueness, path relations, status/timing rules, and relationships contained in one record. It cannot authenticate a referenced file until the verifier retrieves that file.

### Plan traversal

The plan verifier retrieves RunSpec and each ordered stage specification by exact identity. It checks source and plan relationships, selected experiment/variant/replicate, seed, config types and values, metric/objective membership, environment/lockfile bindings, implementation and loader identities, output paths, input roles, and earlier-stage references. External local inputs acquire persisted file identity during capture; their declaration is not equivalent to a prior promoted input.

### Attempt and stage traversal

The attempt verifier checks canonical paths, attempt order and timestamps, terminal outcome, journal transitions, the completed-stage prefix, invocation references, and measurement/log locations. Successful attempts contain every planned stage. For each completed stage it loads the snapshot and compares the embedded spec with the selected request. It verifies the executed or reused completion branch and traverses source, invocation/config binding, runtime observations, input evidence, and output files.

### Artifact and metric traversal

Artifact verification compares byte counts and digests, lists bundle members, checks containment and non-overlap, then invokes the exact loader in a controlled worker. Resume-state artifacts receive additional validation of their known controls. Generic loadability cannot prove that every mutable training component was captured.

For recomputable metrics, the verifier resolves frozen dependencies, runs the metric again under the requested controls, validates both worker receipts, and applies the declared comparator. Stage-recorded metrics without file dependencies receive identity and timing checks rather than a numerical recomputation claim.

### Stored-input and reuse traversal

Stored inputs traverse pointer → ResolvedRun → successful attempt → producer stage → selected artifact. Future inputs traverse an earlier same-run stage. Reuse traverses its source-run receipt and verifies the selected execution and copied evidence rather than fabricating a new invocation. Recursive verification needs a trusted source policy because loaders and metric callables execute source code.

### Implementation boundaries

The built-in checkpoint helper covers optimizer, main-process RNG, and StatefulDataLoader state. Scheduler, scaler, gradient accumulation, and other workspace-specific state require explicit capture. Runtime controls are observed at startup, without continuous enforcement inside user code. A raw external input declaration supplies a source path and declared role; snapshot capture establishes the observed bytes. Configured data roles do not establish that the scientific dataset was correctly labeled. These limits qualify the corresponding formal assumptions rather than becoming undocumented implementation guarantees.

### Limits of the conclusion

Let $P(q,r)$ mean that the implemented checks accept recorded evidence $r$ for plan $q$. Acceptance establishes $P(q,r)$, subject to the trusted code, storage, hashing, and observation assumptions. It does not alone imply every unobserved action of the execution satisfied $q$, nor that all permitted executions produce identical bytes. This distinguishes record consistency, observed runtime agreement, repeated-output comparison, and the conditional reproducibility theorem.

### Verification owners and observing tests

| Relationship | Source owner | Existing observing tests |
|---|---|---|
| Plan, source, selection, inputs, and config | [src/viper/_verification/plan.py](../viper/src/viper/_verification/plan.py) | [tests/test_plan_execution.py](../viper/tests/test_plan_execution.py) |
| Attempt, invocation, startup, and external input evidence | [src/viper/_verification/attempt.py](../viper/src/viper/_verification/attempt.py) | [tests/test_verification_acceptance.py](../viper/tests/test_verification_acceptance.py) |
| Run-result and lineage traversal | [src/viper/verification.py](../viper/src/viper/verification.py) | [tests/test_verification.py](../viper/tests/test_verification.py) |
| Policy resolution and observed controls | [src/viper/runtime.py](../viper/src/viper/runtime.py) | [tests/test_execution_policy_controls.py](../viper/tests/test_execution_policy_controls.py) |
| Supported checkpoint capture/restore | [src/viper/resume.py](../viper/src/viper/resume.py) | [tests/test_resume.py](../viper/tests/test_resume.py) |
| Metric lifecycle and binding | [src/viper/metrics.py](../viper/src/viper/metrics.py) | [tests/test_metric_interface.py](../viper/tests/test_metric_interface.py) |
| Independent confirmation and comparisons | [src/viper/execution/_benchmark.py](../viper/src/viper/execution/_benchmark.py) | [tests/test_benchmark_execution.py](../viper/tests/test_benchmark_execution.py) |
| Reuse selection and evidence | [src/viper/reuse.py](../viper/src/viper/reuse.py) | [tests/test_verification_acceptance.py](../viper/tests/test_verification_acceptance.py) |

## 22. Execution and publication sequence

1. Commit workspace implementation, loaders, config classes, environment lockfile, and authored experiment declarations. `read_source()` supplies source identity through the public repository API.
2. Construct experiment/stage/output/metric declarations and a RunPlanDraft through `plan()`. Select reproducible, relaxed, or explicit custom settings. A plan does not execute model code.
3. Call `execution.run(draft)` or pass a path to an existing saved RunSpec. The draft path compiles and publishes the plan before execution; users do not need to call the internal freezing helper.
4. Allocate an attempt, materialize verified inputs, and visit the ordered stages. Resolve a verified reuse candidate when permitted; otherwise start the stage worker under the selected controls.
5. Capture startup evidence inside the invocation's autocast context, invoke the workspace callable or runner-owned download operation, and retain timing, invocation, retrieval, and metric evidence.
6. Publish each resolved stage and output snapshot, verify it, and append the stage result to the attempt. Publish the terminal attempt record with its journal, logs, measurement files, and evidence references.
7. Publish ResolvedRun and verify its referenced graph. Return RunResult. Use result.status, result.path, result.reference, and result.record directly.
8. Optionally run an independent benchmark confirmation, restore artifacts, or promote an eligible artifact. Batch execution returns one outcome per input in input order and retains failures explicitly.

Logical publication dependencies are source → plan → invocation/execution evidence → stage snapshot → attempt → terminal run → optional benchmark → optional pointer. Different storage destinations implement those immutable references; the public Python workflow is independent of the transport choice.

MCP exposes structured operations for discovery, saved-plan execution, verification, run/measurement search, lineage, and comparison. `tools/list`, get_capabilities, get_schema, and viper://guide establish the installed interface. Access mode limits the available operations. Catalog entries index records; catalog membership alone does not prove verification or authorize executable source.

[Python declarations](viper-protocol-declarations.md#22-execution-and-publication-sequence).

## 23. Repository layout

### Workspace layout

The following layout separates workspace-owned Python code from VIPER's canonical generated paths. `src/research/` and `workflows/` are recommendations; a workspace may use another source layout. Run, stage, attempt, and output locations below reflect current path construction. Optional directories appear only when their operation is used.

```text
workspace/
├── viper.toml
├── pyproject.toml
├── requirements.lock                 # example lockfile name; env chooses it
├── src/research/                     # recommended workspace code
│   ├── configs.py
│   ├── preprocessing.py
│   ├── models.py
│   ├── training.py
│   ├── metrics.py
│   └── loaders.py
├── workflows/
│   └── run_experiment.py             # parameterless main; public authoring API
├── tests/
├── data/                             # external source files, if used
├── benchmarks/
│   └── <benchmark_id>.spec.yaml
├── experiments/<experiment_id>/
│   ├── spec.yaml
│   ├── variants/<variant_id>.spec.yaml
│   └── runs/<variant_id>/<run_id>/
│       ├── spec.yaml
│       ├── resolved.yaml
│       ├── benchmark.result.yaml     # optional
│       ├── stages/<stage_id>/
│       │   ├── spec.yaml
│       │   ├── resolved.yaml
│       │   ├── reuse.yaml             # when a stage is reused
│       │   └── retrievals/<input_name>/body
│       ├── artifacts/<stage_id>/<output_name>/<relative_path>
│       └── attempts/<attempt_id>/
│           ├── resolved.yaml
│           ├── journal.jsonl
│           ├── invocations/<stage_id>.yaml
│           ├── measurements/<stage_id>.<metric_id>.jsonl
│           ├── metric_verification/<stage_id>.<metric_id>.yaml
│           └── logs/<stage_id>.{stdout,stderr}.log
└── .viper/
    ├── store/                        # immutable local objects
    ├── workspaces/                   # materialized execution workspaces
    ├── pointers/<run_digest>/<stage_id>/<output_name>.pointer.yaml
    ├── catalog.sqlite3
    └── knowledge/
```

Pointer paths are constructed by output_pointer_path() and checked by references.py. They select a run digest, stage, and output rather than a manually assigned dataset/model category. Train output names are model and resume_state; eval output name is predictions. Additional output names are workspace-defined. A bundle occupies its declared output directory; file members remain beneath it. Reuse receipts use `stages/<stage_id>/reuse.yaml` beneath the run root. Captured external inputs use `.viper/workspaces/<run_id>/attempt-<attempt_id>/inputs/<stage_id>/<input_name><source_suffix>`; their SnapshotFileRef fixes the exact persisted identity.

`viper.toml` marks the workspace root. The absolute machine path is local configuration. Relative protocol paths are resolved through that root and the referenced source/store. Visible working files may differ from published immutable copies; verification and restoration follow recorded identities.

### VIPER package layout

This is the current source-package tree, excluding caches. The first underscore-prefixed package/module marks an internal boundary; public imports follow the domain module named by the API reference. Workspace programs should not import the worker or verifier implementation packages.

```text
src/viper/
├── _config/
│   ├── __init__.py
│   └── validation.py
├── _verification/
│   ├── __init__.py
│   ├── attempt.py
│   ├── metrics.py
│   ├── paths.py
│   ├── plan.py
│   ├── runtime.py
│   └── storage.py
├── _workers/
│   ├── __init__.py
│   ├── artifacts.py
│   ├── config.py
│   ├── metrics.py
│   └── stages.py
├── execution/
│   ├── __init__.py
│   ├── _attempt.py
│   ├── _batch.py
│   ├── _benchmark.py
│   ├── _downloads.py
│   ├── _materialization.py
│   ├── _metric.py
│   ├── _process.py
│   ├── _publication.py
│   ├── _recovery.py
│   ├── _resolution.py
│   ├── _restore.py
│   ├── _reuse.py
│   ├── _run.py
│   ├── _source.py
│   ├── _stage.py
│   ├── errors.py
│   └── results.py
├── __init__.py
├── _schema.py
├── _subprocess.py
├── api.py
├── artifact_loaders.py
├── artifacts.py
├── authoring.py
├── benchmark.py
├── catalog.py
├── cli.py
├── config.py
├── evidence.py
├── experiments.py
├── http.py
├── ids.py
├── inputs.py
├── inspection.py
├── journal.py
├── keys.py
├── knowledge.py
├── mcp.py
├── metrics.py
├── outputs.py
├── preflight.py
├── randomness.py
├── references.py
├── repository.py
├── restoration.py
├── resume.py
├── reuse.py
├── runs.py
├── runtime.py
├── serialization.py
├── stages.py
├── storage.py
├── verification.py
├── worker.py
└── workspace.py
```

### Public interface and complete examples

- [docs/reference/api.md](../viper/docs/reference/api.md)
- [docs/reference/agents.md](../viper/docs/reference/agents.md)
- [examples/cpu_quickstart.py](../viper/examples/cpu_quickstart.py)
- [examples/stages.py](../viper/examples/stages.py)
- [examples/evaluation.py](../viper/examples/evaluation.py)
- [examples/variants.py](../viper/examples/variants.py)
- [examples/recovery.py](../viper/examples/recovery.py)
- [examples/execution_policies.py](../viper/examples/execution_policies.py)
- [tests/test_readme_workflow.py](../viper/tests/test_readme_workflow.py)

## Appendix A. Complete training-state transition

The derivation describes the full state needed by the chosen training algorithm. The built-in ResumeState helper captures the components listed in Section 18; additional scheduler, scaler, accumulation, or application state requires explicit workspace capture and restoration. A formal state variable does not imply an automatic capture mechanism.

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
The diagrams assume `persistent_workers=False`. These ordinary PyTorch DataLoader examples explain generator consumption. VIPER's capture_resume_state() requires a torchdata StatefulDataLoader, whose state_dict() also records resumable iteration state.

The generator states after iterator creation and randomized index generation
form $r_{k,\mathrm{sampling}}^{(t+1)}$. The generator states after retrieval,
transformation, and collation form $r_{k,\mathrm{batch}}^{(t+1)}$. The shuffled
index sequence, its unread position, and any prefetched work are components of
$b_{k,\mathrm{batch}}^{(t+1)}$.

### Single-process loading

```python
import torch
from torch.utils.data import DataLoader, TensorDataset

run_seed = 7
batch_size = 2
dataset = TensorDataset(torch.arange(8))
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
├── RandomSampler draws a final permutation for its remainder branch
│   └── zero remaining indices are yielded, but g still advances
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

For this default without-replacement sampler, exhausting the iterator advances the generator once more: RandomSampler evaluates a final randperm before taking the empty remainder slice. Saving generator state after the last yielded batch therefore differs from saving it after StopIteration. A checkpoint must preserve the actual iterator position as well as the RNG state.

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
import torch
from torch.utils.data import DataLoader, RandomSampler, TensorDataset

run_seed = 7
batch_size = 2
dataset = TensorDataset(torch.arange(8))
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
and shuffled-permutation generation. The examples use one shared generator to make its state transitions explicit. VIPER does not require the DataLoader and sampler to share a generator; exact continuation requires capturing the state of whichever configuration the workspace actually uses.

### Epoch boundary

When the training procedure defines one epoch as one complete DataLoader pass:

```text
one epoch
├── begins with iterator = iter(loader)
├── consumes batches through repeated next(iterator)
└── ends when the iterator raises StopIteration
```

The next epoch begins with another `iter(loader)` call.

The historical source references below use PyTorch 2.13.0. Iterator creation, shuffled-index generation, and the exhaustion draw were also checked against installed PyTorch 2.14.0:

- [`DataLoader` iterator and base-seed construction](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/dataloader.py#L639-L644);
- [`RandomSampler`](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/sampler.py#L146-L170);
- [`BatchSampler`](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/sampler.py#L306-L316);
- [multiprocess prefetching](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/dataloader.py#L1274-L1276);
- [worker-queue index dispatch](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/dataloader.py#L1531-L1557); and
- [worker RNG initialization](https://github.com/pytorch/pytorch/blob/v2.13.0/torch/utils/data/_utils/worker.py#L274-L281).
