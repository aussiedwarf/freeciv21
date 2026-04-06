// SPDX-License-Identifier: GPL-3.0-or-later
// SPDX-FileCopyrightText: Freeciv21 and Freeciv Contributors

// common
#include "combat.h"

// Qt
#include <QtTest>

#include <cmath>

/**
 * Tests for the win_chance() combat probability function.
 *
 * win_chance(as, ahp, afp, ds, dhp, dfp) computes the attacker's
 * probability of winning a combat given:
 *   as  = attack strength
 *   ahp = attacker hit points
 *   afp = attacker firepower
 *   ds  = defense strength
 *   dhp = defender hit points
 *   dfp = defender firepower
 *
 * These tests validate the math that unit_win_chance() depends on
 * after applying first-strike HP reduction.
 */
class test_combat_math : public QObject {
  Q_OBJECT

private slots:
  void equal_units();
  void attacker_stronger();
  void defender_stronger();
  void reduced_attacker_hp();
  void reduced_defender_hp();
  void first_strike_hp_effect();
  void zero_firepower();
  void high_firepower();
  void zero_strength();
};

/**
 * Equal stats should give approximately 50% win chance.
 */
void test_combat_math::equal_units()
{
  double chance = win_chance(10, 20, 1, 10, 20, 1);
  QVERIFY2(std::abs(chance - 0.5) < 0.01,
           qPrintable(QString("Expected ~0.5, got %1").arg(chance)));
}

/**
 * Higher attack strength should give > 50% win chance.
 */
void test_combat_math::attacker_stronger()
{
  double chance = win_chance(20, 20, 1, 10, 20, 1);
  QVERIFY2(chance > 0.5,
           qPrintable(QString("Expected > 0.5, got %1").arg(chance)));
}

/**
 * Higher defense strength should give < 50% win chance.
 */
void test_combat_math::defender_stronger()
{
  double chance = win_chance(10, 20, 1, 20, 20, 1);
  QVERIFY2(chance < 0.5,
           qPrintable(QString("Expected < 0.5, got %1").arg(chance)));
}

/**
 * Reduced attacker HP (simulating first-strike damage to attacker)
 * should reduce win chance compared to full HP.
 */
void test_combat_math::reduced_attacker_hp()
{
  double full_hp = win_chance(10, 20, 1, 10, 20, 1);
  double reduced = win_chance(10, 15, 1, 10, 20, 1);
  QVERIFY2(reduced < full_hp,
           qPrintable(QString("Reduced HP (%1) should be less than full HP "
                              "(%2)")
                          .arg(reduced)
                          .arg(full_hp)));
}

/**
 * Reduced defender HP (simulating attacker first-strike advantage)
 * should increase attacker win chance.
 */
void test_combat_math::reduced_defender_hp()
{
  double full_hp = win_chance(10, 20, 1, 10, 20, 1);
  double reduced = win_chance(10, 20, 1, 10, 15, 1);
  QVERIFY2(reduced > full_hp,
           qPrintable(QString("Reduced defender HP (%1) should give higher "
                              "win chance than full HP (%2)")
                          .arg(reduced)
                          .arg(full_hp)));
}

/**
 * Simulates the effect of first strikes on combat probability:
 * more first-strike damage should monotonically shift win chance.
 */
void test_combat_math::first_strike_hp_effect()
{
  // Simulate defender taking increasing first-strike damage
  double prev = 0.0;
  for (int def_hp = 20; def_hp >= 5; def_hp -= 5) {
    double chance = win_chance(10, 20, 1, 10, def_hp, 1);
    QVERIFY2(chance > prev,
             qPrintable(
                 QString("Win chance should increase as defender HP drops: "
                         "def_hp=%1, chance=%2, prev=%3")
                     .arg(def_hp)
                     .arg(chance)
                     .arg(prev)));
    prev = chance;
  }

  // Simulate attacker taking increasing first-strike damage
  prev = 1.0;
  for (int att_hp = 20; att_hp >= 5; att_hp -= 5) {
    double chance = win_chance(10, att_hp, 1, 10, 20, 1);
    QVERIFY2(chance < prev,
             qPrintable(
                 QString("Win chance should decrease as attacker HP drops: "
                         "att_hp=%1, chance=%2, prev=%3")
                     .arg(att_hp)
                     .arg(chance)
                     .arg(prev)));
    prev = chance;
  }
}

/**
 * Zero firepower edge cases.
 */
void test_combat_math::zero_firepower()
{
  // Zero attacker firepower: attacker can never kill defender
  double chance = win_chance(10, 20, 0, 10, 20, 1);
  QCOMPARE(chance, 0.0);

  // Zero defender firepower: defender can never kill attacker
  chance = win_chance(10, 20, 1, 10, 20, 0);
  QCOMPARE(chance, 1.0);
}

/**
 * Higher firepower means fewer rounds needed to kill, shifting odds.
 */
void test_combat_math::high_firepower()
{
  // Attacker with 2 firepower vs defender with 1
  double high_att_fp = win_chance(10, 20, 2, 10, 20, 1);
  double equal_fp = win_chance(10, 20, 1, 10, 20, 1);
  QVERIFY2(high_att_fp > equal_fp,
           qPrintable(QString("Higher attacker firepower (%1) should beat "
                              "equal firepower (%2)")
                          .arg(high_att_fp)
                          .arg(equal_fp)));
}

/**
 * Zero attack and defense strength should give 50% chance (coin flip).
 */
void test_combat_math::zero_strength()
{
  double chance = win_chance(0, 20, 1, 0, 20, 1);
  QVERIFY2(std::abs(chance - 0.5) < 0.01,
           qPrintable(QString("Expected ~0.5 for zero strength, got %1")
                          .arg(chance)));
}

QTEST_MAIN(test_combat_math)
#include "combat_math.moc"
