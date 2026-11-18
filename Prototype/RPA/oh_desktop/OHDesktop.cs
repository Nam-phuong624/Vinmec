using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Text;
using System.Web.Script.Serialization;
using System.Windows.Forms;

namespace OHDesktop {
  public partial class PatientForm : Form {
    readonly Dictionary<string, TextBox> fields = new Dictionary<string, TextBox>();
    readonly JavaScriptSerializer json = new JavaScriptSerializer();
    readonly string python, root, database;
    Dictionary<string, object> saved;
    Button open, reload, cancel, save, locking, addressButton, newRecord;
    bool painting, locked;
    int reception;
    Panel body;
    TextBox localFirst,localMiddle,localLast,ageBox;
    TabControl profileTabs;

    static string Q(string value) { return "\"" + value.Replace("\"", "\\\"") + "\""; }
    string S(Dictionary<string,object> obj, string key) { return obj.ContainsKey(key) && obj[key]!=null ? Convert.ToString(obj[key]) : ""; }
    Dictionary<string,object> Copy(Dictionary<string,object> value) { return json.Deserialize<Dictionary<string,object>>(json.Serialize(value)); }
    TextBox Input(string id, bool readOnly) {
      TextBox input=new TextBox { Name=id, AccessibleName=id, ReadOnly=readOnly,
        Dock=DockStyle.Fill, BorderStyle=BorderStyle.FixedSingle, Font=new Font("Segoe UI",11),
        BackColor=readOnly ? Color.FromArgb(245,248,249) : Color.White, Margin=new Padding(0,3,14,5) };
      fields[id]=input; return input;
    }
    Label Label(string text) { return new Label { Text=text, AutoSize=true, ForeColor=Color.FromArgb(75,96,108), Font=new Font("Segoe UI",9), Dock=DockStyle.Top }; }
    Button Action(string id, string text, EventHandler handler) {
      Button button=new Button { Name=id, AccessibleName=text, Text=text, AutoSize=true, Height=35,
        Padding=new Padding(10,3,10,3), FlatStyle=FlatStyle.Flat, BackColor=Color.White, Margin=new Padding(5) };
      button.FlatAppearance.BorderColor=Color.FromArgb(183,202,211);button.Click+=handler;return button;
    }
    void AddField(TableLayoutPanel table, int index, string label, string id, bool readOnly) {
      Panel panel=new Panel { Dock=DockStyle.Fill, Margin=new Padding(0,3,0,3) };
      Label title=Label(label); title.Height=23; title.AutoSize=false;
      TextBox input=Input(id,readOnly);input.Dock=DockStyle.Top;input.AccessibleName=label;
      panel.Controls.Add(input);panel.Controls.Add(title);
      table.Controls.Add(panel,index%2,index/2);
    }
    TableLayoutPanel Section(string title, int height, int rows) {
      GroupBox group=new GroupBox { Text=title, Dock=DockStyle.Top, Height=height, Padding=new Padding(16,26,12,10),
        Font=new Font("Segoe UI",10,FontStyle.Bold), ForeColor=Color.FromArgb(36,57,71) };
      TableLayoutPanel table=new TableLayoutPanel { Dock=DockStyle.Fill, ColumnCount=2, RowCount=rows };
      table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,50));table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,50));
      for(int i=0;i<rows;i++)table.RowStyles.Add(new RowStyle(SizeType.Percent,100f/rows));
      group.Controls.Add(table); body.Controls.Add(group);group.BringToFront();return table;
    }
    Dictionary<string,object> Store(Dictionary<string,object> request) {
      ProcessStartInfo info=new ProcessStartInfo(python, Q(System.IO.Path.Combine(root,"scripts","oh_store.py"))+" "+Q(database));
      info.UseShellExecute=false;info.CreateNoWindow=true;info.RedirectStandardInput=true;
      info.RedirectStandardOutput=true;info.RedirectStandardError=true;
      info.StandardOutputEncoding=Encoding.UTF8;info.StandardErrorEncoding=Encoding.UTF8;
      using(Process process=Process.Start(info)) {
        byte[] bytes=Encoding.UTF8.GetBytes(json.Serialize(request));
        process.StandardInput.BaseStream.Write(bytes,0,bytes.Length);process.StandardInput.Close();
        var output=process.StandardOutput.ReadToEndAsync();var error=process.StandardError.ReadToEndAsync();
        if(!process.WaitForExit(8000)){process.Kill();throw new Exception("Hết thời gian đọc/lưu hồ sơ.");}
        if(process.ExitCode!=0)throw new Exception("Không kết nối được kho hồ sơ cục bộ.");
        var response=json.Deserialize<Dictionary<string,object>>(output.Result);
        if(!(bool)response["ok"])throw new Exception(S(response,"error"));
        return (Dictionary<string,object>)response["record"];
      }
    }
    void Message(string text, bool error=false) {
      fields["message"].Text=text;fields["message"].ForeColor=error?Color.Firebrick:Color.FromArgb(23,107,120);
    }
    void Dirty(object sender,EventArgs args) {
      if(!painting&&saved!=null)fields["save-state"].Text="Có thay đổi chưa lưu";
    }
    void PaintRecord() {
      painting=true;
      foreach(string key in new[]{"pid","name","dob","sex","company","batch","national_id"}) fields[key].Text=S(saved,key);
      foreach(string key in new[]{"package_code","package_name","visit_date","policy_code","policy_name","phone","nationality","address_original"})fields[key].Text=S(saved,key);
      DateTime birthday;if(DateTime.TryParse(S(saved,"dob"),out birthday))fields["dob"].Text=birthday.ToString("dd/MM/yyyy");
      if(localFirst!=null) {
        string[] parts=S(saved,"name").Split(new[]{' '},StringSplitOptions.RemoveEmptyEntries);
        localFirst.Text=parts.Length>0?parts[parts.Length-1]:"";
        localLast.Text=parts.Length>1?parts[0]:"";
        localMiddle.Text=parts.Length>2?String.Join(" ",parts,1,parts.Length-2):"";
        int years=DateTime.Today.Year-birthday.Year;if(birthday.Date>DateTime.Today.AddYears(-years))years--;
        ageBox.Text=years>=0?years.ToString()+" y":"";
      }
      if(profileTabs!=null)profileTabs.SelectedIndex=0;
      Dictionary<string,object> address=(Dictionary<string,object>)saved["address"];
      foreach(string key in new[]{"province","ward","street"})fields[key].Text=S(address,key);
      fields["version"].Text=S(saved,"version");fields["session"].Text=(++reception).ToString();
      fields["save-state"].Text="Chưa có thay đổi";painting=false;
      foreach(Button button in new[]{reload,cancel,save,locking,addressButton})button.Enabled=true;
    }
    void OpenRecord(object sender,EventArgs args) {
      if(locked)return;
      try {
        Message("Đang mở hồ sơ…");Refresh();
        saved=Store(new Dictionary<string,object>{{"action","get"},{"pid",fields["pid-search"].Text.Trim()}});
        PaintRecord();Message("Đã mở hồ sơ "+S(saved,"pid")+". Kiểm tra danh tính trước khi cập nhật.");
      }catch(Exception ex) {
        saved=null;painting=true;foreach(var field in fields)if(field.Key!="pid-search"&&field.Key!="message")field.Value.Text="";painting=false;
        if(localFirst!=null){localFirst.Clear();localMiddle.Clear();localLast.Clear();ageBox.Clear();}
        foreach(Button button in new[]{reload,cancel,save,locking,addressButton})button.Enabled=false;
        Message(ex.Message,true);
      }
    }
    void Reload(object sender,EventArgs args) { if(saved==null||locked)return;fields["pid-search"].Text=S(saved,"pid");OpenRecord(sender,args); }
    void Save(object sender,EventArgs args) {
      if(saved==null||locked)return;
      try {
        var record=Copy(saved);record["national_id"]=fields["national_id"].Text.Trim();
        record["address"]=new Dictionary<string,object>{{"province",fields["province"].Text},{"ward",fields["ward"].Text},{"street",fields["street"].Text}};
        Message("Đang lưu hồ sơ…");Refresh();saved=Store(new Dictionary<string,object>{{"action","save"},{"record",record}});
        PaintRecord();fields["save-state"].Text="Đã lưu thành công";Message("Đã lưu hồ sơ "+S(saved,"pid")+" thành công.");
      }catch(Exception ex){Message(ex.Message,true);}
    }
    void Lock(object sender,EventArgs args) {
      if(saved==null)return;locked=!locked;
      fields["pid-search"].Enabled=!locked;open.Enabled=!locked;reload.Enabled=!locked;cancel.Enabled=!locked;save.Enabled=!locked;newRecord.Enabled=!locked;
      if(browsePatients!=null)browsePatients.Enabled=!locked;
      locking.Text=locked?"Kết thúc khóa hồ sơ":"Khóa hồ sơ để điền";
      Message(locked?"Đang điền · tạm khóa chuyển hồ sơ":"Kiểm tra thông tin trước khi lưu.");
    }
    void Address(object sender,EventArgs args) {
      using(Form dialog=new Form { Name="address-dialog",Text="OH · Cập nhật địa chỉ", Size=new Size(510,380),
          FormBorderStyle=FormBorderStyle.FixedDialog, MaximizeBox=false,MinimizeBox=false,StartPosition=FormStartPosition.CenterParent,
          Font=new Font("Segoe UI",10),BackColor=Color.FromArgb(245,248,249) }) {
        Dictionary<string,TextBox> edits=new Dictionary<string,TextBox>();int y=18;
        string[] keys={"province","ward","street"};string[] labels={"Tỉnh / Thành phố","Phường / Xã","Số nhà / Đường / Thôn"};
        for(int i=0;i<3;i++) {
          Label title=new Label {Text=labels[i],Left=22,Top=y,Width=440,Height=22};
          TextBox edit=new TextBox {Name="address-"+keys[i],AccessibleName=labels[i],Text=fields[keys[i]].Text,
            Left=22,Top=y+25,Width=445,Height=28,MaxLength=250};
          dialog.Controls.Add(title);dialog.Controls.Add(edit);edits[keys[i]]=edit;y+=80;
        }
        Button apply=Action("apply-address","Áp dụng địa chỉ",delegate {
          foreach(string key in keys)if(String.IsNullOrWhiteSpace(edits[key].Text)){edits[key].Focus();return;}
          foreach(string key in keys)fields[key].Text=edits[key].Text.Trim();
          fields["save-state"].Text="Có thay đổi chưa lưu";dialog.DialogResult=DialogResult.OK;dialog.Close();
        });apply.SetBounds(290,275,177,36);
        Button close=Action("close-address","Hủy",delegate{dialog.Close();});close.SetBounds(180,275,100,36);
        dialog.Controls.Add(apply);dialog.Controls.Add(close);dialog.AcceptButton=apply;dialog.CancelButton=close;
        dialog.ShowDialog(this);
      }
    }
    void NewRecord(object sender,EventArgs args) {
      if(locked)return;
      if(fields["save-state"].Text=="Có thay đổi chưa lưu") {Message("Lưu hoặc hủy thay đổi hồ sơ hiện tại trước khi tạo mới.",true);return;}
      using(Form dialog=new Form {Name="create-dialog",Text="OH · Tạo hồ sơ và bung gói khám",Size=new Size(760,780),
          MinimumSize=new Size(700,650),StartPosition=FormStartPosition.CenterParent,Font=new Font("Segoe UI",10),BackColor=Color.White}) {
        var edits=new Dictionary<string,TextBox>();
        string[] keys={"name","national_id","dob","sex","phone","nationality","address_original","company","batch","policy_code","policy_name","package_code","package_name","visit_date"};
        string[] titles={"Họ và tên","CCCD (bắt buộc)","Ngày sinh (YYYY-MM-DD)","Giới tính","Điện thoại từ Excel","Quốc tịch","Địa chỉ nguồn Excel (chưa xác nhận mới)","Công ty","Đợt khám","Mã hợp đồng / Policy","Tên hợp đồng / Policy","Mã gói khám (bắt buộc)","Tên gói khám","Ngày khám (YYYY-MM-DD)"};
        var layout=new TableLayoutPanel {Dock=DockStyle.Fill,ColumnCount=1,RowCount=3,Padding=new Padding(18)};
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute,48));layout.RowStyles.Add(new RowStyle(SizeType.Percent,100));layout.RowStyles.Add(new RowStyle(SizeType.Absolute,116));dialog.Controls.Add(layout);
        var heading=Label("Lần 1 · Tạo khách mới / bung gói. PID được OH cấp sau khi lưu.");heading.Dock=DockStyle.Fill;layout.Controls.Add(heading,0,0);
        var scroller=new Panel {Dock=DockStyle.Fill,AutoScroll=true};
        var grid=new TableLayoutPanel {Dock=DockStyle.Top,ColumnCount=2,RowCount=7,Height=7*72};
        grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,50));grid.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,50));
        for(int i=0;i<7;i++)grid.RowStyles.Add(new RowStyle(SizeType.Absolute,72));
        for(int i=0;i<keys.Length;i++) {
          var panel=new Panel {Dock=DockStyle.Fill,Margin=new Padding(0,0,12,3)};
          var title=Label(titles[i]);title.Height=22;title.AutoSize=false;
          var edit=new TextBox {Name="create-"+keys[i],AccessibleName=titles[i],Dock=DockStyle.Top,MaxLength=250};
          panel.Controls.Add(edit);panel.Controls.Add(title);grid.Controls.Add(panel,i%2,i/2);edits[keys[i]]=edit;
        }
        edits["national_id"].MaxLength=12;scroller.Controls.Add(grid);layout.Controls.Add(scroller,0,1);
        var footer=new Panel {Dock=DockStyle.Fill};layout.Controls.Add(footer,0,2);
        var status=new TextBox {Name="create-status",AccessibleName="Trạng thái tạo hồ sơ",ReadOnly=true,BorderStyle=BorderStyle.None,
          Text="Điền thông tin rồi kiểm tra CCCD trước khi lưu.",Dock=DockStyle.Top,Height=26};
        var existingPid=new TextBox {Name="existing-pid",AccessibleName="PID đã có",ReadOnly=true,Width=140};
        var actions=new FlowLayoutPanel {Dock=DockStyle.Bottom,Height=48,FlowDirection=FlowDirection.RightToLeft};
        Button createButton=null;
        createButton=Action("create-save","Lưu và cấp PID",delegate {
          createButton.Enabled=false;
          try {
            var record=new Dictionary<string,object>();foreach(string key in keys)record[key]=edits[key].Text.Trim();
            saved=Store(new Dictionary<string,object>{{"action","create"},{"record",record}});
            fields["pid-search"].Text=S(saved,"pid");PaintRecord();fields["save-state"].Text="Đã lưu thành công";
            Message("Đã tạo PID "+S(saved,"pid")+" và gói "+S(saved,"package_code")+".");dialog.DialogResult=DialogResult.OK;dialog.Close();
          }catch(Exception ex){status.Text=ex.Message;status.ForeColor=Color.Firebrick;createButton.Enabled=true;}
        });createButton.Enabled=false;
        Button check=Action("create-check","Kiểm tra CCCD",delegate {
          createButton.Enabled=false;existingPid.Text="";
          try {
            var found=Store(new Dictionary<string,object>{{"action","find"},{"national_id",edits["national_id"].Text.Trim()}});
            existingPid.Text=S(found,"pid");
            if(existingPid.Text!="")status.Text="Đã có hồ sơ PID "+existingPid.Text+". Không tạo mới.";
            else {status.Text="CCCD chưa có hồ sơ. Kiểm tra thông tin và lưu để OH cấp PID.";createButton.Enabled=true;}
          }catch(Exception ex){status.Text=ex.Message;}
        });
        edits["national_id"].TextChanged+=delegate{createButton.Enabled=false;existingPid.Text="";status.Text="Cần kiểm tra CCCD trước khi lưu.";};
        Button dismiss=Action("create-cancel","Hủy tạo mới",delegate{dialog.Close();});
        actions.Controls.Add(createButton);actions.Controls.Add(check);actions.Controls.Add(dismiss);
        var existingRow=new FlowLayoutPanel {Dock=DockStyle.Top,Height=30};existingRow.Controls.Add(Label("PID đã có:"));existingRow.Controls.Add(existingPid);
        footer.Controls.Add(existingRow);footer.Controls.Add(status);footer.Controls.Add(actions);
        dialog.CancelButton=dismiss;dialog.ShowDialog(this);
      }
    }
    public PatientForm(string[] args) {
      python=args[0];root=args[1];database=args[2];
      BuildReferenceLayout(args);
    }
    [STAThread] public static void Main(string[] args) {
      if(args.Length<3) {
        string directory=System.IO.Directory.GetParent(AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\')).FullName;
        args=new[]{"python",directory,System.IO.Path.Combine(directory,"runtime","oh.sqlite3")};
      }
      Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);
      Application.Run(new PatientForm(args));
    }
  }
}
