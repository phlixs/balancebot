// ============================================================
// test_safety -- Host-Tests fuer den SafetySupervisor
// Ausfuehren: pio test -e native
// ============================================================

#include <unity.h>
#include "balance/safety.h"

// Testparameter: 45 Grad Sturz, 50 Stale-Zyklen, 50 ms Overrun,
// MAX_DUTY 45, 1000 ms Saettigungs-Timeout
static SafetySupervisor makeSupervisor() {
    return SafetySupervisor(45.0f, 50, 50, 45, 1000);
}

void setUp() {}
void tearDown() {}

void test_normal_cycle_is_ok() {
    SafetySupervisor s = makeSupervisor();
    s.reset();
    TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                      (int)s.check(2.0f, 5.0f, 10, 20, 1000));
}

void test_tilt_triggers_fallen() {
    SafetySupervisor s = makeSupervisor();
    s.reset();
    TEST_ASSERT_EQUAL((int)SafetyVerdict::FALLEN_TILT,
                      (int)s.check(50.0f, 0.0f, 10, 0, 1000));
    TEST_ASSERT_EQUAL((int)SafetyVerdict::FALLEN_TILT,
                      (int)s.check(-50.0f, 0.0f, 10, 0, 1010));
}

void test_loop_overrun_triggers_estop() {
    SafetySupervisor s = makeSupervisor();
    s.reset();
    TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                      (int)s.check(1.0f, 1.0f, 50, 0, 1000)); // exakt Grenze: ok
    TEST_ASSERT_EQUAL((int)SafetyVerdict::ESTOP_LOOP_OVERRUN,
                      (int)s.check(1.0f, 1.1f, 51, 0, 1010));
}

void test_imu_stale_triggers_estop_after_limit() {
    SafetySupervisor s = makeSupervisor();
    s.reset();
    // Erster Zyklus mit echten Werten zaehlt nie als stale
    TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                      (int)s.check(3.0f, 1.0f, 10, 0, 1000));
    // 48 weitere identische Zyklen: noch OK (Zaehler 1..48 < 50)
    for (int i = 0; i < 48; i++) {
        TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                          (int)s.check(3.0f, 1.0f, 10, 0, 1010 + i * 10));
    }
    // 49. und 50. identischer Zyklus: Limit erreicht
    TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                      (int)s.check(3.0f, 1.0f, 10, 0, 2000));
    TEST_ASSERT_EQUAL((int)SafetyVerdict::ESTOP_IMU_STALE,
                      (int)s.check(3.0f, 1.0f, 10, 0, 2010));
}

void test_imu_value_change_resets_stale_counter() {
    SafetySupervisor s = makeSupervisor();
    s.reset();
    s.check(3.0f, 1.0f, 10, 0, 1000);
    for (int i = 0; i < 40; i++) {
        s.check(3.0f, 1.0f, 10, 0, 1010 + i * 10);
    }
    // Ein einziger veraenderter Wert setzt den Zaehler zurueck
    TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                      (int)s.check(3.1f, 1.0f, 10, 0, 1500));
    for (int i = 0; i < 49; i++) {
        TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                          (int)s.check(3.1f, 1.0f, 10, 0, 1510 + i * 10));
    }
    TEST_ASSERT_EQUAL((int)SafetyVerdict::ESTOP_IMU_STALE,
                      (int)s.check(3.1f, 1.0f, 10, 0, 2100));
}

void test_saturation_triggers_fallen_after_timeout() {
    SafetySupervisor s = makeSupervisor();
    s.reset();
    // Duty am positiven Anschlag: Timer startet bei 1000
    TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                      (int)s.check(10.0f, 1.0f, 10, 45, 1000));
    TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                      (int)s.check(10.0f, 1.1f, 10, 45, 1990));
    TEST_ASSERT_EQUAL((int)SafetyVerdict::FALLEN_SATURATION,
                      (int)s.check(10.0f, 1.2f, 10, 45, 2000));
}

void test_saturation_negative_duty_also_counts() {
    SafetySupervisor s = makeSupervisor();
    s.reset();
    s.check(-10.0f, 1.0f, 10, -45, 1000);
    TEST_ASSERT_EQUAL((int)SafetyVerdict::FALLEN_SATURATION,
                      (int)s.check(-10.0f, 1.1f, 10, -45, 2000));
}

void test_saturation_resets_when_duty_recovers() {
    SafetySupervisor s = makeSupervisor();
    s.reset();
    s.check(10.0f, 1.0f, 10, 45, 1000);
    s.check(10.0f, 1.1f, 10, 30, 1500);   // unter Anschlag: Timer loescht
    TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                      (int)s.check(10.0f, 1.2f, 10, 45, 2400)); // neuer Timer ab 2400
    TEST_ASSERT_EQUAL((int)SafetyVerdict::FALLEN_SATURATION,
                      (int)s.check(10.0f, 1.3f, 10, 45, 3400));
}

void test_reset_clears_all_counters() {
    SafetySupervisor s = makeSupervisor();
    s.reset();
    s.check(3.0f, 1.0f, 10, 45, 1000);
    for (int i = 0; i < 45; i++) {
        s.check(3.0f, 1.0f, 10, 45, 1010 + i * 10);
    }
    s.reset(); // neuer BALANCING-Start
    // Gleiche Werte wie vorher: Stale-Zaehler und Saettigungs-Timer bei 0
    TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                      (int)s.check(3.0f, 1.0f, 10, 45, 2500));
    TEST_ASSERT_EQUAL((int)SafetyVerdict::OK,
                      (int)s.check(3.0f, 1.0f, 10, 45, 3400));
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_normal_cycle_is_ok);
    RUN_TEST(test_tilt_triggers_fallen);
    RUN_TEST(test_loop_overrun_triggers_estop);
    RUN_TEST(test_imu_stale_triggers_estop_after_limit);
    RUN_TEST(test_imu_value_change_resets_stale_counter);
    RUN_TEST(test_saturation_triggers_fallen_after_timeout);
    RUN_TEST(test_saturation_negative_duty_also_counts);
    RUN_TEST(test_saturation_resets_when_duty_recovers);
    RUN_TEST(test_reset_clears_all_counters);
    return UNITY_END();
}
