"""Research-only price-action framework derived from XtradingTime's 2026-11-17 article.
No market data fetching, order placement, production integration, or probability claims.
All quantitative choices absent from the article are marked IMPLEMENTATION in SPEC.md.
Python 3.10+, standard library only.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from datetime import date
from typing import Optional

VERSION = "PA_CONTEXT_V0_1_1_RESEARCH"   # V0.1.1: Issue #6 review fixes, see SPEC.md section 10

def _iso_day(value: str) -> bool:
    try:
        return (len(value)==10 and value[4]=="-" and value[7]=="-" and
                date.fromisoformat(value).isoformat()==value)
    except (ValueError,TypeError):
        return False

@dataclass(frozen=True)
class Bar:
    date: str
    open: float
    high: float
    low: float
    close: float

    def __post_init__(self):
        if not _iso_day(self.date):
            raise ValueError("INVALID_DATE")
        if not (0 < self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high):
            raise ValueError("INVALID_OHLC")

@dataclass(frozen=True)
class Level:
    price: float
    kind: str               # SUPPORT or RESISTANCE
    source: str             # PRIOR_PIVOT, USER_VERIFIED, VIDEO_ILLUSTRATION
    as_of: str              # date of last information available; no future levels

    def __post_init__(self):
        if self.kind not in ("SUPPORT", "RESISTANCE") or self.price <= 0 or not _iso_day(self.as_of) or not self.source:
            raise ValueError("INVALID_LEVEL")

@dataclass(frozen=True)
class Config:
    tick: float = 0.01
    swing_left: int = 2       # IMPLEMENTATION
    swing_right: int = 2      # IMPLEMENTATION: confirmed, never use future
    doji_body_max: float = .10            # IMPLEMENTATION
    pin_body_max: float = 1 / 3          # IMPLEMENTATION
    pin_wick_min: float = 2 / 3          # ARTICLE: long shadow >= 2/3
    opposite_wick_max: float = .15        # IMPLEMENTATION
    atr_period: int = 14                 # IMPLEMENTATION
    level_tolerance_atr: float = .25     # IMPLEMENTATION
    minimum_rr: float = 2.0              # ARTICLE
    retrace_min: float = .50             # ARTICLE
    retrace_max: float = .618            # ARTICLE
    engulf_cover_range: bool = False     # IMPLEMENTATION: also require high/low coverage

    def __post_init__(self):
        if self.tick <= 0 or self.swing_left < 1 or self.swing_right < 1:
            raise ValueError("INVALID_CONFIG")
        if not (0 < self.doji_body_max < 1 and 0 < self.pin_body_max < 1 and
                .5 < self.pin_wick_min <= 1 and 0 <= self.opposite_wick_max < 1 and
                0 <= self.level_tolerance_atr and self.atr_period >= 1 and
                self.minimum_rr >= 2 and .4 <= self.retrace_min < self.retrace_max <= .7):
            raise ValueError("INVALID_CONFIG")

@dataclass
class Assessment:
    status: str                # PLAN, REJECT, UNKNOWN
    reason: str
    regime: str = "UNKNOWN"
    location: str = "UNKNOWN"
    pattern: str = "NONE"
    side: str = "NONE"
    plans: list[dict] = field(default_factory=list)
    provenance: str = VERSION

def _tick(price: float, config: Config, up: bool) -> float:
    value = Decimal(str(price)) / Decimal(str(config.tick))
    v = value.to_integral_value(rounding=ROUND_CEILING if up else ROUND_FLOOR)
    return float(v * Decimal(str(config.tick)))

def pivot_points(bars: list[Bar], left: int, right: int) -> tuple[list[int], list[int]]:
    """Confirmed local maxima/minima, only bars in supplied CLOSED history."""
    highs, lows = [], []
    for i in range(left, len(bars) - right):
        neighbors = [j for j in range(i - left, i + right + 1) if j != i]
        if all(bars[i].high > bars[j].high for j in neighbors):
            highs.append(i)
        if all(bars[i].low < bars[j].low for j in neighbors):
            lows.append(i)
    return highs, lows

def structure(bars: list[Bar], c: Config) -> str:
    hs, ls = pivot_points(bars, c.swing_left, c.swing_right)
    if len(hs) < 2 or len(ls) < 2:
        return "UNKNOWN"
    hh = bars[hs[-1]].high > bars[hs[-2]].high
    hl = bars[ls[-1]].low > bars[ls[-2]].low
    lh = bars[hs[-1]].high < bars[hs[-2]].high
    ll = bars[ls[-1]].low < bars[ls[-2]].low
    if hh and hl:
        return "UP"
    if lh and ll:
        return "DOWN"
    return "RANGE"

def atr(bars: list[Bar], period: int) -> Optional[float]:
    if len(bars) < period + 1:
        return None
    vals = []
    for i in range(len(bars) - period, len(bars)):
        b, p = bars[i], bars[i-1]
        vals.append(max(b.high - b.low, abs(b.high - p.close), abs(b.low - p.close)))
    return sum(vals) / period

def patterns(prev: Bar, now: Bar, c: Config) -> set[str]:
    rng = now.high - now.low
    if rng <= 0:
        return set()
    body = abs(now.close - now.open)
    upper = now.high - max(now.open, now.close)
    lower = min(now.open, now.close) - now.low
    out: set[str] = set()
    if body / rng <= c.doji_body_max:
        out.add("DOJI")
    if (body / rng <= c.pin_body_max and lower / rng >= c.pin_wick_min
            and upper / rng <= c.opposite_wick_max):
        out.add("PIN_BULL")
    if (body / rng <= c.pin_body_max and upper / rng >= c.pin_wick_min
            and lower / rng <= c.opposite_wick_max):
        out.add("PIN_BEAR")
    if now.high < prev.high and now.low > prev.low:
        out.add("INSIDE")
    # Real body must cover the previous real body; also covering the previous
    # high/low is an optional, stricter reading (IMPLEMENTATION).
    covers_range = now.high >= prev.high and now.low <= prev.low
    larger_body = abs(now.close-now.open) > abs(prev.close-prev.open)
    if (now.close > now.open and prev.close < prev.open and larger_body and
            now.open <= prev.close and now.close >= prev.open and
            (covers_range or not c.engulf_cover_range)):
        out.add("ENGULF_BULL")
    if (now.close < now.open and prev.close > prev.open and larger_body and
            now.open >= prev.close and now.close <= prev.open and
            (covers_range or not c.engulf_cover_range)):
        out.add("ENGULF_BEAR")
    return out


def confirmed_line(history: list[Bar], c: Config, kind: str) -> Optional[tuple[float,float,int]]:
    """Ascending line with >=3 confirmed contacts; return price, slope, contact_count.
    After validation (third touch), first two additional touches are allowed.
    Sixth+ collinear contact is excluded as a conservative EXHAUSTION filter.
    The 'sixth' mapping is a declared implementation of author's 3rd/4th
    post-validation retest caution, not a statistically established threshold.
    """
    hs,ls = pivot_points(history,c.swing_left,c.swing_right)
    ids = (ls if kind == "SUPPORT" else hs)[-10:]
    if len(ids) < 3:
        return None
    def value(i: int) -> float:
        return history[i].low if kind == "SUPPORT" else history[i].high
    tolerance = max(c.tick,(atr(history,c.atr_period) or 0)*c.level_tolerance_atr)
    for start in range(len(ids)-2):
        i0,i1=ids[start],ids[start+1]
        slope=(value(i1)-value(i0))/(i1-i0)
        if slope <= 0:
            continue
        def line(idx: int, i0: int = i0, slope: float = slope) -> float:
            return value(i0)+slope*(idx-i0)
        # Only a CLOSE beyond the line breaks it (SPEC 3.3: a pierce without a
        # close is not a break); swing points on the far side are not contacts.
        if kind == "SUPPORT":
            broken = any(history[k].close < line(k)-tolerance for k in range(i0, len(history)))
        else:
            broken = any(history[k].close > line(k)+tolerance for k in range(i0, len(history)))
        if broken:
            continue
        contacts=[idx for idx in ids[start:] if abs(value(idx)-line(idx)) <= tolerance]
        if len(contacts) < 3:
            continue
        # Only accept a line that remains current, not an old historical segment.
        if contacts[-1] != ids[-1]:
            continue
        next_price=value(i0)+slope*(len(history)-i0)
        if next_price > 0:
            return next_price,slope,len(contacts)
    return None

def inferred_range_edges(history: list[Bar], c: Config) -> Optional[tuple[float,float]]:
    hs, ls = pivot_points(history,c.swing_left,c.swing_right)
    if len(hs) < 2 or len(ls) < 2:
        return None
    low = min(history[i].low for i in ls[-3:])
    high = max(history[i].high for i in hs[-3:])
    return (low, high) if low < high else None

def derive_levels(history: list[Bar], c: Config) -> list[Level]:
    hs, ls = pivot_points(history, c.swing_left, c.swing_right)
    # A swing point is known only swing_right bars later: date the level then.
    return ([Level(history[i].low, "SUPPORT", "PRIOR_CONFIRMED_PIVOT", history[i + c.swing_right].date)
             for i in ls] +
            [Level(history[i].high, "RESISTANCE", "PRIOR_CONFIRMED_PIVOT", history[i + c.swing_right].date)
             for i in hs])

def nearest_level(signal: Bar, levels: list[Level], kind: str, tolerance: float) -> Optional[Level]:
    eligible = [x for x in levels if x.kind == kind and x.as_of <= signal.date
                and signal.low - tolerance <= x.price <= signal.high + tolerance]
    return min(eligible, key=lambda x: (abs(x.price - signal.close), x.price)) if eligible else None

def target_level(entry: float, levels: list[Level], side: str, signal_date: str) -> Optional[Level]:
    # Nearest known level in the trade direction, whatever role it had when it
    # formed: a broken support above a LONG entry is overhead supply.
    if side == "LONG":
        valid = [x for x in levels if x.price > entry and x.as_of <= signal_date]
        return min(valid, key=lambda x: x.price) if valid else None
    valid = [x for x in levels if x.price < entry and x.as_of <= signal_date]
    return max(valid, key=lambda x: x.price) if valid else None

def make_plan(signal: Bar, side: str, mode: str, target: Level, c: Config,
              wedge_lower: Optional[float] = None) -> dict:
    """Plan at signal CLOSE; fill needs later bars. Stops outside signal extremum.
    Wedge-short breakout also requires lower trendline breach (article).
    """
    if side not in ("LONG","SHORT") or mode not in ("BREAK_EXTREME","RETRACE_50_618"):
        return {"status":"REJECT","reason":"INVALID_SIDE_OR_MODE"}
    width = signal.high - signal.low
    if width <= 0:
        return {"status": "REJECT", "reason": "ZERO_RANGE"}
    if side == "LONG":
        trigger = _tick(signal.high + c.tick, c, up=True)
        stop = _tick(signal.low - c.tick, c, up=False)
        band = [_tick(signal.high - width * c.retrace_max, c, True),
                _tick(signal.high - width * c.retrace_min, c, False)]
        entry = trigger if mode == "BREAK_EXTREME" else band[1]
    else:
        floor = min(signal.low, wedge_lower) if wedge_lower is not None else signal.low
        trigger = _tick(floor - c.tick, c, up=False)
        stop = _tick(signal.high + c.tick, c, up=True)
        band = [_tick(signal.low + width * c.retrace_min, c, True),
                _tick(signal.low + width * c.retrace_max, c, False)]
        entry = trigger if mode == "BREAK_EXTREME" else band[0]
    risk = entry - stop if side == "LONG" else stop - entry
    reward = target.price - entry if side == "LONG" else entry - target.price
    rr = reward / risk if risk > 0 else -1
    valid = (risk > 0 and reward > 0 and rr + 1e-10 >= c.minimum_rr)
    return dict(status="PLAN" if valid else "REJECT",
                reason="RR_PASS" if valid else "RR_LT_2_OR_INVALID",
                side=side, entry_mode=mode, entry_price=entry,
                retrace_band=band if mode == "RETRACE_50_618" else None,
                trigger_price=trigger if mode == "BREAK_EXTREME" else None,
                stop_price=stop, target_price=target.price, target_source=target.source,
                risk_per_share=round(risk, 6), reward_per_share=round(reward, 6),
                gross_rr=round(rr, 4), signal_date=signal.date,
                execution="PENDING_NOT_FILLED", trade_authority=False)

def evaluate_latest(bars: list[Bar], c: Config = Config(),
                    supplied_levels: Optional[list[Level]] = None,
                    regime_override: Optional[str] = None,
                    wedge_lower: Optional[float] = None,
                    range_bounds: Optional[tuple[float,float]] = None) -> Assessment:
    """Last bar must be CLOSED. Override only with separately verified, dated higher-TF context.
    Research ONLY. No future OHLC may enter history or supplied levels.
    """
    min_len = max(c.atr_period+2, 2*c.swing_left+2*c.swing_right+6)
    if len(bars) < min_len:
        return Assessment("UNKNOWN", "INSUFFICIENT_HISTORY")
    if any(bars[i].date >= bars[i+1].date for i in range(len(bars)-1)):
        return Assessment("UNKNOWN", "UNSORTED_OR_DUPLICATE_DATES")
    signal, history = bars[-1], bars[:-1]
    regime = regime_override if regime_override is not None else structure(history, c)
    if regime not in ("UP", "DOWN", "RANGE", "UNKNOWN"):
        return Assessment("UNKNOWN", "INVALID_REGIME")
    if regime == "UNKNOWN":
        return Assessment("UNKNOWN", "UNKNOWN_STRUCTURE", regime=regime)
    a = atr(history, c.atr_period)
    if a is None:
        return Assessment("UNKNOWN", "NO_ATR_HISTORY", regime=regime)
    tol = max(c.tick, c.level_tolerance_atr*a)
    levels = derive_levels(history, c) + (supplied_levels or [])
    # Reject future-sourced levels rather than silently looking ahead.
    # A level dated the signal day itself may have been drawn after the signal bar.
    if any(x.as_of >= signal.date for x in levels):
        return Assessment("UNKNOWN", "FUTURE_LEVEL", regime=regime)
    # Range-center signals are noise, but strong range BOUNDARIES remain eligible
    # (video #2 and article's resistance Doji case). Explicit boundaries are
    # supplied/verified; otherwise infer from older confirmed pivot extremes.
    if regime == "RANGE":
        bounds = range_bounds if range_bounds is not None else inferred_range_edges(history,c)
        if bounds is None or not (0 < bounds[0] < bounds[1]):
            return Assessment("UNKNOWN", "NO_VERIFIABLE_RANGE_BOUNDARIES", regime=regime)
        lo,hi = bounds
        levels += [Level(lo,"SUPPORT","RANGE_BOUNDARY",history[-1].date),
                   Level(hi,"RESISTANCE","RANGE_BOUNDARY",history[-1].date)]
        touches_edge = (signal.low <= lo+tol and signal.high >= lo-tol) or (
            signal.high >= hi-tol and signal.low <= hi+tol)
        if not touches_edge:
            return Assessment("REJECT","RANGE_CENTER_NO_TRADE",regime=regime)
    if regime == "UP":
        low_line = confirmed_line(history,c,"SUPPORT")
        if low_line and low_line[2] <= 5:
            levels.append(Level(low_line[0],"SUPPORT","ASCENDING_LINE_TOUCHES_"+str(low_line[2]),history[-1].date))
        high_line = confirmed_line(history,c,"RESISTANCE")
        if (low_line and high_line and low_line[2] <= 5 and high_line[2] <= 5 and high_line[0] > low_line[0] and
                0 < high_line[1] < low_line[1]):
            levels.append(Level(high_line[0],"RESISTANCE","ASCENDING_WEDGE_UPPER",history[-1].date))
            if wedge_lower is None:
                wedge_lower=low_line[0]
    ps = patterns(history[-1], signal, c)
    support = nearest_level(signal, levels, "SUPPORT", tol)
    resistance = nearest_level(signal, levels, "RESISTANCE", tol)
    side = ""
    selected = ""
    location = ""
    # Context must support the semantic trade. Bear in DOWN is continuation;
    # bull in DOWN is reversal (requires support); opposite for UP.
    for side0, kind, preferred in [
        ("LONG", support, ("PIN_BULL","ENGULF_BULL","INSIDE")),
        ("SHORT", resistance, ("PIN_BEAR","ENGULF_BEAR","DOJI")),
    ]:
        if kind is None:
            continue
        if regime == "RANGE":
            lo,hi = bounds
            if (side0 == "LONG" and abs(kind.price-lo)>tol) or (
                    side0 == "SHORT" and abs(kind.price-hi)>tol):
                continue
        matches = [p for p in preferred if p in ps]
        if not matches:
            continue
        # Source specifically gives INSIDE bullish continuation in UP.
        if "INSIDE" in matches and regime != "UP":
            matches.remove("INSIDE")
        # Source specifically gives DOJI bearish reversal at resistance.
        if "DOJI" in matches and regime not in ("UP","RANGE"):
            matches.remove("DOJI")
        if matches:
            side, selected, location = side0, matches[0], kind.kind+":"+kind.source
            break
    if not side:
        return Assessment("REJECT", "NO_PATTERN_AT_MATCHING_KEY_LEVEL", regime=regime,
                          location="NEAR_LEVEL" if support or resistance else "NO_KEY_LEVEL",
                          pattern=",".join(sorted(ps)) if ps else "NONE")
    plans = []
    width = signal.high - signal.low
    for mode in ("BREAK_EXTREME", "RETRACE_50_618"):
        if side == "LONG":
            provisional = (_tick(signal.high+c.tick,c,True) if mode=="BREAK_EXTREME"
                           else _tick(signal.high-width*c.retrace_min,c,False))
        else:
            floor = min(signal.low,wedge_lower) if wedge_lower is not None else signal.low
            provisional = (_tick(floor-c.tick,c,False) if mode=="BREAK_EXTREME"
                           else _tick(signal.low+width*c.retrace_min,c,True))
        target = target_level(provisional, levels, side, signal.date)
        if target is None:
            plans.append({"status":"UNKNOWN","entry_mode":mode,"entry_price":provisional,
                          "reason":"NO_OBJECTIVE_NEXT_OBSTACLE_TARGET"})
        else:
            plans.append(make_plan(signal, side, mode, target, c, wedge_lower))
    if all(p["status"] == "UNKNOWN" for p in plans):
        return Assessment("UNKNOWN", "NO_OBJECTIVE_NEXT_OBSTACLE_TARGET", regime, location, selected, side, plans)
    if all(p["status"] != "PLAN" for p in plans):
        if any(p["status"] == "UNKNOWN" for p in plans):
            return Assessment("UNKNOWN","ONE_MODE_TARGET_UNKNOWN",regime,location,selected,side,plans)
        return Assessment("REJECT", "NO_RR_GE_2", regime, location, selected, side, plans)
    return Assessment("PLAN", "SIGNAL_PLUS_LOCATION; pending future entry trigger",
                      regime, location, selected, side, plans)

def replay_ohlc(plan: dict, future: list[Bar], move_to_breakeven: bool = False,
                exit_on_opposite_engulf: bool = True, c: Config = Config(),
                max_wait_bars: Optional[int] = None, t_plus_one: bool = False) -> dict:
    """Conservative BAR-LEVEL illustrative replay, not a broker fill simulator.
    Any competing entry/stop or stop/target event in one OHLC bar -> AMBIGUOUS.
    BE is effective NEXT bar after an observed 1R excursion.
    max_wait_bars: a pending plan expires after that many bars without entry (IMPLEMENTATION).
    t_plus_one: a LONG opened on a bar cannot be closed on that bar (A-share rule).
    """
    if plan["status"] != "PLAN":
        return {"status": "REJECT", "reason": "PLAN_NOT_VALID"}
    side, entry, stop, target = [plan[k] for k in
        ("side", "entry_price", "stop_price", "target_price")]
    mode = plan["entry_mode"]
    initial_risk = abs(entry - stop)
    active = False
    previous: Optional[Bar] = None
    waited = 0
    for b in future:
        enter = (b.high >= entry) if side == "LONG" and mode == "BREAK_EXTREME" else (
            (b.low <= entry) if side == "SHORT" and mode == "BREAK_EXTREME" else
            (b.low <= entry <= b.high))
        stopped = (b.low <= stop) if side == "LONG" else (b.high >= stop)
        won = (b.high >= target) if side == "LONG" else (b.low <= target)
        if not active:
            if max_wait_bars is not None and waited >= max_wait_bars:
                return {"status": "EXPIRED", "reason": "ENTRY_WINDOW_ELAPSED", "date": b.date}
            if mode == "RETRACE_50_618":
                # A resting limit opened through is filled at the open, not at the
                # planned price (SPEC 5.4 item 6); an open beyond the stop cancels.
                beyond_entry = b.open < entry if side == "LONG" else b.open > entry
                beyond_stop = b.open <= stop if side == "LONG" else b.open >= stop
                if beyond_entry and not beyond_stop:
                    return {"status": "UNKNOWN", "reason": "GAP_THROUGH_ENTRY", "date": b.date}
            if not enter:
                if stopped:
                    return {"status": "CANCELLED",
                            "reason": "STRUCTURAL_INVALIDATION_BEFORE_ENTRY",
                            "date": b.date}
                waited += 1
                continue
            # T+1: a long opened on this bar cannot reach its target exit on it.
            if stopped or (won and not (t_plus_one and side == "LONG")):
                return {"status": "AMBIGUOUS", "reason": "ENTRY_AND_EXIT_WITHIN_SAME_BAR", "date": b.date}
            if mode == "BREAK_EXTREME" and ((side == "LONG" and b.open > entry) or
                                               (side == "SHORT" and b.open < entry)):
                return {"status": "UNKNOWN", "reason": "GAP_THROUGH_ENTRY", "date": b.date}
            active = True
            previous = b
            # entry is only a theoretical trigger, actual opening gaps/slippage unknown
            continue
        if stopped and won:
            return {"status": "AMBIGUOUS", "reason": "STOP_AND_TARGET_SAME_BAR", "date": b.date}
        if stopped:
            price = (min(b.open, stop) if side == "LONG" else max(b.open, stop))
            return {"status": "EXIT", "reason": "STOP", "date": b.date,
                    "theoretical_exit_price": price}
        if won:
            return {"status": "EXIT", "reason": "TARGET", "date": b.date,
                    "theoretical_exit_price": target}
        if exit_on_opposite_engulf and previous is not None:
            p = patterns(previous,b,c)
            opposite = "ENGULF_BEAR" if side == "LONG" else "ENGULF_BULL"
            if opposite in p:
                return {"status": "EXIT", "reason": "OPPOSITE_ENGULF_AT_CLOSE",
                        "date": b.date, "theoretical_exit_price": b.close}
        achieved_1r = (b.high >= entry+initial_risk if side == "LONG"
                       else b.low <= entry-initial_risk)
        if move_to_breakeven and achieved_1r:
            stop = entry   # from NEXT bar, avoids same-bar lookahead
        previous = b
    return {"status": "OPEN" if active else "NOT_ENTERED",
            "reason": "NO_EXIT_YET" if active else "NO_ENTRY_TRIGGER",
            "current_theoretical_stop": stop if active else None}

def to_dict(obj: Assessment) -> dict:
    return asdict(obj)
