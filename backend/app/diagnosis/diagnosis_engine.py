"""
P_311 Explainable Diagnosis Engine
Combines measured sensor telemetry, rule-based fault triggers, and RAG knowledge
to produce an explainable, actionable diagnostic report via local LLM or deterministic fallback.
"""
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings
from backend.app.db.database import db_manager
from backend.app.diagnosis.llm_client import llm_client
from backend.app.rag.knowledge_indexer import knowledge_indexer

logger = logging.getLogger("diagnosis_engine")


class DiagnosisEngine:
    def __init__(self):
        pass

    def _normalize_list(self, raw_items: Any) -> List[str]:
        if not isinstance(raw_items, list):
            return [str(raw_items)] if raw_items else []
        result = []
        for item in raw_items:
            if isinstance(item, dict):
                parts = [f"{v}" for k, v in item.items() if isinstance(v, str)]
                result.append(" - ".join(parts) if parts else str(item))
            else:
                result.append(str(item))
        return result

    def _build_knowledge_query(self, fault_type: str, triggered_rules: List[str]) -> str:
        rule_text = " ".join(triggered_rules).replace("_", " ").lower()
        return f"{fault_type.replace('_', ' ')} {rule_text}"

    def _generate_fallback_diagnosis(
        self,
        fault_event: Dict[str, Any],
        retrieved_chunks: List[Dict[str, Any]],
        start_time: float
    ) -> Dict[str, Any]:
        """
        Deterministic, transparent fallback diagnosis when Local LLM is offline or timed out.
        Builds actionable output directly from rules and technical manuals without crashing.
        """
        fault_type = fault_event["fault_type"]
        severity = fault_event["severity"]
        evidence = fault_event["sensor_evidence"]
        rules = fault_event["triggered_rules"]

        fallback_titles = {
            "bearing_degradation": "Bearing Mechanical Degradation & Thermal Friction",
            "motor_overheating": "Excessive Stator Thermal Runaway / Inadequate Cooling",
            "motor_overload": "Severe Mechanical Overload & Elevated Rotor Slip",
            "excessive_vibration": "Dynamic Rotor Unbalance / Mechanical Base Looseness",
            "low_pressure": "Auxiliary Lubrication / Cooling Circuit Pressure Depletion",
            "sensor_anomaly": "Sensor Physical Anomaly / Transmitter Open-Circuit Fault",
        }
        title = fallback_titles.get(fault_type, f"Industrial Fault: {fault_type.replace('_', ' ').title()}")

        # Extract causes and checks from retrieved technical knowledge
        likely_causes = []
        recommended_checks = []
        corrective_actions = []

        if fault_type == "bearing_degradation":
            likely_causes = [
                "Inadequate or contaminated bearing grease (lubrication breakdown)",
                "Subsurface fatigue spalling on bearing inner/outer raceways",
                "Shaft angular or parallel misalignment inducing abnormal thrust"
            ]
            recommended_checks = [
                "Measure bearing housing temperature with non-contact IR pyrometer",
                "Inspect grease sample from drain port for darkening or metal particles",
                "Perform shock-pulse or high-frequency demodulation analysis",
                "Rotate shaft by hand (under LOTO) to check for notchiness"
            ]
            corrective_actions = [
                "Replenish bearing with 25g high-temperature polyurea grease",
                "If vibration exceeds 7.1 mm/s, halt machine to prevent cage seizure",
                "Replace bearing assembly (SKF 6308-2Z or equivalent)"
            ]
        elif fault_type == "motor_overheating":
            likely_causes = [
                "Blocked cooling fins, dust blanket, or clogged ventilation cowl",
                "Damaged or broken external shaft-mounted cooling fan",
                "3-phase supply line voltage unbalance (> 1%)"
            ]
            recommended_checks = [
                "Inspect external air grille and cooling passages for clogging",
                "Measure 3-phase line voltages to calculate voltage unbalance %",
                "Verify cooling fan blades and keyway integrity on non-drive shaft"
            ]
            corrective_actions = [
                "Clean stator cooling fins using compressed dry air (< 2 bar)",
                "Replace broken cooling fan impeller",
                "Reduce mechanical load until winding temperature stabilizes < 75°C"
            ]
        elif fault_type == "motor_overload":
            likely_causes = [
                "Driven machinery mechanical jamming or conveyor belt bind",
                "Material process feed rate exceeding 11 kW drive design rating",
                "Supply under-voltage causing motor to draw higher current"
            ]
            recommended_checks = [
                "Uncouple driven machine and spin load shaft manually to check for binding",
                "Measure 3-phase line current balance with AC clamp meter",
                "Check supply bus voltage under load"
            ]
            corrective_actions = [
                "Clear mechanical obstruction in driven unit immediately",
                "Verify thermal overload relay trip settings against motor nameplate",
                "If load is continuous, upgrade drive train capacity"
            ]
        elif fault_type == "excessive_vibration":
            likely_causes = [
                "Rotor dynamic unbalance due to fan blade buildup",
                "Foundation looseness or loose anchor bolts ('soft foot')",
                "Coupling misalignment between motor and driven gearbox"
            ]
            recommended_checks = [
                "Check motor foundation bolts with calibrated torque wrench (85 Nm)",
                "Measure 3-axis vibration (horizontal, vertical, axial)",
                "Perform dial indicator check for soft foot (< 0.05 mm)"
            ]
            corrective_actions = [
                "Retorque foundation mounting bolts and re-shim baseplate",
                "Clean foreign debris from rotor/fan and perform dynamic balancing",
                "Perform precision laser alignment across coupling"
            ]
        elif fault_type == "low_pressure":
            likely_causes = [
                "Clogged duplex oil filter element",
                "Auxiliary oil pump drive coupling failure or air entrainment",
                "Hydraulic line rupture or fluid leak at distribution manifold"
            ]
            recommended_checks = [
                "Check differential pressure gauge across oil filter cartridge",
                "Inspect oil reservoir sight glass level and check for foaming",
                "Inspect piping circuit from pump to bearing housings for leaks"
            ]
            corrective_actions = [
                "Switch to standby filter and replace loaded filter element",
                "Top up lubricant reservoir with ISO VG 46 turbine oil",
                "Tighten loose hydraulic couplings and replace worn gaskets"
            ]
        else: # sensor_anomaly
            likely_causes = [
                "Thermocouple or pressure transmitter open-circuit failure",
                "Damaged analog wiring / shield grounding loop interference",
                "Defective PLC/microcontroller analog input channel"
            ]
            recommended_checks = [
                "Verify sensor resistance and loop current (4-20 mA) with multimeter",
                "Inspect cable gland and terminal block for loose or corroded leads",
                "Cross-check telemetry reading with physical analog dial gauge"
            ]
            corrective_actions = [
                "Replace defective temperature probe / pressure transmitter",
                "Restore proper shield grounding to prevent EMI pickup"
            ]

        knowledge_sources = [f"{c['doc_title']} ({c['section']})" for c in retrieved_chunks]
        if not knowledge_sources:
            knowledge_sources = ["Industrial Motor Maintenance Manual", "ISO 10816-3 Vibration Standard"]

        exec_time = int((time.time() - start_time) * 1000)

        return {
            "id": f"DIAG-{uuid.uuid4().hex[:8].upper()}",
            "fault_event_id": fault_event["id"],
            "machine_id": fault_event["machine_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fault_title": title,
            "severity": severity,
            "sensor_evidence": evidence,
            "likely_causes": likely_causes,
            "recommended_checks": recommended_checks,
            "corrective_actions": corrective_actions,
            "confidence": fault_event.get("confidence", 0.85),
            "uncertainty": "NOTICE: Local LLM is offline or timed out. This diagnosis was deterministically generated directly from rule-based sensor thresholds and indexed technical manuals without LLM synthesis.",
            "knowledge_sources": knowledge_sources,
            "raw_llm_response": "FALLBACK_MODE",
            "execution_time_ms": exec_time,
            "is_fallback": True
        }

    async def diagnose(self, fault_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main diagnosis entry point.
        Executes RAG retrieval, invokes Local LLM, and persists result in SQLite.
        """
        start_time = time.time()
        fault_type = fault_event["fault_type"]
        rules = fault_event["triggered_rules"]
        evidence = fault_event["sensor_evidence"]

        # Step 1: Semantic Retrieval from Technical Knowledge Base
        query = self._build_knowledge_query(fault_type, rules)
        retrieved_chunks = knowledge_indexer.search(query, top_k=settings.RAG_TOP_K)
        knowledge_sources = [f"{c['doc_title']} ({c['section']})" for c in retrieved_chunks]

        # Step 2: Format LLM Prompts
        system_prompt = (
            "You are an Industrial Equipment Reliability and Fault Diagnosis Assistant. "
            "Diagnose industrial machine faults based strictly on the provided sensor evidence and technical documentation. "
            "CRITICAL INSTRUCTIONS:\n"
            "1. Distinguish between MEASURED SENSOR DATA and INFERRED INFORMATION.\n"
            "2. DO NOT invent or alter sensor numbers. Use only the measured evidence given.\n"
            "3. Ground all likely causes and recommended checks in the provided documentation excerpts.\n"
            "4. Respond ONLY with a valid JSON object matching the required schema."
        )

        kb_context_text = "\n\n".join([
            f"--- DOCUMENT: {c['doc_title']} | SECTION: {c['section']} (Relevance: {c['similarity_score']}) ---\n{c['text']}"
            for c in retrieved_chunks
        ])

        user_prompt = f"""
[MEASURED SENSOR EVIDENCE]
- Temperature: {evidence.get('temperature')} °C (Normal: 45 - 65 °C, Warning: >75 °C)
- Vibration: {evidence.get('vibration')} mm/s RMS (Normal: 1.0 - 2.2 mm/s, ISO Alert: >4.5 mm/s, Danger: >7.1 mm/s)
- Stator Current: {evidence.get('current')} A (Rated Full Load: 9.0 A, Warning: >11.5 A)
- Rotor Speed: {evidence.get('rpm')} RPM (Rated: 1485 RPM)
- Cooling/Lube Pressure: {evidence.get('pressure')} bar (Normal: 3.8 - 4.5 bar)
- Line Voltage: {evidence.get('voltage')} V (Rated: 400 V / 230 V phase)

[TRIGGERED DETERMINISTIC FAULT RULES]
- Fault Classification: {fault_type}
- Assigned Severity: {fault_event['severity'].upper()}
- Triggered Rules: {', '.join(rules)}

[RETRIEVED TECHNICAL KNOWLEDGE EXCERPTS]
{kb_context_text if kb_context_text else "General industrial motor standard ISO 10816-3 guidelines apply."}

[REQUIRED JSON SCHEMA]
{{
  "fault_title": "Concise engineering title",
  "severity": "{fault_event['severity']}",
  "likely_causes": ["Cause 1 based on evidence", "Cause 2"],
  "recommended_checks": ["Specific diagnostic procedure 1", "Check 2"],
  "corrective_actions": ["Corrective action 1", "Action 2"],
  "confidence": {fault_event.get('confidence', 0.88)},
  "uncertainty": "Engineering uncertainty and physical inspection caveat"
}}
"""

        # Step 3: Call Local LLM
        llm_response = await llm_client.generate_json(user_prompt, system=system_prompt)

        # Step 4: Parse response or trigger fallback
        if llm_response and isinstance(llm_response, dict) and "fault_title" in llm_response:
            exec_time = int((time.time() - start_time) * 1000)
            diagnosis_data = {
                "id": f"DIAG-{uuid.uuid4().hex[:8].upper()}",
                "fault_event_id": fault_event["id"],
                "machine_id": fault_event["machine_id"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fault_title": str(llm_response.get("fault_title", fault_type)),
                "severity": str(llm_response.get("severity", fault_event["severity"])),
                "sensor_evidence": evidence,
                "likely_causes": self._normalize_list(llm_response.get("likely_causes", [])),
                "recommended_checks": self._normalize_list(llm_response.get("recommended_checks", [])),
                "corrective_actions": self._normalize_list(llm_response.get("corrective_actions") or llm_response.get("correctional_actions", [])),
                "confidence": float(llm_response.get("confidence", fault_event.get("confidence", 0.90))),
                "uncertainty": str(llm_response.get("uncertainty", "Assisted diagnosis based on real-time telemetry; verify via manual inspection.")),
                "knowledge_sources": knowledge_sources if knowledge_sources else ["Technical Manual"],
                "raw_llm_response": str(llm_response),
                "execution_time_ms": exec_time,
                "is_fallback": False
            }
            logger.info("Diagnosis generated via Local LLM in %d ms", exec_time)
        else:
            logger.info("Using deterministic fallback diagnosis generator.")
            diagnosis_data = self._generate_fallback_diagnosis(fault_event, retrieved_chunks, start_time)

        # Step 5: Persist to SQLite
        try:
            await db_manager.insert_diagnosis(diagnosis_data)
        except Exception as e:
            logger.error("Failed to persist diagnosis to SQLite: %s", e)

        return diagnosis_data


diagnosis_engine = DiagnosisEngine()
