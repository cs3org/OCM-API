# Where spec text, code, and stacks disagree

Permalinks are listed in [`metadata.md`](metadata.md) (OCM-API, reva, Nextcloud).

I keep two things separate on purpose. [`ocis-reva.md`](../ocis-reva.md) describes owncloud/ocis and owncloud/reva at the commits I inspected: how the OCM service is wired, what the `/ocm/notifications` handler expects, and what still looked rough. The JSON examples in this folder use [cs3org/reva](https://github.com/cs3org/reva) permalinks because that is the tree the links in this repo point at. The same commit hash often appears on owncloud/reva when both forks carry the same revision. The split between these files is by topic (product wiring versus example JSON), not a claim about which fork is authoritative.

## When servers do not match each other

This section is informal notes from comparing implementations. It is not a complete interoperability matrix.

- Reva `notify` emits `SHARE_CHANGE_PERMISSION`. Nextcloud Files uses `RESHARE_CHANGE_PERMISSION` on the file path ([`matrix-notification-types.md`](../matrix-notification-types.md) section 1). The OpenAPI [`notificationType` MAY list](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/spec.yaml#L768-L777) lists `RESHARE_CHANGE_PERMISSION`. Interoperation requires a mapping if peers compare `notificationType` as a plain string.
- Nextcloud Files uses `sharedSecret` heavily in outbound file traffic (matrix section 1). The oCIS / reva receive path in [`ocis-reva.md`](../ocis-reva.md) expects `grantee` and, for permission changes, `notification.protocol`. The remote has to send what the receiver implements, which is not always the same as the draft text.
- Nextcloud Files sends and receives many `notificationType` values. The reva `notify` switch I pinned only implements `SHARE_UNSHARED` and `SHARE_CHANGE_PERMISSION` ([`reva-ocm-notifications.md`](reva-ocm-notifications.md), matrix section 3). A type string that exists only on the Nextcloud side can fail on reva.
- On the Nextcloud Files receive path, `RESHARE_CHANGE_PERMISSION` calls `updateResharePermissions`, which throws (`HintException`, updating reshares not allowed) in the tree I read. Other layers may still report success. See matrix section 1.1 and [`nextcloud-server.md`](../nextcloud-server.md).
- [CERN / cs3org reva](../cernbox-reva.md) and [openCloud / reva](../opencloud-reva.md) were different in my pass: the route existed, but typed handling was minimal or absent. Check those files before assuming parity with Nextcloud or a full ocmd receiver.

The per-codebase map lives in [`matrix-notification-types.md`](../matrix-notification-types.md) and the platform files under `research/`.

## Reva `protocol` on notifications

Share Creation defines `protocol` as one JSON **object**, not an array:

- [`spec.yaml` `protocol`](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/spec.yaml#L555-L572)
- [`IETF-RFC.md` Share Creation](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/IETF-RFC.md#L873-L897)

For permission-change notifications:

- [`NewNotification`](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/spec.yaml#L761-L801) does not document `notification.protocol`.
- [`IETF-RFC.md` Share Updating](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/IETF-RFC.md#L1293-L1301): `RESHARE_CHANGE_PERMISSION` payload and side effects are out of scope.
- [`notificationType` MAY list](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/spec.yaml#L768-L777): `RESHARE_CHANGE_PERMISSION`; reva sends `SHARE_CHANGE_PERMISSION`.

Reva fills `notification.protocol` with the same object encoding as Share Creation via [`protocols.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/internal/http/services/ocmd/protocols.go) (reva pin in `metadata.md`).

## Nextcloud envelope

Nextcloud keeps the top-level fields stable (`notificationType`, `resourceType`, `providerId`, nested `notification`). Files and Talk diverge inside `notification`. The builder is [`CloudFederationNotification.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/lib/private/Federation/CloudFederationNotification.php) `setMessage`.

## Talk `MESSAGE_POSTED`

`messageData` / `unreadInfo` track the federated chat sync story; keys move with Spreed. I used [`BackendNotifier.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/BackendNotifier.php) `sendMessageUpdate` at the Spreed pin.
