# config/iris/

DFIR-IRIS configuration consumed by the `casemgmt` profile.

- `case-templates/` — IRIS case templates (authentication / malware /
  network / web / generic) used by the Wazuh→IRIS integration. Authored
  in **P2-M3**. The integration creates cases by raw-field population
  first and treats templates as an enhancement, so a missing or
  API-rejected template never blocks case creation (Phase-2 risk #3).

Nothing in this directory is required for the **P2-M0** health gate; it
exists now so the layout is discoverable and git-tracked early.
