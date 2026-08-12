# Prototype Architecture

```text
React/Twilio Device <-> Twilio <-> real phone
                         |
                  both_tracks WSS
                         v
FastAPI media -> per-speaker buffer/STT -> transcript/state -> Fast Coach -> UI WS
                                                | async
                              RAG/tools -> evidence -> Deep Coach
                                                | async
                             PostgreSQL/pgvector + Neo4j + evals
```

`inbound_track` is customer; `outbound_track` is browser agent. Media sequencing, STT, AI, databases, graph, tools, UI delivery and evals have no telephony control path. Events carry event/trace/call/session IDs. Reconnecting UIs receive a full snapshot before incremental events.
