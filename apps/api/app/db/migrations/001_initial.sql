CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS customers (id text PRIMARY KEY, display_name text, phone_hash text);
CREATE TABLE IF NOT EXISTS calls (id text PRIMARY KEY, twilio_call_sid text UNIQUE, customer_id text REFERENCES customers(id), direction text NOT NULL, call_type text NOT NULL, started_at timestamptz, connected_at timestamptz, ended_at timestamptz, status text NOT NULL);
CREATE TABLE IF NOT EXISTS call_participants (id text PRIMARY KEY, call_id text NOT NULL REFERENCES calls(id), role text NOT NULL, customer_id text);
CREATE TABLE IF NOT EXISTS utterances (id text PRIMARY KEY, call_id text NOT NULL REFERENCES calls(id), speaker text NOT NULL, started_at timestamptz, ended_at timestamptz, text text NOT NULL, confidence double precision, sequence integer NOT NULL, source_track text NOT NULL, is_final boolean NOT NULL);
CREATE TABLE IF NOT EXISTS conversation_events (id text PRIMARY KEY, call_id text NOT NULL, kind text NOT NULL, payload jsonb NOT NULL, created_at timestamptz NOT NULL);
CREATE TABLE IF NOT EXISTS call_state_snapshots (id text PRIMARY KEY, call_id text NOT NULL, payload jsonb NOT NULL, created_at timestamptz NOT NULL);
CREATE TABLE IF NOT EXISTS facts (id text PRIMARY KEY, call_id text NOT NULL, kind text NOT NULL, value jsonb NOT NULL, source_event_id text);
CREATE TABLE IF NOT EXISTS signals (id text PRIMARY KEY, call_id text NOT NULL, kind text NOT NULL, payload jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS objections (id text PRIMARY KEY, call_id text NOT NULL, kind text NOT NULL, payload jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS commitments (id text PRIMARY KEY, call_id text NOT NULL, kind text NOT NULL, payload jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS recommendations (id text PRIMARY KEY, call_id text NOT NULL, event_id text, type text NOT NULL, next_move text NOT NULL, reason text NOT NULL, confidence text NOT NULL, created_at timestamptz NOT NULL, stale_at timestamptz, evidence_ids jsonb NOT NULL DEFAULT '[]');
CREATE TABLE IF NOT EXISTS recommendation_feedback (id text PRIMARY KEY, recommendation_id text NOT NULL, useful boolean NOT NULL, reason text);
CREATE TABLE IF NOT EXISTS external_claims (id text PRIMARY KEY, call_id text NOT NULL, claim text NOT NULL, status text NOT NULL);
CREATE TABLE IF NOT EXISTS tool_calls (id text PRIMARY KEY, call_id text NOT NULL, tool text NOT NULL, metadata jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS sources (id text PRIMARY KEY, provider text NOT NULL, title text NOT NULL, url text, source_tier integer NOT NULL, retrieved_at timestamptz NOT NULL, published_at timestamptz, content_hash text);
CREATE TABLE IF NOT EXISTS evidence (id text PRIMARY KEY, claim text NOT NULL, source_id text, support_status text NOT NULL, confidence double precision NOT NULL, freshness text NOT NULL, safe_to_surface_as_fact boolean NOT NULL);
CREATE TABLE IF NOT EXISTS call_summaries (id text PRIMARY KEY, call_id text UNIQUE NOT NULL, customer_id text, content jsonb NOT NULL, created_at timestamptz NOT NULL);
CREATE TABLE IF NOT EXISTS knowledge_documents (id text PRIMARY KEY, title text NOT NULL, metadata jsonb NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS knowledge_chunks (id text PRIMARY KEY, document_id text NOT NULL, content text NOT NULL, embedding vector(1536), metadata jsonb NOT NULL DEFAULT '{}');
CREATE INDEX IF NOT EXISTS knowledge_chunks_embedding_idx ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
CREATE TABLE IF NOT EXISTS eval_examples (id text PRIMARY KEY, payload jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS eval_runs (id text PRIMARY KEY, call_id text, payload jsonb NOT NULL, score double precision);
CREATE TABLE IF NOT EXISTS eval_scores (id text PRIMARY KEY, run_id text NOT NULL, dimension text NOT NULL, score double precision NOT NULL);
CREATE TABLE IF NOT EXISTS system_incidents (id text PRIMARY KEY, call_id text, component text NOT NULL, severity text NOT NULL, payload jsonb NOT NULL);

