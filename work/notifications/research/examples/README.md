# OCM notification examples (wire JSON)

Each example is the HTTP JSON body for `/notifications`-style traffic: one object with `notificationType`, `resourceType`, `providerId`, and nested `notification`. Shapes come from the code paths named in each file; secrets are redacted.

Provenance sits in the markdown (repo, file, method, which side sends). The fenced `json` blocks are the wire payload; metadata keys like `label` or `emission` never belong inside them.

Commits and GitHub permalinks live in `metadata.md` (reva, Nextcloud, OCM-API spec cross-check). Links use `blob/<commit>/path` so they do not break when `main` moves.

Source first; tests where they exist (reva httptest) or the manual steps in `work/notifications/research/` otherwise. Placeholders are angle brackets or `REDACTED`.

Files, Talk, Calendar, and reva `notify` at the pinned commit. More stacks can use the same layout.

| File | What |
| ---- | ---- |
| `metadata.md` | Commits (reva, Nextcloud, OCM-API for spec links) |
| `nextcloud-files.md` | `resourceType` `file` |
| `nextcloud-talk.md` | `resourceType` `talk-room` |
| `nextcloud-calendar.md` | `resourceType` `calendar` |
| `reva-ocm-notifications.md` | reva `notify` output |
| `discrepancies.md` | Spec vs code; where stacks disagree |

PR: rebase onto the target branch, run a secret scan on touched markdown, note any OpenAPI field-name mismatch beside the example.
