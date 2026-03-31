# openCloud And reva Research

Inspected repos:

- `https://github.com/opencloud-eu/opencloud.git`
- `https://github.com/opencloud-eu/reva`

Inspected source commits:

- `opencloud`:
  [`cde52d9e9bbddc72ead0a75e1f39caf0fbd2f21e`](https://github.com/opencloud-eu/opencloud/tree/cde52d9e9bbddc72ead0a75e1f39caf0fbd2f21e)
- `opencloud-eu/reva`:
  [`68e203bfb0b550f01996ce9256308f39fe2b8261`](https://github.com/opencloud-eu/reva/tree/68e203bfb0b550f01996ce9256308f39fe2b8261)

In this inspection, the openCloud / reva path does not yet look like a full
notification implementation.

## What I Saw

The route exists, accepts payloads, and returns `201 Created`, but this
inspection did not find the kind of actual dispatch and state application that
would make it a useful cross-server reference today.

It also did not show a clear outbound notification path or a clear discovery
claim around `notifications`.

## Notification Types And Code Paths

- The notification route in this checkout lives in
  [`notifications.go`](https://github.com/opencloud-eu/reva/blob/68e203bfb0b550f01996ce9256308f39fe2b8261/internal/http/services/ocmd/notifications.go).
- In this pass, that file exposed the route, accepted and logged payloads, and
  returned `201 Created`.
- This pass did not find typed dispatch for specific notification statuses in
  [`notifications.go`](https://github.com/opencloud-eu/reva/blob/68e203bfb0b550f01996ce9256308f39fe2b8261/internal/http/services/ocmd/notifications.go).
- Discovery did not advertise `notifications` in
  [`wellknown/ocm.go`](https://github.com/opencloud-eu/reva/blob/68e203bfb0b550f01996ce9256308f39fe2b8261/internal/http/services/wellknown/ocm.go).
- This inspection also did not find a clear outbound notification client path.

## What This Shows

Even in this state, openCloud still adds one more example where route presence
can move ahead of real receiver behavior. It also keeps another future consumer
of the spec in view.
