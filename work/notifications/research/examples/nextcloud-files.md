# Nextcloud Files: wire JSON for notifications

The server commit and permalink base are in `metadata.md` under Nextcloud server. Above each fenced block I point to the PHP file; inside the fence is the POST body (`Content-Type: application/json`) and nothing else.

Placeholders are angle brackets, not real credentials.

---

## REQUEST_RESHARE

Same server commit as in `metadata.md`. Built in [`Notifications.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/federatedfilesharing/lib/Notifications.php), sent outbound to the remote peer.

```json
{
  "notificationType": "REQUEST_RESHARE",
  "resourceType": "file",
  "providerId": "<REMOTE_SHARE_ID>",
  "notification": {
    "sharedSecret": "<PLACEHOLDER_TOKEN>",
    "shareWith": "<USER>@<REMOTE_HOST>",
    "senderId": "<LOCAL_SENDER_ID>",
    "shareType": "user",
    "message": "Ask owner to reshare the file"
  }
}
```

---

## SHARE_UNSHARED (owner to recipient)

Again [`Notifications.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/federatedfilesharing/lib/Notifications.php), outbound.

```json
{
  "notificationType": "SHARE_UNSHARED",
  "resourceType": "file",
  "providerId": "<REMOTE_SHARE_ID>",
  "notification": {
    "sharedSecret": "<PLACEHOLDER_TOKEN>",
    "message": "file is no longer shared with you"
  }
}
```

---

## RESHARE_UNDO

Same [`Notifications.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/federatedfilesharing/lib/Notifications.php), still outbound.

```json
{
  "notificationType": "RESHARE_UNDO",
  "resourceType": "file",
  "providerId": "<REMOTE_SHARE_ID>",
  "notification": {
    "sharedSecret": "<PLACEHOLDER_TOKEN>",
    "message": "reshare was revoked"
  }
}
```

---

## SHARE_ACCEPTED (re-share chain toward owner)

[`CloudFederationProviderFiles.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/federatedfilesharing/lib/OCM/CloudFederationProviderFiles.php) emits this only in the re-share chain situations (owner vs sharedBy and the rest; read the file for the exact gate), and it is sent outbound like the other file notifications.

```json
{
  "notificationType": "SHARE_ACCEPTED",
  "resourceType": "file",
  "providerId": "<REMOTE_ID_FOR_OWNER>",
  "notification": {
    "sharedSecret": "<PLACEHOLDER_TOKEN>",
    "message": "Recipient accepted the re-share"
  }
}
```

---

## SHARE_DECLINED (re-share chain toward owner)

Same file and gating as the previous entry. [`CloudFederationProviderFiles.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/federatedfilesharing/lib/OCM/CloudFederationProviderFiles.php).

```json
{
  "notificationType": "SHARE_DECLINED",
  "resourceType": "file",
  "providerId": "<REMOTE_ID_FOR_OWNER>",
  "notification": {
    "sharedSecret": "<PLACEHOLDER_TOKEN>",
    "message": "Recipient declined the re-share"
  }
}
```

---

## SHARE_ACCEPTED (incoming external share)

This one is built in [`External/Manager.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/files_sharing/lib/External/Manager.php) and sent outbound.

```json
{
  "notificationType": "SHARE_ACCEPTED",
  "resourceType": "file",
  "providerId": "<REMOTE_ID_FROM_SENDER>",
  "notification": {
    "sharedSecret": "<PLACEHOLDER_TOKEN>",
    "message": "Recipient accept the share"
  }
}
```

---

## SHARE_DECLINED (incoming external share)

Same [`Manager.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/files_sharing/lib/External/Manager.php) as the previous section, also outbound.

```json
{
  "notificationType": "SHARE_DECLINED",
  "resourceType": "file",
  "providerId": "<REMOTE_ID_FROM_SENDER>",
  "notification": {
    "sharedSecret": "<PLACEHOLDER_TOKEN>",
    "message": "Recipient declined the share"
  }
}
```
