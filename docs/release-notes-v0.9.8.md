# Wachturm v0.9.8 — Public Evaluation Release

> **Status: PUBLIC EVALUATION PRE-RELEASE** (same standing as v0.9.0).
> v0.9.8 is the v1.0 product under evaluation; **v1.0.0 stays gated** on the
> human-testing milestone and publishes as the validated "latest" release
> once that gate passes.

## What changed since v0.9.7

- **`make up-casemgmt` fails with `permission denied` on `root-ca-manager.pem`**
  (`images/wazuh-certs-generator/entrypoint-offline.sh`). The cert generator
  ran `chmod -R 500 /certificates` (removing the directory write bit) and then
  tried to create `root-ca-manager.pem` inside it. On Linux with native Docker,
  container root bypasses mode bits. On macOS via Colima/virtiofs the chmod
  propagates to the host filesystem, so the copy silently failed and
  `root-ca-manager.pem` was never written — causing Docker to try to
  auto-create it as a directory on the next run, which then failed with
  `permission denied`.

  Fixed by:
  1. Moving the `root-ca-manager.{pem,key}` copies to before the `chmod` call.
  2. Adding `chmod u+w /certificates` at the start of any re-generation so
     that existing `chmod 400` files from a prior run don't block overwriting.

## Recovering from a partial cert set

If you hit the `root-ca-manager.pem` error on a previous run you will have a
partial cert set with restrictive host permissions. Clear it before retrying:

```bash
chmod u+w config/wazuh/wazuh_indexer_ssl_certs
rm config/wazuh/wazuh_indexer_ssl_certs/*.pem \
   config/wazuh/wazuh_indexer_ssl_certs/*.key
```

Then run `make up-casemgmt` as normal — the cert generator will produce a
complete set automatically.

Everything else is identical to v0.9.7 — see
[`docs/release-notes-v0.9.0.md`](release-notes-v0.9.0.md) for the full
scope, how-to-evaluate guidance, and known limitations.
