Open Cloud Mesh (OCM) is a server federation protocol that is used in practice in various ways.
This document describes how existing servers implement it. There are three authorization flows: public link, invite, and share with.


# creating a share, using httpsig+bearer tokens
# other / multiple protocols, extra (legacy) fields
# dynamic client registration, discovery (/.well-known/ocm, /ocm-provider, DNS SRV)
# recipient user/group discovery, invites
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

### Details of GNAP notifications
To indicate that a new resource is available for a client instance to access,
an AS can send a notification to that client instance.
This notification may include:
* a displayable description of the resource
* instructions for accessing the resource
* a description of the intended end user, through an identifier or an attribute such as a group name.

There may be a response notification, accept/reject.

If the notification is addressed to an unregistered client instance, then the AS MAY dynamically register this client instance
using [GNAP client instance discovery](./gnap-client-instance-discovery.md).

See https://cs3org.github.io/OCM-API/docs.html?branch=v1.1.0&repo=OCM-API&user=cs3org#/paths/~1shares/post

### Details of GNAP client instance discovery
For an RO to dynamically register a client instance, they can:
* provide its FQDN
* the AS will retrieve the .well-known
* if this fails, it can do an SRV lookup
* the AS takes a decision whether to dynamically add the client instance or not

See https://cs3org.github.io/OCM-API/docs.html?branch=v1.1.0&repo=OCM-API&user=cs3org#/paths/~1ocm-provider/get

## invite

Alice sends Bob a nonce out of band. Bob enters this in client instance 2.
It sends a POST to AS 1 with Bob's user identifier.
Client instance registration may happen on the fly.


Scenario 1: only pre-trusted receiving servers.
Scenario 2: dynamic client instance registration as part of invite accepting.
Scenario 3: client instance discovery triggered by RO.

Then GNAP notifications including response notifications

What to do with resharing? -> permission

Then legacy: include sharedSecret in the notification.

show users with access

public link that doesn't expose the document itself
Like DOI
Request an invite to something


# accept/reject/revoke notifications
# reshare notifications