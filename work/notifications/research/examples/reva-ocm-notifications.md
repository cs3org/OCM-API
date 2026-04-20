# Reva: wire JSON from `notify`

Commit is in `metadata.md` under reva. Permalinks use [cs3org/reva](https://github.com/cs3org/reva) at that hash (same tree I inspected).

The `notify` switch in [`ocmshareprovider.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/internal/grpc/services/ocmshareprovider/ocmshareprovider.go) emits the two cases below; other notification types hit the default branch and error out. I cross-checked the client side with [`notify_payload_test.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/pkg/ocm/client/notify_payload_test.go). [`client.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/pkg/ocm/client/client.go) sends them through `NotifyRemote` to `{remote_ocm_endpoint}/notifications`. For the Go structs, see [`payload.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/pkg/ocm/client/payload.go).

Each fenced `json` section is the raw HTTP body and nothing else.

---

## SHARE_UNSHARED

```json
{
  "notificationType": "SHARE_UNSHARED",
  "resourceType": "file",
  "providerId": "<OCM_SHARE_OPAQUE_ID>",
  "notification": {
    "grantee": "<GRANTEE_OPAQUE_USER_ID>"
  }
}
```

---

## SHARE_CHANGE_PERMISSION

OCM-API pin for the links below is in [`metadata.md`](metadata.md).

### Spec cross-check

Share Creation defines `protocol` as one JSON object (`type: object`), not an array:

- [`spec.yaml` `protocol`](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/spec.yaml#L555-L572)
- [`IETF-RFC.md` Share Creation](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/IETF-RFC.md#L873-L897)

For `POST /notifications` I did not find a schema that lists inner keys on `notification`:

- [`NewNotification`](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/spec.yaml#L761-L801)
- [`IETF-RFC.md` `/notifications` fields](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/IETF-RFC.md#L1059-L1070)
- [`IETF-RFC.md` Share Updating](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/IETF-RFC.md#L1293-L1301) leaves the `RESHARE_CHANGE_PERMISSION` payload out of scope
- [`notificationType` MAY list](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/spec.yaml#L768-L777) includes `RESHARE_CHANGE_PERMISSION`; the JSON below uses reva's `SHARE_CHANGE_PERMISSION`

The remaining gap is the inner `notification` shape on this path and the type string, not whether `protocol` is an object. See [`discrepancies.md`](discrepancies.md).

### Reva

`notification.protocol` is produced by [`Protocols.MarshalJSON`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/internal/http/services/ocmd/protocols.go), using the same object model as Share Creation `protocol`.

```json
{
  "notificationType": "SHARE_CHANGE_PERMISSION",
  "resourceType": "file",
  "providerId": "<OCM_SHARE_OPAQUE_ID>",
  "notification": {
    "grantee": "<GRANTEE_OPAQUE_USER_ID>",
    "protocol": {
      "name": "multi",
      "options": {},
      "webdav": {
        "sharedSecret": "<REDACTED>",
        "permissions": ["read", "write"],
        "uri": "https://example.invalid/remote.php/dav/ocm/token"
      }
    }
  }
}
```
