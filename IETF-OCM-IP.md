---
title: 'Open Cloud Mesh Integration Protocol'
docname: draft-nordin-ocm-integration-protocol-00
category: std

ipr: trust200902
area: Applications and Real-Time
keyword: Internet-Draft

stand_alone: yes
stream: IETF

author:
  - ins: M. Nordin
    name: Micke Nordin
    organization: SUNET
    email: kano@sunet.se
    uri: https://code.smolnet.org/micke

  - ins: G. Lo Presti
    name: Giuseppe Lo Presti
    organization: CERN
    email: giuseppe.lopresti@cern.ch
    uri: https://cern.ch/lopresti

  - ins: M. Baghbani
    name: Mahdi Baghbani
    organization: Ponder Source
    email: mahdi@pondersource.org
    uri: https://pondersource.com


--- abstract

The Open Cloud Mesh Integration Protocol (OCM-IP) defines how an Open
Cloud Mesh (OCM) Server can integrate supporting servers, such as
SSH/SFTP servers, web application platforms, or stand-alone WebDAV
servers, to perform protocol-specific work on its behalf.

OCM-IP makes it possible for existing OCM Servers to offload protocol
specific interactions to stand-alone servers, or even implement OCM as a
lightweight server that handles only the OCM parts of a deployment:
discovery, share creation, token issuance and signing.  Anything
protocol-specific, such as serving files over WebDAV, providing SSH
access, or running an interactive web application, can be handed off to
one or more Protocol Servers running elsewhere, possibly operated with
different software and on different infrastructure.

OCM-IP defines three integration modes: a provisioned mode, in which the
OCM Server pushes Share information to the Protocol Server over a signed
back channel; a self-contained mode, in which the Share information is
embedded in the signed access token itself, so that the Protocol Server
needs no per-share state and no inbound API at all; and an introspected
mode, in which the Protocol Server validates presented credentials
through a token introspection endpoint, restoring compatibility with
Receiving Servers that do not support token exchange.

OCM-IP is a protocol between the Sending OCM Server and its Protocol
Servers only.  The Receiving Server is not involved in, and does not
need to be aware of, this protocol: everything it observes is
indistinguishable from the Sending Server serving the access protocols
itself.  For this reason, an OCM Sending Server MAY adopt a
different strategy to interoperate with Protocol Servers, including
e.g. establishing trust via shared keys, without compromising
compliance with the OCM protocol.

--- middle

# Introduction

Open Cloud Mesh [OCM] is a server federation protocol used to notify a
Receiving Party that they have been granted access to some Resource.
OCM deliberately handles interactions only up to the point where the
Receiving Party is informed of their access; actual Resource access is
subsequently managed by other protocols, such as WebDAV [RFC4918], SSH,
or application-specific web protocols.

In existing deployments, the Sending Server typically implements both
the OCM endpoints and all of the access protocols it offers.  This
couples the federation logic to the storage and application logic, and
makes it hard to:

* implement OCM as a small, auditable component in front of existing
infrastructure,
* reuse a protocol implementation (for example a WebDAV server, an SFTP
server, or a computational notebook platform) across multiple OCM
deployments and vendors,
* operate the access protocol on separate infrastructure from the OCM
Server, for example running a web application platform in a different
security domain than the file sync and share system.

This document defines the Open Cloud Mesh Integration Protocol (OCM-IP),
which decouples the two concerns.  An OCM Server delegates the serving
of one or more access protocols to one or more Protocol Servers.  The
OCM Server remains the single party that the rest of the federation
interacts with: it performs OCM API Discovery, receives and sends Share
Creation Notifications.  The Protocol Server serves the actual Resource
access protocol, authorizing requests by independently verifying the
access tokens issued by the OCM Server.

Two properties of [OCM] make this delegation possible without sharing
secrets between the OCM Server and the Protocol Server:

1. The OCM Server publishes its public keys at the Well-Known [RFC8615]
path `/.well-known/jwks.json` in JWK format [RFC7517], and signs its
server-to-server requests using HTTP Message Signatures [RFC9421].
2. The Code Flow lets the Receiving Server exchange the `sharedSecret`
for an access token whose format [OCM] leaves entirely at the issuer's
discretion.

OCM-IP uses that freedom: it requires the OCM Server to issue these
access tokens as JWTs conforming to the JWT Profile for OAuth 2.0 Access
Tokens [RFC9068], signed with the OCM Server's published key.  Any
party, including a third-party service, can then verify such a token
without contacting the OCM Server on a per-request basis.

OCM-IP defines three integration modes that share a common authorization
core:

* Provisioned integration: a small back-channel API through which the
OCM Server provisions and revokes Share records on the Protocol Server,
ahead of any Resource access.
* Self-contained integration: the OCM Server embeds the Share
information in the access token itself, as an additional JWT claim.  The
Protocol Server keeps no per-share state and exposes no inbound API;
everything it needs arrives inside the signed token.
* Introspected integration: the Protocol Server validates each presented
credential through a token introspection endpoint [RFC7662] at the OCM
Server.  This is the compatibility mode: it is the only one that can
serve Receiving Servers that directly presents the legacy `sharedSecret`
instead of performing the token exchange.

In all modes, normative rules define how the Protocol Server authorizes
front-channel Resource access using the OCM credentials.

This document is intended to be useful to anyone who wants to write a
reusable server component for use with OCM, such that one implementation
of, say, a notebook platform integration can be used unchanged behind
OCM Servers from different vendors.

# Terms

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in BCP 14
[RFC2119] [RFC8174] when, and only when, they appear in all capitals, as
shown here.

This document reuses the following terms as defined in [OCM]:
_Resource_, _Share_, _Share Creation Notification_, _Sending Server_,
_Receiving Server_, _Sending Party_, _Receiving Party_, _OCM Address_,
_OCM Server_, and _Code Flow_.

In addition, we define:

* __Protocol Server__ - A server that serves one or more access
protocols (e.g., WebDAV, SSH, a web application) for Resources shared
through an OCM Server, on that OCM Server's behalf.
* __Integration API__ - The back-channel HTTP API exposed by a Protocol
Server, through which a paired OCM Server provisions and revokes Share
records.
* __Pairing__ - The out-of-band configuration step by which an OCM
Server and a Protocol Server are introduced to each other, establishing
mutual trust (see Pairing section).
* __Share Provisioning Request__ - A signed back-channel request from
the OCM Server to the Protocol Server, transferring the information the
Protocol Server needs in order to serve a Share.
* __Share Revocation Request__ - A signed back-channel request from the
OCM Server to the Protocol Server, instructing it to stop serving a
Share and release any associated resources.
* __Share Record__ - The Protocol Server's stored representation of a
provisioned Share, keyed by the pair (sender domain, providerId).
* __Provisioned Integration__ - The integration mode in which the OCM
Server transfers Share information to the Protocol Server over the back
channel, before any Resource access takes place.
* __Self-Contained Integration__ - The integration mode in which the
Share information travels inside the access token, in the `ocm_ip`
claim, and no back channel is used.
* __Introspected Integration__ - The integration mode in which the
Protocol Server validates a presented credential by querying a token
introspection endpoint [RFC7662] hosted by the OCM Server (or its
delegated Token Server).  Defined for backwards compatibility with
Receiving Servers that do not support the Code Flow.
* __ocm_ip Claim__ - A JWT claim, defined by this document, whose value
is an object carrying the Share information a Protocol Server needs in
order to serve a Share in Self-Contained Integration.
* __Front Channel__ - The path through which Resource access requests
reach the Protocol Server, originating from the Receiving Server or from
the Receiving Party's user agent, carrying a credential issued by the
OCM Server: an access token or, in Introspected Integration, possibly
the legacy `sharedSecret`.
* __Back Channel__ - The direct, signed, server-to-server path between
the OCM Server and the Protocol Server, carrying the Integration API
requests.

# Architecture

## Integration Modes

An OCM Server that delegates protocol work takes on the Sending Server
role of [OCM] towards the federation.  Towards its Protocol Servers it
uses one of three integration modes, chosen per pairing and per Share:

* In __Provisioned Integration__, the OCM Server acts as a client of the
Protocol Server's Integration API: it pushes a Share Record over the
signed back channel before the Share is created, and revokes it when the
Share ends.  This mode supports the full Share lifecycle, including
prompt revocation and the release of per-share resources, and is the
only mode that supports SSH.
* In __Self-Contained Integration__, there is no back channel at all:
the OCM Server embeds the Share information in the access token, in the
`ocm_ip` claim.  The Protocol Server is stateless with respect to
Shares, which makes this mode attractive for simple gateways (for
example a token-verifying WebDAV front end to an existing storage
system), at the cost of revocation latency bounded only by token
lifetime (see Lifecycle).
* In __Introspected Integration__, the Protocol Server validates each
presented credential by querying a token introspection endpoint
[RFC7662] at the OCM Server (or its delegated Token Server).  This is a
compatibility mode: it is the only mode that can serve Receiving Servers
that do not support the `exchange-token` capability and therefore
present the legacy `sharedSecret` directly on the front channel.  It
reintroduces a per-request dependency on the OCM Server, which the other
two modes avoid.

A Protocol Server MAY support any combination of the modes.  Protocols
that allocate per-share resources or sessions (for example a notebook
platform that starts a computational session per Share) SHOULD use
Provisioned Integration, since Self-Contained Integration provides no
signal to release such resources.  Introspected Integration SHOULD be
used only where it is needed, namely for Shares towards Receiving
Servers that cannot perform the token exchange; where the Code Flow is
available, the other two modes avoid the per-request coupling.

## Provisioned Integration Flow

~~~
 Sending    OCM Server      Protocol     Receiving    Receiving
  Party   (Sending Server)    Server        Server       Party
    |            |              |             |            |
    | 1. Sending |              |             |            |
    |    Gesture |              |             |            |
    |----------->|              |             |            |
    |            | 2. Share     |             |            |
    |            | Provisioning |             |            |
    |            | Request      |             |            |
    |            |------------->|             |            |
    |            | 3. 201       |             |            |
    |            |<-------------|             |            |
    |            | 4. Share Creation          |            |
    |            |    Notification            |            |
    |            |--------------------------->|            |
    |            |              |             | 5. notify  |
    |            |              |             |----------->|
    |            | 6. Token Request           |            |
    |            |    (Code Flow)             |            |
    |            |<---------------------------|            |
    |            | 7. access_token (JWT)      |            |
    |            |--------------------------->|            |
    |            |              | 8. Resource access       |
    |            |              |    with access_token     |
    |            |              |<------------+------------|
    |            |              | 9. verify token against  |
    |            |              |    OCM Server's JWKS,    |
    |            |              |    look up Share Record, |
    |            |              |    serve the protocol    |
~~~

The numbered steps are:

1. The Sending Party makes a Sending Gesture to the OCM Server, as
   described in [OCM].
2. The OCM Server sends a Share Provisioning Request over the back
   channel to the Protocol Server responsible for (one or more of) the
protocols offered in the Share.
3. The Protocol Server verifies the request signature, stores the Share
   Record and acknowledges.
4. The OCM Server sends the Share Creation Notification to the Receiving
   Server, exactly as specified in [OCM].  The protocol endpoints
advertised in the notification point (directly or via a reverse proxy)
at the Protocol Server.
5. The Receiving Server notifies the Receiving Party as usual.
6. The Receiving Server exchanges the `sharedSecret` for an access token
   at the OCM Server's `tokenEndPoint`, using the Code Flow of [OCM].
7. The OCM Server issues a signed JWT access token whose `client_id`
   claim equals the `providerId` of the Share provisioned in step 2.
8. The Receiving Server (or the Receiving Party's user agent, depending
   on the access protocol) presents the access token to the Protocol
Server.
9. The Protocol Server verifies the token against the OCM Server's
   published keys, looks up the Share Record by (issuer domain,
`client_id`), cross-checks the identities bound into the token, and
serves the protocol-specific Resource access.

## Self-Contained Integration Flow

~~~
 Sending    OCM Server      Protocol     Receiving    Receiving
  Party   (Sending Server)    Server        Server       Party
    |            |              |             |            |
    | 1. Sending |              |             |            |
    |    Gesture |              |             |            |
    |----------->|              |             |            |
    |            | 2. Share Creation          |            |
    |            |    Notification            |            |
    |            |--------------------------->|            |
    |            |              |             | 3. notify  |
    |            |              |             |----------->|
    |            | 4. Token Request           |            |
    |            |    (Code Flow)             |            |
    |            |<---------------------------|            |
    |            | 5. access_token (JWT       |            |
    |            |    with ocm_ip claim)      |            |
    |            |--------------------------->|            |
    |            |              | 6. Resource access       |
    |            |              |    with access_token     |
    |            |              |<------------+------------|
    |            |              | 7. verify token against  |
    |            |              |    OCM Server's JWKS,    |
    |            |              |    check issuer pairing, |
    |            |              |    serve per the ocm_ip  |
    |            |              |    claim                 |
~~~

The flow is the OCM flow unchanged, except that the token issued in step
5 carries the `ocm_ip` claim, and that the protocol endpoints advertised
in step 2 point at the Protocol Server.  The Protocol Server is not
contacted before Resource access, holds no Share Records, and learns of
each Share only when the first request for it arrives.

## Introspected Integration Flow

~~~
 Sending    OCM Server      Protocol     Receiving    Receiving
  Party   (Sending Server)    Server        Server       Party
    |            |              |             |            |
    | 1. Sending |              |             |            |
    |    Gesture |              |             |            |
    |----------->|              |             |            |
    |            | 2. Share Creation          |            |
    |            |    Notification            |            |
    |            |    (legacy sharedSecret)   |            |
    |            |--------------------------->|            |
    |            |              |             | 3. notify  |
    |            |              |             |----------->|
    |            |              | 4. Resource access       |
    |            |              |    with sharedSecret     |
    |            |              |<------------+------------|
    |            | 5. Token Introspection     |            |
    |            |    Request (signed)        |            |
    |            |<-------------|             |            |
    |            | 6. active + Share          |            |
    |            |    information             |            |
    |            |------------->|             |            |
    |            |              | 7. serve per the         |
    |            |              |    introspection         |
    |            |              |    response              |
~~~

The Share Creation Notification in step 2 is a legacy [OCM] share: it
carries the `sharedSecret` and does not include `must-exchange-token`,
because the Receiving Server cannot honor it.  The Protocol Server
validates the presented credential by introspecting it at the OCM Server
(steps 5 and 6) and authorizes the request from the introspection
response.

Introspected Integration composes with Provisioned Integration for the
same Share: in that case the introspection response identifies the
provisioned Share Record via `client_id`, and introspection replaces
only the credential validation, not the lifecycle handling.

## Relationship to Open Cloud Mesh

OCM-IP is layered strictly behind the Sending Server role of [OCM]:

* The OCM Server remains the Discoverable Server.  Protocol Servers MUST
NOT be required to expose `/.well-known/ocm`.
* The OCM Server remains the recipient of Invite Acceptance Requests,
Share Acceptance Notifications and all other OCM endpoints.
* The OCM Server remains the OAuth Authorization Server towards the
federation: access tokens are issued under its identity and verified
against the keys it publishes.  The hosting of the `tokenEndPoint`
itself MAY however be delegated as well; see the note below.
* The Protocol Server takes on (part of) the OAuth Resource Server
function: it is the party that ultimately accepts access tokens in
exchange for Resource access.

Shares whose protocols are served by a Protocol Server MUST use the Code
Flow of [OCM] unless the Share uses Introspected Integration: the OCM
Server MUST include `must-exchange-token` in the requirements of every
protocol entry that a Protocol Server serves in Provisioned or
Self-Contained Integration.  Legacy shared-secret access cannot be
verified by a Protocol Server on its own, because the long-lived secret
is deliberately never replicated to it; Introspected Integration exists
precisely to close this gap for Receiving Servers that cannot perform
the token exchange, at the cost of a per-request callback (see Token
Introspection and Security Considerations).

### Note: Delegating the Token Endpoint

This note is non-normative.

The `tokenEndPoint` is advertised as an absolute URL in the OCM Server's
discovery document, and nothing in [OCM] requires it to be served from
the OCM Server's own host.  Token issuance can therefore, in principle,
be delegated to a separate Token Server, in the same spirit as the rest
of this document:

* The Token Server holds its own signing keypair, and the OCM Server
publishes the public key in its own `/.well-known/jwks.json` under a
`kid` in its own domain.  The `iss` and `kid` rules of this document
(see Token Issuance by the OCM Server) are then satisfied without any
private key leaving the Token Server, and token
verification by Receiving Servers and Protocol Servers is unchanged.
* The Token Server learns about Shares through a special case of the
back channel: a share preparation request, by which the OCM Server sends
the information needed for issuance (the parties, the `providerId` or
the `ocm_ip` contents, the expiration) and receives in response a
`sharedSecret` minted by the Token Server.  The OCM Server forwards that
secret to the Receiving Server in the Share Creation Notification,
without needing to retain it.  The code presented in the Code Flow is
thereby validated by the very server that minted it, and the secret is
never stored outside the Token Server.

In such a deployment the OCM Server is reduced to pure federation logic:
discovery, Share bookkeeping, notifications and invites, with both token
issuance and Resource access served elsewhere.  The share preparation
request is identical to a request sent over the normal back channel, the
only difference being that the response from the Token Server includes
the `sharedSecret`.

## The Transparency Requirement

OCM-IP is purely a protocol between the Sending Server and the Protocol
Server.  The Receiving Server MUST NOT be required to implement, or even
be aware of, OCM-IP.

Concretely, everything observable by the Receiving Server and the
Receiving Party MUST be indistinguishable from a deployment in which the
Sending Server serves the access protocols itself:

* The protocol endpoints advertised in OCM API Discovery and in Share
Creation Notifications are ordinary URIs (or `host:port` addresses for
SSH); whether they are served by the OCM Server, by a reverse proxy in
front of a Protocol Server, or by a Protocol Server on a different
hostname is invisible at the OCM layer.
* Access tokens are obtained from the OCM Server's `tokenEndPoint` and
presented to the advertised protocol endpoint, exactly as specified in
[OCM].
* Errors returned by the Protocol Server on the front channel use the
semantics of the access protocol concerned.

A consequence of this requirement is that no OCM capability or criterium
is defined for OCM-IP: there is nothing for a remote peer to discover.

## Topologies

The mapping between OCM Servers and Protocol Servers is many-to-many:

* An OCM Server MAY pair with multiple Protocol Servers, for example one
serving WebDAV and another serving a web application platform, and MAY
provision the same Share to more than one of them when the Share offers
multiple protocols.
* A Protocol Server MAY be paired with multiple OCM Servers.  Share
Records are keyed by the pair (sender domain, providerId), so records
provisioned by different OCM Servers cannot collide and access tokens
issued by one OCM Server cannot address records provisioned by another.
In Self-Contained Integration the same isolation holds trivially: a
token is honored only if its issuer is paired, and grants only what its
own claims describe.

# Pairing

Before a Protocol Server serves any Share, the OCM Server and the
Protocol Server MUST be paired.  Pairing is performed out of band,
typically by the operators of the two systems, and consists of at least:

* On the OCM Server: which protocols and resource types the Protocol
Server is responsible for, which integration mode(s) to use, and, for
Provisioned Integration, the base URL of the Integration API of the
Protocol Server (referred to as `{integrationAPI}` below).  For
Introspected Integration, additionally the domain of the Protocol
Server, used to verify its introspection requests.
* On the Protocol Server: the domain(s) of the paired OCM Server(s) and
the integration mode(s) permitted for each.  The Protocol Server MUST
maintain an allowlist of paired OCM Server domains, MUST reject
Integration API requests whose sender is not on that allowlist, and MUST
NOT honor the `ocm_ip` claim of tokens whose issuer is not paired for
Self-Contained Integration.  For Introspected Integration, additionally
the URL of the introspection endpoint (referred to as
`{introspectionEndPoint}` below).

No shared secret is exchanged during pairing.  All trust on the back
channel derives from HTTP Message Signatures [RFC9421] made with the OCM
Server's signatory key, verified against the keys the OCM Server
publishes at `https://<domain>/.well-known/jwks.json` [RFC7517], as
specified in [OCM].  All trust on the front channel derives from the JWT
signatures on the access tokens, verified against the same published
keys.  Trust in introspection requests derives, symmetrically, from HTTP
Message Signatures made with the Protocol Server's key, published at the
Protocol Server's own `/.well-known/jwks.json`.

The Protocol Server consequently does not need a signing keypair of its
own to implement this protocol, unless it uses Introspected Integration,
which requires it to sign its introspection requests (see Token
Introspection).

# Integration API

The Integration API is the back channel of Provisioned Integration.  A
Protocol Server that supports only Self-Contained Integration does not
expose it, and an OCM Server never calls it for self-contained Shares.

## General Requirements

All Integration API requests:

* MUST be made over TLS (implementations MAY fall back to plain HTTP in
testing setups only),
* MUST use the HTTP POST method with `application/json` as the
`Content-Type` request header,
* MUST be signed with an HTTP Message Signature [RFC9421] carrying the
label `ocm`, following the same rules as server-to-server requests in
[OCM]: the signature MUST cover at least `@method`, `@target-uri`,
`content-digest`, `content-length` and `date`, MUST include the
`created` parameter, and MUST be made with an asymmetric algorithm using
a key advertised in the OCM Server's `/.well-known/jwks.json`.

On receipt of an Integration API request, the Protocol Server:

1. MUST parse the `sender` field from the request body and derive the
sender domain from the part after the last `@` sign.
2. MUST verify that the sender domain is on its allowlist of paired OCM
Servers, and reject the request with HTTP status 401 otherwise.
3. MUST verify the `ocm`-labeled signature against the JWKS of the
sender domain, following the verification rules of [OCM] (single `ocm`
label, required covered components, content-digest match [RFC9530],
`created`
within a freshness window, `keyid` domain equal to the sender domain),
and reject the request with HTTP status 401 on any failure.

Note that, unlike the Share Creation Notification of [OCM], where the
verification key is discovered from the `sender` field of an arbitrary
remote server, the allowlist check in step 2 happens before any key
fetching: a Protocol Server never fetches keys from, or processes
payloads of, servers it is not paired with.

If the Protocol Server is deployed behind a TLS-terminating reverse
proxy, it MUST reconstruct the `@target-uri` that the OCM Server signed
(i.e., the public URL) when verifying signatures, for example from
forwarding headers set by the proxy.

## Share Provisioning Request

To provision a Share, the OCM Server MUST send a Share Provisioning
Request:

* to `{integrationAPI}/shares`,
* before sending the corresponding Share Creation Notification to the
Receiving Server (see Lifecycle below),
* with a request body containing a JSON document as described below.

### Fields

The request body is the Share Creation Notification object of [OCM] that
the OCM Server intends to send to the Receiving Server, with one
transformation applied: every `sharedSecret` field, in every protocol
entry, MUST be removed.  The Protocol Server never receives, stores, or
needs any OCM secret.

The fields used by the Protocol Server are thus:

* REQUIRED `sender` (string) - OCM Address of the user that creates the
Share.  The domain part identifies the paired OCM Server and selects the
verification keys, as described above.
* REQUIRED `owner` (string) - OCM Address of the user that owns the
Resource.  Used for identity binding on the front channel.
* REQUIRED `shareWith` (string) - OCM Address of the Receiving Party.
Used for identity binding on the front channel.
* REQUIRED `providerId` (string) - as in [OCM]; opaque identifier of the
Share at the OCM Server, unique per Share.  It keys the Share Record and
links the back channel to the front channel (see below).
* REQUIRED `shareType` (string) - as in [OCM].
* REQUIRED `resourceType` (string) - as in [OCM].
* REQUIRED `protocol` (object) - as in [OCM], transformed as described
above.  The protocol entries carry the protocol-specific information the
Protocol Server needs to serve the Share (for example the `webdav`
entry's `uri` and `permissions`, or the `webapp` entry's `viewMode`).
* OPTIONAL `name`, `description`, `ownerDisplayName`,
`senderDisplayName`, `expiration` - as in [OCM]; informational, except
`expiration`, which the Protocol Server SHOULD honor (see Lifecycle).

Additional fields from the Share Creation Notification MAY be present
and MUST be ignored if not understood.

### The providerId

The `providerId` is the link between the back channel and the front
channel, and the following rules apply:

* [OCM] guarantees that the `providerId` is unique per Share, so the
pair (sender domain, providerId) identifies exactly one Share Record.
* The OCM Server MUST set the `client_id` claim of every access token it
issues for this Share (via its `tokenEndPoint`) to exactly the
`providerId`.  This constrains a value that the token profile of this
document (see Token Issuance by the OCM Server) otherwise leaves at the
OCM Server's discretion.
* The `providerId` is an identifier, not a credential: the Receiving
Server learns it from the Share Creation Notification anyway.
Possession of a `providerId` MUST NOT grant any access by itself; all
front channel authorization derives from the verified access token.
Consequently, the `providerId` does not need to be unguessable, and it
MAY appear in URLs and logs.

### Response

On success the Protocol Server MUST respond with HTTP status 201 and a
JSON object with the following fields:

* OPTIONAL `status` (string) - e.g. `"stored"`.
* OPTIONAL `protocol` (object) - protocol details allocated by the
Protocol Server for this Share, in the same format as the `protocol`
object of [OCM].

When the response contains a `protocol` object, the OCM Server SHOULD
use its field values (for example, a per-share `uri` allocated by the
Protocol Server) when constructing the corresponding protocol entries of
the outbound Share Creation Notification, in place of statically
configured values from the pairing.  This allows a Protocol Server to
allocate endpoints dynamically, per Share.

Two restrictions apply to the response `protocol` object:

* It MUST NOT contain `sharedSecret` fields, and an OCM Server MUST
ignore any `sharedSecret` found in a Share Provisioning Response.
(Delegated token issuance is the exception: the share preparation
request is this same request sent to a Token Server, whose response
legitimately carries the `sharedSecret` it minted; see the note on
delegating the token endpoint.)
* The OCM Server MUST NOT take permissions from the response: the
Share's permissions are decided by the Sending Party and the OCM Server,
never by the Protocol Server.

Fields in the response `protocol` object that the OCM Server does not
understand MUST be ignored.

A Share Provisioning Request for a (sender domain, providerId) pair that
already has a Share Record MUST replace the existing record and respond
with HTTP status 201.  This makes provisioning idempotent and gives the
OCM Server a way to update a Share (for example after a permissions
change) by re-provisioning it.

Error responses:

* 400 - the request body is not valid JSON, or a required field is
missing or malformed.
* 401 - the signature is missing, malformed, stale or invalid, or the
sender domain is not on the allowlist of paired OCM Servers.
* 503 - the Protocol Server is temporarily unable to provision the
Share.

## Share Revocation Request

When a Share is deleted, expires, is declined by the Receiving Party, or
access is otherwise withdrawn, the OCM Server SHOULD send a Share
Revocation Request:

* to `{integrationAPI}/revoke`,
* with a request body containing a JSON document with the following
fields:

* REQUIRED `sender` (string) - an OCM Address whose domain part
identifies the paired OCM Server, subject to the same allowlist and
signature checks as all Integration API requests.
* REQUIRED `providerId` (string) - the `providerId` of the Share to
revoke.

On receipt of a valid Share Revocation Request, the Protocol Server MUST
stop serving the identified Share, MUST delete the Share Record, and
SHOULD release any resources associated with it (for example, stopping a
computational session that was started for the Share, or invalidating
local sessions derived from its access tokens).

### Response

Revocation MUST be idempotent: if no Share Record exists for the given
(sender domain, providerId), the Protocol Server MUST respond with HTTP
status 200, so that the OCM Server can treat revocation as
fire-and-forget.  This document defines one OPTIONAL response field:

* OPTIONAL `status` (string) - e.g. `"revoked"` when a record was found
and revoked, `"gone"` when there was nothing to revoke.

Error responses are as for Share Provisioning.

## Liveness

A Protocol Server SHOULD respond to a GET request to `{integrationAPI}`
(or `{integrationAPI}/`) with HTTP status 200 and a JSON object, so that
operators and OCM Servers can verify reachability of the Integration
API.  The contents of the object are not specified.

# Token Introspection

Token introspection is the credential validation path of Introspected
Integration.  The introspection endpoint is hosted by the OCM Server or,
when token issuance is delegated, by its Token Server; its URL,
`{introspectionEndPoint}`, is exchanged during pairing.  It is not
advertised in the OCM discovery document: like the Integration API, it
is invisible to the federation.

Note that a legacy credential is opaque and carries no issuer
information, so the Protocol Server has no way to determine which paired
OCM Server to introspect against; Introspected Integration therefore
cannot work in multi-tenant deployments, where one Protocol Server
serves more than one OCM Server through the same protocol endpoint.

## Request

To validate a presented credential, the Protocol Server sends an HTTP
POST request to `{introspectionEndPoint}` as specified by [RFC7662]: the
request body is `application/x-www-form-urlencoded` with a `token`
parameter carrying the credential exactly as presented on the front
channel.  The credential MAY be a legacy `sharedSecret` or a JWT access
token; the endpoint MUST accept any credential that is valid for a Share
at this OCM Server.

The request MUST be made over TLS and MUST be signed with an HTTP
Message Signature [RFC9421] carrying the label `ocm`, with the same
covered components and `created` rules as Integration API requests.  The
`keyid` MUST identify a key in the Protocol Server's own JWKS, published
at `https://<protocol-server-domain>/.well-known/jwks.json` [RFC7517].
The introspection endpoint MUST verify that the `keyid` domain belongs
to a paired Protocol Server and MUST verify the signature against that
domain's JWKS before evaluating the credential; unauthenticated or
unpaired requests MUST be rejected without revealing whether the
presented credential is valid.  This authentication requirement is what
keeps the endpoint from acting as a credential-validity oracle (Section
4 of [RFC7662]).

## Response

The response is an [RFC7662] introspection response.  For an unknown,
expired or revoked credential the endpoint MUST respond with `{"active":
false}` and no other members.  For a valid credential the response
object MUST contain:

* `active` (boolean) - `true`.
* `iss`, `sub`, `aud` (strings) - with the claim semantics this document
defines for access tokens (see Token Issuance by the OCM Server).
* `exp` (integer) - for a JWT, the token's own `exp`; for a legacy
`sharedSecret`, the time until which the Protocol Server may rely on
this response.  The endpoint MUST set a short horizon (on the order of
minutes), since `exp` also bounds revocation latency.
* `client_id` (string) - the Share's `providerId`, when the Share is
provisioned to the calling Protocol Server.
* `ocm_ip` (object) - the Share information as defined for the `ocm_ip`
claim, when the Share is not provisioned to the calling Protocol Server.

The Protocol Server uses exactly one of these: a `client_id` naming a
Share Record, or the `ocm_ip` member, as described in Token
Verification.

The Protocol Server MAY cache a positive response until its `exp` and
MUST NOT rely on it beyond that.  Negative responses SHOULD NOT be
cached for more than a brief interval.

# Front Channel: Resource Access

## Token Issuance by the OCM Server

Token issuance follows the Code Flow of [OCM]: the Receiving Server
exchanges the `sharedSecret` from the Share Creation Notification for an
access token at the OCM Server's `tokenEndPoint`.  [OCM] treats the
issued `access_token` as an opaque bearer credential and leaves its
format at the issuer's discretion.  This document profiles that format.

For every Share in Provisioned or Self-Contained Integration, the
`access_token` MUST be a JWT conforming to the JWT Profile for OAuth 2.0
Access Tokens [RFC9068].  The JOSE header MUST include `typ` with the
value set to `at+jwt` and MUST include a `kid` parameter identifying the
OCM Server's signatory key advertised in `/.well-known/jwks.json`, and
MUST NOT use `none` as the `alg`.  The JWT MUST be signed with the
private key corresponding to that signatory key, allowing anyone with
access to the corresponding public key, including a Protocol Server, to
verify the token independently.  The `expires_in` value of the token
response MUST agree with the `exp` claim.  Receiving Servers are
unaffected: they continue to treat the token as opaque, per [OCM].

The JWT Claims Set MUST include the claims required by [RFC9068], with
the following OCM-specific semantics, on which the Protocol Server
relies:

* `iss` - the Sending Server identifier, derived from the scheme and
authority of the signatory keyId.
* `sub` - the Share owner on the Sending Server.
* `aud` - the OCM principal authorized by the token, i.e. the
`shareWith` value of the Share.  Per Section 4.1.3 of [RFC7519] the
interpretation of audience values is application-specific, and this
document defines that interpretation.
* `client_id` - as defined in Section 4.3 of [RFC8693], which forwards
to Section 2.2 of [RFC6749].  Verifiers MUST NOT assume a particular
size or format beyond what this document specifies per integration
mode.
* `iat`, `exp`, `jti` - as in [RFC9068].

Further requirements apply per integration mode.

For a Share in Provisioned Integration:

* The `client_id` claim MUST equal the `providerId` of the Share.
* The token MUST NOT carry the `ocm_ip` claim.  Mixing the modes for a
single Share would allow a self-contained token to outlive the
revocation of the Share Record (see Security Considerations).

For a Share in Self-Contained Integration:

* The token MUST carry the `ocm_ip` claim described in the next section.
* The `exp` claim MUST NOT be later than the Share's `expiration`, when
the Share has one.
* The token SHOULD be short-lived: the RECOMMENDED lifetime is on the
order of minutes or for special use-cases, hours, relying on the
Receiving Server to re-exchange the `sharedSecret` for a fresh token per
[OCM].  Because no revocation signal exists in this mode, the remaining
lifetime of the longest-lived valid token is exactly how long access
survives the end of the Share.
* Once the Share ends, the OCM Server MUST NOT issue further tokens for
it.  This holds in all modes, but in Self-Contained Integration it is
the only revocation mechanism.

For a Share in Introspected Integration, no additional issuance
requirements apply.  Typically no token is issued at all, since this
mode serves Receiving Servers that present the legacy `sharedSecret`
directly.  Should such a Share nevertheless be exchanged for tokens, the
Protocol Server can validate those tokens through the same introspection
endpoint.

## The ocm_ip Claim

The value of the `ocm_ip` claim is a JSON object carrying the Share
information that the Share Provisioning Request carries in Provisioned
Integration.  The Share's parties are deliberately not part of the
claim: the owner and the Receiving Party are already bound by the `sub`,
`iss` and `aud` claims of the enclosing token.

Fields:

* REQUIRED `protocol` (object) - as the `protocol` object of [OCM],
restricted to the protocol entries this token grants access to.  It MUST
NOT contain `sharedSecret` fields.
* REQUIRED `providerId` (string) - as in [OCM]; opaque identifier of the
Share at the OCM Server, useful for logging and correlation.
* REQUIRED `resourceType` (string) - as in [OCM].
* OPTIONAL `name` (string) - as in [OCM].
* OPTIONAL `shareType` (string) - as in [OCM].
* OPTIONAL `expiration` (integer) - as in [OCM].

Fields in the `ocm_ip` claim that the Protocol Server does not
understand MUST be ignored.

## Token Verification by the Protocol Server

When a front-channel request presents a credential, the Protocol Server
MUST authorize it as follows:

1. If the credential parses as a JWT, extract the `iss` claim without
trusting it; reject the credential if `iss` is missing or is not an
`https` URL, and continue with step 2.  If it does not parse as a JWT,
or when the Protocol Server prefers introspection over local
verification, validate the credential through Token Introspection
instead: an `active` response supplies the fields (`iss`, `sub`, `aud`,
`exp`, `client_id`, `ocm_ip`) used in steps 4 to 6, and steps 2 and 3
are skipped; an inactive response means the request is rejected.
2. Resolve the signing key: fetch (or use a cached copy of) the JWKS at
`https://<iss-host>/.well-known/jwks.json` and select the key matching
the token's `kid` header parameter.
3. Verify the token signature and validity per [RFC9068]: the algorithm
MUST be an asymmetric algorithm matching the key, MUST NOT be `none`,
and the `exp` claim MUST be in the future.  The claims `iss`, `sub`,
`aud`, `exp` and `client_id` MUST all be present.
4. Determine the integration mode:
   * If a Share Record exists for the pair (host part of `iss`,
   `client_id` claim), the token is authorized against that record
   (Provisioned Integration).  Any `ocm_ip` claim in the token MUST be
   ignored.
   * Otherwise, if the verified token carries an `ocm_ip` claim and the
   host part of `iss` is paired for Self-Contained Integration, or the
   introspection response carries an `ocm_ip` member, the credential is
   authorized against those claims.
   * Otherwise, reject the request.  Because Share Records only come
   into existence through signed back-channel requests from paired OCM
   Servers, the `ocm_ip` claim is only honored for paired issuers, and
   introspection only ever consults paired endpoints, credentials from
   unrelated issuers, however validly signed, grant nothing.
5. Perform identity binding (next section).
6. Serve the request according to the protocol entry of the Share Record
or of the `ocm_ip` claim or member, honoring its permissions (e.g.
`protocol.webdav.permissions`), its `expiration` if present, and any
protocol-specific restrictions.

The token's `exp` claim is authoritative for token lifetime.  Any expiry
hint delivered alongside the token on the front channel (such as the
`access_token_ttl` form field used by WOPI-style web applications) MUST
agree with the `exp` claim, otherwise the access MUST be rejected.

The Protocol Server MAY cache JWKS documents.  It SHOULD bound the cache
lifetime so that key rotation and key revocation at the OCM Server take
effect within a reasonable time.

## Identity Binding

In Provisioned Integration, a valid signature and a matching Share
Record are not sufficient: the token MUST also be bound to the
identities stored in the record.  The Protocol Server MUST verify that:

* the OCM Address formed as `<sub>@<iss-host>` equals the Share Record's
`owner`, and
* the `aud` claim equals the Share Record's `shareWith`.

Comparison of OCM Addresses SHOULD be performed after canonicalising the
host part (lowercasing, removing any stray scheme prefix or trailing
slash); the identifier part is opaque and MUST be compared byte for
byte.

These checks ensure that an access token can only be used for the exact
Share it was issued for: a token legitimately issued to one Receiving
Party for one Resource cannot be replayed against a Share Record
involving any other party or Resource, even at the same Protocol Server
and from the same OCM Server.  The same checks apply when the fields
come from an introspection response that names a Share Record via
`client_id`.

In Self-Contained Integration, and when serving from the `ocm_ip` member
of an introspection response, there is no stored record to compare
against: the credential itself is the authority, and the owner and the
Receiving Party are read directly from `<sub>@<iss-host>` and `aud`.
The cross-checks above therefore do not apply; what remains is to
enforce the scope of the `ocm_ip` claim (protocol entries, permissions,
expiration) and, where the protocol concerned authenticates the
Receiving Party, to derive that identity from `aud` using the same
canonicalisation rules.

## Token Presentation per Protocol

How the access token reaches the Protocol Server depends on the access
protocol, and follows [OCM] and its protocol-specific companion
specifications.  Non-normative summary:

* `webdav` - the Receiving Server acts as the API client and presents
the token in the `Authorization: Bearer` header of its WebDAV requests
to the advertised `webdav` endpoint.
* `webapp` - the Receiving Server delivers the token to the Receiving
Party's user agent, which presents it to the advertised `webapp`
endpoint via a form POST (`access_token` field), keeping the token out
of URLs.  The Protocol Server typically responds by establishing a
session (e.g. a cookie scoped to the application) and serving the
application.
* `ssh` - SSH access is authenticated with the recipient's public key
per [OCM] rather than with a bearer token.  An SSH/SFTP Protocol Server
uses the Share Provisioning Request to learn which key material and
paths to authorize, and the Share Revocation Request to withdraw that
authorization.  The token verification rules of this section do not
apply to the SSH data channel itself, and Self-Contained Integration is
consequently not applicable to `ssh`: there is no token presentation
through which an `ocm_ip` claim could travel.

# Lifecycle

## Ordering

In Provisioned Integration, the OCM Server MUST send the Share
Provisioning Request, and receive a success response, before sending the
Share Creation Notification to the Receiving Server.  If provisioning
fails, the OCM Server MUST NOT create the Share: otherwise the Receiving
Party would be notified of a Share whose Resource access cannot work.

## Revocation and Expiration

The OCM Server SHOULD send a Share Revocation Request whenever a Share
ends, whatever the cause: unshared by the Sending Party, declined by the
Receiving Party (e.g. on receipt of a `SHARE_DECLINED` notification), or
administratively removed.

Revocation is deliberately fire-and-forget: because it is idempotent on
the Protocol Server side, the OCM Server MAY retry it at any time, and a
failure to deliver it MUST NOT block the unshare operation on the OCM
Server.

The Protocol Server SHOULD apply its own bounds on Share Record lifetime
as a backstop against missed revocations:

* If the provisioned Share carries an `expiration`, the Protocol Server
SHOULD stop serving the Share at that time.
* The Protocol Server MAY additionally expire Share Records after an
implementation-defined maximum lifetime; an OCM Server can always
re-provision (idempotently) to extend it.

Note that token expiry alone already limits the damage of a missed
revocation on bearer-token protocols: once the OCM Server stops issuing
fresh tokens for a Share, access ends when the last issued token
expires.

## Lifecycle in Self-Contained Integration

Self-Contained Integration has no provisioning step and no revocation
push.  The Share's lifecycle is enforced entirely at token issuance:

* The OCM Server MUST stop issuing tokens for a Share when it ends,
whatever the cause: unshared by the Sending Party, declined by the
Receiving Party, expired, or administratively removed.
* Until the last issued token expires, the Protocol Server will continue
to honor it.  Revocation latency is therefore bounded by the maximum
token lifetime, which is why the issuance rules require short-lived
tokens in this mode.

Because the Protocol Server keeps no per-share state, there is nothing
for it to expire or reap.  Protocols that do allocate per-share state
are steered to Provisioned Integration (see Integration Modes); a
Protocol Server that nevertheless creates transient state in this mode
(such as login sessions) SHOULD bound its lifetime independently of the
tokens that created it.

## Lifecycle in Introspected Integration

Introspected Integration needs neither provisioning nor a revocation
push for credential validity: every authorization consults the OCM
Server, modulo response caching, so a revoked or expired Share stops
being served as soon as cached introspection responses expire.
Revocation latency is bounded by the `exp` horizon of the responses,
which the introspection endpoint MUST keep short (see Token
Introspection).

Note that introspection only validates credentials.  If the Protocol
Server allocates per-share resources, it still needs the Share
Revocation Request of Provisioned Integration to release them, which is
one reason the two modes compose.

# Security Considerations

## No Secret Replication

A central design goal of OCM-IP is that delegating protocol work does
not multiply the places where secrets live:

* The `sharedSecret` of a Share is never stored on the Protocol Server:
it is stripped from the provisioning payload and absent from the
`ocm_ip` claim.  A compromise of the Protocol Server therefore does not
leak credentials that could be exchanged for tokens at the OCM Server's
`tokenEndPoint`.  (In Introspected Integration the Receiving Server does
present the legacy secret on the front channel; the Protocol Server
forwards it for introspection but MUST NOT retain it beyond the
request.)
* No pairing secret exists; the back channel is authenticated by HTTP
Message Signatures against published keys, the front channel by JWT
signatures against the same keys, and introspection requests by HTTP
Message Signatures against the Protocol Server's published keys.
* The Protocol Server holds no signing keys for this protocol, with two
exceptions: a Protocol Server using Introspected Integration holds a
request-signing key, published at its own `/.well-known/jwks.json`, and
a delegated Token Server (sketched in the note on delegating the token
endpoint) holds its own token-signing key, whose public part is
published through the OCM Server's JWKS.

The Protocol Server does handle bearer access tokens on the front
channel.  These MUST be treated as confidential, MUST NOT be placed in
URLs, and SHOULD NOT be logged or persisted beyond their lifetime,
consistent with the Code Flow considerations of [OCM].

## Legacy Shared-Secret Access Requires Introspection

Without the Code Flow, the only credential is the long-lived
`sharedSecret` itself, which the Receiving Server presents directly on
the front channel.  The Protocol Server cannot verify it on its own: the
secret is deliberately never replicated to it.  A Protocol Server MUST
NOT accept any front-channel credential other than a verifiable access
token or a credential validated through Token Introspection (or, for
SSH, the public-key mechanism of [OCM]).

Introspected Integration therefore reintroduces, deliberately and only
for compatibility, the per-request coupling to the OCM Server that the
other modes remove.  Deployments that do not need to serve legacy
Receiving Servers SHOULD NOT enable it.

The introspection endpoint is a sensitive interface: left
unauthenticated, it would let anyone test guessed or stolen credentials
for validity (Section 4 of [RFC7662]).  The signature and pairing
requirements of the Token Introspection section are therefore mandatory,
and the endpoint SHOULD additionally rate-limit failed introspections
per caller.

## Trust Granted to the Paired OCM Server

Pairing grants the OCM Server significant power over the Protocol
Server: every accepted Share Provisioning Request may consume resources
(storage, compute sessions) and instructs the Protocol Server to serve
content to third parties.  The allowlist is therefore REQUIRED, and an
empty allowlist means the Integration API rejects all requests.

The Protocol Server SHOULD apply resource limits per paired OCM Server
(number of Share Records, concurrent sessions, storage) so that a
misbehaving or compromised OCM Server cannot exhaust it.

Conversely, the OCM Server places trust in the Protocol Server to
enforce the permissions and identity bindings of this document.
Operators SHOULD treat the Protocol Server as part of the Sending
Server's trusted computing base for the protocols it serves.

## Self-Contained Tokens

Self-Contained Integration shifts all authority into the token, with
three major consequences:

* Revocation latency.  An issued token cannot be withdrawn; it can only
expire.  The normative cap on token lifetime in the issuance rules is
what keeps "unshare" meaningful in this mode, and implementations MUST
NOT relax it by issuing long-lived self-contained tokens for
convenience.
* Metadata exposure.  The `ocm_ip` claim is readable by anyone who holds
the token.  For `webapp` Shares in particular, the token transits the
Receiving Party's user agent, so the embedded Share metadata is visible
to the Receiving Party.  The OCM Server MUST NOT place information in
the `ocm_ip` claim that the Receiving Party is not entitled to see, and
SHOULD keep the claim minimal.
* Allowlist is mandatory.  In Provisioned Integration, pairing is
implicitly enforced by the existence of the Share Record.  In
Self-Contained Integration the issuer allowlist is the only thing
standing between any internet-hosted JWKS and Resource access; the
requirement to check the token's issuer against the pairing allowlist
before honoring an `ocm_ip` MUST be enforced.

Provisioned and Self-Contained Integration MUST NOT be mixed for a
single Share.  If a provisioned Share's tokens also carried `ocm_ip`
claims, a token issued before a Share Revocation Request would continue
to grant access through the self-contained path until it expired,
silently surviving the revocation.  This is why the issuance rules
forbid the `ocm_ip` claim on tokens for provisioned Shares, and why
verification gives an existing Share Record precedence over the claim.
Introspected Integration, by contrast, composes safely with Provisioned
Integration: the introspection response names the Share Record via
`client_id`, and revocation of the record takes effect immediately.

## Signature and Token Verification Considerations

All the verification rules of [OCM] for HTTP Message Signatures apply to
the back channel, in particular: exactly one `ocm`-labeled signature,
required covered components, `created` freshness, `keyid` domain
matching the sender domain, and rejection of symmetric algorithms.  Two
considerations deserve emphasis in the Protocol Server context:

* Reverse proxies: when TLS terminates in front of the Protocol Server,
the internally observed URI differs from the signed `@target-uri`.  The
Protocol Server MUST reconstruct the public URL for verification, and
MUST only trust forwarding headers set by its own proxy.
* Issuer/key binding: on the front channel, the key used to verify a
token MUST be fetched from the JWKS of the token's own `iss` host, and
the Share Record lookup MUST use that same host.  An implementation that
verifies against one domain's keys but looks up records under another's
would allow cross-tenant confusion on multi-tenant Protocol Servers.

## Denial of Service

The Integration API performs the allowlist check before fetching any
keys, so unsolicited requests from arbitrary servers are rejected
without outbound traffic.  Front-channel token verification does fetch
JWKS documents from token-asserted issuers; implementations SHOULD
rate-limit verification failures and SHOULD restrict JWKS fetching to
the domains of paired OCM Servers, since no unpaired issuer's credential
can ever be honored in any integration mode.  In Introspected
Integration the Protocol Server additionally generates one introspection
request per uncached front-channel credential; implementations SHOULD
apply negative caching with a short lifetime so that a flood of invalid
credentials does not translate into a flood of introspection traffic
towards the OCM Server.

# IANA Considerations

## JSON Web Token Claims Registry

The following claim is to be registered in the "JSON Web Token Claims"
registry (using the template from [RFC7519]): Claim Name: ocm_ip Claim
Description: Open Cloud Mesh Share information for self-contained
Protocol Server integration Change Controller: IETF Specification
Document(s): the present Draft, once in RFC form

## OAuth Token Introspection Response Registry

The following member is to be registered in the "OAuth Token
Introspection Response" registry established by [RFC7662]: Name: ocm_ip
Description: Open Cloud Mesh Share information for Protocol Server
integration Change Controller: IETF Specification Document(s): the
present Draft, once in RFC form

No other IANA actions are required.  Neither the Integration API nor the
introspection endpoint is exposed at a Well-Known URI; their locations
are exchanged during pairing.

# Copying conditions

The author(s) agree to grant third parties the irrevocable right to
copy, use and distribute the work, with or without modification, in any
medium, without royalty, provided that, unless separate permission is
granted, redistributed modified works do not contain misleading author,
version, name of work, or endorsement information.

# References

## Normative References

[OCM] Lo Presti, G., de Jong, M.B., Baghbani, M. and Nordin, M.  "[Open
Cloud Mesh](
https://datatracker.ietf.org/doc/draft-ietf-ocm-open-cloud-mesh/)", Work
in Progress.

[RFC2119] Bradner, S. "[Key words for use in RFCs to Indicate
Requirement Levels](https://datatracker.ietf.org/doc/html/rfc2119)",
March 1997.

[RFC7517] Jones, M., "[JSON Web Key (JWK)](
https://datatracker.ietf.org/doc/html/rfc7517)", May 2015.

[RFC7519] Jones, M., Bradley, J., Sakimura, N., "[JSON Web Token
(JWT)](https://datatracker.ietf.org/doc/html/rfc7519)", May 2015.

[RFC7662] Richer, J. (ed), "[OAuth 2.0 Token Introspection](
https://datatracker.ietf.org/doc/html/rfc7662)", October 2015.

[RFC8174] Leiba, B. "[Ambiguity of Uppercase vs Lowercase in RFC 2119
Key Words](https://datatracker.ietf.org/html/rfc8174)", May 2017.

[RFC8615] Nottingham, M. "[Well-Known Uniform Resource Identifiers
(URIs)](https://datatracker.ietf.org/doc/html/rfc8615)", May 2019.

[RFC9068] Bertocci, V., "[JSON Web Token (JWT) Profile for OAuth 2.0
Access Tokens](https://datatracker.ietf.org/doc/html/rfc9068)", October
2021.

[RFC9421] Backman, A., Richer, J. and Sporny, M. "[HTTP Message
Signatures](https://tools.ietf.org/html/rfc9421)", February 2024.

[RFC9530] Polli, R., Marwood, D., "[Digest Fields](
https://datatracker.ietf.org/doc/html/rfc9530)", February 2024.

## Informative References

[RFC4918] Dusseault, L. M. "[HTTP Extensions for Web Distributed
Authoring and Versioning]( https://datatracker.ietf.org/html/rfc4918/)",
June 2007.

[RFC6749] Hardt, D. (ed), "[The OAuth 2.0 Authorization Framework](
https://datatracker.ietf.org/html/rfc6749)", October 2012.

[RFC8693] Jones, M., Nadalin, A., Campbell, B., Bradley, J. and
Mortimore, C., "[OAuth 2.0 Token Exchange](
https://datatracker.ietf.org/doc/html/rfc8693)", January 2020.

# Appendix A: Examples

The first set of examples shows Provisioned Integration:
`cloud.example.org` is the OCM Server and `hub.example.org` is a
Protocol Server running a computational notebook platform, paired with
`cloud.example.org` and serving the `webapp` protocol.  Alice
(`alice@cloud.example.org`) shares a notebook with Bob
(`bob@receiver.example.org`).  Self-Contained and Introspected
Integration examples follow at the end.

## Share Provisioning Request

The OCM Server pushes the Share to the Protocol Server before notifying
the Receiving Server.  The body is the Share Creation Notification with
every `sharedSecret` removed (line breaks in the signature headers for
display purposes only):

~~~
POST /services/ocm/shares HTTP/1.1
Host: hub.example.org
Date: Wed, 10 Jun 2026 14:00:00 GMT
Content-Type: application/json
Content-Digest: sha-256=:hj3LWOIuryd4XbzFhoHa6YMUbhtzMdMT3e9Bxpu2Lm0=:
Content-Length: 542
Signature-Input: ocm=("@method" "@target-uri" "content-digest"
"content-length" "date"); created=1781186400;
keyid="cloud.example.org#key1"; alg="ed25519"
Signature: ocm=:[signature-value]:

{
  "shareWith": "bob@receiver.example.org",
  "name": "analysis.ipynb",
  "providerId": "7c084226-d9a1-11e6-bf26-cec0c932ce01",
  "owner": "alice@cloud.example.org",
  "sender": "alice@cloud.example.org",
  "shareType": "user",
  "resourceType": "file",
  "protocol": {
    "name": "multi",
    "webdav": {
      "uri": "7c084226-d9a1-11e6-bf26-cec0c932ce01",
      "permissions": [
        "read",
        "write"
      ]
    },
    "webapp": {
      "uri": "https://hub.example.org/services/ocm/open",
      "viewMode": "write"
    }
  }
}
~~~
{: type="http"}

The Protocol Server stores the Share Record under (`cloud.example.org`,
`7c084226-d9a1-11e6-bf26-cec0c932ce01`) and responds:

~~~
HTTP/1.1 201 Created
Content-Type: application/json

{ "status": "stored" }
~~~
{: type="http"}

The OCM Server then sends the Share Creation Notification to
`receiver.example.org` per [OCM], with `must-exchange-token` in the
protocol requirements and with the `webapp` entry pointing at the
Protocol Server (and a fresh `sharedSecret`, which only the Receiving
Server learns).

## Access Token

When the Receiving Server performs the Code Flow at
`https://cloud.example.org/ocm/token`, the issued JWT carries the JOSE
header:

~~~ json
{
  "typ": "at+jwt",
  "alg": "EdDSA",
  "kid": "cloud.example.org#key1"
}
~~~

and the Claims Set:

~~~ json
{
  "iss": "https://cloud.example.org",
  "sub": "alice",
  "aud": "bob@receiver.example.org",
  "client_id": "7c084226-d9a1-11e6-bf26-cec0c932ce01",
  "iat": 1781186460,
  "exp": 1781190060,
  "jti": "f3b9c0aa-2f6e-4d57-9d24-6f0a1f6d9b11"
}
~~~

## Front-Channel Access

Bob's user agent form-POSTs the token to the advertised `webapp`
endpoint:

~~~
POST /services/ocm/open HTTP/1.1
Host: hub.example.org
Content-Type: application/x-www-form-urlencoded

access_token=eyJ0eXAiOiJhdCtqd3QiLCJhbGciOiJFZERTQSIs...
~~~
{: type="http"}

The Protocol Server verifies the JWT against
`https://cloud.example.org/.well-known/jwks.json`, looks up the Share
Record by (`cloud.example.org`,
`7c084226-d9a1-11e6-bf26-cec0c932ce01`), checks that
`alice@cloud.example.org` equals the stored `owner` and that
`bob@receiver.example.org` equals the stored `shareWith`, and then
starts (or resumes) the notebook session for the Share.

## Share Revocation Request

When Alice unshares the notebook (body shown without the signature
headers, which are as in the provisioning example):

~~~
POST /services/ocm/revoke HTTP/1.1
Host: hub.example.org
Content-Type: application/json

{
  "sender": "alice@cloud.example.org",
  "providerId": "7c084226-d9a1-11e6-bf26-cec0c932ce01"
}
~~~
{: type="http"}

~~~
HTTP/1.1 200 OK
Content-Type: application/json

{ "status": "revoked" }
~~~
{: type="http"}

A repeated revocation for the same `providerId` returns `{ "status":
"gone" }` with HTTP status 200.

## Self-Contained Integration

`dav.example.org` is a stateless WebDAV gateway in front of an existing
storage system, paired with `cloud.example.org` for Self-Contained
Integration.  No provisioning takes place; the gateway exposes no
Integration API and keeps no Share Records.  Alice shares a folder with
Bob, and the OCM Server advertises a `webdav` endpoint at the gateway in
the Share Creation Notification.

When the Receiving Server performs the Code Flow at
`https://cloud.example.org/ocm/token`, the issued JWT carries:

~~~ json
{
  "iss": "https://cloud.example.org",
  "sub": "alice",
  "aud": "bob@receiver.example.org",
  "client_id": "receiver.example.org",
  "iat": 1781186460,
  "exp": 1781186760,
  "jti": "0d9e3c4b-5a6f-4e21-8c37-2b1a9f8e7d65",
  "ocm_ip": {
    "providerId": "9b2e41d7-aa31-4a02-9f0d-3c5e8b7a6f10",
    "resourceType": "folder",
    "name": "dataset-2026",
    "protocol": {
      "webdav": {
        "uri": "9b2e41d7-aa31-4a02-9f0d-3c5e8b7a6f10",
        "permissions": ["read"]
      }
    }
  }
}
~~~

Note the short lifetime (300 seconds): the Receiving Server re-exchanges
the `sharedSecret` at the `tokenEndPoint` for a fresh token before each
expiry, per [OCM], and unsharing takes effect within at most that
lifetime.

The Receiving Server accesses the Resource directly:

~~~
PROPFIND /dav/9b2e41d7-aa31-4a02-9f0d-3c5e8b7a6f10 HTTP/1.1
Host: dav.example.org
Authorization: Bearer eyJ0eXAiOiJhdCtqd3QiLCJhbGciOiJFZERTQSIs...
Depth: 1
~~~
{: type="http"}

The gateway verifies the JWT against
`https://cloud.example.org/.well-known/jwks.json`, finds no Share Record
for (`cloud.example.org`, `receiver.example.org`), confirms that
`cloud.example.org` is paired for Self-Contained Integration, and serves
the PROPFIND read-only, scoped to the `uri` in the `ocm_ip` claim.

## Introspected Integration

`legacy.example.com` is a Receiving Server that does not support the
`exchange-token` capability.  Alice shares the same kind of folder with
Carol (`carol@legacy.example.com`).  The Share Creation Notification is
a legacy [OCM] share: the `webdav` entry points at `dav.example.org` and
carries a `sharedSecret`, with no `must-exchange-token` requirement.
`dav.example.org` is paired with `cloud.example.org` for Introspected
Integration and holds a request-signing key published at
`https://dav.example.org/.well-known/jwks.json`.

The Receiving Server presents the secret directly, per the legacy
resource access flow of [OCM]:

~~~
PROPFIND /dav/4f6a2c81-77b0-4c0e-9e64-1d2f3a5b6c7d HTTP/1.1
Host: dav.example.org
Authorization: Bearer shr-9wq4xkz7vmd2
Depth: 1
~~~
{: type="http"}

The credential does not parse as a JWT, so the gateway introspects it
(signature headers as in the provisioning example, but signed by the
gateway with keyid="dav.example.org#key1"):

~~~
POST /ocm/introspect HTTP/1.1
Host: cloud.example.org
Content-Type: application/x-www-form-urlencoded

token=shr-9wq4xkz7vmd2
~~~
{: type="http"}

~~~
HTTP/1.1 200 OK
Content-Type: application/json

{
  "active": true,
  "iss": "https://cloud.example.org",
  "sub": "alice",
  "aud": "carol@legacy.example.com",
  "exp": 1781186760,
  "ocm_ip": {
    "providerId": "4f6a2c81-77b0-4c0e-9e64-1d2f3a5b6c7d",
    "resourceType": "folder",
    "name": "dataset-2026",
    "protocol": {
      "webdav": {
        "uri": "4f6a2c81-77b0-4c0e-9e64-1d2f3a5b6c7d",
        "permissions": [
          "read"
        ]
      }
    }
  }
}
~~~
{: type="http"}

The gateway serves the PROPFIND read-only and MAY cache this response
until `exp`.  When Alice unshares the folder, introspection starts
returning `{"active": false}`, and Carol's access ends as soon as the
cached response expires.

# Changes

This section collects the changes with respect to the previous version
in the IETF datatracker.  It is meant to ease the review process and it
shall be removed when going to RFC last call.

## Version 00

* Initial version.

# Acknowledgements

This protocol generalizes a working integration between Nextcloud and
JupyterHub developed at SUNET, and builds directly on the Code Flow, JWT
access token, and HTTP Message Signature work in the Open Cloud Mesh
specification.  Thanks to the OCM community for the discussions that
shaped the webapp sharing design this document extends, and in
particular to Enrique Pérez Arnaud and Matthias Kraus who helped shape
the format of this protocol. 

Work on this document has been funded by [Sovereign Tech Agency][sta]
through the [Tech Fund][sta-fund], with a specific [project][sta-ocm].

[sta-ocm]: https://www.sovereign.tech/tech/open-cloud-mesh

[sta-fund]: https://www.sovereign.tech/programs/fund

--- back
