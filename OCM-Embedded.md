# Embedded JSON Resources in Open Cloud Mesh

**Giuseppe Lo Presti**<sup>1</sup>, **Rasmus Oscar Welander**<sup>1</sup>

<sup>1</sup>[CERN](https://home.cern/contact), European Organization for Nuclear Research.</br>
contact: giuseppe.lopresti@cern.ch


## Abstract

This document specifies the `embedded` protocol for Open Cloud Mesh (OCM). The protocol allows a representation of a Resource to be carried directly in an OCM Share Creation Notification, without requiring the Receiving Server to access the Resource through a remote access protocol or to obtain an access credential.

In addition, this document registers the `ro-crate` Resource Type, for Research Object Crate (RO-Crate) resources, and defines the `embedded` protocol for use with `user`, `group`, and `federation` shares of that Resource Type. RO-Crates are represented as a JSON value and can be carried directly in the OCM `protocol` object.

The `embedded` protocol is generic and does not define the semantics of the embedded JSON value. The semantics of the value are defined by the corresponding Resource Type.

## 1. Introduction

The Open Cloud Mesh (OCM) protocol allows a Sending Server to inform a Receiving Server that a Resource has been shared with some recipient.

OCM normally describes how the Receiving Server can subsequently access the shared Resource using one or more access protocols. This document specifies an alternative mechanism in which the representation of the Resource is carried directly in the Share Creation Notification.

An **embedded Resource** is a Resource for which the Share Creation Notification carries the complete Resource representation required by the Share Payload, rather than the metadata required to obtain that representation from the Sending Server.

Consequently, no subsequent access to the Sending Server is required to obtain the embedded representation, and no access credential is required for the embedded Resource.

The mechanism is particularly useful for metadata and other resources that are naturally represented as JSON.

This document defines:

* the `ro-crate` OCM Resource Type;
* the `embedded` OCM Protocol and its corresponding `embedded-receive` Discovery property; and
* the OCM Share Payload combinations for `ro-crate` Resources shared with multiple recipients using the `embedded` protocol.

The `embedded` protocol itself does not define the semantics of the embedded JSON value. It defines only how that value is carried in an OCM Share Creation Notification. The semantics of the value are defined by the corresponding Resource Type and Share Payload.

This document does not redefine any part of the OCM protocol that is already specified by [OCM]. In particular, the syntax and processing of the Share Creation Notification, OCM Discovery, HTTP transport, authentication, message signatures, and share lifecycle are defined by [OCM].

## 2. Conventions and Terminology

The key words **MUST**, **MUST NOT**, **REQUIRED**, **SHALL**, **SHALL NOT**, **SHOULD**, **SHOULD NOT**, **RECOMMENDED**, **NOT RECOMMENDED**, **MAY**, and **OPTIONAL** in this document are to be interpreted as described in BCP 14.

The terminology of [OCM] applies throughout this document.

An **embedded Resource** is a Resource for which the Share Creation Notification carries the complete Resource representation required by the Share Payload, rather than the metadata required to obtain that representation from the Sending Server.

An **embedded value** is the JSON value representing an embedded Resource.

## 3. `ro-crate` Resource Type

This document defines the following OCM Resource Type:

```
ro-crate
```

An `ro-crate` Resource is an RO-Crate Metadata Document represented as a JSON object.

The OCM `ro-crate` Resource Type does not impose any additional requirements on the OCM Share Creation Notification beyond those specified in this document and [OCM].

The semantics and structure of an RO-Crate are defined by the applicable RO-Crate specification.

An implementation MAY support multiple versions or profiles of the RO-Crate specification. The version or profile of an RO-Crate MAY be identified by information contained within the embedded JSON-LD document.

This document does not require the OCM protocol to interpret or otherwise process JSON-LD.

## 4. `embedded` Protocol

This document defines the following OCM Protocol:

```
embedded
```

The `embedded` protocol indicates that the representation of the shared Resource is contained directly in the Share Creation Notification.

When the `embedded` protocol is used:

1. the representation of the Resource MUST be present in the `embedded` protocol details;
2. the embedded representation MUST be a valid JSON value;
3. the Receiving Server MUST NOT be required to contact the Sending Server to retrieve the embedded representation; and
4. no access credential is required to access the embedded representation.

The `embedded` protocol does not define an access endpoint.

The embedded value MAY be any valid JSON value, including a JSON object, array, string, number, boolean, or null.

For Resource Types whose representation requires a JSON object, such as `ro-crate`, the corresponding Resource Type specification imposes the additional restrictions required by that Resource Type.

The `embedded` protocol does not define the semantics of the embedded JSON value. Those semantics are defined by the corresponding Resource Type and Share Payload.

The following conceptual layering applies:

```
embedded protocol
    |
    +-- arbitrary JSON value
             |
             +-- ro-crate Resource Type
                    |
                    +-- RO-Crate Metadata Document
```

Thus, the `embedded` protocol is not specific to RO-Crate and MAY be used by other Resource Types whose representations can be carried as JSON.

### 4.1. Protocol Details

The `protocol` field of a Share Creation Notification using the `embedded` protocol MUST use the `multi` representation defined by [OCM].

The protocol object MUST contain:

```
{
  "name": "multi",
  "embedded": <JSON value>
}
```

where `<JSON value>` is the representation of the shared Resource.

No `sharedSecret`, access token, URI, or other access credential is required or defined for the `embedded` protocol.

For example:

```
{
  "name": "multi",
  "embedded": {
    "example": "value"
  }
}
```

The example illustrates the encoding of the protocol and does not define a particular Resource Type.

## 5. Embedded RO-Crate

For the `ro-crate` Resource Type, the value of the `embedded` member MUST be a JSON object representing an RO-Crate Metadata Document.

The embedded object MUST be encoded as a JSON object and MUST NOT be encoded as a JSON string containing serialized JSON.

For example:

```
{
  "name": "multi",
  "embedded": {
    "@context": "https://w3id.org/ro/crate/1.2/context",
    "@graph": [
      {
        "@id": "ro-crate-metadata.json",
        "@type": "CreativeWork",
        "conformsTo": {
          "@id": "https://w3id.org/ro/crate/1.2"
        },
        "about": {
          "@id": "./"
        }
      },
      {
        "@id": "./",
        "@type": "Dataset",
        "name": "Example Dataset"
      }
    ]
  }
}
```

The JSON object is the Resource itself. It is not an access descriptor and does not contain an OCM access credential.

An implementation receiving an embedded RO-Crate MAY persist the JSON object as an RO-Crate Metadata Document or convert it to another equivalent local representation.

The version and profile of the RO-Crate Metadata Document are determined by the RO-Crate document itself and the applicable RO-Crate specification. This document does not restrict the `ro-crate` Resource Type to a particular version of the RO-Crate specification.

## 6. Processing of Embedded Resources

A Receiving Server that advertises support for the `embedded-receive` protocol for a Resource Type MUST be capable of receiving the corresponding embedded Resource.

Upon receipt of an OCM Share Creation Notification containing an embedded Resource, the Receiving Server MUST process the embedded value according to the specification associated with the corresponding Share Payload.

For an `ro-crate` Resource, the Receiving Server SHOULD process the embedded object as an RO-Crate Metadata Document.

A Receiving Server MAY persist the embedded Resource locally.

For an RO-Crate, a Receiving Server MAY retrieve and persist the Data Entities described by the RO-Crate, subject to the semantics and access mechanisms specified by the RO-Crate itself and local policy.

Retrieval of resources referenced by an RO-Crate is not part of the `embedded` OCM protocol.

In particular, a URI or other identifier occurring within the embedded JSON MUST NOT be interpreted as an OCM access endpoint solely by virtue of appearing in the embedded Resource.

A Receiving Server MUST NOT assume that an embedded Resource is available from the Sending Server unless such availability is separately specified by the Resource Type or by another protocol included in the Share Payload.

## 7. Discovery

A Sending Server supporting the `embedded` protocol MUST advertise the protocol according to the OCM Discovery mechanism defined by [OCM].

A Receiving Server supporting the reception of an embedded Resource MUST advertise the corresponding `embedded-receive` property.

For example, a Discovery entry for an `ro-crate` Resource at an OCM Server implementing both the sending and the receiving capabilities MAY be represented as:

```
{
  ...
  "resourceTypes" : [
    {
      "name": "ro-crate",
      "shareTypes": [
        "user"
      ],
      "protocols": {
        "embedded": {},
        "embedded-receive": {}
      }
    },
    ...
  ],
  "capabilities" : [
    "protocol-object",
    ...
  ],
  ...,
}
```

The precise Discovery document and its processing are defined by [OCM].

A Sending Server SHOULD only send an `ro-crate` Share using the `embedded` protocol when the Receiving Server advertises the corresponding `embedded-receive` capability for the `ro-crate` Resource Type and applicable share type.

## 8. Security Considerations

The embedded Resource is untrusted input and MUST be processed accordingly.

The integrity and authenticity of the OCM Share Creation Notification are governed by the OCM protocol and its applicable security mechanisms. This document does not introduce a separate authentication or authorization mechanism for the embedded Resource.

The `embedded` protocol deliberately does not require an access credential. Consequently, possession of a copy of the Share Creation Notification provides possession of the embedded Resource itself.

Implementations MUST NOT treat identifiers, URLs, JSON-LD contexts, or other values contained in an embedded Resource as trusted solely because they were received through OCM.

In particular, an implementation that dereferences URLs contained in an embedded Resource MUST apply appropriate protections against server-side request forgery, malicious redirects, resource exhaustion, and other attacks associated with processing attacker-controlled URLs.

For an RO-Crate, referenced Data Entities MAY be hosted remotely. Downloading such entities is outside the scope of the `embedded` protocol and MUST be subject to the Receiving Server's local security policy.

Implementations SHOULD impose appropriate limits on the size of an embedded Resource and on any subsequent processing or retrieval triggered by its contents.

An implementation MUST NOT interpret an identifier, URI, or credential contained in an embedded Resource as an OCM authorization credential unless that behavior is explicitly defined by another specification.

## 9. IANA Considerations

IANA is requested to make the following registrations in the "Open Cloud Mesh (OCM) Parameters" registry group.

### 9.1. OCM Resource Types Registry

The following entry is requested:

```
Resource Type:  ro-crate
Description:    An RO-Crate Metadata Document represented as JSON
Reference:      This document, Section 3
```

### 9.2. OCM Protocols Registry

The following entries are requested:

```
Property:       embedded
Role:           send
Reference:      This document, Section 4

Property:       embedded-receive
Role:           receive
Reference:      This document, Section 4
```

### 9.3. OCM Share Payloads Registry

The following entries are requested:

```
+===============+=============+===========+===============+
| Resource Type | Share Type  | Protocol  | Reference     |
+===============+=============+===========+===============+
| ro-crate      | user        | embedded  | This document |
| ro-crate      | group       | embedded  | This document |
| ro-crate      | fedreration | embedded  | This document |
+===============+=============+===========+===============+
```

These registrations define the wire format of the corresponding Share Creation Notifications in conjunction with [OCM] and this document.

## 10. Acknowledgements

We thank Oliver Keeble for the initial discussions in the context of the EOSC Data Commons project.

Work on this document has been funded by the EOSC Data Commons project "Services for inter- and cross-disciplinary data discovery, access, sharing and reuse in the EOSC Federation", which received funding from the European Union under Grant Agreement no. [101188179](https://cordis.europa.eu/project/id/101188179).

## 11. References

### 11.1. Normative References

[OCM]
Lo Presti, G., de Jong, M. B., Baghbani, M., and Nordin, M.,
"Open Cloud Mesh", [draft-ietf-ocm-open-cloud-mesh](https://datatracker.ietf.org/doc/draft-ietf-ocm-open-cloud-mesh).

[RO-CRATE]
Research Object Crate Community,
"RO-Crate Metadata", [specification](https://www.researchobject.org/ro-crate/specification.html).

### 11.2. Informative References

[RFC8126]
Cotton, M., Leiba, B., and Narten, T.,
"Guidelines for Writing an IANA Considerations Section in RFCs",
BCP 26, [RFC 8126](https://www.rfc-editor.org/info/rfc8126/).
