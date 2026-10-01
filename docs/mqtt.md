# MQTT Messaging Architecture & Protocol Specification

## 1. Why MQTT in Industrial IoT?
MQTT (Message Queuing Telemetry Transport) is a lightweight, binary-framed, publish-subscribe messaging protocol designed specifically for constrained devices and high-latency or low-bandwidth networks.

### Comparison: MQTT vs HTTP
| Characteristic | MQTT | HTTP / REST |
| :--- | :--- | :--- |
| **Architecture** | Publish / Subscribe via central Broker | Client / Server Request-Response |
| **Packet Overhead** | Fixed 2-byte header | 200–800 bytes per request (HTTP headers) |
| **Transport** | Persistent TCP connection | Typically ephemeral TCP connection |
| **Connection Decoupling** | Publishers & subscribers do not know each other | Client must know target server IP/port |
| **Bandwidth Usage** | Extremely low (ideal for 1 Hz sensor streams) | High overhead due to repeated HTTP headers |
| **Quality of Service (QoS)** | 0 (at most once), 1 (at least once), 2 (exactly once) | No native QoS; requires application layer |

## 2. Topic Hierarchy
```
p311/
└── machine/
    └── {machine_id}/
        ├── telemetry   (Publisher: Simulator | Subscriber: Backend)
        ├── status      (Publisher: Simulator | Subscriber: Backend, Dashboard)
        ├── fault       (Publisher: Backend Fault Detector)
        └── command     (Publisher: Backend API | Subscriber: Simulator)
```

## 3. Payloads & Schemas

### A. Telemetry (`p311/machine/MOTOR-001/telemetry`)
Emitted at 1.0 Hz:
```json
{
  "machine_id": "MOTOR-001",
  "timestamp": "2026-09-30T11:00:00.123Z",
  "temperature": 52.4,
  "vibration": 1.45,
  "current": 8.82,
  "rpm": 1485.2,
  "voltage": 230.1,
  "pressure": 4.18,
  "state": "running"
}
```

### B. Machine Status (`p311/machine/MOTOR-001/status`)
Emitted on state transitions with MQTT retain flag:
```json
{
  "machine_id": "MOTOR-001",
  "state": "running",
  "active_fault": null,
  "timestamp": "2026-09-30T11:00:00Z"
}
```

### C. Simulation Commands (`p311/machine/MOTOR-001/command`)
Emitted by REST API to control simulator remotely:
```json
{
  "command": "inject_fault",
  "fault_type": "bearing_degradation"
}
```
Or reset:
```json
{
  "command": "reset"
}
```

## 4. Resilience & Error Handling
- **Last Will and Testament (LWT)**: Simulator registers an LWT on `p311/machine/{id}/status` with payload `{"state": "offline", "reason": "abrupt_disconnect"}`.
- **Auto-Reconnect**: Both simulator and backend utilize `paho-mqtt` with auto-reconnection loops and backoff.
- **Pydantic Validation**: Backend rejects malformed or unphysical messages (e.g., negative Kelvin or 10,000V) before database ingestion.
