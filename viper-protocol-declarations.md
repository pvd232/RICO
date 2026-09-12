# Appendix C. Python declarations

Field definitions and inheritance for the [VIPER protocol](viper-protocol.md). Each declaration links to its defining source and validators at the revision named in the protocol. Workspace programs import these types from VIPER; these excerpts omit method bodies.

## Contents

- [8. Artifact partition of a training checkpoint](#8-artifact-partition-of-a-training-checkpoint)
- [12. Protocol record roles](#12-protocol-record-roles)
- [13. File, artifact, and stage-result records](#13-file-artifact-and-stage-result-records)
- [14. Run, input, and attempt records](#14-run-input-and-attempt-records)
- [15. Environment, reproducibility, and execution records](#15-environment-reproducibility-and-execution-records)
- [16. Experiment, variant, replicate, and measurement records](#16-experiment-variant-replicate-and-measurement-records)
- [17. Concrete stage records](#17-concrete-stage-records)
- [18. Training checkpoint mapping](#18-training-checkpoint-mapping)
- [20. Benchmark specification and confirmation](#20-benchmark-specification-and-confirmation)
- [22. Execution and publication sequence](#22-execution-and-publication-sequence)

## 8. Artifact partition of a training checkpoint

[Protocol discussion](viper-protocol.md#8-artifact-partition-of-a-training-checkpoint).

### PythonRNGState

[PythonRNGState source](../viper/src/viper/randomness.py) (line 17).

```python
class PythonRNGState(ProtocolModel):
    "Serializable state returned by Python's global random generator."
    version: int = Field(ge=0)
    internal_state: tuple[int, ...] = Field(min_length=1)
    gaussian_cache: float | None
```

### PCG64InternalState

[PCG64InternalState source](../viper/src/viper/randomness.py) (line 31).

```python
class PCG64InternalState(ProtocolModel):
    'The 128-bit state and stream increment of one PCG64 generator.'
    state: UInt128
    inc: UInt128
```

### PCG64GeneratorState

[PCG64GeneratorState source](../viper/src/viper/randomness.py) (line 38).

```python
class PCG64GeneratorState(ProtocolModel):
    'Complete state required to restore one NumPy PCG64 generator.'
    bit_generator: Literal["PCG64"] = "PCG64"
    state: PCG64InternalState
    has_uint32: Literal[0, 1]
    uinteger: UInt32
```

### LegacyNumPyRNGState

[LegacyNumPyRNGState source](../viper/src/viper/randomness.py) (line 47).

```python
class LegacyNumPyRNGState(ProtocolModel):
    "Complete state required to restore NumPy's global MT19937 generator."
    bit_generator: Literal["MT19937"] = "MT19937"
    keys: tuple[UInt32, ...] = Field(min_length=624, max_length=624)
    position: int = Field(ge=0, le=624)
    has_gaussian: Literal[0, 1]
    cached_gaussian: float = Field(allow_inf_nan=False)
```

### NumPyRNGState

[NumPyRNGState source](../viper/src/viper/randomness.py) (line 57).

```python
class NumPyRNGState(ProtocolModel):
    'Named PCG64 states and the optional legacy global NumPy state.'
    generators: dict[HumanId, PCG64GeneratorState]
    legacy_global: LegacyNumPyRNGState | None
```

### MainProcessRNGState

[MainProcessRNGState source](../viper/src/viper/randomness.py) (line 64).

```python
class MainProcessRNGState(ProtocolModel):
    'Generator states owned by the main training process.'
    python: PythonRNGState
    numpy: NumPyRNGState
    torch_cpu: bytes = Field(min_length=1)
    torch_cuda: tuple[bytes, ...]
```

### DataLoaderConfiguration

[DataLoaderConfiguration source](../viper/src/viper/resume.py) (line 23).

```python
class DataLoaderConfiguration(ProtocolModel):
    'Fix worker and prefetch behavior for the training DataLoader.'
    workers: int = Field(ge=0)
    prefetch_factor: int | None = Field(default=None, ge=1)
    persistent_workers: bool = False
    in_order: Literal[True] = True
```

Validation: Enforce valid worker, prefetch, and persistence combinations.

### DataLoaderResumeState

[DataLoaderResumeState source](../viper/src/viper/resume.py) (line 45).

```python
class DataLoaderResumeState(ProtocolModel):
    'DataLoader configuration and state restored at a checkpoint.'
    configuration: DataLoaderConfiguration
    state_dict: dict[str, object] = Field(min_length=1)
```

### ResumeState

[ResumeState source](../viper/src/viper/resume.py) (line 52).

```python
class ResumeState(ProtocolModel):
    'State required to continue one training stage exactly.'
    schema_version: Literal[1] = 1
    optimizer_state: dict[str, object] = Field(min_length=1)
    main_process_rng: MainProcessRNGState
    dataloader: DataLoaderResumeState
```

## 12. Protocol record roles

[Protocol discussion](viper-protocol.md#12-protocol-record-roles).

### StageDraftOutputRef

[StageDraftOutputRef source](../viper/src/viper/authoring.py) (line 184).

```python
class StageDraftOutputRef():
    'Select one output promised by an in-memory stage draft.'
    producer: StageDraft
    output_name: OutputName
```

### StageDraft

[StageDraft source](../viper/src/viper/authoring.py) (line 311).

```python
class StageDraft(BaseModel):
    'Hold one validated Python stage declaration before freezing.'
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)
    spec: StageSpecDraft
    stage_id: StageId | None = Field(
            default=None, description="Name of this stage within a variant."
        )
```

### VariantDraft

[VariantDraft source](../viper/src/viper/authoring.py) (line 383).

```python
class VariantDraft(BaseModel):
    "Hold one variant's factor levels, stages, and estimator."
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)
    levels: dict[FactorId, LevelId]
    stages: dict[StageId, StageDraft] = Field(min_length=1)
    estimator: StageDraftOutputRef
    variant_id: VariantId | None = Field(
            default=None, description="Name used to select this variant in an experiment."
        )
```

Validation: Require the estimator to come from this variant's stage graph.

### ExperimentDraft

[ExperimentDraft source](../viper/src/viper/authoring.py) (line 414).

```python
class ExperimentDraft(BaseModel):
    'Hold the reusable variants and replicates in one experiment.'
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)
    experiment_id: ExperimentId
    factors: dict[FactorId, FactorDraft] = Field(default_factory=dict)
    variants: dict[VariantId, VariantDraft] = Field(min_length=1)
    replicates: dict[ReplicateId, ReplicateDraft] = Field(min_length=1)
```

Validation: Require every variant level to belong to its declared factor.

### RunPlanDraft

[RunPlanDraft source](../viper/src/viper/authoring.py) (line 436).

```python
class RunPlanDraft(BaseModel):
    'Select one immutable experiment variant and replicate for execution.'
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)
    schema_version: Literal[2] = 2
    run_id: RunId
    experiment: ExperimentDraft
    variant: VariantId
    replicate: ReplicateId
    benchmark: BenchmarkDraft | None = None
    source: GitSource
    env: EnvSpec
    reproducibility: ReproducibilitySpec
    execution_policy: ExecutionPolicyRef = Field(
            description="Policy selected during authoring",
        )
```

## 13. File, artifact, and stage-result records

[Protocol discussion](viper-protocol.md#13-file-artifact-and-stage-result-records).

### ProtocolModel

[ProtocolModel source](../viper/src/viper/_schema.py) (line 65).

```python
class ProtocolModel(BaseModel):
    'Closed, frozen protocol object.'
    model_config = ConfigDict(extra="forbid", frozen=True)
```

### Config

[Config source](../viper/src/viper/config.py) (line 22).

```python
class Config(BaseModel):
    'A versioned JSON config mapping that workspace classes may specialize.'
    model_config = ConfigDict(extra="allow", frozen=True)
    schema_version: Literal[2] = 2
```

Validation: Keep workspace-defined config fields JSON serializable.

### BuildConfig

[BuildConfig source](../viper/src/viper/config.py) (line 38).

```python
class BuildConfig(Config):
    'Config consumed by one workspace-defined build stage.'
```

### EmbedConfig

[EmbedConfig source](../viper/src/viper/config.py) (line 42).

```python
class EmbedConfig(Config):
    'Config consumed by one workspace-defined embedding stage.'
```

### TrainConfig

[TrainConfig source](../viper/src/viper/config.py) (line 46).

```python
class TrainConfig(Config):
    'Config consumed by one workspace-defined training procedure.'
```

### EvalConfig

[EvalConfig source](../viper/src/viper/config.py) (line 50).

```python
class EvalConfig(Config):
    'Model-specific config outside the shared eval contract.'
```

Validation: Keep metric IDs and split inputs on EvalSpec.

### MetricConfig

[MetricConfig source](../viper/src/viper/config.py) (line 62).

```python
class MetricConfig(Config):
    'Config consumed by one workspace-defined metric.'
```

### HttpConfig

[HttpConfig source](../viper/src/viper/config.py) (line 66).

```python
class HttpConfig(Config):
    'Config consumed by one workspace-defined HTTP implementation.'
```

### DiagnosticConfig

[DiagnosticConfig source](../viper/src/viper/config.py) (line 70).

```python
class DiagnosticConfig(Config):
    'Config consumed by one workspace-defined diagnostic stage.'
```

### ConfigTypeRef

[ConfigTypeRef source](../viper/src/viper/config.py) (line 77).

```python
class ConfigTypeRef(ProtocolModel):
    'Identify one config class by owner, source bytes, and symbol.'
    owner: ConfigOwner
    path: PythonSourceRelPath
    symbol: PythonSymbol
    sha256: SHA256
    bytes: int = Field(gt=0)
```

### GitSource

[GitSource source](../viper/src/viper/references.py) (line 14).

```python
class GitSource(ProtocolModel):
    'A repository snapshot identified by an exact Git commit.'
    kind: Literal["git"] = "git"
    repository: HttpUrl
    commit: GitCommit
```

### GitFileRef

[GitFileRef source](../viper/src/viper/references.py) (line 22).

```python
class GitFileRef(GitSource):
    'A file stored at an exact Git revision.'
    path: RepoRelPath
```

### ArtifactPointerRef

[ArtifactPointerRef source](../viper/src/viper/references.py) (line 61).

```python
class ArtifactPointerRef(GitFileRef):
    'A Git reference to the pointer selecting a promoted artifact.'
```

Validation: Enforce the canonical promoted-input pointer path.

### HuggingFaceFileRef

[HuggingFaceFileRef source](../viper/src/viper/references.py) (line 71).

```python
class HuggingFaceFileRef(ProtocolModel):
    'A file stored at an exact Hugging Face repository revision.'
    kind: Literal["huggingface"] = "huggingface"
    repository: NonEmptyStr
    commit: GitCommit
    path: RepoRelPath
    repo_type: Literal["model", "dataset", "space"]
```

### LocalFileRef

[LocalFileRef source](../viper/src/viper/references.py) (line 81).

```python
class LocalFileRef(ProtocolModel):
    'A file in one immutable revision of a repository-local VIPER store.'
    kind: Literal["local"] = "local"
    store: RepoRelPath = ".viper/store"
    commit: SHA256
    path: RepoRelPath
```

### LocalStageResultSnapshotRef

[LocalStageResultSnapshotRef source](../viper/src/viper/references.py) (line 90).

```python
class LocalStageResultSnapshotRef(ProtocolModel):
    'One immutable stage-result revision in a repository-local VIPER store.'
    kind: Literal["local"] = "local"
    store: RepoRelPath = ".viper/store"
    commit: SHA256
```

### HuggingFaceStageResultSnapshotRef

[HuggingFaceStageResultSnapshotRef source](../viper/src/viper/references.py) (line 98).

```python
class HuggingFaceStageResultSnapshotRef(ProtocolModel):
    'The immutable repository revision containing one completed stage.'
    kind: Literal["huggingface"] = "huggingface"
    repository: NonEmptyStr
    commit: GitCommit
    repo_type: Literal["model", "dataset", "space"]
```

### ViperCloudFileRef

[ViperCloudFileRef source](../viper/src/viper/references.py) (line 107).

```python
class ViperCloudFileRef(ProtocolModel):
    'A file in one sealed Viper Cloud revision.'
    kind: Literal["viper_cloud"] = "viper_cloud"
    owner: HumanId
    workspace: HumanId
    revision: SHA256
    path: RepoRelPath
```

### ViperCloudStageResultSnapshotRef

[ViperCloudStageResultSnapshotRef source](../viper/src/viper/references.py) (line 117).

```python
class ViperCloudStageResultSnapshotRef(ProtocolModel):
    'One sealed stage snapshot in Viper Cloud.'
    kind: Literal["viper_cloud"] = "viper_cloud"
    owner: HumanId
    workspace: HumanId
    revision: SHA256
```

### ResolvedFileRef

[ResolvedFileRef source](../viper/src/viper/references.py) (line 141).

```python
class ResolvedFileRef(ProtocolModel):
    'Identify one hashed file and its immutable storage location.'
    sha256: SHA256
    bytes: int = Field(ge=0)
    stored_at: StorageRef
```

### SnapshotFileRef

[SnapshotFileRef source](../viper/src/viper/references.py) (line 149).

```python
class SnapshotFileRef(ProtocolModel):
    'Identify one exact file within a stage-result snapshot.'
    path: RepoRelPath
    sha256: SHA256
    bytes: int = Field(ge=0)
```

### ResolvedGitFileRef

[ResolvedGitFileRef source](../viper/src/viper/references.py) (line 157).

```python
class ResolvedGitFileRef(ResolvedFileRef):
    'Identify an exact file stored at an immutable Git revision.'
    stored_at: GitFileRef
```

### ResolvedStageRef

[ResolvedStageRef source](../viper/src/viper/references.py) (line 163).

```python
class ResolvedStageRef(ProtocolModel):
    'Binds one completed stage to its immutable stage-result snapshot.'
    stage_id: StageId
    snapshot: StageResultSnapshot
    resolved_spec: SnapshotFileRef
```

### ResolvedStageInvocationRef

[ResolvedStageInvocationRef source](../viper/src/viper/references.py) (line 171).

```python
class ResolvedStageInvocationRef(ResolvedFileRef):
    'Identify one immutable stage-invocation receipt.'
    kind: Literal["stage_invocation"] = "stage_invocation"
```

### ResolvedArtifactPointerRef

[ResolvedArtifactPointerRef source](../viper/src/viper/references.py) (line 177).

```python
class ResolvedArtifactPointerRef(ResolvedFileRef):
    'Identify an exact verified artifact-pointer file.'
    kind: Literal["artifact_pointer"] = "artifact_pointer"
```

Validation: Enforce the pointer path for every storage backend.

### ResolvedRunSpecRef

[ResolvedRunSpecRef source](../viper/src/viper/references.py) (line 189).

```python
class ResolvedRunSpecRef(ResolvedFileRef):
    'Identify the exact run specification governing one run.'
    kind: Literal["run_spec"] = "run_spec"
```

### ResolvedRunRef

[ResolvedRunRef source](../viper/src/viper/references.py) (line 195).

```python
class ResolvedRunRef(ResolvedFileRef):
    'Identify one terminal resolved-run document.'
    kind: Literal["resolved_run"] = "resolved_run"
```

### ResolvedBenchmarkSpecRef

[ResolvedBenchmarkSpecRef source](../viper/src/viper/references.py) (line 201).

```python
class ResolvedBenchmarkSpecRef(ResolvedFileRef):
    'Identify the exact benchmark specification applied to a run.'
    kind: Literal["benchmark_spec"] = "benchmark_spec"
```

### ResolvedBenchmarkResultRef

[ResolvedBenchmarkResultRef source](../viper/src/viper/references.py) (line 207).

```python
class ResolvedBenchmarkResultRef(ResolvedFileRef):
    'Identify one completed benchmark result.'
    kind: Literal["benchmark_result"] = "benchmark_result"
```

### OutputDraft

[OutputDraft source](../viper/src/viper/outputs.py) (line 20).

```python
class OutputDraft(BaseModel):
    'Hold one callable-backed output before protocol freezing.'
    model_config = ConfigDict(
            arbitrary_types_allowed=True,
            extra="forbid",
            frozen=True,
        )
    kind: Literal["file", "bundle"] = "file"
    path: RepoRelPath
    loader: Callable[[Path], Any]
    data_role: DataRole
```

### OutputSpec

[OutputSpec source](../viper/src/viper/outputs.py) (line 35).

```python
class OutputSpec(ProtocolModel):
    'Declare one output using an exact loader reference.'
    kind: Literal["file", "bundle"] = "file"
    path: RepoRelPath
    loader: ArtifactLoaderRef
    data_role: DataRole
```

### StageOutputs

[StageOutputs source](../viper/src/viper/outputs.py) (line 44).

```python
class StageOutputs(BaseModel, Generic[OutputT]):
    'Map workspace-defined output names to values of one lifecycle type.'
    model_config = ConfigDict(extra="allow", frozen=True)
```

Validation: Validate extra fields through the concrete generic output type; Require at least one stable Python identifier.

### TrainOutputs

[TrainOutputs source](../viper/src/viper/outputs.py) (line 111).

```python
class TrainOutputs(StageOutputs[OutputT], Generic[OutputT]):
    'Require the two values needed to restore training.'
    model: OutputT
    resume_state: OutputT
```

### EvalOutputs

[EvalOutputs source](../viper/src/viper/outputs.py) (line 118).

```python
class EvalOutputs(StageOutputs[OutputT], Generic[OutputT]):
    'Require the canonical evaluation result.'
    predictions: OutputT
```

### StageArtifactRef

[StageArtifactRef source](../viper/src/viper/artifacts.py) (line 36).

```python
class StageArtifactRef(ProtocolModel):
    'Select one named artifact produced by one stage.'
    stage_id: StageId
    artifact_name: ArtifactName
```

### ArtifactPointer

[ArtifactPointer source](../viper/src/viper/artifacts.py) (line 43).

```python
class ArtifactPointer(ProtocolModel):
    'Select one artifact accepted as a reusable input.'
    schema_version: Literal[2] = 2
    run: ResolvedRunRef
    artifact: StageArtifactRef
    benchmark_result: ResolvedBenchmarkResultRef | None = None
```

### ArtifactLoaderRef

[ArtifactLoaderRef source](../viper/src/viper/artifacts.py) (line 52).

```python
class ArtifactLoaderRef(ProtocolModel):
    'Identify one workspace-owned artifact loader by exact file bytes.'
    path: PythonRepoRelPath
    symbol: PythonSymbol = "load"
    sha256: SHA256
    bytes: int = Field(gt=0)
```

### SingleFileArtifactSpec

[SingleFileArtifactSpec source](../viper/src/viper/artifacts.py) (line 61).

```python
class SingleFileArtifactSpec(ProtocolModel):
    'Declare one named artifact written as one file.'
    kind: Literal["file"] = "file"
    path: RepoRelPath
    loader: ArtifactLoaderRef
    data_role: DataRole
```

### BundleArtifactSpec

[BundleArtifactSpec source](../viper/src/viper/artifacts.py) (line 70).

```python
class BundleArtifactSpec(ProtocolModel):
    'Declare one named artifact written beneath one directory root.'
    kind: Literal["bundle"] = "bundle"
    path: RepoRelPath
    loader: ArtifactLoaderRef
    data_role: DataRole
```

### ResolvedSingleFileArtifact

[ResolvedSingleFileArtifact source](../viper/src/viper/artifacts.py) (line 85).

```python
class ResolvedSingleFileArtifact(ProtocolModel):
    'Record the exact file representing one artifact.'
    kind: Literal["file"] = "file"
    file: SnapshotFileRef
```

### ResolvedBundleMember

[ResolvedBundleMember source](../viper/src/viper/artifacts.py) (line 92).

```python
class ResolvedBundleMember(ProtocolModel):
    "Record one exact file beneath a bundle artifact's directory root."
    relative_path: RepoRelPath
    file: SnapshotFileRef
```

### ResolvedBundleArtifact

[ResolvedBundleArtifact source](../viper/src/viper/artifacts.py) (line 99).

```python
class ResolvedBundleArtifact(ProtocolModel):
    'Record every exact file representing one bundle artifact.'
    kind: Literal["bundle"] = "bundle"
    members: tuple[ResolvedBundleMember, ...] = Field(min_length=2)
```

Validation: Require unique, ordered, and nonoverlapping bundle member paths.

### SingleFileArtifactDraft

[SingleFileArtifactDraft source](../viper/src/viper/artifacts.py) (line 139).

```python
class SingleFileArtifactDraft(BaseModel):
    'Hold one callable-backed file artifact before freezing.'
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)
    kind: Literal["file"] = "file"
    path: RunArtifactPath
    loader: Callable[[Path], Any]
    data_role: DataRole
```

### BundleArtifactDraft

[BundleArtifactDraft source](../viper/src/viper/artifacts.py) (line 150).

```python
class BundleArtifactDraft(BaseModel):
    'Hold one callable-backed artifact directory before freezing.'
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)
    kind: Literal["bundle"] = "bundle"
    path: RunArtifactPath
    loader: Callable[[Path], Any]
    data_role: DataRole
```

## 14. Run, input, and attempt records

[Protocol discussion](viper-protocol.md#14-run-input-and-attempt-records).

### AttemptFailure

[AttemptFailure source](../viper/src/viper/runs.py) (line 58).

```python
class AttemptFailure(ProtocolModel):
    'Identify the operation that terminated one unsuccessful attempt.'
    code: AttemptFailureCode
    stage_id: StageId | None
    message: NonEmptyStr
    occurred_at: AwareDatetime
```

### AttemptJournalRef

[AttemptJournalRef source](../viper/src/viper/runs.py) (line 67).

```python
class AttemptJournalRef(ResolvedFileRef):
    'Identify one immutable attempt journal.'
    kind: Literal["attempt_journal"] = "attempt_journal"
```

### RunAttempt

[RunAttempt source](../viper/src/viper/runs.py) (line 73).

```python
class RunAttempt(ProtocolModel):
    'Record the status and published files of one run attempt.'
    schema_version: Literal[2] = 2
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
```

Validation: Enforce attempt outcome, timing, stage, and file invariants.

### ResolvedAttemptRef

[ResolvedAttemptRef source](../viper/src/viper/runs.py) (line 182).

```python
class ResolvedAttemptRef(ResolvedFileRef):
    'Identify one canonical immutable RunAttempt document.'
    kind: Literal["resolved_attempt"] = "resolved_attempt"
```

### RunStageRef

[RunStageRef source](../viper/src/viper/runs.py) (line 188).

```python
class RunStageRef(ProtocolModel):
    'Identifies and verifies one stage spec in a run-plan snapshot.'
    stage_id: StageId
    spec: RepoRelPath
    sha256: SHA256
    bytes: int = Field(ge=0)
```

### RunSpec

[RunSpec source](../viper/src/viper/runs.py) (line 197).

```python
class RunSpec(ProtocolModel):
    'Freeze one run plan and its ordered stage specifications.'
    schema_version: Literal[2] = 2
    run_id: RunId
    experiment_id: ExperimentId
    variant_id: VariantId
    replicate_id: ReplicateId
    benchmark_id: BenchmarkId | None = None
    seed: RNGSeed
    source: GitSource
    env: EnvSpec
    reproducibility: ReproducibilitySpec
    execution_policy: ExecutionPolicyRef = Field(
            description="Selected execution policy for the run",
        )
    stages: tuple[RunStageRef, ...] = Field(min_length=1)
    estimator: StageArtifactRef
```

Validation: Enforce ordered-stage identity and estimator selection invariants.

### ResolvedRun

[ResolvedRun source](../viper/src/viper/runs.py) (line 248).

```python
class ResolvedRun(ProtocolModel):
    'Reference every attempt and record the terminal outcome of one run.'
    schema_version: Literal[2] = 2
    spec: ResolvedRunSpecRef
    status: Literal["succeeded", "failed", "cancelled"]
    attempts: tuple[ResolvedAttemptRef, ...] = Field(min_length=1)
    successful_attempt_id: int | None
    completed_at: AwareDatetime
```

Validation: Require the success selector only for a successful terminal run.

### LocalSource

[LocalSource source](../viper/src/viper/inputs.py) (line 20).

```python
class LocalSource(ProtocolModel):
    'Identify one repository-local file selected by the user.'
    kind: Literal["local"] = "local"
    path: RepoRelPath
```

### ExternalInputRef

[ExternalInputRef source](../viper/src/viper/inputs.py) (line 27).

```python
class ExternalInputRef(ProtocolModel):
    'Declare one repository-local value supplied to a stage.'
    kind: Literal["external"] = "external"
    source: LocalSource
    data_role: DataRole
```

### ResolvedExternalInputRef

[ResolvedExternalInputRef source](../viper/src/viper/inputs.py) (line 35).

```python
class ResolvedExternalInputRef(ProtocolModel):
    'Record one local input captured in its consuming stage snapshot.'
    kind: Literal["external"] = "external"
    source: LocalSource
    file: SnapshotFileRef
    data_role: DataRole
```

### StoredInputRef

[StoredInputRef source](../viper/src/viper/inputs.py) (line 66).

```python
class StoredInputRef(ProtocolModel):
    "Select a prior run's artifact through its stored pointer."
    kind: Literal["stored"] = "stored"
    pointer: PointerRef
    path: RepoRelPath
    data_role: DataRole
```

Validation: Keep materialized bytes separate from the immutable pointer file.

### FutureInputRef

[FutureInputRef source](../viper/src/viper/inputs.py) (line 87).

```python
class FutureInputRef(ProtocolModel):
    'One named artifact produced by an earlier stage in the same run.'
    kind: Literal["future"] = "future"
    producer_stage_id: StageId
    name: OutputName
```

### ResolvedStoredInputRef

[ResolvedStoredInputRef source](../viper/src/viper/inputs.py) (line 101).

```python
class ResolvedStoredInputRef(ProtocolModel):
    'Bind a stored stage input to its verified pointer file.'
    kind: Literal["stored"] = "stored"
    pointer: ResolvedArtifactPointerRef
```

### ResolvedFutureInputRef

[ResolvedFutureInputRef source](../viper/src/viper/inputs.py) (line 108).

```python
class ResolvedFutureInputRef(ProtocolModel):
    'Bind a future input to its completed producer stage.'
    kind: Literal["future"] = "future"
    producer: ResolvedStageRef
```

## 15. Environment, reproducibility, and execution records

[Protocol discussion](viper-protocol.md#15-environment-reproducibility-and-execution-records).

### GCEBootImageRef

[GCEBootImageRef source](../viper/src/viper/runtime.py) (line 37).

```python
class GCEBootImageRef(ProtocolModel):
    'Select one immutable Google Compute Engine boot image.'
    kind: Literal["boot_image"] = "boot_image"
    project: NonEmptyStr
    name: NonEmptyStr
    id: NonEmptyStr
```

### GCEMachineImageRef

[GCEMachineImageRef source](../viper/src/viper/runtime.py) (line 46).

```python
class GCEMachineImageRef(ProtocolModel):
    'Select one immutable Google Compute Engine machine image.'
    kind: Literal["machine_image"] = "machine_image"
    project: NonEmptyStr
    name: NonEmptyStr
    id: NonEmptyStr
```

### PythonDistributionSpec

[PythonDistributionSpec source](../viper/src/viper/runtime.py) (line 61).

```python
class PythonDistributionSpec(ProtocolModel):
    'Fix one normalized installed Python distribution and version.'
    name: NormalizedDistributionName
    version: NonEmptyStr
```

### CPUComputeSpec

[CPUComputeSpec source](../viper/src/viper/runtime.py) (line 68).

```python
class CPUComputeSpec(ProtocolModel):
    'Request CPU execution for a stage.'
    kind: Literal["cpu"] = "cpu"
```

### CUDAComputeSpec

[CUDAComputeSpec source](../viper/src/viper/runtime.py) (line 74).

```python
class CUDAComputeSpec(ProtocolModel):
    'Request a specific CUDA device model and count.'
    kind: Literal["cuda"] = "cuda"
    model: NonEmptyStr
    count: int = Field(ge=1)
```

### NumPyRandomnessSpec

[NumPyRandomnessSpec source](../viper/src/viper/runtime.py) (line 88).

```python
class NumPyRandomnessSpec(ProtocolModel):
    'Named NumPy generators and legacy-global capture applied run-wide.'
    generators: dict[HumanId, Literal["PCG64"]] = Field(default_factory=dict)
    capture_legacy_global: bool = False
```

### TorchDeterminismSpec

[TorchDeterminismSpec source](../viper/src/viper/runtime.py) (line 95).

```python
class TorchDeterminismSpec(ProtocolModel):
    'PyTorch, cuDNN, and cuBLAS determinism controls.'
    deterministic_algorithms: bool
    deterministic_warn_only: bool
    cudnn_deterministic: bool
    cudnn_benchmark: bool
    cublas_workspace_config: Literal[":16:8", ":4096:8"] | None
```

### TorchPrecisionSpec

[TorchPrecisionSpec source](../viper/src/viper/runtime.py) (line 105).

```python
class TorchPrecisionSpec(ProtocolModel):
    'PyTorch numerical-precision controls that can affect output values.'
    float32_matmul_precision: Literal["highest", "high", "medium"]
    cudnn_allow_tf32: bool
    autocast_enabled: bool
    autocast_dtype: Literal["float16", "bfloat16"] | None
```

Validation: Require an autocast dtype exactly when autocast is enabled.

### ParallelismSpec

[ParallelismSpec source](../viper/src/viper/runtime.py) (line 128).

```python
class ParallelismSpec(ProtocolModel):
    'Fix process, thread-pool, and DataLoader parallelism run-wide.'
    process_count: int = Field(ge=1)
    torch_intraop_threads: int = Field(ge=1)
    torch_interop_threads: int = Field(ge=1)
    dataloader: DataLoaderConfiguration
```

### ReproducibilitySpec

[ReproducibilitySpec source](../viper/src/viper/runtime.py) (line 138).

```python
class ReproducibilitySpec(ProtocolModel):
    'Numerical controls applied to every stage in a run.'
    determinism: TorchDeterminismSpec
    precision: TorchPrecisionSpec
    parallelism: ParallelismSpec
    numpy_randomness: NumPyRandomnessSpec
```

### ExecutionPolicyRef

[ExecutionPolicyRef source](../viper/src/viper/runtime.py) (line 147).

```python
class ExecutionPolicyRef(ProtocolModel):
    'Identify the mode and version used to select execution settings.'
    mode: Literal["reproducible", "relaxed", "custom"] = Field(
            description="Preset used to select settings, or custom for caller settings."
        )
    version: Literal[1] = Field(
            default=1,
            description="Version of the preset definitions and custom selection rules.",
        )
```

### GeneratorInitializationReceipt

[GeneratorInitializationReceipt source](../viper/src/viper/runtime.py) (line 245).

```python
class GeneratorInitializationReceipt(ProtocolModel):
    'Identify one generator state immediately after seeded initialization.'
    family: GeneratorFamily
    seed: RNGSeed
    name: HumanId | None = None
    device_index: int | None = Field(default=None, ge=0)
    state_sha256: SHA256
```

Validation: Match optional identity fields to their generator family.

### PythonEnvSpec

[PythonEnvSpec source](../viper/src/viper/runtime.py) (line 273).

```python
class PythonEnvSpec(ProtocolModel):
    'Fix the interpreter and installed distributions used by a stage.'
    python_version: NonEmptyStr
    distributions: tuple[PythonDistributionSpec, ...] = Field(min_length=1)
```

Validation: Require one canonically ordered entry for each distribution name.

### GCEEnvSpec

[GCEEnvSpec source](../viper/src/viper/runtime.py) (line 290).

```python
class GCEEnvSpec(ProtocolModel):
    'Declare the requested Google Compute Engine env.'
    kind: Literal["gce"] = "gce"
    provisioning: GCEProvisioningRef
    machine_type: NonEmptyStr
    compute: ComputeSpec
    lockfile: GitFileRef
    python_env: PythonEnvSpec
```

### ResolvedGCEEnv

[ResolvedGCEEnv source](../viper/src/viper/runtime.py) (line 301).

```python
class ResolvedGCEEnv(ProtocolModel):
    'Record the env realized for one stage execution.'
    kind: Literal["gce"] = "gce"
    provisioning: GCEProvisioningRef
    machine_type: NonEmptyStr
    compute: ComputeSpec
    lockfile: ResolvedGitFileRef
    python_env: PythonEnvSpec
```

### LocalEnvSpec

[LocalEnvSpec source](../viper/src/viper/runtime.py) (line 312).

```python
class LocalEnvSpec(ProtocolModel):
    'Declare a local development env fixed by one lockfile.'
    kind: Literal["local"] = "local"
    compute: ComputeSpec = Field(default_factory=CPUComputeSpec)
    lockfile: GitFileRef
    python_env: PythonEnvSpec
```

### ResolvedLocalEnv

[ResolvedLocalEnv source](../viper/src/viper/runtime.py) (line 321).

```python
class ResolvedLocalEnv(ProtocolModel):
    'Record the local development env used by one stage.'
    kind: Literal["local"] = "local"
    compute: ComputeSpec = Field(default_factory=CPUComputeSpec)
    lockfile: ResolvedGitFileRef
    python_env: PythonEnvSpec
```

### RuntimeControlsReceipt

[RuntimeControlsReceipt source](../viper/src/viper/runtime.py) (line 341).

```python
class RuntimeControlsReceipt(ProtocolModel):
    'Record PyTorch controls read before a worker invokes user code.'
    backend: Literal["cpu", "cuda"] = Field(
            description="Device type used for autocast queries and backend-specific checks."
        )
    deterministic_algorithms: bool = Field(
            description="Whether PyTorch required deterministic algorithms at invocation."
        )
    deterministic_warn_only: bool = Field(
            description="Whether unsupported deterministic operations warn at invocation."
        )
    cudnn_deterministic: bool = Field(
            description="Observed cuDNN determinism setting, checked for CUDA workers."
        )
    cudnn_benchmark: bool = Field(
            description="Observed cuDNN benchmarking setting, checked for CUDA workers."
        )
    cudnn_allow_tf32: bool = Field(
            description="Observed cuDNN TF32 permission, checked for CUDA workers."
        )
    float32_matmul_precision: Literal["highest", "high", "medium"] = Field(
            description="Observed internal precision for float32 matrix multiplication."
        )
    torch_intraop_threads: int = Field(
            ge=1, description="Observed CPU thread count used within a PyTorch operation."
        )
    torch_interop_threads: int = Field(
            ge=1, description="Observed CPU thread count used across PyTorch operations."
        )
    autocast_enabled: bool = Field(
            description="Whether autocast was enabled in the user call context."
        )
    autocast_dtype: Literal["float16", "bfloat16"] | None = Field(
            description="Autocast dtype at invocation; None when autocast was disabled."
        )
```

### ProcessStartupReceipt

[ProcessStartupReceipt source](../viper/src/viper/runtime.py) (line 411).

```python
class ProcessStartupReceipt(ProtocolModel):
    'Record the startup env, applied controls, and seeded generators.'
    env: dict[StartupVariable, str] = Field(
            description="Allowlisted process environment read before the user call."
        )
    observed_controls: RuntimeControlsReceipt = Field(
            description="PyTorch settings read inside the context used for the user call."
        )
    reproducibility: ReproducibilitySpec = Field(
            description="Requested run settings, retained alongside independent readings."
        )
    generators: tuple[GeneratorInitializationReceipt, ...] = Field(
            description="Seeds and initial-state identities recorded at initialization."
        )
```

### GCEHostContext

[GCEHostContext source](../viper/src/viper/runtime.py) (line 428).

```python
class GCEHostContext(ProtocolModel):
    'Record the Google Compute Engine host observed at execution.'
    provider: Literal["gce"] = "gce"
    project_id: NonEmptyStr
    provisioning: GCEProvisioningRef
    machine_type: NonEmptyStr
    zone: NonEmptyStr
    guest_os_name: NonEmptyStr
    guest_os_version: NonEmptyStr
    kernel_release: NonEmptyStr
```

### LocalHostContext

[LocalHostContext source](../viper/src/viper/runtime.py) (line 443).

```python
class LocalHostContext(ProtocolModel):
    'Record the operating system observed by a local development worker.'
    provider: Literal["local"] = "local"
    operating_system: NonEmptyStr
    release: NonEmptyStr
    architecture: NonEmptyStr
```

### CPUContext

[CPUContext source](../viper/src/viper/runtime.py) (line 458).

```python
class CPUContext(ProtocolModel):
    'Record the CPU available to the execution.'
    architecture: NonEmptyStr
    model: NonEmptyStr
    instruction_features: tuple[NonEmptyStr, ...] = Field(min_length=1)
```

### CPUBackendContext

[CPUBackendContext source](../viper/src/viper/runtime.py) (line 470).

```python
class CPUBackendContext(ProtocolModel):
    'Records that PyTorch executed without a GPU backend.'
    kind: Literal["cpu"] = "cpu"
    device: Literal["cpu"] = "cpu"
```

### CUDADeviceContext

[CUDADeviceContext source](../viper/src/viper/runtime.py) (line 477).

```python
class CUDADeviceContext(ProtocolModel):
    'Record one CUDA device observed at execution.'
    ordinal: int = Field(ge=0)
    model: NonEmptyStr
    compute_capability_major: int = Field(ge=0)
    compute_capability_minor: int = Field(ge=0)
    memory_bytes: int = Field(gt=0)
```

### CUDABackendContext

[CUDABackendContext source](../viper/src/viper/runtime.py) (line 489).

```python
class CUDABackendContext(ProtocolModel):
    'The CUDA backend and devices observed during execution.'
    kind: Literal["cuda"] = "cuda"
    gpu_devices: tuple[CUDADeviceContext, ...] = Field(min_length=1)
    nvidia_driver_version: NonEmptyStr
    pytorch_cuda_version: NonEmptyStr
    cudnn_version: NonEmptyStr
```

Validation: Require one record per CUDA device ordinal.

### NativeLibraryContext

[NativeLibraryContext source](../viper/src/viper/runtime.py) (line 515).

```python
class NativeLibraryContext(ProtocolModel):
    'Record one native numerical library implementation and version.'
    implementation: NonEmptyStr
    version: NonEmptyStr
```

### NativeThreadPoolContext

[NativeThreadPoolContext source](../viper/src/viper/runtime.py) (line 522).

```python
class NativeThreadPoolContext(NativeLibraryContext):
    'Record one native library and its active thread count.'
    threads: int = Field(ge=1)
```

### NumericalRuntimeContext

[NumericalRuntimeContext source](../viper/src/viper/runtime.py) (line 528).

```python
class NumericalRuntimeContext(ProtocolModel):
    'Record language, framework, and numerical-library versions.'
    python_version: NonEmptyStr
    pytorch_version: NonEmptyStr
    numpy_version: NonEmptyStr
    blas: NativeLibraryContext
    lapack: NativeLibraryContext
    native_thread_pools: tuple[NativeThreadPoolContext, ...]
```

### ExecutionContext

[ExecutionContext source](../viper/src/viper/runtime.py) (line 540).

```python
class ExecutionContext(ProtocolModel):
    'Facts observed from the host and running process.'
    host: HostContext
    cpu: CPUContext
    backend: ComputeBackendContext
    numerical_runtime: NumericalRuntimeContext
```

### RuntimeInitialization

[RuntimeInitialization source](../viper/src/viper/runtime.py) (line 560).

```python
class RuntimeInitialization():
    'Return the live named generators and the startup evidence for one child.'
    numpy_generators: dict[str, np.random.Generator]
    generators: tuple[GeneratorInitializationReceipt, ...]
```

## 16. Experiment, variant, replicate, and measurement records

[Protocol discussion](viper-protocol.md#16-experiment-variant-replicate-and-measurement-records).

### FactorSpec

[FactorSpec source](../viper/src/viper/experiments.py) (line 15).

```python
class FactorSpec(ProtocolModel):
    'Declare one experimental factor and its permitted levels.'
    factor_id: FactorId
    levels: tuple[LevelId, ...] = Field(min_length=2)
```

Validation: Require unique levels within the factor.

### ReplicateSpec

[ReplicateSpec source](../viper/src/viper/experiments.py) (line 29).

```python
class ReplicateSpec(ProtocolModel):
    'Identify one experimental replicate and its global seed.'
    replicate_id: ReplicateId
    seed: RNGSeed
```

### ExperimentSpec

[ExperimentSpec source](../viper/src/viper/experiments.py) (line 36).

```python
class ExperimentSpec(ProtocolModel):
    'Declare the factors, variants, replicates, and metrics in an experiment.'
    schema_version: Literal[2] = 2
    experiment_id: ExperimentId
    factors: tuple[FactorSpec, ...]
    variant_ids: tuple[VariantId, ...] = Field(min_length=1)
    replicates: tuple[ReplicateSpec, ...] = Field(min_length=1)
    metrics: tuple[MetricSpec, ...]
```

Validation: Require unique factor, variant, replicate, seed, and metric identities.

### BuildVariantStageConfig

[BuildVariantStageConfig source](../viper/src/viper/experiments.py) (line 72).

```python
class BuildVariantStageConfig(ProtocolModel):
    'Bind one build stage to its selected variant config.'
    kind: Literal["build"] = "build"
    stage_id: StageId
    config: BuildConfig
```

### EmbedVariantStageConfig

[EmbedVariantStageConfig source](../viper/src/viper/experiments.py) (line 80).

```python
class EmbedVariantStageConfig(ProtocolModel):
    'Bind one embedding stage to its selected variant config.'
    kind: Literal["embed"] = "embed"
    stage_id: StageId
    config: EmbedConfig
```

### DiagnosticVariantStageConfig

[DiagnosticVariantStageConfig source](../viper/src/viper/experiments.py) (line 88).

```python
class DiagnosticVariantStageConfig(ProtocolModel):
    'Bind one diagnostic stage to its selected variant config.'
    kind: Literal["diagnostic"] = "diagnostic"
    stage_id: StageId
    config: DiagnosticConfig
```

### TrainVariantStageConfig

[TrainVariantStageConfig source](../viper/src/viper/experiments.py) (line 96).

```python
class TrainVariantStageConfig(ProtocolModel):
    'Bind one training stage to its selected variant config.'
    kind: Literal["train"] = "train"
    stage_id: StageId
    config: TrainConfig
```

### EvalVariantStageConfig

[EvalVariantStageConfig source](../viper/src/viper/experiments.py) (line 104).

```python
class EvalVariantStageConfig(ProtocolModel):
    'Bind one eval stage to its selected variant config.'
    kind: Literal["eval"] = "eval"
    stage_id: StageId
    config: EvalConfig
```

### VariantSpec

[VariantSpec source](../viper/src/viper/experiments.py) (line 122).

```python
class VariantSpec(ProtocolModel):
    'Assign factor levels and typed stage config to one variant.'
    schema_version: Literal[2] = 2
    experiment_id: ExperimentId
    variant_id: VariantId
    levels: dict[FactorId, LevelId]
    stage_configs: tuple[VariantStageConfig, ...] = Field(min_length=1)
```

Validation: Require one variant-config record per stage.

### FloatComparator

[FloatComparator source](../viper/src/viper/metrics.py) (line 38).

```python
class FloatComparator(ProtocolModel):
    'Define equality for one recomputed floating-point metric.'
    mode: Literal["exact", "absolute", "relative"] = "exact"
    tolerance: float = Field(default=0.0, ge=0, allow_inf_nan=False)
```

Validation: Require a positive tolerance for approximate comparison modes.

### MetricImplementationRef

[MetricImplementationRef source](../viper/src/viper/metrics.py) (line 54).

```python
class MetricImplementationRef(ProtocolModel):
    'Identify one workspace-owned metric callable by exact file bytes.'
    path: PythonRepoRelPath
    symbol: PythonSymbol
    sha256: SHA256
    bytes: int = Field(gt=0)
```

### MetricDependency

[MetricDependency source](../viper/src/viper/metrics.py) (line 63).

```python
class MetricDependency(ProtocolModel):
    'Select one stage value and the data role accepted by a metric.'
    source: Literal["input", "artifact"]
    name: HumanId
    data_role: DataRole = Field(
            description="Data role that the selected input or artifact must have."
        )
```

### MetricSpec

[MetricSpec source](../viper/src/viper/metrics.py) (line 73).

```python
class MetricSpec(ProtocolModel):
    'Bind one metric identity to its implementation and frozen config.'
    schema_version: Literal[1] = 1
    metric_id: MetricId
    implementation: MetricImplementationRef
    config_type: ConfigTypeRef
    config: MetricConfig
    mode: MetricMode
    dependencies: tuple[MetricDependency, ...] = ()
    comparator: FloatComparator | None = None
```

Validation: Match the implementation mode with its runtime configuration.

### ResolvedMetricDependency

[ResolvedMetricDependency source](../viper/src/viper/metrics.py) (line 106).

```python
class ResolvedMetricDependency(ProtocolModel):
    'Bind one metric dependency to its exact persisted files.'
    dependency: MetricDependency
    files: tuple[ResolvedFileRef, ...] = Field(min_length=1)
```

### MetricExecutionReceipt

[MetricExecutionReceipt source](../viper/src/viper/metrics.py) (line 113).

```python
class MetricExecutionReceipt(ProtocolModel):
    'Record one controlled metric worker execution and its scalar result.'
    schema_version: Literal[1] = 1
    run_id: RunId
    attempt_id: int = Field(ge=1)
    metric_id: MetricId
    stage_id: StageId
    purpose: Literal["measurement", "verification"]
    implementation: MetricImplementationRef
    config_type: ConfigTypeRef
    config: MetricConfig
    dependencies: tuple[ResolvedMetricDependency, ...] = Field(min_length=1)
    startup: ProcessStartupReceipt
    execution_context: ExecutionContext
    python_env: PythonEnvSpec
    value: float = Field(allow_inf_nan=False)
    started_at: AwareDatetime
    completed_at: AwareDatetime
    outcome: Literal["succeeded"] = "succeeded"
```

### Measurement

[Measurement source](../viper/src/viper/metrics.py) (line 135).

```python
class Measurement(ProtocolModel):
    'One observed metric value produced during a run stage.'
    run_id: RunId
    attempt_id: int = Field(ge=1)
    stage_id: StageId
    metric_id: MetricId
    value: float = Field(allow_inf_nan=False)
    measured_at: AwareDatetime
    epoch: int | None = Field(default=None, ge=0)
    step: int | None = Field(default=None, ge=0)
```

### MetricVerificationReceipt

[MetricVerificationReceipt source](../viper/src/viper/metrics.py) (line 150).

```python
class MetricVerificationReceipt(ProtocolModel):
    'Bind one measurement to independent recomputation evidence.'
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

Validation: Require both workers to select one frozen metric invocation.

### MetricContext

[MetricContext source](../viper/src/viper/metrics.py) (line 215).

```python
class MetricContext(Generic[MetricConfigT]):
    'Supply verified paths and frozen config to one metric invocation.'
    config: MetricConfigT
    inputs: Mapping[str, Path] = field(default_factory=dict)
    artifacts: Mapping[str, Path] = field(default_factory=dict)
```

### MetricObjectiveSpec

[MetricObjectiveSpec source](../viper/src/viper/metrics.py) (line 536).

```python
class MetricObjectiveSpec(ProtocolModel):
    'Persist one objective metric and its direction of improvement.'
    metric_id: MetricId
    direction: ObjectiveDirection
```

## 17. Concrete stage records

[Protocol discussion](viper-protocol.md#17-concrete-stage-records).

### StageContext

[StageContext source](../viper/src/viper/stages.py) (line 76).

```python
class StageContext(Generic[ConfigT]):
    'Give a running stage access to its declared inputs and outputs.'
    run_id: RunId
    attempt_id: int
    stage_id: StageId
    config: ConfigT
    inputs: Mapping[InputName, Path]
    outputs: Mapping[OutputName, Path]
    metrics: Mapping[MetricId, MetricHandle]
    numpy_generators: Mapping[HumanId, np.random.Generator]
```

### StageImplementationRef

[StageImplementationRef source](../viper/src/viper/stages.py) (line 93).

```python
class StageImplementationRef(ProtocolModel):
    'Identify one workspace-owned top-level stage callable by exact file bytes.'
    path: PythonRepoRelPath
    symbol: PythonSymbol
    sha256: SHA256
    bytes: int = Field(gt=0)
```

### StageContextBinding

[StageContextBinding source](../viper/src/viper/stages.py) (line 102).

```python
class StageContextBinding(ProtocolModel):
    'Persist the stable values used to construct one live stage context.'
    schema_version: Literal[2] = 2
    run_id: RunId
    attempt_id: int = Field(ge=1)
    stage_id: StageId
    config_type: ConfigTypeRef
    config_digest: SHA256
    inputs: dict[InputName, RepoRelPath]
    outputs: dict[OutputName, RepoRelPath]
    metric_ids: tuple[MetricId, ...]
    numpy_generator_names: tuple[HumanId, ...]
```

### StageInvocationReceipt

[StageInvocationReceipt source](../viper/src/viper/stages.py) (line 117).

```python
class StageInvocationReceipt(ProtocolModel):
    'Record the callable, logical context, timing, and outcome of one invocation.'
    implementation: StageImplementationRef
    context: StageContextBinding
    context_digest: SHA256
    started_at: AwareDatetime
    completed_at: AwareDatetime
    outcome: Literal["succeeded", "failed", "cancelled", "preempted"]
```

Validation: Require completion to follow invocation start.

### BaseSpec

[BaseSpec source](../viper/src/viper/stages.py) (line 135).

```python
class BaseSpec(ProtocolModel):
    'Execution request recorded before a stage runs.'
    kind: str
    schema_version: Literal[2] = 2
    env: EnvSpec | None = None
    metric_ids: tuple[MetricId, ...] = ()
    outputs: StageOutputs[OutputSpec]
```

Validation: Require each output path to belong to its named stage and output.

### ParameterizedSpec

[ParameterizedSpec source](../viper/src/viper/stages.py) (line 179).

```python
class ParameterizedSpec(BaseSpec):
    'Request an operation governed by one workspace-defined config type.'
    implementation: StageImplementationRef
    config_type: ConfigTypeRef
    reuse: StageReuseMode = "never"
```

Validation: Keep the workspace callable outside every declared artifact root.

### DownloadSpec

[DownloadSpec source](../viper/src/viper/stages.py) (line 197).

```python
class DownloadSpec(BaseSpec):
    'Request HTTP retrievals into same-named single-file outputs.'
    kind: Literal["download"] = "download"
    inputs: dict[InputName, HttpRequestSpec] = Field(min_length=1)
    http: HttpImplementationSpec = Field(default_factory=BuiltinHttpImplementationSpec)
    policy: HttpRetrievalPolicy
```

Validation: Require one same-named file output for every HTTP request.

### InternalSpec

[InternalSpec source](../viper/src/viper/stages.py) (line 215).

```python
class InternalSpec(ParameterizedSpec):
    'Request a stage that consumes stored or prior-stage artifacts.'
    inputs: dict[InputName, InputRef] = Field(min_length=1)
```

Validation: Keep stored inputs, scripts, and artifact paths disjoint.

### BuildSpec

[BuildSpec source](../viper/src/viper/stages.py) (line 253).

```python
class BuildSpec(InternalSpec):
    'Request a workspace function that prepares data or other input artifacts.'
    kind: Literal["build"] = "build"
    config: BuildConfig
```

### EmbedSpec

[EmbedSpec source](../viper/src/viper/stages.py) (line 260).

```python
class EmbedSpec(InternalSpec):
    'Request construction of a workspace-defined embedding artifact.'
    kind: Literal["embed"] = "embed"
    objective: MetricObjectiveSpec | None = None
    config: EmbedConfig
```

Validation: Require a selected embedding objective to occur in metric_ids.

### DiagnosticSpec

[DiagnosticSpec source](../viper/src/viper/stages.py) (line 278).

```python
class DiagnosticSpec(InternalSpec):
    'Request a diagnostic stage whose outputs cannot feed downstream stages.'
    kind: Literal["diagnostic"] = "diagnostic"
    config: DiagnosticConfig
```

### TrainSpec

[TrainSpec source](../viper/src/viper/stages.py) (line 285).

```python
class TrainSpec(InternalSpec):
    'Request training with a measured minimization or maximization objective.'
    kind: Literal["train"] = "train"
    metric_ids: tuple[MetricId, ...] = Field(min_length=1)
    objective: MetricObjectiveSpec
    config: TrainConfig
```

Validation: Require a declared objective and matching model and resume-state outputs.

### EvalSpec

[EvalSpec source](../viper/src/viper/stages.py) (line 331).

```python
class EvalSpec(InternalSpec):
    'Request prediction and recomputed metrics for one fixed eval.'
    kind: Literal["eval"] = "eval"
    eval_id: EvalId
    metric_ids: tuple[MetricId, ...] = Field(min_length=1)
    objective: MetricObjectiveSpec
    split_inputs: tuple[InputName, ...] = Field(min_length=1)
    config: EvalConfig
```

Validation: Require the objective, fixed inputs, splits, and prediction artifact.

### ResolvedBaseSpec

[ResolvedBaseSpec source](../viper/src/viper/stages.py) (line 404).

```python
class ResolvedBaseSpec(ProtocolModel):
    'Record an execution and the exact output files it produced.'
    schema_version: Literal[2] = 2
    kind: str
    spec: BaseSpec
    artifacts: dict[ArtifactName, ResolvedArtifact] = Field(min_length=1)
    completed_at: AwareDatetime
```

Validation: Match realized source, artifacts, env, and context to the request.

### ResolvedExecutedSpec

[ResolvedExecutedSpec source](../viper/src/viper/stages.py) (line 450).

```python
class ResolvedExecutedSpec(ResolvedBaseSpec):
    'Record environment evidence created by a runner-owned execution.'
    env: ResolvedEnv
    execution_context: ExecutionContext
```

Validation: Match the resolved environment to its request and observed host.

### ResolvedDownloadSpec

[ResolvedDownloadSpec source](../viper/src/viper/stages.py) (line 531).

```python
class ResolvedDownloadSpec(ResolvedExecutedSpec):
    'Bind every frozen HTTP input to its completed retrieval evidence.'
    kind: Literal["download"] = "download"
    spec: DownloadSpec
    retrievals: dict[InputName, ResolvedHttpRetrieval]
```

Validation: Match each retrieval to its request, HTTP implementation, and timing.

### ResolvedParameterizedSpec

[ResolvedParameterizedSpec source](../viper/src/viper/stages.py) (line 565).

```python
class ResolvedParameterizedSpec(ResolvedBaseSpec):
    'Record an executed or verified-reused workspace stage.'
    spec: ParameterizedSpec
    completion: StageCompletion
```

Validation: Read existing stage documents into the explicit completion union; Match the resolved source to the selected workspace callable.

### ResolvedInternalSpec

[ResolvedInternalSpec source](../viper/src/viper/stages.py) (line 606).

```python
class ResolvedInternalSpec(ResolvedParameterizedSpec):
    'Record an operation that consumes previously produced artifacts.'
    spec: InternalSpec
    inputs: dict[InputName, ResolvedInputRef]
```

Validation: Match each realized internal input to the frozen request.

### ResolvedBuildSpec

[ResolvedBuildSpec source](../viper/src/viper/stages.py) (line 644).

```python
class ResolvedBuildSpec(ResolvedInternalSpec):
    'Record the realized execution of one build stage.'
    kind: Literal["build"] = "build"
    spec: BuildSpec
```

### ResolvedEmbedSpec

[ResolvedEmbedSpec source](../viper/src/viper/stages.py) (line 651).

```python
class ResolvedEmbedSpec(ResolvedInternalSpec):
    'Record the realized execution of one embedding stage.'
    kind: Literal["embed"] = "embed"
    spec: EmbedSpec
```

### ResolvedDiagnosticSpec

[ResolvedDiagnosticSpec source](../viper/src/viper/stages.py) (line 658).

```python
class ResolvedDiagnosticSpec(ResolvedInternalSpec):
    'Record the realized execution of one diagnostic stage.'
    kind: Literal["diagnostic"] = "diagnostic"
    spec: DiagnosticSpec
```

### ResolvedTrainSpec

[ResolvedTrainSpec source](../viper/src/viper/stages.py) (line 665).

```python
class ResolvedTrainSpec(ResolvedInternalSpec):
    'Record the realized execution of one training stage.'
    kind: Literal["train"] = "train"
    spec: TrainSpec
```

### ResolvedEvalSpec

[ResolvedEvalSpec source](../viper/src/viper/stages.py) (line 672).

```python
class ResolvedEvalSpec(ResolvedInternalSpec):
    'Record the realized execution of one eval stage.'
    kind: Literal["eval"] = "eval"
    spec: EvalSpec
```

### StageDefinition

[StageDefinition source](../viper/src/viper/stages.py) (line 694).

```python
class StageDefinition(Generic[ConfigT]):
    'Store the stage kind and config class attached by one decorator.'
    kind: str
    config_type: type[ConfigT]
```

### StageDefinitionError

[StageDefinitionError source](../viper/src/viper/stages.py) (line 701).

```python
class StageDefinitionError(RuntimeError):
    'Report an invalid decorated stage or frozen implementation identity.'
```

### HttpOrigin

[HttpOrigin source](../viper/src/viper/http.py) (line 54).

```python
class HttpOrigin(ProtocolModel):
    'Identify one normalized HTTP origin including its effective port.'
    scheme: Literal["http", "https"]
    host: NonEmptyStr
    port: int = Field(ge=1, le=65535)
```

Validation: Require the lower-case host representation used for exact matching.

### EnvSecretRef

[EnvSecretRef source](../viper/src/viper/http.py) (line 70).

```python
class EnvSecretRef(ProtocolModel):
    'Select one runtime secret and the HTTP origins authorized to receive it.'
    kind: Literal["env"] = "env"
    variable: NonEmptyStr
    header: HttpHeaderName
    prefix: str = ""
    authorized_origins: frozenset[HttpOrigin] = Field(min_length=1)
```

Validation: Require a portable env-variable name.

### HttpRequestSpec

[HttpRequestSpec source](../viper/src/viper/http.py) (line 88).

```python
class HttpRequestSpec(ProtocolModel):
    'Freeze one experimental HTTP request and its expected response body.'
    kind: Literal["http"] = "http"
    method: Literal["GET"] = "GET"
    url: HttpUrl
    headers: dict[HttpHeaderName, NonEmptyStr] = Field(default_factory=dict)
    version: NonEmptyStr
    expected_body_sha256: SHA256
    expected_body_bytes: int = Field(gt=0)
    credentials: EnvSecretRef | None = None
```

Validation: Keep literal credentials out and authorize the initial request origin.

### HttpRetrievalPolicy

[HttpRetrievalPolicy source](../viper/src/viper/http.py) (line 120).

```python
class HttpRetrievalPolicy(ProtocolModel):
    'Bound the network and response behavior of one logical retrieval.'
    allowed_schemes: frozenset[Literal["http", "https"]] = Field(min_length=1)
    allowed_hosts: frozenset[NonEmptyStr] = Field(min_length=1)
    allowed_ports: frozenset[Annotated[int, Field(ge=1, le=65535)]] = Field(
            min_length=1
        )
    accepted_statuses: frozenset[Annotated[int, Field(ge=100, le=599)]] = frozenset(
            {200}
        )
    max_redirects: int = Field(ge=0)
    max_body_bytes: int = Field(gt=0)
    timeout_seconds: float = Field(gt=0, allow_inf_nan=False)
```

Validation: Require exact lower-case host policy members.

### HttpImplementationRef

[HttpImplementationRef source](../viper/src/viper/http.py) (line 157).

```python
class HttpImplementationRef(ProtocolModel):
    'Identify one workspace-owned HTTP callable by exact file bytes.'
    path: PythonRepoRelPath
    symbol: PythonSymbol
    sha256: SHA256
    bytes: int = Field(gt=0)
```

### ExternalExecutableSpec

[ExternalExecutableSpec source](../viper/src/viper/http.py) (line 166).

```python
class ExternalExecutableSpec(ProtocolModel):
    'Freeze the exact executable selected by one workspace HTTP implementation.'
    executable_id: HumanId
    command: NonEmptyStr
    sha256: SHA256
    bytes: int = Field(gt=0)
```

### BuiltinHttpImplementationSpec

[BuiltinHttpImplementationSpec source](../viper/src/viper/http.py) (line 175).

```python
class BuiltinHttpImplementationSpec(ProtocolModel):
    'Select the built-in HTTPX implementation.'
    kind: Literal["builtin"] = "builtin"
    id: Literal["httpx"] = "httpx"
```

### WorkspaceHttpImplementationSpec

[WorkspaceHttpImplementationSpec source](../viper/src/viper/http.py) (line 182).

```python
class WorkspaceHttpImplementationSpec(ProtocolModel):
    'Select one frozen workspace-owned HTTP implementation.'
    kind: Literal["workspace"] = "workspace"
    id: HumanId
    implementation: HttpImplementationRef
    config_type: ConfigTypeRef
    config: HttpConfig
    executables: tuple[ExternalExecutableSpec, ...] = ()
```

Validation: Require one external executable requirement per identifier.

### ObservedHttpResponse

[ObservedHttpResponse source](../viper/src/viper/http.py) (line 207).

```python
class ObservedHttpResponse(ProtocolModel):
    'Persist the terminal status, URL, and representation response fields.'
    response_url: HttpUrl
    status: int = Field(ge=100, le=599)
    response_headers: dict[HttpHeaderName, str]
```

Validation: Restrict persisted headers to representation and content identity.

### ResolvedExternalExecutable

[ResolvedExternalExecutable source](../viper/src/viper/http.py) (line 231).

```python
class ResolvedExternalExecutable(ProtocolModel):
    'Bind one frozen executable requirement to its verified host path.'
    spec: ExternalExecutableSpec
    path: Path
```

### ResolvedHttpImplementation

[ResolvedHttpImplementation source](../viper/src/viper/http.py) (line 238).

```python
class ResolvedHttpImplementation(ProtocolModel):
    'Record the HTTP and executable identities used for retrieval.'
    spec: HttpImplementationSpec
    external_executables: tuple[ResolvedExternalExecutable, ...] = ()
```

Validation: Resolve every workspace executable exactly once and none for HTTPX.

### ResolvedHttpRetrieval

[ResolvedHttpRetrieval source](../viper/src/viper/http.py) (line 260).

```python
class ResolvedHttpRetrieval(ProtocolModel):
    'Bind one request to its HTTP implementation, response, and snapshot body.'
    input_name: InputName
    request: HttpRequestSpec
    http: ResolvedHttpImplementation
    response: ObservedHttpResponse
    body: SnapshotFileRef
    started_at: AwareDatetime
    completed_at: AwareDatetime
```

Validation: Require positive duration and the frozen expected body identity.

### HttpRetrievalError

[HttpRetrievalError source](../viper/src/viper/http.py) (line 300).

```python
class HttpRetrievalError(RuntimeError):
    'Report one rejected request, HTTP implementation, response, or body.'
```

### RuntimeHttpCredential

[RuntimeHttpCredential source](../viper/src/viper/http.py) (line 305).

```python
class RuntimeHttpCredential():
    'Carry one resolved secret only for the active HTTP invocation.'
    header: HttpHeaderName
    prefix: str
    value: str
```

### HttpContext

[HttpContext source](../viper/src/viper/http.py) (line 314).

```python
class HttpContext(Generic[HttpConfigT]):
    'Supply one HTTP implementation with its request and destination.'
    request: HttpRequestSpec
    credential: RuntimeHttpCredential | None
    workspace: Path
    destination: Path
    policy: HttpRetrievalPolicy
    config: HttpConfigT
    executables: Mapping[HumanId, Path]
```

### HttpResult

[HttpResult source](../viper/src/viper/http.py) (line 327).

```python
class HttpResult():
    'Return one completed response body and its terminal HTTP response.'
    body: Path
    response: ObservedHttpResponse
```

### CustomHttpDraft

[CustomHttpDraft source](../viper/src/viper/http.py) (line 334).

```python
class CustomHttpDraft(BaseModel, Generic[HttpConfigT]):
    'Hold one configured workspace HTTP callable before freezing.'
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)
    implementation: Callable[[HttpContext[HttpConfigT]], HttpResult]
    config: HttpConfigT
    executables: tuple[ExternalExecutableSpec, ...] = ()
```

### HttpDefinition

[HttpDefinition source](../viper/src/viper/http.py) (line 348).

```python
class HttpDefinition(Generic[HttpConfigT]):
    'Store authoring metadata attached to one workspace HTTP callable.'
    id: HumanId
    config_type: type[HttpConfigT]
    executables: tuple[ExternalExecutableSpec, ...]
```

### HttpCallable

[HttpCallable source](../viper/src/viper/http.py) (line 356).

```python
class HttpCallable(Protocol[HttpConfigT]):
    'Describe the callable interface shared by workspace HTTP implementations.'
```

### ReuseFileIdentity

[ReuseFileIdentity source](../viper/src/viper/reuse.py) (line 118).

```python
class ReuseFileIdentity(ProtocolModel):
    'Identify one input file independently of its run-specific path.'
    relative_path: RepoRelPath
    sha256: SHA256
    bytes: int = Field(ge=0)
```

### ReuseInputIdentity

[ReuseInputIdentity source](../viper/src/viper/reuse.py) (line 126).

```python
class ReuseInputIdentity(ProtocolModel):
    'Identify every file selected for one named stage input.'
    input_name: InputName
    data_role: DataRole
    files: tuple[ReuseFileIdentity, ...] = Field(min_length=1)
```

### StageReuseKey

[StageReuseKey source](../viper/src/viper/reuse.py) (line 134).

```python
class StageReuseKey(ProtocolModel):
    'Describe every recorded value allowed to affect a reusable stage.'
    schema_version: Literal[1] = 1
    stage_id: StageId
    stage_sha256: SHA256
    inputs: tuple[ReuseInputIdentity, ...]
    seed: RNGSeed
    env_sha256: SHA256
    reproducibility_sha256: SHA256
    metric_sha256s: tuple[SHA256, ...]
```

### ReusedStageFile

[ReusedStageFile source](../viper/src/viper/reuse.py) (line 147).

```python
class ReusedStageFile(ProtocolModel):
    'Map one verified source file to its target snapshot path.'
    artifact_name: ArtifactName
    source: SnapshotFileRef
    target: SnapshotFileRef
```

Validation: Keep source and target byte identities equal.

### ReusedMetricEvidence

[ReusedMetricEvidence source](../viper/src/viper/reuse.py) (line 164).

```python
class ReusedMetricEvidence(ProtocolModel):
    'Link one reused metric to its original measurement evidence.'
    metric_id: MetricId
    measurement: ResolvedFileRef
    verification: ResolvedFileRef | None = None
```

### StageReuseReceipt

[StageReuseReceipt source](../viper/src/viper/reuse.py) (line 172).

```python
class StageReuseReceipt(ProtocolModel):
    'Record the verified source and remapping for one reused stage.'
    schema_version: Literal[1] = 1
    stage_id: StageId
    key: StageReuseKey
    source_run: ResolvedRunRef
    source_attempt: ResolvedAttemptRef
    source_stage: ResolvedStageRef
    files: tuple[ReusedStageFile, ...] = Field(min_length=1)
    metrics: tuple[ReusedMetricEvidence, ...]
    completed_at: AwareDatetime
```

### ResolvedStageReuseRef

[ResolvedStageReuseRef source](../viper/src/viper/reuse.py) (line 186).

```python
class ResolvedStageReuseRef(ResolvedFileRef):
    'Identify one immutable stage-reuse receipt.'
    kind: Literal["stage_reuse"] = "stage_reuse"
```

### ExecutedStageCompletion

[ExecutedStageCompletion source](../viper/src/viper/reuse.py) (line 192).

```python
class ExecutedStageCompletion(ProtocolModel):
    'Record evidence created by an actual workspace stage process.'
    kind: Literal["executed"] = "executed"
    source: ResolvedGitFileRef
    env: ResolvedEnv
    execution_context: ExecutionContext
    startup: ProcessStartupReceipt
    invocation: ResolvedStageInvocationRef
    command: tuple[str, ...] = Field(min_length=1)
```

### ReusedStageCompletion

[ReusedStageCompletion source](../viper/src/viper/reuse.py) (line 204).

```python
class ReusedStageCompletion(ProtocolModel):
    'Record that a workspace stage selected verified prior output.'
    kind: Literal["reused"] = "reused"
    receipt: ResolvedStageReuseRef
```

## 18. Training checkpoint mapping

[Protocol discussion](viper-protocol.md#18-training-checkpoint-mapping).

See [DataLoaderConfiguration](#dataloaderconfiguration).

See [DataLoaderResumeState](#dataloaderresumestate).

See [ResumeState](#resumestate).

## 20. Benchmark specification and confirmation

[Protocol discussion](viper-protocol.md#20-benchmark-specification-and-confirmation).

### MetricCriterion

[MetricCriterion source](../viper/src/viper/benchmark.py) (line 23).

```python
class MetricCriterion(ProtocolModel):
    'Define one threshold that a benchmark metric must satisfy.'
    metric_id: MetricId
    comparison: Literal["ge", "le"]
    threshold: float = Field(allow_inf_nan=False)
```

### RunArtifactDraft

[RunArtifactDraft source](../viper/src/viper/benchmark.py) (line 31).

```python
class RunArtifactDraft(BaseModel):
    'Select one artifact from a completed run.'
    model_config = ConfigDict(extra="forbid", frozen=True)
    run: ResolvedRunRef
    artifact: StageArtifactRef
    path: RepoRelPath
    data_role: DataRole
```

### BenchmarkDraft

[BenchmarkDraft source](../viper/src/viper/benchmark.py) (line 42).

```python
class BenchmarkDraft(BaseModel):
    'Fix the inputs and metrics used by one benchmark.'
    model_config = ConfigDict(
            arbitrary_types_allowed=True,
            extra="forbid",
            frozen=True,
        )
    benchmark_id: BenchmarkId
    eval_id: EvalId
    test: RunArtifactDraft
    splits: dict[InputName, RunArtifactDraft] = Field(min_length=1)
    metrics: tuple[MetricDraft[Any], ...] = Field(min_length=1)
    criteria: tuple[MetricCriterionDraft, ...] = ()
    execution_count: Literal[2] = 2
```

Validation: Require unique metrics and criteria selected from those metrics.

### BenchmarkSpec

[BenchmarkSpec source](../viper/src/viper/benchmark.py) (line 79).

```python
class BenchmarkSpec(ProtocolModel):
    'Define the fixed inputs and metrics for one benchmark.'
    schema_version: Literal[1] = 1
    benchmark_id: BenchmarkId
    eval_id: EvalId
    test: ResolvedArtifactPointerRef
    splits: dict[InputName, ResolvedArtifactPointerRef] = Field(min_length=1)
    metric_ids: tuple[MetricId, ...] = Field(min_length=1)
    criteria: tuple[MetricCriterion, ...] = ()
    execution_count: Literal[2] = 2
```

Validation: Require unique metrics and optional criteria for selected metrics.

### ArtifactComparisonReceipt

[ArtifactComparisonReceipt source](../viper/src/viper/benchmark.py) (line 105).

```python
class ArtifactComparisonReceipt(ProtocolModel):
    'Record one candidate-to-confirmation artifact comparison.'
    artifact: StageArtifactRef
    candidate_stage: ResolvedStageRef
    confirmation_stage: ResolvedStageRef
    candidate_digest: SHA256
    confirmation_digest: SHA256
    passed: bool
```

Validation: Derive the comparison outcome from the two canonical digests.

### MetricCriterionResult

[MetricCriterionResult source](../viper/src/viper/benchmark.py) (line 123).

```python
class MetricCriterionResult(ProtocolModel):
    'Record one threshold result for both benchmark executions.'
    criterion: MetricCriterion
    candidate_passed: bool
    confirmation_passed: bool
    passed: bool
```

Validation: Require the combined result to equal both execution results.

### BenchmarkMetricResult

[BenchmarkMetricResult source](../viper/src/viper/benchmark.py) (line 139).

```python
class BenchmarkMetricResult(ProtocolModel):
    'Record one metric across candidate and confirmation executions.'
    metric_id: MetricId
    candidate_verification: ResolvedFileRef
    confirmation_verification: ResolvedFileRef
    candidate_value: float = Field(allow_inf_nan=False)
    confirmation_value: float = Field(allow_inf_nan=False)
    matched: bool
    criterion: MetricCriterionResult | None = None
```

### BenchmarkResult

[BenchmarkResult source](../viper/src/viper/benchmark.py) (line 151).

```python
class BenchmarkResult(ProtocolModel):
    'Record the independent confirmation and outcome of a benchmark.'
    schema_version: Literal[1] = 1
    benchmark: ResolvedBenchmarkSpecRef
    run: ResolvedRunRef
    confirmation: ResolvedAttemptRef
    artifacts: tuple[ArtifactComparisonReceipt, ...] = Field(min_length=2)
    metrics: tuple[BenchmarkMetricResult, ...] = Field(min_length=1)
    status: Literal["verified", "passed", "failed"]
    completed_at: AwareDatetime
```

Validation: Require unique artifact selectors and metric results.

## 22. Execution and publication sequence

[Protocol discussion](viper-protocol.md#22-execution-and-publication-sequence).

### RunResult

[RunResult source](../viper/src/viper/execution/results.py) (line 14).

```python
class RunResult(BaseModel):
    'Return one verified terminal run and its local output path.'
    model_config = ConfigDict(extra="forbid", frozen=True)
    record: ResolvedRun = Field(
            description="Verified terminal record saved by the run."
        )
    reference: ResolvedRunRef = Field(
            description="Immutable reference to the saved terminal record."
        )
    path: Path = Field(description="Local path of the terminal record.")
    journal_path: Path = Field(description="Local journal for the completed attempt.")
```

### ConfirmationRunResult

[ConfirmationRunResult source](../viper/src/viper/execution/results.py) (line 34).

```python
class ConfirmationRunResult(BaseModel):
    'Return one independently executed benchmark-confirmation attempt.'
    model_config = ConfigDict(extra="forbid", frozen=True)
    attempt: RunAttempt = Field(description="Completed benchmark confirmation attempt.")
    attempt_reference: ResolvedAttemptRef = Field(
            description="Immutable reference to the confirmation attempt."
        )
    attempt_path: Path = Field(description="Local path of the confirmation attempt.")
    journal_path: Path = Field(description="Journal of confirmation state changes.")
```

### BenchmarkExecutionResult

[BenchmarkExecutionResult source](../viper/src/viper/execution/results.py) (line 47).

```python
class BenchmarkExecutionResult(BaseModel):
    'Return one verified benchmark result and its canonical local path.'
    model_config = ConfigDict(extra="forbid", frozen=True)
    record: BenchmarkResult = Field(description="Verified benchmark comparison record.")
    reference: ResolvedBenchmarkResultRef = Field(
            description="Immutable reference to the benchmark record."
        )
    path: Path = Field(description="Local path of the benchmark record.")
```

### ExperimentRunFailure

[ExperimentRunFailure source](../viper/src/viper/execution/results.py) (line 73).

```python
class ExperimentRunFailure(BaseModel):
    'Describe why one run in a batch failed.'
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: ExperimentRunFailureCode = Field(description="Category of the run failure.")
    message: str = Field(min_length=1, description="Explanation of the run failure.")
```

### ExperimentRunResult

[ExperimentRunResult source](../viper/src/viper/execution/results.py) (line 82).

```python
class ExperimentRunResult(BaseModel):
    'Retain one batch entry in its original input position.'
    model_config = ConfigDict(extra="forbid", frozen=True)
    variant_id: VariantId = Field(description="Variant selected by this batch entry.")
    replicate_id: ReplicateId = Field(description="Replicate selected by this entry.")
    run_id: RunId = Field(description="Identity assigned to the selected run.")
    run_spec_path: Path = Field(description="Frozen plan supplied for this entry.")
    status: ExperimentRunStatus = Field(description="Execution outcome of this entry.")
    result: RunResult | None = Field(
            default=None, description="Verified run returned when execution succeeded."
        )
    failure: ExperimentRunFailure | None = Field(
            default=None, description="Failure details when execution failed."
        )
    skip_reason: str | None = Field(
            default=None, min_length=1, description="Reason this entry was left unexecuted."
        )
```

Validation: Require exactly the fields selected by the result status.

### ExperimentExecutionResult

[ExperimentExecutionResult source](../viper/src/viper/execution/results.py) (line 127).

```python
class ExperimentExecutionResult(BaseModel):
    'Return every batch result in input order.'
    model_config = ConfigDict(extra="forbid", frozen=True)
    runs: tuple[ExperimentRunResult, ...] = Field(
            min_length=1, description="Per-run outcomes in the original input order."
        )
```
