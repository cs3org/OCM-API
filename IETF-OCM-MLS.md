---
title: >-
  Federated Groups in Open Cloud Mesh using Messaging Layer Security
abbrev: "OCM MLS Federated Groups"
docname: draft-nordin-ocm-mls-federated-groups-00
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

This document defines an extension to the Open Cloud Mesh (OCM) protocol
to support federated groups as Receiving Parties of shares.  This is
achieved using the Messaging Layer Security (MLS) protocol (RFC 9420) as
a group management layer.  MLS is used for establishing and rotating a
shared group key across federated group members, as well as for
maintaining group state.  This gives not only a way of federating group
membership, but also a standardized way of distributing encryption keys
in a cryptographically secure way, so that files shared with a group can
optionally be encrypted and decrypted.  MLS usage in OCM acts as a
vehicle for group management that gives users optional encryption
capabilities for resources shared with federated groups.

--- middle

# Introduction

Open Cloud Mesh [OCM] currently supports sharing resources with
individual users across federated servers and with groups on a single
server.  The specification also defines a `shareType` of `"federation"`
but does not further specify its semantics.  This document gives
`"federation"` a concrete definition: a federated group identified by an
OCM Address such as `research-group@receiver.example.org` whose
membership spans multiple OCM servers, with group state managed through
the MLS [RFC9420] epoch mechanism.

In many Enterprise File Sync and Share (EFSS) systems, which constitute
the vast majority of all OCM Servers, there is a tight coupling between
a client and a server, because the server offers a built-in web
interface as its primary client.  In addition to this, a sync client is
often offered as a way of syncing files between the EFSS system and the
user's devices.

In MLS, a client is defined as an agent that establishes shared
cryptographic state with other clients, defined by the cryptographic
keys it holds.  An EFSS server meets this definition directly.  For
deployments where the primary user interface is a web client, the OCM
Server fulfils the MLS client role server-side, holding key material on
behalf of its users, and the word "client" as used in this document
should not necessarily be taken to mean the user's file sync client.
Implementations that do provide a native client application SHOULD
perform cryptographic operations in the native client on the user's
devices, rather than on the server, because this provides stronger
isolation of key material from the server.  In either case the same MLS
client model applies.

Each user who is a member of a federated group has their own MLS leaf
node, enabling individual users to be added and removed independently.
The OCM Server can act as the MLS client on behalf of its users.  For
implementations where the primary interface is a web client, the OCM
Server holds and uses key material server-side.  Implementations with a
native client application SHOULD perform cryptographic operations in the
native client, with the server acting as a relay for MLS messages.

Throughout this document, actions described as being performed by an OCM
server are understood to be performed by that server in its capacity as
an MLS client, on behalf of one of its users.  The server holds no group
membership or cryptographic state independent of its users.

The group and its membership exist and evolve independently of any
sharing activity.  A user that wants to share a resource with a group
can do so without the need to know the current membership details of
that group.  The MLS Delivery Service role is distributed: proposals are
delivered to the home servers of all admins, the Group Owner Server
arbitrates Commits, and File Key (FK) distribution messages are sent
directly from sending servers to member servers, just like OCM share
notifications.  Group membership changes are managed entirely through
MLS group lifecycle operations.

Every group has one or more admins: users who administer the group.  The
user who creates a group is its first admin.  Adding a member, or
removing a member other than oneself, requires the approval of an admin,
placing a human in the loop for changes that grant or revoke access.
Any member can remove themselves from a group without admin approval,
though the Commit is still performed by an admin client.  All Commits
that advance the MLS epoch are constructed by the MLS clients of admins
and arbitrated by the Group Owner Server.

The group's OCM Address is a stable label.  It is minted under the
domain of the server where the group was created, which guarantees its
uniqueness, but it carries no routing semantics: all protocol messages
are routed using the OCM Addresses of individual members and admins,
never the group's.

Files shared with a group can optionally be encrypted with a per-file
key (FK), wrapped with the current group key.  The group key is derived
from the MLS epoch secret and rotates with every epoch transition.  On
every epoch transition the sending server re-wraps the FK under the new
group key and redistributes it, so that the current group key is always
sufficient to unwrap the current FK.  When a member is added to a group,
their MLS client receives the new group key and the re-wrapped FKs, and
can immediately decrypt all resources shared with the group.

When a member is removed from the group, sending servers MAY
additionally generate a new FK and re-encrypt affected resources,
depending on their policy and the nature of the shared data.

# Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",
"SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and
"OPTIONAL" in this document are to be interpreted as described in BCP 14
[RFC2119] [RFC8174] when, and only when, they appear in all capitals, as
shown here.

This document uses terminology from [OCM] and [RFC9420].  Additional
definitions:

- **Group** - A Receiving Party identified by an OCM Address whose
identifier resolves to a set of members spanning multiple OCM servers,
with group state managed through MLS.  The Group's OCM Address is a
stable label assigned at creation and MUST NOT change for the lifetime
of the Group; it carries no routing semantics.  In [RFC9420] a group is
defined as: "a logical collection of clients that share a common secret
value at any given time.  Its state is represented as a linear sequence
of epochs in which each epoch depends on its predecessor."
- **MLS Client** - As defined in [RFC9420]: an agent that establishes
shared cryptographic state with other clients, defined by the
cryptographic keys it holds.  In this protocol an OCM Server can fulfill
this role.
- **Member Server** - An OCM server with one or more users who are
members of a given Group, acting as MLS client on their behalf.
- **Group Owner Server** - The server currently arbitrating Commits for
the Group: the home server of the first Admin in the admin set.
Initially this is the server at which the Group was created.
- **Admin** - A user who administers the Group membership.  The user who
creates a Group is its first Admin.  Only the MLS clients of Admins
(admin clients) construct Commits.  The admin set is part of the group
state ({{admin-set}}).
- **Admin Server** - The home server of an Admin.  Admin Servers
collectively queue proposals for the Group.
- **Group Key** - A symmetric key derived from the current MLS epoch
secret via the MLS Exporter, with the key length of the AEAD algorithm
of the group's cipher suite.  Rotates with every epoch transition.
- **File Key (FK)** - A random symmetric key used to encrypt a single
shared resource.  Wrapped with the current Group Key and distributed to
Member Servers via MLS Application Messages.  Re-wrapped under the new
Group Key on every epoch transition ({{fk-rewrap}}).  Member Servers
always store the most current wrapped FK for each resource.
- **Re-encryption mode** - On member removal, the sending server
generates a new FK, re-encrypts the resource, and distributes the new
wrapped key.  Provides strong cryptographic guarantees independent of
trust assumptions.
- **Key-reuse mode** - On member removal, the existing FK is kept and
only the standard re-wrap on epoch change ({{fk-rewrap}}) is performed,
without re-encrypting the resource.  Appropriate only within formally
trusted federations and where re-encryption is impractical.  Mode is not
a binary choice; sending servers can choose one mode for one epoch and
another mode for another epoch, depending on policy and other
circumstances.
- **KeyPackage** - As defined in [RFC9420].  A signed object that
enables adding an MLS client to a group asynchronously.  KeyPackages
MUST be used only once, except for a designated last resort KeyPackage
([RFC9420] Section 16.8).

# MLS Roles in OCM

MLS is designed to operate with two supporting services: an
Authentication Service (AS) and a Delivery Service (DS) ([RFC9420]
Section 3; see also the MLS architecture [RFC9750]).  This section
describes how those roles are fulfilled by OCM.

## Authentication Service

The AS role is fulfilled by each user's home OCM server.  Credentials in
this protocol are MLS basic credentials ([RFC9420] Section 5.3) whose
identity field is the UTF-8 encoded OCM Address of the user.  Each user
has their own distinct signing key pair so that individual users can be
identified and addressed independently within the MLS group, for example
to add or remove a specific user.  In web-client deployments the key
pair is generated and held by the OCM Server on the user's behalf.  In
native client deployments the key pair is held on the user's device and
the server's role is limited to publishing the user's KeyPackages.

A basic credential carries no verifiable binding of its own; the binding
between a user's OCM Address and their signature key is attested by
authenticated delivery from the user's home server.  A KeyPackage
fetched over TLS from the `<endPoint>/mls-key-packages` endpoint of the
server named in the credential's OCM Address, with the response signed
using HTTP Signatures [RFC9421] verifying against that server's JWKS
endpoint at `/.well-known/jwks.json` [RFC7517], is considered validated
with the AS.  The full validation procedure, including how credentials
introduced later in the life of a group are validated, is specified in
{{trust-and-authentication}}.

## Delivery Service

The DS role is distributed across the servers of the group rather than
centralised on a single server.  MLS places no constraints on how the DS
is arranged, as long as messages are delivered ([RFC9420] Section 3).

- Proposal delivery: `MLS_PROPOSAL` notifications are sent to the home
server of every admin ({{admins}}), derived from the admin set and the
OCM Addresses in the ratchet tree's leaf credentials.  Admin Servers
queue proposals, deduplicated by ProposalRef ([RFC9420] Section 5.2),
and make them available to their admin clients.
- Commit arbitration: the Group Owner Server, the home server of the
first admin in the admin set, accepts exactly one Commit per epoch from
an admin client and broadcasts it to all Member Servers.
- FK distribution: `MLS_APPLICATION` messages carrying wrapped file keys
are sent directly from the sending server to all current Member Servers,
exactly like OCM share notifications; credential updates are sent to a
single Member Server ({{credential-update}}).

All MLS messages are delivered to the `<endPoint>/notifications`
endpoint of each recipient server, authenticated with HTTP Signatures
[RFC9421].

Commits are constructed and signed by admin clients, but only the Commit
accepted by the Group Owner Server takes effect; competing Commits for
the same epoch are discarded by their senders.  Designating a single
arbiter of Commits eliminates conflicting Commits for the same epoch
during normal operation, satisfying the sequencing requirement of
[RFC9420] Section 14; conflicting Commits can arise only during failover
and are then resolved deterministically ({{failover}}).  Per [RFC9420]
Section 14, generating a Commit does not modify the sender's state, so
an admin client whose Commit is rejected simply discards it and
constructs a new Commit on the new epoch.

OCM share notifications are sent directly from the sending server to
each Member Server.  Since sending servers must be group members, they
hold the current MLS ratchet tree after processing each `MLS_COMMIT`,
and can derive the current membership - specifically the OCM Address in
each leaf node's credential - to determine which Member Servers to
contact.  No proxying through the Group Owner Server is required for
OCM-level communication.

MLS is designed to protect confidentiality and integrity even against a
misbehaving DS.  No single server in this design carries the full DS
role, and no server holds key material by virtue of its DS duties; the
MLS security properties with respect to message confidentiality hold
regardless.

# How MLS is implemented over OCM

- **MLS for group key management only.** MLS establishes and rotates a
shared group key.  The only MLS application messages used in this
protocol carry wrapped file keys ({{key-distribution}}) and per-server
transport credential updates ({{credential-update}}).

- **At least one MLS leaf per user.** Each user who is a member of a
federated group has at least one MLS leaf node, enabling individual
users to be added and removed independently.  In web-client deployments
the OCM Server manages a single leaf node per user on their behalf.  In
native client deployments each user may have a leaf node per device.

- **The OCM Server is a MLS client.** An OCM Server meets the MLS
definition of a client.  For web-client deployments this means key
material is held server-side.  For native client deployments
cryptographic operations SHOULD be performed in the native client.

- **Admins approve membership changes.** Every group has one or more
admins ({{admins}}).  Commits are constructed by admin clients and
arbitrated by the Group Owner Server.  Add proposals and Remove
proposals targeting another user require admin approval; any member may
remove themselves, and Update proposals are committed automatically.

- **Encryption is optional.** MLS group management is useful
independently of whether encryption is used.  A federation share MAY be
unencrypted, in which case the `encryption` field is omitted from the
Share Creation Notification and the MLS layer provides only group
membership management.

- **FK re-wrap on every epoch change.** After processing an `MLS_COMMIT`
for a group, a sending server MUST re-wrap the current FK of every
resource it shares with that group under the new Group Key and
distribute it via `MLS_APPLICATION` ({{fk-rewrap}}).  This maintains the
invariant that the current Group Key is always sufficient to unwrap the
current wrapped FK.

- **FK rotation on member removal.** On member removal, a sending server
SHOULD additionally rotate the FK for affected resources: generate a new
FK, re-encrypt the resource, and distribute the new wrapped FK to all
groups that share those resources.  FK rotation may also be triggered by
other factors such as periodic key rotation policy or suspected key
compromise.  Member addition does not require FK rotation; the standard
re-wrap is sufficient.

- **Key-reuse mode as an alternative.** Where re-encryption on removal
is impractical and where participating servers are mutually trusted
within a formal federation, a sending server MAY instead keep the
existing FK, relying on the standard per-epoch re-wrap alone.

- **Sending servers must have group members.** To share a resource with
a group, the sending server must have at least one user who is a member
of that group, allowing it to work out the members to share with, and to
be able to wrap the FK for encrypted shares.  This is by design, to
mitigate spam shares and other abusive behaviour.

- **OCM messages are still just OCM messages.** Proposals flow to the
servers of all admins, Commits are arbitrated by the Group Owner Server,
and FK distribution and OCM share notifications flow directly from the
sending server to each Member Server, derived from the sending server's
local view of group membership from the MLS ratchet tree.  No message is
proxied through a single central server.

- **Sending servers derive membership from the ratchet tree.** Since
sending servers must have group members, they process all `MLS_COMMIT`
messages and hold the current ratchet tree.  The OCM Address in each
leaf node's credential identifies the corresponding Member Server.  The
sending server uses this to determine which Member Servers to contact
directly for share notifications and FK distribution.

- **Push-based FK distribution.** Wrapped file keys are distributed via
`MLS_APPLICATION` directly from the sending server to all current Member
Servers, at share creation and after every epoch transition
({{fk-rewrap}}).  Member Servers always hold the current wrapped FK for
each resource and use their current Group Key to unwrap it at access
time.

- **Minimal protocol surface.** The `shareType: "federation"` value
already defined in the OCM specification is used without modification,
with `shareWith` carrying the group's OCM Address.  A federation share
is otherwise a standard OCM share, carrying every field REQUIRED by
[OCM] including the `protocol` object.  All new server-to-server
messages use the existing `/notifications` endpoint with new
`notificationType` values.  A single new field is added to the Share
Creation Notification: `encryption` (optional, present only for
encrypted resources), carrying all encryption-related parameters,
including the `resourceId`.

# Discovery

A server signals support for federation shares by including
`"federation"` in the `shareTypes` array for a given resource type in
its OCM discovery document at `/.well-known/ocm`:

~~~ json
{
  "enabled": true,
  "apiVersion": "1.4.0",
  "endPoint": "https://cloud.example.org/ocm",
  "provider": "Example Cloud",
  "resourceTypes": [
    {
      "name": "file",
      "shareTypes": ["user", "group", "federation"],
      "protocols": { "webdav": "/webdav/", "webdav-receive": {} }
    }
  ]
}
~~~

No additional discovery fields are introduced.  The notifications
endpoint is derived as `<endPoint>/notifications` per the base OCM
specification.  The KeyPackage endpoint is derived as
`<endPoint>/mls-key-packages`.

A server that advertises `"federation"` MUST be able to receive OCM
Notifications, since all MLS lifecycle messages are delivered as
notifications, and SHOULD include `"notifications"` in its
`capabilities` array.

# KeyPackage Distribution

Each OCM Server acting as an MLS client generates and maintains
KeyPackages for its users and exposes them at:

~~~
GET <endPoint>/mls-key-packages?userId={userId}
~~~

Response:

~~~ json
{
  "userId": "alice@cloud.example.org",
  "keyPackages": [
    {
      "mediaType": "message/mls",
      "encoding": "base64",
      "content": "<base64-encoded MLS KeyPackage>"
    }
  ]
}
~~~

Requests to this endpoint MUST be signed using HTTP Message Signatures
[RFC9421] ({{security-considerations}}).

In native client deployments, the user's device generates KeyPackages
and publishes them to the home server, which exposes them at the same
endpoint without interpreting them.

Each KeyPackage contains an MLS Credential identifying the user by their
OCM Address, signed by the user's own signing key pair.  Users who
require stronger isolation of key material from their server should use
a native client implementation.

KeyPackages MUST be one-time use, with the exception of a designated
"last resort" KeyPackage ([RFC9420] Section 16.8).  The server MUST
remove a KeyPackage after it has been delivered.  Servers SHOULD
pre-generate multiple KeyPackages per user to support concurrent group
additions, MAY designate a last resort KeyPackage per user to be
returned when all single-use KeyPackages are exhausted, and SHOULD
rate-limit KeyPackage requests, so that an attacker cannot block a
user's addition to groups by exhausting their KeyPackages.  KeyPackages
carry a leaf node lifetime, and applications MUST define a maximum total
lifetime they accept ([RFC9420] Section 7.2).

The `userId` fields defined in this document carry the user's full OCM
Address, not the bare identifier that [OCM] calls `userID`; the full
address is required because these messages routinely cross server
boundaries.

# Group Lifecycle

The group lifecycle is entirely independent of other OCM lifecycles
(token-exchange, shares, invitations etc.).  Members are added and
removed through MLS group operations conveyed via the `/notifications`
endpoint.

## Group Creation

The creating server creates an MLS group on behalf of one of its users
and initialises leaf nodes for each of its users who are initial
members.  The creating user becomes the group's first admin
({{admins}}), making the creating server the initial Group Owner Server.
No notifications are required for this step.  The group becomes
addressable at its OCM Address immediately upon creation.

The group's OCM Address is minted under the creating server's domain,
which guarantees its uniqueness, and MUST NOT change for the lifetime of
the group.  It is a label only: no protocol message is routed based on
it, and it remains valid even after the Group Owner Server role has
moved to another server.  The MLS `group_id` SHOULD be a fresh random
value, as recommended by [RFC9420] Section 11.

The creator selects the group's MLS cipher suite based on the
capabilities advertised in the prospective members' KeyPackages
([RFC9420] Section 11).  Implementations of this document MUST support
the mandatory-to-implement MLS cipher suite
MLS_128_DHKEMX25519_AES128GCM_SHA256_Ed25519 ([RFC9420] Section 17.1).

## Group Admins {#admins}

Every group has a set of admins: users who administer the group
membership.  The user who creates the group is its first admin, and an
admin MAY appoint further admins.  Admins are ordinary group members and
MAY be homed on any Member Server.  An admin's MLS clients are referred
to as admin clients.

Commits MUST be constructed and signed by admin clients.  This is an
application-level policy on top of MLS, as anticipated by [RFC9420]
Section 16.11, and it is enforced at two points.  First, the Group Owner
Server MUST reject Commits submitted by any other client.  Second, every
Member Server processing an `MLS_COMMIT` MUST verify that the Commit is
signed by an admin client: a Commit is signed by the leaf indicated in
its sender field ([RFC9420] Section 6.1), and the credential at that
leaf, in the ratchet tree of the epoch in which the Commit was created,
must identify a user listed in `admins` ({{admin-set}}) as of that same
epoch.  A Commit that fails this check MUST be rejected, regardless of
which server broadcast it.  Because the admin set is part of the
GroupContext, every member performs this check locally; acceptance of a
Commit does not rely on trusting the Group Owner Server.

Proposals are handled according to the following policy:

- An Add proposal, or a Remove proposal targeting a leaf that does not
belong to the proposing user, MUST be explicitly approved by an admin
before an admin client commits it, unless both are part of a rejoin pair
as described below.  This places a human in the loop for changes that
grant or revoke another party's access.
- A Remove proposal targeting a leaf that belongs to the proposing user
(self-removal) does not require admin approval.  Any member MAY leave a
group at any time, and admin clients SHOULD commit self-removal
proposals automatically.
- A rejoin pair - a Remove of a leaf together with an Add of a fresh
KeyPackage whose credential carries the same OCM Address as the removed
leaf's credential ({{rejoin}}) - is identity-preserving and grants no
new party access.  It does not require explicit admin approval, and
admin clients SHOULD commit rejoin pairs automatically.
- Update proposals do not require admin approval, and admin clients
SHOULD commit pending Update proposals automatically whenever they are
online.

The group MUST have at least one admin at all times.  A proposal that
would remove the last admin, including a self-removal, MUST be rejected
by the Group Owner Server until another admin has been appointed.

Removing an admin from the group and removing an admin from the admin
set are distinct operations; when an admin's membership ends, a single
Commit combines them ({{admin-set}}).  An admin MAY instead resign from
the admin set while remaining a member: this is a GroupContextExtensions
proposal only, and the resigning admin's own client MAY commit it.
Removing an admin's membership is constrained by MLS: a Commit that
removes its own committer is invalid ([RFC9420] Section 12.2).  A Commit
that removes some but not all of an admin's leaves MAY be committed by
one of that admin's remaining clients, but a Commit that removes an
admin's last leaf is necessarily committed by an admin client of a
different admin.

### Group OCM Address and Admin Set {#admin-set}

The group's OCM Address and the admin set are part of the group state,
carried in a GroupContext extension `ocm_federated_group` ([RFC9420]
Section 13.4):

~~~
struct {
  opaque ocm_address<V>;
} Admin;

struct {
  opaque group_ocm_address<V>;
  Admin admins<V>;
} OCMFederatedGroup;
~~~

All addresses are UTF-8 encoded OCM Addresses.  The `group_ocm_address`
field carries the group's OCM Address and MUST NOT change for the
lifetime of the group.

The `admins` list is ordered by appointment: a newly appointed admin is
appended at the end, a departing admin is deleted by the same Commit
that ends their membership or admin role (see below), and the list MUST
NOT otherwise be reordered.  The home server of the first admin in the
list is the current Group Owner Server.  Succession is therefore
automatic: when the first admin leaves the group or resigns as admin,
the home server of the next admin in the list becomes the Group Owner
Server.  For example, if alice on server1 creates the group and appoints
bob on server2 and then charlie on server3, the list is (alice, bob,
charlie) and server1 is the Group Owner Server; after bob leaves it is
(alice, charlie); after alice then leaves it is (charlie,) and server3
is the Group Owner Server.

An admin client is any MLS client whose leaf credential identifies a
user listed in `admins`.  Because this extension is part of the
GroupContext, it is agreed upon by all members through the MLS key
schedule, every member can verify which clients are entitled to
construct Commits and which server arbitrates them, and new members
learn the group's OCM Address and admin set from the GroupInfo in their
Welcome.  Changes to the admin set are made with a
GroupContextExtensions proposal ([RFC9420] Section 12.1.7); such
proposals MUST be explicitly approved by an admin, MUST be committed by
an admin client, and MUST NOT change `group_ocm_address`.

The admin set and the group membership are coupled: an entry in `admins`
is only meaningful while that admin has at least one leaf in the ratchet
tree.  A Commit after whose application an admin would no longer have
any leaf in the ratchet tree MUST therefore also include a
GroupContextExtensions proposal deleting that admin from `admins`, and
the Group Owner Server and all Member Servers MUST reject a Commit that
would leave an entry in `admins` with no corresponding leaf in the tree.
(A rejoin pair ({{rejoin}}) that replaces an admin's leaf does not
trigger this rule, since the admin retains a leaf after the Commit.)
Because a GroupContextExtensions proposal replaces the extension list
wholesale ([RFC9420] Section 12.1.7), the proposal carries the complete
new `OCMFederatedGroup` value, with the departing admin deleted and
`group_ocm_address` unchanged.  A GroupContextExtensions proposal whose
only change to the admin set is deleting admins whose leaves are removed
in the same Commit requires no separate admin approval; it follows the
approval status of the Remove proposals it accompanies, so that the
self-removal of an admin can still be committed automatically.

Clients implementing this document MUST list the `ocm_federated_group`
extension type in the `capabilities.extensions` field of their
KeyPackages, since GroupContext extensions must be supported by every
member of the group ([RFC9420] Section 13.4).

## Group Owner Server Failover {#failover}

The Group Owner Server can become unavailable, leaving the group without
an arbiter and therefore unable to advance its epoch.  Leaf staleness
({{leaf-key-updates}}) anchors the failover trigger: the absence of
committed Updates from a leaf is part of the group state that all
members observe identically.  The other trigger condition, the absence
of broadcast Commits, is necessarily observer-dependent - a server that
missed a broadcast cannot distinguish silence from loss - which is why
divergent failover decisions are tolerated and resolved
deterministically in step 3 below.

In addition to the update deadline, groups MUST define a takeover time
T.  T MUST be longer than the update deadline, so that the staleness of
the first admin's leaf is observable before takeover is permitted.
Failover proceeds as follows:

1.  Trigger: no `MLS_COMMIT` has been broadcast for time T, and the
    first admin's leaf is stale.
2.  Takeover: the home server of the next admin in the admin set MAY
    begin arbitrating Commits.  The first Commit it arbitrates SHOULD
cover Remove proposals evicting the stale first admin's leaves, together
with the GroupContextExtensions proposal deleting them from the admin
set required by {{admin-set}}, constructed by one of its own admin
clients.  This makes the takeover permanent through the normal
succession rule.
3.  Conflict resolution: if a Member Server receives two different
    Commits for the same epoch from two arbiters, it MUST process the
one arbitrated by the server of the admin listed earlier in the admin
set and discard the other.
4.  Hold-back: a Member Server that has observed the trigger conditions
    of step 1 SHOULD retain the previous epoch's group state when
processing a Commit, so that it can revert and reprocess the winning
Commit if conflict resolution later discards the one it processed first.
Retained state MUST be deleted after a bounded time, per [RFC9420]
Section 14; the security trade-off is discussed in Security
Considerations.
5.  Rejoin: a Member Server that processed a discarded Commit and no
    longer holds the state needed to reprocess the winning Commit has
drifted from the group.  It recovers through the rejoin procedure
({{rejoin}}).  Wrapped FKs are re-wrapped and redistributed by their
sending servers in the new epoch as usual ({{fk-rewrap}}).

Since an unavailable arbiter only pauses membership changes, while
sharing, resource access, and FK distribution continue to operate, the
takeover time T MAY be generous, for example several hours.  Loose time
synchronisation between servers is sufficient and is already assumed by
MLS for leaf node lifetimes ([RFC9420] Section 7.2).

## MLS Notification Types

All MLS group lifecycle messages are sent as OCM Notifications to
`<endPoint>/notifications` using HTTP POST with `Content-Type:
application/json` and HTTP Signatures [RFC9421].

Proposals and Commits MUST be encoded as PublicMessage objects
([RFC9420] Section 6.2), and Application Messages as PrivateMessage
objects ([RFC9420] Section 6.3).  Handshake messages are sent in the
clear at the MLS layer because the servers that route and arbitrate them
are required to track the public group state - the ratchet tree and
GroupContext - in order to derive membership for share routing, resolve
shares to local users, and verify that Commits are signed by admin
clients; in native client deployments those servers do not hold the
group's secrets.  A recipient that holds the group's secrets MUST verify
the membership_tag on a PublicMessage ([RFC9420] Section 6.2); a server
relaying or arbitrating without group secrets verifies what it can,
namely the signature against the sender's leaf in its copy of the
ratchet tree and the policy checks of {{admins}}.  The confidentiality
trade-off relative to encrypted handshake messages is discussed in
Security Considerations.

The notification types defined in this document are group-scoped rather
than share-scoped.  [OCM] requires a `providerId` field in notifications
because the notification types it defines all refer to a Share; the MLS
notification types refer to a group instead, so this document updates
that requirement: `providerId` is REQUIRED only for notification types
that refer to a Share, and the MLS notification types omit it.  All
MLS-specific parameters are carried inside the `notification` object
that [OCM] provides for type-specific parameters.  The `mlsGroupId`
field carries the base64-encoded MLS `group_id` as advisory routing
information, used to dispatch the message to the right group state
without parsing the MLS message; the authoritative `group_id` is the one
inside the MLS message itself, and a mismatch between the two MUST be
treated as an error.  At the OCM layer, groups are otherwise identified
by their OCM Address: in particular, the `groupId` field of the
application data carried inside `MLS_APPLICATION` messages
({{key-distribution}}, {{credential-update}}) is the group's OCM
Address, never the MLS `group_id`.

Since `MLS_PROPOSAL` is delivered only to Admin Servers and never
broadcast to other Member Servers, Member Servers never observe pending
proposals.  Proposals covered by a Commit are instead redistributed
together with that Commit, as described under `MLS_COMMIT` below.  Admin
clients, as the only committers ({{admins}}), MUST satisfy all
considerations of [RFC9420] Section 12.4.

### MLS_WELCOME

Sent to a Member Server when one of its users is added to the group.
The Welcome is constructed by the admin client that created the
corresponding Commit ([RFC9420] Section 12.4.3.1) and delivered by that
admin's home server directly to the added user's server, after the Group
Owner Server has accepted the Commit.  Delivers the MLS Welcome message
for the added user, enabling the receiving MLS client to initialise its
state and derive the current Group Key.  A single `MLS_COMMIT` covering
multiple Add proposals will result in one `MLS_WELCOME` notification per
added user.

~~~ json
{
  "notificationType": "MLS_WELCOME",
  "notification": {
    "mlsGroupId": "<base64 MLS group ID>",
    "userId": "bob@othercloud.example.org",
    "content": "<base64 MLS Welcome wire format>"
  }
}
~~~

The Welcome message MUST include the group's ratchet tree in a
`ratchet_tree` extension ([RFC9420] Section 12.4.3.3).  By default a
Welcome carries only a hash of the tree, and this document defines no
other channel through which a newly added Member Server could obtain it.
Member Servers depend on holding the current ratchet tree, both to
derive the group membership and to process subsequent Commits.  Carrying
the tree inside the Welcome also gives it the same confidentiality
protection as the rest of the group state, as recommended by [RFC9420]
Section 12.4.3.3.

A Member Server processing a Welcome learns the group's OCM Address from
the `ocm_federated_group` extension in the GroupContext ({{admin-set}}).
It MUST reject a Welcome whose `group_ocm_address` is already bound to a
different MLS `group_id`, unless the Welcome reinitialises the group as
described in {{reinit}}.  This keeps the local wrapped FK store, keyed
by `(resourceId, groupId)`, unambiguous.

### MLS_PROPOSAL

Sent by a Member Server to the home server of every admin to propose a
group change (for example Add, Remove, Update, GroupContextExtensions,
or ReInit) on behalf of one of its users.  This notification is NOT
broadcast to other Member Servers.  Each Admin Server queues received
proposals, deduplicated by ProposalRef ([RFC9420] Section 5.2), for
handling by its admin clients according to the policy in {{admins}}.
Sending the proposal to all Admin Servers removes the dependency on any
single server being available and lets whichever admin is online next
act on it.

~~~ json
{
  "notificationType": "MLS_PROPOSAL",
  "notification": {
    "mlsGroupId": "<base64 MLS group ID>",
    "content": "<base64 MLS PublicMessage carrying the Proposal>"
  }
}
~~~

### MLS_COMMIT

Constructed and signed by an admin client ({{admins}}) and submitted to
the Group Owner Server, which accepts at most one Commit per epoch, MUST
reject Commits submitted by non-admin clients, and broadcasts the
accepted Commit to all Member Servers to advance the group epoch.  An
admin client whose Commit is rejected discards it and MAY construct a
new Commit on the resulting epoch ([RFC9420] Section 14).  A Member
Server receiving a broadcast `MLS_COMMIT` MUST verify that the Commit is
signed by an admin client before processing it, as specified in
{{admins}}, and MUST reject it otherwise, regardless of which server
broadcast it.  Commits are ordered by the MLS epoch itself: each Commit
advances the epoch by exactly one, so Member Servers MUST process
Commits in epoch order, and a Commit arriving for an epoch later than
the next expected one indicates one or more missed Commits.  Member
Servers MUST apply the new epoch secret before sending any application
data, per [RFC9420] Section 15.2.

~~~ json
{
  "notificationType": "MLS_COMMIT",
  "notification": {
    "mlsGroupId": "<base64 MLS group ID>",
    "proposals": ["<base64 MLS PublicMessage carrying a Proposal>"],
    "content": "<base64 MLS PublicMessage carrying the Commit>"
  }
}
~~~

A Commit covers each proposal either by value or by reference ([RFC9420]
Section 12.4).  Proposals included by value are carried inside the
Commit itself and are necessarily proposals originated by the committing
admin client, since a by-value proposal carries no sender of its own.
Proposals received from Member Servers via `MLS_PROPOSAL` - in
particular Update proposals, which can only be applied relative to their
original sender's leaf - are covered by reference, and receiving Member
Servers need the original proposal messages in order to validate and
apply the Commit ([RFC9420] Sections 12.1 and 12.4.2).  The `proposals`
array therefore carries every proposal covered by reference, verbatim as
originally sent by their proposers, in the order in which the
corresponding references appear in the Commit.  It MUST be present
whenever the Commit covers at least one proposal by reference and MAY be
omitted otherwise.  A Member Server processing an `MLS_COMMIT` MUST
process the carried proposals before processing the Commit itself.

The `MLS_COMMIT` serves as the signal to all sending servers that the
epoch has advanced: each sending server then re-wraps and redistributes
the FKs of the resources it shares with the group ({{fk-rewrap}}), and
on member removal MAY additionally rotate them according to its policy
({{fk-rotation}}).  Any Commit covering a Remove, Update, or
GroupContextExtensions proposal MUST include an UpdatePath ([RFC9420]
Section 12.4).

### MLS_APPLICATION

Sent by a sending server directly to Member Servers, derived from the
ratchet tree, to deliver updated wrapped file keys and, optionally,
updated per-server transport credentials ({{credential-update}}).  No
central relay is involved.  Messages carrying wrapped FKs are sent to
all current Member Servers; messages carrying a transport credential are
sent only to the affected Member Server.  The `content` is a
`PrivateMessage` carrying application data encrypted in the current
epoch ([RFC9420] Section 15).

~~~ json
{
  "notificationType": "MLS_APPLICATION",
  "notification": {
    "mlsGroupId": "<base64 MLS group ID>",
    "content": "<base64 MLS PrivateMessage wire format>"
  }
}
~~~

Ordering is provided by authenticated MLS metadata rather than a
transport counter: the `PrivateMessage` carries the epoch in the clear,
and the sender's leaf and generation counter are learned upon decryption
([RFC9420] Section 6.3).  Since all FK updates for a given `(resourceId,
groupId)` originate from the resource's sending server, the `(epoch,
generation)` pair totally orders them; see {{key-distribution}}.  A
Member Server that receives an `MLS_APPLICATION` encrypted in an epoch
it has not yet entered SHOULD queue it until the corresponding
`MLS_COMMIT` has been processed.

Because credential-bearing messages are delivered to a single Member
Server, other Member Servers will observe a gap in the sending leaf's
generation counter on the next message they do receive.  Such gaps are
expected and MUST NOT be treated as an error; receivers ratchet forward
past skipped generations as described in [RFC9420] Section 15.3.
Deployments MUST limit the number of generations a receiver will advance
a sender ratchet in response to a single message and reject messages
beyond that limit, bounding the key derivation work a malicious sender
can trigger ([RFC9420] Section 15.3).

### MLS_REJOIN

Sent by a drifted Member Server to the home server of every admin to
request re-admission of its users after local MLS state loss
({{rejoin}}).  Unlike the other notification types, the content is not
an MLS message: a drifted server holds no usable MLS state, so the
request is authenticated only at the OCM layer, by the HTTP Signature of
the sending server.  Each entry in `keyPackages` carries a fresh MLS
KeyPackage for one affected user, in the same format as entries served
by the KeyPackage endpoint.

~~~ json
{
  "notificationType": "MLS_REJOIN",
  "notification": {
    "mlsGroupId": "<base64 MLS group ID>",
    "keyPackages": [
      {
        "userId": "bob@othercloud.example.org",
        "mediaType": "message/mls",
        "encoding": "base64",
        "content": "<base64-encoded MLS KeyPackage>"
      }
    ]
  }
}
~~~

Admin Servers queue rejoin requests alongside proposals and make them
available to their admin clients, which handle them as described in
{{rejoin}}.  A later rejoin request for the same group and user
supersedes an earlier one; admin clients act on the most recent request.

## Leaf Key Updates {#leaf-key-updates}

To maintain post-compromise security ([RFC9420] Section 16.6), Member
Servers SHOULD periodically send `MLS_PROPOSAL` (Update) to the Admin
Servers to rotate their users' leaf keys.  Admin clients SHOULD commit
pending Update proposals automatically whenever they are online, without
user interaction; an Update only achieves post-compromise security once
it has been committed ([RFC9420] Section 16.6).

Groups MUST define an update deadline: the maximum time allowed between
committed Updates of a leaf.  A leaf that has not been updated within
the deadline is stale.  Members with stale leaves SHOULD be removed from
the group per [RFC9420] Section 3.2, and stale admins in particular
SHOULD be removed promptly: an admin whose clients no longer update
cannot commit, and a stale first admin additionally blocks Commit
arbitration until failover ({{failover}}).

## Rejoin After State Loss {#rejoin}

A Member Server can lose its MLS state for a group: it may have
processed a Commit that was later discarded during failover conflict
resolution ({{failover}}) and already deleted the superseded epoch's
secrets per the deletion schedule ([RFC9420] Section 9.2), or its stored
state may be lost or corrupted for any other reason.  Such a server has
drifted from the group: it can no longer process Commits or decrypt
Application Messages, and because MLS messages are bound to the current
GroupContext, it cannot sign a valid Proposal with which to recover.  A
drifted server detects its condition when an `MLS_COMMIT` fails to
process against its local state, for example through a confirmation tag
mismatch, or arrives for an epoch it cannot reach after Commit
retransmission has been exhausted.

Recovery is mediated by an admin client through the normal Commit path:

1.  The drifted server discards its MLS state for the group and
    generates a fresh KeyPackage for each of its users who are members
of the group.
2.  It sends an `MLS_REJOIN` notification carrying those KeyPackages to
    the home server of every admin.  The notification is authenticated
at the OCM layer with HTTP Signatures [RFC9421], the same trust anchor
that authenticates KeyPackage distribution itself, so a rejoin request
is exactly as trustworthy as a freshly fetched KeyPackage.
3.  An admin client verifies that each KeyPackage's credential carries
    the OCM Address of a leaf currently in the ratchet tree, and that
the notification was signed by the server named in those OCM Addresses.
A rejoin MUST NOT admit a user without a leaf in the tree; it can only
replace existing members.
4.  The admin client constructs a single Commit containing, by value, a
    Remove proposal for each stale leaf and an Add proposal for the
corresponding fresh KeyPackage.  This rejoin pair preserves the OCM
Address of every affected leaf and grants no new party access, so admin
clients SHOULD commit it automatically, per the policy in {{admins}}.
5.  The Commit is arbitrated and broadcast as usual, and the drifted
    server receives one `MLS_WELCOME` per re-added user, restoring clean
state from the Welcome's `ratchet_tree` extension.

A single Commit recovers all of the drifted server's users at once.
Until the rejoin completes, the drifted server can continue to serve
resources whose wrapped FKs it received before the fork, using the Group
Key of the last epoch it processed; wrapped FKs distributed after the
fork become accessible when the re-wrap following the rejoin Commit
({{fk-rewrap}}) arrives.

## Group Reinitialisation {#reinit}

Reinitialisation ([RFC9420] Section 11.2) replaces a group with a new
MLS group with the same membership and the same OCM Address but
different parameters: a new MLS version, cipher suite, or extension set,
and necessarily a fresh MLS `group_id`.  It is the migration path for
cryptographic agility, for example moving a long-lived group to a
stronger cipher suite.

A ReInit proposal is a group parameter change and is handled like other
group-changing proposals: it MUST be explicitly approved by an admin and
MUST be committed by an admin client.  Per [RFC9420] Section 12.2, a
ReInit proposal is committed alone.  The `extensions` field of the
ReInit proposal MUST include an `ocm_federated_group` extension with
`group_ocm_address` unchanged; the admin set is normally carried over
unchanged.

After the ReInit Commit is processed, the old group MUST NOT be used to
send messages ([RFC9420] Section 12.4.2).  In particular, sending
servers MUST NOT send `MLS_APPLICATION` messages in the old group; the
per-epoch re-wrap obligation ({{fk-rewrap}}) arising from the ReInit
Commit is deferred to the new group.

The admin client that committed the ReInit SHOULD create the new group:
it fetches fresh KeyPackages, valid for the new version and cipher
suite, for every member of the old group, creates the new group with an
initial Commit re-admitting them, and sends each member a Welcome
carrying a PreSharedKeyID of type resumption with usage reinit, as
specified by [RFC9420] Section 11.2.  The Add proposals of this initial
Commit re-admit the old group's members and require no separate admin
approval.  If the committing admin client fails to complete this step in
reasonable time, any other admin client MAY do so instead.  If a Member
Server receives competing reinitialisation Welcomes for the same
`group_ocm_address`, it MUST accept the one whose new group was created
by the admin listed earliest in the old group's admin set and reject the
others.

A Member Server processing a reinitialisation Welcome MUST perform the
verifications of [RFC9420] Section 12.4.3.1 for usage reinit: the last
Commit of the old group contains the ReInit proposal, the new group's
parameters match it, and every member of the old group is a member of
the new group, where members are equivalent if their leaf credentials
carry the same OCM Address.  It MUST additionally verify that the
`group_ocm_address` of the new group equals that of the old group.  On
success it rebinds the OCM Address from the old `group_id` to the new
one; this is the only case in which that binding may change.  Because
the local wrapped FK store is keyed by the group's OCM Address, stored
entries carry over unchanged.

After joining the new group, a sending server MUST re-wrap the FK of
every resource it shares with the group under the new group's Group Key
and redistribute the wrapped FKs to all Member Servers, exactly as for
an epoch change ({{fk-rewrap}}).  The new group's Group Key differs from
any key of the old group both through the fresh epoch secret and through
the new `group_id` in the Exporter context, so no wrapped FK from the
old group can be unwrapped in the new one.  Until the re-wrapped FKs
arrive, Member Servers retain the old group's last Group Key under the
same retention rule as for an epoch change.  Members SHOULD retain the
resumption PSK of the old group's final epoch until the reinitialisation
has completed ([RFC9420] Section 8.6).

# Encryption Model

## Group Key Derivation

After processing any MLS Welcome or Commit, the MLS client MUST apply
the new epoch secret before encrypting any application data, then
derives the current Group Key:

~~~
group_key = MLS-Exporter("ocm-group-key", group_id_bytes, AEAD.Nk)
~~~

`AEAD.Nk` is the length in bytes of a key for the AEAD algorithm of the
group's negotiated MLS cipher suite ([RFC9420] Section 9.1).  Deriving
the Group Key at exactly this length makes it a valid key for the wrap
AEAD ({{file-key-wrapping}}), which is the AEAD algorithm of the group's
cipher suite, for every cipher suite, including those whose AEAD takes a
16-byte key such as AES-128-GCM.

The MLS Exporter ([RFC9420] Section 8.5) produces application-specific
key material from the epoch secret without exposing the epoch secret
itself.  The label `"ocm-group-key"` scopes the output to this
application.  The `group_id_bytes` context, the raw MLS `group_id` of
the group, further binds the output to this specific group.  The Group
Key therefore changes with every epoch transition and cannot be derived
by any party that did not participate in that epoch.

Per [RFC9420] Section 8.5, the Group Key SHOULD be refreshed after each
processed Commit.  Security-sensitive values derived from the epoch
secret MUST be deleted as soon as they are consumed, per [RFC9420]
Section 9.2.

All MLS clients in the group independently derive the same Group Key for
a given epoch.

## Resource Id {#resource-id}

The `resourceId` used in the AEAD associated data MUST be a stable
identifier for the underlying file, consistent across all groups it is
shared with.  It identifies the resource, not a particular version of
it. This ensures that the FK unwrapped by members of any group correctly
decrypts the same ciphertext.  The `providerId` values in separate share
notifications, for the same resource, MUST differ, per the `providerId`
definition in [OCM], but the `resourceId` in the AEAD associated data
MUST be the same.  This means that the `providerId` MUST NOT be reused
as `resourceId`.  The sending server is responsible for maintaining this
stable `resourceId` and MUST send it in the `encryption` object of the
share payload ({{share-creation}}).

## File Key Wrapping {#file-key-wrapping}

Two AEAD algorithms are involved in protecting a resource, and they are
deliberately decoupled.  The content AEAD encrypts the resource itself:
it is chosen by the sending server from the AEAD algorithms defined for
HPKE ([RFC9180] Section 7.3), it is fixed for the lifetime of a
ciphertext and identical across all groups the resource is shared with,
and it is identified explicitly by the `cipher` field of the
`encryption` object ({{share-creation}}).  The wrap AEAD protects the FK
in transit: it is always the AEAD algorithm of the respective group's
MLS cipher suite, keyed with that group's Group Key, and may therefore
differ between groups that share the same resource.

When sharing an encrypted resource with a group, the sending MLS client
acts on behalf of a user who is a member of that group:

1.  Chooses the content AEAD and generates a random per-file key (FK)
    whose length is the key length of that algorithm.
2.  Encrypts the resource with FK using the content AEAD.
    Implementations supporting native client decryption of large files
SHOULD use a chunked AEAD construction to enable streaming decryption.
3.  Derives the current Group Key from the user's local MLS state.
4.  Wraps FK using the wrap AEAD:

    ~~~
    wrapped_file_key = AEAD-Encrypt(
      key       = group_key,
      nonce     = random_nonce,
      plaintext = FK,
      aad       = FKWrapAAD
    )
    ~~~

    where the associated data is the serialisation of the following
    structure, in the presentation language of [RFC9420]:

    ~~~
    struct {
      opaque group_ocm_address<V>;
      opaque resource_id<V>;
    } FKWrapAAD;
    ~~~

    The `group_ocm_address` field is the UTF-8 encoding of the group's
    OCM Address (the same value carried in the `shareWith` field of the
    share notification) and `resource_id` is the UTF-8 encoding of the
    `resourceId` field of the `encryption` object.  The length-prefixed
    encoding makes the pair unambiguous; raw concatenation of the two
    strings would allow distinct (address, identifier) pairs to produce
    identical associated data.  The MLS `group_id` is NOT used in the
    associated data.

5.  Sends an `MLS_APPLICATION` notification directly to all current
    Member Servers, carrying the wrapped FK keyed by `(resourceId,
groupId)`.

## FK Re-wrap on Epoch Change {#fk-rewrap}

The Group Key changes with every epoch transition, whatever the reason
for the transition: a Commit covering Add, Remove, Update, or
GroupContextExtensions proposals, or an empty Commit, all advance the
epoch.  To maintain the invariant that the current Group Key is always
sufficient to unwrap the current wrapped FK, a sending server MUST,
after processing an `MLS_COMMIT` for a group, or after joining the
successor group of a reinitialisation via its Welcome ({{reinit}}), for
every resource it shares with that group:

1.  Re-wrap the resource's current FK under the new Group Key, following
    the procedure in {{file-key-wrapping}}.
2.  Distribute the new wrapped FK to all current Member Servers, derived
    from the new ratchet tree, via `MLS_APPLICATION`.

Note that the FK itself is unchanged by this procedure; only its
wrapping is refreshed.  Whether the FK is also rotated is a separate,
removal-triggered policy decision ({{fk-rotation}}).

If the Commit added one or more members, the set of Member Servers may
have grown.  The sending server MUST identify Member Servers that are
new to the group and send them the Share Creation Notifications for its
federation shares with the group, as described in {{share-creation}}, in
addition to the wrapped FKs.  A server that joins the group after a
share was created thereby receives both the share itself and a wrapped
FK it can decrypt, since the `MLS_APPLICATION` is encrypted in an epoch
in which it is a member.

Between processing a Commit and receiving the re-wrapped FK for a
resource, a Member Server holds a wrapped FK produced under the previous
epoch's Group Key.  To remain able to serve access requests in this
window, a Member Server SHOULD retain the previous epoch's Group Key
until it has received a strictly newer wrapped FK ({{key-distribution}})
for every locally stored `(resourceId, groupId)` pair of that group, or
until a bounded time has elapsed, whichever comes first, and MUST delete
it at that point.  The security trade-off of this retention window is
discussed in Security Considerations.

The volume of `MLS_APPLICATION` traffic produced by this rule grows with
the number of shared resources and the frequency of epoch transitions;
see the batching item in Open Issues.

## Key Distribution via MLS Application Messages {#key-distribution}

Wrapped file keys are distributed to Member Servers via MLS Application
Messages, `PrivateMessage` objects carrying application data ([RFC9420]
Section 15).  Wrapped FKs are distributed at share creation and
re-distributed after every epoch transition ({{fk-rewrap}}).  A sending
server MUST process the `MLS_COMMIT` and derive the new Group Key before
sending an `MLS_APPLICATION` with updated wrapped keys, per [RFC9420]
Section 15.2.

The `PrivateMessage` application data is a JSON object carrying the
current wrapped FK for each `(resourceId, groupId)` pair in a `keys`
array, and MAY also carry a `credentials` array ({{credential-update}}):

~~~ json
{
  "keys": [
    {
      "resourceId": "3a02538b-aa54-42f2-8853-a38996e211b1",
      "groupId": "research-group@receiver.example.org",
      "wrappedKey": "<base64 nonce || wrapped_file_key || tag>"
    }
  ]
}
~~~

The `groupId` field carries the group's OCM Address, matching the
`shareWith` of the corresponding share notification, and the
`resourceId` field matches the `resourceId` in the `encryption` object
of that notification.

The `PrivateMessage` is encrypted using the current epoch's keys, so
only current group members can decrypt it.  A just-removed member cannot
decrypt the Application Message even if they receive the notification,
as they do not hold the new epoch's key material.

Member Servers store the received wrapped FKs locally, keyed by
`(resourceId, groupId)`, always replacing any previous wrapped FK for
the same pair with the latest one.  "Latest" is defined by the
authenticated `(epoch, generation)` of the enclosing `PrivateMessage`,
compared lexicographically, not by arrival order: a stored wrapped FK
MUST only be replaced by one with a strictly higher `(epoch,
generation)`.  A sending server MUST send all FK updates for a given
group through a single MLS leaf within any given epoch, since generation
counters are maintained per leaf; updates from a later epoch always
supersede updates from an earlier epoch regardless of leaf.  MLS
Application Messages may be delayed or reordered in transit ([RFC9420]
Section 15.3); a Member Server that receives an out-of-order
`MLS_APPLICATION` simply ignores wrapped FKs that are not newer than
those it already holds.  At access time, the Member Server uses its
current Group Key, derived from its current MLS state for the identified
group, to unwrap the FK.


## Transport Credential Updates {#credential-update}

The per-server transport credential of a share ({{share-creation}}) may
need to be rotated during the lifetime of the share.  In particular, in
native client deployments the user's device interacts directly with the
sending server and therefore holds its server's credential, so when such
a user is removed from the group, the credential of their server can no
longer be considered private to that server's remaining users.  On
removal of a member whose clients may have held a server's transport
credential, the sending server SHOULD rotate that server's credential
for every share affected.  Rotation MAY also be triggered by policy or
suspected leakage.

A rotated credential is delivered in an `MLS_APPLICATION` message sent
only to the affected Member Server, carrying a `credentials` array in
the application data:

~~~ json
{
  "credentials": [
    {
      "providerId": "7c084226-d9a1-11e6-bf26-cec0c932ce01",
      "groupId": "research-group@receiver.example.org",
      "recipient": "othercloud.example.org",
      "sharedSecret": "<new transport credential>"
    }
  ]
}
~~~

Each entry identifies the share by its `providerId`, the group by its
OCM Address in `groupId`, and the intended Member Server by its FQDN in
`recipient`.  A Member Server MUST ignore entries whose `recipient` does
not name itself.  Upon accepting an entry, the Member Server replaces
the stored transport credential for that share; replacement follows the
same `(epoch, generation)` supersede rule as wrapped FKs
({{key-distribution}}).  The sending server invalidates the old
credential once the rotation has been delivered.

Encrypting the credential update in the current epoch guarantees that
the removed member cannot read it, independent of transport protection:
they do not hold the new epoch's key material.  Confidentiality with
respect to other Member Servers, by contrast, rests on targeted
delivery: the `PrivateMessage` is decryptable by any group member that
obtains it, so delivering it to the affected server only is a routing
measure, not a cryptographic one (see Security Considerations).

A `keys` array and a `credentials` array MAY appear in the same
application data object when both are destined for the same single
Member Server.

## Resource Access

To access a resource:

1.  The resource is fetched from the sending server using the standard
    OCM resource access procedure ([OCM]), with the protocol details and
per-server credential from the `protocol` object of the share
notification.  For an encrypted resource, what is fetched is ciphertext.
2.  The MLS client identifies the relevant group from the `shareWith`
    field of the share notification and looks up the locally stored
`wrapped_file_key` for the `(resourceId, groupId)` pair.
3.  The MLS client derives the current Group Key from its local MLS
    state for that group and unwraps FK using the wrap AEAD of the
group's cipher suite.
4.  The MLS client decrypts the resource using FK and the content AEAD
    named in the `cipher` field of the `encryption` object.

In web-client deployments, decryption happens server-side and the
plaintext is served to the user through whatever access protocol is in
use (WebDAV [RFC4918], SFTP, webapp, etc.).  In native client
deployments, decryption happens on the user's device and the client
interacts directly with the sending server, which serves only
ciphertext.

## Resource Modification by Member Servers

A common operation is for a user on a Member Server to open a shared
encrypted resource, modify it, and save it back.  The cryptographic flow
is as follows:

1.  The Member Server fetches the encrypted resource from the sending
    server using the standard OCM resource access procedure, with the
credential from the share's `protocol` object.
2.  The Member Server identifies the relevant group from the `shareWith`
    field of the share notification, looks up the locally stored
`wrapped_file_key` for the `(resourceId, groupId)` pair, derives the
current Group Key from its local MLS state for that group, and unwraps
FK.
3.  The Member Server decrypts the resource using FK and presents the
    plaintext to the user.
4.  The user modifies the resource.
5.  The Member Server re-encrypts the modified resource using the same
    FK and the same content AEAD, but a fresh random nonce.  The nonce
MUST NOT be reused with the same key, as required by AEAD security.
6.  The Member Server uploads the re-encrypted resource to the sending
    server.  This requires the share to grant `write` permission in its
`protocol` object.

The FK is reused across modifications of the same resource because it is
bound to the group's OCM Address and `resourceId` in the AEAD associated
data, making it specific to that resource.  No new `MLS_APPLICATION`
message is needed, as the wrapped FK in all Member Servers' local stores
remains valid for the updated ciphertext.

FK rotation for a resource is only necessary on member removal in
re-encryption mode ({{fk-rotation}}).



## Sharing a Resource with Multiple Groups

A sending server MAY share the same encrypted resource with more than
one group.  The file is encrypted once, with a single FK and a single
content AEAD; the `cipher` field in every group's share notification
names that same algorithm.  Each group receives its own wrapped FK,
produced with that group's wrap AEAD, Group Key, and OCM Address:

~~~
wrapped_file_key_group1 = AEAD-Encrypt(group_key_1, nonce_1, FK,
                  FKWrapAAD(group_ocm_address_1, resource_id))
wrapped_file_key_group2 = AEAD-Encrypt(group_key_2, nonce_2, FK,
                  FKWrapAAD(group_ocm_address_2, resource_id))
~~~

A separate Share Creation Notification is sent to each Member Server of
each group.  A separate `MLS_APPLICATION` carrying the respective
wrapped FK is broadcast to each group's Member Servers.  Members of each
group can only unwrap the FK using their own group's Group Key and
cannot access the other group's wrapped FK or Group Key.

The sending server MUST maintain a mapping from each resource to all
groups it has been shared with.  This mapping is required to correctly
handle member removal in re-encryption mode, as described in the
following section.

## FK Rotation (RECOMMENDED) {#fk-rotation}

FK rotation is distinct from the re-wrap performed on every epoch change
({{fk-rewrap}}): rotation generates a new FK and re-encrypts the
resource, whereas a re-wrap only refreshes the wrapping of the existing
FK.  A sending server SHOULD rotate the FK for a resource when a member
is removed from any group that has access to it.  FK rotation may also
be triggered by other factors, such as periodic key rotation policy,
regulatory requirements, or a suspected compromise of key material.
Applications SHOULD define a policy for the frequency of FK rotation
independent of membership changes.

When rotating the FK for a resource, the sending server:

1.  Generates a new FK for the resource.
2.  Re-encrypts the resource with the new FK.
3.  For every group that has access to the resource, wraps the new FK
    using that group's current Group Key:

    ~~~
    new_wrapped_file_key_groupN = AEAD-Encrypt(group_key_N, nonce_N,
          new_FK, FKWrapAAD(group_ocm_address_N, resource_id))
    ~~~

4.  Broadcasts an `MLS_APPLICATION` notification carrying the respective
    new wrapped FK directly to each group's Member Servers.

Distributing the new wrapped FK to all groups that share the resource is
necessary because all groups share the same ciphertext.  If only one
group received the new wrapped FK, members of other groups would hold a
wrapped FK that no longer decrypts the current ciphertext.

A member removed from one group but still a member of another group that
shares the same resource retains the ability to decrypt that resource
through the second group.  This is correct and intended behaviour:
access is determined by current group membership, and the user remains a
member of the second group.  The default safe rule is to rotate the FK
and redistribute to all groups on any removal event.  A sending server
MAY instead compare the unique set of users with access before and after
an epoch change, and skip FK rotation if that set is unchanged, for
example because the removed user remains a member of every other group
that has access to the same resource.  Whether this optimisation is
worth the added complexity depends on the nature of the resource and the
frequency of membership changes.

Member addition does not require FK rotation.  The new member receives
the current Group Key via their Welcome, and the re-wrap triggered by
the Add Commit ({{fk-rewrap}}) delivers a wrapped FK, encrypted in an
epoch in which the new member is a member, that the new member can
unwrap with that Group Key.

## Member Removal: Key-reuse Mode (OPTIONAL)

Where re-encryption is impractical, for example due to frequent changes
of very large files, and where all participating servers belong to a
formal federation with explicit governance and mutual trust, a sending
server MAY instead keep the existing FK.  In that case no action beyond
the standard re-wrap on epoch change ({{fk-rewrap}}) is required: the
Remove Commit advances the epoch, and the sending server re-wraps the
existing FK under the new Group Key and distributes it to the remaining
Member Servers of the affected group.

When a resource is shared with multiple groups, only the epoch of the
group from which the member was removed has advanced, so only that
group's FK wrapping is refreshed.  The wrapped FKs for other groups are
unchanged and remain valid for their respective members.

In this mode, access-follows-membership relies on trust rather than
cryptography: the FK itself is unchanged, so a removed member's server
and, in native client deployments, the removed user's devices, may still
hold the superseded Group Key together with the old wrapped FK, or the
unwrapped FK itself, any of which decrypts the unchanged ciphertext.
Key-reuse mode therefore relies on trusting servers to discard key
material they are no longer entitled to after a Remove Commit.  A
removed member who is also a member of another group that has access to
the same resource will still be able to decrypt via that group's wrapped
FK, which is the expected behaviour - they remain a member of that
group.  This assumption is appropriate within a formal federation but
SHOULD NOT be made in open or ad-hoc sharing contexts.

The sending server's choice of mode is its own policy decision and is
not signalled in the protocol.

## Member Removal: OCM Notifications

Member removal requires no OCM-level notification by itself.  Because
federation shares are addressed to the group ({{share-creation}}), each
Member Server observes the Remove Commit and re-evaluates which of its
local users the share resolves to; a removed user loses access without
any action by the sending server.  If the removed member's clients may
have held their server's transport credential, the sending server SHOULD
additionally rotate that credential ({{credential-update}}).

When the last member homed on a given server is removed from the group,
that server no longer has any user with access.  A well-behaved sending
server SHOULD then reconcile the OCM state of the share, revoke that
server's per-server transport credential ({{share-creation}}), and send
a `SHARE_UNSHARED` notification to the `/notifications` endpoint of that
server.

# Share Creation {#share-creation}

The sending server sends one OCM Share Creation Notification directly to
each current Member Server, identified through the OCM Addresses in the
ratchet tree's leaf credentials.  This is standard OCM server-to-server
communication, with `shareWith` set to the group's OCM Address and
`shareType` set to `"federation"`.  The share is addressed to the group
as the Receiving Party; no per-user notifications are sent.

A federation share is a standard OCM share: every field that is REQUIRED
by [OCM], including the `protocol` object, is REQUIRED here too, and
resource access follows the standard OCM resource access procedure
driven by the `protocol` object.  For encrypted resources the protocol
endpoint serves ciphertext; the plaintext is obtained by unwrapping the
FK as described in the Encryption Model.

Each Member Server SHOULD be given its own `sharedSecret` (or equivalent
protocol credential) in its copy of the notification.  The credential is
per server, not per user: all users on a Member Server share it,
mirroring how the server holds MLS state on behalf of its users.
Distinct per-server credentials allow the sending server to revoke a
single server's transport access, for example when the last group member
on that server is removed, without affecting other Member Servers.
Share Creation Notifications sent to servers that join the group later
({{fk-rewrap}}) carry credentials minted at that time, and a server's
credential can be rotated during the share's lifetime
({{credential-update}}).

Share Permissions apply uniformly to the whole group: every member of
the group receives the same permissions on the resource.  A sending
server that needs different permissions for different parties should use
separate groups or individual shares.  Receiving Server criteria that
affect the share payload, such as `must-exchange-token`, are evaluated
per Member Server against that server's discovery document, exactly as
in base OCM.

The receiving server resolves `shareWith` against its local MLS state:
it identifies the group whose `group_ocm_address` ({{admin-set}})
matches the `shareWith` value and delivers the share to every local user
whose leaf credential appears in that group's ratchet tree.  On every
subsequent `MLS_COMMIT` the receiving server MUST re-evaluate this
resolution, so that local users added to the group gain access to
existing federation shares, and removed users lose it, without any
further OCM notifications.

Addressing the share to the group also allows the receiving server to
distinguish between shares of the same resource arriving via different
groups - a user may be a member of two groups that both have access to
the same resource from the same sending server - and to correctly key
its local wrapped FK store by `(resourceId, groupId)` rather than
`resourceId` alone, where `groupId` is the group OCM Address carried in
`shareWith`, ensuring that FK updates delivered via `MLS_APPLICATION`
are applied to the correct entry.

Because notifications can be delayed or reordered in transit, a
federation share MAY arrive before the receiving server has processed
the Welcome or Commit that made it a Member Server of the group.  A
receiving server that does not recognise the `shareWith` value as a
known group SHOULD queue the share, or reject it in a way that causes
the sender to retry, rather than fail it permanently.  Since sending
servers only contact servers present in the ratchet tree, this condition
is transient.

When an `MLS_COMMIT` adds one or more members to the group, the sending
server MUST send each Member Server that is new to the group a Share
Creation Notification for every federation share it has with that group,
encrypted or not.  For encrypted resources this accompanies the
re-wrapped FK ({{fk-rewrap}}).  A server that joins the group after a
share was created thereby learns of the shares its users now have access
to without any further action by its users.

Each notification MAY include the optional `encryption` field:

~~~ json
{
  "shareWith": "research-group@receiver.example.org",
  "shareType": "federation",
  "resourceType": "file",
  "sender": "alice@cloud.example.org",
  "owner": "alice@cloud.example.org",
  "providerId": "7c084226-d9a1-11e6-bf26-cec0c932ce01",
  "name": "experiment-data.tar",
  "protocol": {
    "name": "multi",
    "webdav": {
      "uri": "experiment-data.tar",
      "sharedSecret": "<per-Member-Server secret>",
      "permissions": ["read", "write"]
    }
  },
  "encryption": {
    "scheme": "ocm-mls-1",
    "cipher": "AES-256-GCM",
    "resourceId": "3a02538b-aa54-42f2-8853-a38996e211b1"
  }
}
~~~

The `encryption` field is OPTIONAL.  If absent, the resource is
unencrypted and the share follows the standard OCM flow without
modification.  If present, it carries all encryption-related parameters:
`scheme` identifies the encryption scheme, for which this document
defines `"ocm-mls-1"`; `resourceId` is the stable resource identifier
described in {{resource-id}}; and `cipher` (REQUIRED when `encryption`
is present) names the content AEAD that the resource is encrypted with
({{file-key-wrapping}}), one of the AEAD algorithms defined for HPKE
([RFC9180] Section 7.3): `"AES-128-GCM"`, `"AES-256-GCM"`, or
`"CHACHA20-POLY1305"`.  The field signals that the FK is distributed via
the `MLS_APPLICATION` mechanism keyed by `(resourceId, groupId)`.  No
epoch information is carried in the share notification.  Member Servers
always hold the current wrapped FK for each `(resourceId, groupId)` pair
and use their current Group Key to unwrap it at access time.

The Group Owner Server is not involved in the delivery of OCM share
notifications.  All other OCM notifications relating to a share, such as
share updates and share deletions, are likewise sent directly from the
sending server to each Member Server, referencing the share by its
`providerId` as in base OCM.

# Trust and Authentication {#trust-and-authentication}

The Authentication Service role ([RFC9420] Section 3) is fulfilled by
each user's home OCM server: the server that publishes a user's
KeyPackages attests the binding between the user's OCM Address and their
signature key.  Because the basic credential itself carries no
verifiable binding, the attestation lies in the delivery channel.  

## Validation procedure

A KeyPackage is considered validated with the AS when all of the
following hold:

- it was fetched from the `<endPoint>/mls-key-packages` endpoint of the
server named in the credential's OCM Address, over TLS, with the
response signed using HTTP Signatures [RFC9421] verifying against that
server's JWKS [RFC7517];
- the OCM Address in the credential is identical to the `userId` the
KeyPackage was requested for, which is the OCM Address of the user the
requester intends to add; in particular, its host part names the server
the KeyPackage was fetched from; and
- the KeyPackage signature verifies with the `signature_key` of its
LeafNode, proving possession of the private key ([RFC9420] Section
10.1).

Requests to the KeyPackage endpoint are signed at the server level
({{security-considerations}}), so in native client deployments the
fetch is performed by the admin's home server on the admin client's
behalf.  The home server SHOULD relay the response with its HTTP
Message Signature intact, allowing the native client to verify the
channel binding end-to-end against the target server's published JWKS;
a native client that cannot do so delegates the channel verification to
its home server and verifies the KeyPackage signature itself.

[RFC9420] Section 5.3.1 requires a credential to be validated whenever
it is introduced into the group.  This protocol distributes that duty to
the party that introduces the credential:

- Add: the admin client committing an Add MUST have validated the
KeyPackage as described above.  Other members accept the new leaf on the
strength of the admin-signed Commit; they do not contact the new
member's home server.
- Update proposals, and Commits whose UpdatePath carries a new
credential: the successor credential MUST present the same OCM Address
as the credential it replaces, and members MUST reject the proposal or
Commit otherwise.  This is the successor-credential policy anticipated
by [RFC9420] Section 5.3.1.  Continuity of the signature key is anchored
in MLS itself: the message introducing the new leaf is signed with the
member's current key, so only the holder of the previous key can rotate
to a new one.
- Joining via Welcome: the joiner MUST verify the GroupInfo signature
and the integrity of the ratchet tree as required by [RFC9420] Section
12.4.3.1, and MUST verify that every leaf credential is a basic
credential carrying a well-formed OCM Address.  The joiner accepts the
bindings of those credentials transitively, on the basis that each was
validated by an admin client when it was introduced.  It MAY
additionally re-validate any leaf against the `/mls-key-packages`
endpoint of its home server, but such re-validation can fail benignly,
since published KeyPackages rotate independently of leaves already in
groups.

In this transitive model, each home server is trusted to attest only its
own users, and each admin client is trusted to have performed the
attestation check at introduction time.  A malicious home server can
impersonate its own users - it is their Authentication Service - but it
cannot impersonate users of other servers, since it cannot produce an
authenticated KeyPackage delivery for an OCM Address whose host part it
does not serve.

Users who require protection of their key material from their own server
should choose a native client implementation where cryptographic
operations occur on the user's device.

# Security Considerations {#security-considerations}

**Trust model.** In web-client deployments, the OCM Server holds the
Group Key and can decrypt any resource shared with the group on behalf
of its users.  This is consistent with the standard OCM Server trust
model, where users trust their server with their data, and with OCM's
existing approach of abstracting security to the server level.  Native
client deployments provide stronger isolation, as the server does not
hold key material.  Implementations SHOULD move toward native client
deployments over time.

**FK rotation vs key-reuse.** FK rotation provides cryptographic access
revocation on member removal, independent of trust assumptions, and
SHOULD also be performed periodically or when key compromise is
suspected.  In key-reuse mode the FK is unchanged and the ciphertext is
not re-encrypted, so revocation is not cryptographic: it relies on
trusting servers to discard all key material they are no longer entitled
to - superseded Group Keys, old wrapped FKs, and any cached unwrapped
FKs - after a Remove Commit.  Key-reuse mode SHOULD only be used within
formal federations with governance agreements that enforce this
behaviour.

**Two access-control layers.** For an encrypted federation share, access
is controlled at two independent layers: the per-server transport
credential in the `protocol` object gates who can fetch the ciphertext,
and the Group Key gates who can unwrap the FK and decrypt it.
Confidentiality rests on the cryptographic layer alone; the transport
credential provides defence in depth and is shared by all users on a
Member Server.  The two layers can diverge: a server whose last group
member was just removed may still hold a valid transport credential
until the sending server revokes it, which is why revocation SHOULD
accompany the `SHARE_UNSHARED` notification.  For unencrypted federation
shares the transport credential is the only access control, exactly as
in base OCM, and access-follows-membership then depends on the receiving
server re-evaluating share resolution on every Commit
({{share-creation}}) and on the sending server revoking the credentials
of departed servers promptly.

**Credential rotation.** Rotated transport credentials are delivered in
group-encrypted `MLS_APPLICATION` messages sent only to the affected
server ({{credential-update}}).  A removed member is excluded
cryptographically: it does not hold the new epoch's key material.  Other
Member Servers are excluded only by targeted delivery; a credential
message that leaks to another member server is readable by it.  Since
every Member Server already holds transport access to the same
ciphertext under its own credential, the impact of such a leak is
limited to transport-layer attribution.

**Key distribution via Application Messages.** Wrapped FKs are
distributed in MLS `PrivateMessage` objects encrypted in the current
epoch.  A removed member cannot decrypt these messages as they do not
hold the new epoch's key material.  Because sending servers re-wrap and
redistribute FKs after every epoch transition ({{fk-rewrap}}), and
Member Servers always replace their locally stored wrapped FK with the
latest received, the current Group Key is always sufficient for
unwrapping once the re-wrapped FKs have arrived.

**Group Key retention window.** Between processing a Commit and
receiving the re-wrapped FKs for the new epoch ({{fk-rewrap}}), a Member
Server may retain the previous epoch's Group Key in order to keep
serving access requests.  This retention slightly weakens forward
secrecy for the duration of the window: a server compromised during the
window exposes the previous epoch's Group Key in addition to the current
one.  The window is bounded by the arrival of the re-wrapped FKs, and
Member Servers MUST delete the previous Group Key as soon as it is no
longer needed, or after a bounded time, whichever comes first.

**Commit ordering.** The Group Owner Server is the sole arbiter of
Commits, eliminating conflicting Commits for the same epoch during
normal operation.  A compromised or unavailable Group Owner Server can
stall epoch transitions, but it cannot decrypt resource content, and it
cannot cause the group to accept a Commit constructed by a non-admin
client, because every Member Server independently verifies the committer
against the admin set before processing a Commit ({{admins}}).  The role
passes automatically to the next admin's server when the first admin
leaves the group ({{admin-set}}), and an unavailable arbiter is
eventually replaced through failover ({{failover}}), during which
conflicting Commits can briefly exist and are resolved
deterministically.

**Forked-state retention.** During a detected failover window, Member
Servers retain the previous epoch's group state so that they can revert
to the winning Commit ({{failover}}).  Retaining forked state weakens
forward secrecy for its duration; [RFC9420] Section 14 requires such
state to be deleted promptly, so the retention is bounded in time and
limited to servers that have observed the failover trigger.

**Rejoin.** The rejoin procedure ({{rejoin}}) lets a home server replace
its own users' leaves with fresh KeyPackages on the strength of its HTTP
Signature alone, without per-request admin approval.  This grants no new
capability: the home server is already the trust anchor for its own
users' KeyPackages and could substitute their keys at any time through
the ordinary KeyPackage endpoint.  Because admin clients verify that a
rejoin only replaces leaves whose OCM Addresses name the requesting
server and that are already present in the ratchet tree, a rejoin can
never admit a new party.

**Admin liveness and removal latency.** A Remove proposal takes
cryptographic effect only when an admin client commits it.  Removing
another member additionally requires explicit admin approval, so the
revocation latency for a membership change is bounded by admin
availability.  Groups SHOULD appoint multiple admins, on multiple Member
Servers, to keep this window small and to avoid stalling group
operations when a single admin is offline.  The same bound applies to
the post-compromise security provided by Update proposals, which only
take effect once committed.

**Application message ordering.** Per [RFC9420] Section 15.2, sending
servers MUST apply a new epoch secret before encrypting any application
data.  `MLS_APPLICATION` messages carrying re-wrapped keys MUST be sent
only after the sending server has processed the corresponding
`MLS_COMMIT`.

**Ordering and the DS.** All ordering in this protocol derives from
MLS-authenticated metadata: Commits are ordered by the epoch they
advance, and FK updates by the `(epoch, generation)` of the enclosing
`PrivateMessage`.  No unauthenticated transport counter is relied upon.
Servers in the DS role can still delay, drop, or selectively withhold
messages, but cannot reorder them undetectably or forge them, consistent
with the MLS threat model ([RFC9420] Section 16.9).

**Reinitialisation continuity.** A reinitialisation Welcome is accepted
only with a resumption PSK from the old group's final epoch and after
verification of the old group's ReInit Commit and of membership
preservation ({{reinit}}).  A party that was not a member of the old
group's final epoch cannot produce that PSK, so the binding between a
group's OCM Address and its MLS group state cannot be hijacked through a
forged reinitialisation.

**Handshake message confidentiality.** Proposals and Commits are sent as
PublicMessage, so group operations are visible to the servers that
handle them.  The MLS architecture [RFC9750] recommends encrypting
handshake messages to hide membership changes and signatures from the
Delivery Service; this protocol deliberately departs from that
recommendation because the servers performing the DS role must know the
group's membership anyway: sending servers derive notification
recipients from the ratchet tree, and receiving servers resolve
federation shares to their local users.  No information is exposed to
those servers beyond what their OCM duties already require, and
transport protection (TLS and HTTP Signatures [RFC9421]) prevents
exposure to outside observers.  Application Messages, which carry key
material, are always encrypted as PrivateMessage.

**Group membership privacy.** The ratchet tree contains every member's
OCM Address and is held by every Member Server, so the full membership
of a group is visible to all servers that have a member in it.  This is
inherent to the design - servers route shares and notifications using
exactly this information - but it sets the privacy baseline: federated
groups are not anonymous, and membership of a group is as visible to the
participating servers as membership of a shared folder.  The tree is not
exposed to servers outside the group, and transport protection prevents
exposure to third parties.

**Admin set integrity.** The admin set and the group's OCM Address are
carried in the GroupContext ({{admin-set}}), so they are covered by the
MLS confirmation tag and agreed upon by all members of every epoch.  A
malicious server cannot unilaterally appoint admins or seize the Group
Owner Server role; changing the admin set requires a Commit constructed
by an existing admin client.

**Post-compromise security.** Member Servers SHOULD periodically rotate
their users' leaf keys via Update proposals to maintain post-compromise
security ([RFC9420] Section 16.6).  Members that do not update SHOULD
eventually be removed from the group.

**Key material deletion.** Security-sensitive values MUST be deleted as
soon as they are consumed, per [RFC9420] Section 9.2.  In particular,
the exporter_secret used to derive the Group Key must not be retained
after the Group Key has been derived.

**KeyPackage reuse.** KeyPackages MUST be one-time use, except for a
designated last resort KeyPackage used when a user's single-use
KeyPackages are exhausted ([RFC9420] Section 16.8).  Servers MUST remove
a KeyPackage that has been consumed, and SHOULD rate-limit KeyPackage
requests to make exhaustion attacks impractical.

**User enumeration.** A server MUST only reply to HTTPS GET requests
signed using HTTP Message Signatures [RFC9421] and SHOULD implement rate
limiting and other access control methods on the `/mls-key-packages`
endpoint to avoid user enumeration.

# IANA Considerations

The MLS Exporter label `"ocm-group-key"` used in the Group Key
Derivation section is to be registered in the "MLS Exporter Labels"
registry defined in [RFC9420] Section 17.8, to avoid collisions with
other applications using the MLS Exporter:

- Label: "ocm-group-key"
- Recommended: N
- Reference: This document

The GroupContext extension `ocm_federated_group` defined in
{{admin-set}} is to be registered in the "MLS Extension Types" registry
defined in [RFC9420] Section 17.3:

- Value: TBD
- Name: ocm_federated_group
- Message(s): GC
- Recommended: N
- Reference: This document

# Open Issues

This section collects open design issues and shall be removed before
publication.

- **Streaming decryption.** A chunked AEAD construction enabling
streaming decryption of large files should be specified for native
client implementations.  The specific construction and its interaction
with the FK wrapping model needs to be defined.
- **Application Message batching.** The frequency and batching of
`MLS_APPLICATION` messages carrying wrapped FKs needs to be defined.
Since every epoch transition triggers a re-wrap of every shared
resource's FK ({{fk-rewrap}}), batching is load-bearing when many shares
exist and epoch transitions are frequent.
- **Commit retransmission.** A missed Commit is detected directly from
the MLS epoch: a Commit arriving for a later epoch than the next
expected one indicates a gap.  A mechanism for requesting retransmission
of missed Commits, from the Group Owner Server or any Admin Server,
needs to be specified.  Retransmission is the first remedy for a gap;
the rejoin procedure ({{rejoin}}) is the fallback when retransmitted
Commits can no longer be applied. The proposed OCM Journaling mechanism
can be useful in this context.

# References

## Normative References

[OCM] Lo Presti, G., de Jong, M.B., Baghbani, M. and Nordin, M.  "[Open
Cloud
Mesh](https://datatracker.ietf.org/doc/draft-ietf-ocm-open-cloud-mesh/)",
Work in Progress, Internet-Draft.

[RFC2119] Bradner, S.  "[Key words for use in RFCs to Indicate
Requirement Levels](https://datatracker.ietf.org/doc/html/rfc2119)",
March 1997.

[RFC7517] Jones, M., "[JSON Web Key
(JWK)](https://datatracker.ietf.org/doc/html/rfc7517)", May 2015.

[RFC8174] Leiba, B.  "[Ambiguity of Uppercase vs Lowercase in RFC 2119
Key Words](https://datatracker.ietf.org/html/rfc8174)", May 2017.

[RFC9180] Barnes, R., Bhargavan, K., Lipp, B. and Wood, C. A.  "[Hybrid
Public Key Encryption](https://datatracker.ietf.org/doc/html/rfc9180)",
February 2022.

[RFC9420] Barnes, R., Beurdouche, B., Robert, R., Millican, J., Omara,
E. and Cohn-Gordon, K.  "[The Messaging Layer Security (MLS)
Protocol](https://datatracker.ietf.org/doc/html/rfc9420)", July 2023.

[RFC9421] Backman, A., Richer, J. and Sporny, M.  "[HTTP Message
Signatures](https://datatracker.ietf.org/doc/html/rfc9421)", February
2024.

## Informative References

[RFC4918] Dusseault, L. M.  "[HTTP Extensions for Web Distributed
Authoring and
Versioning](https://datatracker.ietf.org/doc/html/rfc4918)", June 2007.

[RFC9750] Beurdouche, B., Rescorla, E., Omara, E., Inguva, S. and Duric,
A.  "[The Messaging Layer Security (MLS)
Architecture](https://datatracker.ietf.org/doc/html/rfc9750)", April
2025.

# Acknowledgements

This work builds on the Open Cloud Mesh specification and the
discussions in the OCM community.

Work on this document has been funded by [Sovereign Tech Agency][sta]
through the [Tech Fund][sta-fund], with a specific [project][sta-ocm].

[sta-ocm]: https://www.sovereign.tech/tech/open-cloud-mesh

[sta-fund]: https://www.sovereign.tech/programs/fund

--- back
