# Invite Flow

Informative: establishing contact before share creation.
Diagrams add no new normative rules; see IETF-OCM.md.

```mermaid
sequenceDiagram
    autonumber
    actor ISU as Invite Sender
    actor IRU as Invite Receiver

    box Invite Sender OCM Server
        participant ISS as Invite Sender Server
    end

    box Invite Receiver OCM Server
        participant IRS as Invite Receiver Server
    end

    ISS->>ISS: Generate unique Invite Token
    ISS->>ISU: OOB Invite Message<br/>(token + sender FQDN)
    ISU->>IRU: Deliver Invite Message<br/>(out-of-band)

    opt WAYF Page on sender server (link-format invite)
        IRU->>ISS: Open invite link<br/>sender/wayf?token=...
        ISS->>IRU: WAYF page: pick receiver<br/>OCM Server (list/free-text)
        IRU->>ISS: Submit receiver FQDN
        ISS->>IRS: GET /.well-known/ocm<br/>(discover inviteAcceptDialog)
        IRS-->>ISS: Discovery document
        ISS->>IRU: Redirect to receiver<br/>inviteAcceptDialog<br/>?token=...&providerDomain=sender
    end

    IRU->>IRS: Invite Acceptance Gesture
    IRS->>ISS: GET /.well-known/ocm<br/>(discovery)
    ISS-->>IRS: Discovery document

    Note over IRS,ISS: POST /invite-accepted body:<br/>recipientProvider, token,<br/>userID, email, name
    IRS->>ISS: POST /invite-accepted<br/>(receiver signs if http-sig)
    ISS->>ISS: Verify signature<br/>(when http-sig)

    ISS-->>IRS: 200 + sender identity<br/>(userID, email, name)
    IRS->>IRS: MAY allowlist sender server
    ISS->>ISS: MAY allowlist receiver server
    IRS->>IRU: Contact established
    ISU->>ISU: Contact established
```

- Steps follow [Invite Flow](../IETF-OCM.md#invite-flow) and
  [Establishing Contact](../IETF-OCM.md#establishing-contact).
- When the invite uses the link format, the Invite Sender's WAYF page
  discovers the Invite Receiver OCM Server's `inviteAcceptDialog` via OCM
  API Discovery (`GET /.well-known/ocm` on the receiver FQDN) and
  redirects the Invite Receiver there with `token` and `providerDomain`
  query parameters. The `invite-wayf` capability and `inviteAcceptDialog`
  field are advertised in discovery; see [Invite
  format](../IETF-OCM.md#invite-format) and [OCM API
  Discovery](../IETF-OCM.md#ocm-api-discovery). The WAYF server list MAY
  be populated from a Directory Service.
- The Invite Acceptance Request is a signed POST to `/invite-accepted`
  on the Invite Sender OCM Server; see [Invite Acceptance Request
  Details](../IETF-OCM.md#invite-acceptance-request-details).
- Both servers MAY allowlist each other and add the remote party as a
  contact; see [Addition into address
  books](../IETF-OCM.md#addition-into-address-books).
- Invites are orthogonal to share lifecycle; see
  [04-share-lifecycle.md](04-share-lifecycle.md).
