"""Wachturm Phase-2 integrations (DFIR-IRIS, Cortex).

Each module here bridges the Phase-1 detection stack to the case-
management tools. They follow the same conventions as ``wachturm.cli``:
the unavoidable IO boundary (``docker exec`` into a container, HTTP to a
tool's API) is taken via an injected callable / transport so the logic
is unit-testable without a running lab.
"""
