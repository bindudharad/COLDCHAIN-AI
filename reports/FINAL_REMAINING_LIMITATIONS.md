# Remaining Real-World Hardware & Data Dependencies

**Date:** 2026-10-15  
**Project:** COLDCHAIN-AI  
**Scope:** Transparent disclosure of external hardware, data, and engineering prerequisites necessary prior to real-world deployment.

---

## 1. Physical Actuation & Compressor Control Boundary

> [!CAUTION]
> **SAFETY CUTOFF REQUIREMENT:**  
> The setpoints output by NSGA-II are **advisory decision-support targets**. Under no circumstances should software outputs be connected directly to high-voltage compressor contactors, VFDs, or motor starters without hardwired, certified electro-mechanical safety thermostats and thermal overload relays.

### Equipment Required for Physical Actuation
1. **Certified Industrial PLC / Microcontroller:**
   - E.g., Siemens S7-1200, Schneider Modicon, or industrial ESP32/ARM Cortex with isolated 4–20 mA or 0–10 V analog outputs.
2. **Variable Frequency Drive (VFD):**
   - For continuous cooling valve/inverter modulation ($u \in [0.1, 1.0]$).
3. **Hardwired High/Low Thermal Safety Interlocks:**
   - Independent safety circuit that forcibly de-energizes the compressor if temperature drops below $-1.0\text{ }^\circ\text{C}$ or exceeds $+8.0\text{ }^\circ\text{C}$, completely bypassing software logic.

---

## 2. Power & Energy Measurement Instrumentation

All energy metrics in the current platform are **`ESTIMATED / SIMULATED`**. To transition to **`MEASURED`** energy:
1. **Three-Phase Digital Power Transducers:**
   - True RMS power transducers (e.g. Accuenergy Acuvim II, Schneider PM5000) measuring real-time kW, kVA, Power Factor, and cumulative kWh with $\pm 0.5\%$ accuracy.
2. **Current Transformers (CTs) & Potential Transformers (PTs):**
   - Sized for compressor motor full-load amperes (FLA).
3. **Telemetry Integration:**
   - Modbus RTU / Modbus TCP or MQTT bridge forwarding true electrical power readings to `POST /api/iot/telemetry/`.

---

## 3. Physical IoT Telemetry Nodes

While the ingestion API `POST /api/iot/telemetry/` is fully operational in software:
1. **Physical Sensor Nodes:**
   - Calibrated 4-wire PT100 RTDs or digital NIST-traceable temperature sensors placed in cold room core, air delivery, and return ducting.
2. **Firmware:**
   - Implementation of the documented firmware client (`docs/REAL_IOT_SETUP.md`) on an ESP32 or cellular gateway with non-volatile offline flash buffering.
3. **Environmental Sealing:**
   - IP67/NEMA 4X enclosures rated for condensing and freezing environments down to $-40\text{ }^\circ\text{C}$.

---

## 4. Cold-Storage Thermal Telemetry & Real-World Calibration

1. **Refrigerant Line Telemetry:**
   - Suction and liquid line pressure transducers to compute actual coefficient of performance ($COP = Q / W$).
2. **Air Infiltration Flow Meters:**
   - Door micro-switches or proximity sensors logging door opening duration (seconds).
3. **Product Simulators:**
   - Glycol-buffered temperature probes to measure core cargo temperature rather than rapid air fluctuations.
