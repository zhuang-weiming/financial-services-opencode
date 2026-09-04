#!/usr/bin/env python3
"""
Fix czsc library for pure-Python fallback (reusable patch).

## 背景 (Background)

czsc 0.10.12's `core.py` has a version bug: when the `rs_czsc` Rust extension is
a stub (version "0.0.0-stub", installed without the compiled core classes), czsc
takes the `else` branch and tries `from rs_czsc import Operate, Freq, CZSC, ...`,
which fails with ImportError.

However, the **complete pure-Python implementation exists** in `czsc/py/`
(Operate, Freq, CZSC, RawBar, BarGenerator, etc.). The fix forces `check_rs_czsc()`
to return False when the stub is detected, so czsc uses the pure-Python path.

## 用法 (Usage)

```bash
python3 .opencode/skills/_shared/fix_czsc.py
# → patches site-packages/czsc/core.py in-place
```

## 验证 (Verify)

```bash
python3 -c "from czsc import CZSC, RawBar, Freq, Operate; print('OK')"
```

## 安全 (Safety)

- Backs up original to `core.py.bak_YYYYMMDD` before patching
- Idempotent: re-running on an already-patched file is a no-op
"""
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

SITE_PACKAGES = Path(
    __file__).resolve().parent.parent.parent.parent if False else None


def find_czsc_core():
    """Locate the czsc/core.py file in site-packages."""
    import czsc
    return Path(czsc.__file__).parent / "core.py"


def patch_core(core_path):
    """Patch czsc/core.py check_rs_czsc to return False on stub."""
    core_path = Path(core_path)
    original = core_path.read_text(encoding="utf-8")

    # Idempotency check: if already patched, no-op
    if "PATCHED_2026_09_01_FIX_CZSC" in original:
        print("  czsc/core.py already patched — no-op")
        return False

    backup = core_path.with_name(
        f"core.py.bak_{datetime.now().strftime('%Y%m%d')}")
    if not backup.exists():
        shutil.copy(core_path, backup)
        print(f"  Backup created: {backup}")

    marker = "PATCHED_2026_09_01_FIX_CZSC"
    new_check = '''def check_rs_czsc() -> Tuple[bool, Optional[str]]:
    """
    PATCHED_2026_09_01_FIX_CZSC: force pure-Python fallback.
    The rs_czsc Rust extension is a stub (0.0.0-stub) in this environment
    and does not provide Operate/Freq/CZSC etc. The pure-Python path in
    czsc/py/ has the complete implementation, so we return False here to
    force czsc to use it.
    """
    try:
        import rs_czsc
        version = getattr(rs_czsc, '__version__', 'unknown')
        # Validate that the Rust extension actually has the core classes.
        # A stub has only (Signal, WeightBacktest, daily_performance, top_drawdowns).
        required = ['Operate', 'Freq', 'CZSC', 'RawBar', 'BarGenerator']
        missing = [n for n in required if not hasattr(rs_czsc, n)]
        if missing:
            return False, f"rs_czsc stub detected (version={version}); missing: {missing}"
        return True, version
    except ImportError as e:
        return False, f"ImportError: {str(e)}"
    except Exception as e:
        return False, f"Error: {str(e)}"
'''

    if "def check_rs_czsc()" not in original:
        print(f"  ERROR: check_rs_czsc not found in {core_path}")
        return False

    # Replace from "def check_rs_czsc" to the line before "installed, rs_czsc_version"
    start = original.index("def check_rs_czsc")
    end = original.index("installed, rs_czsc_version")
    patched = original[:start] + new_check + "\n" + original[end:]
    core_path.write_text(patched, encoding="utf-8")
    print(f"  Patched: {core_path}")
    return True


def main():
    core_path = find_czsc_core()
    print(f"Found czsc/core.py at: {core_path}")
    changed = patch_core(core_path)

    # Verify
    print("\nVerifying import...")
    try:
        from czsc import CZSC, RawBar, Freq, Operate
        from czsc.py import BarGenerator
        print("  ✅ from czsc import CZSC, RawBar, Freq, Operate  OK")
        print("  ✅ from czsc.py import BarGenerator  OK")
        print(f"     Operate values: {[o.value for o in Operate]}")
        print("\n  czsc is READY for chanlun analysis.")
    except ImportError as e:
        print(f"  ❌ Import still fails: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
