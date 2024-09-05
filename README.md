# Open Cloud Mesh Protocol Specification

![Open Cloud Mesh Protocol Specification](logo.png)

This repository contains the specification of the Open Cloud Mesh protocol, including
the [OpenAPI](https://github.com/OAI/OpenAPI-Specification) (fka Swagger) specification for its API. This specification describes disovery and use of the RESTful API endpoints, request and response headers, possible response codes, request and response formats, hypermedia controls, error handling, and other API design best practices which vendors should support to make sharing of resources between different vendors possible.

* [Scope and assumptions](#scope-and-assumptions)
* [Specification](#specification)
  * [Discovery](#discovery)
  * [Share Creation](#create)
  * [Share Acceptance](#accept)
  * [Share Access](#access)
  * [Share Deletion](#unshare)
  * [Share Updating](#update)
  * [Resharing](#reshare)
  * [Invite](#invite)
  * [Signing Request](#signing-request)

* [Contributing](#contributing)

## Scope and assumptions

* For the core sharing functionality, the provider knows the consumer (both endpoint and user) when it creates a share with the consumer (also see [#26](https://github.com/cs3org/OCM-API/issues/26)). In addition, an optional invitation workflow is available in this specification (see below), which gives the consumer a way to automatically trust a provider (and vice versa). The [ScienceMesh](https://sciencemesh.io) infrastructure provides a managed white list of trusted federated sites.
* Consumer doesn't have to accept a share, the resource will be available to the consumer immediately ([#25](https://github.com/cs3org/OCM-API/issues/25)).
* Dealing with incoming shares is a vendor specific implementation. One vendor might use an 'accept before' process while another vendor might use a 'decline after' approach. This is considered part of the UX and thus not part of the interaction between different vendors. However, the consumer could notify the provider by using the introduced `/notifications` endpoint (also see [#27](https://github.com/cs3org/OCM-API/issues/27)).
* Reverting access to outgoing shares is a vendor specific implementation. One vendor might delete an entire share while another might invalidate an access token. This is considered part of vendor-specific internals and thus not part of the interaction between different vendors. However, the provider could notify the consumer by using the introduced `/notifications` endpoint (also see [#27](https://github.com/cs3org/OCM-API/issues/27)).
* The actual file sync is not part of this specification. To keep this specification 'future proof', the file sync protocol will be embedded as a separate object in Open Cloud Mesh API calls. This protocol object contains all protocol specific options, e.g. WebDAV specific options.

## Specification
### Introduction
Open Cloud Mesh is a  server federation protocol that is used to notify a remote user that they have
been granted access to some resource. It has similarities with authorization flows such as OAuth, as well as with social internet protocols such as ActivityPub and email.

### Terms
We define the following concepts (with some non-normative references to related concepts from OAuth and elsewhere):
* __Resource__ - the piece of data or interaction to which access is being granted
* __Share__ - a policy rule stating that certain actors are allowed access to a resource. Also: a record in a database representing this rule
* __Sending Party__ - a person or party who is authorized to create shares ("Resource Owner")
* __Receiving Party__ - a person, group or party who is granted access to the resource through the share ("Requesting Party / RqP" in OAuth-UMA)
* __Sending Server__ - the server that:
  * holds the resource ("file server", "Entreprise File Sync and Share (EFSS) server"),
  * provides access to it ("API"),
  * takes the decision to create the share based on user interface gestures from the sending user ("Authorization Server")
  * takes the decision about authorizing attempts to access the resource ("Resource Server")
  * send out share creation notifications when appropriate (see below)
* __Receiving Server__ - the server that:
  * receives share creation notifications (see below)
  * actively or passively notifies the receiving user or group of any incoming share creation notification
  * acts as an API client, allowing the receiving user to access the resource through an API (e.g. WebDAV) of the sending server
* __Sending Gesture__ - a user interface interaction from the Sending Party to the Sending Server, conveying the intention to create a share
* __Share Creation__ - the addition of a Share to the database state of the Sending Server, in response to a successful Sending Gesture or for another reason
* __Share Creation Notification__ - a server-to-server request from the sending server to the receiving server, notifying the receiving server that a share has been created
* __OCM Address__ - a string of the form `<Receiving Party's identifier>@<fqdn>` which can be used to uniquely identify a user or group "at" an OCM-capable server. `<Receiving Party's identifier>` is an opaque string,
unique at the server. `<fqdn>` is the Fully Qualified Domain Name by which the server is identified. This can, but doesn't need to be, the domain at which the OCM API of that server is hosted.
* __OCM Notification__ - a message from the Receiving Server to the Sending Server or vice versa, using the OCM Notifications endpoint.
* __Invite Message__ - out-of-band message used to establish contact between parties and servers in the Invite Flow, containing an Invite Token (see below) and the Invite Sender's OCM Address
* __Invite Sender__ - the party sending an Invite
* __Invite Receiver__ - the party receiving an Invite
* __Invite Sender OCM Server__ - the server holding an addressbook used by the Invite Sender, to which details of the Invite Receiver are to be added
* __Invite Receiver OCM Server__ - the server holding an addressbook used by the Invite Receiver, to which details of the Invite Sender are to be added
* __Invite Token__ - a hard-to-guess string used in the Invite Flow, generated by the Invite Sender OCM Server and linked uniquely to the Invite Sender's OCM Address
* __Invite Creation Gesture__ - gesture from the Invite Sender to the Invite Sender OCM Server, resulting in the creation of an Invite Token.
* __Invite Acceptance Gesture__ - gesture from the Invite Receiver to the Invite Receiver OCM Server, supplying the Invite Token as well as the OCM Address of the Invite Sender, effectively allowlisting the Invite Sender OCM Server for sending Share Creation Notifications to the Invite Receiver OCM Server.
* __Invite Acceptance Request__ - API call from the Invite Receiver OCM Server to the Invite Sender OCM Server, supplying the Invite Token as well as the OCM Address of the Invite Receiver, effectively allowlisting the Invite Sender OCM Server for sending Share Creation Notifications to the Invite Receiver OCM Server.
* __Invite Acceptance Response__ - HTTP response to the Invite Acceptance Request

### Discovery
Authentication between services is already established. This means that this specification doesn't cover the way a service authenticates incoming API calls (e.g. through an API Key, VPN connection or IP whitelisting). In this scope we assume that the services are already authenticated.

If a finite whitelist of receiver servers exists on the sender side, then this list may already contain all necessary endpoint details.

When a sending server allows sharing to any internet-hosted receiving server, then discovery can happen from the sharee address, using the `/.well-known/ocm` (or `/ocm-provider`, for backwards compatibility) URL that receiving servers SHOULD provide according to this [specification](https://cs3org.github.io/OCM-API/docs.html?branch=develop&repo=OCM-API&user=cs3org#/paths/~1.well-known~1ocm/get).

To ease the process of confirming the identity of a remote party, the discovery data MAY contain a public key: each incoming request that requires to origin from an authenticated source MUST be signed in its headers using the private key of that source, whose public key MUST be exposed in its discovery data.

To fill the gap between users knowning other peers' email addresses of the form `user@provider.org`, and the actual cloud storage endpoints being in the form `https://my-cloud-storage.provider.org`, a further discovery mechanism MAY be provided in case hosting https://provider.org/.well-known/ocm is impractical, based on DNS `SRV` Service Records.

* If e.g. https://provider.org/.well-known/ocm does not exist, a provider MAY instead point to e.g. https://my-cloud-storage.provider.org/.well-known/ocm by ensuring that a `type=SRV` DNS query to `_ocm._tcp.provider.org` resolves to e.g. `service = 10 10 443 my-cloud-storage.provider.org`
* When requested to discover the EFSS endpoint for `user@provider.org`, if https://provider.org/.well-known/ocm can not be fetched, implementations SHOULD fall back to querying the corresponding `_ocm._tcp.domain` DNS record, e.g. `_ocm._tcp.provider.org`, and subsequently make a HTTP GET request to the host returned by that DNS query, followed by the `/.well-known/ocm` URL path.

### Share Creation
To create a share, the sending server SHOULD make a HTTP POST request to the `/shares` endpoint of the receiving server ([docs](https://cs3org.github.io/OCM-API/docs.html?branch=develop&repo=OCM-API&user=cs3org#/paths/~1shares/post)).

### Share Acceptance
In response to a share creation, the receiving server MAY send back a [notification](https://cs3org.github.io/OCM-API/docs.html?branch=develop&repo=OCM-API&user=cs3org#/paths/~1notifications/post) to the sending server, with  `notificationType` set to `"SHARE_ACCEPTED"` or `"SHARE_DECLINED"`. The sending server MAY expose this information to the end user.

### Share Access
To access a share, the receiving server MAY use multiple ways, depending on the received payload and on the `protocol.name` property:

* If `protocol.name` = `multi`, the receiver MUST make a HTTP PROPFIND request to `protocol.webdav.uri` to access the remote share. If `protocol.webdav.sharedSecret` is not empty, the receiver MUST pass it as a `Authorization: bearer` header.
Otherwise, if `protocol.webdav.code` is not empty, the receiver SHOULD discover the sender's OCM endpoint and make a signed POST request to `<OCM endpoint>/token`, to exchange
the code for a short-lived bearer token,
and then use that bearer token to access the remote share.

* If `protocol.name` = `webdav`, the receiver SHOULD inspect the `protocol.options` property. If it contains a `sharedSecret`, as in the [legacy example](https://cs3org.github.io/OCM-API/docs.html?branch=develop&repo=OCM-API&user=cs3org#/paths/~1shares/post), then the receiver SHOULD make a HTTP PROPFIND request to `https://<sharedSecret>:@<host><path>`, where `<host>` is the remote server, and `<path>` is obtained by querying the [Discovery](#discovery) endpoint at the remote server and getting `resourceTypes[0].protocols.webdav`. Note that this access method is _deprecated_ and may be removed in a future release of the Protocol.

In both cases, when the share is a folder and the receiver accesses a resource within the share, it SHOULD append its relative path to that URL.

Additionally, if `protocol.<protocolname>.permissions` include `mfa-enforced`, the receiving host MUST ensure that the user accessing the resource has been authenticated with MFA.

### Share Deletion
A `"SHARE_ACCEPTED"` notification followed by a `"SHARE_UNSHARED"` notification is
equivalent to a `"SHARE_DECLINED"` notification.

### Share Updating
TODO: document `"RESHARE_CHANGE_PERMISSION"`

### Resharing
The `"REQUEST_RESHARE"` and `"RESHARE_UNDO"` notification types MAY be used by the
receiving server to persuarde the sending server to share the same resource with another share recipient.
TODO: document how receiver.com can know if sender.com understood and processed the
reshare request.

### Invite
If Alice (`alice at sender.com`) and Bob (`bob at receiver.com`) know each other, yet they may not have a mechanism to trust any received share request, as that may be similar to receiving spam.

In this case, Alice may invite Bob to initiate a mutual trust relationship: on the provider side, the `sender.com` service MAY implement an interface for Alice to generate a single-use token and send it to Bob off-band (e.g. via e-mail). In addition, the `sender.com` service MAY integrate this interface with [ScienceMesh](https://sciencemesh.io), and only allow a curated white list of sites as receivers.

On the receiving end, assuming that Bob wishes to accept the invitation, the receiving server MAY provide an interface for Bob to input the received token, or to interact with the ScienceMesh directory. In any case, the receiving server SHOULD make a HTTP POST request to the [/invite-accepted](https://cs3org.github.io/OCM-API/docs.html?branch=develop&repo=OCM-API&user=cs3org#/paths/~1invite-accepted/post) endpoint of the sending server, sending the token and disclosing Bob's identity details such as `bob at receiver.com`. If the token matches the one created earlier by Alice, the response MUST include Alice's identity details such as `alice at sender.com`.

Following this step, both services at `sender.com` and `receiver.com` MAY display, respectively, `bob` and `alice` as trusted or white-listed contacts, and enable sharing between them. Sites MAY enforce a policy to only accept shares between such trusted contacts, or MAY display a warning to users when a share from an unknown party is received.

For further details on this concept, see also [#54](https://github.com/cs3org/OCM-API/pull/54) and related issues. For a discussion about trust policies, see [sciencemesh#196](https://github.com/sciencemesh/sciencemesh/issues/196).

### Multi Factor Authentication
If an OCM provider exposes the capability `/mfa-capable`, it indicates that it will try and comply with a MFA requirement set as a permission on a share. If the sharer OCM provider trusts the receiver OCM provider, the sharer MAY set the permission `mfa-enforced` on a share, which SHOULD be honored. A compliant OCM provider that signals that it is MFA-capable MUST not allow access to a resource protected with the `mfa-enforced` permission, if the consumer has not provided a second factor to establish their identity with greater confidence.

Since there is no way to guarantee that the sharee OCM provider will actually enforce the MFA requirement, it is up to the sharer OCM provider to establish a trust with the OCM sharee provider such that it is reasonable to assume that the sharee OCM provider will honor the MFA requirement. This establishment of trust will inevitably be implementation dependent, and can be done for example using a pre approved allow list of trusted OCM providers. The procedure of establishing trust is out of scope for this specification: a mechanism similar to the [ScienceMesh](https://sciencemesh.io) integration for the [Invite](#invite) capability may be envisaged.


## Signing request

A request is signed by adding the signature in the headers. The sender also needs to expose the public key used to generate the signature. The receiver can then validate the signature and therefore the origin of the request.
To help debugging, it is recommended to also add all properties used in the signature as headers, even if they can easily be re-generated from the payload.

Note: Signed requests prove the identity of the sender but does not encrypt nor affect its payload.

Here is an example of headers needed to sign a request.

```
  {
    "(request-target)": "post /path",
    "content-length": 380,
    "date": "Mon, 08 Jul 2024 14:16:20 GMT",
    "digest": "SHA-256=U7gNVUQiixe5BRbp4Tg0xCZMTcSWXXUZI2\\/xtHM40S0=",
    "host": "hostname.of.the.recipient",
    "Signature": "keyId=\"https://author.hostname/key\",algorithm=\"rsa-sha256\",headers=\"content-length date digest host\",signature=\"DzN12OCS1rsA[...]o0VmxjQooRo6HHabg==\""
  }
```

- '(request-target)' contains the reached endpoint and the used method,
- 'content-length' is the total length of the payload of the request,
- 'date' is the date and time when the request has been sent,
- 'digest' is a checksum of the payload of the request,
- 'host' is the hostname of the recipient of the request (remote when signing outgoing request, local on incoming request),
- 'Signature' contains the signature generated using the private key and details on its generation:
  * 'keyId' is a unique id, formatted as an url. hostname is used to retrieve the public key via custom discovery
  * 'algorithm' specify the algorithm used to generate signature
  * 'headers' specify the properties used when generating the signature
  * 'signature' the signature of an array containing the properties listed in 'headers'. Some properties like content-length, date, digest, and host are mandatory to protect against authenticity override.


### How to generate the Signature for outgoing request

After properties are set in the headers, the Signature is generated and added to the list.

This is a quick PHP example of headers for outgoing request:

```php
    $headers = [
        '(request-target)' => 'post /path',
        'content-length' => strlen($payload),
        'date' => gmdate('D, d M Y H:i:s T'),
        'digest': 'SHA-256=' . base64_encode(hash('sha256', utf8_encode($payload), true)),
        'host': 'hostname.of.the.recipient',
    ];

    openssl_sign(implode("\n", $headers), $signed, $privateKey, OPENSSL_ALGO_SHA256);
		
    $signature = [
        'keyId' => 'https://author.hostname/key',
        'algorithm' => 'rsa-sha256',
        'headers' => 'content-length date digest host',
        'signature' => $signed
    ];

    $headers['Signature'] = implode(',', $signature);
```


### How to confirm Signature on incoming request

The first step would be to confirm the validity of each properties:

- '(request-target)' and 'host' are immutable to the type of the request and the local/current host,
- 'content-length' and 'digest' can be re-generated and compared from the payload of the request,
- A maximum TTL must be applied to 'date' and current timestamp,
- regarding data contained in the 'Signature' header:
  * using 'keyId' to get the public key from remote signatory,
  * 'headers' is used to generate the clear version of the signature and must contain at least 'content-length', 'date', 'digest' and 'host',
  * 'signature' is the encrypted version of the signature.

Here is an example of how to verify the signature using the headers, the signature and the public key:

```php
    $clear = [
        '(request-target)' => 'post /path',
        'content-length' => strlen($payload),
        'date' => 'Mon, 08 Jul 2024 14:16:20 GMT',
        'digest': 'SHA-256=' . base64_encode(hash('sha256', utf8_encode($payload), true)),
        'host': $localhost
    ];

    $signed = "DzN12OCS1rsA[...]o0VmxjQooRo6HHabg==";
    if (openssl_verify(implode("\n", $clear), $signed, $publicKey, 'sha256') !== 1) {
        throw new InvalidSignatureException('signature issue');
    }
```

### Validating the payload

Following the validation of the signature, the host should also confirm the validity of the payload, that is ensuring that the actions implied in the payload actually initiated on behalf of the source of the request.

As an example, if the payload is about initiating a new share the file owner has to be an account from the instance at the origin of the request.


## Changelog

[Available here](CHANGELOG.md)


## Contributing

The specification can be rendered as HTML documentation using [ReDoc](https://github.com/Redocly/redoc) and is available as follows:

* [version 1.1](https://cs3org.github.io/OCM-API/docs.html?branch=v1.1.0&repo=OCM-API&user=cs3org#/paths/~1shares/post) - current official version, supported by ScienceMesh
* [version 1.0](https://cs3org.github.io/OCM-API/docs.html?branch=v1.0.0&repo=OCM-API&user=cs3org#/paths/~1shares/post) - first official and supported version

The current developments yet to be released are available in the [develop branch](https://cs3org.github.io/OCM-API/docs.html?branch=develop&repo=OCM-API&user=cs3org)

The Open Cloud Mesh API specification is an open source, community-driven project. If you'd like to contribute, please follow the [Contributing Guidelines](CONTRIBUTING.md).

To stage the changes of your PR, you can change the repo and branch in the URL.
For instance to see the proposed changes of https://github.com/cs3org/OCM-API/pull/41, use:
[https://cs3org.github.io/OCM-API/docs.html?branch=add-endpoint-to-accept-invite&repo=OCM-API&user=LovisaLugnegard](https://cs3org.github.io/OCM-API/docs.html?branch=add-endpoint-to-accept-invite&repo=OCM-API&user=LovisaLugnegard)
