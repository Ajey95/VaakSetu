import asyncio,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"apps"/"api"))
from app.services.call_service import CallService
from app.models.contracts import Speaker
async def main():
 s=CallService(); c=(await s.create_synthetic_call("07700 900123","demo-customer"))["call"]["id"]
 for speaker,text in [(Speaker.AGENT,"What budget are you working to?"),(Speaker.CUSTOMER,"My budget is £450,000, mortgage approved, moving in six weeks, but the price feels too high."),(Speaker.CUSTOMER,"Prices in Manchester fell 10%")]: await s.process_utterance(c,speaker,text,True)
 snap=await s.end_call(c); print(snap.model_dump_json(indent=2))
asyncio.run(main())
