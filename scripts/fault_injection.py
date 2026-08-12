import asyncio, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"apps"/"api"))
from app.services.call_service import CallService
async def main():
 s=CallService(); c=(await s.create_synthetic_call("07700 900123",None))["call"]["id"]
 faults="stt_disconnect stt_reconnect buffer_replay duplicate_replay llm_timeout llm_malformed external_timeout external_rate_limit evidence_conflict evidence_unverified database_failure graph_failure frontend_disconnect".split()
 results=[await s.run_fault_scenario(c,f) for f in faults]; exercised=sum(bool(item['exercised'] and item['observable']) for item in results); print(f"{exercised}/{len(faults)} behavioral faults isolated; call={results[-1]['call_status']}")
asyncio.run(main())
