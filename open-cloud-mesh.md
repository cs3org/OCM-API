Open Cloud Mesh (OCM) is a server federation protocol that is used to notify a remote user that they have
been granted access to some resource. It has similarities with authorization flows such as OAuth, as well as with social fediverse protocols such as ActivityPub.

# creating a share
Suppose Alice has an account on a sending server (sender.com) and Bob has an account on a receiving server (receiver.com).
The receiving server is registered as an API client of the sending server.
Alice gestures that she wants to grant Bob access to a given resource, and wants him to be notified of this.
In this scenario, support that the sending server knows the OCM endpoint of the receiving server (say `https://receiver.com/ocm`), and also knows some identifier of Bob's account at that server (say `bob-153`).
The sending and receiving server also know each other's public key for http signatures.
To send the notification, the sending server:
* determines the public uri (say `https://sender.com/webdav/some/folder/`) and protocol (say `webdav`) through which the receiving server will be able to access the resource
* generates a unique code, say '123456',
* makes a POST request to the `/shares` path within the receiving server's OCM API, with a JSON body
* includes at least the following fields in that JSON body:
```http
POST /ocm/shares
Host: receiver.com
Content-Type: application/json
[...]

{
  "shareWith": "bob-153@receiver.com",
  "code": "123456",
  "protocol": {
    "webdav": {
        "uri": "https://sender.com/webdav/some/folder/"
    }
  }
}
```
* generates and adds http signature headers as described in [draft-cavage-http-signatures-12](https://datatracker.ietf.org/doc/html/draft-cavage-http-signatures-12)

# share creation request fields
The JSON object in the `/shares` POST body can have the following fields:
* REQUIRED `shareWith` - of the form `<receiver_id>@<fqdn>`, where `<receiver_id>` SHOULD be a user or group identifier, and `<fqdn>` should be the fully qualified domain name
of the receiving server.
* REQUIRED `code` - SHOULD contain a string that can be exchanged for a short-lived bearer token and refresh token using a signed POST to the sending server's `tokenEndpoint`. See "obtaining a bearer token" below.
* REQUIRED `protocol` - SHOULD have one or more sub-objects, as per the OCM protocol registry (see below).
* OPTIONAL `shareType` - can be omitted, or set to 'user', 'group' or 'federation', to add information to the `<receiver_id>` part of the `shareWith` field.
* OPTIONAL `name` - can be used in a notification to the receiving user(s), could be authored by the sender or generated automatically from for instance the file name and path of the resource being shared.
* OPTIONAL `resourceType` - can be for instance 'file' or 'folder', or other types depending on the protocol field.
* OPTIONAL `description` - human-readable string that describes the resource
* OPTIONAL `providerId` - identifier for this share, to be used to refer to it in notifications. Required if notifications are supported.
* OPTIONAL `sharedBy` - an identifier of the form `<sender_id>@<fqdn>` that describes the sending user or origin of this share.
* OPTIONAL `sharedByDisplayName` - a human-readable display name for the sending user or origin of this share.
* OPTIONAL `owner` - an identifier of the form `<sender_id>@<fqdn>` that describes the main authority in control of the resource.
* OPTIONAL `ownerDisplayName` - a human-readable display name for the main authority in control of the resource.

# OCM protocol registry
## `webdav`
To indicate a resource can be accessed via the WebDAV protocol. It may contain:
* REQUIRED `URI` - URI of the resource. The receiving server SHOULD make sure this URI is on a domain that is under the sending server's control.
* DEPRECATED `sharedSecret` - version 1.1 implementations of OCM expect a long-lived bearer token to be directly included here. This is not recommended.
## `webapp`
[...]
## ...
[...]

# obtaining a bearer token
When the receiving server receives the request, it can obtain a bearer token by making a signed POST request to the `/token` path within the sending server's OCM API, with a JSON body:
```http
POST /ocm/token
Host: sender.com
Content-Type: application/json
request-target: post /ocm/token
Content-Length: 92
Host: localhost
Date: Tue, 03 Sep 2024 12:30:03 GMT
Digest: SHA-256=GgoXGmns9ORRxTwHEp8s4UJ6ehjaSQzHgxEbeBFE1is=
Signature: keyId="localhost",algorithm="rsa-sha256",headers="request-target,content-length,host,date,digest",signature="OSGjChaUHiHOfolJLkgdtjDIzeqdcZz42RciNtqaYH4DSifwl+qIoPvB/4ETTGTlizQvyJaPYYVuRWDJ/f+J/nW9FU+ZWahjsyIY/PYHY1ak3IAKUMCf/T/eoS67Tx6DtKCwj5tesN0r6LoMmakYYKNMD/2xM/2Mi8xl4pcPyWcoleRxG7uKsk8CBLahwiYs/OBPe4aJEX6pkdp7iYxTVVxMVOS9gJC/krJGgNx3fwBMPJ22aODRCEMsFnhgSKJPPlsu8hdIGx2A/HTQRI0Ys2Q7MV1Iq+V5vtX2tm9AqxdTxP1AxTHA1Zx38wXKQc5YrneGm4deI1Dph1/k95JyIQ=="

{
    "client_id": "receiver.com",
    "code": "123456"
}
```
To which the sending server's token endpoint could reply:
```json
{
   "access_token": "asdfgh",
   "token_type": "bearer",
   "expires_in": 3600,
   "refresh_token": "qwertyuiop" 
}
```
And with that, the receiving server could access the resource at its URI:
```http
GET /webdav/some/folder/
Host: sender.com
Authorization: Bearer asdfgh
```

This completes the description of the basic Open Cloud Mesh mechanism. The rest of this specification details optional extensions and legacy versions of it.

# legacy resource access
In OCM version 1.1, for the webdav protocol, the resource could be accessed using a WebDAV request to the URI specified in `protocol.webdav.URI`, adding
an `Authorization: Bearer <protocol.webdav.sharedSecret>` or `Authorization: Bearer <protocol.options.sharedSecret>` header.
In OCM version 1.0, for the webdav protocol, the resource could be accessed using a WebDAV request a previously agreed URI, adding
an `Authorization: Basic <base64(protocol.webdav.sharedSecret + ':')` or `Authorization: Basic <base64(protocol.options.sharedSecret + ':')>` header.
The `protocol.webdav.sharedSecret` and `protocol.options.sharedSecret` fields SHOULD NOT be included in a share creation request unless the receiving server
is known to support only older versions of OCM.
When received, they SHOULD NOT be used unless the sending server is known to support only older versions of OCM.

# dynamic client registration
Although OCM is useful in a closed community such as a continent-wide network of universities that mutually trust each other, it can also be used in open mode,
more like email or social networking, where a sending server is allowed to send an OCM share to ANY receiving server that understands it.

To enable this, the sending server needs to:
* discover information about the receiving server, either from a directory or by doing server config discovery (see below)

### server config discovery
From a fully qualified domain name, the sending and receiving servers could discover information about each other by fetching
`https://<fqdn>/.well-known/ocm` or (if that fails) `https://<fqdn>/ocm-provider`. If that also fails, they could try a DNS SRV
lookup of `_ocm._tcp.<fqdn>` which could then for instance resolve to `service = 10 10 443 <alt-fqdn>`, after which discovery
could be reattempted using `<alt-fqdn>` instead of `<fqdn>`.

The resulting configuration document can contain the following fields:
* REQUIRED `apiVersion` - SHOULD be one of `"1.0-proposal1"`, `"1.1.0"` or `"2.0"`
* REQUIRED `endPoint` - this was used instead as the base URL for all OCM requests like create-share, token, etc.
* OPTIONAL `capabilities` - array of strings indicating which capabilities this OCM server has. Example: `[ '/invite-accepted' ]`
* OPTIONAL `federation` - see https://github.com/cs3org/OCM-API/pull/94
* OPTIONAL `resourceTypes` - array of resource type objects, each with:
* OPTIONAL `resourceTypes[i].name` - string describing the type, for instance `"file"`
* OPTIONAL `resourceTypes[i].shareTypes` - array of strings describing the share types supported for this resource type, for instance `["user", "federated"]`
* OPTIONAL `resourceTypes[i].protocols` - object containing protocol API base URLs for various protocols
* OPTIONAL `provider` - a human-readable name for this server

# recipient user/group discovery, invites
The receiving server MAY expose a directory service for the sending server to discover potential recipient users and (federated) groups.
The servers MAY also share a directory service such as a community-administered Authorization and Authentication Infrastructure of which
both servers are a member, and where (federated) group information or user identifiers can be looked up.

## invites
Servers MAY also support the `/invite-accepted` capability, and if both the sending and the receiving server do, and both servers trust each other,
then the invite flow may be used to bootstrap common knowledge of user identifiers between the participating users. If supported, this optional capability of OCM servers
works as follows.

### send a unique string
Say Alice wants to initiate a connection with Bob, with the goal of discovering Bob's user identifier and OCM server, and at the same time sending her own user identifier and OCM server
information to Bob. Using an out-of-band communication channel (for instance email or voice), she shares a unique string with Bob. Bob passes this string on to his OCM server in some way.
This might involve opening a URL at a redirect server and finding his OCM server in a list, copy-pasting the string into a graphical user interface, scanning a QR code with a smartphone application, etcetera.

### server-to-server information exchange

The string contains the fully qualified domain name of Alice's OCM server, so Bob's server can use server config discovery (see above) to contact Alice's server. It can then make an `invite-accepted`
request to it (see [example](https://cs3org.github.io/OCM-API/docs.html?branch=v1.1.0&repo=OCM-API&user=cs3org#/paths/~1notifications/post)), sharing a unique user identifier for Bob.
Alice's server can respond and include a unique user identifier for Alice in the reply.

### contacts interface

Next time Alice wants to share a resource with Bob, she will not have to input Bob's full user identifier and OCM server FQDN into her OCM server's interface. Instead, she will be able to select Bob
from a list of contacts, and initiate the sharing from there.

# flows
## public link

Alice creates a public link for a resource on her account on server 1.
Bob visits the GUI of server 1 to view it, and clicks 'save to my cloud <bob@server2>'.
Since Bob has access to this resource, he is allowed to tell server 1 to share it forward, so server sends a notification to server 2.
Bob now visits the GUI of server 2 to accept the share there.

The fact that Bob is allowed to do this means Bob is essentially a resource owner for this resource on server 1.

So then it's not much different from the share-with flow.


The public link flow of OCM was developed independently from GNAP, but is very similar to
the RS-first Method of AS Discovery described in section 9.1 of [GNAP](https://datatracker.ietf.org/doc/draft-ietf-gnap-core-protocol/).

It can be interpreted as a client instance switching protocol: bob@server1 acts as an RO, registers server2 as a client instance, and grants bob@server2 access.

## share with

Share with flow is similar but Alice is the RO who vets and registers server2 as a client instance, and triggers a notification.
It uses a specific implementation of GNAP notifications, and a specific implementation of GNAP client instance discovery in case the
client instance to which the notification is addressed is not (yet) registered at the AS.

Client instance registration may happen on the fly.

Scenario 1: only pre-trusted receiving servers.
Scenario 2: dynamic client instance registration as part of invite accepting.
Scenario 3: client instance discovery triggered by RO.

# accept/reject/revoke notifications
# reshare notifications

# show users with access
# public link that doesn't expose the document itself
Like DOI
Request an invite to something
