// ============================================================
// test_pid -- Host-Tests fuer den PID-Regler
// Ausfuehren: pio test -e native
// ============================================================

#include <unity.h>
// Implementierung direkt einbinden (native Env kompiliert src/ nicht)
#include "balance/pid.cpp"

void setUp() {}
void tearDown() {}

void test_p_term_proportional() {
    Pid pid(2.0f, 0.0f, 0.0f);
    float out = pid.compute(10.0f, 0.01f);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 20.0f, out);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 20.0f, pid.pTerm());
}

void test_numeric_derivative_first_step_suppressed() {
    Pid pid(0.0f, 0.0f, 1.0f);
    // Erster Schritt: kein gueltiger prevError -> D = 0
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, pid.compute(5.0f, 0.01f));
    // Zweiter Schritt: (6-5)/0.01 = 100
    TEST_ASSERT_FLOAT_WITHIN(0.01f, 100.0f, pid.compute(6.0f, 0.01f));
}

void test_measured_rate_active_from_first_cycle() {
    Pid pid(0.0f, 0.0f, 0.5f);
    // Gemessene Rate wirkt SOFORT (kein firstStep-Loch) -- genau der
    // Vorteil der Gyro-Variante beim Arm-Moment
    float out = pid.compute(0.0f, 40.0f, 0.01f);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 20.0f, out);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 20.0f, pid.dTerm());
}

void test_measured_rate_matches_kd_times_rate() {
    Pid pid(1.0f, 0.0f, 0.1f);
    // error=2, rate=-30: out = 2*1 + 0.1*(-30) = -1
    float out = pid.compute(2.0f, -30.0f, 0.01f);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, -1.0f, out);
}

void test_output_clamped() {
    Pid pid(10.0f, 0.0f, 0.0f, 0.0f, 50.0f, -45.0f, 45.0f);
    TEST_ASSERT_FLOAT_WITHIN(0.001f,  45.0f, pid.compute( 100.0f, 0.01f));
    TEST_ASSERT_FLOAT_WITHIN(0.001f, -45.0f, pid.compute(-100.0f, 0.01f));
}

void test_integral_grows_and_is_bounded() {
    Pid pid(0.0f, 1.0f, 0.0f, 0.0f, 5.0f, -100.0f, 100.0f);
    // Konstanter Fehler 10 ueber viele Schritte: Integral waechst,
    // bleibt aber durch integralMax=5 begrenzt -> iTerm max 5
    float out = 0.0f;
    for (int i = 0; i < 200; i++) {
        out = pid.compute(10.0f, 0.01f);
    }
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 5.0f, out);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 5.0f, pid.iTerm());
}

void test_anti_windup_slows_integrator_in_saturation() {
    // Zwei identische Regler, einer mit Back-Calculation (kaw=1):
    // bei gesaettigtem Ausgang muss dessen Integrator kleiner bleiben
    Pid withAw(5.0f, 1.0f, 0.0f, 1.0f, 100.0f, -10.0f, 10.0f);
    Pid noAw  (5.0f, 1.0f, 0.0f, 0.0f, 100.0f, -10.0f, 10.0f);
    for (int i = 0; i < 100; i++) {
        withAw.compute(10.0f, 0.01f); // P=50 >> outputMax=10 -> saettigt
        noAw.compute(10.0f, 0.01f);
    }
    TEST_ASSERT_TRUE(withAw.iTerm() < noAw.iTerm());
}

void test_reset_clears_state() {
    Pid pid(1.0f, 1.0f, 1.0f);
    pid.compute(10.0f, 0.01f);
    pid.compute(20.0f, 0.01f);
    pid.reset();
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, pid.iTerm());
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, pid.dTerm());
    // Nach Reset: erster numerischer Schritt wieder ohne D-Spike
    float out = pid.compute(5.0f, 0.01f);
    TEST_ASSERT_FLOAT_WITHIN(0.1f, 5.05f, out); // P=5 + I=0.05 + D=0
}

void test_runtime_setters() {
    Pid pid(1.0f, 0.0f, 0.0f);
    pid.setKp(3.0f);
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 3.0f, pid.kp());
    TEST_ASSERT_FLOAT_WITHIN(0.001f, 30.0f, pid.compute(10.0f, 0.01f));
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_p_term_proportional);
    RUN_TEST(test_numeric_derivative_first_step_suppressed);
    RUN_TEST(test_measured_rate_active_from_first_cycle);
    RUN_TEST(test_measured_rate_matches_kd_times_rate);
    RUN_TEST(test_output_clamped);
    RUN_TEST(test_integral_grows_and_is_bounded);
    RUN_TEST(test_anti_windup_slows_integrator_in_saturation);
    RUN_TEST(test_reset_clears_state);
    RUN_TEST(test_runtime_setters);
    return UNITY_END();
}
