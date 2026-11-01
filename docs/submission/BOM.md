# Bill of Materials (BOM) & Hardware Specifications
## Project P_311: Knowledge-Driven IoT Fault Diagnosis Assistant

---

## 1. Academic Hardware Disclosure & Scope Notice

> **IMPORTANT ACADEMIC INTEGRITY NOTICE**:  
> Project P_311 is implemented, tested, and validated as a **high-fidelity edge software digital twin system**. In accordance with university engineering ethics, **no physical high-voltage rotating motor hardware, industrial sensors, or microcontrollers were purchased, physically wired, or physically destroyed** during the execution of this project.  
> 
> All physical state dynamics (thermal curves, vibration velocity harmonics, rotor slip, load transients, and Gaussian sensor noise) were mathematically modeled and simulated in real-time by the validated industrial motor telemetry simulator (`simulator/motor_simulator.py`).
> 
> This document is divided into two transparent sections:
> 1. **Section A**: Computing hardware and environment **actually used** to develop, execute, and evaluate the software system.
> 2. **Section B**: The complete prospective engineering **Bill of Materials (BOM)** required to deploy this architecture to a physical industrial motor in a factory setting.

---

## Section A: Hardware & Computing Environment Actually Used

The entire application stack—including the 11 kW motor digital twin simulator, MQTT broker, FastAPI application server, PostgreSQL 16 database, Grafana SCADA engine, local SentenceTransformers RAG vector store, and local 1.5B parameter Ollama LLM—runs self-contained on the following host workstation hardware:

| Component Category | Actual Hardware Specification | Operational Role in Project | Resource Utilization |
| :--- | :--- | :--- | :--- |
| **Host Workstation** | Consumer Engineering Laptop | Development, testing, evaluation, and demonstration host. | System Chassis |
| **Processor (CPU)** | Intel® Core™ i5-12450H (12th Gen)<br/>8 Cores (4P + 4E), 12 Threads, up to 4.40 GHz | Runs FastAPI server, MQTT broker, database transactions, and SentenceTransformers RAG vector search. | ~8% CPU load during 1 Hz continuous telemetry streaming |
| **System Memory (RAM)** | 16 GB DDR4 (3200 MHz) | Shared memory pool for operating system, Docker containers, and Python run-time. | Total application stack consumes $< 1.2\text{ GB}$ RAM |
| **Dedicated GPU** | NVIDIA® GeForce RTX™ 2050 Laptop GPU<br/>4 GB GDDR6 VRAM | Hardware acceleration for local Ollama LLM inference (`qwen2.5:1.5b-instruct` Q4_K_M). | Consumes ~1.35 GB VRAM ($< 35\%$ of 4 GB budget) |
| **Storage (SSD)** | 512 GB PCIe Gen 4 NVMe M.2 SSD | Hosts Linux operating system, Docker volumes, RAG vector index, and SQLite/PostgreSQL data. | Project workspace requires $< 4\text{ GB}$ total disk space |
| **Operating System** | Debian GNU/Linux 13 (Trixie / x86_64) | Enterprise Linux environment with KDE Plasma desktop and PipeWire audio. | Base host environment |
| **Virtual Networking** | Localhost Loopback & Docker Bridge (`172.x`) | Local communication across ports `1883` (MQTT), `5433` (Postgres), `3000` (Grafana), `8000` (FastAPI), `11434` (Ollama). | Zero external network transmission |

---

## Section B: Prospective Hardware Bill of Materials (Physical Implementation)

The following engineering specification outlines the components, sensors, microcontrollers, and estimated industrial pricing required to transition Project P_311 from a software simulator to a physical physical electric motor monitoring setup in an industrial facility.

### 1. Target Physical Machinery Under Test
- **Machine Type**: 3-Phase Squirrel-Cage Induction Motor (Foot Mounted)
- **Rated Power**: 11 kW (15 HP), Class F Insulation, Continuous Duty (S1)
- **Rated Supply**: 400 V AC, 3-Phase, 50 Hz, Star/Delta Connected
- **Rated Speed**: 1485 RPM (4-Pole Synchronous Speed 1500 RPM, 1.0% Rated Slip)
- **Rated Full Load Amperes (FLA)**: 9.0 Amperes per phase

### 2. Physical Sensor Transducers & Signal Conditioning

| Component Ref | Subsystem | Sensor / Transducer Model | Technical Specifications | Purpose in Monitoring System | Est. Unit Cost (INR) | Est. Unit Cost (USD) |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| **SEN-01** | Vibration | **ADXL345 / MPU-6050** (Lab Test)<br/>*or* **Wilcoxon 786A** (Industrial) | Tri-axial MEMS accelerometer, I2C/SPI output, $\pm 16\text{ g}$ dynamic range, 3.2 kHz bandwidth. | Mounted on Drive-End (DE) bearing housing to detect ISO 10816-3 velocity RMS. | ₹450 / ₹18,000 | $6 / $220 |
| **SEN-02** | Stator Temp | **Pt100 RTD Sensor** (3-Wire Class A)<br/>with **MAX31865** RTD-to-Digital SPI | $-50^\circ\text{C}\text{ to }+200^\circ\text{C}$, $\pm 0.15^\circ\text{C}$ accuracy, platinum thin-film element. | Embedded into stator core slots to monitor IEC Class F thermal insulation limits. | ₹650 | $8 |
| **SEN-03** | Line Current | **SCT-013-000 Non-Invasive Current Transformer** (Split-Core) | Primary current: 0–100 A AC; secondary output: 0–50 mA; non-linearity $\pm 3\%$. | Clamped onto Line 1 (Phase A) conductor to detect electrical overload ($> 125\%$ FLA). | ₹550 | $7 |
| **SEN-04** | Line Voltage | **ZMPT101B Voltage Transformer Module** | AC voltage isolation transformer, active op-amp calibration, measures 0–250V AC RMS. | Measures single-phase / 3-phase line voltage to evaluate voltage unbalance. | ₹320 | $4 |
| **SEN-05** | Shaft Speed | **Hall Effect Sensor (NJK-5002C)** with neodymium shaft magnet | 3-wire NPN open collector, detection distance 10 mm, response frequency 320 Hz. | Counts shaft revolutions to compute operational RPM and detect rotor slip $> 6\%$. | ₹280 | $3.50 |
| **SEN-06** | Lubrication | **Piezoresistive Pressure Transducer (G1/4" Thread)** | Input: 5V DC; Output: 0.5V – 4.5V linear; Operating range: 0 – 1.2 MPa (0 – 12 bar). | Tapped into forced-oil lubrication manifold to detect oil starvation ($< 2.0\text{ bar}$). | ₹1,200 | $15 |

### 3. Edge Microcontroller & Data Acquisition Unit

| Component Ref | Component Type | Hardware Model | Technical Specifications | Role in Physical Architecture | Est. Unit Cost (INR) | Est. Unit Cost (USD) |
| :---: | :--- | :--- | :--- | :--- | :---: | :---: |
| **MCU-01** | Edge IoT Node | **ESP32-S3-WROOM-1** (Dual-Core Xtensa LX7) | 240 MHz clock, 512 KB SRAM, 8 MB Flash, 2.4 GHz Wi-Fi + BLE 5.0, hardware SPI/I2C/ADC. | Samples sensor ADC channels at 10 Hz, averages to 1 Hz, packages JSON, and publishes MQTT over Wi-Fi. | ₹750 | $9 |
| **MCU-02** | Industrial Alternative | **Raspberry Pi Compute Module 4 (CM4)** | Quad-core Cortex-A72, 4 GB RAM, Gigabit Ethernet, onboard eMMC. | Acts as standalone on-machine edge gateway running Mosquitto, FastAPI, and local RAG. | ₹6,500 | $80 |
| **PWR-01** | Power Supply | **Mean Well RS-15-5** | 100–240V AC input, 5V DC / 3A output, industrial DIN-rail mountable, short-circuit protection. | Regulates clean 5V DC power for ESP32 and sensor modules from plant auxiliary power. | ₹850 | $10 |
| **ENC-01** | Enclosure | **IP65 Fibreglass Electrical Enclosure** | Dimensions: $200\times 150\times 100\text{ mm}$, transparent hinged door, cable gland cutouts. | Protects MCU, power supply, and terminal blocks against factory oil mist, dust, and moisture. | ₹1,400 | $17 |
| **CAB-01** | Cabling & HW | **Shielded Twisted Pair (STP) + Glands** | 4-core twisted pair with braided shield, M12 aviation connectors, DIN terminal blocks. | Prevents EMI from high-voltage motor inverter cables from corrupting sensor signals. | ₹800 | $10 |

### 4. Summary Cost Comparison

| Implementation Category | Key Assets Included | Total Estimated Cost (INR) | Total Estimated Cost (USD) |
| :--- | :--- | :---: | :---: |
| **Current Software Digital Twin Implementation** | Existing student laptop, open-source software stack, zero physical sensor hardware. | **₹0.00** *(Leveraged existing workstation)* | **$0.00** |
| **Prospective Laboratory Prototype (Bench Scale)** | ESP32-S3, ADXL345, Pt100, SCT-013, ZMPT101B, Hall sensor, 5V power supply, wiring. | **₹6,250** | **~$75** |
| **Prospective Industrial Production Setup** | IP65 enclosure, industrial Wilcoxon accelerometer, DIN power, shielded cabling, Raspberry Pi CM4 gateway. | **₹32,500** | **~$390** |
