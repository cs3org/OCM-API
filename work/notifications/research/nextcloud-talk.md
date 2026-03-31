# Nextcloud Talk Research

Inspected repo: `https://github.com/nextcloud/spreed`
Inspected source commit:
[`76fd45d40827f76619942c9cd0a3323188dc6e42`](https://github.com/nextcloud/spreed/tree/76fd45d40827f76619942c9cd0a3323188dc6e42)

In this inspection, Nextcloud Talk changes the shape of the problem. It does
not create a separate notification transport. Instead, it reuses core
Nextcloud OCM and shows that `/notifications` is already being used as a
resource-event channel, not only as a file-share callback API.

## What I Saw

Talk adds the `talk-room` resource type and uses notifications for room-state
changes, participant updates, and message propagation after the initial share
bootstrap. The initial invite is still an OCM share, but the later lifecycle
depends much more on notifications.

That matters because it becomes much harder to describe `/notifications` as a
flat list of file-share types once a real deployed app is already using it for
resource-specific event traffic.

The receive side still uses shared-secret-based binding, so Talk does not move
fully away from the broader Nextcloud model. But the payloads are much richer
and clearly resource-specific. The endpoint carries room details, participant
details, and message details, not only file-share status changes.

Talk also uses the notification response in an important way. In particular,
`RESOURCE_NOT_FOUND` is not only a log message or an example string. It can
change retry behavior and lead Talk to treat a remote participant or share as
gone.

## Notification Types And Code Paths

- Talk registers its cloud federation provider in
  [`Application.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/AppInfo/Application.php).
- Talk advertises `talk-room` and the `talk-v1` follow-up path through
  [`ResourceTypeRegisterListener.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/Proxy/TalkV1/Listener/ResourceTypeRegisterListener.php).
- `SHARE_ACCEPTED` and `SHARE_DECLINED` are sent back to the host when an
  invited user accepts or declines a room share through
  [`FederationManager.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/FederationManager.php)
  and
  [`BackendNotifier.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/BackendNotifier.php).
- The main inbound receiver lives in
  [`CloudFederationProviderTalk.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/CloudFederationProviderTalk.php).
  In this pass it receives `SHARE_ACCEPTED`, `SHARE_DECLINED`,
  `SHARE_UNSHARED`, `PARTICIPANT_MODIFIED`, `ROOM_MODIFIED`, and
  `MESSAGE_POSTED`.
- In that provider, `SHARE_ACCEPTED` updates the stored host-side federated
  attendee row, while `SHARE_DECLINED` removes the pending federated attendee
  from the host room. See
  [`CloudFederationProviderTalk.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/CloudFederationProviderTalk.php).
- `SHARE_UNSHARED` is handled on the invited side. It deletes the stored
  invitation and removes the local participant if the room had already been
  accepted. See
  [`CloudFederationProviderTalk.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/CloudFederationProviderTalk.php).
- `PARTICIPANT_MODIFIED` is intentionally narrow here. In this pass the
  receiver only acts on permission changes and `RESEND_CALL`. See
  [`CloudFederationProviderTalk.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/CloudFederationProviderTalk.php).
- `ROOM_MODIFIED` is broader. It updates room state such as room name,
  description, type, avatar, lobby, permissions, read-only flags, expiration,
  pinned state, recording flags, and SIP state. See
  [`CloudFederationProviderTalk.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/CloudFederationProviderTalk.php).
- `MESSAGE_POSTED` carries a full message snapshot plus unread counters. It is
  used for new messages, and it also covers edit and delete cases. See
  [`CloudFederationProviderTalk.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/CloudFederationProviderTalk.php).
- On the sender side, `SHARE_UNSHARED` is sent from
  [`BeforeRoomDeletedListener.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/Proxy/TalkV1/Notifier/BeforeRoomDeletedListener.php),
  `PARTICIPANT_MODIFIED` from
  [`ParticipantModifiedListener.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/Proxy/TalkV1/Notifier/ParticipantModifiedListener.php),
  `ROOM_MODIFIED` from
  [`RoomModifiedListener.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/Proxy/TalkV1/Notifier/RoomModifiedListener.php),
  and `MESSAGE_POSTED` from
  [`MessageSentListener.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/Proxy/TalkV1/Notifier/MessageSentListener.php).
- The response body from `/notifications` is part of Talk's state machine in
  [`BackendNotifier.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/Federation/BackendNotifier.php).
  `RESOURCE_NOT_FOUND` is treated as a real remote state signal, not only as a
  log message.
- Failed Talk notifications are retried from `talk_retry_ocm` by
  [`RetryNotificationsJob.php`](https://github.com/nextcloud/spreed/blob/76fd45d40827f76619942c9cd0a3323188dc6e42/lib/BackgroundJob/RetryNotificationsJob.php).

## What This Shows

This path makes it clear that the spec needs room for extensions. Even if the
first shared file profile stays small, the current behavior already shows
resource-specific profiles around the common envelope.

It also shows that a notification path may need more than one follow-up
channel. After OCM bootstrap, it advertises and uses `talk-v1` as a companion
path for room and chat behavior. That does not replace `/notifications`, but it
does show that discovery and extension language need more detail than the
current draft gives them.

## Limits

Talk supports the idea of an extension model, but it is not a reason to force
all of Talk's payload details into the common notification contract. Those
details belong to a resource-specific profile if they belong in the spec at
all.

It is also not a reason to treat the current Talk behavior as fully settled.
The code surface is large, the retry logic is detailed, and the behavior still
needs careful reading. So this is better read as "evidence that the endpoint is
already broader than the RFC says" than as "the final extension template is
already clear."
