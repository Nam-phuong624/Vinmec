param([long]$WindowHandle, [string]$Destination)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class WindowCapture {
  [StructLayout(LayoutKind.Sequential)] public struct Rect { public int Left, Top, Right, Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out Rect r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
  [DllImport("user32.dll")] public static extern IntPtr GetAncestor(IntPtr h, uint flags);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern IntPtr GetWindowDpiAwarenessContext(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr context);
}
'@
[WindowCapture]::SetProcessDPIAware() | Out-Null
$targetHandle = [WindowCapture]::GetAncestor([IntPtr]$WindowHandle, 2)
[WindowCapture]::SetThreadDpiAwarenessContext([WindowCapture]::GetWindowDpiAwarenessContext($targetHandle)) | Out-Null
$bounds = New-Object WindowCapture+Rect
if (-not [WindowCapture]::GetWindowRect($targetHandle, [ref]$bounds)) { throw 'Cannot read window bounds.' }
$bitmap = New-Object System.Drawing.Bitmap(($bounds.Right-$bounds.Left), ($bounds.Bottom-$bounds.Top))
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$dc = $graphics.GetHdc()
try {
    if (-not [WindowCapture]::PrintWindow($targetHandle, $dc, 2)) { throw 'Cannot capture window.' }
} finally { $graphics.ReleaseHdc($dc); $graphics.Dispose() }
try { $bitmap.Save($Destination, [System.Drawing.Imaging.ImageFormat]::Png) } finally { $bitmap.Dispose() }
