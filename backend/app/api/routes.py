"""
P_311 FastAPI REST Router
Provides endpoints for health, telemetry history, faults, diagnoses, RAG, and simulator control.
"""
import asyncio
from datetime import datetime, timezone
import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from backend.app.core.config import settings
from backend.app.db.database import db_manager
from backend.app.diagnosis.llm_client import llm_client
from backend.app.models.schemas import HealthResponse, SimulationCommand
from backend.app.mqtt.consumer import mqtt_service
from backend.app.rag.knowledge_indexer import knowledge_indexer

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health():
    """System diagnostic health check."""
    llm_online = await llm_client.is_available()
    chunks_count = len(knowledge_indexer.chunks)

    return HealthResponse(
        status="healthy",
        mqtt_broker=mqtt_service.is_connected,
        database=True,
        database_type="postgresql" if db_manager.use_postgres else "sqlite",
        grafana_url=settings.GRAFANA_URL,
        ollama_llm=llm_online,
        model_name=settings.LLM_MODEL,
        vector_store_chunks=chunks_count,
        active_machine=settings.DEFAULT_MACHINE_ID,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@router.get("/machines")
async def list_machines():
    return await db_manager.get_machines()


@router.get("/machines/{machine_id}")
async def get_machine(machine_id: str):
    m = await db_manager.get_machine(machine_id)
    if not m:
        raise HTTPException(status_code=404, detail="Machine not found")
    return m


@router.get("/telemetry/latest")
async def get_latest_telemetry(machine_id: str = settings.DEFAULT_MACHINE_ID):
    data = await db_manager.get_latest_telemetry(machine_id)
    if not data:
        return {}
    return data


@router.get("/telemetry/history")
async def get_telemetry_history(
    machine_id: str = settings.DEFAULT_MACHINE_ID,
    limit: int = Query(60, ge=1, le=500)
):
    return await db_manager.get_recent_telemetry(machine_id, limit=limit)


@router.get("/telemetry/stream")
async def telemetry_stream(request: Request):
    """
    Server-Sent Events (SSE) endpoint providing real-time telemetry streaming at 1 Hz.
    Eliminates WebSocket overhead while providing auto-reconnect and instant UI updates.
    """
    queue: asyncio.Queue = asyncio.Queue(maxsize=30)
    mqtt_service.sse_queues.add(queue)

    async def event_generator():
        try:
            # Send initial connection heartbeat
            yield f"event: connected\ndata: {json.dumps({'message': 'Connected to P_311 Live Telemetry Stream'})}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    payload = await asyncio.wait_for(queue.get(), timeout=2.0)
                    yield f"data: {payload}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat comment to keep connection alive
                    yield ": ping\n\n"
        finally:
            mqtt_service.sse_queues.discard(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/faults")
async def get_faults(
    machine_id: str = settings.DEFAULT_MACHINE_ID,
    limit: int = Query(50, ge=1, le=100)
):
    return await db_manager.get_fault_events(machine_id, limit=limit)


@router.get("/faults/{fault_id}")
async def get_fault(fault_id: str):
    f = await db_manager.get_fault_event_by_id(fault_id)
    if not f:
        raise HTTPException(status_code=404, detail="Fault event not found")
    return f


@router.get("/diagnosis/latest")
async def get_latest_diagnosis(machine_id: str = settings.DEFAULT_MACHINE_ID):
    diag = await db_manager.get_latest_diagnosis(machine_id)
    if not diag:
        return {}
    return diag


@router.get("/diagnosis/{diagnosis_id}")
async def get_diagnosis(diagnosis_id: str):
    d = await db_manager.get_diagnosis_by_id(diagnosis_id)
    if not d:
        raise HTTPException(status_code=404, detail="Diagnosis not found")
    return d


# Simulator Controls
@router.post("/simulation/fault")
async def inject_simulation_fault(cmd: SimulationCommand):
    """Injects a physical fault mode into the simulator via MQTT."""
    payload = {
        "command": "inject_fault",
        "fault_type": cmd.fault_type or "bearing_degradation"
    }
    machine_id = cmd.machine_id or settings.DEFAULT_MACHINE_ID
    success = mqtt_service.publish_command(machine_id, payload)
    return {"status": "success" if success else "failed", "injected_fault": cmd.fault_type}


@router.post("/simulation/reset")
async def reset_simulation(machine_id: str = settings.DEFAULT_MACHINE_ID):
    """Resets simulator to normal baseline operating parameters."""
    payload = {"command": "reset"}
    success = mqtt_service.publish_command(machine_id, payload)
    await db_manager.update_machine_status(machine_id, "healthy")
    return {"status": "success" if success else "failed", "mode": "normal"}


@router.post("/simulation/start")
async def start_simulation(machine_id: str = settings.DEFAULT_MACHINE_ID):
    success = mqtt_service.publish_command(machine_id, {"command": "start"})
    return {"status": "success" if success else "failed"}


@router.post("/simulation/stop")
async def stop_simulation(machine_id: str = settings.DEFAULT_MACHINE_ID):
    success = mqtt_service.publish_command(machine_id, {"command": "stop"})
    return {"status": "success" if success else "failed"}


# Knowledge Base & RAG endpoints
@router.post("/knowledge/ingest")
async def ingest_knowledge():
    count = knowledge_indexer.ingest_all()
    return {"status": "success", "chunks_indexed": count}


@router.get("/knowledge/search")
async def search_knowledge(
    q: str = Query(..., description="Semantic query string"),
    top_k: int = Query(3, ge=1, le=10)
):
    results = knowledge_indexer.search(q, top_k=top_k)
    return {"query": q, "results": results}


@router.post("/assistant/chat")
async def assistant_chat(payload: Dict[str, Any]):
    """
    Interactive engineering assistant & viva Q&A endpoint.
    Answers technical questions using live telemetry, active diagnoses, and RAG technical manuals.
    """
    import httpx
    user_msg = payload.get("message", "").strip()
    if not user_msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    machine_id = payload.get("machine_id", settings.DEFAULT_MACHINE_ID)
    latest_tel = await db_manager.get_latest_telemetry(machine_id)
    latest_diag = await db_manager.get_latest_diagnosis(machine_id)

    # 1. Semantic RAG Search
    chunks = knowledge_indexer.search(user_msg, top_k=3)
    citations = [f"{c['doc_title']} ({c['section']})" for c in chunks]
    context_text = "\n\n".join([f"[{c['doc_title']} > {c['section']}]\n{c['raw_text']}" for c in chunks])

    system = (
        "You are an Industrial Equipment Reliability Engineer and Expert Viva Assistant. "
        "Answer the question clearly, concisely, and authoritatively using the retrieved documentation excerpts "
        "and current equipment telemetry. Highlight ISO 10816 vibration standards and safety guidelines when relevant."
    )
    prompt = f"""
Current Machine Telemetry:
{json.dumps(latest_tel, indent=2) if latest_tel else "Normal baseline (Healthy)"}

Active Diagnosis:
{latest_diag.get('fault_title', 'None - System Normal') if latest_diag else 'None - System Normal'}

Retrieved Technical Documentation Excerpts:
{context_text if context_text else "General industrial motor standard ISO 10816-3 guidelines apply."}

User Question: {user_msg}

Answer concisely with technical precision and actionable insights.
"""

    reply_text = None
    try:
        if await llm_client.is_available():
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(f"{settings.LLM_BASE_URL}/api/generate", json={
                    "model": settings.LLM_MODEL,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_ctx": 2048}
                })
                if res.status_code == 200:
                    reply_text = res.json().get("response", "").strip()

        if not reply_text:
            excerpt = chunks[0]["raw_text"] if chunks else "All readings within nominal bounds. Refer to ISO 10816 standards."
            reply_text = f"**Knowledge Base Direct Documentation Reference:**\n\n{excerpt}"
            return {"reply": reply_text, "citations": citations, "is_fallback": True}

        return {"reply": reply_text, "citations": citations, "is_fallback": False}
    except Exception as e:
        excerpt = chunks[0]["raw_text"] if chunks else "Refer to equipment maintenance manual."
        return {"reply": f"**Technical Manual Reference:**\n\n{excerpt}", "citations": citations, "is_fallback": True}


@router.get("/reports/work-order")
async def generate_work_order(machine_id: str = settings.DEFAULT_MACHINE_ID):
    """Generates a printable HTML Maintenance Work Order based on active diagnosis."""
    from fastapi.responses import HTMLResponse
    diag = await db_manager.get_latest_diagnosis(machine_id)
    tel = await db_manager.get_latest_telemetry(machine_id)
    machine = await db_manager.get_machine(machine_id)

    title = diag.get("fault_title", "Routine Maintenance Inspection") if diag else "Routine Maintenance Inspection"
    severity = (diag.get("severity", "NORMAL") if diag else "NORMAL").upper()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    causes_html = "".join([f"<li>{c}</li>" for c in diag.get("likely_causes", ["Normal baseline operating condition."])]) if diag else "<li>Nominal wear and tear.</li>"
    checks_html = "".join([f"<li>[ ] {c}</li>" for c in diag.get("recommended_checks", ["Daily shift inspection."])]) if diag else "<li>[ ] Perform shift inspection.</li>"
    actions_html = "".join([f"<li>-> {c}</li>" for c in diag.get("corrective_actions", ["Continue continuous telemetry monitoring."])]) if diag else "<li>-> Log hourly readings.</li>"
    citations_html = "".join([f"<span class='badge'>{s}</span>" for s in diag.get("knowledge_sources", ["General Motor Manual"])]) if diag else "<span class='badge'>ISO 10816-3</span>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>Maintenance Work Order - {machine_id}</title>
      <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 30px; color: #1e293b; background: #fff; }}
        .header {{ border-bottom: 3px solid #0284c7; padding-bottom: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; }}
        h1 {{ margin: 0; font-size: 24px; color: #0f172a; }}
        .badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: bold; background: #e0f2fe; color: #0369a1; margin-right: 5px; }}
        .badge-critical {{ background: #ffe4e6; color: #be123c; }}
        .badge-high {{ background: #fef3c7; color: #b45309; }}
        .table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        .table th, .table td {{ border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; font-size: 13px; }}
        .table th {{ background: #f1f5f9; }}
        ul {{ font-size: 13px; line-height: 1.6; }}
        .sig-block {{ margin-top: 40px; display: flex; justify-content: space-between; font-size: 12px; border-top: 1px solid #cbd5e1; padding-top: 15px; }}
        @media print {{
          .no-print {{ display: none; }}
          body {{ margin: 0; }}
        }}
      </style>
    </head>
    <body>
      <div class="no-print" style="margin-bottom: 20px;">
        <button onclick="window.print()" style="padding: 10px 20px; background: #0284c7; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
          🖨 Print / Save as PDF
        </button>
      </div>
      <div class="header">
        <div>
          <h1>INDUSTRIAL MAINTENANCE WORK ORDER</h1>
          <div style="font-size: 12px; color: #64748b; margin-top: 5px;">Project P_311 AI-Assisted IoT Diagnostic Assistant</div>
        </div>
        <div style="text-align: right; font-size: 12px;">
          <div><strong>Order Ref:</strong> WO-{datetime.now().strftime('%Y%m%d%H%M')}</div>
          <div><strong>Date:</strong> {now_str}</div>
          <div><strong>Machine:</strong> {machine_id} ({machine.get('type') if machine else '11 kW Motor'})</div>
        </div>
      </div>

      <div style="margin-bottom: 15px;">
        <strong>Fault Classification:</strong> {title}
        <span class="badge {('badge-critical' if severity == 'CRITICAL' else 'badge-high') if severity != 'NORMAL' else ''}">{severity}</span>
      </div>

      <h3>1. Measured Sensor Evidence at Alarm Time</h3>
      <table class="table">
        <tr><th>Sensor</th><th>Recorded Value</th><th>Nominal Rating</th><th>ISO / Physical Limit</th></tr>
        <tr><td>Stator / Bearing Temperature</td><td><strong>{tel.get('temperature', '--')} °C</strong></td><td>45 – 65 °C</td><td>Warning > 75 °C | Trip > 95 °C</td></tr>
        <tr><td>Vibration Velocity RMS</td><td><strong>{tel.get('vibration', '--')} mm/s</strong></td><td>&lt; 1.8 mm/s (Zone A)</td><td>ISO Zone C > 4.5 | Zone D > 7.1</td></tr>
        <tr><td>Stator Line Current</td><td><strong>{tel.get('current', '--')} A</strong></td><td>9.0 A (Rated FLA)</td><td>Warning > 11.5 A | Trip > 13.5 A</td></tr>
        <tr><td>Shaft Speed (RPM)</td><td><strong>{tel.get('rpm', '--')} RPM</strong></td><td>1485 RPM</td><td>Min Slip > 1440 RPM</td></tr>
        <tr><td>Cooling / Lube Pressure</td><td><strong>{tel.get('pressure', '--')} bar</strong></td><td>3.8 – 4.5 bar</td><td>Trip &lt; 2.0 bar</td></tr>
      </table>

      <h3>2. Plausible Root Causes</h3>
      <ul>{causes_html}</ul>

      <h3>3. Mandatory Diagnostic Procedures (Checklist)</h3>
      <ul style="list-style-type: none; padding-left: 0;">{checks_html}</ul>

      <h3>4. Required Corrective Actions & Safety Notes</h3>
      <ul style="list-style-type: none; padding-left: 0;">{actions_html}</ul>
      <div style="font-size: 11px; background: #fffbeb; border-left: 4px solid #f59e0b; padding: 8px; margin: 10px 0;">
        <strong>MANDATORY SAFETY:</strong> Prior to mechanical disassembly or terminal box access, perform strict Lockout/Tagout (LOTO) on the upstream 400V circuit breaker.
      </div>

      <h3>5. Technical Documentation Citations</h3>
      <div>{citations_html}</div>

      <div class="sig-block">
        <div><strong>Lead Maintenance Technician:</strong> _______________________</div>
        <div><strong>Plant Electrical Reliability Engineer:</strong> _______________________</div>
        <div><strong>Status:</strong> [ ] Open &nbsp; [ ] In Progress &nbsp; [ ] Signed Off</div>
      </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

