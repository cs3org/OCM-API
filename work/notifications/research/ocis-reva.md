# oCIS And reva Research

Inspected repos:

- `https://github.com/owncloud/ocis`
- `https://github.com/owncloud/reva`

Inspected source commits:

- `owncloud/ocis`:
  [`7234648e1485f02102a3464c8815c97a5a9db3e7`](https://github.com/owncloud/ocis/tree/7234648e1485f02102a3464c8815c97a5a9db3e7)
- `owncloud/reva`:
  [`823c2f1c2593ad310f49da2f68e35b757fb49e15`](https://github.com/owncloud/reva/tree/823c2f1c2593ad310f49da2f68e35b757fb49e15)

This pair is the main non-Nextcloud contrast in this inspection. It shows a
narrower notification surface than Nextcloud and it makes different choices
about naming, binding, and discovery.

## What I Saw

The real notification behavior lives in reva. The main `ocis` repo mostly wires
that service into the product rather than adding a second separate
implementation.

The supported file-notification surface is smaller than what we saw in
Nextcloud. In this inspection, the main receive surface was essentially
`SHARE_UNSHARED` and `SHARE_CHANGE_PERMISSION`.

The binding model is also different. Instead of leaning on
`notification.sharedSecret` the way Nextcloud does, this stack reads more like
it expects `providerId`, `grantee`, and, for permission changes, `protocol`.
This is one visible cross-server difference in the current inspection.

The naming split is real too. ownCloud / reva uses `SHARE_CHANGE_PERMISSION`,
while Nextcloud still exposes `RESHARE_CHANGE_PERMISSION`.

## Notification Types And Code Paths

- The inbound `/ocm/notifications` handler lives in
  [`notifications.go`](https://github.com/owncloud/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/internal/http/services/ocmd/notifications.go).
- In this inspection, that handler receives only `SHARE_UNSHARED` and
  `SHARE_CHANGE_PERMISSION`. The same path requires `notification.grantee`.
- `SHARE_UNSHARED` is the removal path for an earlier share in
  [`notifications.go`](https://github.com/owncloud/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/internal/http/services/ocmd/notifications.go).
- `SHARE_CHANGE_PERMISSION` is the permission-update path there. It expects
  `notification.protocol` and uses `SHARE_CHANGE_PERMISSION` instead of
  Nextcloud's `RESHARE_CHANGE_PERMISSION`. See
  [`notifications.go`](https://github.com/owncloud/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/internal/http/services/ocmd/notifications.go).
- On the sender side,
  [`ocmshareprovider.go`](https://github.com/owncloud/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/internal/grpc/services/ocmshareprovider/ocmshareprovider.go)
  sends only `SHARE_UNSHARED` and `SHARE_CHANGE_PERMISSION` too.
- The outgoing notification payloads are built and sent from
  [`payload.go`](https://github.com/owncloud/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/pkg/ocm/client/payload.go)
  and
  [`client.go`](https://github.com/owncloud/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/pkg/ocm/client/client.go).
- The reva OCM service is wired into `ocis` through
  [`config.go`](https://github.com/owncloud/ocis/blob/7234648e1485f02102a3464c8815c97a5a9db3e7/services/ocm/pkg/revaconfig/config.go)
  and
  [`server.go`](https://github.com/owncloud/ocis/blob/7234648e1485f02102a3464c8815c97a5a9db3e7/services/ocm/pkg/command/server.go).
- Outgoing notifications currently hardcode `resourceType: "file"` in the reva
  client path.

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
