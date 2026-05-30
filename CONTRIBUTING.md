# Contributing to Wachturm

Thanks for considering a contribution. Wachturm is a learning tool that exists because students need a way to practice real Tier 1 SOC work. Every contribution — a new scenario, a fixed typo, an instructor doc improvement — makes the project more useful for the next learner.

## What contributions are welcome

In rough order of impact:

1. **New scenarios** following the v1.0+ taxonomy at `scenarios/_taxonomy.md`. This is the highest-leverage contribution.
2. **Improvements to instructor companion docs** — better "common student errors" entries, better discussion questions, better solution walkthroughs.
3. **Student curriculum improvements** — clearer explanations, better examples, additional pitfalls observed in real teaching.
4. **Bug fixes and stability improvements** to the runner, the integrations, or the Compose configuration.
5. **Tool guide expansions** as the tools' UIs evolve.
6. **Translations** of student-facing docs (German is most-wanted; other languages welcome).

What's NOT currently in scope:

- New tools beyond the locked stack. v1.0 ships Wazuh, Suricata, DFIR-IRIS, and Cortex; Shuffle and MISP are wired as roadmap profiles for v1.1+. Attack/benign activity is per-scenario scripted (ART-inspired, not the bundled ART framework). Substitutions or additions require an [`ARCHITECTURE.md`](ARCHITECTURE.md) discussion first.
- Custom UIs that wrap the existing tools. Students must interact with the real tool UIs; that's the pedagogical core.
- Cloud-deployment variants. v2+ territory.

## Before you start

1. **Learn the conventions and the safety model.** Code style and the contribution rules are summarised below (Contributing code). The non-negotiable security/network model — the three-network isolation, loopback-only exposure, no attacker egress — is documented in [`ARCHITECTURE.md`](ARCHITECTURE.md); read it before touching `docker-compose.yml`, any image, or the runner. The `make` targets are the contract: if `make check` and a scenario gate pass, your change fits the harness.
2. **Read the relevant existing material.** Authoring a scenario? Read [`skills/scenario-author/SKILL.md`](skills/scenario-author/SKILL.md) and at least one existing scenario trio. Fixing a doc? Read the surrounding docs to match voice and audience.
3. **Open an issue first** for non-trivial contributions. A scenario proposal, a feature, or anything over ~100 lines of code change should start with an issue. The issue templates at `.github/ISSUE_TEMPLATE/` cover the common cases.

## Contributing a new scenario

Scenarios are the heart of Wachturm. We have a dedicated workflow:

1. **Open a scenario proposal issue** (template: `.github/ISSUE_TEMPLATE/scenario.md`). Wait for a thumbs-up before doing the work — this prevents duplicate effort and ensures the taxonomy stays balanced.
2. **Follow the authoring skill.** `skills/scenario-author/SKILL.md` is the canonical workflow. It walks you through the three required files (YAML, brief, instructor doc), the validation steps, and the anti-patterns to avoid.
3. **Test end-to-end in a running lab.** Run `make scenario SCN=YOUR-ID`, triage it yourself, run `make score`, confirm the score reflects what you intended.
4. **Open a PR with all three files** plus an update to `scenarios/_taxonomy.md` marking the slot as `✅ DONE`.

Scenarios are licensed CC BY-SA 4.0 (see `LICENSE-content`). By submitting a scenario, you agree to release it under that license.

## Contributing code

1. **Match the house style.** Python 3.11+, `ruff` formatted, `mypy --strict`, pydantic v2 for schemas, typer for the CLI. `make check` runs the exact CI gate locally (ruff + mypy + pytest) — run it before opening a PR.
2. **Write tests** for runner logic. Integration tests against the live stack are nice but not required for every PR.
3. **Pin dependencies** properly. Don't introduce a new dependency without surfacing it in the PR description.
4. **Don't break the network model.** The three-network isolation (`wachturm-victims` / `wachturm-attack` / `wachturm-mgmt`) is a security design, not a convenience.

Code is licensed Apache 2.0 (see `LICENSE`). By submitting code, you agree to release it under that license.

## Contributing docs

- **Student docs (`docs/student/`)** are written in a teaching voice: direct, practical, examples-driven. Match the existing tone.
- **Instructor docs (`docs/instructor-guide.md`, `scenarios/*.instructor.md`)** are written peer-to-peer to other educators. Include common student errors observed in your own classrooms when possible — those are the highest-value sections.
- **Architecture and operational docs** are written for contributors and AI coding agents. Match the existing voice.

Docs are CC BY-SA 4.0.

## Pull request expectations

- **One PR, one logical change.** Don't combine a scenario addition with a runner refactor.
- **PRs against `main`.** No long-lived feature branches.
- **CI must pass.** No exceptions; if CI is wrong, fix CI first.
- **Description should explain the why,** not just the what. Reviewers can read the diff for the what.
- **Reference the issue** if one exists. `Closes #N` in the description triggers auto-close on merge.

## Review timing

This is a small project. PRs are reviewed when the maintainer has time, typically within a week. Scenarios contributed by students are reviewed faster (within a few days) when possible because the contributor likely needs the merge for portfolio or coursework.

If a PR has been open for >2 weeks without comment, ping the maintainer directly in the PR thread. Maintainers are human; sometimes things get missed.

## Code of conduct

Be kind. Be patient with newer contributors. Disagree about design without making it personal. The maintainer will adopt a formal Contributor Covenant when the project's contributor base warrants it; until then, this paragraph is the policy.

## Recognition

Contributors are listed in the repo's contributor graph and credited on release announcements. Significant scenario contributions get an explicit author credit in the scenario YAML and brief. If you contribute substantially and want a different recognition format, ask.

## Questions

Open a discussion in the GitHub Discussions tab. The `Help / Troubleshooting` and `Ideas` categories are appropriate for most questions.

For private inquiries, contact the maintainer via the email in the repo's main README.

Thanks for reading this far. Welcome.
