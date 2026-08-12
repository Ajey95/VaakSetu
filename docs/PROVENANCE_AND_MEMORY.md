# Provenance and Follow-Up Memory

External claims travel through information need, tool call, source, evidence evaluation and recommendation IDs. Source tier, URL, retrieval/publication time, freshness, support status and confidence remain attached. Unsupported/conflicting claims show unverified/conflicting states and cannot become facts.

Current-call state is in memory. PostgreSQL/pgvector stores operational and episodic/domain retrieval. Temporal graph facts keep valid-from, valid-to, observed-at, source-event and current history. The first call creates durable memory asynchronously. Follow-up briefs use the latest summary/commitments and may later enrich from vector/graph context; neither brief nor graph can block dialing or fast coaching.
