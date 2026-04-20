# CERN / cs3org reva Research

Inspected repo: `https://github.com/cs3org/reva`
Inspected source commit:
[`38515cdf789457bf0696a4c022c6652133bd0ad0`](https://github.com/cs3org/reva/tree/38515cdf789457bf0696a4c022c6652133bd0ad0)

In this inspection, this repo is mainly relevant for the gap between route
presence and notification behavior.

## What I Saw

In this inspection, the `/ocm/notifications` path can read and log payload
data, and it returns `201 Created`, but it does not look like a receiver that
interprets notification types and applies state transitions.

Outbound notification sending also does not look complete in this tree.
Discovery, by contrast, appears more developed than the notification path
itself.

This combination shows the difference between "this product has an endpoint"
and "this product implements notification behavior that another server can
depend on."

## Notification Types And Code Paths

- The inbound `/ocm/notifications` handler lives in
  [`notifications.go`](https://github.com/cs3org/reva/blob/38515cdf789457bf0696a4c022c6652133bd0ad0/internal/http/services/opencloudmesh/ocmd/notifications.go).
- In this checkout, that file does not decode typed notification requests. It
  reads the raw JSON body only for `application/json`, logs what it got, and
  returns `201 Created`.
- The code comments in
  [`notifications.go`](https://github.com/cs3org/reva/blob/38515cdf789457bf0696a4c022c6652133bd0ad0/internal/http/services/opencloudmesh/ocmd/notifications.go)
  mention `SHARE_ACCEPTED`, `SHARE_DECLINED`, `REQUEST_RESHARE`,
  `SHARE_UNSHARED`, `RESHARE_UNDO`, and `RESHARE_CHANGE_PERMISSION`, but in
  this pass those values were examples only. They were not decoded or acted on.
- Outgoing notification sending is still not wired because
  [`client.go`](https://github.com/cs3org/reva/blob/38515cdf789457bf0696a4c022c6652133bd0ad0/internal/http/services/opencloudmesh/ocmd/client.go)
  still has `NewNotification()` unimplemented.
- The route is registered in
  [`ocm.go`](https://github.com/cs3org/reva/blob/38515cdf789457bf0696a4c022c6652133bd0ad0/internal/http/services/opencloudmesh/ocmd/ocm.go)
  and `/notifications` is still listed in `Unprotected()`.

## What This Shows

This upstream line shows why the spec needs a clearer separation between route
presence and real handling. If a test or a discovery document looks only for
the existence of `/notifications`, it can easily give an incomplete picture of
cross-server behavior.

For that reason, this repo is currently more relevant as context for discovery
behavior and for understanding one part of the wider reva landscape than as a
main reference for notification behavior.
