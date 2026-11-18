"""Browser adapter. Reads/writes OH exclusively through the rendered application."""
from dataclasses import dataclass
import json
from time import perf_counter
from threading import Event
from shared.identity import Identity, ReviewRequired, match_identity
from shared.paths import RUNTIME


@dataclass(frozen=True)
class Proposal:
    snapshot: dict
    identity: Identity
    row: dict
    match_ms: float


class BrowserRPA:
    def __init__(self, page):
        self.page = page
        self.page.set_default_timeout(5000)

    def snapshot(self):
        value = self.page.evaluate('window.ohSnapshot?.()')
        if not value or value['loading']:
            raise ReviewRequired('OH chưa mở hồ sơ hoặc đang tải. Mở đúng PID rồi thử lại.')
        return value

    def prepare(self, identity, rows, company, batch):
        started = perf_counter()
        snapshot = self.snapshot()
        if snapshot['locked'] or snapshot['dialogOpen']:
            raise ReviewRequired('OH đang khóa hoặc mở hộp thoại; kết thúc thao tác hiện tại trước.')
        if snapshot['record'] != snapshot['saved']:
            raise ReviewRequired('OH có thay đổi chưa lưu; lưu hoặc hủy trước khi đối chiếu.')
        row = match_identity(identity, rows, company, batch, snapshot['record'])
        return Proposal(snapshot, identity, row, (perf_counter() - started) * 1000)

    def check(self, proposal, cancelled=None, revision=None):
        if cancelled is not None and cancelled.is_set():
            raise ReviewRequired('Đã dừng. Kiểm tra dữ liệu đã điền một phần; chưa tự lưu.')
        now = self.snapshot()
        before = proposal.snapshot
        if now['viewId'] != before['viewId'] or now['record']['pid'] != before['record']['pid']:
            raise ReviewRequired('Hồ sơ đã đổi hoặc trang đã tải lại. Đối chiếu lại trước khi điền.')
        if now['saved']['version'] != before['saved']['version']:
            raise ReviewRequired('Phiên bản hồ sơ đã thay đổi; đối chiếu lại.')
        if revision is not None and now['revision'] != revision:
            raise ReviewRequired('OH đã bị sửa sau bản xem trước; đối chiếu lại.')
        return now

    def fill(self, proposal: Proposal, address: dict, confirmed: bool, cancelled: Event | None = None):
        if not confirmed:
            raise ReviewRequired('Cần xác nhận địa chỉ với khách trước khi điền.')
        address = {k: str(address.get(k, '')).strip() for k in ('province', 'ward', 'street')}
        if any(not v or len(v) > 250 for v in address.values()):
            raise ReviewRequired('Nhập đủ địa chỉ hợp lệ trước khi điền.')
        started = perf_counter()
        before = proposal.snapshot
        self.check(proposal, cancelled, before['revision'])
        expected_id = proposal.identity.national_id
        acquired = False
        try:
            self.page.locator('#lock-record').click()
            acquired = True
            self.check(proposal, cancelled, before['revision'])
            if not self.snapshot()['locked']:
                raise ReviewRequired('Không khóa được hồ sơ để điền.')
            if before['record']['national_id'] != expected_id:
                self.page.locator('#national-id').fill(expected_id)
            self.check(proposal, cancelled)
            if before['record']['address'] != address:
                self.page.locator('#edit-address').click()
                for key in ('province', 'ward', 'street'):
                    self.check(proposal, cancelled)
                    self.page.locator('#' + key).fill(address[key])
                self.check(proposal, cancelled)
                self.page.locator('#apply-address').click()
            actual = self.check(proposal, cancelled)['record']
            if actual['national_id'] != expected_id or actual['address'] != address:
                raise ReviewRequired('Đọc lại không khớp. Chưa lưu; kiểm tra các trường đã điền.')
            elapsed = (perf_counter() - started) * 1000 + proposal.match_ms
            self.audit('filled', elapsed_ms=round(elapsed, 1))
            return dict(pid=actual['pid'], national_id=expected_id, address=address,
                        version=before['saved']['version'], elapsed_ms=elapsed)
        finally:
            if acquired and not self.page.is_closed():
                # Stop is cooperative; close modal before unlocking a partially filled form.
                try:
                    current = self.snapshot()
                    if current['viewId'] == before['viewId'] and current['record']['pid'] == before['record']['pid']:
                        if current['dialogOpen']:
                            self.page.locator('#close-address').click()
                        if self.snapshot()['locked']:
                            self.page.locator('#lock-record').click()
                except Exception:
                    # Do not mask the original failure when the page was closed or navigated.
                    self.audit('unlock_unavailable')

    def verify_saved(self, pending):
        now = self.snapshot()
        if now['record']['pid'] != pending['pid']:
            raise ReviewRequired('Đã đổi hồ sơ trước khi xác minh lưu; lượt này chưa hoàn tất.')
        if now['saved']['version'] <= pending['version']:
            return False
        for key in ('national_id', 'address'):
            if now['saved'][key] != pending[key] or now['record'][key] != pending[key]:
                raise ReviewRequired('Thông tin lưu khác bản đã điền; kiểm tra lại.')
        # Reload UI to verify persistence, without a direct data request from RPA.
        self.page.reload()
        self.page.wait_for_function('window.ohSnapshot?.() && !window.ohSnapshot().loading')
        now = self.snapshot()
        if now['record']['pid'] != pending['pid'] or any(now['saved'][k] != pending[k] for k in ('national_id', 'address')):
            raise ReviewRequired('Mở lại hồ sơ không khớp dữ liệu dự kiến.')
        self.audit('saved_verified')
        return True

    @staticmethod
    def audit(event, **fields):
        RUNTIME.mkdir(exist_ok=True)
        with (RUNTIME / 'audit.jsonl').open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(event=event, **fields)) + '\n')
