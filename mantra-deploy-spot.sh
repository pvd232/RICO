#!/usr/bin/env bash
set -euo pipefail

# === MANTRA CORE PARAMETERS ===
PROJECT="${PROJECT:-mantra-477901}"
MACHINE_TYPE="${MACHINE_TYPE:-g2-standard-12}"
INSTANCE_NAME="${INSTANCE_NAME:-mantra-g2-spot}"
EXPECTED_ACCELERATOR_PROFILE="nvidia-l4,1"
PROVISIONING_MODEL="${PROVISIONING_MODEL:-SPOT}"
if [[ "$PROVISIONING_MODEL" != "SPOT" && "$PROVISIONING_MODEL" != "STANDARD" ]]; then
  echo "[!] Error: PROVISIONING_MODEL must be SPOT or STANDARD."
  exit 1
fi

# Global VPC/IAP resources and per-region Cloud NAT resource names
NETWORK="${NETWORK:-default}"
IAP_FIREWALL_RULE="${IAP_FIREWALL_RULE:-allow-ssh-from-iap}"
IAP_NETWORK_TAG="${IAP_NETWORK_TAG:-allow-ssh-iap}"
NAT_ROUTER_PREFIX="${NAT_ROUTER_PREFIX:-mantra-router}"
NAT_GATEWAY_PREFIX="${NAT_GATEWAY_PREFIX:-mantra-nat}"

# Stable local SSH alias used by editors. Set UPDATE_SSH_CONFIG=false to opt out.
UPDATE_SSH_CONFIG="${UPDATE_SSH_CONFIG:-true}"
SSH_CONFIG_FILE="${SSH_CONFIG_FILE:-$HOME/.ssh/config}"
SSH_HOST_ALIAS="${SSH_HOST_ALIAS:-mantra-g2}"
SSH_USER="${SSH_USER:-$(id -un)}"

# Default to the MANTRA machine image. Set SOURCE_IMAGE and
# SOURCE_IMAGE_PROJECT to create a clean boot disk from a pinned public image.
SOURCE_MACHINE_IMAGE="${SOURCE_MACHINE_IMAGE:-mantra-backup-blueprint}"
SOURCE_IMAGE="${SOURCE_IMAGE:-}"
SOURCE_IMAGE_PROJECT="${SOURCE_IMAGE_PROJECT:-}"
BOOT_DISK_DEVICE_NAME="persistent-disk-0"
BOOT_DISK_SIZE="${BOOT_DISK_SIZE:-}"
BOOT_DISK_TYPE="${BOOT_DISK_TYPE:-}"
INSTANCE_LABELS="${INSTANCE_LABELS:-}"

# Search lower-demand regions before established MANTRA regions. Central US is
# intentionally absent because these jobs should avoid its higher Spot churn.
# Override this ordered, space-separated list for a deliberate capacity probe.
ZONE_SEARCH_ORDER="${ZONE_SEARCH_ORDER:-us-west4-a us-west4-c us-east4-a us-east4-c us-west1-b us-west1-c us-west1-a us-east1-d us-east1-c us-east1-b}"
read -r -a CANDIDATE_ZONES <<< "$ZONE_SEARCH_ORDER"

ACTION="${1:-launch}"
PYTHON="${PYTHON:-python3}"
LAUNCH_RECEIPT_PATH="${LAUNCH_RECEIPT_PATH:-.viper/gpu/${INSTANCE_NAME}.json}"
VIPER_CLOUD_PROBE_RECEIPT="${VIPER_CLOUD_PROBE_RECEIPT:-}"
ARTIFACT_RESTORE_RECEIPT="${ARTIFACT_RESTORE_RECEIPT:-}"
TEARDOWN_RECEIPT_PATH="${TEARDOWN_RECEIPT_PATH:-${LAUNCH_RECEIPT_PATH%.json}-teardown.json}"

CREATED_ZONE=""
BOOT_DISK_NAME=""
REGION=""
NAT_ROUTER_NAME=""
NAT_GATEWAY_NAME=""
NAT_ROUTER_CREATED=false
NAT_GATEWAY_CREATED=false
CLEANUP_ON_EXIT=false

require_digest_probe() {
  local path="$1"
  local label="$2"

  if [[ -z "$path" || ! -f "$path" ]]; then
    echo "[!] Error: $label is required and must name a file."
    return 1
  fi
  "$PYTHON" - "$path" "$label" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
label = sys.argv[2]
record = json.loads(path.read_text(encoding="utf-8"))
required = {"passed", "artifact_uri", "sha256", "restored_sha256"}
missing = required - record.keys()
if missing:
    raise SystemExit(f"{label} lacks fields: {sorted(missing)}")
if record["passed"] is not True:
    raise SystemExit(f"{label} did not pass")
digest = record["sha256"]
if not isinstance(digest, str) or len(digest) != 64:
    raise SystemExit(f"{label} has an invalid SHA-256 digest")
if record["restored_sha256"] != digest:
    raise SystemExit(f"{label} restored different bytes")
PY
}

delete_instance_and_disk() {
  local zone="$1"
  local disk="$2"

  gcloud compute instances delete "$INSTANCE_NAME" \
    --project="$PROJECT" \
    --zone="$zone" \
    --delete-disks=all \
    --quiet >/dev/null 2>&1 || true
  if [[ -n "$disk" ]] && gcloud compute disks describe "$disk" \
    --project="$PROJECT" \
    --zone="$zone" >/dev/null 2>&1; then
    gcloud compute disks delete "$disk" \
      --project="$PROJECT" \
      --zone="$zone" \
      --quiet >/dev/null
  fi
}

delete_created_network() {
  local region="$1"
  local router="$2"
  local nat="$3"
  local nat_created="$4"
  local router_created="$5"

  if [[ "$nat_created" == true ]]; then
    gcloud compute routers nats delete "$nat" \
      --project="$PROJECT" \
      --router="$router" \
      --region="$region" \
      --quiet >/dev/null 2>&1 || true
  fi
  if [[ "$router_created" == true ]]; then
    gcloud compute routers delete "$router" \
      --project="$PROJECT" \
      --region="$region" \
      --quiet >/dev/null 2>&1 || true
  fi
}

cleanup_failed_launch() {
  local status=$?
  if [[ "$CLEANUP_ON_EXIT" == true && -n "$CREATED_ZONE" ]]; then
    echo "[!] Cleaning resources created by the failed launch in $CREATED_ZONE."
    set +e
    delete_instance_and_disk "$CREATED_ZONE" "$BOOT_DISK_NAME"
    if [[ -n "$REGION" ]]; then
      delete_created_network \
        "$REGION" \
        "$NAT_ROUTER_NAME" \
        "$NAT_GATEWAY_NAME" \
        "$NAT_GATEWAY_CREATED" \
        "$NAT_ROUTER_CREATED"
    fi
    set -e
  fi
  return "$status"
}

write_launch_receipt() {
  local cloud_probe_sha256

  cloud_probe_sha256=$(shasum -a 256 "$VIPER_CLOUD_PROBE_RECEIPT" | awk '{print $1}')
  mkdir -p "$(dirname "$LAUNCH_RECEIPT_PATH")"
  "$PYTHON" - \
    "$LAUNCH_RECEIPT_PATH" "$PROJECT" "$INSTANCE_NAME" "$CREATED_ZONE" \
    "$REGION" "$BOOT_DISK_NAME" "$NAT_ROUTER_NAME" "$NAT_GATEWAY_NAME" \
    "$NAT_ROUTER_CREATED" "$NAT_GATEWAY_CREATED" "$cloud_probe_sha256" \
    "$PROVISIONING_MODEL" <<'PY'
import json
import sys
from pathlib import Path

(
    path,
    project,
    instance,
    zone,
    region,
    boot_disk,
    router,
    nat,
    router_created,
    nat_created,
    cloud_probe_sha256,
    provisioning_model,
) = sys.argv[1:]
record = {
    "schema_version": 1,
    "project": project,
    "instance": instance,
    "zone": zone,
    "region": region,
    "boot_disk": boot_disk,
    "router": router,
    "nat": nat,
    "router_created": router_created == "true",
    "nat_created": nat_created == "true",
    "cloud_probe_sha256": cloud_probe_sha256,
    "provisioning_model": provisioning_model,
}
destination = Path(path)
temporary = destination.with_suffix(destination.suffix + ".tmp")
temporary.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
temporary.replace(destination)
PY
}

teardown_worker() {
  local receipt="$LAUNCH_RECEIPT_PATH"
  local receipt_project
  local receipt_instance
  local zone
  local region
  local boot_disk
  local router
  local nat
  local router_created
  local nat_created

  require_digest_probe "$ARTIFACT_RESTORE_RECEIPT" "ARTIFACT_RESTORE_RECEIPT"
  if [[ ! -f "$receipt" ]]; then
    echo "[!] Error: Launch receipt is unavailable: $receipt"
    return 1
  fi
  IFS=$'\t' read -r receipt_project receipt_instance zone region boot_disk \
    router nat router_created nat_created < <(
    "$PYTHON" - "$receipt" <<'PY'
import json
import sys
from pathlib import Path

record = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
keys = (
    "project",
    "instance",
    "zone",
    "region",
    "boot_disk",
    "router",
    "nat",
    "router_created",
    "nat_created",
)
missing = set(keys) - record.keys()
if missing:
    raise SystemExit(f"launch receipt lacks fields: {sorted(missing)}")
print(*(str(record[key]).lower() if isinstance(record[key], bool) else record[key] for key in keys), sep="\t")
PY
  )
  if [[ "$receipt_project" != "$PROJECT" || "$receipt_instance" != "$INSTANCE_NAME" ]]; then
    echo "[!] Error: Launch receipt names another project or instance."
    return 1
  fi

  delete_instance_and_disk "$zone" "$boot_disk"
  delete_created_network "$region" "$router" "$nat" "$nat_created" "$router_created"
  if gcloud compute instances describe "$INSTANCE_NAME" \
    --project="$PROJECT" --zone="$zone" >/dev/null 2>&1; then
    echo "[!] Error: Worker still exists after teardown."
    return 1
  fi
  if gcloud compute disks describe "$boot_disk" \
    --project="$PROJECT" --zone="$zone" >/dev/null 2>&1; then
    echo "[!] Error: Boot disk still exists after teardown."
    return 1
  fi

  mkdir -p "$(dirname "$TEARDOWN_RECEIPT_PATH")"
  "$PYTHON" - "$TEARDOWN_RECEIPT_PATH" "$receipt" "$ARTIFACT_RESTORE_RECEIPT" <<'PY'
import json
import sys
from pathlib import Path

path, launch_receipt, restore_receipt = map(Path, sys.argv[1:])
record = {
    "schema_version": 1,
    "launch_receipt": str(launch_receipt),
    "artifact_restore_receipt": str(restore_receipt),
    "worker_absent": True,
    "boot_disk_absent": True,
}
temporary = path.with_suffix(path.suffix + ".tmp")
temporary.write_text(json.dumps(record, sort_keys=True) + "\n", encoding="utf-8")
temporary.replace(path)
PY
  echo "[*] Teardown verified for $INSTANCE_NAME in $zone."
}

if [[ "$ACTION" == "teardown" ]]; then
  teardown_worker
  exit 0
fi
if [[ "$ACTION" != "launch" ]]; then
  echo "[!] Usage: $0 [launch|teardown]"
  exit 2
fi

require_digest_probe "$VIPER_CLOUD_PROBE_RECEIPT" "VIPER_CLOUD_PROBE_RECEIPT"

verify_iap_firewall_rule() {
  local rule_network
  local rule_direction
  local rule_disabled
  local rule_sources
  local rule_tags
  local rule_allowed

  if ! rule_network=$(gcloud compute firewall-rules describe "$IAP_FIREWALL_RULE" \
    --project="$PROJECT" \
    --format='value(network.basename())'); then
    echo "[!] Error: Required IAP firewall rule '$IAP_FIREWALL_RULE' was not found."
    return 1
  fi

  rule_direction=$(gcloud compute firewall-rules describe "$IAP_FIREWALL_RULE" \
    --project="$PROJECT" \
    --format='value(direction)')
  rule_disabled=$(gcloud compute firewall-rules describe "$IAP_FIREWALL_RULE" \
    --project="$PROJECT" \
    --format='value(disabled)')
  rule_sources=$(gcloud compute firewall-rules describe "$IAP_FIREWALL_RULE" \
    --project="$PROJECT" \
    --format='value(sourceRanges.list())')
  rule_tags=$(gcloud compute firewall-rules describe "$IAP_FIREWALL_RULE" \
    --project="$PROJECT" \
    --format='value(targetTags.list())')
  rule_allowed=$(gcloud compute firewall-rules describe "$IAP_FIREWALL_RULE" \
    --project="$PROJECT" \
    --format='value(allowed)')

  if [[ "$rule_network" != "$NETWORK" ||
        "$rule_direction" != "INGRESS" ||
        "$rule_disabled" != "False" ||
        "$rule_sources" != "35.235.240.0/20" ||
        "$rule_tags" != "$IAP_NETWORK_TAG" ||
        "$rule_allowed" != *"'IPProtocol': 'tcp'"* ||
        "$rule_allowed" != *"'22'"* ]]; then
    echo "[!] Error: IAP firewall rule '$IAP_FIREWALL_RULE' does not match the required configuration."
    echo "[!] Expected: network=$NETWORK, ingress tcp:22, source=35.235.240.0/20, tag=$IAP_NETWORK_TAG."
    return 1
  fi
}

update_ssh_config() {
  local zone="$1"
  local instance_id="$2"
  local config_dir
  local temp_config
  local temp_config_has_content
  local managed_begin="# BEGIN MANTRA MANAGED HOST $SSH_HOST_ALIAS"
  local managed_end="# END MANTRA MANAGED HOST $SSH_HOST_ALIAS"

  if [[ "$UPDATE_SSH_CONFIG" != "true" ]]; then
    echo "[*] Skipping SSH config update (UPDATE_SSH_CONFIG=$UPDATE_SSH_CONFIG)."
    return 0
  fi

  config_dir=$(dirname "$SSH_CONFIG_FILE")
  mkdir -p "$config_dir"
  chmod 700 "$config_dir"
  touch "$SSH_CONFIG_FILE"
  chmod 600 "$SSH_CONFIG_FILE"
  temp_config=$(mktemp "${config_dir}/mantra-ssh-config.XXXXXX")

  if ! awk \
    -v alias="$SSH_HOST_ALIAS" \
    -v managed_begin="$managed_begin" \
    -v managed_end="$managed_end" '
      $0 == managed_begin { in_managed = 1; next }
      in_managed && $0 == managed_end { in_managed = 0; next }
      in_managed { next }

      $1 == "Host" {
        if (in_legacy) {
          in_legacy = 0
        }
        if (NF == 2 && $2 == alias) {
          in_legacy = 1
          next
        }
      }

      !in_legacy { print }
    ' "$SSH_CONFIG_FILE" > "$temp_config"; then
    rm -f "$temp_config"
    echo "[!] Error: Could not prepare SSH configuration update."
    return 1
  fi

  temp_config_has_content=false
  if [[ -s "$temp_config" ]]; then
    temp_config_has_content=true
  fi

  {
    if [[ "$temp_config_has_content" == true ]]; then
      printf '\n'
    fi
    printf '%s\n' "$managed_begin"
    printf 'Host %s\n' "$SSH_HOST_ALIAS"
    printf '    HostName compute.%s\n' "$instance_id"
    printf '    User %s\n' "$SSH_USER"
    printf '    IdentityFile %s/.ssh/google_compute_engine\n' "$HOME"
    printf '    UserKnownHostsFile %s/.ssh/google_compute_known_hosts\n' "$HOME"
    printf '    HostKeyAlias compute.%s\n' "$instance_id"
    printf '    IdentitiesOnly yes\n'
    printf '    CheckHostIP no\n'
    printf '    StrictHostKeyChecking yes\n'
    printf '    ProxyCommand gcloud compute start-iap-tunnel %s %%p --zone=%s --project=%s --listen-on-stdin --verbosity=error\n' \
      "$INSTANCE_NAME" "$zone" "$PROJECT"
    printf '%s\n' "$managed_end"
  } >> "$temp_config"

  chmod 600 "$temp_config"
  if ! ssh -F "$temp_config" -G "$SSH_HOST_ALIAS" >/dev/null; then
    rm -f "$temp_config"
    echo "[!] Error: Generated SSH configuration failed validation; existing config was preserved."
    return 1
  fi

  if ! mv "$temp_config" "$SSH_CONFIG_FILE"; then
    rm -f "$temp_config"
    echo "[!] Error: Could not install the SSH configuration update."
    return 1
  fi

  echo "[*] Updated SSH alias '$SSH_HOST_ALIAS' in $SSH_CONFIG_FILE."
}

ensure_regional_cloud_nat() {
  local region="$1"
  local router_name="${NAT_ROUTER_PREFIX}-${region}"
  local nat_name="${NAT_GATEWAY_PREFIX}-${region}"
  local router_description
  local router_network
  local router_status
  local nat_names
  local nat_allocation
  local nat_source_ranges

  NAT_ROUTER_NAME="$router_name"
  NAT_GATEWAY_NAME="$nat_name"
  NAT_ROUTER_CREATED=false
  NAT_GATEWAY_CREATED=false

  set +e
  router_description=$(gcloud compute routers describe "$router_name" \
    --project="$PROJECT" \
    --region="$region" \
    --format='value(network.basename())' \
    2>&1)
  router_status=$?
  set -e

  if [[ $router_status -eq 0 ]]; then
    router_network="$router_description"
    if [[ "$router_network" != "$NETWORK" ]]; then
      echo "[!] Error: Router '$router_name' already exists in $region on network '$router_network', not '$NETWORK'."
      return 1
    fi
    echo "[*] Reusing Cloud Router '$router_name' in $region."
  elif grep -qiE 'not found|was not found' <<< "$router_description"; then
    echo "[*] Creating Cloud Router '$router_name' in $region..."
    if ! gcloud compute routers create "$router_name" \
      --project="$PROJECT" \
      --region="$region" \
      --network="$NETWORK" \
      --quiet; then
      return 1
    fi
    NAT_ROUTER_CREATED=true
  else
    echo "[!] Error while checking for Cloud Router '$router_name':"
    echo "$router_description"
    return 1
  fi

  if ! nat_names=$(gcloud compute routers nats list \
    --project="$PROJECT" \
    --router="$router_name" \
    --region="$region" \
    --format='value(name)'); then
    return 1
  fi

  if grep -Fxq "$nat_name" <<< "$nat_names"; then
    echo "[*] Reusing Public NAT gateway '$nat_name' in $region."
  else
    echo "[*] Creating Public NAT gateway '$nat_name' in $region..."
    if ! gcloud compute routers nats create "$nat_name" \
      --project="$PROJECT" \
      --router="$router_name" \
      --region="$region" \
      --type=PUBLIC \
      --auto-allocate-nat-external-ips \
      --nat-all-subnet-ip-ranges \
      --quiet; then
      return 1
    fi
    NAT_GATEWAY_CREATED=true
  fi

  nat_allocation=$(gcloud compute routers nats describe "$nat_name" \
    --project="$PROJECT" \
    --router="$router_name" \
    --region="$region" \
    --format='value(natIpAllocateOption)')
  nat_source_ranges=$(gcloud compute routers nats describe "$nat_name" \
    --project="$PROJECT" \
    --router="$router_name" \
    --region="$region" \
    --format='value(sourceSubnetworkIpRangesToNat)')

  if [[ "$nat_allocation" != "AUTO_ONLY" ||
        "$nat_source_ranges" != "ALL_SUBNETWORKS_ALL_IP_RANGES" ]]; then
    echo "[!] Error: NAT '$nat_name' exists but is not configured for automatic IP allocation across all regional subnet ranges."
    return 1
  fi

  echo "[*] Verified regional outbound path: $NETWORK -> $router_name -> $nat_name."
}

echo "[*] Verifying the global IAP SSH firewall path..."
verify_iap_firewall_rule

echo "[*] Auditing hardware profile compatibility in the configured zone order..."
VALID_ZONES=()

for ZONE in "${CANDIDATE_ZONES[@]}"; do
  ACCELERATOR_PROFILE=$(gcloud compute machine-types describe "$MACHINE_TYPE" \
    --zone="$ZONE" \
    --project="$PROJECT" \
    --format='csv[no-heading](accelerators[].guestAcceleratorType,accelerators[].guestAcceleratorCount)' \
    2>/dev/null) || continue

  if [[ "$ACCELERATOR_PROFILE" == "$EXPECTED_ACCELERATOR_PROFILE" ]]; then
    VALID_ZONES+=("$ZONE")
  fi
done

if [[ ${#VALID_ZONES[@]} -eq 0 ]]; then
  echo "[!] Error: No candidate zones provide $MACHINE_TYPE with one NVIDIA L4 GPU."
  exit 1
fi

SOURCE_ARGS=()
BOOT_DISK_ARGS=(
  --boot-disk-device-name="$BOOT_DISK_DEVICE_NAME"
  --boot-disk-auto-delete
)

if [[ -n "$SOURCE_IMAGE" ]]; then
  if [[ -z "$SOURCE_IMAGE_PROJECT" ]]; then
    echo "[!] Error: SOURCE_IMAGE_PROJECT is required when SOURCE_IMAGE is set."
    exit 1
  fi

  IMAGE_STATUS=$(gcloud compute images describe "$SOURCE_IMAGE" \
    --project="$SOURCE_IMAGE_PROJECT" \
    --format='value(status)')
  if [[ "$IMAGE_STATUS" != "READY" ]]; then
    echo "[!] Error: Source image $SOURCE_IMAGE is not ready (status: $IMAGE_STATUS)."
    exit 1
  fi

  PROVISIONING_KIND="boot_image"
  PROVISIONING_PROJECT="$SOURCE_IMAGE_PROJECT"
  PROVISIONING_NAME="$SOURCE_IMAGE"
  PROVISIONING_ID=$(gcloud compute images describe "$SOURCE_IMAGE" \
    --project="$SOURCE_IMAGE_PROJECT" \
    --format='value(id)')

  SOURCE_ARGS=(
    --image="$SOURCE_IMAGE"
    --image-project="$SOURCE_IMAGE_PROJECT"
  )
else
  IMAGE_STATUS=$(gcloud compute machine-images describe "$SOURCE_MACHINE_IMAGE" \
    --project="$PROJECT" \
    --format='value(status)')
  if [[ "$IMAGE_STATUS" != "READY" ]]; then
    echo "[!] Error: Machine image $SOURCE_MACHINE_IMAGE is not ready (status: $IMAGE_STATUS)."
    exit 1
  fi

  PROVISIONING_KIND="machine_image"
  PROVISIONING_PROJECT="$PROJECT"
  PROVISIONING_NAME="$SOURCE_MACHINE_IMAGE"
  PROVISIONING_ID=$(gcloud compute machine-images describe "$SOURCE_MACHINE_IMAGE" \
    --project="$PROJECT" \
    --format='value(id)')

  SOURCE_ARGS=(--source-machine-image="$SOURCE_MACHINE_IMAGE")
fi

if [[ -n "$BOOT_DISK_SIZE" ]]; then
  BOOT_DISK_ARGS+=(--boot-disk-size="$BOOT_DISK_SIZE")
fi
if [[ -n "$BOOT_DISK_TYPE" ]]; then
  BOOT_DISK_ARGS+=(--boot-disk-type="$BOOT_DISK_TYPE")
fi
PROVISIONING_ARGS=(--provisioning-model="$PROVISIONING_MODEL")
if [[ "$PROVISIONING_MODEL" == "SPOT" ]]; then
  PROVISIONING_ARGS+=(--instance-termination-action=DELETE)
fi
INSTANCE_CREATE_ARGS=(
  --machine-type="$MACHINE_TYPE"
  "${SOURCE_ARGS[@]}"
  "${BOOT_DISK_ARGS[@]}"
  "${PROVISIONING_ARGS[@]}"
  --maintenance-policy=TERMINATE
  --network="$NETWORK"
  --no-address
  --tags="$IAP_NETWORK_TAG"
  --metadata="viper-provisioning-kind=$PROVISIONING_KIND,viper-provisioning-project=$PROVISIONING_PROJECT,viper-provisioning-name=$PROVISIONING_NAME,viper-provisioning-id=$PROVISIONING_ID"
)
if [[ -n "$INSTANCE_LABELS" ]]; then
  INSTANCE_CREATE_ARGS+=(--labels="$INSTANCE_LABELS")
fi

EXISTING_INSTANCES=$(gcloud compute instances list \
  --project="$PROJECT" \
  --filter="name=\"$INSTANCE_NAME\"" \
  --format='csv[no-heading](name,zone.basename(),status)')

if [[ -n "$EXISTING_INSTANCES" ]]; then
  echo "[!] Error: An instance named $INSTANCE_NAME already exists:"
  while IFS= read -r INSTANCE; do
    echo "    $INSTANCE"
  done <<< "$EXISTING_INSTANCES"
  echo "[!] Reuse, restart, rename, or delete the existing instance before deploying another."
  exit 1
fi

echo "[*] Validated source image and G2/L4 target zones."
echo

# === ORDERED DIRECT GPU PROVISIONING LOOP ===
for ZONE in "${VALID_ZONES[@]}"; do
  echo "=== Querying $PROVISIONING_MODEL Resource Pool Availability: $ZONE ==="

  set +e
  # The global VPC selects its auto-mode subnet in the zone's parent region.
  # --no-address keeps the VM private and compliant with the external-IP policy.
  OUTPUT=$(gcloud compute instances create "$INSTANCE_NAME" \
    --project="$PROJECT" \
    --zone="$ZONE" \
    "${INSTANCE_CREATE_ARGS[@]}" \
    2>&1)
  STATUS=$?
  set -e

  # Code 0 means hardware was found AND the network bound successfully
  if [[ $STATUS -eq 0 ]]; then
    CREATED_ZONE="$ZONE"
    CLEANUP_ON_EXIT=true
    trap cleanup_failed_launch EXIT
    BOOT_DISK_NAME=$(gcloud compute instances describe "$INSTANCE_NAME" \
      --project="$PROJECT" \
      --zone="$ZONE" \
      --format='value(disks[0].source.basename())')
    if [[ -z "$BOOT_DISK_NAME" ]]; then
      echo "[!] Error: The VM was created, but its boot disk could not be identified."
      exit 1
    fi
    if ! gcloud compute instances set-disk-auto-delete "$INSTANCE_NAME" \
      --project="$PROJECT" \
      --zone="$ZONE" \
      --disk="$BOOT_DISK_NAME" \
      --auto-delete \
      --quiet; then
      echo "[!] Error: The VM was created, but boot-disk auto-delete could not be enabled."
      exit 1
    fi
    BOOT_DISK_AUTO_DELETE=$(gcloud compute instances describe "$INSTANCE_NAME" \
      --project="$PROJECT" \
      --zone="$ZONE" \
      --format='value(disks[0].autoDelete)')
    if [[ "$BOOT_DISK_AUTO_DELETE" != "True" ]]; then
      echo "[!] Error: The VM was created with boot-disk auto-delete disabled."
      exit 1
    fi

    if ! REGION=$(gcloud compute zones describe "$ZONE" \
      --project="$PROJECT" \
      --format='value(region.basename())'); then
      echo "[!] Error: The VM was created, but its parent region could not be resolved."
      exit 1
    fi

    echo
    echo "[*] $PROVISIONING_MODEL capacity selected $ZONE; configuring outbound access in $REGION..."
    if ! ensure_regional_cloud_nat "$REGION"; then
      echo
      echo "[!] Error: The VM was created, but regional Cloud NAT setup failed."
      exit 1
    fi

    INSTANCE_ID=$(gcloud compute instances describe "$INSTANCE_NAME" \
      --project="$PROJECT" \
      --zone="$ZONE" \
      --format='value(id)')

    if ! update_ssh_config "$ZONE" "$INSTANCE_ID"; then
      echo "[!] Warning: The VM and Cloud NAT are ready, but the local SSH config was not updated."
      echo "[!] You can still connect with the explicit gcloud command below."
    fi

    write_launch_receipt
    CLEANUP_ON_EXIT=false
    trap - EXIT

    echo
    echo "[🚀] SUCCESS: $PROVISIONING_MODEL VM '$INSTANCE_NAME' was created in zone: $ZONE"
    echo "[*] Inbound SSH: IAP -> private VM address (the VM has no external IP)."
    echo "[*] Outbound internet: private VM address -> Cloud NAT '$NAT_GATEWAY_NAME' in $REGION."
    echo "--------------------------------------------------------------------------------"
    echo "👉 RUN THIS EXACT COMMAND TO TUNNEL IN VIA IAP:"
    echo "--------------------------------------------------------------------------------"
    echo "gcloud compute ssh $INSTANCE_NAME --project=$PROJECT --zone=$ZONE --tunnel-through-iap"
    if [[ "$UPDATE_SSH_CONFIG" == "true" ]]; then
      echo "or use the stable editor/SSH alias: ssh $SSH_HOST_ALIAS"
    fi
    echo "--------------------------------------------------------------------------------"
    echo "[!] WHEN FINISHED, VERIFY RESTORATION AND RUN:"
    echo "ARTIFACT_RESTORE_RECEIPT=<receipt.json> LAUNCH_RECEIPT_PATH=$LAUNCH_RECEIPT_PATH $0 teardown"
    echo
    echo "[*] Teardown will remove only network resources recorded as created by this launch."
    exit 0
  fi

  # Error filtering for standard GCE stockout resource patterns
  if grep -qiE "ZONE_RESOURCE_POOL_EXHAUSTED|resource pool exhausted|does not have enough resources|resources? (is|are) currently unavailable in .*zone|quota.*exceeded|exceeded.*quota|QUOTA_EXCEEDED" <<< "$OUTPUT"; then
    echo "[-] Allocation denied by capacity or quota in $ZONE; trying the next declared zone."
  else
    echo "[⚠️] Unexpected Runtime API Exception in $ZONE:"
    echo "$OUTPUT"
    exit "$STATUS"
  fi
  echo
done

echo "[!] Script Failure: No $PROVISIONING_MODEL L4 capacity was available in the configured zones."
exit 1
