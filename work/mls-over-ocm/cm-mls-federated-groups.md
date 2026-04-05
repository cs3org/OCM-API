# Federated Groups in OCM using MLS

---

## Abstract

This document proposes an extension to the Open Cloud Mesh (OCM)
protocol to support federated groups as receiving parties of shares.
This is achieved using the Messaging Layer Security (MLS) protocol
[RFC9420] as a group management layer. MLS is used for establishing and
rotating a shared group key across federated group members, as well as
for maintaining group state. This gives us not only a way of federating
group membership, but also a standardized way of distributing encryption
keys in a cryptographically secure way, so that we can optionally
encrypt and decrypt files shared across a group. MLS usage in OCM is not
used to carry application messages (i.e. for "chatting"), but rather as
a vehicle for group management that gives users optional encryption
capabilities for resources shared with federated groups.

In many EFSS systems, there is a tight coupling between a client and a
server, because the server offers a built in web interface as it's
primary client. In addition to this a `sync client` is often offered as
a way of syncing files between the EFSS system and the users devices.

In MLS, a client is defined as an agent that establishes shared
cryptographic state with other clients, defined by the cryptographic
keys it holds.

An EFSS server meets this definition directly. For deployments where the
primary user interface is a web client, the EFSS fulfils the MLS client
role server-side, holding key material on behalf of its users and the
word `client` as used in this text should not neccessarily be taken to
mean the users file sync client. Implementations that do provide a
native client application SHOULD perform cryptographic operations in the
native client on the users devices, rather than on the server, because
this provides stronger isolation of key material from the server. In
either case the same MLS client model applies.

Files shared with a group can optionally be encrypted with a per-file
key (FK), wrapped with the current group key. The group key is derived
from the MLS epoch secret and rotates with every epoch transition. When
a member is added to a group, their MLS client receives the new group
key and can immediately decrypt all resources shared with the group.
When a member is removed, the group key rotates.

On member removal, a sending server SHOULD rotate the FK for affected
resources, re-encrypting with a new FK and distributing the new wrapped
FK to all groups that share those resources. This provides strong
cryptographic guarantees regardless of trust assumptions. Where
re-encryption is impractical, for example due to frequent changes in
groups with very large files, and where participating servers belong to
a formal federation with explicit governance and mutual trust, a sending
server acting as an MLS client MAY instead re-wrap the existing FK under
the new group key without re-encrypting the file data. In this case,
access-follows-membership relies on trusting member servers not to
retain superseded group keys.

---

## 1. Introduction

OCM currently supports sharing resources with individual users across
federated servers and with groups on a single server. The specification
also defines a `shareType` of `"federation"` but does not further
specify its semantics. This proposal gives `"federation"` a concrete
definition: a federated group identified by an OCM Address such as
`research-group@cloud.example.org` whose membership spans multiple OCM
servers, with group state managed through the MLS epoch mechanism.

Each user who is a member of a federated group has their own MLS leaf
node, enabling individual users to be added and removed independently.
The EFSS can act as the MLS client on behalf of its users. For
implementations where the primary interface is a web client, the EFSS
holds and uses key material server-side. Implementations with a native
client application SHOULD perform cryptographic operations in the native
client, with the server acting as a relay for MLS messages.

Throughout this document, actions described as being performed by an OCM
server are understood to be performed by that server in its capacity as
an MLS client, on behalf of one of its users. The server holds no
independent group membership or cryptographic state independent of it's
users.

The group and its membership exist and evolve independently of any
sharing activity. A user that wants to share a resource with a group can
do so without the need to know the current membership details of that
group. The Group Owner Server acts as the MLS Delivery Service, the
single distribution point for all MLS group lifecycle messages and FK
distribution. OCM share notifications are sent directly between sending
servers and member servers. Group membership changes are managed
entirely through MLS group lifecycle operations.

When a member is removed from the group, sending servers are notified
via the MLS commit mechanism and MAY choose to re-encrypt affected
resources or re-wrap existing per-file keys, depending on their policy
and the nature of the shared data.

---

## 2. MLS Roles in OCM

MLS is designed to operate with two supporting services: an
Authentication Service (AS) and a Delivery Service (DS). This section
describes how those roles are fulfilled by OCM.

### 2.1. Authentication Service

The AS role is fulfilled by each user's home OCM server. MLS Credentials
in KeyPackages identify users by their OCM Address and are signed by the
user's own signing key pair. Each user has their own distinct signing
key pair so that individual users can be identified and addressed
independently within the MLS group, for example to add or remove a
specific user. In web-client deployments the key pair is generated and
held by the EFSS on the user's behalf. In native client deployments the
key pair is held on the user's device and the server's role is limited
to publishing the public key.

A group member authenticates another member's credential by fetching
their KeyPackage from the canonical `<endPoint>/mls-key-packages`
endpoint of the server named in the OCM Address and verifying the
signature against the published public key. The server-to-server channel
over which KeyPackages are fetched is authenticated using HTTP
Signatures [RFC9421], with the server's public key discoverable via its
JWKS endpoint at `/.well-known/jwks.json` [RFC7517].

### 2.2. Delivery Service

The Group Owner Server fulfils the DS role for MLS group lifecycle
messages. It serialises incoming `MLS_PROPOSAL` notifications into
Commits, broadcasts `MLS_COMMIT` notifications to all member servers
with monotonically increasing sequence numbers, and broadcasts
`MLS_APPLICATION` messages carrying wrapped file keys to all current
member servers. All MLS messages are delivered to the
`<endPoint>/notifications` endpoint of each recipient server,
authenticated with HTTP Signatures [RFC9421].

By designating the Group Owner Server as the sole committer, this design
eliminates the possibility of conflicting Commits for the same epoch,
satisfying the sequencing requirement of [RFC9420] Section 14 without
requiring a conflict resolution protocol.

OCM share notifications are sent directly from the sending server to
each member server. Since sending servers must be group members, they
hold the current MLS ratchet tree after processing each `MLS_COMMIT`,
and can derive the current membership — specifically the OCM Address in
each leaf node's credential — to determine which member servers to
contact. No proxying through the Group Owner Server is required for
OCM-level communication.

MLS is designed to protect confidentiality and integrity even against a
misbehaving DS. The Group Owner Server carries more responsibility than
a typical MLS DS since it also relays key distribution messages, but the
MLS security properties with respect to message confidentiality still
hold.

---

## 3. Design Principles

- **MLS for group key management only.** MLS establishes and rotates a
  shared group key. The only MLS application messages used in this
  protocol carry wrapped file keys as described in Section 8.3.

- **At least one MLS leaf per user.** Each user who is a member of a
  federated group has at least one MLS leaf node, enabling individual
  users to be added and removed independently. In web-client deployments
  the EFSS manages a single leaf node per user on their behalf. In
  native client deployments each user may have a leaf node per device.

- **The EFSS is the MLS client.** An EFSS meets the MLS definition of a
  client. For web-client deployments this means key material is held
  server-side. For native client deployments cryptographic operations
  SHOULD be performed in the native client.

- **Encryption is optional.** MLS group management is useful
  independently of whether encryption is used. A federation share MAY be
  unencrypted, in which case the `encryption` field is omitted from the
  Share Creation Notification and the MLS layer provides only group
  membership management.

- **FK rotation on member removal.** On member removal, a sending server
  SHOULD rotate the FK for affected resources and distribute the new
  wrapped FK to all groups that share those resources. FK rotation may
  also be triggered by other factors such as periodic key rotation
  policy or suspected key compromise. Member addition does not require
  FK rotation.

- **Key-reuse mode as an alternative.** Where re-encryption on removal
  is impractical and where participating servers are mutually trusted
  within a formal federation, a sending server MAY instead re-wrap the
  existing FK under the new group key.

- **Sending servers must have group members.** To share a resource with
  a group, the sending server must have at least one user who is a
  member of that group, allowing it to work out the members to share
  with, and to be able to wrap the FK for encrypted shares. This is by
  design, as to mitigate spam shares and other abusive behaviour.

- **OCM messages are still just OCM messages.** MLS group lifecycle
  messages and FK distribution flow through the Group Owner Server
  acting as DS. OCM share notifications flow directly from the sending
  server to each member server, derived from the sending server's local
  view of group membership from the MLS ratchet tree. No proxying of OCM
  messages through the Group Owner Server is required.

- **Sending servers derive membership from the ratchet tree.** Since
  sending servers must have group members, they process all `MLS_COMMIT`
  messages and hold the current ratchet tree. The OCM Address in each
  leaf node's credential identifies the corresponding member server. The
  sending server uses this to determine which member servers to contact
  directly for share notifications and FK distribution.

- **Push-based FK distribution via the Group Owner Server.** Wrapped
  file keys are distributed via `MLS_APPLICATION` through the Group
  Owner Server, which broadcasts them to all current member servers.
  Member servers always hold the current wrapped FK for each resource
  and use their current Group Key to unwrap it at access time.

- **Minimal protocol surface.** The `shareType: "federation"` value
  already defined in the OCM spec is used without modification. All new
  server-to-server messages use the existing `/notifications` endpoint
  with new `notificationType` values. Two new fields are added to the
  Share Creation Notification: `groupId` (required for all federation
  shares) and `encryption` (optional, present only for encrypted
  resources).

---

## 4. Terminology

This document uses terminology from draft-ietf-ocm-open-cloud-mesh-04
and [RFC9420]. Additional definitions:

- **Group** — A Receiving Party identified by an OCM Address whose
  identifier resolves to a set of members spanning multiple OCM servers,
  with group state managed through MLS. In [RFC9420] a group is defined
  as: "a logical collection of clients that share a common secret value
  at any given time. Its state is represented as a linear sequence of
  epochs in which each epoch depends on its predecessor."

- **MLS Client** — As defined in [RFC9420]: an agent that establishes
  shared cryptographic state with other clients, defined by the
  cryptographic keys it holds. In this protocol the EFSS fulfils this
  role.

- **Member Server** — An OCM server with one or more users who are
  members of a given group, acting as MLS client on their behalf.

- **Group Owner Server** — The OCM server at which the Group is
  registered. Fulfils the MLS Delivery Service role, is the sole
  committer for the group, and relays FK distribution messages to member
  servers via `MLS_APPLICATION`.

- **Group Key** — A 32-byte symmetric key derived from the current MLS
  epoch secret via the MLS Exporter. Rotates with every epoch
  transition.

- **File Key (FK)** — A random symmetric key used to encrypt a single
  shared resource. Wrapped with the current Group Key and distributed to
  member servers via MLS Application Messages. Member servers always
  store the most current wrapped FK for each resource.

- **Re-encryption mode** — On member removal, the sending server
  generates a new FK, re-encrypts the resource, and distributes the new
  wrapped key. Provides strong cryptographic guarantees independent of
  trust assumptions.

- **Key-reuse mode** — On member removal, the existing FK is re-wrapped
  under the new Group Key without re-encrypting the resource.
  Appropriate only within formally trusted federations and where
  re-encryption is impractical. Mode is not a binary choice, instead
  sending servers can choose one mode for one epoch, and another mode
  for another epoch, depending on policy and other circumstances.

- **KeyPackage** — As defined in [RFC9420]. A signed object that enables
  adding an MLS client to a group asynchronously. KeyPackages MUST be
  used only once ([RFC9420] §16.8).

---

## 5. Discovery

A server signals support for federation shares by including
`"federation"` in the `shareTypes` array for a given resource type in
its OCM discovery document at `/.well-known/ocm`:

```json
{
  "enabled": true,
  "apiVersion": "1.1.0",
  "endPoint": "https://cloud.example.org/ocm",
  "provider": "Example Cloud",
  "resourceTypes": [
    {
      "name": "file",
      "shareTypes": ["user", "group", "federation"],
      "protocols": { "webdav": "/webdav/" }
    }
  ]
}
```

No additional discovery fields are introduced. The notifications
endpoint is derived as `<endPoint>/notifications` per the base OCM
specification. The KeyPackage endpoint is derived as
`<endPoint>/mls-key-packages`.

---

## 6. KeyPackage Distribution

Each EFSS acting as an MLS client generates and maintains KeyPackages
for its users and exposes them at:

```
GET <endPoint>/mls-key-packages?userId={userId}
```

Response:

```json
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
```

In native client deployments, the user's device generates KeyPackages
and publishes them to the home server, which exposes them at the same
endpoint without interpreting them.

Each KeyPackage contains an MLS Credential identifying the user by their
OCM Address, signed by the user's own signing key pair. Users who
require stronger isolation of key material from their server should use
a native client implementation.

KeyPackages MUST be one-time use ([RFC9420] §16.8). The server MUST
remove a KeyPackage after it has been delivered. Servers SHOULD
pre-generate multiple KeyPackages per user to support concurrent group
additions.

---

## 7. Group Lifecycle

The group lifecycle is entirely independent of the share lifecycle.
Members are added and removed through MLS group operations conveyed via
the `/notifications` endpoint. None of these operations are triggered by
or coupled to share creation.

### 7.1. Group Creation

The Group Owner Server creates an MLS group and initialises leaf nodes
for each of its users who are initial members. No notifications are
required for this step. The group becomes addressable at its OCM Address
immediately upon creation.

### 7.2. MLS Notification Types

All MLS group lifecycle messages are sent as OCM Notifications to
`<endPoint>/notifications` using HTTP POST with
`Content-Type: application/json` and HTTP Signatures [RFC9421].

Since `MLS_PROPOSAL` is delivered only to the Group Owner Server and
never broadcast to other member servers, those member servers never
observe pending proposals. The Group Owner Server, as sole committer,
satisfies [RFC9420] §12.4 by processing the Commit before sending any
application data.

#### 7.2.1. `MLS_WELCOME`

Sent by the Group Owner Server to a member server when one of its users
is added to the group. Delivers the MLS Welcome message for the added
user, enabling the receiving MLS client to initialise its state and
derive the current Group Key. A single `MLS_COMMIT` covering multiple
Add proposals will result in one `MLS_WELCOME` notification per added
user.

```json
{
  "notificationType": "MLS_WELCOME",
  "groupId": "<base64 MLS group ID>",
  "userId": "bob@othercloud.example.org",
  "content": "<base64 MLS Welcome wire format>"
}
```

#### 7.2.2. `MLS_PROPOSAL`

Sent by a member server to the Group Owner Server to propose a
membership change (Add or Remove) on behalf of one of its users. This
notification is NOT broadcast to other member servers; it is delivered
only to the Group Owner Server, which acts as sole committer.

```json
{
  "notificationType": "MLS_PROPOSAL",
  "groupId": "<base64 MLS group ID>",
  "content": "<base64 MLS Proposal wire format>"
}
```

#### 7.2.3. `MLS_COMMIT`

Sent by the Group Owner Server to all member servers to advance the
group epoch. The `sequenceNumber` is assigned by the Group Owner Server
and MUST be monotonically increasing. Member servers MUST process
commits in sequence-number order and MUST apply the new epoch secret
before sending any application data, per [RFC9420] §15.2.

```json
{
  "notificationType": "MLS_COMMIT",
  "groupId": "<base64 MLS group ID>",
  "sequenceNumber": 42,
  "content": "<base64 MLS Commit wire format>"
}
```

The `MLS_COMMIT` serves as the signal to all sending servers that group
composition has changed, enabling them to trigger re-encryption or
re-wrapping according to their policy. Any Commit covering a Remove
proposal MUST include an UpdatePath ([RFC9420] §12.4).

#### 7.2.4. `MLS_APPLICATION`

Used in two directions. Sending servers send this to the Group Owner
Server to deliver updated wrapped file keys after processing an epoch
transition. The Group Owner Server then broadcasts it to all current
member servers. The `content` is a `PrivateMessage` carrying application
data encrypted in the current epoch ([RFC9420] §15).

```json
{
  "notificationType": "MLS_APPLICATION",
  "groupId": "<base64 MLS group ID>",
  "content": "<base64 MLS PrivateMessage wire format>"
}
```

### 7.3. Leaf Key Updates

To maintain post-compromise security ([RFC9420] §16.6), member servers
SHOULD periodically send `MLS_PROPOSAL` (Update) to the Group Owner
Server to rotate their users' leaf keys. The Group Owner Server MUST
commit received Update proposals promptly. Members that do not update
SHOULD eventually be removed from the group per [RFC9420] §3.2.

---

## 8. Encryption Model

### 8.1. Group Key Derivation

After processing any MLS Welcome or Commit, the MLS client MUST apply
the new epoch secret before encrypting any application data, then
derives the current 32-byte Group Key:

```
group_key = MLS-Exporter("ocm-group-key", group_id_bytes, 32)
```

The MLS Exporter ([RFC9420] §8.5) produces application-specific key
material from the epoch secret without exposing the epoch secret itself.
The label `"ocm-group-key"` scopes the output to this application. The
`group_id_bytes` context further binds the output to this specific
group. The Group Key therefore changes with every epoch transition and
cannot be derived by any party that did not participate in that epoch.

Per [RFC9420] §8.5, the Group Key SHOULD be refreshed after each
processed Commit. Security-sensitive values derived from the epoch
secret MUST be deleted as soon as they are consumed, per [RFC9420] §9.2.

All MLS clients in the group independently derive the same Group Key for
a given epoch.

### 8.2. File Key Wrapping

When sharing an encrypted resource with a group, the sending MLS client
acts on behalf of a user who is a member of that group:

1. Generates a random per-file key (FK) of appropriate length for the
   chosen AEAD algorithm.
2. Encrypts the resource using an AEAD algorithm from the set supported
   by the MLS cipher suite negotiated for the group, as defined in
   [RFC9180]. Implementations supporting native client decryption of
   large files SHOULD use a chunked AEAD construction to enable
   streaming decryption.
3. Derives the current Group Key from the user's local MLS state.
4. Wraps FK using the same AEAD algorithm:
   ```
   wrapped_file_key = AEAD-Encrypt(
     key       = group_key,
     nonce     = random_nonce,
     plaintext = FK,
     aad       = group_id || resource_id_utf8
   )
   ```
5. Sends an `MLS_APPLICATION` notification to the Group Owner Server
   carrying the wrapped FK keyed by `(providerId, groupId)`, for
   broadcast to all current member servers.

### 8.3. Key Distribution via MLS Application Messages

Wrapped file keys are distributed to member servers via MLS Application
Messages, `PrivateMessage` objects carrying application data ([RFC9420]
§15). A sending server MUST process the `MLS_COMMIT` and derive the new
Group Key before sending an `MLS_APPLICATION` with updated wrapped keys,
per [RFC9420] §15.2.

The `PrivateMessage` application data is a JSON object carrying the
current wrapped FK for each `(providerId, groupId)` pair:

```json
{
  "keys": [
    {
      "providerId": "7c084226-d9a1-11e6-bf26-cec0c932ce01",
      "groupId": "research-group@cloud.example.org",
      "wrappedKey": "<base64 nonce || wrapped_file_key || AEAD tag>"
    }
  ]
}
```

The `PrivateMessage` is encrypted using the current epoch's keys, so
only current group members can decrypt it. A just-removed member cannot
decrypt the Application Message even if they receive the notification,
as they do not hold the new epoch's key material.

Member servers store the received wrapped FKs locally, always replacing
any previous wrapped FK for the same `(providerId, groupId)` pair with
the latest received. At access time, the member server uses its current
Group Key, derived from its current MLS state for the identified group,
to unwrap the FK.

### 8.4. Resource Access

To access a resource:

1. The MLS client identifies the relevant group from the `groupId` in
   the share notification and looks up the locally stored
   `wrapped_file_key` for the `(providerId, groupId)` pair.
2. The MLS client derives the current Group Key from its local MLS state
   for that group and unwraps FK.
3. The MLS client decrypts the resource using FK.

In web-client deployments, decryption happens server-side and the
plaintext is served to the user through whatever access protocol is in
use (WebDAV, SFTP, webapp, etc.). In native client deployments,
decryption happens on the user's device and the client interacts
directly with the sending server, which serves only ciphertext.

### 8.5. Resource Modification by Member Servers

A common operation is for a user on a member server to open a shared
encrypted resource, modify it, and save it back. The cryptographic flow
is as follows:

1. The member server fetches the encrypted resource from the sending
   server via whatever access protocol is in use.
2. The member server identifies the relevant group from the `groupId` in
   the share notification, looks up the locally stored
   `wrapped_file_key` for the `(providerId, groupId)` pair, derives the
   current Group Key from its local MLS state for that group, and
   unwraps FK.
3. The member server decrypts the resource using FK and presents the
   plaintext to the user.
4. The user modifies the resource.
5. The member server re-encrypts the modified resource using the same FK
   but a fresh random nonce. The nonce MUST NOT be reused with the same
   key, as required by AEAD security.
6. The member server uploads the re-encrypted resource to the sending
   server.

The FK is reused across modifications of the same resource because it is
bound to the `group_id` and `resource_id` in the AEAD associated data,
making it specific to that resource. No new `MLS_APPLICATION` message is
needed, as the wrapped FK in all member servers' local stores remains
valid for the updated ciphertext.

The `resource_id` used in the AEAD associated data MUST be stable across
edits of the same resource. It identifies the resource, not a particular
version of it. In OCM terms this corresponds to the `providerId` of the
share. The `groupId` in the AEAD associated data further scopes the
wrapped FK to a specific group, so the same resource shared with two
different groups produces two distinct wrapped FKs that cannot be
confused.

FK rotation for a resource is only necessary on member removal in
re-encryption mode (Section 8.6).

### 8.6. Sharing a Resource with Multiple Groups

A sending server MAY share the same encrypted resource with more than
one group. The file is encrypted once with a single FK. Each group
receives its own wrapped FK, produced using that group's Group Key and
`group_id`:

```
wrapped_file_key_group1 = AEAD-Encrypt(group_key_1, nonce_1, FK,
                                  group_id_1 || resource_id)
wrapped_file_key_group2 = AEAD-Encrypt(group_key_2, nonce_2, FK,
                                  group_id_2 || resource_id)
```

A separate Share Creation Notification is sent to each member of the
group. A separate `MLS_APPLICATION` is sent to each Group Owner Server
carrying the respective wrapped FK. Members of each group can only
unwrap the FK using their own group's Group Key and cannot access the
other group's wrapped FK or Group Key.

The `resource_id` used in the AEAD associated data MUST be a stable
identifier for the underlying file, consistent across all groups it is
shared with. This ensures that the FK unwrapped by members of any group
correctly decrypts the same ciphertext. The `providerId` values in the
separate share notifications MAY differ, but the `resource_id` in the
AEAD associated data MUST be the same. The sending server is responsible
for maintaining this stable `resource_id`.

The sending server MUST maintain a mapping from each resource to all
groups it has been shared with. This mapping is required to correctly
handle member removal in re-encryption mode, as described in the
following section.

### 8.7. FK Rotation (RECOMMENDED)

A sending server SHOULD rotate the FK for a resource when a member is
removed from any group that has access to it. FK rotation may also be
triggered by other factors, such as periodic key rotation policy,
regulatory requirements, or a suspected compromise of key material.
Applications SHOULD define a policy for the frequency of FK rotation
independent of membership changes.

When rotating the FK for a resource, the sending server:

1. Generates a new FK for the resource.
2. Re-encrypts the resource with the new FK.
3. For every group that has access to the resource, wraps the new FK
   using that group's current Group Key:
   ```
   new_wrapped_file_key_groupN = AEAD-Encrypt(group_key_N, nonce_N, new_FK,
                                         group_id_N || resource_id)
   ```
4. Sends an `MLS_APPLICATION` notification to every group's Group Owner
   Server carrying the respective new wrapped FK for broadcast to that
   group's member servers.

Distributing the new wrapped FK to all groups that share the resource is
necessary because all groups share the same ciphertext. If only one
group received the new wrapped FK, members of other groups would hold a
wrapped FK that no longer decrypts the current ciphertext.

A member removed from one group but still a member of another group that
shares the same resource retains the ability to decrypt that resource
through the second group. This is correct and intended behaviour: access
is determined by current group membership, and the user remains a member
of the second group. The default safe rule is to rotate the FK and
redistribute to all groups on any removal event. A sending server MAY
instead compare the unique set of users with access before and after an
epoch change, and skip FK rotation if that set is unchanged, for example
because the removed user remains a member of every other group that has
access to the same resource. Whether this optimisation is worth the
added complexity depends on the nature of the resource and the frequency
of membership changes.

Member addition does not require FK rotation. The new member receives
the current Group Key via their Welcome and can unwrap the existing FK
directly.

### 8.8. Member Removal: Key-reuse Mode (OPTIONAL)

Where re-encryption is impractical, for example due to frequent changes
of very large files, and where all participating servers belong to a
formal federation with explicit governance and mutual trust, a sending
server MAY instead:

1. Process the Commit and derive the new Group Key for the affected
   group.
2. Re-wrap the existing FK under the new Group Key for the affected
   group.
3. Send an `MLS_APPLICATION` notification to that group's Group Owner
   Server carrying the re-wrapped FK for broadcast to all remaining
   member servers.

In key-reuse mode, when a resource is shared with multiple groups, it is
sufficient to re-wrap the FK only for the group from which the member
was removed. The wrapped FKs for other groups are unchanged and remain
valid for their respective members.

In this mode, access-follows-membership relies on trusting member
servers to discard superseded group keys after processing a Remove
Commit. A removed member who is also a member of another group that has
access to the same resource will still be able to decrypt via that
group's wrapped FK, which is the expected behaviour — they remain a
member of that group. This assumption is appropriate within a formal
federation but SHOULD NOT be made in open or ad-hoc sharing contexts.

The sending server's choice of mode is its own policy decision and is
not signalled in the protocol.

### 8.9. Member Removal: OCM Notifications

When a member has been removed from a group, a well-behaved sending
server SHOULD reconcile the OCM state of the share, and send a
SHARE_UNSHARED notification to the /notification endpoint of the
receiving server.

---

## 9. Share Creation

### 9.1. Share Creation Notification

The sending server sends individual OCM Share Creation Notifications
directly to each current member server, using the OCM Address from each
leaf node's credential in the ratchet tree to identify the recipients.
This is standard OCM server-to-server communication, with `shareWith`
set to the receiving user's OCM Address and `shareType` set to
`"federation"` to indicate the share originates from a federated group
context.

A `groupId` field carrying the OCM Address of the group MUST be included
in all federation share notifications. This allows the receiving server
to distinguish between shares of the same resource arriving via
different groups — a user may be a member of two groups that both have
access to the same resource from the same sending server. It also allows
the receiving server to correctly key its local wrapped FK store by
`(providerId, groupId)` rather than `providerId` alone, ensuring that FK
updates delivered via `MLS_APPLICATION` are applied to the correct
entry.

Each notification MAY include the optional `encryption` field:

```json
{
  "shareWith": "bob@othercloud.example.org",
  "shareType": "federation",
  "groupId": "research-group@cloud.example.org",
  "resourceType": "file",
  "sender": "alice@cloud.example.org",
  "owner": "alice@cloud.example.org",
  "providerId": "7c084226-d9a1-11e6-bf26-cec0c932ce01",
  "name": "experiment-data.tar",
  "encryption": {
    "scheme": "ocm-mls-1"
  }
}
```

The `encryption` field is OPTIONAL. If absent, the resource is
unencrypted and the share follows the standard OCM flow without
modification. If present, `scheme` identifies the encryption scheme.
This proposal defines `"ocm-mls-1"`. The field signals that the FK is
distributed via the `MLS_APPLICATION` mechanism keyed by
`(providerId, groupId)`. No epoch information is carried in the share
notification. Member servers always hold the current wrapped FK for each
`(providerId, groupId)` pair and use their current Group Key to unwrap
it at access time.

The Group Owner Server is not involved in the delivery of OCM share
notifications. All other OCM notifications relating to a share, such as
share updates and share deletions, are likewise sent directly from the
sending server to each member server and MUST include the `groupId`
field.

---

## 10. Trust and Authentication

The Authentication Service role ([RFC9420] §3) is fulfilled by each
user's home OCM server. A KeyPackage is considered authenticated if it
is retrievable from the canonical `<endPoint>/mls-key-packages` endpoint
of the server named in the user's OCM Address, and the credential
signature verifies against the user's published public key.

Users who require protection of their key material from their own server
should choose a native client implementation where cryptographic
operations occur on the user's device.

---

## 11. Security Considerations

**Trust model.** In web-client deployments, the EFSS holds the Group Key
and can decrypt any resource shared with the group on behalf of its
users. This is consistent with the standard EFSS trust model, where
users trust their server with their data, and with OCM's existing
approach of abstracting security to the server level. Native client
deployments provide stronger isolation, as the server does not hold key
material. Implementations SHOULD move toward native client deployments
over time.

**FK rotation vs key-reuse.** FK rotation provides cryptographic access
revocation on member removal, independent of trust assumptions, and
SHOULD also be performed periodically or when key compromise is
suspected. Key-reuse mode relies on trusting member servers to discard
superseded group keys after processing a Remove Commit. Key-reuse mode
SHOULD only be used within formal federations with governance agreements
that enforce this behaviour.

**Key distribution via Application Messages.** Wrapped FKs are
distributed in MLS `PrivateMessage` objects encrypted in the current
epoch. A removed member cannot decrypt these messages as they do not
hold the new epoch's key material. Member servers always replace their
locally stored wrapped FK with the latest received, so the current Group
Key is always sufficient for unwrapping.

**Commit ordering.** The Group Owner Server is the sole committer,
eliminating the possibility of conflicting Commits for the same epoch. A
compromised or unavailable Group Owner Server can stall epoch
transitions but cannot decrypt resource content from the key store
alone.

**Application message ordering.** Per [RFC9420] §15.2, sending servers
MUST apply a new epoch secret before encrypting any application data.
`MLS_APPLICATION` messages carrying re-wrapped keys MUST be sent only
after the sending server has processed the corresponding `MLS_COMMIT`.

**Post-compromise security.** Member servers SHOULD periodically rotate
their users' leaf keys via Update proposals to maintain post-compromise
security ([RFC9420] §16.6). Members that do not update SHOULD eventually
be removed from the group.

**Key material deletion.** Security-sensitive values MUST be deleted as
soon as they are consumed, per [RFC9420] §9.2. In particular, the
exporter_secret used to derive the Group Key must not be retained after
the Group Key has been derived.

**KeyPackage reuse.** As per [RFC9420] §16.8, KeyPackages MUST be
one-time use. Servers MUST remove a KeyPackage that has been consumed.

**User enumeration.** A server MUST only reply to HTTPS GET requests
signed using http-sig [RFC9421] and SHOULD implement rate limiting and
other access control methods on the /mls-key-packages endpoint to avoid
user enumeration.

---

## 12. IANA Considerations

The MLS Exporter label `"ocm-group-key"` used in Section 8.1 SHOULD be
registered in the MLS Exporter Labels registry defined in [RFC9420]
§17.8 to avoid collisions with other applications using the MLS
Exporter.

---

## 13. Open Issues

- **Streaming decryption.** A chunked AEAD construction enabling
  streaming decryption of large files should be specified for native
  client implementations. The specific construction and its interaction
  with the FK wrapping model needs to be defined.

- **Application Message batching.** The frequency and batching of
  `MLS_APPLICATION` messages carrying wrapped FKs needs to be defined,
  particularly when many shares exist and epoch transitions are
  frequent.

- **Group Owner Server failover.** A mechanism for designating a
  successor Group Owner Server, and for publishing a current GroupInfo
  object to enable External Joins ([RFC9420] §3.3) for member servers
  that have lost state, needs to be specified.

---

## 14. References

- draft-ietf-ocm-open-cloud-mesh-04, Lo Presti et al., March 2026
- [RFC9420] Barnes et al., "The Messaging Layer Security (MLS)
  Protocol", July 2023
- [RFC9421] Backman et al., "HTTP Message Signatures"
- [RFC9180] Bhargavan et al., "Hybrid Public Key Encryption"
- [RFC7517] Jones, "JSON Web Key (JWK)"
- [RFC4918] Dusseault, "HTTP Extensions for Web Distributed Authoring
  and Versioning (WebDAV)"
