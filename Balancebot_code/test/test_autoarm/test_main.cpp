// ============================================================
// test_autoarm -- Host-Tests fuer den Auto-Arm-Detektor
// Ausfuehren: pio test -e native
// ============================================================

#include <unity.h>
#include "balance/autoarm.h"

// Testparameter: 6 Grad / 20 Grad/s Fenster, 800 ms Stabilitaet
static const float         ANGLE  = 6.0f;
static const float         RATE   = 20.0f;
static const unsigned long STABLE = 800;

void setUp() {}
void tearDown() {}

void test_arms_after_stable_window() {
    AutoArm a(ANGLE, RATE, STABLE);
    TEST_ASSERT_FALSE(a.update(0.0f, 0.0f, 1000));  // Fenster startet
    TEST_ASSERT_FALSE(a.update(1.0f, 5.0f, 1500));  // 500 ms < 800 ms
    TEST_ASSERT_TRUE(a.update(-1.0f, -5.0f, 1800)); // 800 ms erreicht
}

void test_angle_violation_resets_window() {
    AutoArm a(ANGLE, RATE, STABLE);
    a.update(0.0f, 0.0f, 1000);
    a.update(10.0f, 0.0f, 1500);                    // Winkel zu gross -> Fenster verworfen
    TEST_ASSERT_FALSE(a.update(0.0f, 0.0f, 2200));  // neues Fenster startet HIER
    TEST_ASSERT_FALSE(a.update(0.0f, 0.0f, 2999));  // 799 ms
    TEST_ASSERT_TRUE(a.update(0.0f, 0.0f, 3000));   // 800 ms voll
}

void test_rate_violation_resets_window() {
    AutoArm a(ANGLE, RATE, STABLE);
    a.update(0.0f, 0.0f, 1000);
    a.update(0.0f, 50.0f, 1500);                    // Rate zu gross (wackelt)
    TEST_ASSERT_FALSE(a.update(0.0f, 0.0f, 2299));  // neues Fenster startet HIER
    TEST_ASSERT_FALSE(a.update(0.0f, 0.0f, 3098));  // 799 ms
    TEST_ASSERT_TRUE(a.update(0.0f, 0.0f, 3099));   // 800 ms voll
}

void test_boundary_is_exclusive() {
    AutoArm a(ANGLE, RATE, STABLE);
    // Exakt auf der Grenze zaehlt NICHT als "im Fenster"
    TEST_ASSERT_FALSE(a.update(6.0f, 0.0f, 1000));
    TEST_ASSERT_FALSE(a.update(6.0f, 0.0f, 5000));
    TEST_ASSERT_FALSE(a.update(0.0f, 20.0f, 9000));
}

void test_reset_clears_window() {
    AutoArm a(ANGLE, RATE, STABLE);
    a.update(0.0f, 0.0f, 1000);
    a.reset();                                       // z.B. Zustandswechsel
    TEST_ASSERT_FALSE(a.update(0.0f, 0.0f, 1900));   // altes Fenster weg
    TEST_ASSERT_TRUE(a.update(0.0f, 0.0f, 2700));
}

void test_stale_window_after_state_change_would_misfire() {
    // Regressionstest fuer den Grund von reset(): ohne Reset wuerde ein
    // altes Fenster nach langer Pause sofort ausloesen
    AutoArm a(ANGLE, RATE, STABLE);
    a.update(0.0f, 0.0f, 1000);   // Fenster ab 1000
    // ... Bot balanciert, faellt, liegt 10 s ...
    a.reset();
    TEST_ASSERT_FALSE(a.update(0.0f, 0.0f, 12000)); // darf NICHT sofort armen
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_arms_after_stable_window);
    RUN_TEST(test_angle_violation_resets_window);
    RUN_TEST(test_rate_violation_resets_window);
    RUN_TEST(test_boundary_is_exclusive);
    RUN_TEST(test_reset_clears_window);
    RUN_TEST(test_stale_window_after_state_change_would_misfire);
    return UNITY_END();
}
