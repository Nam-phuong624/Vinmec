"""Windows UI Automation adapter. No DOM, API, IPC snapshot or DB access."""
from time import perf_counter, monotonic
from threading import Event
from pywinauto import Application
from pywinauto.timings import wait_until
import win32gui
import win32process
from shared.identity import ReviewRequired, match_identity, dob, normalized, visit_datetime
from rpa_tool.contracts import Proposal, audit


class DesktopRPA:
    def __init__(self, process_id: int, timeout=5):
        self.process_id=process_id
        self.timeout=timeout
        handle=self.find_window()
        self.app=Application(backend='uia').connect(handle=handle,timeout=timeout)
        self.window=self.app.window(handle=handle)
        self.handle=handle
        self.window.wait('visible',timeout=timeout)
        self.timeout=timeout
        self._controls={}
        self.cache_controls(self.window,self.handle)

    def cache_controls(self,parent,handle):
        for control in parent.wrapper_object().descendants():
            key=(handle,control.element_info.automation_id,control.element_info.control_type)
            # Descendant enumeration can cache visibility. Navigation groups
            # may later collapse, so subsequent checks must use current state.
            control.element_info.set_cache_strategy(False)
            self._controls[key]=control

    def find_window(self,title=None):
        found=[]
        def search():
            found.clear()
            def visit(handle,_):
                if (win32process.GetWindowThreadProcessId(handle)[1]==self.process_id
                    and win32gui.IsWindowVisible(handle)
                    and win32gui.GetClassName(handle).startswith('WindowsForms10.Window')
                    and (title is None or win32gui.GetWindowText(handle)==title)):
                    found.append(handle)
            win32gui.EnumWindows(visit,None)
            return bool(found)
        wait_until(self.timeout,.05,search)
        return found[0]

    def control(self, name, kind='Edit', parent=None):
        root=parent or self.window
        key=(self.handle if parent is None else root.handle,name,kind)
        if key in self._controls:
            return self._controls[key]
        control=root.child_window(auto_id=name,control_type=kind)
        control.wait('exists',timeout=self.timeout)
        wrapper=control.wrapper_object()
        self._controls[key]=wrapper
        return wrapper

    def read(self,name,parent=None):
        return self.control(name,parent=parent).get_value()

    def click(self,name,parent=None):
        # Modal handlers keep InvokePattern synchronous; queue the actual button
        # click on its HWND so the worker can continue operating the new dialog.
        control=self.control(name,'Button',parent)
        if not control.is_enabled():
            raise ReviewRequired('Thao tác OH đang bị khóa: '+name)
        if name in ('edit-address','new-record','browse-patients','nav-patient-list'):
            win32gui.PostMessage(control.handle,0x00F5,0,0)  # BM_CLICK
        else:
            control.invoke()

    def write(self,name,value,parent=None):
        self.control(name,parent=parent).set_edit_text(value)

    def snapshot(self):
        pid=self.read('pid')
        if not pid:
            raise ReviewRequired('OH chưa mở hồ sơ. Mở đúng PID rồi thử lại.')
        record={key:self.read(key) for key in ('pid','name','dob','sex','national_id','company','batch')}
        for key in ('package_code','package_name','visit_date','policy_code','policy_name','phone','nationality','address_original'):
            record[key]=self.read(key)
        record['address']={key:self.read(key) for key in ('province','ward','street')}
        try:
            version=int(self.read('version'))
        except ValueError as exc:
            raise ReviewRequired('Không đọc được phiên bản hồ sơ OH.') from exc
        record['version']=version
        state=self.read('save-state')
        dirty=state=='Có thay đổi chưa lưu'
        # The fingerprint is derived solely from values exposed by real visible controls.
        revision=(tuple(record[key] for key in ('pid','name','dob','sex','national_id','company','batch')),
                  tuple(record['address'].values()),state,self.read('session'))
        return dict(record=record,saved={'version':version},dirty=dirty,revision=revision,
                    viewId=(self.handle,self.read('session')),
                    locked=not self.control('pid-search').is_enabled())

    def open_pid(self,pid):
        self.write('pid-search',pid)
        previous=self.read('session')
        self.click('open-record')
        wait_until(self.timeout,.05,lambda:self.read('session')!=previous or not self.read('pid'))
        return self.snapshot()

    def prepare(self, identity, rows, company, batch):
        started=perf_counter();snapshot=self.snapshot()
        if snapshot['locked']:
            raise ReviewRequired('OH đang khóa hoặc mở hộp thoại; kết thúc thao tác hiện tại trước.')
        if snapshot['dirty']:
            raise ReviewRequired('OH có thay đổi chưa lưu; lưu hoặc hủy trước khi đối chiếu.')
        row=match_identity(identity,rows,company,batch,snapshot['record'])
        return Proposal(snapshot,identity,row,(perf_counter()-started)*1000)

    def check(self,proposal,cancelled=None,revision=None):
        if cancelled is not None and cancelled.is_set():
            raise ReviewRequired('Đã dừng. Kiểm tra dữ liệu đã điền một phần; chưa tự lưu.')
        now=self.snapshot();before=proposal.snapshot
        if now['viewId']!=before['viewId'] or now['record']['pid']!=before['record']['pid']:
            raise ReviewRequired('Hồ sơ đã đổi hoặc tải lại. Đối chiếu lại trước khi điền.')
        if now['saved']['version']!=before['saved']['version']:
            raise ReviewRequired('Phiên bản hồ sơ đã thay đổi; đối chiếu lại.')
        if revision is not None and now['revision']!=revision:
            raise ReviewRequired('OH đã bị sửa sau bản xem trước; đối chiếu lại.')
        return now

    def address_dialog(self):
        dialog=self.app.window(handle=self.find_window('OH · Cập nhật địa chỉ'))
        dialog.wait('visible',timeout=self.timeout)
        self.cache_controls(dialog,dialog.handle)
        return dialog

    def fill(self,proposal,address,confirmed,cancelled:Event|None=None):
        if not confirmed:
            raise ReviewRequired('Cần xác nhận địa chỉ với khách trước khi điền.')
        address={key:str(address.get(key,'')).strip() for key in ('province','ward','street')}
        if any(not value or len(value)>250 for value in address.values()):
            raise ReviewRequired('Nhập đủ địa chỉ hợp lệ trước khi điền.')
        started=perf_counter();before=proposal.snapshot;acquired=False;dialog=None
        self.check(proposal,cancelled,before['revision'])
        try:
            self.click('lock-record');acquired=True
            self.check(proposal,cancelled,before['revision'])
            if not self.snapshot()['locked']:
                raise ReviewRequired('Không khóa được hồ sơ để điền.')
            if before['record']['national_id']!=proposal.identity.national_id:
                self.write('national_id',proposal.identity.national_id)
            self.check(proposal,cancelled)
            if before['record']['address']!=address:
                # Invoke is non-blocking: the WinForms modal has its own message loop.
                self.click('edit-address')
                dialog=self.address_dialog()
                for key in ('province','ward','street'):
                    self.check(proposal,cancelled)
                    self.write('address-'+key,address[key],dialog)
                self.check(proposal,cancelled)
                dialog_handle=dialog.handle
                self.click('apply-address',dialog)
                wait_until(self.timeout,.05,lambda:not win32gui.IsWindow(dialog_handle));dialog=None
                self._controls={key:value for key,value in self._controls.items() if key[0]!=dialog_handle}
            actual=self.check(proposal,cancelled)['record']
            if actual['national_id']!=proposal.identity.national_id or actual['address']!=address:
                raise ReviewRequired('Đọc lại không khớp. Chưa lưu; kiểm tra dữ liệu đã điền.')
            elapsed=(perf_counter()-started)*1000+proposal.match_ms
            self.audit('desktop_filled',elapsed_ms=round(elapsed,1))
            return dict(pid=actual['pid'],national_id=actual['national_id'],address=address,
                        version=before['saved']['version'],elapsed_ms=elapsed)
        finally:
            if acquired:
                try:
                    if dialog is not None and dialog.exists():self.click('close-address',dialog)
                    current=self.snapshot()
                    if current['viewId']==before['viewId'] and current['locked']:
                        self.click('lock-record')
                except Exception:
                    self.audit('desktop_unlock_unavailable')

    def verify_saved(self,pending):
        now=self.snapshot()
        if now['record']['pid']!=pending['pid']:
            raise ReviewRequired('Đã đổi hồ sơ trước khi xác minh lưu; lượt này chưa hoàn tất.')
        if now['saved']['version']<=pending['version']:
            return False
        if now['dirty'] or any(now['record'][k]!=pending[k] for k in ('national_id','address')):
            raise ReviewRequired('Thông tin lưu khác bản đã điền; kiểm tra lại.')
        session=now['viewId']
        self.click('reload-record')
        wait_until(self.timeout,.05,lambda:self.snapshot()['viewId']!=session)
        now=self.snapshot()
        if now['record']['pid']!=pending['pid'] or any(now['record'][k]!=pending[k] for k in ('national_id','address')):
            raise ReviewRequired('Mở lại hồ sơ không khớp dữ liệu dự kiến.')
        self.audit('desktop_saved_verified');return True

    def fill_creation(self,row,cancelled=None):
        if row.get('blocked'):
            raise ReviewRequired('Dòng bị trùng định danh trong Excel; không tạo hồ sơ.')
        if row.get('pid'):
            raise ReviewRequired('Dòng đã có PID. Lần 1 chỉ tạo hồ sơ khách mới chưa có PID.')
        if self.read('save-state')=='Có thay đổi chưa lưu':
            raise ReviewRequired('Lưu hoặc hủy thay đổi trên OH trước khi tạo mới.')
        expected={key:str(row.get(key,'') or '') for key in ('name','national_id','dob','sex','phone','nationality',
                  'company','batch','policy_code','policy_name','package_code','package_name','visit_date')}
        expected['address_original']=row.get('address','')
        if not expected['package_code']:
            raise ReviewRequired('Cần mã gói khám cho lần 1.')
        expected['dob']=dob(expected['dob']);expected['visit_date']=visit_datetime(expected['visit_date'])
        handle=None
        def check_stop():
            if cancelled is not None and cancelled.is_set():
                raise ReviewRequired('Đã dừng lần 1. Chưa lưu hoặc cấp PID.')
            if handle and not win32gui.IsWindow(handle):
                raise ReviewRequired('Hộp tạo hồ sơ đã đóng; không tiếp tục điền.')
        try:
            check_stop();self.click('new-record')
            handle=self.find_window('OH · Tạo hồ sơ và bung gói khám')
            dialog=self.app.window(handle=handle);dialog.wait('visible',timeout=self.timeout)
            self.cache_controls(dialog,handle)
            for key,value in expected.items():
                check_stop();self.write('create-'+key,value,dialog)
            check_stop();self.click('create-check',dialog)
            existing=self.read('existing-pid',dialog)
            if existing:
                raise ReviewRequired('CCCD đã có hồ sơ PID '+existing+'. Không tạo trùng; kiểm tra hồ sơ có sẵn.')
            if not self.control('create-save','Button',dialog).is_enabled():
                raise ReviewRequired(self.read('create-status',dialog))
            for key,value in expected.items():
                if self.read('create-'+key,dialog)!=value:
                    raise ReviewRequired('Đọc lại dữ liệu tạo hồ sơ không khớp Excel.')
            check_stop();self.audit('preparation_filled')
            return dict(kind='creation',dialog_handle=handle,expected=expected,row=dict(row))
        except Exception:
            if handle and win32gui.IsWindow(handle):
                try:self.click('create-cancel',self.app.window(handle=handle))
                except Exception:self.audit('create_dialog_close_unavailable')
            if handle:self._controls={k:v for k,v in self._controls.items() if k[0]!=handle}
            raise

    def verify_creation(self,pending):
        if win32gui.IsWindow(pending['dialog_handle']):
            return None
        self._controls={k:v for k,v in self._controls.items() if k[0]!=pending['dialog_handle']}
        current=self.snapshot()
        def validate(record):
            for key,value in pending['expected'].items():
                actual=record.get(key,'')
                if key in ('dob','visit_date'):
                    normalizer=dob if key=='dob' else visit_datetime
                    if not actual or normalizer(actual)!=value:raise ReviewRequired('Ngày lưu khác Excel; chưa bàn giao PID.')
                elif (str(actual).strip()!=value if key in ('national_id','package_code','policy_code','phone')
                      else normalized(actual)!=normalized(value)):
                    raise ReviewRequired('Tạo mới đã hủy hoặc thông tin lưu khác Excel; chưa bàn giao PID.')
        validate(current['record'])
        if current['dirty']:
            raise ReviewRequired('Hồ sơ mới còn thay đổi chưa lưu; chưa bàn giao PID.')
        pid=current['record']['pid'];before=current['viewId']
        self.click('reload-record')
        wait_until(self.timeout,.05,lambda:self.snapshot()['viewId']!=before)
        reloaded=self.snapshot();validate(reloaded['record'])
        if reloaded['record']['pid']!=pid:
            raise ReviewRequired('PID thay đổi khi tải lại; kiểm tra thủ công.')
        self.audit('preparation_pid_verified')
        return dict(pending['row'],pid=pid)

    audit=staticmethod(audit)
