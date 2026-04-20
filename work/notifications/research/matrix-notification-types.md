# Notification types matrix (what I saw in code)

Source-level map of what shows up on the logical OCM notifications endpoint (`notificationType`, `resourceType`, `providerId`, nested `notification`). Normative text stays in `IETF-RFC.md` and `spec.yaml`.

Commits and GitHub permalinks are in `research/examples/metadata.md` (Nextcloud server, Spreed, and [cs3org/reva](https://github.com/cs3org/reva) for the reva pin).

For concrete JSON bodies, see `research/examples/nextcloud-files.md`, `nextcloud-talk.md`, `nextcloud-calendar.md`, `reva-ocm-notifications.md`. Tables here stay short; the examples carry the wire format.

Placeholders in the tables are angle-bracket tokens, not real secrets.

---

## 1. Nextcloud Files (`resourceType` `file`)

### 1.1 Inbound `notificationReceived`

Inbound handling is the switch in [`CloudFederationProviderFiles.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/federatedfilesharing/lib/OCM/CloudFederationProviderFiles.php) `notificationReceived`.


| notificationType          | Handler method           | providerId semantics                                                                                   |
| ------------------------- | ------------------------ | ------------------------------------------------------------------------------------------------------ |
| SHARE_ACCEPTED            | shareAccepted            | Federated share id string `$id` (local id on receiver for `federatedShareProvider->getShareById($id)`) |
| SHARE_DECLINED            | shareDeclined            | Same                                                                                                   |
| SHARE_UNSHARED            | unshare                  | Same                                                                                                   |
| REQUEST_RESHARE           | reshareRequested         | Same                                                                                                   |
| RESHARE_UNDO              | undoReshare              | Same                                                                                                   |
| RESHARE_CHANGE_PERMISSION | updateResharePermissions | Same (handler throws `HintException`: updating reshares not allowed in inspected code path)            |


### 1.2 Outbound (emitted via OCM)

| notificationType | Primary source file                                                                                   | Inner `notification` keys (summary)                   |
| ---------------- | ----------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| REQUEST_RESHARE  | [`Notifications.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/federatedfilesharing/lib/Notifications.php)                                                     | sharedSecret, shareWith, senderId, shareType, message |
| SHARE_UNSHARED   | same                                                                                                  | sharedSecret, message                                 |
| RESHARE_UNDO     | same                                                                                                  | sharedSecret, message                                 |
| SHARE_ACCEPTED   | [`CloudFederationProviderFiles.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/federatedfilesharing/lib/OCM/CloudFederationProviderFiles.php) (re-share chain to owner remote) | sharedSecret, message                                 |
| SHARE_DECLINED   | same                                                                                                  | sharedSecret, message                                 |
| SHARE_ACCEPTED   | [`Manager.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/files_sharing/lib/External/Manager.php) (incoming external share accept)                        | sharedSecret, message                                 |
| SHARE_DECLINED   | same                                                                                                  | sharedSecret, message                                 |


Outbound `providerId` for Files: remote share identifier (`remoteId` / `getRemoteId` depending on path).

Envelope for senders: [`CloudFederationNotification.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/lib/private/Federation/CloudFederationNotification.php) method `setMessage`.

### 1.3 User OCS triggers (not OCM JSON; they cause outbound notifications)

Routes: [`routes.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/files_sharing/appinfo/routes.php). Controller: [`RemoteController.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/files_sharing/lib/Controller/RemoteController.php).

---

## 2. Nextcloud Talk (`resourceType` `talk-room`)

Constants: [`FederationManager.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/FederationManager.php).

Outbound: [`BackendNotifier.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/BackendNotifier.php) (via `sendUpdateToRemote` -> `sendCloudNotification`).

Inbound: [`CloudFederationProviderTalk.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/CloudFederationProviderTalk.php) method `notificationReceived` (`providerId` numeric string cast to int for local attendee id).


| notificationType     | Outbound methods (same file)                                                        | providerId         | Inner keys (summary)                                                            |
| -------------------- | ----------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------- |
| SHARE_ACCEPTED       | sendShareAccepted                                                                   | remote attendee id | remoteServerUrl, sharedSecret, message, displayName, cloudId                    |
| SHARE_DECLINED       | sendShareDeclined                                                                   | remote attendee id | remoteServerUrl, sharedSecret, message                                          |
| SHARE_UNSHARED       | sendRemoteUnShare                                                                   | local attendee id  | remoteServerUrl, sharedSecret, message                                          |
| PARTICIPANT_MODIFIED | sendParticipantModifiedUpdate                                                       | local attendee id  | remoteServerUrl, sharedSecret, remoteToken, changedProperty, newValue, oldValue |
| ROOM_MODIFIED        | sendRoomModifiedUpdate, sendCallStarted, sendCallEnded, sendRoomModifiedLobbyUpdate | local attendee id  | Variants add callFlag, details, dateTime, timerReached                          |
| MESSAGE_POSTED       | sendMessageUpdate                                                                   | local attendee id  | remoteServerUrl, sharedSecret, remoteToken, messageData, unreadInfo             |


`MESSAGE_POSTED` path: [`MessageSentListener.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/Proxy/TalkV1/Notifier/MessageSentListener.php) -> `sendMessageUpdate`.

---

## 3. Reva `notify` line (`resourceType` `file`)

The table below is the pinned cs3org/reva tree. For how ocis wraps that service
and what the HTTP handler expects, see [`ocis-reva.md`](ocis-reva.md).

Structs: [`payload.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/pkg/ocm/client/payload.go).

Runtime send: [`ocmshareprovider.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/internal/grpc/services/ocmshareprovider/ocmshareprovider.go) function `notify`.


| notificationType        | Sent by notify switch | Inner notification object              |
| ----------------------- | --------------------- | -------------------------------------- |
| SHARE_UNSHARED          | yes                   | grantee only (opaque user id)          |
| SHARE_CHANGE_PERMISSION | yes                   | grantee + protocol (from getProtocols) |


Other `notificationType` strings: default branch in inspected `notify` returns error (see tests in [`pkg/ocm/client`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/pkg/ocm/client/notify_payload_test.go)).

HTTP: [`client.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/pkg/ocm/client/client.go) `NotifyRemote` -> `POST` `{endpoint}/notifications`.

Pins: `metadata.md` (reva and OCM-API commits).

Permission-change: reva sends `SHARE_CHANGE_PERMISSION` and sets `notification.protocol` via [`protocols.go`](https://github.com/cs3org/reva/blob/823c2f1c2593ad310f49da2f68e35b757fb49e15/internal/http/services/ocmd/protocols.go) `Protocols.MarshalJSON`, same object model as Share Creation [`protocol`](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/spec.yaml#L555-L572).

OpenAPI [`notificationType` MAY list](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/spec.yaml#L768-L777) and IETF [Share Updating](https://github.com/cs3org/OCM-API/blob/2de5068e0b4755794b54670655d625bbd78615fc/IETF-RFC.md#L1293-L1301) use `RESHARE_CHANGE_PERMISSION`. `NewNotification` does not document inner `notification` keys. See `research/examples/discrepancies.md`.

---

## 4. Calendar (`resourceType` `calendar`) add-on

Outbound: [`CalendarFederationNotifier.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/dav/lib/CalDAV/Federation/CalendarFederationNotifier.php) method `notifySyncCalendar`.

- notificationType: `SYNC_CALENDAR` (constant `NOTIFICATION_SYNC_CALENDAR`).
- providerId: literal string `calendar` (`CalendarFederationProvider::PROVIDER_ID` in [`CalendarFederationProvider.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/dav/lib/CalDAV/Federation/CalendarFederationProvider.php)).
- Inner keys: sharedSecret, shareWith, calendarUrl.

Inbound: [`CalendarFederationProvider.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/dav/lib/CalDAV/Federation/CalendarFederationProvider.php) method `notificationReceived`.

---

## 5. Signing (high level)

Inbound: [`RequestHandlerController.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/cloud_federation_api/lib/Controller/RequestHandlerController.php) method `receiveNotification` uses signed request validation when signing is not disabled via app config.

Outbound: [`OCMDiscoveryService.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/lib/private/OCM/OCMDiscoveryService.php) `requestRemoteOcmEndpoint` (signing on outgoing requests; JSON body shape unchanged vs unsigned path).

---

## 6. Caveats

- Files `RESHARE_CHANGE_PERMISSION`: receive path throws before useful work; no working permission update in the code I read.
- Talk: needs real federation to exercise; I did not capture every type on the wire.
- Calendar: `providerId` is the fixed string `calendar`, not a numeric share id like Files.
