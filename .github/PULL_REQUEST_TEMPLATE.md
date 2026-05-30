# Pull Request

## What this changes

<!-- Brief summary. The diff shows the what; tell me the why. -->

## Related issue

<!-- e.g., Closes #42, or "No issue — small fix" -->

## Type of change

- [ ] New scenario (YAML + brief + instructor doc)
- [ ] Scenario fix or improvement
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactor / cleanup (no behavior change)
- [ ] CI / tooling change
- [ ] Other (describe):

## Pre-merge checklist

- [ ] I've read `AGENTS.md` and `CONTRIBUTING.md`
- [ ] CI is passing
- [ ] If this is a scenario: all three files present (YAML + brief + instructor) and `_taxonomy.md` updated
- [ ] If this is code: `ruff check`, `mypy --strict`, and `pytest` all pass locally
- [ ] If this is a doc change: I've matched the existing voice and audience for that doc layer
- [ ] I haven't added a new dependency without flagging it in the description
- [ ] I haven't modified the network model, security defaults, or any compose profile boundary
- [ ] This PR is one logical change; I haven't combined unrelated work

## Anything reviewers should know

<!--
- Tricky parts of the diff worth a second look
- Things you considered but didn't do
- Open questions you have
-->
