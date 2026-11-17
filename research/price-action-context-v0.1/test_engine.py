"""Deterministic examples. Illustrative, NOT a backtest or realized trading proof."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import (Bar, Level, Config, patterns, pivot_points, structure,
                    make_plan, evaluate_latest, replay_ohlc, confirmed_line)

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

if __name__ == "__main__":
    unittest.main(verbosity=2)
