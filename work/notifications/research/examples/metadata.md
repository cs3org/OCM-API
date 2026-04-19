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

## Reva (notify samples)

The examples in this folder use [cs3org/reva](https://github.com/cs3org/reva)
for `blob/` links. [`ocis-reva.md`](../ocis-reva.md) is written against
[owncloud/reva](https://github.com/owncloud/reva) when the tree matched that
commit. The hash is the same in both places; only the GitHub org in the URL
changes. Line numbers can still drift between forks, so verify before you rely
on a permalink.

The hash below exists on cs3org/reva; other forks may not match line-for-line.

| | |
| --- | --- |
| Commit | `823c2f1c2593ad310f49da2f68e35b757fb49e15` |
| Branch | `main` |
| Open on GitHub | [cs3org/reva @ that commit](https://github.com/cs3org/reva/commit/823c2f1c2593ad310f49da2f68e35b757fb49e15) |

---

## OCM-API (OpenAPI and IETF draft text)

Cross-checks in `discrepancies.md` and `reva-ocm-notifications.md` use this tree.

| | |
| --- | --- |
| Repo | [cs3org/OCM-API](https://github.com/cs3org/OCM-API) |
| Commit | `2de5068e0b4755794b54670655d625bbd78615fc` |
| Open on GitHub | [commit](https://github.com/cs3org/OCM-API/commit/2de5068e0b4755794b54670655d625bbd78615fc) |

---

## Reva paths I keep pointing at

Same commit as in the previous section. Permalinks all start from `https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/`.

| What | Path |
| ---- | ---- |
| Notify client tests | [`pkg/ocm/client/notify_payload_test.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/pkg/ocm/client/notify_payload_test.go) |
| `notify` in the gRPC service | [`internal/grpc/services/ocmshareprovider/ocmshareprovider.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/internal/grpc/services/ocmshareprovider/ocmshareprovider.go) (`notify`) |
| Protocol JSON shape | [`internal/http/services/ocmd/protocols.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/internal/http/services/ocmd/protocols.go) |

---

When you change a pin, update the permalinks in the same change. If you move the OCM-API pin, refresh every `blob/2de5068...` link under `work/notifications/research/examples/`.
