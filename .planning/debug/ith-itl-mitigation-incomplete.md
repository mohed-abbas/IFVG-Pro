---
status: resolved
trigger: "ITH/ITL mitigation detection only triggers on wick-through, not on body close-through"
created: 2026-04-12T00:00:00Z
updated: 2026-04-12T00:00:00Z
---

## Current Focus

hypothesis: The detection logic (complete break check) correctly sets is_valid=false for ITH/ITL on body-close-through, BUT the rendering code does not visually reflect this state change for ITH/ITL levels. The rendering only checks is_swept for ITH/ITL color, and the skip/hide logic for broken levels only applies to EQH/EQL.
test: Fix rendering to handle is_valid=false for ITH/ITL, verify visually
expecting: Broken ITH/ITL levels should appear grayed out / faded like EQH/EQL when broken
next_action: Apply fix to rendering code

## Symptoms

expected: ITH/ITL levels should be marked as mitigated (is_valid=false or is_swept=true) when price passes through them -- whether by a wick that exceeds the level OR by a candle body that closes through the level.
actual: Only marks as mitigated when a wick passes through the level. When a candle body directly closes above an ITH or below an ITL, the level remains active visually.
errors: No runtime errors -- logic bug in rendering code for ITH/ITL broken-through state.
reproduction: Apply indicator to any chart. Find an ITH level. When a candle closes above the ITH with its body, the level should be visually invalidated.
started: Since initial implementation of liquidity detection.

## Eliminated

- hypothesis: check_liquidity_sweeps() complete break check (lines 1122-1129) is not executing
  evidence: Code structure and indentation is correct. The complete break block IS inside the for loop and does set is_valid=false when close > level for ITH/EQH and close < level for ITL/EQL. Detection logic is working.
  timestamp: 2026-04-12

## Evidence

- timestamp: 2026-04-12
  checked: check_liquidity_sweeps() function (lines 1100-1129)
  found: Complete break check at lines 1122-1129 correctly sets is_valid=false for ITH/ITL when body closes through. The detection is NOT broken.
  implication: Issue is downstream in rendering, not in detection.

- timestamp: 2026-04-12
  checked: render_liquidity_lines() ITH/ITL color logic (lines 2103-2105)
  found: ITH/ITL rendering only checks is_swept for color change (ternary on line 2104). Does NOT check is_valid. When is_valid=false but is_swept=false, ITH/ITL renders with active (non-grayed) color.
  implication: This is the visual root cause -- broken ITH/ITL looks identical to active ITH/ITL.

- timestamp: 2026-04-12
  checked: Skip/hide logic for mitigated levels (lines 2050-2060)
  found: The skip logic for swept/broken levels (is_swept or not is_valid) only applies to EQH/EQL types. ITH/ITL levels that are broken through are never skipped or hidden.
  implication: Even when user might expect broken ITH/ITL to be cleaned up, they persist as active-looking lines.

## Resolution

root_cause: Two rendering deficiencies in render_liquidity_lines(): (1) ITH/ITL color logic at line 2104 only checks is_swept, not is_valid, so body-close-through levels look active. (2) The skip/hide logic for mitigated levels at lines 2050-2060 only covers EQH/EQL, not ITH/ITL.
fix: Two rendering changes in render_liquidity_lines(): (1) ITH/ITL color logic now checks is_valid in addition to is_swept -- broken-through levels render as gray dotted lines. (2) Added skip/hide block for mitigated ITH/ITL levels (mirrors existing EQH/EQL skip logic) so broken ITH/ITL are hidden when i_show_swept_eqhl is off.
verification: confirmed fixed by user on TradingView (2026-04-13)
files_changed: [src/IFVG_Indicator.pine]
