# OCM-API Diagrams

## Purpose

This folder holds informative Mermaid diagrams for the OCM API spec in
`../IETF-OCM.md`. They illustrate discovery, share creation, access
paths, signing, and invites. They add no new normative rules; the
Internet-Draft is always authoritative.

## Adding a diagram

If you want to add or update a diagram, keep it in sync with the
normative text and follow the style rules at the end of this file. Each
diagram file is a standalone Markdown page with a `# Title`, a short
prose intro, the Mermaid block, and a few bullets citing the
IETF-OCM.md sections it illustrates.

## Normative source

Authoritative text: [IETF-OCM.md](../IETF-OCM.md).

Key anchors:

- [Appendix E: Navigation
  Index](../IETF-OCM.md#appendix-e-navigation-index)
- [Signing Direction Index](../IETF-OCM.md#signing-direction-index)
- [OCM API Discovery](../IETF-OCM.md#ocm-api-discovery)
- [Invite Flow](../IETF-OCM.md#invite-flow)
- [General Flow](../IETF-OCM.md#general-flow)

## Four planes

OCM separates four planes (see
[01-planes-overview.md](01-planes-overview.md)):

1. **Discovery** - `capabilities[]`, `criteria[]`, and dual-role
   `exchange-token` / `tokenEndPoint` in `/.well-known/ocm`.
2. **Share** - per-share `requirements[]` and `protocol.*` shape in the
   Share Creation Notification.
3. **Peer interaction** - the Sending Server reads the receiver's
   discovery document during preflight.
4. **Enforcement** - the Receiving Server applies criteria at admission
   and requirements at resource access.

Only `must-exchange-token` binds from receiver `criteria[]` to sender
`requirements[]`; other criteria gate admission directly.

## Reading order

1. [01-planes-overview.md](01-planes-overview.md) - the four planes and
   the dual-role exchange-token capability.
2. [02-discovery-receiver-publish.md](02-discovery-receiver-publish.md)
   - how a receiver builds and publishes its discovery document.
3. [03-discovery-sender-consume.md](03-discovery-sender-consume.md) -
   sender preflight: criteria binding and the voluntary strict mode.
4. [04-share-lifecycle.md](04-share-lifecycle.md) - end-to-end flow from
   publish through access and unshare.
5. [05-access-webdav-paths.md](05-access-webdav-paths.md) - WebDAV token
   exchange, MFA, and bearer vs legacy sharedSecret paths.
6. [06-access-webapp-code-flow.md](06-access-webapp-code-flow.md) -
   WebApp Code Flow presentation via the browser and tokenEndPoint.
7. [07-signing-directions.md](07-signing-directions.md) - who signs and
   who verifies each OCM API request; read this before implementing any
   signed endpoint.
8. [08-invite-flow.md](08-invite-flow.md) - establishing contact: invite
   token, acceptance, and allowlisting before shares.

## Color legend

Flowchart nodes use a fixed, CVD-safe palette:

- **Blue (disc)** - discovery documents, reads, and link-out references.
- **Rose (share)** - share artifacts (`POST /shares`, requirements).
- **Amber (gate)** - decision gates and enforcement checkpoints.
- **Green (ok)** - success paths and completed actions.
- **Red (fail)** - hard failures and discard outcomes.
- **Light red (term)** - terminal states (declined, revoked, strict
  fail).
- **Grey (neutral)** - omit paths, legacy fallback, polling.
- **Cyan (sign)** - HTTP Message Signature application.
- **Indigo (verify)** - HTTP Message Signature verification.

Sequence diagrams use transparent `box Label` grouping (no colored
fills) so they stay readable in both light and dark themes; a `Note`
labels any highlighted region. Semantic color lives in the flowcharts.

## Style rules for new diagrams

Every flowchart MUST paste this exact `classDef` block verbatim:

```mermaid
classDef disc fill:#e8f0fe,stroke:#1a73e8,color:#174ea6
classDef gate fill:#fef7e0,stroke:#b06000,color:#7a5900
classDef ok fill:#e6f4ea,stroke:#188038,color:#0d652d
classDef fail fill:#fce8e6,stroke:#d93025,color:#a50e0e
classDef term fill:#f7d4d0,stroke:#d93025,color:#a50e0e
classDef neutral fill:#f1f3f4,stroke:#5f6368,color:#3c4043
classDef share fill:#fce4ec,stroke:#ad1457,color:#9c0066
classDef sign fill:#e0f7fa,stroke:#00838f,color:#006064
classDef verify fill:#e8eaf6,stroke:#3949ab,color:#1a237e
```

Additional rules:

- Start with `# Title`, then a prose intro (<=72 columns), then the
  Mermaid body, then post-diagram bullets citing IETF-OCM.md sections.
- Use `<br/>` in labels, never `\n`.
- Keep labels to <=36 characters per line and at most 3 lines.
- Give every flowchart node exactly one class from the block above.
- For sequence diagrams, group with `box Label` (transparent, no color)
  and add `autonumber`. Do not use `box rgb(...)`/`box #hex` and do not
  wrap messages in `rect rgb(...)`/`rect rgba(...)`: sequence `box` and
  `rect` cannot set text color, so a light fill inherits the renderer's
  dark-theme light text and becomes unreadable in dark mode. The
  `%%{init}%%` themeVariables override is ignored by some renderers (for
  example the VS Code preview), so it is not a reliable fix. Use a
  `Note` to label a region instead of a colored rect. Flowcharts do not
  need this; their `classDef` sets text `color` directly.
