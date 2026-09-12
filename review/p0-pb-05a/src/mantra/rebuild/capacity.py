"""Storage calculation for bounded MANTRA restoration."""

from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

GIB = 1024**3
DEFAULT_RESERVED_BYTES = 20 * GIB


@dataclass(frozen=True, slots=True)
class CapacityPlan:
    """Maximum simultaneous bytes retained during restoration."""

    compressed_cache_bytes: int
    canonical_bytes: int
    viper_bytes: int
    temporary_bytes: int
    reserved_bytes: int = DEFAULT_RESERVED_BYTES

    def __post_init__(self) -> None:
        """Reject non-integer or negative storage terms."""

        for field, value in asdict(self).items():
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{field} must be an integer")
            if value < 0:
                raise ValueError(f"{field} cannot be negative")

    @property
    def required_bytes(self) -> int:
        """Return the maximum simultaneous storage requirement."""

        return (
            self.compressed_cache_bytes
            + self.canonical_bytes
            + self.viper_bytes
            + self.temporary_bytes
            + self.reserved_bytes
        )


@dataclass(frozen=True, slots=True)
class CapacityReceipt:
    """Observed free space and the resulting capacity decision."""

    filesystem_path: str
    free_bytes: int
    plan: CapacityPlan

    @property
    def passed(self) -> bool:
        """Return whether observed free space satisfies the plan."""

        return self.free_bytes >= self.plan.required_bytes

    def to_dict(self) -> dict[str, object]:
        """Serialize every capacity input, total, and decision."""

        return {
            "filesystem_path": self.filesystem_path,
            "free_bytes": self.free_bytes,
            "compressed_cache_bytes": self.plan.compressed_cache_bytes,
            "canonical_bytes": self.plan.canonical_bytes,
            "viper_bytes": self.plan.viper_bytes,
            "temporary_bytes": self.plan.temporary_bytes,
            "reserved_bytes": self.plan.reserved_bytes,
            "required_bytes": self.plan.required_bytes,
            "passed": self.passed,
        }


def measure_capacity(
    filesystem_path: Path,
    plan: CapacityPlan,
) -> CapacityReceipt:
    """Measure free space on the filesystem that will hold the restoration."""

    path = Path(filesystem_path).resolve()
    if not path.exists():
        raise FileNotFoundError(path)
    return CapacityReceipt(
        filesystem_path=str(path),
        free_bytes=shutil.disk_usage(path).free,
        plan=plan,
    )
