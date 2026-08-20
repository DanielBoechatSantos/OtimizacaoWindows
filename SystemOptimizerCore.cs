using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Runtime.InteropServices;
using System.Text;

namespace SystemOptimizerCore
{
    public static class NativeMethods
    {
        [DllImport("psapi.dll", SetLastError = true)]
        public static extern int EmptyWorkingSet(IntPtr hwProc);

        [DllImport("dnsapi.dll", EntryPoint = "DnsFlushResolverCache", SetLastError = true)]
        public static extern int DnsFlushResolverCache();

        [DllImport("shell32.dll", CharSet = CharSet.Unicode)]
        public static extern int SHEmptyRecycleBin(IntPtr hwnd, string pszRootPath, uint dwFlags);

        public const uint SHERB_NOCONFIRMATION = 0x00000001;
        public const uint SHERB_NOPROGRESSUI   = 0x00000002;
        public const uint SHERB_NOSOUND        = 0x00000004;

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        public class MEMORYSTATUSEX
        {
            public uint dwLength;
            public uint dwMemoryLoad;
            public ulong ullTotalPhys;
            public ulong ullAvailPhys;
            public ulong ullTotalPageFile;
            public ulong ullAvailPageFile;
            public ulong ullTotalVirtual;
            public ulong ullAvailVirtual;
            public ulong ullAvailExtendedVirtual;

            public MEMORYSTATUSEX()
            {
                this.dwLength = (uint)Marshal.SizeOf(typeof(MEMORYSTATUSEX));
            }
        }

        [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        public static extern bool GlobalMemoryStatusEx([In, Out] MEMORYSTATUSEX lpBuffer);

        [DllImport("kernel32.dll")]
        public static extern ulong GetTickCount64();
    }

    public class SystemOptimizer
    {
        public static long OptimizeProcessMemory(int processId)
        {
            try
            {
                using (Process proc = Process.GetProcessById(processId))
                {
                    if (proc.HasExited) return 0;
                    long before = proc.WorkingSet64;
                    NativeMethods.EmptyWorkingSet(proc.Handle);
                    proc.Refresh();
                    long after = proc.WorkingSet64;
                    return Math.Max(0, before - after);
                }
            }
            catch
            {
                return 0;
            }
        }

        public static string OptimizeAllProcesses()
        {
            int successCount = 0;
            int totalCount = 0;
            long totalFreedBytes = 0;

            Process[] processes = Process.GetProcesses();
            foreach (Process proc in processes)
            {
                totalCount++;
                try
                {
                    if (proc.Id == 0 || proc.Id == 4) continue; // Skip Idle & System
                    long before = proc.WorkingSet64;
                    int result = NativeMethods.EmptyWorkingSet(proc.Handle);
                    if (result != 0)
                    {
                        successCount++;
                        proc.Refresh();
                        long after = proc.WorkingSet64;
                        if (before > after)
                        {
                            totalFreedBytes += (before - after);
                        }
                    }
                }
                catch
                {
                    // Ignore processes with denied access
                }
                finally
                {
                    proc.Dispose();
                }
            }

            double freedMB = totalFreedBytes / (1024.0 * 1024.0);
            return string.Format("{0:F2}|{1}|{2}", freedMB, successCount, totalCount);
        }

        public static bool FlushDnsCache()
        {
            try
            {
                int result = NativeMethods.DnsFlushResolverCache();
                return result != 0;
            }
            catch
            {
                return false;
            }
        }

        public static bool EmptyRecycleBin()
        {
            try
            {
                uint flags = NativeMethods.SHERB_NOCONFIRMATION | NativeMethods.SHERB_NOPROGRESSUI | NativeMethods.SHERB_NOSOUND;
                int result = NativeMethods.SHEmptyRecycleBin(IntPtr.Zero, null, flags);
                return result == 0;
            }
            catch
            {
                return false;
            }
        }

        public static string GetMemoryInfo()
        {
            try
            {
                NativeMethods.MEMORYSTATUSEX memStatus = new NativeMethods.MEMORYSTATUSEX();
                if (NativeMethods.GlobalMemoryStatusEx(memStatus))
                {
                    double totalGB = memStatus.ullTotalPhys / (1024.0 * 1024.0 * 1024.0);
                    double availGB = memStatus.ullAvailPhys / (1024.0 * 1024.0 * 1024.0);
                    double usedGB = totalGB - availGB;
                    uint loadPercent = memStatus.dwMemoryLoad;

                    return string.Format("{0:F2}|{1:F2}|{2:F2}|{3}", totalGB, usedGB, availGB, loadPercent);
                }
            }
            catch
            {
            }
            return "0.0|0.0|0.0|0";
        }

        public static double GetSystemUptimeHours()
        {
            try
            {
                ulong millis = NativeMethods.GetTickCount64();
                return millis / (1000.0 * 60.0 * 60.0);
            }
            catch
            {
                return 0.0;
            }
        }

        public static double GetThermalReadingWMI()
        {
            try
            {
                using (ManagementObjectSearcher searcher = new ManagementObjectSearcher(@"root\WMI", "SELECT * FROM MSAcpi_ThermalZoneTemperature"))
                {
                    foreach (ManagementObject obj in searcher.Get())
                    {
                        double tempKelvinTenths = Convert.ToDouble(obj["CurrentTemperature"]);
                        double tempCelsius = (tempKelvinTenths / 10.0) - 273.15;
                        if (tempCelsius > 0 && tempCelsius < 125)
                        {
                            return tempCelsius;
                        }
                    }
                }
            }
            catch
            {
            }
            return 0.0;
        }

        public static string GetDriveSummary()
        {
            StringBuilder sb = new StringBuilder();
            try
            {
                DriveInfo[] drives = DriveInfo.GetDrives();
                foreach (DriveInfo drive in drives)
                {
                    if (drive.IsReady && drive.DriveType == DriveType.Fixed)
                    {
                        double totalGB = drive.TotalSize / (1024.0 * 1024.0 * 1024.0);
                        double freeGB = drive.TotalFreeSpace / (1024.0 * 1024.0 * 1024.0);
                        double usedGB = totalGB - freeGB;
                        double freePct = (freeGB / totalGB) * 100.0;

                        if (sb.Length > 0) sb.Append(";");
                        sb.Append(string.Format("{0}|{1:F1}|{2:F1}|{3:F1}|{4:F1}|{5}",
                            drive.Name.TrimEnd('\\'), totalGB, usedGB, freeGB, freePct, drive.DriveFormat));
                    }
                }
            }
            catch
            {
            }
            return sb.ToString();
        }

        public static bool SetHighPerformancePowerPlan()
        {
            try
            {
                ProcessStartInfo psi = new ProcessStartInfo
                {
                    FileName = "powercfg.exe",
                    Arguments = "/setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", // High Performance GUID
                    CreateNoWindow = true,
                    UseShellExecute = false,
                    WindowStyle = ProcessWindowStyle.Hidden
                };
                using (Process p = Process.Start(psi))
                {
                    p.WaitForExit(3000);
                    return p.ExitCode == 0;
                }
            }
            catch
            {
                return false;
            }
        }
    }
}
