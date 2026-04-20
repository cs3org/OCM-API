# Commits I pinned for these examples

Label: `ocm-notifications-implementation-examples`

Commits for the server, Spreed, and reva trees these notes came from. Use them when you diff the PHP or Go against the markdown and JSON in this folder.

---

## Nextcloud server (Files + Calendar)

| | |
| --- | --- |
| Repo | [nextcloud/server](https://github.com/nextcloud/server) |
| Branch | `master` |
| Commit | `f5faddaf31ebabd6f722e7b29f35d1f28c947259` |
| Version string (from `version.php` at the time) | `34.0.0 dev` |

---

## Nextcloud Spreed (Talk)

| | |
| --- | --- |
| Repo | [nextcloud/spreed](https://github.com/nextcloud/spreed) |
| Branch | `main` |
| Commit | `76fd45d40827f76619942c9cd0a3323188dc6e42` |

---

## ownCloud reva (oCIS notification path)

The JSON examples in this folder come from
[owncloud/reva](https://github.com/owncloud/reva) at the commit below. This is
the tree that implements `pkg/ocm/client`, the `notify` switch in
`ocmshareprovider.go`, and the typed `/ocm/notifications` handler used by the
oCIS-related notes.

| | |
| --- | --- |
| Repo | [owncloud/reva](https://github.com/owncloud/reva) |
| Commit | `9ef2450fc1c9c711cc4e21034aa921bb2d47f34c` |
| Open on GitHub | [owncloud/reva @ that commit](https://github.com/owncloud/reva/commit/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c) |

---

## cs3org/reva (upstream contrast)

This section points to [cs3org/reva](https://github.com/cs3org/reva). I keep it
separate because the latest upstream tree does not implement the same OCM
notification sender path.
It has the route and share protocol structs, but `/notifications` is still a
stub there.

| | |
| --- | --- |
| Repo | [cs3org/reva](https://github.com/cs3org/reva) |
| Commit | `38515cdf789457bf0696a4c022c6652133bd0ad0` |
| Open on GitHub | [cs3org/reva @ that commit](https://github.com/cs3org/reva/commit/38515cdf789457bf0696a4c022c6652133bd0ad0) |

---

## OCM-API (OpenAPI and IETF draft text)

Cross-checks in `discrepancies.md` and `reva-ocm-notifications.md` use this tree.

| | |
| --- | --- |
| Repo | [cs3org/OCM-API](https://github.com/cs3org/OCM-API) |
| Commit | `6b2225e31fc4d50df16aac24a570e8263591130c` |
| Open on GitHub | [commit](https://github.com/cs3org/OCM-API/commit/6b2225e31fc4d50df16aac24a570e8263591130c) |

---

## ownCloud reva paths I keep pointing at

Same commit as in the ownCloud reva section above. Permalinks all start from `https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/`.

| What | Path |
| ---- | ---- |
| Notify client tests | [`pkg/ocm/client/notify_payload_test.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/pkg/ocm/client/notify_payload_test.go) |
| Notification payload struct | [`pkg/ocm/client/payload.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/pkg/ocm/client/payload.go) |
| `notify` in the gRPC service | [`internal/grpc/services/ocmshareprovider/ocmshareprovider.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/internal/grpc/services/ocmshareprovider/ocmshareprovider.go) (`notify`) |
| Typed receive handler | [`internal/http/services/ocmd/notifications.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/internal/http/services/ocmd/notifications.go) |
| Protocol JSON shape | [`internal/http/services/ocmd/protocols.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/internal/http/services/ocmd/protocols.go) |

---

## cs3org/reva paths I keep pointing at

Same commit as in the cs3org/reva section above. Permalinks all start from `https://github.com/cs3org/reva/blob/38515cdf789457bf0696a4c022c6652133bd0ad0/`.

| What | Path |
| ---- | ---- |
| Stub `/notifications` handler | [`internal/http/services/opencloudmesh/ocmd/notifications.go`](https://github.com/cs3org/reva/blob/38515cdf789457bf0696a4c022c6652133bd0ad0/internal/http/services/opencloudmesh/ocmd/notifications.go) |
| Router and unprotected list | [`internal/http/services/opencloudmesh/ocmd/ocm.go`](https://github.com/cs3org/reva/blob/38515cdf789457bf0696a4c022c6652133bd0ad0/internal/http/services/opencloudmesh/ocmd/ocm.go) |
| Unimplemented `NewNotification` | [`internal/http/services/opencloudmesh/ocmd/client.go`](https://github.com/cs3org/reva/blob/38515cdf789457bf0696a4c022c6652133bd0ad0/internal/http/services/opencloudmesh/ocmd/client.go) |
| Share `Protocols` encoding | [`internal/http/services/opencloudmesh/ocmd/specs.go`](https://github.com/cs3org/reva/blob/38515cdf789457bf0696a4c022c6652133bd0ad0/internal/http/services/opencloudmesh/ocmd/specs.go) |

---

When you change a pin, update the permalinks in the same change. If you move the OCM-API pin, refresh every `blob/6b2225...` link under `work/notifications/research/examples/`.
