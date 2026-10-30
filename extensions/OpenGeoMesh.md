# OpenGeoMesh Protocol for Open Cloud Mesh

**Matthias Kraus**<sup>1</sup>

<sup>1</sup>[OpenGeoMesh](https://opengeomesh.org)
contact: info@opengeomesh.org

## Abstract

This document specifies the `opengeomesh` protocol for Open Cloud Mesh (OCM). The protocol enables federated sharing of individual OGC API collections between independently operated servers.

This document defines the `ogcapi` Resource Type, the `opengeomesh` protocol and its corresponding `opengeomesh-receive` Discovery property. OGC API collections are accessed using a URI and a share-specific access credential.

## 1. Introduction

The Open Cloud Mesh (OCM) protocol allows a Sending Server to inform a Receiving Server that a Resource has been shared with a recipient.

OCM provides mechanisms for discovering server capabilities, negotiating shares, and managing their lifecycle. This document specifies how OCM can be used to share individual OGC API collections.

An OpenGeoMesh share provides the URI of a collection and a credential for accessing it. The Receiving Server uses these details to access the collection on behalf of the recipient, optionally exposing it through its own OGC API.

This document defines:

* the `ogcapi` OCM Resource Type;
* the `opengeomesh` OCM protocol and its corresponding `opengeomesh-receive` Discovery property; and
* the OCM Share Payload for `ogcapi` Resources shared using the `opengeomesh` protocol.

This document does not redefine any part of the OCM protocol that is already specified by [OCM]. In particular, OCM Discovery, Share Creation Notifications, HTTP transport, authentication, message signatures, and share lifecycle are defined by [OCM].

## 2. Conventions and Terminology

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT, RECOMMENDED, NOT RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in BCP 14.

The terminology of [OCM] applies throughout this document.

A **Sending Server** is the OCM server that creates and provides access to a share.

A **Receiving Server** is the OCM server that receives a share and provides access to it for the recipient.

An **OpenGeoMesh Resource** is an individual OGC API collection, including its metadata, items, and supported subresources.

## 3. `ogcapi` Resource Type

This document defines the following OCM Resource Type:

    ogcapi

An `ogcapi` Resource represents an individual collection as defined by [OGC-API-COMMON] and [OGC-API-COLLECTIONS].

The URI identifying the shared Resource MUST identify the individual collection. It MUST NOT identify a general collections listing or an API endpoint exposing multiple collections.

The shared Resource includes the collection metadata and its supported subresources, such as feature items and individual feature endpoints, as defined by [OGC-API-FEATURES].

OpenGeoMesh does not define a proprietary geospatial data model. The structure and semantics of the shared Resource are defined by the applicable OGC API specifications.

Implementations MUST support:
* JSON representations of collection metadata, as defined by [OGC-API-COLLECTIONS].
* GeoJSON representations of features, as defined by [OGC-API-FEATURES].

Implementations MAY support additional OGC API interfaces and building blocks.

For writable shares, implementations MAY support [OGC-API-FEATURES-PART4], which specifies operations for creating, replacing, updating, and deleting features.

## 4. `opengeomesh` Protocol

This document defines the following OCM Protocol:

    opengeomesh

The `opengeomesh` protocol provides access to a shared `ogcapi` Resource through a URI and a share-specific credential.

The URI identifies an individual OGC API collection. The collection and its supported subresources MUST be accessible according to the applicable OGC API specifications.

When the `opengeomesh` protocol is used:

1. The protocol details MUST contain the URI of the shared collection.
2. The protocol details MUST contain a `sharedSecret` used to authorize access to the Resource.
3. Requests to the shared Resource MUST be authenticated using the `sharedSecret` as a bearer credential.
4. The shared URI MAY be absolute or relative to the base URI advertised for `opengeomesh` in OCM Discovery.
5. The protocol MAY provide a `service-desc` identifying an OpenAPI description for the shared collection.

### 4.1. Protocol Details

The `protocol` field of a Share Creation Notification using the `opengeomesh` protocol MUST use the `multi` representation defined by [OCM].

The protocol object MUST contain:

    {
      "name": "multi",
      "opengeomesh": {
        "sharedSecret": "<share-specific secret>",
        "uri": "<collection URI>"
      }
    }

The `service-desc` field MAY be included to identify an OpenAPI description for the shared collection.

For example:

    {
      "name": "multi",
      "opengeomesh": {
        "sharedSecret": "<share-specific secret>"
        "uri": "collections/incidents",
        "service-desc": "collections/api"
      }
    }

The `uri` identifies the individual collection defined by [OGC-API-COLLECTIONS]. If relative, it MUST be resolved against the `opengeomesh` base URI advertised by the Sending Server.

The `sharedSecret` MUST be unpredictable and MUST be treated as a secret. It MUST grant access only to the Resource and operations authorized by the share.

The `service-desc`, if present, MUST resolve to an OpenAPI description applicable to the shared collection. Access to this description MUST be protected by the same authorization requirements as the shared Resource.

The OGC API responses MUST preserve the semantics of the applicable OGC API specifications. In particular, collection metadata and feature resources MUST conform to [OGC-API-COLLECTIONS] and [OGC-API-FEATURES], respectively.

## 5. Processing of OpenGeoMesh Shares

A Receiving Server that advertises support for the `opengeomesh-receive` property for the `ogcapi` Resource Type MUST be capable of receiving the corresponding OpenGeoMesh shares.

Upon receipt of a Share Creation Notification containing an OpenGeoMesh share, the Receiving Server MUST process the share according to [OCM] and this document.

The Receiving Server SHOULD provide an interface through which the recipient can access the shared collection.

To access the Resource, the Receiving Server MUST resolve the URI as specified in Section 4.1 and MUST authenticate requests using the `sharedSecret` as a bearer credential.

The Receiving Server MUST NOT expose the `sharedSecret` to the recipient.

If the Receiving Server provides an OGC API interface for the shared Resource, links in the upstream OGC API responses MUST be rewritten to refer to the corresponding local resources.

The Receiving Server SHOULD respect HTTP caching headers supplied by the Sending Server, subject to authorization and revocation requirements.

Share acceptance, rejection, and deletion are handled through the OCM notification mechanisms defined by [OCM]. The Receiving Server MUST stop providing access to a share when it learns that the share has been revoked.

## 6. Discovery

A Sending Server supporting the `opengeomesh` protocol MUST advertise the protocol according to the OCM Discovery mechanism defined by [OCM].

A Receiving Server supporting the reception of OpenGeoMesh shares MUST advertise the corresponding `opengeomesh-receive` property.

For example, a Discovery entry for an OCM server implementing both capabilities MAY be represented as:

    {
      "enabled": true,
      "apiVersion": "1.3.0",
      "endPoint": "https://receiving-server.example.org",
      "provider": "Example Organization",
      "resourceTypes": [
        {
          "name": "ogcapi",
          "shareTypes": [
            "user"
          ],
          "protocols": {
            "opengeomesh": "/ogm/",
            "opengeomesh-receive": {}
          }
        }
      ],
      "capabilities": [
        "protocol-object"
      ],
      "criteria": [
        "http-request-signatures"
      ]
    }

The `opengeomesh` Discovery property identifies the base URI used to resolve relative collection URIs in shares sent by that server.

The `opengeomesh-receive` property indicates that the server can receive OpenGeoMesh shares. It does not define a separate access endpoint.

The precise Discovery document and its processing are defined by [OCM].

A Sending Server SHOULD send an OpenGeoMesh share only when the Receiving Server advertises the corresponding `opengeomesh-receive` property for the `ogcapi` Resource Type and applicable share type.

## 7. Security Considerations

All communication between OGM Servers MUST use HTTPS with certificate verification.

The authenticity of requests that create or modify shares MUST be verified according to the authentication and HTTP Message Signature requirements defined by [OCM].

Public keys used to verify remote servers MUST be retrieved and validated through HTTPS as specified by [OCM].

The `sharedSecret` grants access to the shared Resource and MUST be protected accordingly. It MUST NOT be included in URLs or exposed in logs, error messages, or client-visible responses.

The Sending Server MUST enforce the permissions associated with a share for every request. The Receiving Server MUST NOT forward credentials to unauthorized origins.

Implementations MUST validate resource URIs and prevent unauthorized access to internal network services. Federated sharing can otherwise be abused to perform server-side request forgery. Deployments SHOULD use network separation, outbound firewall rules, or destination allowlists to restrict access to internal networks.

Cached resources MUST NOT be served to users who are no longer authorized to access the share. Revocation cannot guarantee deletion of copies already downloaded by recipients.

## 8. IANA Considerations

IANA is requested to make the following registrations in the "Open Cloud Mesh (OCM) Parameters" registry group.

### 8.1. OCM Resource Types Registry

The following entry is requested:

    Resource Type:  ogcapi
    Description:    An individual OGC API collection and its supported subresources
    Reference:      This document, Section 3

### 8.2. OCM Protocols Registry

The following entries are requested:

    Property:       opengeomesh
    Role:           send
    Reference:      This document, Section 4

    Property:       opengeomesh-receive
    Role:           receive
    Reference:      This document, Section 6

### 8.3. OCM Share Payloads Registry

The following entry is requested:

    +===============+=============+=============+===============+
    | Resource Type | Share Type  | Protocol    | Reference     |
    +===============+=============+=============+===============+
    | ogcapi        | user        | opengeomesh | This document |
    +===============+=============+=============+===============+

These registrations define the wire format of the corresponding Share Creation Notifications in conjunction with [OCM] and this document.

## 9. Acknowledgements

The author thanks the OpenCloudMesh and OpenGeoMesh communities for their work on federated sharing and interoperable geospatial services.

## 10. References

### 10.1. Normative References

Lo Presti, G., de Jong, M. B., Baghbani, M., and Nordin, M., "Open Cloud Mesh". <https://datatracker.ietf.org/doc/draft-ietf-ocm-open-cloud-mesh>

[OGC-API-COMMON] Open Geospatial Consortium, "OGC API – Common, Part 1: Core". <https://docs.ogc.org/is/19-072/19-072.html>

[OGC-API-COLLECTIONS] Open Geospatial Consortium, "OGC API – Common, Part 2: Collections". <https://docs.ogc.org/DRAFTS/20-024.html>

[OGC-API-FEATURES] Open Geospatial Consortium, "OGC API – Features, Part 1: Core". <https://docs.opengeospatial.org/is/17-069r4/17-069r4.html>

[OGC-API-FEATURES-PART4] Open Geospatial Consortium, "OGC API – Features, Part 4: Create, Replace, Update and Delete". <https://docs.ogc.org/DRAFTS/20-002r1.html>

[RFC2119] Bradner, S., "Key words for use in RFCs to Indicate Requirement Levels", BCP 14, RFC 2119. <https://www.rfc-editor.org/rfc/rfc2119.html>

[RFC8174] Leiba, B., "Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words", BCP 14, RFC 8174. <https://www.rfc-editor.org/rfc/rfc8174.html>

### 10.2. Informative References

[OPEN-GEOMESH] OpenGeoMesh. <https://opengeomesh.org/en/>

[OPEN-GEOMESH-CONCEPT] OpenGeoMesh Concept. <https://opengeomesh.org/posts/concept>

[OGC-API-WORKSHOP] Open Geospatial Consortium, "OGC API Workshop". <https://ogcapi-workshop.ogc.org/api-deep-dive/features/>
