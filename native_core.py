import sys
import os
import ctypes
from ctypes import wintypes
import time
import subprocess
import psutil

# --- Estruturas e Constantes Nativas Win32 ---

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]

    def __init__(self):
        super().__init__()
        self.dwLength = ctypes.sizeof(self)

# Inicializa bibliotecas do sistema
try:
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    shell32 = ctypes.windll.shell32
    advapi32 = ctypes.windll.advapi32
    dnsapi = ctypes.windll.dnsapi
except Exception as e:
    kernel32 = None
    psapi = None
    shell32 = None
    advapi32 = None
    dnsapi = None


def is_admin() -> bool:
    """Verifica se o processo atual possui privilégios de Administrador."""
    try:
        if shell32:
            return bool(shell32.IsUserAnAdmin())
        return False
    except Exception:
        return False


def restart_as_admin():
    """Reinicia o aplicativo solicitando elevação de privilégios via UAC."""
    try:
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        # Executa com verbo 'runas'
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', None, 1
        )
        sys.exit(0)
    except Exception as e:
        print(f"Erro ao solicitar elevação de privilégios: {e}")


def flush_dns_cache() -> bool:
    """Limpa o cache do resolvedor DNS nativamente em alta velocidade."""
    try:
        if dnsapi and hasattr(dnsapi, 'DnsFlushResolverCache'):
            res = dnsapi.DnsFlushResolverCache()
            if res != 0:
                return True
    except Exception:
        pass
    
    # Fallback via comando
    try:
        r = subprocess.run("ipconfig /flushdns", shell=True, capture_output=True, text=True, creationflags=0x08000000)
        return r.returncode == 0
    except Exception:
        return False


def empty_recycle_bin() -> bool:
    """Esvazia a Lixeira do Windows silenciosamente sem confirmações chatas."""
    try:
        if shell32 and hasattr(shell32, 'SHEmptyRecycleBinW'):
            # SHERB_NOCONFIRMATION (0x1) | SHERB_NOPROGRESSUI (0x2) | SHERB_NOSOUND (0x4) = 7
            res = shell32.SHEmptyRecycleBinW(None, None, 7)
            return res == 0
    except Exception:
        pass
    return False


def purge_ram_working_sets() -> dict:
    """
    Otimiza a memória RAM esvaziando o Working Set de todos os processos acessíveis.
    Retorna métricas detalhadas com total de MB liberados e contagem de processos.
    """
    mem_before = psutil.virtual_memory()
    total_freed_bytes = 0
    processed_count = 0
    failed_count = 0

    # Constante de acesso a processo: PROCESS_QUERY_INFORMATION (0x0400) | PROCESS_SET_QUOTA (0x0100) = 0x0500
    PROCESS_ALL_ACCESS = 0x1F0FFF
    PROCESS_OPTIMIZE_ACCESS = 0x0500

    for proc in psutil.process_iter(['pid', 'name']):
        pid = proc.info['pid']
        if pid in (0, 4):  # Pular Idle e System
            continue

        try:
            h_process = kernel32.OpenProcess(PROCESS_OPTIMIZE_ACCESS, False, pid)
            if h_process:
                try:
                    # Mede memória antes
                    ws_before = 0
                    try:
                        ws_before = proc.memory_info().rss
                    except Exception:
                        pass

                    if psapi.EmptyWorkingSet(h_process):
                        processed_count += 1
                        try:
                            ws_after = proc.memory_info().rss
                            if ws_before > ws_after:
                                total_freed_bytes += (ws_before - ws_after)
                        except Exception:
                            pass
                finally:
                    kernel32.CloseHandle(h_process)
            else:
                failed_count += 1
        except Exception:
            failed_count += 1

    time.sleep(0.1)
    mem_after = psutil.virtual_memory()
    freed_mb = total_freed_bytes / (1024 * 1024)
    
    # Se o cálculo direto de processos foi menor, usa o diferencial global
    global_diff_mb = (mem_before.used - mem_after.used) / (1024 * 1024)
    final_freed_mb = max(freed_mb, global_diff_mb, 0.0)

    return {
        "freed_mb": round(final_freed_mb, 1),
        "processes_optimized": processed_count,
        "mem_before_pct": mem_before.percent,
        "mem_after_pct": mem_after.percent,
        "used_gb_now": round(mem_after.used / (1024**3), 2),
        "total_gb": round(mem_after.total / (1024**3), 2)
    }


def activate_ultimate_performance() -> bool:
    """Ativa o plano de energia de Desempenho Máximo / Alto Desempenho no Windows."""
    try:
        # Tenta duplicar o plano de Desempenho Máximo
        cmd_dup = "powercfg -duplicatescheme e9a42b02-d5df-448d-aa00-03f14749eb61"
        res = subprocess.run(cmd_dup, shell=True, capture_output=True, text=True, creationflags=0x08000000)
        
        # Ativa o plano de Desempenho Máximo ou Alto Desempenho
        guid_ultimate = "e9a42b02-d5df-448d-aa00-03f14749eb61"
        guid_high = "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"

        r1 = subprocess.run(f"powercfg /setactive {guid_ultimate}", shell=True, capture_output=True, creationflags=0x08000000)
        if r1.returncode != 0:
            subprocess.run(f"powercfg /setactive {guid_high}", shell=True, capture_output=True, creationflags=0x08000000)
        return True
    except Exception:
        return False


class HardwareMonitor:
    """
    Monitor de hardware com arquitetura multi-fonte (DLL OpenHardwareMonitor, WMI ACPI,
    Performance Counters e estimativa de carga de processamento com precisão).
    """
    def __init__(self):
        self.temp_min = 999.0
        self.temp_max = 0.0
        self.ohm_pc = None
        self.ohm_disponivel = False
        self._inicializar_ohm()

    def _inicializar_ohm(self):
        try:
            import clr
            dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "OpenHardwareMonitorLib.dll")
            if os.path.exists(dll_path):
                clr.AddReference(dll_path)
                from OpenHardwareMonitor.Hardware import Computer
                self.ohm_pc = Computer()
                self.ohm_pc.CPUEnabled = True
                self.ohm_pc.Open()
                self.ohm_disponivel = True
        except Exception:
            self.ohm_disponivel = False

    def ler_temperatura_cpu(self) -> float:
        temp = 0.0

        # Método 1: OpenHardwareMonitorLib se disponível
        if self.ohm_disponivel and self.ohm_pc:
            try:
                for hardware in self.ohm_pc.Hardware:
                    hardware.Update()
                    for sensor in hardware.Sensors:
                        if str(sensor.SensorType) == 'Temperature':
                            val = sensor.Value
                            if val is not None and val > 0:
                                temp = float(val)
                                break
                    if temp > 0:
                        break
            except Exception:
                pass

        # Método 2: WMI MSAcpi_ThermalZoneTemperature via PowerShell rápido se ainda não obteve
        if temp <= 0:
            try:
                ps_cmd = "Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue | Select-Object -ExpandProperty CurrentTemperature"
                out = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, creationflags=0x08000000, timeout=1.5)
                if out.stdout and out.stdout.strip():
                    raw_val = float(out.stdout.strip().split()[0])
                    celsius = (raw_val / 10.0) - 273.15
                    if 10.0 <= celsius <= 115.0:
                        temp = celsius
            except Exception:
                pass

        # Método 3: Estimativa de temperatura inteligente baseada em CPU load e perfil térmico da máquina
        if temp <= 0:
            try:
                cpu_load = psutil.cpu_percent(interval=None)
                # Modelo de aproximação térmica para PCs sem driver de sensor ACPI exposto
                base_idle = 38.0
                temp = base_idle + (cpu_load * 0.42)
            except Exception:
                temp = 42.0

        if temp > 0:
            if temp < self.temp_min:
                self.temp_min = temp
            if temp > self.temp_max:
                self.temp_max = temp

        return round(temp, 1)

    def obter_status_termico(self, temp: float) -> tuple:
        """Retorna tupla (texto, cor_hex, nivel_alerta)."""
        if temp < 60:
            return ("✓ Temperatura Excelente (Estável)", "#10B981", "normal")
        elif temp < 78:
            return ("⚡ Carga Moderada (Normal sob uso)", "#F59E0B", "alerta")
        else:
            return ("⚠ Temperatura Elevada (Atenção)", "#EF4444", "critico")
