// ============================================================
// test_deadzone -- Host-Tests fuer die Totzonen-Kompensation
// Ausfuehren: pio test -e native
// ============================================================

#include <unity.h>
#include "balance/deadzone.h"

// Gemessene Anlaufpunkte 2026-08-07 bei 3.57 V
static const int DZ_POS = 23;
static const int DZ_NEG = 17;

void setUp() {}
void tearDown() {}

void test_zero_stays_zero() {
    TEST_ASSERT_EQUAL(0, compensateDeadzone(0, DZ_POS, DZ_NEG));
}

void test_small_positive_is_lifted_to_pos_onset() {
    TEST_ASSERT_EQUAL(23, compensateDeadzone(1, DZ_POS, DZ_NEG));
    TEST_ASSERT_EQUAL(23, compensateDeadzone(12, DZ_POS, DZ_NEG));
    TEST_ASSERT_EQUAL(23, compensateDeadzone(22, DZ_POS, DZ_NEG));
}

void test_small_negative_is_lifted_to_neg_onset() {
    TEST_ASSERT_EQUAL(-17, compensateDeadzone(-1, DZ_POS, DZ_NEG));
    TEST_ASSERT_EQUAL(-17, compensateDeadzone(-10, DZ_POS, DZ_NEG));
    TEST_ASSERT_EQUAL(-17, compensateDeadzone(-16, DZ_POS, DZ_NEG));
}

void test_at_onset_passes_through() {
    TEST_ASSERT_EQUAL(23, compensateDeadzone(23, DZ_POS, DZ_NEG));
    TEST_ASSERT_EQUAL(-17, compensateDeadzone(-17, DZ_POS, DZ_NEG));
}

void test_strong_commands_pass_through() {
    TEST_ASSERT_EQUAL(30, compensateDeadzone(30, DZ_POS, DZ_NEG));
    TEST_ASSERT_EQUAL(-30, compensateDeadzone(-30, DZ_POS, DZ_NEG));
    TEST_ASSERT_EQUAL(45, compensateDeadzone(45, DZ_POS, DZ_NEG));
    TEST_ASSERT_EQUAL(-45, compensateDeadzone(-45, DZ_POS, DZ_NEG));
}

void test_motor_pair_mapping_moves_both_wheels() {
    // Kern des Problems mit symmetrischer Schwelle: kleiner Vorwaerts-
    // Befehl u -> M1 bekommt +u (pos. Seite), M2 bekommt -u (neg. Seite).
    // Beide muessen NACH Kompensation ueber ihrem Anlaufpunkt liegen.
    int u = 5;
    int m1 = compensateDeadzone( u, DZ_POS, DZ_NEG);
    int m2 = compensateDeadzone(-u, DZ_POS, DZ_NEG);
    TEST_ASSERT_TRUE(m1 >= DZ_POS);    // M1 laeuft an
    TEST_ASSERT_TRUE(m2 <= -DZ_NEG);   // M2 laeuft an

    // Rueckwaerts spiegelbildlich
    m1 = compensateDeadzone(-u, DZ_POS, DZ_NEG);
    m2 = compensateDeadzone( u, DZ_POS, DZ_NEG);
    TEST_ASSERT_TRUE(m1 <= -DZ_NEG);
    TEST_ASSERT_TRUE(m2 >= DZ_POS);
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_zero_stays_zero);
    RUN_TEST(test_small_positive_is_lifted_to_pos_onset);
    RUN_TEST(test_small_negative_is_lifted_to_neg_onset);
    RUN_TEST(test_at_onset_passes_through);
    RUN_TEST(test_strong_commands_pass_through);
    RUN_TEST(test_motor_pair_mapping_moves_both_wheels);
    return UNITY_END();
}
