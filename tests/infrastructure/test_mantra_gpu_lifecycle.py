"""Verify the governed Spot worker lifecycle without creating cloud resources."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
LAUNCHER = ROOT / "mantra-deploy-spot.sh"


def _write_json(path: Path, value: dict[str, object]) -> None:
    """Write one deterministic JSON fixture."""
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def _probe(path: Path, *, passed: bool = True) -> None:
    """Write one artifact publication or restoration probe."""
    digest = "a" * 64
    _write_json(
        path,
        {
            "passed": passed,
            "artifact_uri": "viper://fixture/probe",
            "sha256": digest,
            "restored_sha256": digest,
        },
    )


def _fake_gcloud(path: Path) -> None:
    """Install a stateful gcloud substitute that models one regional fallback."""
    path.write_text(
        """#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

args = sys.argv[1:]
state_path = Path(os.environ["FAKE_GCLOUD_STATE"])
log_path = Path(os.environ["FAKE_GCLOUD_LOG"])
state = json.loads(state_path.read_text())
with log_path.open("a", encoding="utf-8") as stream:
    stream.write(json.dumps(args) + "\\n")

def option(prefix):
    return next((item.split("=", 1)[1] for item in args if item.startswith(prefix + "=")), "")

def save():
    state_path.write_text(json.dumps(state, sort_keys=True) + "\\n")

if args[:3] == ["compute", "firewall-rules", "describe"]:
    fmt = option("--format")
    values = {
        "value(network.basename())": "default",
        "value(direction)": "INGRESS",
        "value(disabled)": "False",
        "value(sourceRanges.list())": "35.235.240.0/20",
        "value(targetTags.list())": "allow-ssh-iap",
        "value(allowed)": "{'IPProtocol': 'tcp', 'ports': ['22']}",
    }
    print(values[fmt])
elif args[:3] == ["compute", "machine-types", "describe"]:
    print("nvidia-l4,1")
elif args[:3] == ["compute", "machine-images", "describe"]:
    print("READY" if option("--format") == "value(status)" else "12345")
elif args[:3] == ["compute", "images", "describe"]:
    print("READY" if option("--format") == "value(status)" else "12345")
elif args[:3] == ["compute", "instances", "list"]:
    if state["instance"]:
        print(f"mantra-g2-test,{state['zone']},RUNNING")
elif args[:3] == ["compute", "instances", "create"]:
    zone = option("--zone")
    if zone == "us-west4-a" and not state["quota_rejected"]:
        state["quota_rejected"] = True
        save()
        print("QUOTA_EXCEEDED: regional NVIDIA_L4_GPUS quota exceeded", file=sys.stderr)
        raise SystemExit(1)
    state.update(instance=True, disk=True, zone=zone)
    save()
elif args[:3] == ["compute", "instances", "describe"]:
    if not state["instance"]:
        raise SystemExit(1)
    fmt = option("--format")
    if fmt == "value(id)" and os.environ.get("FAKE_FAIL_INSTANCE_ID") == "true":
        raise SystemExit(1)
    values = {
        "value(disks[0].source.basename())": "mantra-g2-test-disk",
        "value(disks[0].autoDelete)": "True",
        "value(id)": "987654321",
    }
    print(values.get(fmt, "RUNNING"))
elif args[:3] == ["compute", "instances", "set-disk-auto-delete"]:
    pass
elif args[:3] == ["compute", "instances", "delete"]:
    state.update(instance=False, disk=False)
    save()
elif args[:3] == ["compute", "disks", "describe"]:
    raise SystemExit(0 if state["disk"] else 1)
elif args[:3] == ["compute", "disks", "delete"]:
    state["disk"] = False
    save()
elif args[:3] == ["compute", "zones", "describe"]:
    print("us-west4")
elif args[:3] == ["compute", "routers", "describe"]:
    if not state["router"]:
        print("not found", file=sys.stderr)
        raise SystemExit(1)
    print("default")
elif args[:3] == ["compute", "routers", "create"]:
    state["router"] = True
    save()
elif args[:4] == ["compute", "routers", "nats", "list"]:
    if state["nat"]:
        print("mantra-nat-us-west4")
elif args[:4] == ["compute", "routers", "nats", "create"]:
    if os.environ.get("FAKE_FAIL_NAT") == "true":
        raise SystemExit(1)
    state["nat"] = True
    save()
elif args[:4] == ["compute", "routers", "nats", "describe"]:
    fmt = option("--format")
    if fmt == "value(natIpAllocateOption)":
        print("AUTO_ONLY")
    else:
        print("ALL_SUBNETWORKS_ALL_IP_RANGES")
elif args[:4] == ["compute", "routers", "nats", "delete"]:
    state["nat"] = False
    save()
elif args[:3] == ["compute", "routers", "delete"]:
    state["router"] = False
    save()
else:
    print(f"unsupported fake gcloud call: {args}", file=sys.stderr)
    raise SystemExit(2)
""",
        encoding="utf-8",
    )
    path.chmod(0o755)


def _environment(
    tmp_path: Path, *, preexisting_network: bool = False
) -> dict[str, str]:
    """Return an isolated launcher environment and its valid input records."""
    binaries = tmp_path / "bin"
    binaries.mkdir(parents=True)
    _fake_gcloud(binaries / "gcloud")
    state = tmp_path / "gcloud-state.json"
    _write_json(
        state,
        {
            "quota_rejected": False,
            "instance": False,
            "disk": False,
            "zone": "",
            "router": preexisting_network,
            "nat": preexisting_network,
        },
    )
    cloud_probe = tmp_path / "cloud-probe.json"
    _probe(cloud_probe)
    return {
        **os.environ,
        "PATH": f"{binaries}:/usr/bin:/bin:/usr/sbin:/sbin",
        "PYTHON": sys.executable,
        "PROJECT": "mantra-fixture",
        "INSTANCE_NAME": "mantra-g2-test",
        "ZONE_SEARCH_ORDER": "us-west4-a us-west4-c",
        "UPDATE_SSH_CONFIG": "false",
        "VIPER_CLOUD_PROBE_RECEIPT": str(cloud_probe),
        "LAUNCH_RECEIPT_PATH": str(tmp_path / "launch.json"),
        "TEARDOWN_RECEIPT_PATH": str(tmp_path / "teardown.json"),
        "FAKE_GCLOUD_STATE": str(state),
        "FAKE_GCLOUD_LOG": str(tmp_path / "gcloud.log"),
    }


def _run(
    env: dict[str, str], action: str = "launch"
) -> subprocess.CompletedProcess[str]:
    """Run one launcher action and retain output for a failed assertion."""
    return subprocess.run(
        ("/bin/bash", str(LAUNCHER), action),
        cwd=ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def test_probes_launch_and_deletes_worker_and_disk(tmp_path: Path) -> None:
    """Fall back after quota denial, then remove only launch-owned resources."""
    env = _environment(tmp_path)

    launched = _run(env)

    assert launched.returncode == 0, launched.stderr + launched.stdout
    launch = json.loads(Path(env["LAUNCH_RECEIPT_PATH"]).read_text())
    assert launch["zone"] == "us-west4-c"
    assert launch["router_created"] is True
    assert launch["nat_created"] is True
    calls = Path(env["FAKE_GCLOUD_LOG"]).read_text(encoding="utf-8")
    assert calls.index("us-west4-a") < calls.index("us-west4-c")

    restore = tmp_path / "restore.json"
    _probe(restore)
    env["ARTIFACT_RESTORE_RECEIPT"] = str(restore)
    torn_down = _run(env, "teardown")

    assert torn_down.returncode == 0, torn_down.stderr + torn_down.stdout
    state = json.loads(Path(env["FAKE_GCLOUD_STATE"]).read_text())
    assert state == {
        "disk": False,
        "instance": False,
        "nat": False,
        "quota_rejected": True,
        "router": False,
        "zone": "us-west4-c",
    }
    assert json.loads(Path(env["TEARDOWN_RECEIPT_PATH"]).read_text()) == {
        "artifact_restore_receipt": str(restore),
        "boot_disk_absent": True,
        "launch_receipt": env["LAUNCH_RECEIPT_PATH"],
        "schema_version": 1,
        "worker_absent": True,
    }


def test_blocks_training_or_teardown_on_failed_probe(tmp_path: Path) -> None:
    """Create no worker before storage proof and retain one before bad teardown."""
    env = _environment(tmp_path)
    env.pop("VIPER_CLOUD_PROBE_RECEIPT")

    blocked_launch = _run(env)

    assert blocked_launch.returncode != 0
    assert not Path(env["FAKE_GCLOUD_LOG"]).exists()

    env = _environment(tmp_path / "teardown")
    launched = _run(env)
    assert launched.returncode == 0, launched.stderr + launched.stdout
    failed_restore = tmp_path / "failed-restore.json"
    _probe(failed_restore, passed=False)
    env["ARTIFACT_RESTORE_RECEIPT"] = str(failed_restore)

    blocked_teardown = _run(env, "teardown")

    assert blocked_teardown.returncode != 0
    state = json.loads(Path(env["FAKE_GCLOUD_STATE"]).read_text())
    assert state["instance"] is True
    assert state["disk"] is True


@pytest.mark.parametrize("preexisting_network", [False, True])
def test_cleans_partial_launch_without_deleting_shared_network(
    tmp_path: Path,
    preexisting_network: bool,
) -> None:
    """Clean a failed worker and preserve network resources reused by the run."""
    env = _environment(tmp_path, preexisting_network=preexisting_network)
    env["ZONE_SEARCH_ORDER"] = "us-west4-c"
    if preexisting_network:
        env["FAKE_FAIL_INSTANCE_ID"] = "true"
    else:
        env["FAKE_FAIL_NAT"] = "true"

    failed = _run(env)

    assert failed.returncode != 0
    state = json.loads(Path(env["FAKE_GCLOUD_STATE"]).read_text())
    assert state["instance"] is False
    assert state["disk"] is False
    assert state["router"] is preexisting_network
    assert state["nat"] is preexisting_network
