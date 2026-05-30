# Security Policy

## Reporting a vulnerability

If you believe you've found a security vulnerability in Wachturm, please report it privately rather than opening a public issue.

**Preferred channel:** [GitHub Security Advisories](https://github.com/lernen-edu/wachturm/security/advisories/new) — this lets us discuss and patch privately, then publish coordinated disclosure when a fix ships.

**Email fallback:** `security@wachturm.dev` (if you cannot use the GitHub channel).

When reporting, include:

- A description of the issue and its potential impact
- Steps to reproduce, with a minimal proof-of-concept if possible
- The affected version(s) — output of `git rev-parse HEAD` is ideal
- Any suggested mitigation

We aim to acknowledge reports within 72 hours and provide a status update within 14 days.

## Scope

Wachturm is a self-hosted educational simulator. The following classes of issue are in scope:

- **Container escape** from any Wachturm container to the host
- **Unintended network egress** from isolated networks (`wachturm-attack` reaching the internet, `wachturm-victims` reaching the host, etc.)
- **Privilege escalation paths** that a student running scenarios could exploit to gain unintended access
- **Default credentials** that should have been randomized
- **Vulnerabilities in the Wachturm runner** (`runner/`) and integration scripts
- **Vulnerabilities in scenario YAMLs** that could be misused outside the intended educational context
- **Secrets or credentials accidentally committed** to the repo

### Out of scope

- Vulnerabilities in upstream tools (Wazuh, DFIR-IRIS, Cortex, Shuffle, MISP, Suricata, etc.) — report those to their respective projects. We will track and consume upstream fixes via Dependabot.
- Issues that require an attacker to already have root on the host or have arbitrary file-system access.
- Misconfigurations arising from non-default operator deployment choices (running with privileged containers, exposing UIs beyond loopback, disabling network isolation).
- Theoretical vulnerabilities without a practical demonstration.
- Vulnerabilities in tools or services Wachturm uses for development but does not ship (e.g., GitHub Actions runners, Codespaces).

## Supported versions

Wachturm follows semantic versioning. Security updates are provided for:

- The current minor version (`MAJOR.MINOR.x`).
- The previous minor version, until 90 days after a new minor version is released.

Older versions receive no security updates. Users are encouraged to stay current with the latest release.

## Disclosure timeline

Our default process for a confirmed vulnerability:

1. Acknowledge receipt within 72 hours.
2. Confirm or dispute scope within 14 days.
3. Develop a fix in the private repo.
4. Coordinate disclosure timing with the reporter (default: 90 days from confirmation, or sooner if a fix is ready).
5. Release a patched version and publish a GitHub Security Advisory.
6. Credit the reporter, or honor a request for anonymity.

For critical vulnerabilities with active exploitation, the timeline compresses — typically a fix within 7 days of confirmation.

## What we will not do

- We will not pursue legal action against researchers acting in good faith.
- We will not require an NDA to discuss your finding.
- We will not pay a bounty — Wachturm is a non-commercial educational project. We can credit you in the advisory and in release notes.

## Security posture overview

Wachturm's security stance is intentionally narrow:

- **Local-laptop deployment is the supported use case.** Multi-tenant or cloud deployments are user-driven and not security-supported.
- **The attacker container has no internet egress by default.** This is enforced by Docker network configuration and is a non-negotiable design constraint.
- **All UIs bind to loopback only** (`127.0.0.1`). Exposing them more broadly is a user-driven configuration change.
- **Cortex requires the host Docker socket.** Cortex spawns each analyzer as a transient container, so the `cortex` service mounts `/var/run/docker.sock` — root-equivalent on the host, the single highest-blast-radius mount in the stack. This is a deliberate, accepted trade-off for the local single-operator lab: Cortex ingress is loopback-only and the host is the operator's own machine. Operators who object can run the `casemgmt` profile without Cortex; a socket-free custom-analyzer image is the documented hardening backlog. `shuffle-orborus` (Phase 4) carries the same requirement.
- **Cortex analyzer job directory is a host bind** (`/tmp/cortex-jobs:/tmp/cortex-jobs`, identical path inside and outside the container — the official TheHive-Project Cortex pattern). Cortex writes each analyzer's transient input/output there and asks the host Docker to bind it into the neuron; the path must match on both sides or every analyzer fails. This is *entailed by* the Docker-socket decision above — dockerized analyzers cannot run without a shared job directory — and is far lower blast-radius (short-lived per-job scratch, `keepJobFolder=false`, no credentials). Same single-operator-loopback justification applies.
- **No real malware samples** are ever shipped. Scenarios use EICAR and behavioral simulation only.
- **Dependency scanning** (Dependabot) and **static analysis** (CodeQL) run on every commit and PR. Container images built by the project are scanned with Trivy.
- **Push protection** is enabled to block accidental secret commits.

The full architecture and threat model are documented in `ARCHITECTURE.md`.
