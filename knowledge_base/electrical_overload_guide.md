# Motor Electrical Overload & Overcurrent Guide
*DEMONSTRATION MATERIAL - Fictional Technical Reference for P_311*

## 1. Symptoms of Electrical Overload
- Motor Stator Current significantly exceeding Full Load Amps (FLA): e.g. drawing 13.0 A - 18.0 A against 9.0 A rated.
- Noticeable drop in shaft rotational speed (RPM drops below 1430 RPM due to elevated rotor slip).
- Accelerated winding temperature increase due to $I^2R$ copper losses.
- Audible heavy 50Hz/100Hz electromagnetic hum from stator laminations.
- Thermal overload relay or variable frequency drive (VFD) tripping on $I^2t$ inverse-time curve.

## 2. Plausible Causes
- Driven Machine Mechanical Binding: Jammed conveyor belt, locked pump impeller, gearbox gear tooth binding.
- Excessive Mechanical Process Load: Material feed rate exceeding processing capacity of the driven unit.
- Under-Voltage Condition: Supply voltage falling below 360V (motor draws higher current to maintain shaft power).
- Single-Phasing: Loss of one power phase causing the remaining two lines to pull $\sqrt{3} \approx 1.73 \times$ current.
- Rotor Bar Fractures: Cracked end-rings or broken cage bars reducing torque capability.

## 3. Diagnostic Procedures
1. Disconnect mechanical coupling between motor and load; spin load shaft manually to check for mechanical binding.
2. Measure 3-phase currents ($I_A, I_B, I_C$) with an AC clamp meter; verify current balance within 5%.
3. Verify 3-phase line-to-line voltages under load; confirm voltage is within $\pm 10\%$ of 400V nominal (360V - 440V).
4. Perform Motor Current Signature Analysis (MCSA) to identify sideband frequencies indicative of broken rotor bars.

## 4. Recommended Corrective Actions
- Immediate: Trip motor if current exceeds 150% FLA for longer than 10 seconds to prevent winding insulation burnout.
- Clearance: Clear mechanical blockage in the driven conveyor, pump, or extruder.
- Sizing: If process requirements have permanently increased, upgrade drive train to higher kW rating.
- Electrical: Inspect upstream circuit breakers, fuses, and thermal overload relay settings.
