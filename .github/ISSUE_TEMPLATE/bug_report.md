---
name: Bug report
about: Something in Wachturm isn't working as documented
title: "[BUG] <short summary>"
labels: bug, needs-triage
assignees: ''
---

## Bug report

### What happened

<!-- Be specific. What did you do, what happened, what did you expect to happen. -->

### Steps to reproduce

```bash
# the exact commands you ran, in order
```

### What you expected

<!-- Reference the doc or behavior you expected, if applicable. -->

### What actually happened

<!-- Include error messages, screenshots, log lines. -->

### Environment

- OS: <!-- macOS 14 / Ubuntu 22.04 / WSL2 / etc. -->
- Docker version: <!-- `docker --version` -->
- Compose version: <!-- `docker compose version` -->
- Available RAM: <!-- e.g., 16 GB -->
- Available disk: <!-- e.g., 60 GB free -->
- Wachturm commit: <!-- `git rev-parse HEAD` -->

### Compose profile

<!-- Which profile(s) you brought up: core / casemgmt / soar / intel -->

### Affected services

<!-- Which containers, if you know. e.g., wazuh-manager, iris-app -->

### Logs

<!--
Paste relevant logs in code blocks. Run `make logs SERVICE=<name>` for the
affected service. Don't paste 500 lines — find the relevant section.
-->

```
<paste logs here>
```

### Anything else

<!-- Anything that might help diagnose. Skip if not. -->

---

### Before opening this issue

- [ ] I've checked README.md and docs/student/ for documented troubleshooting
- [ ] I've run `make doctor` and the output looked clean
- [ ] I've run `make reset` and retried (this fixes 30% of issues)
- [ ] I'm running a recent commit, not a months-old fork
