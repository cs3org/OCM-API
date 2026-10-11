# OpenGeoMesh Protocol for Open Cloud Mesh

**Matthias Kraus**<sup>1</sup> 

<sup>1</sup>[OpenGeoMesh](https://OpenGeoMesh)</br>
contact: info@opengeomesh.org 

## Abstract

This document specifies the `opengeomesh` protocol for OpenCloudMesh (OCM), enabling federated sharing of individual OGC API collections between independently operated servers.

The specification defines the `ogcapi` resource type, the `opengeomesh` protocol, and the `opengeomesh-receive` capability. OCM provides share negotiation and lifecycle management, while OGC API standards define access to geospatial resources.

## 1. Introduction

OpenGeoMesh is a lightweight, standards-based protocol for federated sharing and collaboration on private geospatial data. It enables organisations and their tools to exchange and jointly use geospatial maps, for example during incidents involving emergency services.

## 2. Scope

This specification defines how individual OGC API collections are shared between federated systems. It builds on existing standards rather than defining a proprietary geospatial data model:

* **OpenCloudMesh** for discovery, share negotiation, and lifecycle management.
* **OGC API** for geospatial data access.
* **Situation Data Exchange Format (SDXF)** for optional representation of operational situation maps.

A typical sharing process consists of the following steps:

1. The Sending Server discovers the Receiving Server's capabilities and sends an OCM share containing the collection URI and access credentials.
2. The Receiving Server processes the share and notifies the recipient.
3. The recipient accepts the share through the Receiving Server.
4. The Receiving Server accesses the shared collection on behalf of the recipient, using the supplied credentials.
5. The recipient accesses the collection through an interface provided by the Receiving Server.

## 3. Standards Dependencies

### 3.1 OpenCloudMesh

[OpenCloudMesh](https://github.com/cs3org/OCM-API) provides federated discovery, share negotiation, and notifications between independently operated servers.

The minimum required OCM version is [1.3.0](https://github.com/cs3org/OCM-API/blob/v1.3.0/IETF-RFC.md).

OpenGeoMesh defines the following OCM identifiers:

* Resource Type: `ogcapi`
* Protocol: `opengeomesh`
* Receiving capability: `opengeomesh-receive`

OCM remains responsible for the underlying notification and share lifecycle mechanisms.

### 3.2 OGC API – Features

Shared collections are accessed using OGC API standards. OpenGeoMesh requires support for the following specifications:

* [OGC API – Common, Part 1: Core](https://docs.ogc.org/is/19-072/19-072.html)
* [OGC API – Common, Part 2: Collections](https://docs.ogc.org/DRAFTS/20-024.html)
* [OGC API – Features, Part 1: Core](https://docs.opengeospatial.org/is/17-069r4/17-069r4.html)

Implementations MUST support JSON representations of collection metadata and GeoJSON representations of features.

Implementations MAY support additional OGC API interfaces and building blocks, including [OGC API – Features, Part 4: Create, Replace, Update and Delete](https://docs.ogc.org/DRAFTS/20-002r1.html), for writable shares.

See the [OGC API Workshop](https://ogcapi-workshop.ogc.org/api-deep-dive/features/) for an introduction to OGC API – Features.

### 3.3 Situation Data Exchange Format (SDXF)

The [Situation Data Exchange Format (SDXF)](https://github.com/einsatzverwaltung/SituationDataXchangeFormat) is a JSON-based format for exchanging operational information between emergency management systems. It includes a specification for situation maps based on GeoJSON.

[SituationMapJson v0.3](https://github.com/einsatzverwaltung/SituationDataXchangeFormat/blob/main/SituationMapJson.md) defines properties for representing tactical symbols, affected areas, fronts, and evacuation routes. It also supports the [Mapbox SimpleStyle specification](https://github.com/mapbox/simplestyle-spec/tree/master/1.1.0) for styling GeoJSON features.

SDXF support is optional. Implementations claiming compatibility MUST conform to the applicable SDXF specification.

## 4. Protocol Concepts

### 4.1 Share Negotiation

To initiate a share, the sender provides the Sending Server with the recipient's OCM address, for example `user@receiving-server.example.org`.

The Sending Server discovers the recipient's server capabilities through:

`https://<recipient-domain>/.well-known/ocm`

The Discovery response identifies supported resource types, protocols, share types, and endpoints. See the [OCM API Discovery specification](https://github.com/cs3org/OCM-API).

OpenGeoMesh defines the `ogcapi` resource type to represent an individual OGC API collection and the `opengeomesh` protocol to provide authenticated access to it.

#### Resource Type: `ogcapi`

An `ogcapi` resource represents one individual OGC API collection, including its metadata, items, and supported subresources.

The shared URI MUST identify the collection itself, not a general collections listing or an API endpoint exposing multiple collections.

#### Protocol: `opengeomesh`

The `opengeomesh` protocol provides the URI of the shared collection and a share-specific secret. Requests to the shared resource MUST authenticate using that secret in the HTTP `Authorization: Bearer` header.

The URI MAY be absolute or relative to the `opengeomesh` base URI advertised through OCM Discovery.

An optional `service-desc` field MAY identify an OpenAPI description for the shared collection.

#### Discovery

Servers supporting OpenGeoMesh MUST advertise the `ogcapi` resource type and the applicable protocol capabilities.

A server providing shares MUST advertise `opengeomesh`. A server receiving shares MUST advertise `opengeomesh-receive`.

Example Discovery payload:
```

{ "enabled": true, "apiVersion": "1.3.0", "endPoint": "https://receiving-server.example.org", "provider": "Example Organization", "resourceTypes": \[ { "name": "ogcapi", "shareTypes": \[ "user" \], "protocols": { "opengeomesh": "/ogm/", "opengeomesh-receive": {} } } \], "capabilities": \[ "protocol-object" \], "criteria": \[ "http-request-signatures" \], "publicKey": { "keyId": "https://receiving-server.example.org/.well-known/ocm#signature", "publicKeyPem": "-----BEGIN PUBLIC KEY-----\\nREPLACE_WITH_SERVER_PUBLIC_KEY\\n-----END PUBLIC KEY-----\\n" } }

```

The example illustrates the intended capabilities. The exact representation of `opengeomesh-receive` MUST conform to the applicable OCM Discovery schema.

#### Share Payload

An OpenGeoMesh share uses the OCM `multi` protocol representation.

Example:
```

{ "name": "Incident Map", "owner": "owner@sending-server.example.org", "protocol": { "name": "multi", "opengeomesh": { "sharedSecret": "REPLACE_WITH_RANDOM_SHARE_SECRET", "uri": "collections/incidents", "service-desc": "collections/incidents/api" } }, "providerId": "incident-map-share", "resourceType": "ogcapi", "sender": "sender@sending-server.example.org", "shareType": "user", "shareWith": "recipient@receiving-server.example.org" }

```

The example omits any additional fields required by the applicable OCM notification schema.

The `uri` identifies the individual collection. If relative, it MUST be resolved against the base URI advertised for `opengeomesh` by the Sending Server.

The `sharedSecret` MUST be unpredictable and scoped to the shared resource. The optional `service-desc` identifies an OpenAPI description applicable to that collection.

### 4.2 Providing Access to a Shared Resource

The Sending Server MUST provide authenticated access to the shared collection and its supported subresources.

Requests MUST include the share credential:
```

Authorization: Bearer \<sharedSecret\>

```

The Sending Server MUST enforce the permissions associated with the share for every request. Links in OGC API responses MUST refer to resources accessible through the shared collection endpoint.

The implementation MAY delegate resource access to another service, provided that the URI and authentication behavior remain consistent with this specification.

Responses SHOULD include appropriate HTTP caching headers to reduce unnecessary transfers and server load.

### 4.3 Accessing a Received Share

The Receiving Server SHOULD provide an interface through which the recipient can access received OpenGeoMesh shares.

The Receiving Server accesses the collection using the URI and `sharedSecret` from the share. Relative URIs MUST be resolved against the Sending Server's advertised `opengeomesh` base URI.

Requests MUST use the bearer credential defined in Section 4.1. The Receiving Server MUST NOT expose the credential to the recipient.

If the Receiving Server exposes the collection through its own OGC API interface, it MUST rewrite upstream links to refer to the corresponding local resources.

The Receiving Server SHOULD respect caching headers supplied by the Sending Server, subject to authorization and revocation requirements.

### 4.4 Accepting, Declining or Deleting a Share

Share acceptance, rejection, and deletion MUST follow the applicable OCM notification procedures.

* Acceptance and rejection use the OCM Share Acceptance Notification.
* Deletion uses the `SHARE_UNSHARED` notification.

See the [OCM Share Acceptance Notification](https://datatracker.ietf.org/doc/html/draft-ietf-ocm-open-cloud-mesh-04#name-share-acceptance-notificati) and [OCM Share Deletion](https://datatracker.ietf.org/doc/html/draft-ietf-ocm-open-cloud-mesh-04#name-share-deletion).

When a share is revoked, the Sending Server MUST prevent subsequent unauthorized access. The Receiving Server MUST stop serving the share when it learns that access has been revoked.

## 5. Security Considerations

### 5.1 Transfer Encryption

All communication between OGM Servers MUST use HTTPS with certificate verification.

Share credentials MUST be protected in transit. They MUST NOT be included in URLs or exposed in logs, error messages, or client-visible responses.

### 5.2 Request Authentication

Requests that create or modify shares MUST be authenticated according to the applicable OCM specification, including its HTTP Message Signature requirements.

Public keys used to verify remote servers MUST be retrieved and validated through HTTPS as specified by OCM.

Requests to shared resources MUST use the share-specific bearer credential. Implementations MUST validate authorization for every request.

### 5.3 Network Separation

Federated sharing can cause a server to make outbound requests to arbitrary remote hosts. Incorrect URI validation or unrestricted redirects can expose internal services through server-side request forgery.

Implementations MUST validate shared resource URIs and prevent access to unauthorized internal endpoints. Credentials MUST NOT be forwarded to unauthorized origins.

Deployments SHOULD use network separation, outbound firewall rules, or destination allowlists to restrict access to internal networks.

### 5.4 Caching and Revocation

Cached resources MUST NOT be served to users who are no longer authorized to access the share.

Revocation prevents future authorized access but cannot guarantee deletion of copies already downloaded by recipients.

## 6. IANA Considerations

This document defines identifiers for use with OpenCloudMesh.

The following entries are proposed for registration in the applicable OCM registries, subject to their registration procedures.

| Registry | Identifier | Description |
|---|---|---|
| Resource Type | `ogcapi` | An individual OGC API collection and its supported subresources |
| Protocol | `opengeomesh` | Provides authenticated access to a shared OGC API collection |
| Protocol | `opengeomesh-receive` | Indicates support for receiving OpenGeoMesh shares |

The registration and wire representation of `opengeomesh-receive` MUST be consistent with the applicable OCM specification.

## 7. Change Management

OpenGeoMesh prioritizes stability and interoperability while allowing the protocol to evolve.

Backward-compatible extensions SHOULD build on existing standards, particularly OCM and OGC API. Implementations MAY add support for additional OGC API interfaces and capabilities without changing the meaning of existing protocol fields.

Proposed changes SHOULD be discussed through the [OpenGeoMesh issue tracker](https://codeberg.org/OpenGeoMesh/OpenGeoMesh/issues).

Topics under discussion include:

* [Real-time collaboration](https://codeberg.org/OpenGeoMesh/OpenGeoMesh/issues/32)
* [Referencing and sharing additional resources](https://codeberg.org/OpenGeoMesh/OpenGeoMesh/issues/31)
* [Using the OCM Token Flow instead of shared secrets](https://codeberg.org/OpenGeoMesh/OpenGeoMesh/issues/33)

Breaking changes MAY be introduced when approved by a significant portion of implementers. Such changes SHOULD result in a new major version of this specification.

## 8. References

### 8.1 Normative References

* **[OCM]** OpenCloudMesh API. <https://github.com/cs3org/OCM-API>
* **[OCM-1.3]** OpenCloudMesh Version 1.3.0. <https://github.com/cs3org/OCM-API/blob/v1.3.0/IETF-RFC.md>
* **[OGC-API-COMMON]** OGC API – Common, Part 1: Core. <https://docs.ogc.org/is/19-072/19-072.html>
* **[OGC-API-COLLECTIONS]** OGC API – Common, Part 2: Collections. <https://docs.ogc.org/DRAFTS/20-024.html>
* **[OGC-API-FEATURES]** OGC API – Features, Part 1: Core. <https://docs.opengeospatial.org/is/17-069r4/17-069r4.html>
* **[RFC9111]** HTTP Caching. <https://www.rfc-editor.org/rfc/rfc9111.html>
* **[RFC2119]** Key words for use in RFCs to Indicate Requirement Levels. <https://www.rfc-editor.org/rfc/rfc2119.html>
* **[RFC8174]** Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words. <https://www.rfc-editor.org/rfc/rfc8174.html>

### 8.2 Informative References

* **[OPEN-GEOMESH]** OpenGeoMesh. <https://opengeomesh.org/en/>
* **[OPEN-GEOMESH-CONCEPT]** OpenGeoMesh Concept. <https://opengeomesh.org/posts/concept>
* **[OGC-API-WORKSHOP]** OGC API Workshop. <https://ogcapi-workshop.ogc.org/api-deep-dive/features/>
