"""Build a native WinForms executable with the compiler shipped in Windows .NET."""
import os
from pathlib import Path
import subprocess
import sys
from shared.paths import ROOT, RUNTIME


def build() -> Path:
    source=ROOT/'oh_desktop'/'OHDesktop.cs'
    reference=ROOT/'oh_desktop'/'OHDesktop.Reference.cs'
    navigation=ROOT/'oh_desktop'/'OHDesktop.Navigation.cs'
    patients=ROOT/'oh_desktop'/'OHDesktop.Patients.cs'
    executable=RUNTIME/'OHDesktop-v5.exe'
    compiler=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Microsoft.NET'/'Framework64'/'v4.0.30319'/'csc.exe'
    RUNTIME.mkdir(exist_ok=True)
    if not executable.exists() or executable.stat().st_mtime<max(source.stat().st_mtime,reference.stat().st_mtime,navigation.stat().st_mtime,patients.stat().st_mtime):
        subprocess.run([str(compiler),'/nologo','/codepage:65001','/target:winexe',f'/out:{executable}',
            '/reference:System.Windows.Forms.dll','/reference:System.Drawing.dll',
            '/reference:System.Web.Extensions.dll',str(source),str(reference),str(navigation),str(patients)],check=True,cwd=ROOT,
            creationflags=subprocess.CREATE_NO_WINDOW)
    return executable


def launch(db_path=None,title=None,env=None):
    executable=build()
    command=[str(executable),sys.executable,str(ROOT),str(db_path or RUNTIME/'oh.sqlite3')]
    if title: command.append(title)
    return subprocess.Popen(command,cwd=ROOT,env=env)
