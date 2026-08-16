// ============================================================
// pid.cpp -- BalanceBot: PID-Implementierung
// ============================================================

#include "pid.h"

Pid::Pid(float kp, float ki, float kd, float kaw,
         float integralMax, float outputMin, float outputMax)
    : _kp(kp), _ki(ki), _kd(kd), _kaw(kaw),
      _integralMax(integralMax), _outputMin(outputMin), _outputMax(outputMax)
{}

float Pid::compute(float error, float dt) {
    // Schutz vor dt=0 oder Negativwerten (z.B. millis()-Ueberlauf)
    if (dt <= 0.0f) return 0.0f;

    // Fehler-Ableitung numerisch bilden.
    // Beim ersten Schritt keinen D-Anteil berechnen (kein gueltiger prevError)
    float errorRate;
    if (_firstStep) {
        errorRate  = 0.0f;
        _firstStep = false;
    } else {
        errorRate = (error - _prevError) / dt;
    }
    _prevError = error;

    return _computeWithRate(error, errorRate, dt);
}

float Pid::compute(float error, float errorRate, float dt) {
    // Variante mit extern gemessener Ableitung (z.B. Gyro-Rate, Phase C):
    // kein firstStep-Problem, die Messung ist ab dem ersten Zyklus gueltig
    if (dt <= 0.0f) return 0.0f;

    _prevError = error;
    _firstStep = false;

    return _computeWithRate(error, errorRate, dt);
}

float Pid::_computeWithRate(float error, float errorRate, float dt) {
    // --- P-Anteil ---
    _pTerm = _kp * error;

    // --- D-Anteil ---
    _dTerm = _kd * errorRate;

    // --- Ungesaettigter Ausgang ---
    // Integralanteil wird erst nach Anti-Windup-Update berechnet
    float outputUnclamped = _pTerm + (_ki * _integral) + _dTerm;

    // --- Ausgangsbegrenzung ---
    float outputClamped = outputUnclamped;
    if (outputClamped >  _outputMax) outputClamped =  _outputMax;
    if (outputClamped < _outputMin)  outputClamped =  _outputMin;

    // --- Anti-Windup: Back-Calculation ---
    // e_aw = Differenz zwischen gesaettigtem und ungesaettigtem Ausgang
    // Bei Saettigung: e_aw != 0 --> bremst Integrator ab
    // Bei normaler Operation: e_aw = 0 --> kein Einfluss
    float e_aw = outputClamped - outputUnclamped;

    // --- I-Anteil: Integrator-Update ---
    // Normales Integral + Anti-Windup-Rueckkopplung
    _integral += (error * dt) + (_kaw * e_aw * dt);

    // Sekundaere Begrenzung des Integratorspeichers (Fallback)
    if (_integral >  _integralMax) _integral =  _integralMax;
    if (_integral < -_integralMax) _integral = -_integralMax;

    // I-Term fuer Logging
    _iTerm = _ki * _integral;

    return outputClamped;
}

void Pid::reset() {
    // Zustand vollstaendig zuruecksetzen
    // Muss vor jedem neuen Balancierversuch aufgerufen werden
    _integral  = 0.0f;
    _prevError = 0.0f;
    _firstStep = true;
    _pTerm     = 0.0f;
    _iTerm     = 0.0f;
    _dTerm     = 0.0f;
}
