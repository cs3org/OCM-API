# The Four Orthogonal Planes

Informative: discovery, share, peer-interaction, enforcement planes.
Diagrams add no new normative rules; see IETF-OCM.md.

```mermaid
flowchart TD
    subgraph DISC["Discovery plane"]
        CAP["capabilities[]<br/>what server CAN do"]
        CRI["criteria[]<br/>inbound admission"]
        ET["exchange-token +<br/>tokenEndPoint<br/>(dual-role)"]
    end

    subgraph SHARE["Share plane"]
        REQ["requirements[]<br/>must-exchange-token"]
        SHAPE["protocol.* fields<br/>uri, sharedSecret, ..."]
    end

    DOC["Discovery document<br/>/.well-known/ocm"]
    PEER["Sender reads<br/>peer discovery"]
    BIND["must-exchange-token only:<br/>criteria -> requirements"]
    OTH["other criteria:<br/>http-sig, invite, lists"]
    ENF["Receiver enforces<br/>before granting access"]

    DOC --> CAP
    DOC --> CRI
    DOC --> ET
    CAP -. "advertised once<br/>read by peer" .-> PEER
    CRI -. "advertised once<br/>read by peer" .-> PEER
    ET -. "Sending: hosts<br/>tokenEndPoint" .-> PEER
    ET -. "Receiving: honors<br/>strict inbound shares" .-> PEER

    PEER --> BIND
    BIND --> REQ
    PEER --> OTH
    CRI --> OTH
    OTH --> ENF
    REQ --> ENF
    SHAPE --> ENF

    classDef disc fill:#e8f0fe,stroke:#1a73e8,color:#174ea6
    classDef gate fill:#fef7e0,stroke:#b06000,color:#7a5900
    classDef ok fill:#e6f4ea,stroke:#188038,color:#0d652d
    classDef fail fill:#fce8e6,stroke:#d93025,color:#a50e0e
    classDef term fill:#f7d4d0,stroke:#d93025,color:#a50e0e
    classDef neutral fill:#f1f3f4,stroke:#5f6368,color:#3c4043
    classDef share fill:#fce4ec,stroke:#ad1457,color:#9c0066
    classDef sign fill:#e0f7fa,stroke:#00838f,color:#006064
    classDef verify fill:#e8eaf6,stroke:#3949ab,color:#1a237e

    class DOC,CAP,CRI,ET disc
    class REQ,SHAPE share
    class PEER disc
    class BIND share
    class OTH gate
    class ENF gate
```

- Capabilities and criteria live in the receiver's discovery document;
  requirements and protocol shape live in each Share Creation
  Notification. See
  [OCM API Discovery](../IETF-OCM.md#ocm-api-discovery) and
  [Share Creation
  Notification](../IETF-OCM.md#share-creation-notification).
- `exchange-token` and `tokenEndPoint` describe a dual-role capability:
  the Sending Server hosts `tokenEndPoint`; the Receiving Server honors
  inbound strict shares.
- Only `must-exchange-token` binds from receiver `criteria[]` to sender
  `requirements[]`; other criteria gate admission directly.
- Enforcement of requirements and protocol fields happens at resource
  access time on the Receiving Server.
