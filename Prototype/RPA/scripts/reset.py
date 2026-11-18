from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
if sys.prefix == sys.base_prefix:
    sys.path.insert(0, str(ROOT/'.deps'))

if __name__ == '__main__':
    import ctypes
    if ctypes.windll.user32.FindWindowW(None,'OH Desktop · Tiếp đón — DEMO'):
        raise SystemExit('Close the running OH Desktop demo before resetting.')
    from scripts.generate_demo import main
    from oh_desktop.store import initialize
    main()
    initialize(reset=True)
    import re
    generated=ROOT/'runtime'/'prepared'
    for output in generated.glob('*.xlsx'):
        if re.fullmatch(r'[0-9a-f]{16}(\.pending)?\.xlsx',output.name):output.unlink()
    print('Restored 20 fictional patients. Data/ and OH_UI/ were not modified.')
