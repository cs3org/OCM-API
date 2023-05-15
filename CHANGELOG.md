# Changelog

## [1.1.0] - 2023-05-15 - Giuseppe Lo Presti <lopresti@cern.ch>

* Added a new `/invite-accepted` endpoint to support an invitation
  workflow in the context of the ScienceMesh.
* Officially added the `/ocm-provider` discovery endpoint, already
  in use by several implementations. Within this endpoint, clarified
  which are the minimal capabilities required to be "OCM compliant".
* Added support for multi-protocol shares, and fully specified
  the properties required for each supported protocol.
* Added a `federation` recipient share type.
* Deprecated `protocol.options` in `/shares`.

## [1.0.0] - 2020-07-01 - Bjoern Schiessle <bjoern@schiessle.org>

* First official release of the Open Cloud Mesh (OCM) protocol
  specification, to enable federated sharing and notifications.
  The supported endpoints are `/shares` and `/notifications`.

