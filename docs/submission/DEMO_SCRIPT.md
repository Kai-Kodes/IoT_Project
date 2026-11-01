# Demonstration Script & Video Narration Guide
## Project P_311: Knowledge-Driven IoT Fault Diagnosis Assistant

---

### Demonstration Overview
- **Target Video Duration**: 5 to 7 Minutes
- **Target Audience**: College Evaluators, External Viva Examiners, Industrial Reliability Engineers
- **Required Video Setup**: Screen recording software (e.g., OBS Studio, SimpleScreenRecorder) capturing a 1080p desktop showing terminal windows, React Dashboard (`localhost:8000`), and Grafana (`localhost:3000`).

---

## Timeline & Scene-by-Scene Script

```
0:00 - 0:45 | Scene 1: Project Title & Industrial Motivation
0:45 - 1:30 | Scene 2: Architectural Overview & One-Click Startup
1:30 - 2:30 | Scene 3: Baseline Normal Telemetry & Digital Twin Motor
2:30 - 3:45 | Scene 4: Fault Injection, Deterministic Tripping & Audio Alarm
3:45 - 4:45 | Scene 5: Local RAG Knowledge Citations & AI Work Order Synthesis
4:45 - 5:45 | Scene 6: Printable Maintenance Work Order & Grafana SCADA View
5:45 - 6:30 | Scene 7: Interactive Viva AI Tutor Chat & Graceful Fallback Mode
6:30 - 7:00 | Scene 8: Conclusion & Summary
```

---

### Scene 1: Title & Industrial Motivation (0:00 – 0:45)
- **Visual**: Title slide on screen, transitioning to the clean desktop workspace.
- **Screen Recording**: Show project repository in terminal and title slide.
- **Narration**:
  > *"Good morning, respected evaluators. Welcome to the demonstration of Project P_311: Knowledge-Driven IoT Fault Diagnosis Assistant for Industrial Rotating Machinery.*  
  >  
  > *In manufacturing plants, 3-phase induction motors drive critical pumps, fans, and compressors. When a motor fails unexpectedly—often due to bearing wear or stator overheating—it can halt an entire production line, costing plants over $50,000 an hour in downtime.*  
  >  
  > *While conventional SCADA systems trigger loud threshold alarms, they tell operators WHAT tripped, but never WHY it failed or HOW to repair it safely. Furthermore, cloud-based predictive platforms risk leaking proprietary operational data and suffer from internet latency.*  
  >  
  > *P_311 solves this by combining sub-millisecond deterministic safety trips conforming to ISO 10816-3 with local semantic RAG and a local quantized Large Language Model—running 100% locally on standard workstation hardware with zero cloud dependencies."*

---

### Scene 2: Architecture & One-Click Startup (0:45 – 1:30)
- **Visual**: Open terminal in project root `/home/redsheronin/Files/Coding/College/IoT/proj`.
- **Screen Recording**: Execute `./start.sh` in the terminal and highlight the startup logs.
- **Narration**:
  > *"Let us launch the entire system using our automated master control script: `./start.sh`.*  
  >  
  > *Notice the startup sequence:  
  > 1. It launches our infrastructure containers—PostgreSQL 16 on port 5433 and Grafana on port 3000. It automatically detects our active Mosquitto broker on port 1883 to prevent address collisions.  
  > 2. It verifies our local Ollama AI daemon running the `qwen2.5:1.5b` model on port 11434.  
  > 3. It boots our FastAPI backend and React frontend on port 8000.  
  > 4. It starts our 11 kW industrial motor physical simulator.  
  > 5. Finally, it launches our secure public tunnel for remote access.  
  >  
  > All services are online in under 8 seconds."*

---

### Scene 3: Baseline Normal Telemetry & Digital Twin Motor (1:30 – 2:30)
- **Visual**: Switch browser to `http://localhost:8000`.
- **Screen Recording**: Pan across the React dashboard showing live telemetry sparklines, metric cards, and the SVG Digital Twin motor.
- **Narration**:
  > *"Here is the P_311 React diagnostic dashboard. Telemetry is streaming in real-time at 1 Hz directly from our MQTT broker over Server-Sent Events—eliminating WebSocket polling overhead.*  
  >  
  > *Let us observe the baseline normal readings for our 11 kW motor, MOTOR-001:  
  > - Stator Temperature is running nominal at 51.5°C (well within normal limits).  
  > - Vibration Velocity RMS is at 1.45 mm/s, conforming to ISO 10816-3 Zone A—the standard for newly commissioned machines.  
  > - Stator Line Current is at 8.8 Amperes against our rated 9.0 Amperes.  
  > - Shaft Speed is stable at 1485 RPM with 1.0% rated rotor slip.  
  > - Lubrication Pressure is healthy at 4.2 bar.*  
  >  
  > *Notice our interactive SVG Digital Twin motor in the center: the rotor rotates dynamically in real-time proportional to shaft RPM, and the stator casing reflects a cool cyan glow, indicating nominal thermal state."*

---

### Scene 4: Fault Injection, Deterministic Tripping & Audio Alarm (2:30 – 3:45)
- **Visual**: Scroll to the Simulation Control Panel on the dashboard.
- **Screen Recording**: Click the **"Bearing Degradation"** button. Show telemetry curves spiking, audio alarm beeping, and warning status badge appearing.
- **Narration**:
  > *"Now, let us test the system under industrial emergency conditions. In the Simulation Control Panel, I will inject a physical Bearing Degradation fault.*  
  >  
  > *Watch the telemetry shift in real-time:  
  > - As mechanical friction accumulates, vibration velocity ramps past 4.5 mm/s, immediately breaching ISO 10816-3 Zone C.  
  > - Bearing temperature rapidly climbs past 78°C.  
  >  
  > Notice what happened: in less than 1 millisecond, our deterministic rule detector flagged the compound condition: `HIGH_VIBRATION_ZONE_C_ALARM` coupled with `HIGH_TEMPERATURE_FRICTION`.  
  >  
  > The dashboard sounds an industrial audio alarm, the machine badge transitions to WARNING, and the SVG Digital Twin motor glows amber to alert the operator."*

---

### Scene 5: Local RAG Knowledge Citations & AI Work Order Synthesis (3:45 – 4:45)
- **Visual**: Scroll to the Active Diagnostic Report card on the dashboard.
- **Screen Recording**: Highlight the diagnostic checklist, root-cause analysis, and the RAG manual citations.
- **Narration**:
  > *"Notice that we did not ask a cloud LLM to guess whether the machine should trip. Safety was secured deterministically.*  
  >  
  > *Simultaneously, our local RAG pipeline searched 34 technical manual sections using `all-MiniLM-L6-v2` embeddings on the CPU in 0.6 milliseconds. It extracted the exact manufacturer procedures for bearing raceway fatigue and polyurea grease replenishment.*  
  >  
  > *Our local 1.5B parameter LLM, running on our laptop's GPU, synthesized this grounded diagnostic work order:  
  > - Likely Causes: Lubrication breakdown and inner raceway spalling.  
  > - Mandatory Safety: Perform strict Lockout/Tagout on the 400V circuit breaker.  
  > - Diagnostic Checklist: Inspect grease drain port, check for metal flakes, and perform high-frequency shock pulse analysis.  
  > - Actionable Solution: Replenish bearing with 25g polyurea grease.  
  >  
  > Every finding includes clickable citations directly referencing `bearing_troubleshooting_guide.md`."*

---

### Scene 6: Printable Work Order & Grafana SCADA View (4:45 – 5:45)
- **Visual**: Click "Print Work Order", show the generated HTML/PDF print layout. Then switch browser tab to `http://localhost:3000` (Grafana).
- **Screen Recording**: Demonstrate the printable maintenance work order with signature blocks. Then show Grafana operational time-series panels with ISO threshold lines.
- **Narration**:
  > *"For factory technicians, a single click on 'Print Work Order' generates an official industrial maintenance order. It includes the exact sensor snapshot at alarm time, manufacturer checklists, and sign-off blocks for the plant electrical reliability engineer.*  
  >  
  > *Now let us switch to our operational SCADA interface: Grafana on port 3000.  
  > Plant control room operators need high-density historical trends. Grafana connects directly to our PostgreSQL 16 database. Notice the multi-channel panels:  
  > - Stator Temperature with IEC Class F reference lines.  
  > - Vibration Velocity RMS plotted against ISO 10816 Zone C and Zone D trip boundaries.  
  > - Stator line current with Full Load Ampere thresholds.*  
  >  
  > *This demonstrates our strict separation of concerns: Grafana monitors time-series operations, while React delivers explainable AI diagnosis."*

---

### Scene 7: Viva AI Tutor Chat & Graceful Fallback Mode (5:45 – 6:30)
- **Visual**: Return to React dashboard, scroll to Viva Assistant Chat at the bottom.
- **Screen Recording**: Type: *"Why did the bearing degradation alarm trigger?"* Show the immediate grounded response.
- **Narration**:
  > *"At the bottom of our dashboard, we built an interactive Viva AI Tutor. Students and technicians can ask technical engineering questions.  
  >  
  > I will type: 'Why did the bearing degradation alarm trigger?'  
  > The assistant responds immediately, citing ISO 10816 Zone C limits, referencing current machine vibration of 5.8 mm/s, and citing the bearing troubleshooting manual.  
  >  
  > Furthermore, if our GPU runs out of VRAM or Ollama is stopped, the backend automatically engages our Deterministic Fallback Mode. It generates complete, standards-based diagnostic work orders using pre-compiled templates—guaranteeing 100% system uptime."*

---

### Scene 8: Conclusion & Summary (6:30 – 7:00)
- **Visual**: Click "Reset Simulation" (system returns to green normal state), then show terminal executing `./stop.sh`.
- **Screen Recording**: Show clean shutdown output in terminal and final slide.
- **Narration**:
  > *"When we click 'Reset Simulation', the motor transitions back to healthy baseline parameters within 3 seconds.  
  >  
  > To conclude: Project P_311 proves that explainable, standards-compliant AI IoT predictive maintenance does not require expensive cloud subscriptions or massive GPU clusters. With 99.38% classification accuracy, sub-millisecond ISO tripping, local semantic RAG, and dual SCADA visualization, P_311 provides a reliable, edge-ready solution for industrial rotating machinery.*  
  >  
  > *When we are done, running `./stop.sh` cleanly terminates all containers, daemons, and public tunnels.*  
  >  
  > *Thank you, and we welcome your questions."*
