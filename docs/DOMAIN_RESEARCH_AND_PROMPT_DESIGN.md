# Domain Research and Prompt Design

## Buyer calls

Buyers ask about price, tenure, condition, location, transport, schools, EPC, service charges, chain, availability and viewing times. Core qualification is motivation, locations, property type/bedrooms, budget, deposit/mortgage agreement in principle, timeline, chain and decision makers. Serious signals include precise criteria, approved finance, fixed timing, repeat questions about one property, viewing availability and offer language; casual signals include vague geography/budget, no timing and unwillingness to progress. Common objections are price, finance, condition, location and risk.

## Vendor calls

Vendors ask about valuation, achievable price, fees, marketing, time to sell, viewings, prior-agent failure and contract terms. Anxiety concentrates on underpricing, overpromising, time on market, communication and commission. Motivation, target date, access for valuation/photography, documents, pricing realism and willingness to discuss instruction signal readiness. Fee objection should be diagnosed and related to service/value, never dismissed.

## Progression

Offer a viewing when criteria, affordability and intent align. Discuss an offer after property interest and buying position are clear. Propose valuation after vendor motivation/property context is known. Seek instruction only after valuation evidence, service, fees and obligations are understood. Each next move acknowledges the latest customer point, uses known facts, asks one unresolved question or proposes one concrete commitment.

## Prompt structure

Conversation Agent input is the latest final utterance, speaker, recent exchanges and structured state; it returns typed stage, intent, entities, signals, objections, commitments and retrieval flags. Fast Coach receives only current state, event, recent exchanges and compact playbook rules. Deep Coach additionally receives relevant RAG and validated evidence. System rules prohibit generic advice, unsupported market/property claims, protected-trait use and category mixing. It must name what was just said and propose one usable action. Full transcripts are not repeatedly sent. Unverified evidence requires abstention. The deterministic trigger/cooldown layer prevents per-token calls and card spam.
