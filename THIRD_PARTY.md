# Third-Party Components and Licenses

Wachturm is an open-source project that orchestrates other open-source projects via Docker Compose. This document inventories every third-party component Wachturm depends on, its license, and how it's used. It is part of Wachturm's commitment to license transparency and to honoring upstream licensing requirements.

If you find an error in this inventory, please open an issue.

## How dependencies are used

Wachturm does not modify, link to, or statically embed any of the components below. They are pulled as standalone Docker images at runtime, run as separate processes in isolated containers, and communicate with Wachturm's own code over network APIs. Under the "mere aggregation" doctrine recognized by both the GPL family and Apache License 2.0, this form of use does not create derivative works of the components.

This means each component remains under its own license when run inside Wachturm. Wachturm's own code (the Python runner, scenario YAMLs, Compose files, Dockerfiles, and documentation) is licensed separately under Apache 2.0 (code) and CC BY-SA 4.0 (scenarios and documentation).

## Image provenance

Wachturm sources container images in a fixed order of preference (see `AGENTS.md` §1): (a) the upstream project's own official image, pinned by tag and digest; (b) where no official image exists, an image built locally from the upstream's official package/release repository, version-pinned, on a digest-pinned base and scanned in CI; (c) a vetted community image, digest-pinned with provenance recorded here, only as a last resort. The "How Wachturm uses it" column below states which applies to each component.

## Inventory

### Detection and SIEM

| Component | Upstream | License | How Wachturm uses it |
|---|---|---|---|
| Wazuh Manager | https://github.com/wazuh/wazuh | GPLv2 | Pulled as image; runs as SIEM/HIDS manager. Unmodified. |
| Wazuh Indexer | https://github.com/wazuh/wazuh-indexer | Apache 2.0 | Pulled as image; OpenSearch-based indexer for Wazuh. Unmodified. |
| Wazuh Dashboard | https://github.com/wazuh/wazuh-dashboard | Apache 2.0 | Pulled as image; web UI for Wazuh. Unmodified. |
| Wazuh Agent | https://github.com/wazuh/wazuh | GPLv2 | Installed into victim container images; configuration only, no source modifications. |
| Suricata | https://github.com/OISF/suricata | GPLv2 | Image built locally from OISF's official package repository, version-pinned, on a digest-pinned base; NIDS feeding Wazuh. Configuration only, Suricata itself unmodified. |

### Case management and enrichment

| Component | Upstream | License | How Wachturm uses it |
|---|---|---|---|
| DFIR-IRIS | https://github.com/dfir-iris/iris-web | LGPL3 | Pulled as image; case management platform. Configuration only. |
| Cortex | https://github.com/TheHive-Project/Cortex | AGPLv3 | Pulled as image; observable enrichment engine. Optional Phase 2+ component. Unmodified. |
| Cortex Analyzers (neurons) | https://github.com/TheHive-Project/Cortex-Analyzers | AGPLv3 | Cortex pulls individual analyzer images (`ghcr.io/thehive-project/*`) at first run from the official catalog (`download.thehive-project.org/analyzers.json`). Not redistributed by Wachturm; fetched at runtime by Cortex, run as transient containers, unmodified. Phase 2 enables only keyless analyzers (e.g. MaxMind GeoIP, MISP warning lists); AbuseIPDB is opt-in via an operator key. |
| Alpine Linux | https://alpinelinux.org/ | MIT | Version-pinned base for the one-shot `iris-certs-generator` helper (build-time `openssl` only, sealed runtime); generates the self-signed loopback TLS cert the IRIS nginx front end serves. Configuration only. |
| Python (slim) | https://www.python.org/ | PSF | Version-pinned base for the `wazuh-to-iris` watcher image; runs the in-repo `wachturm` runner package (Wazuh alerts → IRIS cases). Build-time `pip install` only, sealed runtime. Configuration only. |

### SOAR and threat intelligence (Phase 4+)

| Component | Upstream | License | How Wachturm uses it |
|---|---|---|---|
| Shuffle | https://github.com/Shuffle/Shuffle | AGPLv3 | Pulled as image; SOAR playbook engine. Configuration and workflow definitions only. |
| MISP | https://github.com/MISP/MISP | AGPLv3 | Pulled as image; threat intelligence platform. Configuration only. |

### Data stores and infrastructure

| Component | Upstream | License | How Wachturm uses it |
|---|---|---|---|
| PostgreSQL | https://www.postgresql.org/ | PostgreSQL License (BSD-style) | Pulled as image; backs DFIR-IRIS. Unmodified. |
| RabbitMQ | https://github.com/rabbitmq/rabbitmq-server | MPL 2.0 (and Apache 2.0 for some components) | Pulled as image; message bus for DFIR-IRIS. Unmodified. |
| MariaDB | https://github.com/MariaDB/server | GPLv2 | Pulled as image; backs MISP (Phase 4+ only). Unmodified. |
| nginx | http://nginx.org/ | BSD 2-clause | Base image for the Wachturm portal; configuration only. |

### Attack simulation

| Component | Upstream | License | How Wachturm uses it |
|---|---|---|---|
| Atomic Red Team | https://github.com/redcanaryco/atomic-red-team | MIT | Selected tests referenced from Wachturm scenario YAMLs and executed inside the attacker container. Tests are not redistributed; the upstream repo is fetched at attacker-image build time. |
| Custom Python attack scripts | (Wachturm) | Apache 2.0 | Wachturm's own activity generators. |

### Python runner dependencies

The Wachturm runner (`runner/`) is written in Python and depends on these libraries, all installed via `pip` at build time. None are modified.

| Library | License |
|---|---|
| typer | MIT |
| httpx | BSD 3-clause |
| pydantic | MIT |
| pytest | MIT |
| ruff | MIT |
| mypy | MIT |
| pyyaml | MIT |

### Fonts (loaded at runtime by the portal)

| Font | License | Notes |
|---|---|---|
| Big Shoulders Display | OFL 1.1 | Loaded from Google Fonts at runtime by the portal. Not redistributed by Wachturm. For offline deployment, see `docs/offline-fonts.md`. |
| JetBrains Mono | OFL 1.1 | Loaded from Google Fonts at runtime by the portal. |

## License compatibility notes

- **Apache 2.0 (Wachturm code) ↔ GPLv2 (Wazuh, Suricata, MariaDB):** Apache 2.0 is one-way compatible with GPLv3+, and these GPLv2 components are used as standalone processes, so no compatibility issue arises in Wachturm's orchestration model.
- **Apache 2.0 (Wachturm code) ↔ AGPLv3 (Cortex, Shuffle, MISP):** Same — these are standalone processes, accessed over their network APIs. Wachturm's code is not a derivative work.
- **Apache 2.0 (Wachturm code) ↔ LGPL3 (DFIR-IRIS):** Same.
- **CC BY-SA 4.0 (Wachturm scenarios) ↔ everything else:** Scenarios are data, not code. CC BY-SA 4.0 applies only to the scenario content (YAML specs, briefs, instructor docs).

If you fork Wachturm and make modifications, your modifications to Wachturm's own code are governed by Apache 2.0 and your modifications to scenarios are governed by CC BY-SA 4.0. The licenses of the third-party components above continue to apply to those components.

## What this means for you

- **Running Wachturm locally for learning:** No license obligations beyond using each component as designed.
- **Forking Wachturm to add scenarios or features:** Your modifications to Wachturm's own code are Apache 2.0; you must preserve copyright notices. Your scenario additions are CC BY-SA 4.0; you must attribute and share-alike.
- **Distributing modified third-party components:** If you modify Wazuh, Suricata, IRIS, Cortex, Shuffle, MISP, or other dependencies and distribute those modifications, you are bound by their respective licenses (GPLv2, AGPLv3, LGPL3). Wachturm itself doesn't redistribute these — we pull official images at runtime — so this responsibility falls on you only if you fork the dependencies themselves.
- **Operating Wachturm as a service for others (e.g., a hosted training platform):** AGPLv3 components (Cortex, Shuffle, MISP) require you to provide source code of any modifications you made to those components to your users. Wachturm's own code (Apache 2.0) does not impose this requirement.

## Reporting

If you believe Wachturm is violating any third-party license, please open an issue immediately. License compliance is a hard requirement; we will fix violations the same day they are reported.
