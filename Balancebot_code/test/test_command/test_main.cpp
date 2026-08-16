// ============================================================
// test_command -- Host-Tests fuer den Tuning-Befehls-Parser
// Ausfuehren: pio test -e native
// ============================================================

#include <unity.h>
#include "balance/command.h"

void setUp() {}
void tearDown() {}

void test_parses_all_keys() {
    TEST_ASSERT_EQUAL((int)TuneKey::KP, (int)parseTuneCommand("Kp=3.5").key);
    TEST_ASSERT_EQUAL((int)TuneKey::KI, (int)parseTuneCommand("Ki=0.1").key);
    TEST_ASSERT_EQUAL((int)TuneKey::KD, (int)parseTuneCommand("Kd=0.25").key);
    TEST_ASSERT_EQUAL((int)TuneKey::SP, (int)parseTuneCommand("Sp=-1.5").key);
}

void test_parses_values() {
    TEST_ASSERT_FLOAT_WITHIN(0.0001f, 3.5f,  parseTuneCommand("Kp=3.5").value);
    TEST_ASSERT_FLOAT_WITHIN(0.0001f, -1.5f, parseTuneCommand("Sp=-1.5").value);
    TEST_ASSERT_FLOAT_WITHIN(0.0001f, 0.0f,  parseTuneCommand("Ki=0").value);
}

void test_trailing_whitespace_and_cr_ok() {
    TuneCommand tc = parseTuneCommand("Kd=0.2 \r");
    TEST_ASSERT_EQUAL((int)TuneKey::KD, (int)tc.key);
    TEST_ASSERT_FLOAT_WITHIN(0.0001f, 0.2f, tc.value);
}

void test_rejects_garbage() {
    TEST_ASSERT_EQUAL((int)TuneKey::NONE, (int)parseTuneCommand("").key);
    TEST_ASSERT_EQUAL((int)TuneKey::NONE, (int)parseTuneCommand("Kp").key);
    TEST_ASSERT_EQUAL((int)TuneKey::NONE, (int)parseTuneCommand("Kp=").key);
    TEST_ASSERT_EQUAL((int)TuneKey::NONE, (int)parseTuneCommand("Kp=abc").key);
    TEST_ASSERT_EQUAL((int)TuneKey::NONE, (int)parseTuneCommand("Kp=3.5xyz").key);
    TEST_ASSERT_EQUAL((int)TuneKey::NONE, (int)parseTuneCommand("Kx=1.0").key);
    TEST_ASSERT_EQUAL((int)TuneKey::NONE, (int)parseTuneCommand("=3.5").key);
    TEST_ASSERT_EQUAL((int)TuneKey::NONE, (int)parseTuneCommand("kp=3.5").key); // klein = falsch
    TEST_ASSERT_EQUAL((int)TuneKey::NONE, (int)parseTuneCommand(nullptr).key);
}

void test_lowercase_keys_rejected_by_design() {
    // Kleinbuchstaben-Keys wuerden mit Einzelzeichen-Befehlen kollidieren
    // (z.B. "sp=" beginnt mit Start-Befehl 's') -- deshalb NONE
    TEST_ASSERT_EQUAL((int)TuneKey::NONE, (int)parseTuneCommand("sp=1.0").key);
}

int main(int, char**) {
    UNITY_BEGIN();
    RUN_TEST(test_parses_all_keys);
    RUN_TEST(test_parses_values);
    RUN_TEST(test_trailing_whitespace_and_cr_ok);
    RUN_TEST(test_rejects_garbage);
    RUN_TEST(test_lowercase_keys_rejected_by_design);
    return UNITY_END();
}
