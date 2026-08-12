from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.models.contracts import Speaker, normalize_phone_number


class IdentityRequest(BaseModel): identity: str = Field(min_length=1, max_length=121)
class DemoCallRequest(BaseModel): phone_number: str; customer_id: str | None = None
class UtteranceRequest(BaseModel): speaker: Speaker; text: str = Field(min_length=1); is_final: bool = True
class FeedbackRequest(BaseModel): useful: bool; reason: str | None = None


router = APIRouter()


@router.get("/health")
async def health(request: Request):
    return {"status": "ok", "mode": request.app.state.settings.app_mode.value}


@router.get("/health/providers")
async def providers(request: Request):
    return {key: value.model_dump(mode="json") for key, value in request.app.state.settings.provider_readiness().items()}


@router.post("/twilio/token")
async def twilio_token(body: IdentityRequest, request: Request):
    return request.app.state.twilio.access_token(body.identity)


@router.post("/twilio/voice")
async def twilio_voice(request: Request):
    form = await request.form()
    if not request.app.state.twilio.validate_webhook(request.url.path, dict(form),
                                                     request.headers.get("X-Twilio-Signature")):
        raise HTTPException(403, "Invalid Twilio signature")
    destination = form.get("To") or form.get("to")
    call_id = form.get("CallSid") or f"call_{__import__('uuid').uuid4().hex[:12]}"
    if not destination:
        raise HTTPException(422, "Missing To")
    await request.app.state.calls.register_real_call(str(call_id), str(destination))
    return Response(request.app.state.twilio.outbound_twiml(str(destination), str(call_id)), media_type="application/xml")


@router.post("/twilio/status", status_code=204)
async def twilio_status(request: Request):
    form = await request.form()
    if not request.app.state.twilio.validate_webhook(request.url.path, dict(form),
                                                     request.headers.get("X-Twilio-Signature")):
        raise HTTPException(403, "Invalid Twilio signature")
    call_id = form.get("ParentCallSid") or form.get("CallSid")
    provider_status = form.get("CallStatus")
    if call_id and provider_status:
        await request.app.state.calls.update_real_call_status(str(call_id), str(provider_status))
        if str(provider_status) == "completed":
            await request.app.state.calls.end_call(str(call_id))
    return Response(status_code=204)


@router.post("/twilio/stream-status", status_code=204)
async def stream_status(): return Response(status_code=204)


@router.post("/demo/calls", status_code=status.HTTP_201_CREATED)
async def create_demo_call(body: DemoCallRequest, request: Request):
    try: normalize_phone_number(body.phone_number)
    except ValueError as exc: raise HTTPException(422, str(exc)) from exc
    return await request.app.state.calls.create_synthetic_call(body.phone_number, body.customer_id)


@router.post("/demo/calls/{call_id}/utterances", status_code=201)
async def utterance(call_id: str, body: UtteranceRequest, request: Request):
    try: return await request.app.state.calls.process_utterance(call_id, body.speaker, body.text, body.is_final)
    except KeyError as exc: raise HTTPException(404, "Call not found") from exc


@router.post("/calls/{call_id}/end")
async def end_call(call_id: str, request: Request):
    try: return await request.app.state.calls.end_call(call_id)
    except KeyError as exc: raise HTTPException(404, "Call not found") from exc


@router.post("/demo/calls/{call_id}/end", include_in_schema=False)
async def end_demo_call(call_id: str, request: Request):
    return await end_call(call_id, request)


@router.post("/demo/calls/{call_id}/faults/{fault}")
async def fault(call_id: str, fault: str, request: Request):
    try: return await request.app.state.calls.inject_fault(call_id, fault)
    except KeyError as exc: raise HTTPException(404, "Call or fault not found") from exc


@router.get("/calls/{call_id}")
async def call_snapshot(call_id: str, request: Request):
    try: return await request.app.state.calls.snapshot(call_id)
    except KeyError as exc: raise HTTPException(404, "Call not found") from exc


@router.get("/calls/{call_id}/summary")
async def call_summary(call_id: str, request: Request):
    snapshot = await call_snapshot(call_id, request)
    if not snapshot.summary: raise HTTPException(404, "Summary not ready")
    return snapshot.summary


@router.get("/calls/{call_id}/trajectories")
async def trajectories(call_id: str, request: Request):
    if call_id not in request.app.state.calls._call_sessions:
        raise HTTPException(404, "Call not found")
    return request.app.state.calls.trajectories.get(call_id, [])


@router.get("/customers/{customer_id}/precall-brief")
async def brief(customer_id: str, request: Request): return await request.app.state.calls.pre_call_brief(customer_id)


@router.get("/customers/{customer_id}/history")
async def history(customer_id: str, request: Request): return await request.app.state.calls.history(customer_id)


@router.post("/recommendations/{recommendation_id}/feedback", status_code=201)
async def feedback(recommendation_id: str, body: FeedbackRequest, request: Request):
    return request.app.state.calls.record_feedback(recommendation_id, body.useful, body.reason)


@router.get("/evidence/{evidence_id}")
async def evidence(evidence_id: str, request: Request):
    for session_id in request.app.state.calls._call_sessions.values():
        session = await request.app.state.calls.store.get(session_id)
        match = next((item for item in session.evidence if item.id == evidence_id), None)
        if match: return match
    raise HTTPException(404, "Evidence not found")


@router.get("/metrics")
async def metrics(request: Request):
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
