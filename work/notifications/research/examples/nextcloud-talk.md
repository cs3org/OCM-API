# Nextcloud Talk: wire JSON for notifications

The Spreed commit I used is in `metadata.md` under Nextcloud Spreed. On the server side the envelope still goes through [`CloudFederationNotification`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/lib/private/Federation/CloudFederationNotification.php) at the server commit listed there. The fenced blocks are the JSON body as it goes on the wire.

I traced the send path through [`BackendNotifier.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/BackendNotifier.php); all of these are outbound toward the remote peer unless I say otherwise.

---

## SHARE_ACCEPTED

Outbound when the remote side accepts: `sendShareAccepted`.

```json
{
  "notificationType": "SHARE_ACCEPTED",
  "resourceType": "talk-room",
  "providerId": "<REMOTE_ATTENDEE_ID>",
  "notification": {
    "remoteServerUrl": "<HTTPS_BASE_URL_OF_SENDER>",
    "sharedSecret": "<PLACEHOLDER_ACCESS_TOKEN>",
    "message": "Recipient accepted the share",
    "displayName": "<DISPLAY_NAME>",
    "cloudId": "<USER>@<HOST>"
  }
}
```

---

## SHARE_DECLINED

Outbound when the remote side declines: `sendShareDeclined`.

```json
{
  "notificationType": "SHARE_DECLINED",
  "resourceType": "talk-room",
  "providerId": "<REMOTE_ATTENDEE_ID>",
  "notification": {
    "remoteServerUrl": "<HTTPS_BASE_URL_OF_SENDER>",
    "sharedSecret": "<PLACEHOLDER_ACCESS_TOKEN>",
    "message": "Recipient declined the share"
  }
}
```

---

## SHARE_UNSHARED

Outbound unshare: `sendRemoteUnShare`.

```json
{
  "notificationType": "SHARE_UNSHARED",
  "resourceType": "talk-room",
  "providerId": "<LOCAL_ATTENDEE_ID>",
  "notification": {
    "remoteServerUrl": "<HTTPS_BASE_URL_OF_SENDER>",
    "sharedSecret": "<PLACEHOLDER_ACCESS_TOKEN>",
    "message": "This room has been unshared"
  }
}
```

---

## PARTICIPANT_MODIFIED

Participant field changes go through `sendParticipantModifiedUpdate`.

```json
{
  "notificationType": "PARTICIPANT_MODIFIED",
  "resourceType": "talk-room",
  "providerId": "<LOCAL_ATTENDEE_ID>",
  "notification": {
    "remoteServerUrl": "<HTTPS_BASE_URL_OF_SENDER>",
    "sharedSecret": "<PLACEHOLDER_ACCESS_TOKEN>",
    "remoteToken": "<ROOM_TOKEN>",
    "changedProperty": "<STRING>",
    "newValue": "<STRING_OR_INT>",
    "oldValue": "<STRING_OR_INT_OR_NULL>"
  }
}
```

---

## ROOM_MODIFIED (basic room property change)

Plain room metadata changes use `sendRoomModifiedUpdate`.

```json
{
  "notificationType": "ROOM_MODIFIED",
  "resourceType": "talk-room",
  "providerId": "<LOCAL_ATTENDEE_ID>",
  "notification": {
    "remoteServerUrl": "<HTTPS_BASE_URL_OF_SENDER>",
    "sharedSecret": "<PLACEHOLDER_ACCESS_TOKEN>",
    "remoteToken": "<ROOM_TOKEN>",
    "changedProperty": "<STRING>",
    "newValue": "<VALUE>",
    "oldValue": "<VALUE>"
  }
}
```

---

## ROOM_MODIFIED (call started variant)

`sendCallStarted` covers the call-start variant of `ROOM_MODIFIED`.

```json
{
  "notificationType": "ROOM_MODIFIED",
  "resourceType": "talk-room",
  "providerId": "<LOCAL_ATTENDEE_ID>",
  "notification": {
    "remoteServerUrl": "<HTTPS_BASE_URL_OF_SENDER>",
    "sharedSecret": "<PLACEHOLDER_ACCESS_TOKEN>",
    "remoteToken": "<ROOM_TOKEN>",
    "changedProperty": "<STRING>",
    "newValue": "<UNIX_TIMESTAMP>",
    "oldValue": null,
    "callFlag": 0,
    "details": {}
  }
}
```

---

## ROOM_MODIFIED (lobby variant)

`sendRoomModifiedLobbyUpdate` covers the lobby/timer branch of `ROOM_MODIFIED`.

```json
{
  "notificationType": "ROOM_MODIFIED",
  "resourceType": "talk-room",
  "providerId": "<LOCAL_ATTENDEE_ID>",
  "notification": {
    "remoteServerUrl": "<HTTPS_BASE_URL_OF_SENDER>",
    "sharedSecret": "<PLACEHOLDER_ACCESS_TOKEN>",
    "remoteToken": "<ROOM_TOKEN>",
    "changedProperty": "<STRING>",
    "newValue": 0,
    "oldValue": 0,
    "dateTime": "",
    "timerReached": false
  }
}
```

---

## MESSAGE_POSTED

[`MessageSentListener.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/Proxy/TalkV1/Notifier/MessageSentListener.php) ends up calling `sendMessageUpdate` on [`BackendNotifier.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/BackendNotifier.php). The exact fields inside `messageData` and `unreadInfo` will move between Spreed releases; this block matches what I read at the pinned commit.

```json
{
  "notificationType": "MESSAGE_POSTED",
  "resourceType": "talk-room",
  "providerId": "<LOCAL_ATTENDEE_ID>",
  "notification": {
    "remoteServerUrl": "<HTTPS_BASE_URL_OF_SENDER>",
    "sharedSecret": "<PLACEHOLDER_ACCESS_TOKEN>",
    "remoteToken": "<ROOM_TOKEN>",
    "messageData": {
      "remoteMessageId": 0,
      "actorType": "users",
      "actorId": "<id>",
      "actorDisplayName": "<name>",
      "messageType": "comment",
      "systemMessage": "",
      "expirationDatetime": "",
      "message": "<text>",
      "messageParameter": "[]",
      "creationDatetime": "<ISO8601>",
      "metaData": ""
    },
    "unreadInfo": {
      "unreadMessages": 0,
      "unreadMention": false,
      "unreadMentionDirect": false,
      "lastReadMessage": 0
    }
  }
}
```
