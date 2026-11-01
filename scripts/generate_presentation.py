#!/usr/bin/env python3
"""
P_311 Academic Presentation Deck Generator
Creates a professional 15-slide PowerPoint deck (docs/submission/PRESENTATION.pptx)
using python-pptx with custom layouts, colors, and engineering design.
"""
import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Color Palette
    BG_DARK = RGBColor(15, 23, 42)      # Slate 900
    TEXT_LIGHT = RGBColor(248, 250, 252) # Slate 50
    TEXT_MUTED = RGBColor(148, 163, 184) # Slate 400
    PRIMARY = RGBColor(2, 132, 199)     # Sky 600
    ACCENT_BLUE = RGBColor(56, 189, 248)# Sky 400
    ACCENT_GREEN = RGBColor(16, 185, 129)# Emerald 500
    ACCENT_AMBER = RGBColor(245, 158, 11)# Amber 500
    CARD_BG = RGBColor(30, 41, 59)      # Slate 800
    CARD_BORDER = RGBColor(51, 65, 85)  # Slate 700

    def add_slide_background(slide, color=BG_DARK):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, title_text, category_text="P_311 INDUSTRIAL IoT & PREDICTIVE MAINTENANCE"):
        # Category Banner
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = PRIMARY

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_LIGHT

    def add_card(slide, left, top, width, height, title, items, badge="", badge_color=PRIMARY):
        # Card shape
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.color.rgb = CARD_BORDER
        shape.line.width = Pt(1)

        # Text Frame
        tf = shape.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0.3)
        tf.margin_right = Inches(0.3)
        tf.margin_top = Inches(0.25)
        tf.margin_bottom = Inches(0.25)

        # Title
        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(16)
        p_title.font.bold = True
        p_title.font.color.rgb = ACCENT_BLUE

        if badge:
            p_badge = tf.add_paragraph()
            p_badge.text = f"[{badge}]"
            p_badge.font.size = Pt(10)
            p_badge.font.bold = True
            p_badge.font.color.rgb = badge_color
            p_badge.space_after = Pt(8)

        # Items
        for item in items:
            p = tf.add_paragraph()
            p.text = f"• {item}"
            p.font.size = Pt(12)
            p.font.color.rgb = TEXT_LIGHT
            p.space_after = Pt(6)

    # -------------------------------------------------------------
    # SLIDE 1: TITLE SLIDE
    # -------------------------------------------------------------
    slide1 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide1)

    t_box = slide1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(3.5))
    tf1 = t_box.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "HCLTech BTech Final Year Project Submission | Academic Defense"
    p0.font.size = Pt(12)
    p0.font.bold = True
    p0.font.color.rgb = PRIMARY
    p0.space_after = Pt(12)

    p1 = tf1.add_paragraph()
    p1.text = "P_311: Knowledge-Driven IoT Fault Diagnosis Assistant"
    p1.font.size = Pt(32)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_LIGHT
    p1.space_after = Pt(8)

    p2 = tf1.add_paragraph()
    p2.text = "Edge-Ready Industrial Rotating Machinery Monitoring with ISO 10816-3 Tripping, Local Semantic RAG & Quantized LLM Reasoning"
    p2.font.size = Pt(16)
    p2.font.color.rgb = ACCENT_BLUE
    p2.space_after = Pt(28)

    p3 = tf1.add_paragraph()
    p3.text = "Project Team: [Student Name 1] ([Reg No 1]), [Student Name 2] ([Reg No 2])\nProject Guide: [Name of Project Guide], Department of CSE / IoT\nInstitution: [Name of College / University] | Academic Year: 2025–2026"
    p3.font.size = Pt(13)
    p3.font.color.rgb = TEXT_MUTED

    # -------------------------------------------------------------
    # SLIDE 2: INDUSTRIAL CONTEXT & THE PROBLEM
    # -------------------------------------------------------------
    slide2 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide2)
    add_header(slide2, "Industrial Maintenance Challenge: Induction Motors")

    add_card(slide2, Inches(0.8), Inches(1.6), Inches(3.6), Inches(5.2),
             "Downtime Impact",
             ["Electric motors consume > 70% of total manufacturing electricity.",
              "Downtime costs range between $20,000 to $250,000 per hour in continuous manufacturing.",
              "Motor failure immediately halts production lines, compressors, and cooling pumps."],
             "CRITICAL ASSET", ACCENT_AMBER)

    add_card(slide2, Inches(4.8), Inches(1.6), Inches(3.6), Inches(5.2),
             "Root Failure Modes",
             ["Bearing Degradation (41% – 51%): Raceway spalling, cage fatigue, and grease breakdown.",
              "Stator Winding Burnout (28% – 36%): Thermal insulation aging and electrical overcurrent.",
              "Rotor & Shaft Faults (8% – 12%): Dynamic unbalance, misalignment, and soft foot."],
             "IEEE / EPRI STATS", ACCENT_GREEN)

    add_card(slide2, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.2),
             "The Monitoring Gap",
             ["Incipient degradation signals exist days before physical seizure.",
              "Conventional factory systems only collect raw numbers without diagnosing cause.",
              "Maintenance technicians lack immediate access to engineering standards."],
             "THE OPPORTUNITY", PRIMARY)

    # -------------------------------------------------------------
    # SLIDE 3: LIMITATIONS OF TRADITIONAL SYSTEMS
    # -------------------------------------------------------------
    slide3 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide3)
    add_header(slide3, "Why Traditional Plant Monitoring Fails")

    add_card(slide3, Inches(0.8), Inches(1.6), Inches(5.6), Inches(2.4),
             "1. Binary SCADA Alarms (No Context)",
             ["Simple threshold beeps ('CH-04 HIGH') tell operators THAT a fault occurred.",
              "Zero diagnostic context on WHY it occurred or HOW to repair it safely."],
             "OPERATIONAL LIMITATION", ACCENT_AMBER)

    add_card(slide3, Inches(6.8), Inches(1.6), Inches(5.7), Inches(2.4),
             "2. The Knowledge Binder Chasm",
             ["Manuals and ISO vibration charts exist in physical binders or static PDFs.",
              "Junior technicians must guess root causes under high-stress emergency conditions."],
             "MTTR INFLATION", ACCENT_AMBER)

    add_card(slide3, Inches(0.8), Inches(4.3), Inches(5.6), Inches(2.5),
             "3. Cloud Predictive Maintenance Hurdles",
             ["Exposes factory operational rates and production secrets to external clouds.",
              "Continuous high-bandwidth internet is impossible in air-gapped plants.",
              "Recurring cloud API tokens incur heavy financial overhead."],
             "PRIVACY & COST RISKS", RGBColor(239, 68, 68))

    add_card(slide3, Inches(6.8), Inches(4.3), Inches(5.7), Inches(2.5),
             "4. The Probabilistic AI Safety Fallacy",
             ["Routing raw sensor data into cloud LLMs to decide equipment trips causes 3-5s lag.",
              "Probabilistic models can hallucinate during critical safety trips."],
             "SAFETY HAZARD", RGBColor(239, 68, 68))

    # -------------------------------------------------------------
    # SLIDE 4: OBJECTIVES
    # -------------------------------------------------------------
    slide4 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide4)
    add_header(slide4, "Project Objectives & Technical Targets")

    add_card(slide4, Inches(0.8), Inches(1.6), Inches(3.6), Inches(5.2),
             "Edge Ingestion & Safety",
             ["Decoupled 1 Hz telemetry streaming over MQTT QoS 1 (port 1883).",
              "Sub-millisecond (< 5 ms) deterministic safety tripping adhering to ISO 10816-3 and IEC 60034-1.",
              "Compound multi-sensor physical anomaly evaluations."],
             "OBJECTIVE 1 & 2", PRIMARY)

    add_card(slide4, Inches(4.8), Inches(1.6), Inches(3.6), Inches(5.2),
             "Local RAG & Edge AI",
             ["In-process semantic vector indexing (all-MiniLM-L6-v2) on CPU (< 1 ms).",
              "Grounded LLM diagnosis using qwen2.5:1.5b running in Ollama (< 1.5 GB VRAM).",
              "Deterministic rule fallback for guaranteed zero-crash resilience."],
             "OBJECTIVE 3 & 4", ACCENT_GREEN)

    add_card(slide4, Inches(8.8), Inches(1.6), Inches(3.7), Inches(5.2),
             "Visualization & Twin",
             ["Grafana SCADA dashboard on port 3000 for operational time-series trends.",
              "React 18 + Vite interface on port 8000 with SVG Digital Twin motor animation.",
              "Printable HTML/PDF maintenance work orders with technician sign-off."],
             "OBJECTIVE 5 & 6", ACCENT_BLUE)

    # -------------------------------------------------------------
    # SLIDE 5: ARCHITECTURE
    # -------------------------------------------------------------
    slide5 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide5)
    add_header(slide5, "End-to-End System Architecture")

    add_card(slide5, Inches(0.8), Inches(1.6), Inches(2.7), Inches(5.2),
             "1. Producer",
             ["11 kW Motor Digital Twin Simulator",
              "CSV Replay Engine",
              "7-channel telemetry vector at 1 Hz",
              "MQTT QoS 1 / LWT"],
             "SIMULATOR", PRIMARY)

    add_card(slide5, Inches(3.8), Inches(1.6), Inches(2.7), Inches(5.2),
             "2. Ingestion & Broker",
             ["Mosquitto Broker (1883)",
              "FastAPI Consumer",
              "Pydantic Validation",
              "SSE Event Streamer"],
             "MQTT BROKER", ACCENT_GREEN)

    add_card(slide5, Inches(6.8), Inches(1.6), Inches(2.7), Inches(5.2),
             "3. Detection & AI",
             ["ISO 10816-3 Engine (< 5 ms)",
              "Local RAG Vector Store (CPU)",
              "Ollama qwen2.5:1.5b (GPU)",
              "Fallback Generator"],
             "CORE BRAIN", ACCENT_AMBER)

    add_card(slide5, Inches(9.8), Inches(1.6), Inches(2.7), Inches(5.2),
             "4. Storage & UI",
             ["PostgreSQL 16 (5433)",
              "SQLite 3 Fallback",
              "Grafana SCADA (3000)",
              "React Digital Twin (8000)"],
             "DUAL UI & DB", ACCENT_BLUE)

    # -------------------------------------------------------------
    # SLIDE 6: TECHNOLOGY STACK
    # -------------------------------------------------------------
    slide6 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide6)
    add_header(slide6, "Technology Stack Justification")

    add_card(slide6, Inches(0.8), Inches(1.6), Inches(5.6), Inches(2.5),
             "Backend & Messaging",
             ["FastAPI (Python 3.13): Asynchronous async/await event loop with high-speed Pydantic validation.",
              "Eclipse Mosquitto (port 1883): Lightweight C MQTT broker (2-byte header, QoS 1, LWT disconnect).",
              "PostgreSQL 16 (Docker port 5433): Async connection pool (asyncpg) with native JSONB indexing."],
             "PIPELINE", PRIMARY)

    add_card(slide6, Inches(6.8), Inches(1.6), Inches(5.7), Inches(2.5),
             "Intelligence & Vector Search",
             ["all-MiniLM-L6-v2 (SentenceTransformers): 384-dimensional dense vectors on CPU in 0.62 ms.",
              "Ollama + qwen2.5:1.5b: 4-bit quantized model consuming only ~1.35 GB VRAM with enforced JSON mode.",
              "Zero Cloud Dependency: 100% offline air-gapped operation with zero subscription fees."],
             "LOCAL AI", ACCENT_GREEN)

    add_card(slide6, Inches(0.8), Inches(4.3), Inches(5.6), Inches(2.5),
             "Presentation & Digital Twin",
             ["React 18 + Vite: Reactive frontend with Server-Sent Events (SSE) streaming at 1 Hz.",
              "Custom SVG Digital Twin: Real-time rotor RPM rotation and thermal color shift.",
              "Printable Work Order: Generates HTML/PDF industrial maintenance orders in 1 click."],
             "WEB DASHBOARD", ACCENT_BLUE)

    add_card(slide6, Inches(6.8), Inches(4.3), Inches(5.7), Inches(2.5),
             "Operational SCADA",
             ["Grafana OSS 11.2.0: Declarative provisioning with PostgreSQL data source on port 3000.",
              "ISO Limit Lines: Color-coded threshold boundaries for Zone C and Zone D limits.",
              "Anonymous Viewer Access: Instant presentation access without login friction."],
             "SCADA MONITOR", ACCENT_AMBER)

    # -------------------------------------------------------------
    # SLIDE 7: MQTT TELEMETRY PIPELINE
    # -------------------------------------------------------------
    slide7 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide7)
    add_header(slide7, "MQTT Telemetry Pipeline & Simulator")

    add_card(slide7, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
             "7 Physical Monitored Channels",
             ["1. Stator / Bearing Temperature: Nominal 45–65°C | Warning > 75°C | Trip > 95°C",
              "2. Vibration Velocity RMS: Nominal < 1.8 mm/s | ISO Zone C > 4.5 | Zone D > 7.1",
              "3. Stator Line Current: Nominal 8.8–9.0 A (FLA) | Warning > 11.5 A | Trip > 13.5 A",
              "4. Shaft Speed: Nominal 1485 RPM (1.0% slip) | Overload slip < 1450 RPM",
              "5. Line Voltage: Nominal 230 V (Phase) / 400 V (Line-to-Line)",
              "6. Lubrication Pressure: Nominal 3.8–4.5 bar | Low warning < 3.0 bar | Trip < 2.0 bar",
              "7. Operational State: running, warning, critical, stopped"],
             "TELEMETRY CONTRACT", PRIMARY)

    add_card(slide7, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
             "MQTT Architecture & Digital Twin",
             ["Topic Pattern: p311/machine/<id>/telemetry (QoS 1)",
              "Last Will & Testament (LWT): Broker publishes offline state automatically if client drops.",
              "Remote Command RPC: Dashboard publishes to p311/machine/<id>/command to trigger faults.",
              "Continuous Differential Physics: Simulator models thermal inertia and load dynamics.",
              "Gaussian Noise: Emulates physical sensor noise on real industrial ADC transducers."],
             "PROTOCOL & PHYSICS", ACCENT_GREEN)

    # -------------------------------------------------------------
    # SLIDE 8: DETERMINISTIC FAULT DETECTION
    # -------------------------------------------------------------
    slide8 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide8)
    add_header(slide8, "Deterministic Fault Detection Methodology")

    add_card(slide8, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
             "Standardized Engineering Rules",
             ["ISO 10816-3 (Vibration Severity):",
              "  • Zone A/B: Good / Acceptable (< 2.8 mm/s)",
              "  • Zone C: Unrestricted Warning (> 4.5 mm/s)",
              "  • Zone D: Immediate Safety Trip (≥ 7.1 mm/s)",
              "IEC 60034-1 (Thermal Insulation):",
              "  • Class F Winding Warning: > 75.0°C",
              "  • Class F Winding Alarm: > 85.0°C",
              "  • Class F Immediate Trip: ≥ 95.0°C",
              "Full Load Ampere (FLA) Slip Limit:",
              "  • Current > 125% FLA (11.5 A) with RPM < 1450 RPM."],
             "INTERNATIONAL STANDARDS", ACCENT_AMBER)

    add_card(slide8, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
             "Compound Physical Classifications",
             ["1. Bearing Degradation: Vibration > 4.5 mm/s + Temperature > 75°C",
              "2. Motor Overload: Current > 11.5 A + RPM < 1450 RPM",
              "3. Motor Overheating: Temperature > 85°C with nominal vibration",
              "4. Excessive Vibration: Vibration > 4.5 mm/s without thermal buildup",
              "5. Low Pressure: Lubrication pressure < 3.0 bar",
              "6. Sensor Physical Anomaly: Temperature out of physical bounds",
              "Execution Latency: Measured at 0.84 ms (well within < 5 ms budget).",
              "Debounced State Machine: Prevents duplicate alert storms."],
             "SUB-MS EXECUTION", ACCENT_GREEN)

    # -------------------------------------------------------------
    # SLIDE 9: RAG & SEMANTIC SEARCH
    # -------------------------------------------------------------
    slide9 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide9)
    add_header(slide9, "Local RAG Pipeline & Semantic Search")

    add_card(slide9, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
             "Curated Technical Corpus",
             ["7 Specialist Manuals in knowledge_base/:",
              "  • bearing_troubleshooting_guide.md",
              "  • motor_maintenance_manual.md",
              "  • vibration_diagnostics_guide.md",
              "  • electrical_overload_guide.md",
              "  • motor_overheating_guide.md",
              "  • pressure_system_troubleshooting.md",
              "  • preventive_maintenance_checklist.md",
              "34 Semantic Document Chunks extracted by H2 section with metadata retention."],
             "KNOWLEDGE BASE", PRIMARY)

    add_card(slide9, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
             "Retrieval Performance & Metrics",
             ["Embedding Model: all-MiniLM-L6-v2 running on CPU (~80 MB RAM).",
              "Vector Geometry: 384-dimensional unit vectors.",
              "Cosine Similarity Search: Matrix dot product in 0.62 ms.",
              "Empirical Benchmark Evaluation:",
              "  • Mean Reciprocal Rank (MRR): 1.000",
              "  • Hit Rate @ 1: 100.0%",
              "  • Hit Rate @ 3: 100.0%",
              "  • Average Top-1 Cosine Similarity: 0.6499",
              "Zero Factual Hallucinations: Grounded directly in manuals."],
             "BENCHMARK RESULTS", ACCENT_GREEN)

    # -------------------------------------------------------------
    # SLIDE 10: LOCAL LLM & FALLBACK
    # -------------------------------------------------------------
    slide10 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide10)
    add_header(slide10, "Local LLM Reasoning & Fallback Resilience")

    add_card(slide10, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
             "Quantized Local LLM (qwen2.5:1.5b)",
             ["Hosted locally via Ollama daemon on port 11434.",
              "VRAM Footprint: ~1.35 GB on NVIDIA RTX 2050 (4 GB budget).",
              "Inference Speed: ~30-50 tokens/sec (Avg latency 2.18s).",
              "Enforced JSON Mode: Outputs strict schema with:",
              "  • Likely Root Causes",
              "  • Mandatory Safety & Lockout/Tagout (LOTO)",
              "  • Diagnostic Checklist for Electricians",
              "  • Corrective Repair Actions",
              "  • Verified Manual Citations with Similarity Scores."],
             "EDGE INFERENCE", ACCENT_BLUE)

    add_card(slide10, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
             "Deterministic Zero-Crash Fallback",
             ["Industrial systems must NEVER crash when AI components fail.",
              "Automatic Standby Activation:",
              "  • Triggers if Ollama is offline, unreachable, or times out (> 45s).",
              "  • Pre-compiled rule templates combine sensor evidence with direct manual quotes.",
              "  • Generates complete work order in < 2 ms.",
              "  • Sets is_fallback: True for complete audit transparency.",
              "Guarantees 100% operational uptime."],
             "RESILIENCE PATTERN", ACCENT_AMBER)

    # -------------------------------------------------------------
    # SLIDE 11: DASHBOARD & WORK ORDER
    # -------------------------------------------------------------
    slide11 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide11)
    add_header(slide11, "Dashboard & Maintenance Work Order Generator")

    add_card(slide11, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
             "React 18 + Vite Engineering UI",
             ["Real-Time 1 Hz SSE Telemetry Cards with 50-sample rolling sparklines.",
              "SVG Digital Twin Motor: Dynamic rotor speed rotation and stator heat glow.",
              "Industrial Audio Alarm: Web Audio API sound with mute toggle.",
              "One-Click Fault Injection: Inject bearing, thermal, overload, or vibration faults.",
              "Interactive Viva AI Tutor: Real-time chat grounded in RAG manuals."],
             "PORT 8000 INTERFACE", PRIMARY)

    add_card(slide11, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
             "Industrial Maintenance Work Order",
             ["One-Click Printable Work Order (Endpoint: /api/reports/work-order).",
              "Captures exact physical sensor values at alarm timestamp.",
              "Mandatory Lockout/Tagout (LOTO) 400V breaker safety warnings.",
              "Checkboxes for mechanical inspection and grease replenishment.",
              "Technician and Lead Reliability Engineer signature blocks.",
              "Fully formatted for physical or PDF archiving."],
             "ACTIONABLE OUTPUT", ACCENT_GREEN)

    # -------------------------------------------------------------
    # SLIDE 12: TESTING & RESULTS
    # -------------------------------------------------------------
    slide12 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide12)
    add_header(slide12, "Verification Suite & Empirical Results")

    add_card(slide12, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
             "Automated Pytest Suite (25 Tests)",
             ["100% Pass Rate (25/25 passed in 14.68 seconds).",
              "Validation Tests (VAL-01 to 04): Pydantic payload integrity.",
              "Rule Detection Tests (DET-01 to 06): ISO thresholds & compound faults.",
              "RAG Pipeline Tests (RAG-01 to 03): Chunking & cosine similarity.",
              "Diagnosis & Fallback (LLM-01 to 02): LLM and zero-crash fallback.",
              "Database Persistence (DB-01 to 03): Retention purging & JSONB.",
              "REST & MQTT (API-01 to 06, MQTT-01): End-to-end pub-sub."],
             "AUTOMATED TESTING", ACCENT_GREEN)

    add_card(slide12, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
             "4,000-Sample Benchmark Evaluation",
             ["Overall Classification Accuracy: 99.38% (3,975 / 4,000 correct).",
              "Macro Precision: 0.9902 | Macro Recall: 0.9961",
              "Macro F1-Score: 0.9931 | Weighted F1: 0.9938",
              "Per-Class Performance:",
              "  • Bearing Degradation: F1 = 0.9950",
              "  • Motor Overload: F1 = 0.9988",
              "  • Motor Overheating: F1 = 0.9900",
              "  • Excessive Vibration: F1 = 0.9950",
              "Latency: Rule check 0.84 ms | RAG search 0.62 ms | LLM 2.18 s."],
             "EMPIRICAL METRICS", PRIMARY)

    # -------------------------------------------------------------
    # SLIDE 13: HARDWARE & BOM
    # -------------------------------------------------------------
    slide13 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide13)
    add_header(slide13, "Hardware Footprint & Bill of Materials")

    add_card(slide13, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
             "Workstation Resource Utilization",
             ["Host: Intel i5-12450H (12th Gen), 16 GB RAM, RTX 2050 (4 GB VRAM).",
              "System RAM Footprint: < 1.2 GB total for entire stack:",
              "  • PostgreSQL Container: ~66 MB",
              "  • Grafana Container: ~49 MB",
              "  • FastAPI Backend + Simulator: ~150 MB",
              "  • Ollama Daemon: ~300 MB",
              "GPU VRAM Footprint: ~1.35 GB (< 35% of 4 GB budget).",
              "Actual Cost: ₹0 / $0 (Open-source on student hardware)."],
             "ACTUAL SYSTEM", PRIMARY)

    add_card(slide13, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
             "Prospective Physical Deployment BOM",
             ["Honest Disclosure: Tested via high-fidelity digital twin simulator.",
              "Prospective Benchtop Prototype (~₹6,250 / ~$75):",
              "  • ESP32-S3 IoT MCU (Dual-core, Wi-Fi): ₹750",
              "  • ADXL345 3-Axis Accelerometer (Vibration): ₹450",
              "  • Pt100 RTD with MAX31865 (Stator Temp): ₹650",
              "  • SCT-013 Split-Core Current Clamp: ₹550",
              "  • ZMPT101B Voltage Transformer Module: ₹320",
              "  • Piezoresistive Pressure Transducer: ₹1,200",
              "  • 5V DIN Power Supply & Enclosure: ₹2,250."],
             "PROSPECTIVE BOM", ACCENT_AMBER)

    # -------------------------------------------------------------
    # SLIDE 14: LIMITATIONS & FUTURE SCOPE
    # -------------------------------------------------------------
    slide14 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide14)
    add_header(slide14, "Limitations & Future Research Directions")

    add_card(slide14, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2),
             "Current Project Limitations",
             ["1. Software Digital Twin Validation: High-voltage physical motors were not physically damaged in the lab due to safety and cost constraints.",
              "2. Single-Asset Focus: Primary demonstration configured for MOTOR-001 (extensible to multi-machine fleets via database schema).",
              "3. English Technical Corpus: Manuals and generated work orders are currently formatted in English."],
             "LIMITATIONS", ACCENT_AMBER)

    add_card(slide14, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2),
             "Future Engineering Scope",
             ["1. Physical Microcontroller Port: Deploy data acquisition firmware to ESP32-S3 and Raspberry Pi CM4 industrial gateways.",
              "2. Motor Current Signature Analysis (MCSA): Implement Fast Fourier Transforms (FFT) on stator current to detect broken rotor bars.",
              "3. Multi-Asset Fleet SCADA: Extend Grafana dashboards to monitor enterprise plant floors with hundreds of motors.",
              "4. Multilingual LLM Output: Generate work orders in regional languages for factory shop-floor electricians."],
             "FUTURE WORK", ACCENT_GREEN)

    # -------------------------------------------------------------
    # SLIDE 15: CONCLUSION & Q&A
    # -------------------------------------------------------------
    slide15 = prs.slides.add_slide(prs.slide_layouts[6])
    add_slide_background(slide15)

    t_box15 = slide15.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(4.5))
    tf15 = t_box15.text_frame
    tf15.word_wrap = True

    p0 = tf15.paragraphs[0]
    p0.text = "CONCLUSION & SUMMARY"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = PRIMARY
    p0.space_after = Pt(14)

    p1 = tf15.add_paragraph()
    p1.text = "P_311: A Complete, Explainable Industrial IoT Solution"
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_LIGHT
    p1.space_after = Pt(16)

    p2 = tf15.add_paragraph()
    p2.text = "• Solved the Explainability Gap: Moves beyond raw threshold beeps to structured, standards-grounded maintenance work orders.\n• Verified Performance: 99.38% classification accuracy, 1.000 MRR retrieval, and sub-millisecond (0.84 ms) ISO detection.\n• Edge-Native & Private: 100% offline local execution with zero cloud subscription fees and zero data leakage.\n• Guaranteed Reliability: Strict separation of safety concerns coupled with a zero-crash deterministic fallback engine."
    p2.font.size = Pt(14)
    p2.font.color.rgb = ACCENT_BLUE
    p2.space_after = Pt(24)

    p3 = tf15.add_paragraph()
    p3.text = "Thank You!\nWe are open to questions from the honorable examination committee."
    p3.font.size = Pt(18)
    p3.font.bold = True
    p3.font.color.rgb = ACCENT_GREEN

    # Save
    out_path = Path("docs/submission/PRESENTATION.pptx")
    prs.save(out_path)
    print(f"Presentation deck successfully generated at: {out_path} ({out_path.stat().st_size} bytes)")

if __name__ == "__main__":
    create_deck()
