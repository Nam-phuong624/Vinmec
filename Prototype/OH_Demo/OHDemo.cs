// Demo giao diện mô phỏng Patient Profile (Orion Health) + kịch bản tự động nhập PID -> xem hồ sơ -> Edit -> điền -> lưu.
// Toàn bộ dữ liệu là dữ liệu giả. Biên dịch bằng build.cmd (csc.exe có sẵn trong .NET Framework 4 của Windows).
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace OHDemo
{
    class Patient
    {
        public string Pid = "", Title = "", First = "", Middle = "", Last = "", Sex = "", Dob = "";
        public string PhoneType = "Di động", PhoneCountry = "+84 Việt Nam", PhoneArea = "", Phone = "";
        public string Nationality = "Việt Nam", Language = "Vietnamese", Ethnicity = "Không rõ", Occupation = "Unknown";
        public List<string> Addresses = new List<string>();
        public string FullName
        {
            get { return string.Join(" ", new[] { First, Middle, Last }.Where(s => s != "").ToArray()); }
        }
    }

    class MainForm : Form
    {
        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        static extern IntPtr SendMessage(IntPtr h, int m, IntPtr w, string l);
        [DllImport("user32.dll")]
        static extern bool SetProcessDPIAware();

        static readonly Font F = new Font("Segoe UI", 10f), FB = new Font("Segoe UI Semibold", 11f), FS = new Font("Segoe UI", 9f);
        static readonly Color Ink = Color.FromArgb(36, 48, 64), Grey = Color.FromArgb(110, 118, 130), Blue = Color.FromArgb(38, 103, 168);
        static readonly Color LineC = Color.FromArgb(214, 219, 226), Soft = Color.FromArgb(255, 236, 179), Navbg = Color.FromArgb(243, 245, 248);

        List<Patient> db = new List<Patient>();
        Patient cur;
        bool editing, demoRunning, stopDemo, nameConfirmed = true;
        List<string> draftAddr = new List<string>();
        string ethnicDraft = "";
        Panel addrPanel;                       // khung ô địa chỉ mở rộng ngay trong trang Edit (bấm +)
        List<Control> belowAddr = new List<Control>();
        bool addrOpen;
        int y;
        Dictionary<string, Control> f = new Dictionary<string, Control>();

        Panel body, avatar, headerPanel;
        Label nameLbl, infoLbl, status, addrInfo, ethnicTag, ageLbl, pageTitle;
        TextBox searchBox;
        Button editBtn, saveBtn, confirmedBtn, temporaryBtn, newBtn;
        bool newMode, resultMode;
        List<Patient> results = new List<Patient>();
        string lastQuery = "";
        ListView resultList;
        string notFound;      // != null: vừa tìm mà không có hồ sơ → để trống, không thông báo
        Panel bottomBar, tabsPanel;
        int pidSeq;

        // Enter gửi vào ô tìm kiếm luôn kích hoạt tìm kiếm, kể cả khi ô chưa có tiêu điểm (RPA chạy nền gửi phím thẳng vào ô).
        protected override bool ProcessCmdKey(ref Message msg, Keys keyData)
        {
            if (keyData == Keys.Enter && searchBox != null && msg.HWnd == searchBox.Handle) { DoSearch(); return true; }
            return base.ProcessCmdKey(ref msg, keyData);
        }

        public MainForm(string[] args)
        {
            db.Add(new Patient { Pid = "DEMO0001", Title = "Ông", First = "Nguyễn", Middle = "Văn", Last = "Mẫu", Sex = "Nam", Dob = "15/02/1980", Phone = "0900000001" });
            db.Add(new Patient { Pid = "DEMO0002", Title = "Bà", First = "Trần", Middle = "Thị", Last = "Thử", Sex = "Nữ", Dob = "20/05/1990", Phone = "0900000002" });
            db.Add(new Patient { Pid = "DEMO0003", Title = "Ông", First = "Lê", Middle = "Minh", Last = "Giả", Sex = "Nam", Dob = "01/02/2000", Phone = "0900000003" });
            // Hai người trùng tên với DEMO0001 nhưng khác năm sinh và thông tin (để thử tìm theo tên).
            db.Add(new Patient { Pid = "DEMO0004", Title = "Ông", First = "Nguyễn", Middle = "Văn", Last = "Mẫu", Sex = "Nam", Dob = "03/09/1992", Phone = "0900000004", Addresses = new List<string> { "Thôn A, Xã B, Tỉnh Demo" } });
            db.Add(new Patient { Pid = "DEMO0005", Title = "Ông", First = "Nguyễn", Middle = "Văn", Last = "Mẫu", Sex = "Nam", Dob = "12/12/1975", Phone = "0900000005", Addresses = new List<string> { "5 Đường C, Phường D, Thành phố Demo" } });

            Text = "OH · Patient Profile — DEMO"; Font = F; ClientSize = new Size(1240, 820); MinimumSize = new Size(1000, 640);
            StartPosition = FormStartPosition.CenterScreen; BackColor = Color.White;

            // ---- vùng chính ----
            Panel main = new Panel { Dock = DockStyle.Fill };
            body = new Panel { Dock = DockStyle.Fill, AutoScroll = true, BackColor = Color.White, Name = "profile-body", AccessibleName = "Profile body" };
            Panel bottom = new Panel { Dock = DockStyle.Bottom, Height = 52, BackColor = Navbg };
            Panel tabs = new Panel { Dock = DockStyle.Top, Height = 44 };
            pageTitle = new Label { Text = "Patient Profile", Dock = DockStyle.Top, Height = 44, Font = new Font("Segoe UI", 15f), ForeColor = Ink, Padding = new Padding(20, 8, 0, 0) };
            headerPanel = new Panel { Dock = DockStyle.Top, Height = 78, BackColor = Color.White };
            bottomBar = bottom; tabsPanel = tabs;
            main.Controls.Add(body); main.Controls.Add(bottom); main.Controls.Add(tabs); main.Controls.Add(pageTitle); main.Controls.Add(headerPanel);

            avatar = new Panel { Left = 20, Top = 12, Width = 54, Height = 54 };
            avatar.Paint += delegate (object s, PaintEventArgs e)
            {
                e.Graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
                e.Graphics.FillEllipse(new SolidBrush(Color.FromArgb(56, 64, 76)), 0, 0, 52, 52);
                e.Graphics.FillEllipse(Brushes.White, 18, 11, 16, 16);
                e.Graphics.FillPie(Brushes.White, 11, 28, 30, 30, 180, 180);
            };
            nameLbl = new Label { Left = 86, Top = 12, AutoSize = false, Height = 30, Width = 700, Font = new Font("Segoe UI", 15f), ForeColor = Ink, Name = "header-name" };
            infoLbl = new Label { Left = 86, Top = 44, AutoSize = false, Height = 22, Width = 900, Font = FS, ForeColor = Grey, Name = "header-info" };
            headerPanel.Controls.Add(avatar); headerPanel.Controls.Add(nameLbl); headerPanel.Controls.Add(infoLbl);

            string[] tabNames = { "Demographics", "Circle of Care", "Financial" };
            for (int i = 0; i < 3; i++)
            {
                Button t = new Button { Text = tabNames[i], Left = 20 + i * 150, Top = 6, Width = 144, Height = 34, FlatStyle = FlatStyle.Flat, BackColor = i == 0 ? Color.White : Navbg, ForeColor = Ink };
                t.FlatAppearance.BorderColor = LineC;
                if (i > 0) t.Click += delegate { Say("Tab ngoài phạm vi demo."); };
                tabs.Controls.Add(t);
            }

            editBtn = Btn("edit-toggle", "Edit", 20, 8, 90); saveBtn = Btn("edit-save", "Save", 120, 8, 90);
            saveBtn.BackColor = Blue; saveBtn.ForeColor = Color.White; saveBtn.Visible = false;
            editBtn.Click += delegate { ToggleEdit(); };
            saveBtn.Click += delegate { Save(); };
            bottom.Controls.Add(editBtn); bottom.Controls.Add(saveBtn);
            string[] other = { "Notes", "Documents", "Functions ▾" };
            for (int i = 0; i < 3; i++)
            {
                Button b = Btn("footer-" + other[i].ToLower().Replace(" ▾", ""), other[i], 230 + i * 135, 8, 125);
                b.Click += delegate { Say("Chức năng ngoài phạm vi demo."); };
                bottom.Controls.Add(b);
            }

            // ---- thanh tìm kiếm (trên khung tên) ----
            Panel top = new Panel { Dock = DockStyle.Top, Height = 54, BackColor = Navbg };
            top.Controls.Add(new Label { Text = "Tìm hồ sơ", Left = 270, Top = 17, AutoSize = true, ForeColor = Grey });
            searchBox = new TextBox { Name = "pid-search", AccessibleName = "PID hoặc tên bệnh nhân", Left = 350, Top = 13, Width = 380, Height = 28 };
            searchBox.KeyDown += delegate (object s, KeyEventArgs e) { if (e.KeyCode == Keys.Enter) { e.SuppressKeyPress = true; DoSearch(); } };   // chỉ cần Enter để tìm
            newBtn = Btn("new-patient", "+ New Patient", 750, 11, 150);
            newBtn.Click += delegate { OpenNew(""); };
            top.Controls.Add(searchBox); top.Controls.Add(newBtn);
            searchBox.HandleCreated += delegate { SendMessage(searchBox.Handle, 0x1501, (IntPtr)1, "Nhập PID hoặc tên bệnh nhân"); };

            // Kịch bản tự động không còn nút trên giao diện: chạy bằng tham số dòng lệnh --demo=pid|name|new, nhấn Esc để dừng.
            KeyPreview = true;
            KeyDown += delegate (object s, KeyEventArgs e) { if (e.KeyCode == Keys.Escape) stopDemo = true; };
            Shown += delegate
            {
                string a = args.FirstOrDefault(x => x.StartsWith("--demo="));
                if (a == "--demo=pid") StartDemo(0); else if (a == "--demo=name") StartDemo(2); else if (a == "--demo=new") StartDemo(1);
            };

            status = new Label { Dock = DockStyle.Bottom, Height = 28, ForeColor = Grey, BackColor = Navbg, Padding = new Padding(10, 5, 0, 0), Name = "status" };

            Controls.Add(main); Controls.Add(BuildNav()); Controls.Add(status); Controls.Add(top);
            Render();
            Say("Sẵn sàng. Nhập PID để mở hồ sơ.");
        }

        // ================= điều hướng trái =================
        Control BuildNav()
        {
            FlowLayoutPanel nav = new FlowLayoutPanel { Dock = DockStyle.Left, Width = 280, FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoScroll = true, BackColor = Navbg, Name = "left-menu" };
            string[][] groups = {
                new[] { "REGISTRATION", "Patient Profile", "Visit Manager", "OPD Visit Registration", "Emergency Visit Registration", "Patient Queue", "Medical Record Requests" },
                new[] { "CASHIER", "Select Company", "Patient Billing", "Deposit and Refund", "Shift" },
                new[] { "ADMISSION", "Admission Management", "Request Admission", "Inpatient Admission", "Locate Patient", "Bed Schedule" },
                new[] { "DISCHARGE", "Discharge Planner", "Discharge Patient", "Discharge Workbench" },
                new[] { "TRANSFER", "Transfer" },
                new[] { "APPOINTMENTS", "Enterprise Scheduling", "Patient Appointments", "Work Schedule" },
                new[] { "VISIT", "Visit Browser", "Delete Visit", "Reopen Visit", "Visit Status Changes", "Bed Charges", "Add Document to Patient File" },
                new[] { "MAINTENANCE", "Move Charges", "Room Charge Set Maintenance" } };
            foreach (string[] g in groups)
            {
                FlowLayoutPanel items = new FlowLayoutPanel { FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoSize = true, Margin = new Padding(0) };
                for (int i = 1; i < g.Length; i++)
                {
                    string text = g[i];
                    Label l = new Label { Text = text, AutoSize = false, Width = 256, Height = 26, Padding = new Padding(16, 3, 0, 0), ForeColor = text == "Patient Profile" ? Blue : Ink, Cursor = Cursors.Hand, Margin = new Padding(0) };
                    if (text == "Patient Profile") l.Font = FB;
                    l.Click += delegate { Say(text == "Patient Profile" ? "Đang ở Patient Profile." : "“" + text + "” ngoài phạm vi demo."); };
                    items.Controls.Add(l);
                }
                Label head = new Label { Text = g[0] + "  ⌄", AutoSize = false, Width = 256, Height = 30, Padding = new Padding(8, 6, 0, 0), Font = FS, ForeColor = Grey, Cursor = Cursors.Hand, Margin = new Padding(0, 6, 0, 0) };
                head.Click += delegate { items.Visible = !items.Visible; };
                nav.Controls.Add(head); nav.Controls.Add(items);
            }
            return nav;
        }

        // ================= tiện ích dựng control =================
        Button Btn(string name, string text, int x, int yy, int w)
        {
            Button b = new Button { Name = name, AccessibleName = text, Text = text, Left = x, Top = yy, Width = w, Height = 32, FlatStyle = FlatStyle.Flat, BackColor = Color.White, ForeColor = Ink };
            b.FlatAppearance.BorderColor = LineC;
            return b;
        }

        Label Lbl(string text, int x, int yy, int w, Color c, Font font, ContentAlignment align, string name)
        {
            Label l = new Label { Text = text, Left = x, Top = yy, Width = w, Height = 28, ForeColor = c, Font = font, TextAlign = align };
            if (name != null) { l.Name = name; f[name] = l; }   // không đặt AccessibleName: để UIA đọc được chính nội dung nhãn
            body.Controls.Add(l);
            return l;
        }

        void Section(string title)
        {
            y += 10;
            Lbl(title + "  ⌄", 20, y, 500, Ink, FB, ContentAlignment.MiddleLeft, null);
            y += 32;
            body.Controls.Add(new Panel { Left = 20, Top = y, Width = 880, Height = 1, BackColor = LineC });
            y += 12;
        }

        void RowLabel(string text, bool required)
        {
            Lbl(text, 20, y, 222, Grey, F, ContentAlignment.MiddleRight, null);
            if (required) Lbl("*", 244, y - 2, 14, Color.Firebrick, F, ContentAlignment.MiddleLeft, null);
        }

        TextBox Tb(string name, string text, int x, int w, string cue)
        {
            TextBox t = new TextBox { Name = name, AccessibleName = name, Text = text, Left = x, Top = y, Width = w };
            body.Controls.Add(t); f[name] = t;
            if (cue != null) { IntPtr h = t.Handle; SendMessage(h, 0x1501, (IntPtr)1, cue); }
            return t;
        }

        ComboBox Cb(string name, string[] items, string sel, int x, int w)
        {
            ComboBox c = new ComboBox { Name = name, AccessibleName = name, DropDownStyle = ComboBoxStyle.DropDownList, Left = x, Top = y, Width = w };
            c.Items.AddRange(items);
            if (sel != null && c.Items.Contains(sel)) c.SelectedItem = sel;
            body.Controls.Add(c); f[name] = c;
            return c;
        }

        Button Small(string name, string text, int x, int w)
        {
            Button b = Btn(name, text, x, y - 1, w); b.Height = 30;
            body.Controls.Add(b); f[name] = b;
            return b;
        }

        // ================= vẽ trang =================
        void Render()
        {
            body.SuspendLayout();
            foreach (Control c in body.Controls.Cast<Control>().ToList()) { body.Controls.Remove(c); c.Dispose(); }
            // Xóa vị trí cuộn cũ trước khi đặt control mới, nếu không tọa độ Top bị cộng lệch theo offset cuộn.
            body.AutoScroll = false; body.AutoScrollPosition = new Point(0, 0); body.AutoScroll = true;
            f.Clear(); y = 8;
            // Giao diện tạo mới là một trang riêng: ẩn tiêu đề hồ sơ, tab Demographics và thanh Edit/Notes.
            headerPanel.Visible = pageTitle.Visible = tabsPanel.Visible = bottomBar.Visible = !(newMode || resultMode);
            if (resultMode)
            {
                RenderResults();
            }
            else if (newMode)
            {
                RenderNew();
            }
            else if (cur == null)
            {
                if (notFound != null) { nameLbl.Text = ""; infoLbl.Text = ""; }   // không có hồ sơ: để trống
                else
                {
                    nameLbl.Text = "Chưa chọn bệnh nhân"; infoLbl.Text = "Nhập PID hoặc tên vào ô tìm kiếm phía trên.";
                }
            }
            else
            {
                UpdateHeader();
                if (editing) RenderEdit(); else RenderView();
            }
            body.ResumeLayout();
            body.AutoScrollPosition = new Point(0, 0);
            if (IsHandleCreated) BeginInvoke(new Action(delegate { body.AutoScrollPosition = new Point(0, 0); }));
            editBtn.Enabled = cur != null && !newMode; editBtn.Text = editing ? "View" : "Edit"; saveBtn.Visible = editing;
        }

        // Khung tạo mới: tab nhỏ + khung viền + hàng "nhãn căn phải / ô nhập" (theo ảnh mẫu OPD Activity).
        // Chỉ nhập tên, năm sinh, số điện thoại; các trường còn lại để trống, hoàn thiện sau ở bước Edit.
        void RenderNew()
        {
            Label tab = new Label { Text = "New Patient", Left = 10, Top = 8, Width = 130, Height = 30, TextAlign = ContentAlignment.MiddleCenter, BackColor = Color.White, ForeColor = Ink, BorderStyle = BorderStyle.FixedSingle };
            Panel frame = new Panel { Left = 10, Top = 37, Width = Math.Max(880, body.ClientSize.Width - 20), Height = 250, BackColor = Color.FromArgb(247, 248, 249), BorderStyle = BorderStyle.FixedSingle, Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right };
            body.Controls.Add(frame); body.Controls.Add(tab); tab.BringToFront();
            y = 58;
            RowLabel("Name", true);
            Tb("new-first", newFirst, 262, 150, "First Name"); Tb("new-middle", newMiddle, 420, 150, "Middle Name(s)"); Tb("new-last", newLast, 578, 150, "Last Name");
            y += 44;
            RowLabel("Year of Birth", true); Tb("new-year", "", 262, 100, "yyyy"); ((TextBox)f["new-year"]).MaxLength = 4; y += 44;
            RowLabel("Phone Number", true);
            Cb("new-phone-type", new[] { "Di động", "Nhà", "Cơ quan" }, "Di động", 262, 110);
            Cb("new-phone-country", new[] { "+84 Việt Nam", "+1 United States" }, "+84 Việt Nam", 380, 170);
            Tb("new-phone", "", 558, 170, null); y += 52;
            Button save = Btn("new-save", "Save", 262, y, 100); save.BackColor = Blue; save.ForeColor = Color.White;
            Button cancel = Btn("new-cancel", "Cancel", 372, y, 100);
            body.Controls.Add(save); body.Controls.Add(cancel); f["new-save"] = save; f["new-cancel"] = cancel;
            save.Click += delegate { CreatePatient(); }; cancel.Click += delegate { newMode = false; Render(); Say("Đã hủy tạo mới."); };
            Lbl("Sau khi Save, hệ thống cấp PID; các trường khác để trống và được bổ sung ở bước Edit.", 490, y, 400, Grey, new Font("Segoe UI", 9f, FontStyle.Italic), ContentAlignment.MiddleLeft, null);
            ((Label)body.Controls[body.Controls.Count - 1]).Height = 40;
            foreach (Control c in body.Controls) if (c is Label && c != tab && c.Top >= 50 && c.Top < 290) c.BackColor = frame.BackColor;
            frame.SendToBack();   // Controls.Add xếp control sau ở lớp dưới; đưa khung viền xuống đáy để không che các ô nhập
            y = 310;
        }

        // Danh sách kết quả tìm theo tên: nhiều người có thể trùng tên, phân biệt bằng năm sinh / SĐT / địa chỉ.
        void RenderResults()
        {
            Label tab = new Label { Text = "Search Results", Left = 10, Top = 8, Width = 140, Height = 30, TextAlign = ContentAlignment.MiddleCenter, BackColor = Color.White, ForeColor = Ink, BorderStyle = BorderStyle.FixedSingle };
            resultList = new ListView { Name = "search-results", AccessibleName = "Kết quả tìm kiếm", View = View.Details, FullRowSelect = true, GridLines = true, MultiSelect = false, HideSelection = false,
                Left = 10, Top = 37, Width = Math.Max(880, body.ClientSize.Width - 20), Height = 64 + 32 * Math.Max(4, results.Count), Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right };
            string[] cols = { "PID", "Name", "Sex", "Date of Birth", "Age", "Phone", "Address" };
            int[] widths = { 110, 230, 70, 130, 60, 130, 320 };
            for (int i = 0; i < cols.Length; i++) resultList.Columns.Add(cols[i], widths[i]);
            foreach (Patient p in results)
            {
                int a = Age(p.Dob);
                ListViewItem it = new ListViewItem(new[] { p.Pid, p.FullName, p.Sex, p.Dob, a >= 0 ? a + " y" : "", p.Phone, string.Join("; ", p.Addresses.ToArray()) }) { Tag = p };
                resultList.Items.Add(it);
            }
            body.Controls.Add(resultList); f["search-results"] = resultList; body.Controls.Add(tab); tab.BringToFront();
            int by = 37 + resultList.Height + 12;
            Label info = new Label { Left = 10, Top = by, Width = 900, Height = 26, ForeColor = Grey, Text = results.Count + " kết quả cho “" + lastQuery + "”. Phân biệt bằng năm sinh, SĐT, địa chỉ rồi chọn đúng người." };
            Button open = Btn("results-open", "Open", 10, by + 34, 100); open.BackColor = Blue; open.ForeColor = Color.White;
            Button cancel = Btn("results-cancel", "Cancel", 120, by + 34, 100);
            body.Controls.Add(info); body.Controls.Add(open); body.Controls.Add(cancel); f["results-open"] = open; f["results-cancel"] = cancel;
            open.Click += delegate { OpenSelected(); };
            cancel.Click += delegate { resultMode = false; notFound = ""; Render(); Say(""); };
            resultList.DoubleClick += delegate { OpenSelected(); };
            if (resultList.Items.Count > 0) resultList.Items[0].Selected = true;
        }

        void OpenSelected()
        {
            if (resultList == null || resultList.SelectedItems.Count == 0) { Say("Chọn một dòng trong danh sách."); return; }
            Open((Patient)resultList.SelectedItems[0].Tag);
        }

        string newFirst = "", newMiddle = "", newLast = "";

        void OpenNew(string prefill)
        {
            if (editing && !ConfirmLeave()) return;
            newFirst = newMiddle = newLast = "";
            string[] tk = (prefill ?? "").Trim().Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
            if (tk.Length >= 2) { newFirst = tk[0]; newLast = tk[tk.Length - 1]; newMiddle = string.Join(" ", tk.Skip(1).Take(tk.Length - 2).ToArray()); }
            cur = null; editing = false; newMode = true; resultMode = false; notFound = null; Render();
            Say("Nhập tên, năm sinh, số điện thoại rồi Save để cấp PID.");
        }

        void CreatePatient()
        {
            string first = T("new-first"), mid = T("new-middle"), last = T("new-last"), year = T("new-year"), phone = T("new-phone");
            string err = null;
            if (first == "" || last == "") err = "Nhập họ và tên.";
            else if (year.Length != 4 || Age(year) < 0 || Age(year) > 120) err = "Năm sinh phải gồm 4 chữ số hợp lệ.";
            else if (phone.Length < 8 || phone.Any(ch => !char.IsDigit(ch))) err = "Số điện thoại chỉ gồm chữ số (tối thiểu 8).";
            if (err != null) { Say("Chưa lưu · " + err); return; }
            Patient dup = db.FirstOrDefault(p => p.Phone == phone && Fold(p.FullName) == Fold(first + " " + mid + " " + last).Replace("  ", " "));
            if (dup != null && !demoRunning && MessageBox.Show(this, "Có thể trùng với " + dup.Pid + " · " + dup.FullName + ". Vẫn tạo mới?", "Kiểm tra trùng", MessageBoxButtons.YesNo) != DialogResult.Yes) return;
            pidSeq++;
            Patient p2 = new Patient { Pid = "NEW" + pidSeq.ToString("D6"), First = first, Middle = mid, Last = last, Dob = year, PhoneType = C("new-phone-type"), PhoneCountry = C("new-phone-country"), Phone = phone, Nationality = "", Language = "", Ethnicity = "", Occupation = "" };
            db.Add(p2);
            newMode = false; cur = p2; editing = true; draftAddr = new List<string>(); nameConfirmed = true; Render();
            Say("Đã cấp PID " + p2.Pid + ". Các trường còn lại đang trống — hoàn thiện rồi bấm Save.");
        }

        int Age(string dob)
        {
            DateTime d;
            int yr;
            if (dob != null && dob.Length == 4 && int.TryParse(dob, out yr) && yr >= 1900 && yr <= DateTime.Today.Year) return DateTime.Today.Year - yr;
            if (!DateTime.TryParseExact(dob, "dd/MM/yyyy", CultureInfo.InvariantCulture, DateTimeStyles.None, out d)) return -1;
            int a = DateTime.Today.Year - d.Year; if (d.Date > DateTime.Today.AddYears(-a)) a--; return a;
        }

        void UpdateHeader()
        {
            nameLbl.Text = cur.FullName;
            int a = Age(cur.Dob);
            infoLbl.Text = "BORN " + cur.Dob + (a >= 0 ? " (" + a + " y)" : "") + "   |   SEX " + cur.Sex + "   |   HN " + cur.Pid;
        }

        void ViewRow(string label, bool req, string value, string name)
        {
            RowLabel(label, req);
            Lbl(string.IsNullOrWhiteSpace(value) ? "–" : value, 262, y, 600, Ink, F, ContentAlignment.MiddleLeft, name);
            y += 38;
        }

        void RenderView()
        {
            Patient p = cur;
            Section("Identification Details");
            ViewRow("Hospital Number", false, p.Pid, "view-pid");
            ViewRow("Name (Local)", true, ((p.Title + " " + p.FullName).Trim()), "view-name");
            ViewRow("Name (Other)", true, "", "view-name-other");
            ViewRow("Sex", true, p.Sex, "view-sex");
            ViewRow("Date of Birth", true, p.Dob, "view-dob");
            ViewRow("Official Documents", false, "", "view-docs");
            ViewRow("Banner Indicators", false, "", "view-banner");
            Section("Contact Details");
            ViewRow("Phone Numbers", true, p.Phone == "" ? "" : p.PhoneType + "  " + p.PhoneCountry.Split(' ')[0] + " " + p.PhoneArea + " " + p.Phone, "view-phone");
            ViewRow("Email Addresses", false, "Unspecified", "view-email");
            ViewRow("Addresses", true, string.Join("; ", p.Addresses.ToArray()), "view-addresses");
            Section("Personal Details");
            ViewRow("Nationality", true, p.Nationality, "view-nationality");
            ViewRow("Primary Language", true, p.Language, "view-language");
            ViewRow("Ethnicity", true, p.Ethnicity, "view-ethnicity");
            ViewRow("Occupation", true, p.Occupation, "view-occupation");
            Section("Employment Details");
            y += 20;
        }

        void NameRow(string label, string pre, string title, string first, string mid, string last, bool other)
        {
            RowLabel(label, true);
            Cb(pre + "-title", new[] { "", "Ông", "Bà", "Anh", "Chị", "Bé" }, title, 262, 130);
            Tb(pre + "-first", first, 400, 140, other ? "First Name" : null);
            Tb(pre + "-middle", mid, 548, 140, other ? "Middle Name(s)" : null);
            Tb(pre + "-last", last, 696, 140, other ? "Last Name" : null);
            Small(pre + "-more", "…", 844, 30);
            y += 44;
        }

        void RenderEdit()
        {
            Patient p = cur;
            Section("Identification Details");
            RowLabel("Hospital Number", false); Lbl(p.Pid, 262, y, 300, Ink, F, ContentAlignment.MiddleLeft, "edit-pid"); y += 40;
            NameRow("Name (Local)", "edit-local", p.Title, p.First, p.Middle, p.Last, false);
            NameRow("Name (Other)", "edit-other", "", "", "", "", true);
            RowLabel("Name Status", false);
            confirmedBtn = Small("edit-name-confirmed", "Confirmed", 262, 110); temporaryBtn = Small("edit-name-temporary", "Temporary", 376, 120);
            confirmedBtn.Click += delegate { nameConfirmed = true; StyleStatus(); }; temporaryBtn.Click += delegate { nameConfirmed = false; StyleStatus(); };
            StyleStatus(); y += 40;
            RowLabel("Other Names", false); Small("edit-other-names", "…", 262, 34); y += 40;
            RowLabel("Sex", true); Cb("edit-sex", new[] { "Nam", "Nữ", "Khác" }, p.Sex, 262, 300); y += 40;
            RowLabel("Date of Birth", true);
            Cb("edit-dob-precision", new[] { "Year, Month and Day", "Year only" }, p.Dob.Length == 4 ? "Year only" : "Year, Month and Day", 262, 190);
            TextBox dob = Tb("edit-dob", p.Dob, 462, 150, null);
            ageLbl = Lbl("", 630, y, 120, Grey, F, ContentAlignment.MiddleLeft, "edit-age");
            dob.TextChanged += delegate { int a = Age(dob.Text); ageLbl.Text = a >= 0 ? "Age  " + a + " y" : "Age  –"; };
            { int a0 = Age(p.Dob); ageLbl.Text = a0 >= 0 ? "Age  " + a0 + " y" : "Age  –"; }
            y += 40;
            RowLabel("Official Documents", false); Small("edit-add-document", "+", 262, 34);
            Lbl("Add one or more official documents.", 306, y, 400, Grey, new Font("Segoe UI", 10f, FontStyle.Italic), ContentAlignment.MiddleLeft, null); y += 40;
            RowLabel("Banner Indicators", false); Cb("edit-banner", new[] { "" }, null, 262, 300); y += 40;

            Section("Contact Details");
            RowLabel("Phone Numbers", true);
            Cb("edit-phone-type", new[] { "Di động", "Nhà", "Cơ quan" }, p.PhoneType, 262, 110);
            Cb("edit-phone-country", new[] { "+84 Việt Nam", "+1 United States" }, p.PhoneCountry, 380, 170);
            Tb("edit-phone-area", p.PhoneArea, 558, 70, "Area");
            Tb("edit-phone", p.Phone, 636, 160, null);
            y += 38;
            Small("edit-add-phone", "+", 262, 34).Click += delegate { Say("Demo chỉ hỗ trợ một số điện thoại."); };
            Lbl("Click + to add new phone number.", 306, y, 400, Grey, new Font("Segoe UI", 10f, FontStyle.Italic), ContentAlignment.MiddleLeft, null); y += 40;
            RowLabel("Email Addresses", false); Small("edit-add-email", "+", 262, 34);
            Lbl("Unspecified", 306, y, 120, Ink, F, ContentAlignment.MiddleLeft, null);
            Lbl("Click + to add new email address.", 440, y, 400, Grey, new Font("Segoe UI", 10f, FontStyle.Italic), ContentAlignment.MiddleLeft, null); y += 40;
            RowLabel("Addresses", true);
            Small("edit-add-address", "+", 262, 34).Click += delegate { SetAddressOpen(!addrOpen); };
            body.Controls.Add(new CheckBox { Name = "edit-address-temporary", Text = "Temporary", Left = 306, Top = y, Width = 110 });
            addrInfo = Lbl("", 420, y, 480, Grey, new Font("Segoe UI", 10f, FontStyle.Italic), ContentAlignment.MiddleLeft, "edit-address-info");
            addrInfo.AutoSize = false; addrInfo.Height = 28;
            RefreshAddr(); y += 44;
            BuildAddressPanel(y);
            int belowStart = body.Controls.Count;   // mọi control từ đây trở xuống sẽ dời xuống khi khung địa chỉ mở

            Section("Personal Details");
            RowLabel("Nationality", true); Cb("edit-nationality", new[] { "Việt Nam", "Khác" }, p.Nationality, 262, 300); y += 40;
            RowLabel("Primary Language", true); Cb("edit-language", new[] { "Vietnamese", "English" }, p.Language, 262, 300); y += 40;
            RowLabel("Ethnicity", true);
            ethnicDraft = p.Ethnicity;
            ComboBox eth = Cb("edit-ethnicity", new[] { "Kinh", "Tày", "Thái", "Mường", "Hoa", "Không rõ" }, null, 262, 300);
            ethnicTag = Lbl(ethnicDraft == "" ? "(chưa chọn)" : ethnicDraft + "  ×", 574, y, 160, Ink, F, ContentAlignment.MiddleCenter, "edit-ethnicity-tag");
            ethnicTag.BackColor = Color.FromArgb(232, 236, 241);
            eth.SelectedIndexChanged += delegate { if (eth.SelectedItem != null) { ethnicDraft = (string)eth.SelectedItem; ethnicTag.Text = ethnicDraft + "  ×"; } };
            ethnicTag.Click += delegate { ethnicDraft = "Không rõ"; ethnicTag.Text = ethnicDraft + "  ×"; };
            y += 40;
            RowLabel("Occupation", true);
            Cb("edit-occupation", new[] { "Unknown", "Nhân viên văn phòng", "Công nhân", "Nông dân", "Giáo viên", "Hưu trí" }, p.Occupation, 262, 300); y += 40;
            Section("Employment Details");
            y += 20;
            belowAddr = body.Controls.Cast<Control>().Skip(belowStart).ToList();
        }

        void StyleStatus()
        {
            confirmedBtn.BackColor = nameConfirmed ? Color.FromArgb(222, 235, 250) : Color.White;
            temporaryBtn.BackColor = nameConfirmed ? Color.White : Color.FromArgb(255, 236, 179);
        }

        void RefreshAddr()
        {
            if (addrInfo == null) return;
            addrInfo.Text = draftAddr.Count == 0 ? "Add one or more addresses." : string.Join("; ", draftAddr.ToArray());
        }

        // ================= nghiệp vụ =================
        static string Fold(string s)
        {
            string n = (s ?? "").ToLowerInvariant().Replace('đ', 'd').Normalize(NormalizationForm.FormD);
            StringBuilder sb = new StringBuilder();
            foreach (char c in n) if (CharUnicodeInfo.GetUnicodeCategory(c) != UnicodeCategory.NonSpacingMark) sb.Append(c);
            return sb.ToString().Trim();
        }

        void Say(string text) { status.Text = text; }

        void DoSearch()
        {
            string q = searchBox.Text.Trim();
            if (q == "") { Say("Nhập PID hoặc tên bệnh nhân."); return; }
            if (editing && !ConfirmLeave()) return;
            Patient exact = db.FirstOrDefault(p => string.Equals(p.Pid, q, StringComparison.OrdinalIgnoreCase));
            List<Patient> hits = exact != null ? new List<Patient> { exact } : db.Where(p => Fold(p.FullName).Contains(Fold(q))).ToList();
            newMode = false; resultMode = false;
            if (hits.Count == 0) { cur = null; editing = false; notFound = q; Render(); Say(""); return; }   // không thông báo, để trống
            if (exact != null) { Open(exact); return; }                                                     // đúng PID → mở thẳng
            // Tìm theo tên: luôn hiện danh sách (kể cả 1 kết quả) để nhân viên đối chiếu năm sinh/thông tin.
            cur = null; editing = false; notFound = null; results = hits; lastQuery = q; resultMode = true; Render();
            Say(hits.Count + " kết quả. Chọn đúng bệnh nhân rồi bấm Open (hoặc nhấp đúp).");
        }

        bool ConfirmLeave()
        {
            return demoRunning || !IsDirty() || MessageBox.Show(this, "Bỏ các thay đổi chưa lưu?", "Patient Profile", MessageBoxButtons.YesNo) == DialogResult.Yes;
        }

        // Chỉ coi là "có thay đổi" khi giá trị trên form Edit khác hồ sơ đang lưu.
        bool IsDirty()
        {
            if (!editing || cur == null || !f.ContainsKey("edit-local-first")) return false;
            Patient p = cur;
            return C("edit-local-title") != p.Title || T("edit-local-first") != p.First || T("edit-local-middle") != p.Middle || T("edit-local-last") != p.Last
                || C("edit-sex") != p.Sex || T("edit-dob") != p.Dob || C("edit-phone-type") != p.PhoneType || C("edit-phone-country") != p.PhoneCountry
                || T("edit-phone-area") != p.PhoneArea || T("edit-phone") != p.Phone || C("edit-nationality") != p.Nationality || C("edit-language") != p.Language
                || C("edit-occupation") != p.Occupation || ethnicDraft != p.Ethnicity || !draftAddr.SequenceEqual(p.Addresses);
        }

        void Open(Patient p)
        {
            cur = p; editing = false; newMode = false; resultMode = false; notFound = null; Render();
            Say("Đã mở hồ sơ " + p.Pid + ". Bấm Edit để chỉnh sửa.");
        }

        void ToggleEdit()
        {
            if (cur == null) return;
            if (!editing) { editing = true; draftAddr = new List<string>(cur.Addresses); nameConfirmed = true; Render(); Say("Chế độ chỉnh sửa. Bấm Save để lưu hoặc View để bỏ thay đổi."); }
            else { if (!ConfirmLeave()) return; editing = false; Render(); Say("Không lưu thay đổi."); }
        }

        string T(string name) { return ((TextBox)f[name]).Text.Trim(); }
        string C(string name) { return ((ComboBox)f[name]).SelectedItem as string ?? ""; }

        void Save()
        {
            if (!editing || cur == null) return;
            string err = null;
            if (T("edit-local-first") == "" || T("edit-local-last") == "") err = "Thiếu tên (Local).";
            else if (C("edit-sex") == "") err = "Chưa chọn Sex.";
            else if (C("edit-dob-precision") == "Year only" ? (T("edit-dob").Length != 4 || Age(T("edit-dob")) < 0) : (T("edit-dob").Length != 10 || Age(T("edit-dob")) < 0))
                err = C("edit-dob-precision") == "Year only" ? "Date of Birth (Year only) phải là năm 4 chữ số." : "Date of Birth phải theo dạng dd/mm/yyyy.";
            else if (T("edit-phone") == "") err = "Thiếu số điện thoại.";
            if (err != null) { Say("Chưa lưu · " + err); return; }
            Patient p = cur;
            p.Title = C("edit-local-title"); p.First = T("edit-local-first"); p.Middle = T("edit-local-middle"); p.Last = T("edit-local-last");
            p.Sex = C("edit-sex"); p.Dob = T("edit-dob");
            p.PhoneType = C("edit-phone-type"); p.PhoneCountry = C("edit-phone-country"); p.PhoneArea = T("edit-phone-area"); p.Phone = T("edit-phone");
            p.Nationality = C("edit-nationality"); p.Language = C("edit-language"); p.Ethnicity = ethnicDraft; p.Occupation = C("edit-occupation");
            p.Addresses = new List<string>(draftAddr);
            editing = false; Render();
            Say("Đã lưu hồ sơ " + p.Pid + ".");
        }

        // Bấm "+" ở Addresses: các ô nhập mở rộng ngay bên dưới (không tạo cửa sổ mới); các mục phía dưới dời xuống.
        void BuildAddressPanel(int top)
        {
            addrOpen = false;
            addrPanel = new Panel { Name = "edit-address-panel", Left = 262, Top = top - 4, Width = 640, Height = 168, BackColor = Color.FromArgb(247, 248, 249), BorderStyle = BorderStyle.FixedSingle, Visible = false };
            string[] names = { "edit-address-province", "edit-address-ward", "edit-address-street" };
            string[] labels = { "Tỉnh / Thành phố", "Phường / Xã", "Số nhà / Đường / Thôn" };
            int[][] pos = { new[] { 12, 8, 280 }, new[] { 318, 8, 300 }, new[] { 12, 66, 606 } };
            for (int i = 0; i < 3; i++)
            {
                addrPanel.Controls.Add(new Label { Text = labels[i], Left = pos[i][0], Top = pos[i][1], Width = pos[i][2], Height = 20, ForeColor = Grey });
                TextBox tb = new TextBox { Name = names[i], AccessibleName = names[i], Left = pos[i][0], Top = pos[i][1] + 22, Width = pos[i][2], MaxLength = 250 };
                addrPanel.Controls.Add(tb); f[names[i]] = tb;
            }
            Button add = Btn("edit-address-add", "Add", 12, 124, 100), cancel = Btn("edit-address-cancel", "Cancel", 122, 124, 100);
            add.BackColor = Blue; add.ForeColor = Color.White;
            add.Click += delegate { ApplyAddress(); }; cancel.Click += delegate { SetAddressOpen(false); };
            addrPanel.Controls.Add(add); addrPanel.Controls.Add(cancel); f["edit-address-add"] = add; f["edit-address-cancel"] = cancel;
            body.Controls.Add(addrPanel); f["edit-address-panel"] = addrPanel;
        }

        void SetAddressOpen(bool open)
        {
            if (addrPanel == null || open == addrOpen) return;
            addrOpen = open;
            int delta = addrPanel.Height + 8;
            // Control đang ẩn không được cập nhật vị trí khi trang cuộn: đặt lại ngay dưới nút "+" trước khi hiện.
            if (open) addrPanel.Top = f["edit-add-address"].Bottom + 6;
            addrPanel.Visible = open;
            foreach (Control c in belowAddr) c.Top += open ? delta : -delta;
        }

        void ApplyAddress()
        {
            string province = T("edit-address-province"), ward = T("edit-address-ward"), street = T("edit-address-street");
            if (province == "" || street == "") { Say("Nhập Tỉnh/Thành phố và Số nhà/Đường (Phường/Xã có thể trống)."); return; }
            draftAddr.Add(string.Join(", ", new[] { street, ward, province }.Where(s => s != "").ToArray()));
            RefreshAddr();
            foreach (string n in new[] { "edit-address-province", "edit-address-ward", "edit-address-street" }) ((TextBox)f[n]).Clear();
            SetAddressOpen(false);
        }

        // ================= kịch bản demo tự động =================
        async Task D(int ms)
        {
            if (stopDemo) throw new OperationCanceledException();
            await Task.Delay(ms);
            if (stopDemo) throw new OperationCanceledException();
        }

        async Task Step(string text, int pause)
        {
            Say(text); await D(pause);
        }

        async Task Mark(Control c)
        {
            Color old = c.BackColor; c.BackColor = Soft; await D(450); c.BackColor = old;
        }

        async Task TypeInto(TextBox t, string text)
        {
            await Mark(t); t.Focus(); t.Clear();
            foreach (char ch in text) { t.AppendText(ch.ToString()); await D(85); }
            await D(300);
        }

        async Task Press(Button b)
        {
            await Mark(b); b.PerformClick(); await D(500);
        }

        async void StartDemo(int mode)
        {
            if (demoRunning) return;
            demoRunning = true; stopDemo = false;
            try { if (mode == 1) await RunDemoNew(); else if (mode == 2) await RunDemoName(); else await RunDemo(); }
            catch (OperationCanceledException) { Say("Đã dừng demo."); }
            catch (Exception ex) { Say("Demo lỗi: " + ex.Message); }
            finally
            {
                demoRunning = false;
            }
        }

        // Kịch bản 3: tìm theo tên → ra nhiều người trùng tên khác năm sinh → chọn đúng người → mở hồ sơ.
        async Task RunDemoName()
        {
            editing = false; newMode = false; resultMode = false; notFound = null; cur = null; searchBox.Clear(); Render();
            await Step("Bước 1/4 · Tìm theo tên — có nhiều người trùng tên", 700);
            await TypeInto(searchBox, "Nguyễn Văn Mẫu");
            await D(400); DoSearch(); await D(1200);
            await Step("Bước 2/4 · Cùng tên nhưng khác năm sinh, SĐT, địa chỉ", 2800);
            await Step("Bước 3/4 · Chọn đúng người (sinh năm 1992)", 400);
            ListViewItem target = resultList.Items.Cast<ListViewItem>().First(it => it.SubItems[3].Text.EndsWith("1992"));
            Color oldBack = target.BackColor; target.BackColor = Soft; await D(500);
            target.Selected = true; target.EnsureVisible(); resultList.Focus(); await D(1000); target.BackColor = oldBack;
            await Step("Bước 4/4 · Bấm Open để mở hồ sơ", 400);
            await Press((Button)f["results-open"]);
            await D(1200);
            await Step("Hoàn tất · đã mở đúng hồ sơ " + (cur != null ? cur.Pid : "") + ".", 0);
        }

        async Task Pick(string name, string value)
        {
            await Mark(f[name]); ((ComboBox)f[name]).SelectedItem = value; await D(500);
        }

        // Kịch bản 2: PID không tồn tại -> tạo bệnh nhân mới (chỉ tên, năm sinh, SĐT) -> Save cấp PID -> bổ sung các trường còn trống.
        async Task RunDemoNew()
        {
            editing = false; newMode = false; resultMode = false; notFound = null; cur = null; searchBox.Clear(); Render();
            await Step("Bước 1/6 · Nhập PID — người này chưa có trong danh sách gói khám", 700);
            await TypeInto(searchBox, "DEMO0099");
            await D(400); DoSearch(); await D(1800);
            await Step("Bước 2/6 · Không có hồ sơ (để trống) → bấm + New Patient", 500);
            await Press(newBtn);
            await Step("Bước 3/6 · Chỉ nhập tên, năm sinh, số điện thoại", 500);
            await TypeInto((TextBox)f["new-first"], "Phạm");
            await TypeInto((TextBox)f["new-middle"], "Thị");
            await TypeInto((TextBox)f["new-last"], "Mới");
            await TypeInto((TextBox)f["new-year"], "1992");
            await TypeInto((TextBox)f["new-phone"], "0933445566");
            await Step("Bước 4/6 · Save → hệ thống cấp PID mới, các trường còn lại để trống", 400);
            await Press((Button)f["new-save"]);
            await D(1500);
            await Step("Bước 5/6 · Bổ sung các trường còn trống ở trang Edit", 500);
            await Pick("edit-local-title", "Bà");
            await Pick("edit-sex", "Nữ");
            await Pick("edit-dob-precision", "Year, Month and Day");
            await TypeInto((TextBox)f["edit-dob"], "10/08/1992");
            await Pick("edit-nationality", "Việt Nam");
            await Pick("edit-language", "Vietnamese");
            await Pick("edit-ethnicity", "Kinh");
            await Pick("edit-occupation", "Nhân viên văn phòng");
            await Press((Button)f["edit-add-address"]);
            await TypeInto((TextBox)f["edit-address-province"], "Thành phố Demo");
            await TypeInto((TextBox)f["edit-address-ward"], "Phường Mới");
            await TypeInto((TextBox)f["edit-address-street"], "12 Đường Demo");
            await Press((Button)f["edit-address-add"]);
            await Step("Bước 6/6 · Save hồ sơ", 400);
            await Press(saveBtn);
            await Step("Hoàn tất · đã tạo và hoàn thiện hồ sơ " + (cur != null ? cur.Pid : "") + ".", 0);
        }

        async Task RunDemo()
        {
            if (editing) { editing = false; }
            newMode = false; resultMode = false; notFound = null;
            cur = null; searchBox.Clear(); Render();
            await Step("Bước 1/7 · Nhập PID bệnh nhân vào ô tìm kiếm", 700);
            await TypeInto(searchBox, "DEMO0001");
            await Step("Bước 2/7 · Nhấn Enter để tìm hồ sơ", 500);
            await D(400); DoSearch(); await D(1200);
            await Step("Bước 3/7 · Hồ sơ đã mở (chế độ xem) — kiểm tra thông tin hiện có", 2200);
            await Step("Bước 4/7 · Bấm Edit để chỉnh sửa", 400);
            await Press(editBtn);
            await Step("Bước 5/7 · Điền số điện thoại và chọn dân tộc", 500);
            await TypeInto((TextBox)f["edit-phone"], "0912345678");
            await Mark(f["edit-ethnicity"]); ((ComboBox)f["edit-ethnicity"]).SelectedItem = "Kinh"; await D(700);
            await Step("Bước 6/7 · Thêm địa chỉ bằng nút +", 400);
            await Press((Button)f["edit-add-address"]);
            await TypeInto((TextBox)f["edit-address-province"], "Thành phố Demo");
            await TypeInto((TextBox)f["edit-address-ward"], "Phường Mới");
            await TypeInto((TextBox)f["edit-address-street"], "12 Đường Demo");
            await Press((Button)f["edit-address-add"]);
            await Step("Bước 7/7 · Bấm Save để lưu hồ sơ", 400);
            await Press(saveBtn);
            await Step("Hoàn tất · đã lưu hồ sơ DEMO0001 (xem lại ở chế độ View). Có thể chạy lại demo.", 0);
        }

        [STAThread]
        static void Main(string[] args)
        {
            try { SetProcessDPIAware(); } catch { }
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm(args));
        }
    }
}
