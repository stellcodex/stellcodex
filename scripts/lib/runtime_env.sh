#!/usr/bin/env bash

RUNTIME_ENV_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_ENV_REPO_ROOT="$(cd "${RUNTIME_ENV_DIR}/../.." && pwd)"

RUNTIME_ENV_DEFAULT_ENV_FILES=(
  "${RUNTIME_ENV_REPO_ROOT}/.env"
  "${RUNTIME_ENV_REPO_ROOT}/infrastructure/deploy/.env"
  "/var/www/stellcodex/.env"
)

runtime_has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

runtime_container_exists() {
  local candidate="${1:-}"
  [ -n "${candidate}" ] || return 1
  runtime_has_cmd docker || return 1
  docker inspect "${candidate}" >/dev/null 2>&1
}

runtime_first_existing_container() {
  local candidate
  for candidate in "$@"; do
    if runtime_container_exists "${candidate}"; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

runtime_first_existing_file() {
  local candidate
  for candidate in "$@"; do
    [ -n "${candidate}" ] || continue
    if [ -f "${candidate}" ]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

runtime_strip_wrapping_quotes() {
  local value="${1:-}"
  if [[ "${value}" == \"*\" && "${value}" == *\" ]]; then
    value="${value:1:${#value}-2}"
  elif [[ "${value}" == \'*\' && "${value}" == *\' ]]; then
    value="${value:1:${#value}-2}"
  fi
  printf '%s\n' "${value}"
}

runtime_read_env_value() {
  local key="${1:-}"
  shift || true

  local value="${!key:-}"
  if [ -n "${value}" ]; then
    printf '%s\n' "${value}"
    return 0
  fi

  if [ "$#" -eq 0 ]; then
    set -- "${RUNTIME_ENV_DEFAULT_ENV_FILES[@]}"
  fi

  local file line
  for file in "$@"; do
    [ -f "${file}" ] || continue
    while IFS= read -r line || [ -n "${line}" ]; do
      case "${line}" in
        ""|\#*)
          continue
          ;;
        "${key}"=*)
          runtime_strip_wrapping_quotes "${line#*=}"
          return 0
          ;;
      esac
    done < "${file}"
  done
  return 1
}

runtime_check_http_code() {
  local url="${1:-}"
  local timeout="${2:-5}"
  curl -sS -o /dev/null -w "%{http_code}" --max-time "${timeout}" "${url}" 2>/dev/null || true
}

runtime_resolve_backend_base_url() {
  local explicit="${BASE_URL:-${BACKEND_BASE_URL:-}}"
  if [ -n "${explicit}" ]; then
    printf '%s\n' "${explicit%/}"
    return 0
  fi

  local candidate path code
  for candidate in "http://127.0.0.1:8000"; do
    for path in "/api/v1/health" "/api/v1/admin/health" "/health" "/healthz" "/readyz" "/_health"; do
      code="$(runtime_check_http_code "${candidate}${path}")"
      if [ "${code}" = "200" ]; then
        printf '%s\n' "${candidate}"
        return 0
      fi
    done
  done

  printf '%s\n' "http://127.0.0.1:8000"
}

runtime_resolve_front_base_url() {
  local explicit="${FRONT_BASE:-}"
  if [ -n "${explicit}" ]; then
    printf '%s\n' "${explicit%/}"
    return 0
  fi

  local candidate path code
  for candidate in "http://127.0.0.1:3010" "http://127.0.0.1:3000"; do
    for path in "/sign-in" "/"; do
      code="$(runtime_check_http_code "${candidate}${path}")"
      case "${code}" in
        200|301|302|307|308)
          printf '%s\n' "${candidate}"
          return 0
          ;;
      esac
    done
  done

  printf '%s\n' "http://127.0.0.1:3010"
}

runtime_resolve_step_sample_path() {
  runtime_first_existing_file \
    "${STEP_SAMPLE:-}" \
    "/var/stellcodex/work/samples/parca.STEP" \
    "${RUNTIME_ENV_REPO_ROOT}/samples/parca.STEP"
}

runtime_resolve_stl_sample_path() {
  runtime_first_existing_file \
    "${STL_SAMPLE:-}" \
    "/var/www/stellcodex/frontend/public/models/demo.STL" \
    "${RUNTIME_ENV_REPO_ROOT}/frontend/public/models/demo.STL" \
    "${RUNTIME_ENV_REPO_ROOT}/frontend__DISABLED__20260320_193121/public/models/demo.STL"
}

runtime_resolve_db_container() {
  local explicit="${DB_CONTAINER:-}"
  if runtime_container_exists "${explicit}"; then
    printf '%s\n' "${explicit}"
    return 0
  fi
  runtime_first_existing_container "deploy_postgres_1" "stellcodex-postgres"
}

runtime_resolve_minio_container() {
  local explicit="${MINIO_CONTAINER:-${LIVE_MINIO_CONTAINER:-}}"
  if runtime_container_exists "${explicit}"; then
    printf '%s\n' "${explicit}"
    return 0
  fi
  runtime_first_existing_container "deploy_minio_1" "stellcodex-minio"
}

runtime_resolve_backend_container() {
  local explicit="${LIVE_BACKEND_CONTAINER:-${BACKEND_CONTAINER:-}}"
  if runtime_container_exists "${explicit}"; then
    printf '%s\n' "${explicit}"
    return 0
  fi
  runtime_first_existing_container "deploy_backend_1" "stellcodex-backend"
}

runtime_resolve_worker_container() {
  local explicit="${LIVE_WORKER_CONTAINER:-${WORKER_CONTAINER:-}}"
  if runtime_container_exists "${explicit}"; then
    printf '%s\n' "${explicit}"
    return 0
  fi
  runtime_first_existing_container "deploy_worker_1" "stellcodex-worker"
}

runtime_resolve_docker_network() {
  local explicit="${PROBE_NETWORK:-}"
  if [ -n "${explicit}" ]; then
    printf '%s\n' "${explicit}"
    return 0
  fi

  local container network
  for container in "$(runtime_resolve_backend_container 2>/dev/null || true)" "$(runtime_resolve_db_container 2>/dev/null || true)"; do
    [ -n "${container}" ] || continue
    network="$(docker inspect "${container}" --format '{{range $k,$v := .NetworkSettings.Networks}}{{println $k}}{{end}}' 2>/dev/null | head -n 1)"
    if [ -n "${network}" ]; then
      printf '%s\n' "${network}"
      return 0
    fi
  done

  printf '%s\n' "deploy_default"
}

runtime_auth_email() {
  runtime_read_env_value "AUTH_EMAIL" \
    || runtime_read_env_value "AUTH_SEED_MEMBER_EMAIL" \
    || runtime_read_env_value "AUTH_SEED_ADMIN_EMAIL"
}

runtime_auth_password() {
  runtime_read_env_value "AUTH_PASSWORD" \
    || runtime_read_env_value "AUTH_SEED_MEMBER_PASSWORD" \
    || runtime_read_env_value "AUTH_SEED_ADMIN_PASSWORD"
}

runtime_json_field() {
  python3 - "$1" "$2" <<'PY'
import json
import sys

path, field = sys.argv[1], sys.argv[2]
try:
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
except Exception:
    data = {}
value = data.get(field, "")
print(value if value is not None else "")
PY
}

runtime_request_auth_token() {
  local api_base="${1%/}"
  if [ -n "${AUTH_TOKEN:-}" ]; then
    printf '%s\n' "${AUTH_TOKEN}"
    return 0
  fi

  local tmp token email password
  email="$(runtime_auth_email 2>/dev/null || true)"
  password="$(runtime_auth_password 2>/dev/null || true)"
  if [ -z "${email}" ] || [ -z "${password}" ]; then
    return 1
  fi

  tmp="$(mktemp)"
  python3 - "${api_base}" "${email}" "${password}" > "${tmp}" <<'PY'
import json
import sys
import urllib.error
import urllib.request

api_base, email, password = sys.argv[1:]
payload = json.dumps({"email": email, "password": password}).encode()
request = urllib.request.Request(
    f"{api_base.rstrip('/')}/auth/login",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST",
)
try:
    with urllib.request.urlopen(request, timeout=15) as response:
        sys.stdout.write(response.read().decode())
except urllib.error.HTTPError as exc:
    sys.stdout.write(exc.read().decode())
except Exception:
    sys.stdout.write("{}")
PY

  token="$(runtime_json_field "${tmp}" "access_token")"
  rm -f "${tmp}"
  if [ -n "${token}" ]; then
    printf '%s\n' "${token}"
    return 0
  fi
  return 1
}
