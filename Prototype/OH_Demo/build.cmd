@echo off
rem Biên dịch OHDemo.exe bằng csc.exe có sẵn trong .NET Framework 4 của Windows (không cần cài thêm).
set CSC=%WINDIR%\Microsoft.NET\Framework64\v4.0.30319\csc.exe
if not exist "%CSC%" set CSC=%WINDIR%\Microsoft.NET\Framework\v4.0.30319\csc.exe
"%CSC%" /nologo /codepage:65001 /target:winexe /out:"%~dp0OHDemo.exe" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll "%~dp0OHDemo.cs"
if errorlevel 1 (echo Build that bai & exit /b 1)
echo Da tao %~dp0OHDemo.exe
