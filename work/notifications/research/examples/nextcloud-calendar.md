# Nextcloud Calendar: wire JSON for notifications

Use the Nextcloud server commit from `metadata.md`. This file only documents one notification type.

---

## SYNC_CALENDAR

The notifier is [`CalendarFederationNotifier.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/dav/lib/CalDAV/Federation/CalendarFederationNotifier.php) and the traffic is outbound. `providerId` is the fixed string `calendar` because that is what [`CalendarFederationProvider.php`](https://github.com/nextcloud/server/blob/f5faddaf31ebabd6f722e7b29f35d1f28c947259/apps/dav/lib/CalDAV/Federation/CalendarFederationProvider.php) exposes as `PROVIDER_ID`.

```json
{
  "notificationType": "SYNC_CALENDAR",
  "resourceType": "calendar",
  "providerId": "calendar",
  "notification": {
    "sharedSecret": "<PLACEHOLDER_TOKEN>",
    "shareWith": "<CLOUD_ID_STRING>",
    "calendarUrl": "https://<HOST>/remote.php/dav/remote-calendars/<...>"
  }
}
```
