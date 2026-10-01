# Motor Thermal & Overheating Troubleshooting Guide
*DEMONSTRATION MATERIAL - Fictional Technical Reference for P_311*

## 1. Thermal Limits & Symptoms
- Nominal Stator Temperature: 45°C - 65°C under nominal 40°C ambient conditions.
- Class F Insulation Limit: Maximum allowable hot-spot temperature is 155°C (continuous design rating: 105°C).
- Warning Threshold: Surface temperature exceeding 85°C.
- Critical Trip Threshold: Surface temperature exceeding 95°C - 105°C.
- Symptoms: Stator thermal alarm trip, thermal dissipation burning odor, discolored exterior enamel paint.

## 2. Plausible Causes
- Blocked Cooling Passages: Dust, fibrous lint, or chemical encrustation choking the external cooling fins and cowl.
- Cooling Fan Failure: Damaged, loose, or missing external cooling fan impeller on the non-drive shaft end.
- High Ambient Temperature: Inadequate machine room HVAC ventilation (ambient > 40°C).
- Prolonged Low-Speed Operation: VFD operation at low frequencies (< 25 Hz) without external forced cooling blower.
- Phase Voltage Imbalance: 2% voltage unbalance induces up to 15% winding temperature rise.

## 3. Diagnostic Procedures
1. Inspect air intake grille and external cooling fins for clogging; measure ambient temperature.
2. Inspect mechanical integrity of cooling fan blades and keyway attachment.
3. Check 3-phase supply line voltages with a True-RMS digital multimeter to calculate voltage unbalance:
   `Unbalance % = (Max Deviation from Average / Average) * 100` (must be < 1.0%).
4. Verify heat exchanger / cooling medium flow rate and thermal delta across the motor jacket.

## 4. Recommended Corrective Actions
- Immediate: Reduce motor mechanical load or halt machine if stator thermistor exceeds 100°C.
- Cleaning: Use compressed air (< 2 bar) or dry ice blasting to thoroughly clean stator cooling fins.
- Mechanical: Replace cracked cooling fan cowl or broken fan hub.
- Electrical: Inspect upstream contactor contacts for carbon pitting causing voltage drop on one phase.
