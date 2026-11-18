using System;
using System.Collections;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;

namespace OHDesktop {
  public partial class PatientForm {
    Button browsePatients;

    void BrowsePatients(object sender,EventArgs args) {
      if(locked){Message("RPA đang điền. Chờ kết thúc trước khi đổi hồ sơ.");return;}
      if(fields["save-state"].Text=="Có thay đổi chưa lưu") {
        Message("Lưu hoặc hủy thay đổi hiện tại trước khi mở danh sách.",true);return;
      }
      string selectedPid="";int offset=0,total=0;const int pageSize=50;
      using(var dialog=new Form {Name="patient-browser",Text="OH · Danh sách hồ sơ",Size=new Size(1180,700),
          MinimumSize=new Size(950,560),StartPosition=FormStartPosition.CenterParent,Font=new Font("Segoe UI",10),BackColor=Color.White}) {
        var layout=new TableLayoutPanel {Dock=DockStyle.Fill,ColumnCount=1,RowCount=4,Padding=new Padding(18)};
        layout.RowStyles.Add(new RowStyle(SizeType.Absolute,36));layout.RowStyles.Add(new RowStyle(SizeType.Absolute,63));
        layout.RowStyles.Add(new RowStyle(SizeType.Percent,100));layout.RowStyles.Add(new RowStyle(SizeType.Absolute,82));dialog.Controls.Add(layout);
        layout.Controls.Add(new Label {Text="Danh sách hồ sơ người khám",Dock=DockStyle.Fill,Font=new Font("Segoe UI",16),ForeColor=Color.FromArgb(38,53,68)},0,0);
        var searchRow=new TableLayoutPanel {Dock=DockStyle.Fill,ColumnCount=3,RowCount=2};
        searchRow.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));searchRow.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,110));searchRow.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,112));
        searchRow.Controls.Add(new Label {Text="Tìm theo tên, CCCD, PID hoặc công ty (có thể gõ không dấu)",AutoSize=true},0,0);
        var query=new TextBox {Name="patient-query",AccessibleName="Tìm hồ sơ",Dock=DockStyle.Fill,MaxLength=250,Margin=new Padding(0,4,8,0)};
        searchRow.Controls.Add(query,0,1);layout.Controls.Add(searchRow,0,1);
        var list=new ListView {Name="patient-list",AccessibleName="Danh sách hồ sơ",Dock=DockStyle.Fill,View=View.Details,
          FullRowSelect=true,MultiSelect=false,HideSelection=false,GridLines=true,UseCompatibleStateImageBehavior=false};
        string[] titles={"PID","Họ và tên","Ngày sinh","CCCD","Công ty","Đợt khám","Mã gói","Ngày / giờ khám"};
        int[] widths={112,190,98,125,170,118,98,153};
        for(int i=0;i<titles.Length;i++)list.Columns.Add(titles[i],widths[i]);layout.Controls.Add(list,0,2);
        var footer=new Panel {Dock=DockStyle.Fill,Padding=new Padding(0,8,0,0)};
        var count=new TextBox {Name="patient-count",AccessibleName="Số hồ sơ",ReadOnly=true,BorderStyle=BorderStyle.None,Dock=DockStyle.Top,Text="Đang nạp danh sách…",BackColor=Color.White};footer.Controls.Add(count);
        var actions=new FlowLayoutPanel {Dock=DockStyle.Bottom,Height=42,FlowDirection=FlowDirection.RightToLeft};
        Button openSelected=null,previous=null,next=null;
        EventHandler choose=delegate {
          if(list.SelectedItems.Count==0)return;
          selectedPid=Convert.ToString(list.SelectedItems[0].Tag);dialog.DialogResult=DialogResult.OK;dialog.Close();
        };
        openSelected=Action("patient-open","Mở hồ sơ đã chọn",choose);openSelected.Enabled=false;
        var close=Action("patient-close","Đóng",delegate{dialog.Close();});dialog.CancelButton=close;
        Action load=delegate {
          try {
            count.Text="Đang nạp danh sách…";count.Refresh();
            var response=Store(new Dictionary<string,object>{{"action","list"},{"query",query.Text.Trim()},{"offset",offset},{"limit",pageSize}});
            total=Convert.ToInt32(response["total"]);list.BeginUpdate();list.Items.Clear();
            foreach(object value in (IEnumerable)response["items"]) {
              var record=(Dictionary<string,object>)value;string pid=S(record,"pid");
              DateTime birth;string birthday=S(record,"dob");if(DateTime.TryParse(birthday,out birth))birthday=birth.ToString("dd/MM/yyyy");
              var row=new ListViewItem(new[]{pid,S(record,"name"),birthday,S(record,"national_id"),S(record,"company"),S(record,"batch"),S(record,"package_code"),S(record,"visit_date")});
              row.Tag=pid;list.Items.Add(row);
            }
            list.EndUpdate();
            count.Text=total==0?"Không tìm thấy hồ sơ. Thử từ khóa khác.":"Hiển thị "+(offset+1)+"–"+(offset+list.Items.Count)+" / Tổng "+total+" hồ sơ · Chọn một dòng rồi Mở, hoặc nhấp đúp.";
            previous.Enabled=offset>0;next.Enabled=offset+pageSize<total;openSelected.Enabled=list.Items.Count>0;
            if(list.Items.Count>0){list.Items[0].Selected=true;list.Items[0].Focused=true;}
          }catch(Exception ex){list.EndUpdate();count.Text=ex.Message;openSelected.Enabled=false;previous.Enabled=false;next.Enabled=false;}
        };
        var search=Action("patient-search","Tìm kiếm",delegate{offset=0;load();});
        var refresh=Action("patient-refresh","Làm mới",delegate{offset=0;load();});
        searchRow.Controls.Add(search,1,1);searchRow.Controls.Add(refresh,2,1);
        previous=Action("patient-previous","‹ Trang trước",delegate{offset=Math.Max(0,offset-pageSize);load();});
        next=Action("patient-next","Trang sau ›",delegate{offset+=pageSize;load();});
        actions.Controls.Add(openSelected);actions.Controls.Add(close);actions.Controls.Add(next);actions.Controls.Add(previous);
        footer.Controls.Add(actions);layout.Controls.Add(footer,0,3);
        list.ItemSelectionChanged+=delegate{openSelected.Enabled=list.SelectedItems.Count>0;};
        list.DoubleClick+=choose;
        list.KeyDown+=delegate(object control,KeyEventArgs key){if(key.KeyCode==Keys.Enter){key.SuppressKeyPress=true;choose(control,key);}};
        query.KeyDown+=delegate(object control,KeyEventArgs key){if(key.KeyCode==Keys.Enter){key.SuppressKeyPress=true;offset=0;load();}};
        dialog.Shown+=delegate{load();query.Focus();};
        dialog.ShowDialog(this);
      }
      if(selectedPid!=""){fields["pid-search"].Text=selectedPid;OpenRecord(sender,args);}
    }
  }
}
