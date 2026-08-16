# BalanceBot Center of Mass Analysis

*Created: 12.04.2026 19:30:56*  
*Script: /home/phlix/workspaces/NewBalanceBot_planung/CAD_BalanceBot/CoM_analysis.py*

| Part | Vol [mm3] | Mass [g] | CoM X [mm] | CoM Y [mm] | CoM Z [mm] |
|------|-----------|----------|------------|------------|------------|
| botframe | 13592.7 | 14.14 | 0.00 | -0.78 | -5.17 |
| NANOMotorCarrier | 11434.0 | 21.15 | -0.22 | -4.38 | 4.58 |
| Arduino_Nano33IoT | 1530.2 | 2.83 | -0.02 | -0.50 | 12.89 |
| Battery_18650 | 8205.3 | 22.15 | -0.00 | 0.01 | -9.46 |
| motorhalter_R | 1187.7 | 1.24 | 30.00 | 3.79 | -15.00 |
| motorhalter_L | 1187.7 | 1.24 | -30.00 | 3.79 | -15.00 |
| N20_motor_R | 2838.3 | 12.77 | 29.56 | -0.58 | -13.82 |
| N20_motor_L | 2838.3 | 12.77 | -30.56 | -0.42 | -13.82 |
| Wheel_R_Hub | 10683.0 | 11.11 | 52.90 | -0.60 | -14.70 |
| Wheel_R_Tire | 19596.6 | 22.54 | 52.90 | -0.60 | -14.70 |
| Wheel_L_Hub | 10683.0 | 11.11 | -53.90 | -0.40 | -14.70 |
| Wheel_L_Tire | 19596.6 | 22.54 | -53.90 | -0.40 | -14.70 |
| CoM_Marker | 57.7 | 0.00 | -0.33 | -0.91 | -9.82 |
| **TOTAL** | **103431.3** | **155.58** | | | |

## Summary

| Metric | X [mm] | Y [mm] | Z [mm] |
|--------|--------|--------|--------|
| CoM (volume-weighted) | -0.35 | -0.83 | -10.45 |
| CoM (mass-weighted) | -0.33 | -0.91 | -9.82 |

- Wheel axle Z = -14.7 mm
- CoM height above axle: **4.88 mm** (mass-weighted)
- CoM Y offset from axle: **-0.91 mm** (positive = forward)

The coordinate origin is below the botframe base plate. Check the CAD-Assembly-File in FreeCAD to verify

For balancing: the CoM should be ABOVE the wheel axle (high Z) and centered on the axle in Y.

> CoM is **ABOVE** the axle (inverted pendulum, balanceable)
