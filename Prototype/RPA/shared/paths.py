import os
import sys
from pathlib import Path

# Khi đóng gói bằng PyInstaller, ROOT là thư mục chứa file .exe; khi chạy từ mã nguồn là thư mục dự án RPA.
FROZEN = getattr(sys, 'frozen', False)
ROOT = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parents[1]
DEMO = ROOT / 'demo'
RUNTIME = ROOT / 'runtime'


def _find_ds_bung() -> Path:
    """Thư mục "ds bung" (mỗi ngày một thư mục con DD-MM-YYYY). Đặt DS_BUNG_DIR để chỉ định rõ;
    nếu không, tìm ở thư mục chứa chương trình và các thư mục cha gần nhất."""
    explicit = os.environ.get('DS_BUNG_DIR')
    if explicit:
        return Path(explicit)
    for base in [ROOT, *ROOT.parents[:4]]:
        if (base / 'ds bung').is_dir():
            return base / 'ds bung'
    return ROOT / 'ds bung'


DS_BUNG = _find_ds_bung()
