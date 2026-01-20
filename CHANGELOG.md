# Changelog

## [1.3.0] - 2026-01-20 - Micke Nordin <kano@sunet.se>

* First edition of the draft after IETF Working Group adoption.
* Introduced functions, roles, and object models to the specification.
* Added support for SSH as a share access method.
* Introduced `accessType` property in shares and removed the datatx
  "protocol" in favor of a cleaner access model.
* Improved resource access description with token exchange, and
  specified request payload format for the `/token` endpoint.
* Added RFC 9421 HTTP Message Signatures support via `http-sig`
  capability and RFC 7515 (JWS) compliant JWKS and prescribed use of
  JWS for the Directory Service.
* Updated and homogenized capabilities across the specification.
* Added JSContact extension to IANA Considerations.
* Changed example domain to use cloud.example.org per RFC 2606.

## [1.2.2] - 2025-10-21 - Giuseppe Lo Presti <lopresti@cern.ch>

* Further improvements and clarifications in the spec, prior to
  handing over to the IETF.
* Introduced concept of Invite string for the Invite flow.

## [1.2.1] - 2025-07-17 - Giuseppe Lo Presti <lopresti@cern.ch>

* Overall review of the spec in the ongoing quest to improve clarity
  and consistency, without altering the semantic of the API.
* Introduced concept of a Directory Service with a Where-Are-You-From
  page capability and an Invite Accept Dialog property to complement
  the Invite flow. Correspondingly, the Discovery endpoint has been
  extended and its description improved.

## [1.2.0] - 2024-11-20 - Michiel B. de Jong <michiel@pondersource.com>

* Rephrased and improved the whole protocol description text
  in order to conform to the IETF Internet Draft style.
* Updated the API specification to OpenAPI 3.0.
* Added a `/.well-known` endpoint for discovery, to replace
  the legacy `/ocm-provider` endpoint in a future release, and
  extended the properties and capabilities each implementation
  can expose.
* Introduced a concept of `requirements` in new shares, which indicate
  that a recipient of a share MUST fulfill some capabilities in order
  to access the share.
* Introduced several mechanisms to improve security:
  * Support for Multi-Factor Authentication.
  * Support for signing requests.
  * Support for OAuth-style exchanges, via a new `/token` endpoint.
  * Clarified access methods to remote shares, and deprecated
    less secure ones.
* Extended the `/notifications` endpoint.

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

