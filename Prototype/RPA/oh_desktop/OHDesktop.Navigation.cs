using System;
using System.Drawing;
using System.Windows.Forms;

namespace OHDesktop {
  public partial class PatientForm {
    Panel navigationPanel,navigationScroll;
    FlowLayoutPanel navigationGroups;
    ComboBox navigationModule;
    Button navigationToggle;
    bool navigationManuallyCollapsed;

    void NavigationGroup(string id,string caption,string[][] items) {
      bool expanded=true;
      var group=new Panel {Name="nav-section-"+id,Width=240,Height=31+items.Length*29,Margin=new Padding(0),BackColor=Color.FromArgb(244,245,247)};
      var header=new Button {Name="nav-group-"+id,AccessibleName=caption,Text=caption,Dock=DockStyle.Top,Height=31,
        TextAlign=ContentAlignment.MiddleLeft,Font=new Font("Segoe UI",9),FlatStyle=FlatStyle.Flat,
        ForeColor=Color.FromArgb(72,77,84),BackColor=Color.FromArgb(238,240,243),Padding=new Padding(10,0,0,0)};
      header.FlatAppearance.BorderSize=0;
      header.Paint+=delegate(object sender,PaintEventArgs args) {
        args.Graphics.DrawLine(Pens.LightGray,0,header.Height-1,header.Width,header.Height-1);
        TextRenderer.DrawText(args.Graphics,expanded?"⌄":"›",header.Font,new Rectangle(header.Width-25,0,20,header.Height),header.ForeColor,TextFormatFlags.VerticalCenter|TextFormatFlags.HorizontalCenter);
      };
      var list=new TableLayoutPanel {Dock=DockStyle.Fill,RowCount=items.Length,ColumnCount=1,Margin=new Padding(0),Padding=new Padding(0)};
      for(int i=0;i<items.Length;i++) {
        string itemId=items[i][0],text=items[i][1];bool active=itemId=="patient-profile";
        var item=new Button {Name="nav-"+itemId,AccessibleName=text.Replace("★ ",""),Text=text,Dock=DockStyle.Fill,
          TextAlign=ContentAlignment.MiddleLeft,FlatStyle=FlatStyle.Flat,Height=29,Margin=new Padding(0),
          Padding=new Padding(text.StartsWith("★")?10:26,0,0,0),
          Font=new Font("Segoe UI",10,active?FontStyle.Bold:FontStyle.Regular),ForeColor=Color.FromArgb(45,49,56),
          BackColor=active?Color.FromArgb(224,229,236):group.BackColor};
        item.FlatAppearance.BorderSize=0;item.FlatAppearance.MouseOverBackColor=Color.FromArgb(232,236,242);
        item.Click+=delegate {
          if(itemId=="patient-list")BrowsePatients(item,EventArgs.Empty);
          else if(active){if(profileTabs!=null)profileTabs.SelectedIndex=0;Message("Patient Profile");}
          else Message(text.Replace("★ ","")+": chức năng tham chiếu, ngoài phạm vi nghiệp vụ demo.");
        };
        list.RowStyles.Add(new RowStyle(SizeType.Absolute,29));list.Controls.Add(item,0,i);
      }
      header.Click+=delegate {
        expanded=!expanded;list.Visible=expanded;group.Height=expanded?31+items.Length*29:31;header.Invalidate();
      };
      group.Controls.Add(list);group.Controls.Add(header);navigationGroups.Controls.Add(group);
    }
    void FitNavigation() {
      if(navigationPanel==null)return;
      bool expanded=!navigationManuallyCollapsed&&ClientSize.Width>=1360;
      navigationPanel.Width=expanded?260:38;
      navigationScroll.Visible=expanded;navigationModule.Visible=expanded;
      navigationToggle.Text=expanded?"‹":"☰";
    }
    void BuildNavigation() {
      navigationPanel=new Panel {Name="oh-navigation",AccessibleName="OH navigation",Dock=DockStyle.Left,Width=260,
        BackColor=Color.FromArgb(239,241,244),BorderStyle=BorderStyle.FixedSingle};
      var header=new TableLayoutPanel {Dock=DockStyle.Top,Height=39,ColumnCount=2,RowCount=1,Padding=new Padding(4,6,2,3)};
      header.ColumnStyles.Add(new ColumnStyle(SizeType.Percent,100));header.ColumnStyles.Add(new ColumnStyle(SizeType.Absolute,29));
      navigationModule=RefChoice("navigation-module",216,"Patient Profile");navigationModule.Dock=DockStyle.Fill;
      navigationToggle=SmallAction("navigation-toggle","‹",delegate {
        if(ClientSize.Width<1360) {
          if(Width<1400)Width=Math.Min(1480,Screen.FromControl(this).WorkingArea.Width-24);
          navigationManuallyCollapsed=false;
        } else navigationManuallyCollapsed=!navigationManuallyCollapsed;
        FitNavigation();
      },27);
      header.Controls.Add(navigationModule,0,0);header.Controls.Add(navigationToggle,1,0);
      navigationScroll=new Panel {Name="navigation-scroll",AccessibleName="Navigation menu scroll area",Dock=DockStyle.Fill,AutoScroll=true};
      navigationGroups=new FlowLayoutPanel {Dock=DockStyle.Top,AutoSize=true,AutoSizeMode=AutoSizeMode.GrowAndShrink,
        FlowDirection=FlowDirection.TopDown,WrapContents=false,Margin=new Padding(0),Padding=new Padding(0)};
      navigationScroll.Controls.Add(navigationGroups);
      NavigationGroup("registration","REGISTRATION",new[]{
        new[]{"patient-profile","Patient Profile"},new[]{"patient-list","Danh sách hồ sơ"},new[]{"visit-manager","★ Visit Manager"},
        new[]{"opd-registration","OPD Visit Registration"},new[]{"emergency-registration","Emergency Visit Registration"},
        new[]{"patient-queue","Patient Queue"},new[]{"medical-record-requests","Medical Record Requests"}});
      NavigationGroup("cashier","CASHIER",new[]{new[]{"select-company","Select Company"},new[]{"patient-billing","★ Patient Billing"},
        new[]{"deposit-refund","Deposit and Refund"},new[]{"shift","Shift"}});
      NavigationGroup("admission","ADMISSION",new[]{new[]{"admission-management","Admission Management"},new[]{"request-admission","Request Admission"},
        new[]{"inpatient-admission","Inpatient Admission"},new[]{"locate-patient","Locate Patient"},new[]{"bed-schedule","Bed Schedule"}});
      NavigationGroup("discharge","DISCHARGE",new[]{new[]{"discharge-planner","Discharge Planner"},new[]{"discharge-patient","Discharge Patient"},new[]{"discharge-workbench","Discharge Workbench"}});
      NavigationGroup("transfer","TRANSFER",new[]{new[]{"transfer","Transfer"}});
      NavigationGroup("appointments","APPOINTMENTS",new[]{new[]{"enterprise-scheduling","Enterprise Scheduling"},new[]{"patient-appointments","Patient Appointments"},new[]{"work-schedule","Work Schedule"}});
      NavigationGroup("visit","VISIT",new[]{new[]{"visit-browser","Visit Browser"},new[]{"delete-visit","Delete Visit"},new[]{"reopen-visit","Reopen Visit"},
        new[]{"visit-status","Visit Status Changes"},new[]{"bed-charges","Bed Charges"},new[]{"add-patient-document","Add Document to Patient File"}});
      NavigationGroup("maintenance","MAINTENANCE",new[]{new[]{"move-charges","Move Charges"},new[]{"room-charges-maintenance","Room Charges Set Maintenance"}});
      navigationPanel.Controls.Add(navigationScroll);navigationPanel.Controls.Add(header);Controls.Add(navigationPanel);
      Resize+=delegate{FitNavigation();};Shown+=delegate{FitNavigation();};FitNavigation();
    }
  }
}
