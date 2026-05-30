# Wachturm — Makefile (the user contract; see AGENTS.md §4).
#
# Every common operation is `make <target>`. Start with `make help`.
#
# Phase 0: only `help`, `doctor`, and `test` do real work. Every other
# target's implementation lands in a later phase — those print an
# informative message and exit non-zero (they never silently no-op).

.DEFAULT_GOAL := help
SHELL := bash
.SHELLFLAGS := -eu -o pipefail -c

.PHONY: help doctor test check up up-casemgmt up-full down reset logs \
        scenario scenarios score hint tutor noise-start noise-stop \
        shell portal trust-certs first-run-creds

# ─── Real targets (Phase 0) ──────────────────────────────────────────

help: ## Show this help (lists every target and what it does)
	@echo "Wachturm — make targets:"
	@grep -hE '^[a-zA-Z0-9_-]+:.*## ' $(MAKEFILE_LIST) \
		| awk 'BEGIN{FS=":.*## "}{printf "  %-16s %s\n", $$1, $$2}'

doctor: ## Check Docker, Compose, and host resources
	@python3 runner/src/wachturm/doctor.py

install: ## Create .venv and install the runner (required before make up-casemgmt on a fresh clone)
	python3 -m venv "$(CURDIR)/.venv"
	"$(CURDIR)/.venv/bin/pip" install -e "$(CURDIR)/runner" --quiet
	@echo "Runner installed in .venv. Run 'source .venv/bin/activate' to use it interactively."

test: ## Run the Python test suite (needs: make install or pip install -e runner[dev])
	@if [ -x "$(CURDIR)/.venv/bin/python" ]; then PY="$(CURDIR)/.venv/bin/python"; else PY=python3; fi; \
		cd runner && "$$PY" -m pytest

check: ## Run the full CI gate locally — ruff + mypy --strict + pytest, same scope as ci.yml (needs: pip install -e runner[dev])
	@if [ -x "$(CURDIR)/.venv/bin/python" ]; then PY="$(CURDIR)/.venv/bin/python"; else PY=python3; fi; \
		echo "→ ruff check runner/"          && "$$PY" -m ruff check runner/          && \
		echo "→ ruff format --check runner/" && "$$PY" -m ruff format --check runner/ && \
		echo "→ mypy --strict runner/"       && "$$PY" -m mypy --strict runner/       && \
		echo "→ pytest (cd runner)"          && cd runner && "$$PY" -m pytest

# ─── Stubs — implemented in a later phase (BUILD_ORDER.md) ────────────

up: ## [Phase 1] Bring up the core profile (Wazuh + victims + attacker + portal)
	docker compose --profile core up -d --build --wait --wait-timeout 1200
	@echo "core profile healthy. Portal: http://localhost:8000  ·  next: make scenario SCN=SCN-001"

up-casemgmt: ## [Phase 2] Bring up core + casemgmt (DFIR-IRIS + Cortex)
	@mem=$$(docker info --format '{{.MemTotal}}' 2>/dev/null); \
		[[ "$$mem" =~ ^[0-9]+$$ ]] || mem=0; \
		gib=$$(( mem / 1073741824 )); \
		if [ "$$gib" -gt 0 ] && [ "$$gib" -lt 12 ]; then \
		  echo "WARN  Docker is allocated ~$$gib GiB. core+casemgmt needs ~10 GiB"; \
		  echo "      working set: the Phase-1 stack PLUS DFIR-IRIS, Postgres,"; \
		  echo "      RabbitMQ, Cortex and a 1 GiB-heap Elasticsearch. If services"; \
		  echo "      flap or get OOM-killed, raise Docker's memory (Docker Desktop:"; \
		  echo "      Settings → Resources → Memory) to 12-16 GiB and retry."; \
		fi
	@# token dir USER-owned BEFORE compose up (else Docker root-creates
	@# the wazuh-to-iris bind-mount source); drop any stale token so the
	@# watcher waits for THIS lab's fresh one, not a previous lab's.
	@mkdir -p "$$HOME/.wachturm" && chmod 700 "$$HOME/.wachturm" && rm -f "$$HOME/.wachturm/iris.token"
	docker compose --profile core --profile casemgmt up -d $(if $(NO_BUILD),,--build) --wait --wait-timeout 1800
	@echo "core + casemgmt healthy — bootstrapping the IRIS API token…"
	@if [ ! -x "$(CURDIR)/.venv/bin/python" ]; then \
	  echo "→ first run: creating .venv and installing runner…"; \
	  python3 -m venv "$(CURDIR)/.venv" && \
	  "$(CURDIR)/.venv/bin/pip" install -e "$(CURDIR)/runner" --quiet; \
	fi
	@if [ -x "$(CURDIR)/.venv/bin/python" ]; then PY="$(CURDIR)/.venv/bin/python"; else PY=python3; fi; \
		cd runner && PYTHONPATH=src "$$PY" -m wachturm iris-bootstrap
	@# Cortex bootstrap is idempotent (skips when ~/.wachturm/cortex.token
	@# still authenticates — no key churn on a plain re-up). ABUSEIPDB is
	@# opt-in: read the key from .env if present; unset just means that
	@# one analyzer is not enabled and the lab still works out of the box.
	@echo "bootstrapping Cortex (migrate + org + service key + analyzers)…"
	@if [ -x "$(CURDIR)/.venv/bin/python" ]; then PY="$(CURDIR)/.venv/bin/python"; else PY=python3; fi; \
		AK=$$(grep -E '^ABUSEIPDB_API_KEY=' "$(CURDIR)/.env" 2>/dev/null | tail -1 | cut -d= -f2-); \
		cd runner && PYTHONPATH=src ABUSEIPDB_API_KEY="$$AK" "$$PY" -m wachturm cortex-bootstrap
	@echo "core + casemgmt ready."
	@echo "  IRIS   : https://127.0.0.1:9000    Cortex : http://127.0.0.1:9001"
	@echo "  tokens : ~/.wachturm/iris.token + ~/.wachturm/cortex.token (0600)"
	@echo "  next   : make scenario SCN=SCN-001  (Phase 2 turns alerts into IRIS cases)"

up-full: ## [Phase 4] Bring up all profiles (adds SOAR + Threat Intel)
	@echo "make up-full: not yet implemented — lands in Phase 4 (see BUILD_ORDER.md)."; exit 1

down: ## [Phase 1] Stop and remove containers (keep volumes)
	docker compose --profile core down
	@echo "containers removed; volumes kept (use 'make reset' to wipe volumes too)."

reset: ## [Phase 1] Stop and remove containers AND volumes (clean state)
	@if [ "$(RESET_YES)" != "1" ]; then \
	  printf 'make reset DESTROYS all containers, docker volumes, and generated\nTLS material (any in-lab student work is lost). Type "yes" to proceed: '; \
	  read ans; [ "$$ans" = "yes" ] || { echo "aborted (set RESET_YES=1 to skip this prompt)."; exit 1; }; \
	fi
	docker compose --profile core --profile casemgmt --profile soar --profile intel down -v --remove-orphans
	@rm -rf config/wazuh/wazuh_indexer_ssl_certs/* 2>/dev/null || true
	@echo "clean state: containers + volumes + generated certs cleared. Next: make up"

logs: ## [Phase 1] Tail a service (SERVICE=name)
	@if [ -z "$(SERVICE)" ]; then echo "usage: make logs SERVICE=wazuh-manager"; exit 2; fi
	docker compose logs -f --tail=200 $(SERVICE)

scenario: ## [Phase 1] Run a scenario (SCN=SCN-001)
	@if [ -z "$(SCN)" ]; then echo "usage: make scenario SCN=SCN-001"; exit 2; fi
	@if [ -x "$(CURDIR)/.venv/bin/python" ]; then PY="$(CURDIR)/.venv/bin/python"; else PY=python3; fi; \
		cd runner && PYTHONPATH=src "$$PY" -m wachturm scenario "$(SCN)"

scenarios: ## [Phase 3a] List/filter scenarios (FILTER='--difficulty hard --verdict benign')
	@if [ -x "$(CURDIR)/.venv/bin/python" ]; then PY="$(CURDIR)/.venv/bin/python"; else PY=python3; fi; \
		cd runner && PYTHONPATH=src "$$PY" -m wachturm scenarios $(FILTER)

score: ## [Phase 2] Score your closed case against the answer key (SCN=SCN-001)
	@if [ -z "$(SCN)" ]; then echo "usage: make score SCN=SCN-001"; exit 2; fi
	@if [ -x "$(CURDIR)/.venv/bin/python" ]; then PY="$(CURDIR)/.venv/bin/python"; else PY=python3; fi; \
		cd runner && PYTHONPATH=src "$$PY" -m wachturm score "$(SCN)"

hint: ## [Phase 3a] Reveal the next hint (SCN=SCN-001; -5 pts each at scoring)
	@if [ -z "$(SCN)" ]; then echo "usage: make hint SCN=SCN-001"; exit 2; fi
	@if [ -x "$(CURDIR)/.venv/bin/python" ]; then PY="$(CURDIR)/.venv/bin/python"; else PY=python3; fi; \
		cd runner && PYTHONPATH=src "$$PY" -m wachturm hint "$(SCN)"

tutor: ## [Phase 3a] Open the Socratic tutor (menu picks the agent when several are installed; override: AGENT=claude|codex|gemini|opencode|pi)
	@$(if $(AGENT),WACHTURM_TUTOR_AGENT=$(AGENT) )bash tools/launch-tutor.sh

noise-start: ## [Phase 1] Start the benign-noise generator
	docker compose --profile core up -d --build noise-gen
	@echo "noise-gen started (benign ambient traffic). Logs: docker logs -f noise-gen"

noise-stop: ## [Phase 1] Stop the benign-noise generator
	docker compose --profile core stop noise-gen
	@echo "noise-gen stopped."

shell: ## [Phase 1] Exec a shell into a container (SERVICE=name)
	@if [ -z "$(SERVICE)" ]; then echo "usage: make shell SERVICE=vic-jump"; exit 2; fi
	docker compose exec $(SERVICE) sh -c 'exec bash 2>/dev/null || exec sh'

portal: ## [Phase 1] Open the portal landing page in your browser
	@url=http://localhost:8000; \
	if command -v open >/dev/null 2>&1; then open "$$url"; \
	elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$$url"; \
	elif command -v powershell.exe >/dev/null 2>&1; then powershell.exe -NoProfile -Command "Start-Process '$$url'"; \
	fi; \
	echo "Portal: $$url"

trust-certs: ## [Phase 1] Install an mkcert local CA and reissue tool certs
	@command -v mkcert >/dev/null 2>&1 || { \
	  echo "mkcert not found — install it, then re-run 'make trust-certs':"; \
	  echo "  macOS        : brew install mkcert nss"; \
	  echo "  Linux        : apt install libnss3-tools  +  mkcert from github.com/FiloSottile/mkcert/releases"; \
	  echo "  Windows/WSL2 : run inside the WSL2 shell; choco/scoop install mkcert"; \
	  exit 1; }
	mkcert -install
	mkcert -cert-file config/wazuh/wazuh_indexer_ssl_certs/wazuh.dashboard.pem \
	       -key-file  config/wazuh/wazuh_indexer_ssl_certs/wazuh.dashboard-key.pem \
	       localhost 127.0.0.1 ::1
	docker compose restart wazuh-dashboard
	@echo "Done — mkcert local CA trusted by your OS; the Wazuh dashboard now"
	@echo "serves a locally-trusted cert. Hard-refresh https://127.0.0.1:8443/ ."
	@echo "Only the browser-facing dashboard cert changed; Wazuh's internal"
	@echo "TLS (root-ca.pem) is untouched. Linux: identical command."

first-run-creds: ## Print first-run credentials/URLs for running services
	@port=8443; irispw=changeme_in_env; \
	if [ -f .env ]; then \
	  v=$$(grep -E '^WAZUH_DASHBOARD_PORT=' .env 2>/dev/null | tail -1 | cut -d= -f2); \
	  if [ -n "$$v" ]; then port=$$v; fi; \
	  p=$$(grep -E '^IRIS_ADM_PASSWORD=' .env 2>/dev/null | tail -1 | cut -d= -f2-); \
	  if [ -n "$$p" ]; then irispw=$$p; fi; \
	fi; \
	echo "Wachturm — first-run credentials (loopback-only sealed lab)"; \
	echo "----------------------------------------------------------"; \
	echo "[Phase 1 — core profile]"; \
	echo "Wazuh dashboard : https://127.0.0.1:$$port/"; \
	echo "  login         : admin / SecretPassword"; \
	echo "  Wazuh API     : wazuh-wui / MyS3cr37P450r.*-"; \
	echo "  (upstream Wazuh DEMO defaults — config/wazuh/wazuh_indexer/"; \
	echo "   internal_users.yml. Self-signed-cert warning is expected.)"; \
	echo ""; \
	echo "[Phase 2 — casemgmt profile, after 'make up-casemgmt']"; \
	echo "DFIR-IRIS      : https://127.0.0.1:9000/  (HTTPS; self-signed)"; \
	echo "  login        : administrator / $$irispw"; \
	echo "                 (IRIS_ADM_PASSWORD in .env; default shown if"; \
	echo "                  unset. IRIS forces a password change on first"; \
	echo "                  login — pick anything, the lab is loopback.)"; \
	echo "Cortex         : http://127.0.0.1:9001/  (HTTP, not HTTPS)"; \
	echo "  analyst      : wachturm-svc / wachturm-analyst   (org wachturm"; \
	echo "                 — THIS is the login students use to run"; \
	echo "                 analyzers for the documented IRIS->Cortex pivot)"; \
	echo "  superadmin   : admin / wachturm-admin   (org cortex; manages"; \
	echo "                 users/orgs only — cannot run analyzers)"; \
	echo "  (sealed-lab defaults set by 'make up-casemgmt' cortex-bootstrap;"; \
	echo "   AbuseIPDB analyzer is enabled only if ABUSEIPDB_API_KEY is in"; \
	echo "   .env — the keyless analyzers always work.)"; \
	echo ""; \
	echo "API tokens (0600, written by 'make up-casemgmt' once the stack"; \
	echo "is healthy; integration + scoring read these — never commit them):"; \
	echo "  ~/.wachturm/iris.token   IRIS admin api_key (read out of"; \
	echo "                           iris-db — IRIS exposes no token API;"; \
	echo "                           authenticated against /api/ping)"; \
	echo "  ~/.wachturm/cortex.token wachturm-svc org API key (minted via"; \
	echo "                           the Cortex API bootstrap)"; \
	echo ""; \
	echo "SECURITY: Cortex mounts the host Docker socket (root-equivalent)"; \
	echo "to run each analyzer as a transient container, plus a"; \
	echo "/tmp/cortex-jobs bind for analyzer job I/O. Accepted ONLY for"; \
	echo "this local single-operator loopback lab — see SECURITY.md."; \
	echo ""; \
	echo "Shuffle / MISP : not deployed until Phase 4."
