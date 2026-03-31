# Nextcloud Server Research

Inspected repo: `https://github.com/nextcloud/server.git`
Inspected source commit:
[`f8cc0adefb0703bc5d816b328f2c1d97a40f7e04`](https://github.com/nextcloud/server/tree/f8cc0adefb0703bc5d816b328f2c1d97a40f7e04)

In this inspection, Nextcloud server has a real file-oriented notification
path.

## What I Saw

Nextcloud has a real receive path for `/ocm/notifications`, not only a route.
It accepts known notification types, binds them to existing local share state,
and applies side effects. This gives one clear example of receiver behavior in
deployed code.

For file notifications, `notification.sharedSecret` is the main binding input.
When signatures are available, the server also ties the request back to the
expected remote identity. In other words, Nextcloud already behaves as if
transport authentication and object binding are related but still separate.

The implementation also shows that success bodies can matter. In particular,
`REQUEST_RESHARE` can return response data instead of behaving like a generic
empty acknowledgment.

Another important point is scope: Nextcloud is not using `/notifications` only
for file-share accept and decline flows. The same transport is also used for
calendar sync, which is one reason the spec discussion is now larger than a
small file-share patch.

## Notification Types And Code Paths

- `SHARE_ACCEPTED` and `SHARE_DECLINED` are sent when a remote share is
  accepted or declined through
  [`External/Manager.php`](https://github.com/nextcloud/server/blob/f8cc0adefb0703bc5d816b328f2c1d97a40f7e04/apps/files_sharing/lib/External/Manager.php).
- `REQUEST_RESHARE`, `SHARE_UNSHARED`, and `RESHARE_UNDO` are sent from
  [`Notifications.php`](https://github.com/nextcloud/server/blob/f8cc0adefb0703bc5d816b328f2c1d97a40f7e04/apps/federatedfilesharing/lib/Notifications.php).
- Initial federated file delivery does not use `/notifications`. It still goes
  through `/shares` from
  [`Notifications.php`](https://github.com/nextcloud/server/blob/f8cc0adefb0703bc5d816b328f2c1d97a40f7e04/apps/federatedfilesharing/lib/Notifications.php).
- The main file receiver lives in
  [`CloudFederationProviderFiles.php`](https://github.com/nextcloud/server/blob/f8cc0adefb0703bc5d816b328f2c1d97a40f7e04/apps/federatedfilesharing/lib/OCM/CloudFederationProviderFiles.php).
  In this pass it receives `SHARE_ACCEPTED`, `SHARE_DECLINED`,
  `SHARE_UNSHARED`, `REQUEST_RESHARE`, `RESHARE_UNDO`, and
  `RESHARE_CHANGE_PERMISSION`.
- In that provider, `SHARE_ACCEPTED` and `SHARE_DECLINED` update earlier share
  state, `SHARE_UNSHARED` removes an external share if one is found,
  `REQUEST_RESHARE` can return `token` and `providerId`, and `RESHARE_UNDO`
  undoes an earlier reshare. See
  [`CloudFederationProviderFiles.php`](https://github.com/nextcloud/server/blob/f8cc0adefb0703bc5d816b328f2c1d97a40f7e04/apps/federatedfilesharing/lib/OCM/CloudFederationProviderFiles.php).
- `RESHARE_CHANGE_PERMISSION` is present in the receive surface, but the same
  provider currently throws `HintException("Updating reshares not allowed")`,
  so this type is not working as a real OCM permission-update path here. See
  [`CloudFederationProviderFiles.php`](https://github.com/nextcloud/server/blob/f8cc0adefb0703bc5d816b328f2c1d97a40f7e04/apps/federatedfilesharing/lib/OCM/CloudFederationProviderFiles.php).
- `SYNC_CALENDAR` is sent from
  [`CalendarFederationNotifier.php`](https://github.com/nextcloud/server/blob/f8cc0adefb0703bc5d816b328f2c1d97a40f7e04/apps/dav/lib/CalDAV/Federation/CalendarFederationNotifier.php)
  and received by
  [`CalendarFederationProvider.php`](https://github.com/nextcloud/server/blob/f8cc0adefb0703bc5d816b328f2c1d97a40f7e04/apps/dav/lib/CalDAV/Federation/CalendarFederationProvider.php).
  Unknown calendar notification types return an empty result there.
- The canonical `/ocm/notifications` controller is
  [`cloud_federation_api/lib/Controller/RequestHandlerController.php`](https://github.com/nextcloud/server/blob/f8cc0adefb0703bc5d816b328f2c1d97a40f7e04/apps/cloud_federation_api/lib/Controller/RequestHandlerController.php).
- The older OCS controller still used by some accept, decline, and unshare
  flows is
  [`federatedfilesharing/lib/Controller/RequestHandlerController.php`](https://github.com/nextcloud/server/blob/f8cc0adefb0703bc5d816b328f2c1d97a40f7e04/apps/federatedfilesharing/lib/Controller/RequestHandlerController.php).

## Limits

Even though Nextcloud is the richest implementation in this inspection, it is
not a simple "copy this into the spec" template.

The behavior is split across several layers. There is a canonical OCM route,
but there are also older OCS fallbacks and app-specific paths. Those paths do
not all return the same status codes or expose the same failure behavior. So
it is easy to describe the implementation as more uniform than it really is.

The resource-type story is also uneven. `file` is clearly present in the common
path. `folder` appears in internal registration, but it does not look settled
enough to treat as a shared starting point yet. `calendar` is real in code, but it
is not as clearly represented in default discovery output as one might expect.

Permission change is another example that needs care. The type appears in the
dispatch surface, but the current file path does not look like a clear OCM path
that another stack could safely target today.

There are also places where a successful response does not necessarily mean a
strong real outcome. For example, some paths can log and continue, and some
unshare handling can become a no-op when no matching local row is found.

## What This Shows

For the spec discussion, Nextcloud server shows that `/notifications` can have
meaningful receiver behavior in deployed code. It also shows that the endpoint
is not only theoretical and that state-transition language is part of the
current implementation picture.

At the same time, this inspection also shows why the current Nextcloud behavior
should not be read as one direct template for the full spec text. Some parts
look broadly reusable, and some parts still look local to this implementation
or to specific apps.
