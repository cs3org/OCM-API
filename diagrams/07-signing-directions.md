# Signing Directions

Informative visual companion to the Signing Direction Index in the
IETF draft. Diagrams add no new normative rules; see IETF-OCM.md.

```mermaid
flowchart LR
    subgraph R1["POST /shares"]
        S1["Sending Server<br/>signs"]
        V1["Receiving Server<br/>verifies"]
    end

    subgraph R2["POST tokenEndPoint"]
        S2["Receiving Server<br/>signs (token client)"]
        V2["Sending Server<br/>verifies"]
    end

    subgraph R3["POST /invite-accepted"]
        S3["Invite Receiver Server<br/>signs"]
        V3["Invite Sender Server<br/>verifies"]
    end

    subgraph R4["POST /notifications"]
        S4R["Receiving Server signs<br/>SHARE_ACCEPTED / DECLINED"]
        V4R["Sending Server verifies"]
        S4S["Sending Server SHOULD sign<br/>sender-initiated updates"]
        V4S["Receiving Server verifies"]
    end

    subgraph R5["POST /request-share"]
        S5["Requesting Server<br/>signs"]
        V5["Requested Server<br/>verifies"]
    end

    S1 --> V1
    S2 --> V2
    S3 --> V3
    S4R --> V4R
    S4S --> V4S
    S5 --> V5

    JWKS["Verify prep: GET<br/>/.well-known/jwks.json<br/>(when http-sig)"]

    classDef disc fill:#e8f0fe,stroke:#1a73e8,color:#174ea6
    classDef gate fill:#fef7e0,stroke:#b06000,color:#7a5900
    classDef ok fill:#e6f4ea,stroke:#188038,color:#0d652d
    classDef fail fill:#fce8e6,stroke:#d93025,color:#a50e0e
    classDef term fill:#f7d4d0,stroke:#d93025,color:#a50e0e
    classDef neutral fill:#f1f3f4,stroke:#5f6368,color:#3c4043
    classDef share fill:#fce4ec,stroke:#ad1457,color:#9c0066
    classDef sign fill:#e0f7fa,stroke:#00838f,color:#006064
    classDef verify fill:#e8eaf6,stroke:#3949ab,color:#1a237e

    class JWKS disc
    class S1,S2,S3,S4R,S4S,S5 sign
    class V1,V2,V3,V4R,V4S,V5 verify
```

- Companion to [Signing Direction
  Index](../IETF-OCM.md#signing-direction-index) and [HTTP Message
  Signatures](../IETF-OCM.md#http-message-signatures).
- Signing applies when the peer advertises `http-sig`;
  `must-use-http-sig` makes verification mandatory on inbound
  requests.
- `/notifications` carries traffic in both directions; signing follows
  the notification actor, not the endpoint name.
- The Code Flow token request is signed by the Receiving Server (token
  client) and verified by the Sending Server.
- Verifiers SHOULD fetch JWKS from `/.well-known/jwks.json` when
  `http-sig` is advertised.
