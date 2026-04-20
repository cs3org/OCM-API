# oCIS And reva Research

I inspected owncloud/reva at the commit below. This note covers the oCIS side
of that stack: what the `/ocm/notifications` handler checks, what the outbound
client sends, and where the behavior differs from Nextcloud. The raw JSON
samples are in `research/examples/reva-ocm-notifications.md`, with
owncloud/reva permalinks at the same commit. Upstream cs3org/reva is a
different case and is reviewed separately in `cernbox-reva.md`. The
owncloud/ocis wiring references below point directly to GitHub. If you need to
compare trees across forks, see [`examples/metadata.md`](examples/metadata.md).

Inspected repos:

- `https://github.com/owncloud/ocis`
- `https://github.com/owncloud/reva`

Inspected source commits:

- `owncloud/ocis`:
  [`7234648e1485f02102a3464c8815c97a5a9db3e7`](https://github.com/owncloud/ocis/tree/7234648e1485f02102a3464c8815c97a5a9db3e7)
- `owncloud/reva`:
  [`9ef2450fc1c9c711cc4e21034aa921bb2d47f34c`](https://github.com/owncloud/reva/tree/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c)

This pair is the main non-Nextcloud contrast in this inspection. It shows a
narrower notification surface than Nextcloud and it makes different choices
about naming, binding, and discovery.

## What I Saw

The real notification behavior lives in owncloud/reva. The main `ocis` repo
mostly wires that service into the product rather than adding a second separate
implementation.

The supported file-notification surface is smaller than what we saw in
Nextcloud. In this inspection, the main receive surface was essentially
`SHARE_UNSHARED` and `SHARE_CHANGE_PERMISSION`.

The binding model is also different. Instead of leaning on
`notification.sharedSecret` the way Nextcloud does, this stack reads more like
it expects `providerId`, `grantee`, and, for permission changes, `protocol`.
This is one visible cross-server difference in the current inspection.

There is also a naming split: ownCloud / reva uses `SHARE_CHANGE_PERMISSION`,
while Nextcloud still exposes `RESHARE_CHANGE_PERMISSION`. The MAY list in
[`spec.yaml`](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/spec.yaml#L768-L777)
at the OCM-API pin in `research/examples/metadata.md` uses the `RESHARE_*`
spelling.

## Notification Types And Code Paths

- The inbound `/ocm/notifications` handler lives in
  [`notifications.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/internal/http/services/ocmd/notifications.go).
- In this inspection, that handler receives only `SHARE_UNSHARED` and
  `SHARE_CHANGE_PERMISSION`. The same path requires `notification.grantee`.
- `SHARE_UNSHARED` is the removal path for an earlier share in
  [`notifications.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/internal/http/services/ocmd/notifications.go).
- `SHARE_CHANGE_PERMISSION` is the permission-update path there. It expects
  `notification.protocol` and uses `SHARE_CHANGE_PERMISSION` instead of
  Nextcloud's `RESHARE_CHANGE_PERMISSION`. See
  [`notifications.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/internal/http/services/ocmd/notifications.go).
- I would still read the receive path a bit carefully. The top-level handler
  checks `req.Notification.Grantee` before any nil guard, and if `grantee` is
  empty it writes a bad-request response without returning immediately.
- The permission-update helper does check `req.Notification == nil ||
  req.Notification.Protocols == nil`, but that check happens a little later,
  inside `handleShareChangePermission`, after the earlier top-level access to
  `req.Notification.Grantee`.
- There is a similar point on the error path. Both helper methods can return
  `(nil, err)`, while the outer handler still calls `status.GetMessage()` on
  error. So a missing `notification.protocol` is one case to keep in mind, but
  gateway-selection or CS3 call failures can reach the same nil-status path too.
- `getNotification` can also return `(nil, nil)` for non-JSON content types, so
  that is another way to arrive at the handler with no parsed request object.
  The `validate` tags on the request structs are present, but the validator is
  commented out, so I would read the JSON examples here as happy-path evidence
  rather than as proof that every malformed request is handled cleanly.
- On the sender side,
  [`ocmshareprovider.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/internal/grpc/services/ocmshareprovider/ocmshareprovider.go)
  sends only `SHARE_UNSHARED` and `SHARE_CHANGE_PERMISSION` too.
- The outgoing notification payloads are built and sent from
  [`payload.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/pkg/ocm/client/payload.go)
  and
  [`client.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/pkg/ocm/client/client.go).
- The reva OCM service is wired into `ocis` through
  [`config.go`](https://github.com/owncloud/ocis/blob/7234648e1485f02102a3464c8815c97a5a9db3e7/services/ocm/pkg/revaconfig/config.go)
  and
  [`server.go`](https://github.com/owncloud/ocis/blob/7234648e1485f02102a3464c8815c97a5a9db3e7/services/ocm/pkg/command/server.go).
- Outgoing notifications currently hardcode `resourceType: "file"` in the
  owncloud/reva client path.

## What This Shows

This path matters because it does not look like a small variation of Nextcloud
behavior. If the spec is meant to help real cross-server use, it has to account
for why these two implementation families made different choices.

It also supports a smaller shared starting point. The overlap between the two
stacks looks more limited than the full Nextcloud notification surface.

## Limits

The current path still needs careful reading. In the inspected service, the
route is unprotected at the HTTP layer, discovery does not advertise
`notifications`, and the handler details make direct testing especially
important.

So this stack is a real contrast, but it is better treated as evidence of what
another deployed family expects than as a final answer for the spec text.
