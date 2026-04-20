# Notifications research

Research notes for `/notifications`.

- `matrix-notification-types.md` - types and where they live in code (pinned links)
- `examples/README.md` - layout of the example files
- `examples/metadata.md` - pinned commits (ownCloud reva, cs3org/reva, Nextcloud, OCM-API spec cross-check)
- `examples/nextcloud-files.md`, `examples/nextcloud-talk.md`, `examples/nextcloud-calendar.md` - wire JSON + context
- `examples/reva-ocm-notifications.md` - ownCloud reva `notify` bodies
- `examples/discrepancies.md` - spec vs code, and where stacks disagree
- `nextcloud-server.md`, `nextcloud-talk.md`, `ocis-reva.md`, `cernbox-reva.md`, `opencloud-reva.md` - per-platform notes

Notes for ocis and owncloud/reva are in `ocis-reva.md`. The example JSON under
`examples/` uses owncloud/reva permalinks, because that repo implements the
notification sender and typed payloads. Upstream cs3org/reva is tracked
separately in `cernbox-reva.md`.

Platform files list notification types and send/receive paths from code review.
