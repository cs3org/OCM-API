# Where spec text, code, and stacks disagree

Permalinks are listed in [`metadata.md`](metadata.md) (OCM-API, ownCloud reva,
cs3org/reva, Nextcloud).

I keep two things separate on purpose. [`ocis-reva.md`](../ocis-reva.md)
describes owncloud/ocis plus owncloud/reva at the commits I inspected: how the
OCM service is wired, what the `/ocm/notifications` handler expects, and what
still looked rough. The JSON examples in this folder use the same
owncloud/reva tree, because that repo actually implements the `notify` sender,
the typed payload structs, and the typed `/ocm/notifications` handler
discussed here. Upstream cs3org/reva is a separate case and is covered in
[`cernbox-reva.md`](../cernbox-reva.md).

## When servers do not match each other

This section is informal notes from comparing implementations. It is not a complete interoperability matrix.

- ownCloud reva `notify` emits `SHARE_CHANGE_PERMISSION`. Nextcloud Files uses `RESHARE_CHANGE_PERMISSION` on the file path ([`matrix-notification-types.md`](../matrix-notification-types.md) section 1). The OpenAPI [`notificationType` MAY list](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/spec.yaml#L768-L777) lists `RESHARE_CHANGE_PERMISSION`. Interoperation requires a mapping if peers compare `notificationType` as a plain string.
- Nextcloud Files uses `sharedSecret` heavily in outbound file traffic (matrix section 1). The oCIS / reva receive path in [`ocis-reva.md`](../ocis-reva.md) expects `grantee` and, for permission changes, `notification.protocol`. The remote has to send what the receiver implements, which is not always the same as the draft text.
- Nextcloud Files sends and receives many `notificationType` values. The ownCloud reva `notify` switch I pinned only implements `SHARE_UNSHARED` and `SHARE_CHANGE_PERMISSION` ([`reva-ocm-notifications.md`](reva-ocm-notifications.md), matrix section 3). A type string that exists only on the Nextcloud side can fail on reva.
- On the Nextcloud Files receive path, `RESHARE_CHANGE_PERMISSION` calls `updateResharePermissions`, which throws (`HintException`, updating reshares not allowed) in the tree I read. The canonical `/ocm/notifications` controller then returns a bad request rather than a successful update. See matrix section 1.1 and [`nextcloud-server.md`](../nextcloud-server.md).
- [CERN / cs3org reva](../cernbox-reva.md) and [openCloud / reva](../opencloud-reva.md) were different in my pass: the route existed, but typed handling was minimal or absent. Check those files before assuming parity with ownCloud reva, Nextcloud, or a full ocmd receiver.

The per-codebase map lives in [`matrix-notification-types.md`](../matrix-notification-types.md) and the platform files under `research/`.

## ownCloud reva `protocol` on notifications

Share Creation defines `protocol` as one JSON **object**, not an array:

- [`spec.yaml` `protocol`](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/spec.yaml#L555-L572)
- [`IETF-RFC.md` Share Creation](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/IETF-RFC.md#L873-L897)

For permission-change notifications:

- [`NewNotification`](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/spec.yaml#L761-L801) does not document `notification.protocol`.
- [`IETF-RFC.md` Share Acceptance fields](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/IETF-RFC.md#L1059-L1070) are scoped to Share Acceptance Notification, not a generic field list for every notification type. That same block also marks `resourceType` optional, while OpenAPI `NewNotification` requires it.
- [`IETF-RFC.md` Share Updating](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/IETF-RFC.md#L1293-L1301): `RESHARE_CHANGE_PERMISSION` payload and side effects are out of scope.
- [`notificationType` MAY list](https://github.com/cs3org/OCM-API/blob/6b2225e31fc4d50df16aac24a570e8263591130c/spec.yaml#L768-L777): `RESHARE_CHANGE_PERMISSION`; ownCloud reva sends `SHARE_CHANGE_PERMISSION`.

ownCloud reva fills `notification.protocol` with the same object encoding as
Share Creation via [`protocols.go`](https://github.com/owncloud/reva/blob/9ef2450fc1c9c711cc4e21034aa921bb2d47f34c/internal/http/services/ocmd/protocols.go) (reva pin in `metadata.md`).

## Nextcloud envelope

Nextcloud keeps the top-level fields stable (`notificationType`, `resourceType`, `providerId`, nested `notification`). Files and Talk diverge inside `notification`. The builder is [`CloudFederationNotification.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/lib/private/Federation/CloudFederationNotification.php) `setMessage`.

## Talk `MESSAGE_POSTED`

`messageData` / `unreadInfo` track the federated chat sync story; keys move with Spreed. I used [`BackendNotifier.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/BackendNotifier.php) `sendMessageUpdate` at the Spreed pin.
