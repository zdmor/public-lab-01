"""Deterministic examples. Illustrative, NOT a backtest or realized trading proof."""
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import (Bar, Level, Config, patterns, pivot_points, structure,
                    make_plan, evaluate_latest, replay_ohlc, confirmed_line,
                    derive_levels)

C = Config()

class Tests(unittest.TestCase):
    def test_pin_and_context_free_patterns(self):
        before = Bar("2026-01-01", 10, 11, 9, 10.5)
        bullish = Bar("2026-01-02", 10.50, 10.65, 8.50, 10.60)
        bearish = Bar("2026-01-02", 10.50, 12.50, 10.35, 10.40)
        self.assertIn("PIN_BULL", patterns(before, bullish, C))
        self.assertIn("PIN_BEAR", patterns(before, bearish, C))
        self.assertIn("INSIDE", patterns(before, Bar("2026-01-02",10,10.8,9.2,10.1),C))
        self.assertIn("DOJI", patterns(before, Bar("2026-01-02",10,10.5,9.5,10.01),C))
        previous_down = Bar("2026-01-01", 10.5,10.6,9.7,9.8)
        up_engulf = Bar("2026-01-02",9.7,10.8,9.6,10.7)
        self.assertIn("ENGULF_BULL", patterns(previous_down, up_engulf, C))

    def test_structure_pivots_no_future(self):
        prices = [10,12,11,14,12,16,13,18,15]
        bars = [Bar(f"2026-01-{i+1:02d}",p,p+.2,p-.2,p) for i,p in enumerate(prices)]
        self.assertEqual("UP",structure(bars,Config(swing_left=1,swing_right=1)))
        hs,ls=pivot_points(bars,1,1)
        self.assertEqual([1,3,5,7],hs)
        self.assertEqual([2,4,6],ls)

    def test_video_four_math_1_to_2_and_1_to_5(self):
        # Video: short 103.5 / stop 110.5 / target 89.5; retrace 107 / same stop & target.
        s = Bar("2026-11-17",104,110.49,103.51,103.9)
        t = Level(89.5,"SUPPORT","VIDEO_ILLUSTRATION","2026-11-17")
        br = make_plan(s,"SHORT","BREAK_EXTREME",t,C)
        re = make_plan(s,"SHORT","RETRACE_50_618",t,C)
        self.assertEqual((103.5,110.5,89.5,2.0),
                         (br["entry_price"],br["stop_price"],br["target_price"],br["gross_rr"]))
        self.assertEqual((107.,110.5,89.5,5.0),
                         (re["entry_price"],re["stop_price"],re["target_price"],re["gross_rr"]))

    def test_video_three_math_1_to_3(self):
        s = Bar("2026-11-17",106.5,109.49,106.01,106.2)
        t = Level(95.5,"SUPPORT","VIDEO_ILLUSTRATION","2026-11-17")
        p = make_plan(s,"SHORT","BREAK_EXTREME",t,C)
        self.assertEqual((106.,109.5,95.5,3.0),
                         (p["entry_price"],p["stop_price"],p["target_price"],p["gross_rr"]))

    def test_rr_reject_with_nearby_resistance(self):
        s = Bar("2026-11-17",10,10.8,9.4,10.5)
        t = Level(11.,"RESISTANCE","TEST","2026-11-17")
        self.assertEqual("REJECT", make_plan(s,"LONG","BREAK_EXTREME",t,C)["status"])

    def test_latest_with_frozen_external_levels(self):
        history=[Bar(f"2026-01-{i:02d}",10.5,10.6,10.4,10.5) for i in range(1,21)]
        signal=Bar("2026-01-21",9.82,9.92,8.99,9.9)
        support=Level(9.0,"SUPPORT","VERIFIED_H4","2026-01-20")
        resistance=Level(15.,"RESISTANCE","VERIFIED_H4","2026-01-20")
        a=evaluate_latest(history+[signal],supplied_levels=[support,resistance],regime_override="UP")
        self.assertEqual(("PLAN","LONG","PIN_BULL"), (a.status,a.side,a.pattern))
        future=Level(9.0,"SUPPORT","FUTURE","2026-01-22")
        b=evaluate_latest(history+[signal],supplied_levels=[future,resistance],regime_override="UP")
        self.assertEqual(("UNKNOWN","FUTURE_LEVEL"), (b.status,b.reason))
        c=evaluate_latest(history+[signal],supplied_levels=[support],regime_override="UP")
        self.assertEqual(("UNKNOWN","NO_OBJECTIVE_NEXT_OBSTACLE_TARGET"), (c.status,c.reason))


    def test_range_boundary_yes_center_no(self):
        prices=[10,12,11,9]*6
        history=[Bar(f"2026-01-{i+1:02d}",p,p+.2,p-.2,p) for i,p in enumerate(prices)]
        upper_doji=Bar("2026-01-25",12,12.24,11.8,12.01)
        a=evaluate_latest(history+[upper_doji],Config(swing_left=1,swing_right=1))
        self.assertEqual(("PLAN","SHORT","DOJI"),(a.status,a.side,a.pattern))
        mid_doji=Bar("2026-01-25",10,10.5,9.7,10.01)
        b=evaluate_latest(history+[mid_doji],Config(swing_left=1,swing_right=1))
        self.assertEqual(("REJECT","RANGE_CENTER_NO_TRADE"),(b.status,b.reason))

    def test_trendline_three_confirmed_pivot_contacts(self):
        prices=[10,11,9,11,12,11,10,12,13,12,11,13,14,13]
        bars=[Bar(f"2026-01-{i+1:02d}",p,p+.2,p-.2,p) for i,p in enumerate(prices)]
        line=confirmed_line(bars,Config(swing_left=1,swing_right=1),"SUPPORT")
        self.assertIsNotNone(line)
        self.assertGreater(line[1],0)


    def test_opposite_engulf_exit_and_gap_unknown(self):
        sig=Bar("2026-11-17",104,110.49,103.51,103.9)
        target=Level(89.5,"SUPPORT","VIDEO","2026-11-17")
        p=make_plan(sig,"SHORT","BREAK_EXTREME",target,C)
        entered=Bar("2026-11-18",104,105,103,103.2)
        opposite=Bar("2026-11-19",103.0,105.2,102.9,105.1)
        self.assertEqual("OPPOSITE_ENGULF_AT_CLOSE",
                         replay_ohlc(p,[entered,opposite])["reason"])
        gap=Bar("2026-11-18",102,103,100,101)
        self.assertEqual("GAP_THROUGH_ENTRY",replay_ohlc(p,[gap])["reason"])


    def test_nearest_target_per_entry_and_reject_overhead_barrier(self):
        # Breakout enters above 9.93 obstacle; retrace enters below it.
        history=[Bar(f"2026-01-{i:02d}",10.5,10.6,10.4,10.5) for i in range(1,21)]
        signal=Bar("2026-01-21",9.82,9.92,8.99,9.9)
        levels=[
            Level(9.,"SUPPORT","VERIFIED","2026-01-20"),
            Level(9.93,"RESISTANCE","VERIFIED","2026-01-20"),
            Level(15.,"RESISTANCE","VERIFIED","2026-01-20"),
        ]
        a=evaluate_latest(history+[signal],supplied_levels=levels,regime_override="UP")
        self.assertEqual("PLAN",a.status)
        self.assertEqual(15.,a.plans[0]["target_price"])
        self.assertEqual("PLAN",a.plans[0]["status"])
        self.assertEqual(9.93,a.plans[1]["target_price"])
        self.assertEqual("REJECT",a.plans[1]["status"])


    def test_invalidation_cancels_unfilled_retrace(self):
        sig=Bar("2026-11-17",104,110.49,103.51,103.9)
        target=Level(89.5,"SUPPORT","VIDEO","2026-11-17")
        p=make_plan(sig,"SHORT","RETRACE_50_618",target,C)
        invalid=Bar("2026-11-18",111.0,111.5,110.6,111.0)
        later_retrace=Bar("2026-11-19",107.5,108,106.9,107.1)
        result=replay_ohlc(p,[invalid,later_retrace])
        self.assertEqual(("CANCELLED","STRUCTURAL_INVALIDATION_BEFORE_ENTRY"),
                         (result["status"],result["reason"]))

    def test_no_future_leakage_and_bad_bars(self):
        with self.assertRaises(ValueError):
            Bar("2026-01-01",5,3,4,5)
        history=[Bar(f"2026-01-{i:02d}",10,10.1,9.9,10) for i in range(1,20)]
        a=evaluate_latest(history)
        self.assertEqual("UNKNOWN",a.status)

    def test_replay_conservative_ambiguity(self):
        s=Bar("2026-11-17",104,110.49,103.51,103.9)
        t=Level(89.5,"SUPPORT","VIDEO","2026-11-17")
        p=make_plan(s,"SHORT","BREAK_EXTREME",t,C)
        ambiguous=Bar("2026-11-18",105,111,102,104)
        self.assertEqual("AMBIGUOUS",replay_ohlc(p,[ambiguous])["status"])
        entry=Bar("2026-11-18",104,105,103,103.2)
        target=Bar("2026-11-19",102,104,89,90)
        self.assertEqual(("EXIT","TARGET"), (replay_ohlc(p,[entry,target])["status"],
                                            replay_ohlc(p,[entry,target])["reason"]))
        nofill=Bar("2026-11-18",105,106,104,105)
        self.assertEqual("NOT_ENTERED", replay_ohlc(p,[nofill])["status"])


# ---- V0.1.1: cases from the Issue #6 review (bar indices are 0-based) ----

def _day(i, start=date(2026, 1, 1)):
    return (start + timedelta(days=i)).isoformat()


def _series(closes, spread):
    return [Bar(_day(i), p, round(p + spread, 4), round(p - spread, 4), p) for i, p in enumerate(closes)]


# Swing low 9.60 at index 3 is broken later (index 16 closes at 9.30); swing high 13.65 at index 9.
BROKEN_SUPPORT = [10.4, 10.2, 9.95, 9.75, 10.1, 10.8, 11.5, 12.2, 12.9, 13.5,
                  13.0, 12.3, 11.6, 10.9, 10.2, 9.6, 9.3]
# Swing lows (window 1/1) 8.8 / 9.8 / 11.3 / 11.8 at indices 2 / 6 / 10 / 14.
# 2, 6 and 14 lie on one rising line (slope 0.25); index 10 is a higher low above it.
HIGHER_LOW_LINE = [9.6, 9.3, 9.0, 9.6, 10.4, 10.2, 10.0, 10.8, 11.8, 11.7,
                   11.5, 12.3, 12.9, 12.4, 12.0, 12.6, 13.0]
FLAT = [Bar(f"2026-01-{i:02d}", 10.5, 10.6, 10.4, 10.5) for i in range(1, 21)]
VIDEO_SHORT = Bar("2026-11-17", 104, 110.49, 103.51, 103.9)


class Issue6Review(unittest.TestCase):
    def test_broken_support_is_an_overhead_obstacle(self):
        # SPEC 5.3: the nearest level above a LONG entry caps the target,
        # whether it formed as support or resistance.
        hist = _series(BROKEN_SUPPORT, 0.15)
        signal = Bar(_day(len(hist)), 9.25, 9.35, 8.70, 9.30)  # bullish pin touching 8.75
        support = Level(8.75, "SUPPORT", "VERIFIED", hist[-1].date)
        a = evaluate_latest(hist + [signal], supplied_levels=[support], regime_override="DOWN")
        # V0.1: PLAN, both targets 13.65, gross RR 6.40 / 14.03
        self.assertEqual({9.6}, {p["target_price"] for p in a.plans})
        self.assertEqual(("REJECT", "NO_RR_GE_2"), (a.status, a.reason))

    def test_retrace_entry_gapped_through_is_unknown(self):
        # SPEC 5.4 item 6 also applies to RETRACE_50_618: sell limit 107, stop 110.5.
        plan = make_plan(VIDEO_SHORT, "SHORT", "RETRACE_50_618",
                         Level(89.5, "SUPPORT", "VIDEO", "2026-11-17"), C)
        gap_then_stop = Bar("2026-11-18", 108.0, 111.0, 107.5, 110.8)  # V0.1: CANCELLED
        gap_only = Bar("2026-11-18", 108.0, 108.5, 107.5, 108.2)       # V0.1: NOT_ENTERED
        for bar in (gap_then_stop, gap_only):
            r = replay_ohlc(plan, [bar])
            self.assertEqual(("UNKNOWN", "GAP_THROUGH_ENTRY"), (r["status"], r["reason"]))

    def test_trendline_allows_a_higher_low_between_touches(self):
        # SPEC 3.3: three touches, no close below the line, a higher low in between.
        line = confirmed_line(_series(HIGHER_LOW_LINE, 0.2), Config(swing_left=1, swing_right=1), "SUPPORT")
        self.assertIsNotNone(line)  # V0.1: None
        self.assertAlmostEqual(0.25, line[1])
        self.assertEqual(3, line[2])
        self.assertAlmostEqual(12.55, line[0])

    def test_level_dated_on_the_signal_day_is_rejected(self):
        # SPEC 2: a level dated the signal day may have been drawn after the signal bar.
        signal = Bar("2026-01-21", 9.82, 9.92, 8.99, 9.9)
        drawn = Level(8.99, "SUPPORT", "DRAWN_AT_SIGNAL_LOW", "2026-01-21")
        resistance = Level(15.0, "RESISTANCE", "VERIFIED", "2026-01-20")
        a = evaluate_latest(FLAT + [signal], supplied_levels=[drawn, resistance], regime_override="UP")
        self.assertEqual(("UNKNOWN", "FUTURE_LEVEL"), (a.status, a.reason))  # V0.1: PLAN

    def test_derived_level_is_dated_when_the_pivot_is_confirmed(self):
        # SPEC 2: a swing point is known only swing_right bars after it.
        hist = _series(BROKEN_SUPPORT, 0.15)
        as_of = {(x.kind, x.price): x.as_of for x in derive_levels(hist, C)}
        self.assertEqual(hist[3 + C.swing_right].date, as_of[("SUPPORT", 9.6)])  # V0.1: hist[3]
        self.assertEqual(hist[9 + C.swing_right].date, as_of[("RESISTANCE", 13.65)])

    def test_engulf_requires_body_cover_and_range_cover_is_optional(self):
        # SPEC 4: the real body must cover the previous real body.
        prev = Bar("2026-01-01", 10.5, 10.6, 9.9, 10.0)
        body_not_covered = Bar("2026-01-02", 9.95, 10.6, 9.9, 10.46)  # V0.1: ENGULF_BULL
        prev_long_wick = Bar("2026-01-01", 10.5, 11.2, 9.9, 10.0)
        body_covered = Bar("2026-01-02", 9.95, 10.7, 9.9, 10.65)      # V0.1: not engulfing
        self.assertNotIn("ENGULF_BULL", patterns(prev, body_not_covered, C))
        self.assertIn("ENGULF_BULL", patterns(prev_long_wick, body_covered, C))
        strict = Config(engulf_cover_range=True)
        self.assertNotIn("ENGULF_BULL", patterns(prev_long_wick, body_covered, strict))

    def test_entry_window_expires(self):
        # SPEC 5.4 item 7: optional entry window.
        signal = Bar("2026-01-21", 9.82, 9.92, 8.99, 9.9)
        a = evaluate_latest(FLAT + [signal], regime_override="UP", supplied_levels=[
            Level(9.0, "SUPPORT", "VERIFIED", "2026-01-20"),
            Level(15.0, "RESISTANCE", "VERIFIED", "2026-01-20")])
        quiet = [Bar(_day(i, date(2026, 1, 22)), 9.5, 9.8, 9.2, 9.5) for i in range(25)]
        breakout = Bar(_day(25, date(2026, 1, 22)), 9.85, 10.2, 9.8, 10.1)
        self.assertEqual("OPEN", replay_ohlc(a.plans[0], quiet + [breakout])["status"])
        self.assertEqual("EXPIRED", replay_ohlc(a.plans[0], quiet + [breakout], max_wait_bars=3)["status"])

    def test_t_plus_one_long_cannot_exit_on_entry_day(self):
        # SPEC 5.4 item 8: A-share T+1 for longs.
        signal = Bar("2026-11-17", 10.00, 10.20, 9.90, 10.15)
        plan = make_plan(signal, "LONG", "BREAK_EXTREME", Level(10.90, "RESISTANCE", "TEST", "2026-11-16"), C)
        entry_day = Bar("2026-11-18", 10.18, 10.95, 10.10, 10.80)  # trigger 10.21 and target 10.90 same day
        next_day = Bar("2026-11-19", 10.85, 11.00, 10.70, 10.95)
        self.assertEqual("AMBIGUOUS", replay_ohlc(plan, [entry_day, next_day])["status"])
        r = replay_ohlc(plan, [entry_day, next_day], t_plus_one=True)
        self.assertEqual(("EXIT", "TARGET", "2026-11-19"), (r["status"], r["reason"], r["date"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
