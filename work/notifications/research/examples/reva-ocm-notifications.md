# ownCloud reva: wire JSON from `notify`

Commit is in `metadata.md` under ownCloud reva. These examples come from
[owncloud/reva](https://github.com/owncloud/reva).

The `notify` switch in [`ocmshareprovider.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/internal/grpc/services/ocmshareprovider/ocmshareprovider.go) emits the two cases below; other notification types hit the default branch and return an error. I cross-checked the client side with [`notify_payload_test.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/pkg/ocm/client/notify_payload_test.go). [`client.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/pkg/ocm/client/client.go) sends them through `NotifyRemote` to `{remote_ocm_endpoint}/notifications`. For the Go structs, see [`payload.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/pkg/ocm/client/payload.go).

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

- [`spec.yaml` `protocol`](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/spec.yaml#L555-L572)
- [`IETF-RFC.md` Share Creation](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/IETF-RFC.md#L873-L897)

For `POST /notifications` I did not find a schema that lists inner keys on `notification`:

- [`NewNotification`](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/spec.yaml#L761-L801)
- [`IETF-RFC.md` Share Acceptance `/notifications` fields](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/IETF-RFC.md#L1059-L1070)
- [`IETF-RFC.md` Share Updating](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/IETF-RFC.md#L1293-L1301) leaves the `RESHARE_CHANGE_PERMISSION` payload out of scope
- [`notificationType` MAY list](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/spec.yaml#L768-L777) includes `RESHARE_CHANGE_PERMISSION`; the JSON below uses ownCloud reva's `SHARE_CHANGE_PERMISSION`

That IETF field block is scoped to Share Acceptance Notification, not every notification type, and it marks `resourceType` optional there while OpenAPI `NewNotification` requires it. The remaining gap is the inner `notification` shape on this path and the type string, not whether `protocol` is an object. See [`discrepancies.md`](discrepancies.md).

### ownCloud reva

`notification.protocol` is produced by [`Protocols.MarshalJSON`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/internal/http/services/ocmd/protocols.go), using the same object model as Share Creation `protocol`.

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
