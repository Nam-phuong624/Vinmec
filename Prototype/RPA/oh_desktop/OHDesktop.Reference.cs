using System;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Windows.Forms;

namespace OHDesktop {
  public class ReferenceCaption : Label {
    public bool Required;
    protected override void OnPaint(PaintEventArgs e) {
      e.Graphics.Clear(BackColor);
      var bounds=ClientRectangle;
      if(Required)bounds.Width-=12;
      TextRenderer.DrawText(e.Graphics,Text,Font,bounds,ForeColor,
        TextFormatFlags.Right|TextFormatFlags.VerticalCenter|TextFormatFlags.SingleLine|TextFormatFlags.NoPadding);
      if(Required)TextRenderer.DrawText(e.Graphics,"*",Font,new Rectangle(Width-10,0,10,Height),Color.Firebrick,
        TextFormatFlags.Left|TextFormatFlags.VerticalCenter|TextFormatFlags.SingleLine|TextFormatFlags.NoPadding);
    }
  }
  // Native controls arranged from the supplied OH_UI/OH.jpg reference.
  public partial class PatientForm {
    const int ReferenceRowHeight=32;
    [DllImport("user32.dll",CharSet=CharSet.Unicode)]
    static extern IntPtr SendMessage(IntPtr hwnd,int message,IntPtr wParam,string lParam);

    TextBox RefInput(string id,int width,bool readOnly,string hint="") {
      var input=Input(id,readOnly);input.Dock=DockStyle.None;input.Width=width;
      input.Font=new Font("Segoe UI",10);input.BackColor=Color.White;
      input.Margin=new Padding(0,2,5,0);
      if(hint!="")input.HandleCreated+=delegate{SendMessage(input.Handle,0x1501,(IntPtr)1,hint);};
      return input;
    }
    TextBox ReferenceOnly(string id,string text,int width) {
      return new TextBox {Name=id,AccessibleName=id,Text=text,ReadOnly=true,Width=width,
        Font=new Font("Segoe UI",10),BackColor=Color.White,BorderStyle=BorderStyle.FixedSingle,
        Margin=new Padding(0,2,5,0)};
    }
    ComboBox RefChoice(string id,int width,params string[] choices) {
      var combo=new ComboBox {Name=id,AccessibleName=id,Width=width,DropDownStyle=ComboBoxStyle.DropDownList,
        Font=new Font("Segoe UI",10),Margin=new Padding(0,2,5,0)};
      combo.Items.AddRange(choices);if(choices.Length>0)combo.SelectedIndex=0;return combo;
    }
    Label Inline(string text,bool italic=false,int width=0) {
      var label=new Label {Text=text,AutoSize=width==0,Height=26,TextAlign=ContentAlignment.MiddleLeft,
        Font=new Font("Segoe UI",9.5f,italic?FontStyle.Italic:FontStyle.Regular),ForeColor=Color.FromArgb(86,91,99),
        Margin=new Padding(3,3,7,0)};
      if(width>0)label.Width=width;return label;
    }
    FlowLayoutPanel RefLine(params Control[] controls) {
      var panel=new FlowLayoutPanel {Dock=DockStyle.Fill,WrapContents=false,Margin=new Padding(0),Padding=new Padding(0)};
      foreach(var control in controls){control.Dock=DockStyle.None;panel.Controls.Add(control);}return panel;
    }
    Button SmallAction(string id,string text,EventHandler handler,int width=30) {
      var button=Action(id,text,handler);button.AutoSize=false;button.Size=new Size(width,26);
      button.Font=new Font("Segoe UI",9.5f);button.Padding=new Padding(0);button.Margin=new Padding(0,2,5,0);
      button.BackColor=Color.FromArgb(247,248,250);button.FlatAppearance.BorderColor=Color.FromArgb(190,196,204);
      return button;
    }
    TableLayoutPanel RefSection(string id,string title,int rows) {
      var section=new Panel {Name=id,Dock=DockStyle.Top,Height=31+rows*ReferenceRowHeight+8,
        Padding=new Padding(0,0,0,7),BackColor=Color.White};
      var table=new TableLayoutPanel {Dock=DockStyle.Fill,ColumnCount=2,RowCount=rows,Padding=new Padding(0,4,12,0)};
      table.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,204));table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
      for(int i=0;i<rows;i++)table.RowStyles.Add(new RowStyle(SizeType.Absolute,ReferenceRowHeight));
      var header=new Button {Name=id+"-header",AccessibleName=title,Text=title+"  ⌄",Dock=DockStyle.Top,Height=30,
        TextAlign=ContentAlignment.MiddleLeft,Font=new Font("Segoe UI",11),FlatStyle=FlatStyle.Flat,
        BackColor=Color.FromArgb(241,243,246),ForeColor=Color.FromArgb(43,47,55),Padding=new Padding(10,0,0,0)};
      header.FlatAppearance.BorderSize=0;
      header.Click+=delegate{table.Visible=!table.Visible;section.Height=table.Visible?31+rows*ReferenceRowHeight+8:31;header.Text=title+(table.Visible?"  ⌄":"  ›");};
      section.Controls.Add(table);section.Controls.Add(header);body.Controls.Add(section);section.BringToFront();return table;
    }
    void RefRow(TableLayoutPanel table,int row,string caption,Control content,bool required=false) {
      var labelPanel=new Panel {Dock=DockStyle.Fill,Margin=new Padding(0,0,11,0)};
      var label=new ReferenceCaption {Text=caption,AccessibleName=caption,Required=required,Dock=DockStyle.Fill,TextAlign=ContentAlignment.MiddleRight,
        ForeColor=Color.FromArgb(49,54,62),Font=new Font("Segoe UI",9.5f)};
      labelPanel.Controls.Add(label);
      content.Dock=DockStyle.Fill;content.Margin=new Padding(0,0,0,0);
      table.Controls.Add(labelPanel,0,row);table.Controls.Add(content,1,row);
    }
    Control NameParts(bool local) {
      var row=new TableLayoutPanel {Dock=DockStyle.Fill,ColumnCount=5,RowCount=1,Margin=new Padding(0)};
      row.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,126));
      for(int i=0;i<3;i++)row.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,33.333f));
      row.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,32));
      row.Controls.Add(RefChoice(local?"local-title":"other-title",120,"Title","Ông","Bà"),0,0);
      string[] names={"First Name","Middle Name(s)","Last Name"};
      for(int i=0;i<3;i++) {
        TextBox entry;
        if(local){entry=ReferenceOnly("local-name-"+i,"",100);if(i==0)localFirst=entry;else if(i==1)localMiddle=entry;else localLast=entry;}
        else {entry=ReferenceOnly("other-name-"+i,"",100);string hint=names[i];entry.HandleCreated+=delegate{SendMessage(entry.Handle,0x1501,(IntPtr)1,hint);};}
        entry.Dock=DockStyle.Fill;row.Controls.Add(entry,i+1,0);
      }
      var more=SmallAction(local?"local-name-more":"other-name-more","…",delegate{},28);more.Enabled=false;row.Controls.Add(more,4,0);
      return row;
    }
    void BuildReferenceLayout(string[] args) {
      Name="OHDesktop";Text=args.Length>3?args[3]:"OH Desktop · Tiếp đón — DEMO";
      Font=new Font("Segoe UI",9.5f);BackColor=Color.FromArgb(239,241,244);
      var work=Screen.PrimaryScreen.WorkingArea;
      Size=new Size(Math.Min(1480,work.Width-36),Math.Min(960,work.Height-32));MinimumSize=new Size(1120,680);
      StartPosition=FormStartPosition.Manual;Location=new Point(work.Left+12,work.Top+12);
      BuildNavigation();
      var shell=new TableLayoutPanel {Dock=DockStyle.Fill,ColumnCount=1,RowCount=5,Padding=new Padding(18,8,18,6),BackColor=Color.White};
      shell.RowStyles.Add(new RowStyle(SizeType.Absolute,37));shell.RowStyles.Add(new RowStyle(SizeType.Absolute,45));
      shell.RowStyles.Add(new RowStyle(SizeType.Percent,100));shell.RowStyles.Add(new RowStyle(SizeType.Absolute,39));shell.RowStyles.Add(new RowStyle(SizeType.Absolute,45));
      Controls.Add(shell);shell.BringToFront();

      var toolbar=new FlowLayoutPanel {Dock=DockStyle.Fill,WrapContents=false,Margin=new Padding(0),BackColor=Color.FromArgb(247,248,250)};
      toolbar.Controls.Add(Inline("PID"));toolbar.Controls.Add(RefInput("pid-search",165,false,"Quét / nhập PID"));
      open=SmallAction("open-record","Mở hồ sơ",OpenRecord,102);reload=SmallAction("reload-record","Tải lại",Reload,77);
      newRecord=SmallAction("new-record","Tạo mới / bung gói",NewRecord,160);
      toolbar.Controls.Add(open);toolbar.Controls.Add(reload);toolbar.Controls.Add(newRecord);
      browsePatients=SmallAction("browse-patients","Danh sách hồ sơ",BrowsePatients,137);toolbar.Controls.Add(browsePatients);
      var demo=Inline("MÔ PHỎNG · DỮ LIỆU GIẢ");demo.ForeColor=Color.FromArgb(151,109,37);demo.Margin=new Padding(18,4,0,0);toolbar.Controls.Add(demo);
      shell.Controls.Add(toolbar,0,0);
      fields["pid-search"].KeyDown+=delegate(object sender,KeyEventArgs e){if(e.KeyCode==Keys.Enter){e.SuppressKeyPress=true;OpenRecord(sender,e);}};
      shell.Controls.Add(new Label {Text="Patient Profile",Dock=DockStyle.Fill,TextAlign=ContentAlignment.MiddleLeft,Font=new Font("Segoe UI",19),ForeColor=Color.FromArgb(31,36,44)},0,1);
      profileTabs=new TabControl {Name="profile-tabs",Dock=DockStyle.Fill,Font=new Font("Segoe UI",10),Padding=new Point(18,6)};
      var demographics=new TabPage("Demographics") {Name="demographics-tab",BackColor=Color.White,Padding=new Padding(7,10,7,0)};
      profileTabs.TabPages.Add(demographics);
      foreach(string title in new[]{"Circle of Care","Financial"}) {
        var page=new TabPage(title);page.Controls.Add(new Label {Text=title+" — ngoài phạm vi demo",Dock=DockStyle.Fill,TextAlign=ContentAlignment.MiddleCenter,ForeColor=Color.Gray});profileTabs.TabPages.Add(page);
      }
      shell.Controls.Add(profileTabs,0,2);
      body=new Panel {Name="profile-scroll",AccessibleName="Patient profile scroll area",Dock=DockStyle.Fill,AutoScroll=true,BackColor=Color.White};demographics.Controls.Add(body);

      var identification=RefSection("identification-section","Identification Details",9);
      var fullName=RefInput("name",385,true);fullName.BorderStyle=BorderStyle.None;fullName.AccessibleName="Full patient name";
      RefRow(identification,0,"Hospital Number",RefLine(RefInput("pid",185,true),fullName));
      RefRow(identification,1,"Name (Local)",NameParts(true),true);
      RefRow(identification,2,"Name (Other)",NameParts(false),true);
      var confirmed=ReferenceOnly("name-status-confirmed","Confirmed",100);confirmed.BackColor=Color.FromArgb(235,240,247);
      RefRow(identification,3,"Name Status",RefLine(confirmed,Inline("♙ Temporary")));
      var otherNames=SmallAction("other-names-reference","…",delegate{},32);otherNames.Enabled=false;
      RefRow(identification,4,"Other Names",RefLine(otherNames));
      RefRow(identification,5,"Sex",RefLine(RefInput("sex",365,true),Inline("▾")),true);
      ageBox=ReferenceOnly("age-display","",76);
      RefRow(identification,6,"Date of Birth",RefLine(RefChoice("birth-precision",210,"Year, Month and Day"),RefInput("dob",220,true),Inline("Age"),ageBox),true);
      var official=SmallAction("official-documents-add","+",delegate{fields["national_id"].Focus();});
      var cccd=RefInput("national_id",290,false,"Add one or more official documents.");cccd.MaxLength=12;cccd.TextChanged+=Dirty;
      RefRow(identification,7,"Official Documents",RefLine(official,cccd,Inline("CCCD")));
      RefRow(identification,8,"Banner Indicators",RefLine(RefChoice("banner-indicators",365,"")));

      var contact=RefSection("contact-section","Contact Details",5);
      RefRow(contact,0,"Phone Numbers",RefLine(RefChoice("phone-type",125,"Di động"),RefChoice("phone-country",170,"+84 Việt Nam"),ReferenceOnly("phone-area","Area",65),RefInput("phone",205,true),Inline("✎")),true);
      var addPhone=SmallAction("add-phone-reference","+",delegate{});addPhone.Enabled=false;
      RefRow(contact,1,"",RefLine(addPhone,Inline("Click + to add new phone number.",true)));
      RefRow(contact,2,"Email Addresses",RefLine(ReferenceOnly("email-unspecified","Unspecified",114),ReferenceOnly("email-advised","Advised no email",145),Inline("Click + to add new email address.",true)));
      addressButton=SmallAction("edit-address","+",Address);
      RefRow(contact,3,"Addresses",RefLine(addressButton,new CheckBox {Text="Temporary",AutoSize=true,Enabled=false,Margin=new Padding(1,4,4,0)},Inline("Add one or more addresses.",true)),true);
      RefRow(contact,4,"Current address",RefLine(RefInput("province",240,true,"Tỉnh / Thành phố"),RefInput("ward",200,true,"Phường / Xã"),RefInput("street",275,true,"Số nhà / Đường / Thôn")));

      var personal=RefSection("personal-section","Personal Details",4);
      RefRow(personal,0,"Nationality",RefLine(RefInput("nationality",365,true),Inline("▾")),true);
      RefRow(personal,1,"Primary Language",RefLine(RefChoice("primary-language",365,"Vietnamese")),true);
      RefRow(personal,2,"Ethnicity",RefLine(RefChoice("ethnicity-reference",365,"Không rõ")),true);
      RefRow(personal,3,"Occupation",RefLine(RefChoice("occupation-reference",365,"Unknown")),true);
      var employment=RefSection("employment-section","Employment Details",2);
      RefRow(employment,0,"Company",RefLine(RefInput("company",520,true)));RefRow(employment,1,"Examination batch",RefLine(RefInput("batch",365,true)));
      var package=RefSection("package-section","Prepared Examination Package",6);
      RefRow(package,0,"Package Code",RefLine(RefInput("package_code",365,true)));RefRow(package,1,"Package Name",RefLine(RefInput("package_name",620,true)));
      RefRow(package,2,"Visit Date / Time",RefLine(RefInput("visit_date",365,true)));RefRow(package,3,"Policy Code",RefLine(RefInput("policy_code",365,true)));
      RefRow(package,4,"Policy Name",RefLine(RefInput("policy_name",620,true)));RefRow(package,5,"Excel address (source)",RefLine(RefInput("address_original",650,true)));

      var actions=new TableLayoutPanel {Dock=DockStyle.Fill,ColumnCount=2,RowCount=1,Margin=new Padding(0)};
      actions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,40));actions.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,60));
      actions.Controls.Add(RefLine(Inline("Notes       Documents       Functions ▾")),0,0);
      var saveActions=new FlowLayoutPanel {Dock=DockStyle.Fill,FlowDirection=FlowDirection.RightToLeft,WrapContents=false};
      save=SmallAction("save-record","Lưu hồ sơ",Save,105);save.BackColor=Color.FromArgb(229,235,243);
      cancel=SmallAction("cancel-record","Hủy thay đổi",delegate{if(saved!=null&&!locked){PaintRecord();Message("Đã hủy thay đổi chưa lưu.");}},118);
      locking=SmallAction("lock-record","Khóa hồ sơ để điền",Lock,168);
      saveActions.Controls.Add(save);saveActions.Controls.Add(cancel);saveActions.Controls.Add(locking);actions.Controls.Add(saveActions,1,0);shell.Controls.Add(actions,0,3);
      var status=new TableLayoutPanel {Dock=DockStyle.Fill,ColumnCount=7,RowCount=1,Margin=new Padding(0)};
      status.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));
      foreach(int width in new[]{64,38,46,38,78,190})status.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,width));
      var message=RefInput("message",300,true);message.BorderStyle=BorderStyle.None;message.Dock=DockStyle.Fill;message.Font=new Font("Segoe UI",8.5f);status.Controls.Add(message,0,0);
      status.Controls.Add(Inline("Version"),1,0);status.Controls.Add(RefInput("version",30,true),2,0);
      status.Controls.Add(Inline("Lượt"),3,0);status.Controls.Add(RefInput("session",30,true),4,0);
      status.Controls.Add(Inline("Trạng thái"),5,0);status.Controls.Add(RefInput("save-state",180,true),6,0);shell.Controls.Add(status,0,4);
      foreach(Button button in new[]{reload,cancel,save,locking,addressButton})button.Enabled=false;
      Message("Sẵn sàng tiếp nhận. Nhập PID để bắt đầu.");Shown+=delegate{fields["pid-search"].Focus();};
    }
  }
}
