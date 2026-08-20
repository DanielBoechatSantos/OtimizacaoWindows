import os
import sys
import platform
import subprocess
import time
import datetime
import psutil
import socket

def format_bytes(bytes_val: int) -> str:
    """Converte bytes para representação legível (GB, MB)."""
    if bytes_val >= 1024**3:
        return f"{bytes_val / (1024**3):.2f} GB"
    elif bytes_val >= 1024**2:
        return f"{bytes_val / (1024**2):.2f} MB"
    elif bytes_val >= 1024:
        return f"{bytes_val / 1024:.2f} KB"
    return f"{bytes_val} B"


def get_cpu_info() -> dict:
    """Obtém detalhes aprofundados do processador."""
    info = {
        "model": platform.processor() or "Processador x86/x64",
        "cores_physical": psutil.cpu_count(logical=False) or 1,
        "cores_logical": psutil.cpu_count(logical=True) or 1,
        "current_load_pct": psutil.cpu_percent(interval=0.1),
        "freq_current_mhz": 0.0,
        "freq_max_mhz": 0.0
    }
    
    try:
        freq = psutil.cpu_freq()
        if freq:
            info["freq_current_mhz"] = round(freq.current, 1)
            info["freq_max_mhz"] = round(freq.max, 1)
    except Exception:
        pass

    # Tenta obter nome comercial exato da CPU via PowerShell
    try:
        ps_cmd = "Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name"
        res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, creationflags=0x08000000, timeout=2.0)
        if res.stdout and res.stdout.strip():
            info["model"] = res.stdout.strip().split('\n')[0].strip()
    except Exception:
        pass

    return info


def get_memory_info() -> dict:
    """Obtém informações completas da memória RAM e slots."""
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()

    info = {
        "total_gb": round(vm.total / (1024**3), 2),
        "used_gb": round(vm.used / (1024**3), 2),
        "available_gb": round(vm.available / (1024**3), 2),
        "percent_used": vm.percent,
        "swap_total_gb": round(swap.total / (1024**3), 2),
        "swap_used_gb": round(swap.used / (1024**3), 2),
        "slots_info": []
    }

    try:
        ps_cmd = "Get-CimInstance Win32_PhysicalMemory | Select-Object Capacity, Speed, Manufacturer, MemoryType, FormFactor | ConvertTo-Json"
        res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, creationflags=0x08000000, timeout=2.5)
        if res.stdout and res.stdout.strip():
            import json
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                data = [data]
            for slot in data:
                cap_gb = round(int(slot.get("Capacity", 0)) / (1024**3), 1)
                speed = slot.get("Speed", "N/A")
                mfg = slot.get("Manufacturer", "Genérico")
                info["slots_info"].append(f"{cap_gb} GB @ {speed} MHz ({mfg})")
    except Exception:
        pass

    return info


def get_storage_info() -> list:
    """Obtém detalhes de todos os discos físicos e partições montadas."""
    discos = []
    
    # Mapear tipos de mídia (SSD vs HDD)
    media_types = {}
    try:
        ps_script = (
            "Get-Partition | Where-Object {$_.DriveLetter} | ForEach-Object { "
            "$letter = $_.DriveLetter; "
            "$disk = Get-Disk -Number $_.DiskNumber; "
            "Write-Output \"$letter:$($disk.MediaType):$($disk.Model)\" "
            "}"
        )
        res = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, creationflags=0x08000000, timeout=3.0)
        if res.stdout:
            for line in res.stdout.strip().split('\n'):
                if ":" in line:
                    parts = line.strip().split(":", 2)
                    letra = parts[0].upper()
                    m_type = parts[1] if len(parts) > 1 else "Unknow"
                    model = parts[2] if len(parts) > 2 else "Drive"
                    media_types[letra] = {"type": m_type, "model": model}
    except Exception:
        pass

    for part in psutil.disk_partitions(all=False):
        try:
            if "cdrom" in part.opts or part.fstype == "":
                continue
            usage = psutil.disk_usage(part.mountpoint)
            letra = part.device.replace(":\\", "").replace(":", "").upper()
            
            meta = media_types.get(letra, {"type": "Desconhecido", "model": "Disco Local"})
            tipo_formatado = meta["type"]
            if "SSD" in tipo_formatado.upper():
                tipo_formatado = "⚡ SSD (Alta Velocidade)"
            elif "HDD" in tipo_formatado.upper() or "UNSPECIFIED" in tipo_formatado.upper():
                tipo_formatado = "💽 HDD / Disco Magnético"

            discos.append({
                "mountpoint": part.mountpoint,
                "device": part.device,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent_used": usage.percent,
                "percent_free": round(100.0 - usage.percent, 1),
                "media_type": tipo_formatado,
                "model": meta.get("model", "Unidade de Armazenamento")
            })
        except Exception:
            pass

    return discos


def get_gpu_info() -> list:
    """Obtém dados das placas de vídeo instaladas."""
    gpus = []
    try:
        ps_cmd = "Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion, AdapterRAM, VideoProcessor, CurrentHorizontalResolution, CurrentVerticalResolution, CurrentRefreshRate | ConvertTo-Json"
        res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, creationflags=0x08000000, timeout=2.5)
        if res.stdout and res.stdout.strip():
            import json
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                data = [data]
            for item in data:
                ram_val = item.get("AdapterRAM") or 0
                vram_gb = round(int(ram_val) / (1024**3), 2) if ram_val else 0.0
                h_res = item.get("CurrentHorizontalResolution", "")
                v_res = item.get("CurrentVerticalResolution", "")
                res_str = f"{h_res}x{v_res} @ {item.get('CurrentRefreshRate', '')}Hz" if h_res else "N/A"
                
                gpus.append({
                    "name": item.get("Name", "Adaptador Gráfico"),
                    "driver_version": item.get("DriverVersion", "N/A"),
                    "vram_gb": vram_gb,
                    "resolution": res_str
                })
    except Exception:
        pass
    
    if not gpus:
        gpus.append({"name": "Adaptador de Vídeo Padrão", "driver_version": "N/A", "vram_gb": 0, "resolution": "N/A"})
    return gpus


def get_os_info() -> dict:
    """Obtém detalhes do Sistema Operacional, Build e Uptime."""
    boot_time = psutil.boot_time()
    uptime_sec = time.time() - boot_time
    
    days = int(uptime_sec // 86400)
    hours = int((uptime_sec % 86400) // 3600)
    minutes = int((uptime_sec % 3600) // 60)
    uptime_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"

    info = {
        "os_name": f"{platform.system()} {platform.release()}",
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "computer_name": socket.gethostname(),
        "uptime_str": uptime_str,
        "uptime_hours": round(uptime_sec / 3600.0, 1),
        "boot_time_str": datetime.datetime.fromtimestamp(boot_time).strftime("%d/%m/%Y %H:%M:%S")
    }

    try:
        ps_cmd = "Get-CimInstance Win32_OperatingSystem | Select-Object Caption, OSArchitecture, Version, BuildNumber | ConvertTo-Json"
        res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, creationflags=0x08000000, timeout=2.0)
        if res.stdout and res.stdout.strip():
            import json
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                info["os_name"] = data.get("Caption", info["os_name"]).strip()
                info["build_number"] = data.get("BuildNumber", "N/A")
    except Exception:
        pass

    return info


def get_motherboard_info() -> dict:
    """Obtém dados da Placa-mãe e BIOS."""
    info = {
        "manufacturer": "N/A",
        "product": "N/A",
        "bios_version": "N/A",
        "bios_date": "N/A"
    }
    try:
        ps_cmd = "Get-CimInstance Win32_BaseBoard | Select-Object Manufacturer, Product | ConvertTo-Json"
        res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, creationflags=0x08000000, timeout=2.0)
        if res.stdout and res.stdout.strip():
            import json
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                info["manufacturer"] = data.get("Manufacturer", "N/A").strip()
                info["product"] = data.get("Product", "N/A").strip()
    except Exception:
        pass

    try:
        ps_cmd = "Get-CimInstance Win32_BIOS | Select-Object SMBIOSBIOSVersion, ReleaseDate | ConvertTo-Json"
        res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True, creationflags=0x08000000, timeout=2.0)
        if res.stdout and res.stdout.strip():
            import json
            data = json.loads(res.stdout)
            if isinstance(data, dict):
                info["bios_version"] = data.get("SMBIOSBIOSVersion", "N/A").strip()
                info["bios_date"] = str(data.get("ReleaseDate", "N/A"))[:10]
    except Exception:
        pass

    return info


def get_network_info() -> list:
    """Obtém adaptadores de rede ativos e endereçamento IP."""
    adapters = []
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for name, addr_list in addrs.items():
            stat = stats.get(name)
            is_up = stat.isup if stat else False
            if not is_up:
                continue

            ipv4 = "N/A"
            mac = "N/A"
            for a in addr_list:
                if a.family == socket.AF_INET:
                    ipv4 = a.address
                elif getattr(a, 'family', None) == getattr(psutil, 'AF_LINK', None) or hasattr(a, 'address') and len(a.address) == 17:
                    mac = a.address

            if ipv4 != "N/A" and not ipv4.startswith("127."):
                adapters.append({
                    "name": name,
                    "ipv4": ipv4,
                    "mac": mac,
                    "speed_mbps": stat.speed if stat else 0
                })
    except Exception:
        pass

    return adapters


def generate_full_system_report() -> dict:
    """Coleta e agrega todas as informações de hardware e software do sistema."""
    return {
        "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "os": get_os_info(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "storage": get_storage_info(),
        "gpu": get_gpu_info(),
        "motherboard": get_motherboard_info(),
        "network": get_network_info()
    }


def export_report_as_text(report: dict) -> str:
    """Formata o relatório do sistema em texto legível para exportação."""
    lines = []
    lines.append("=" * 65)
    lines.append("       RELATÓRIO COMPLETO DE HARDWARE E SISTEMA")
    lines.append(f"       Gerado em: {report['timestamp']}")
    lines.append("=" * 65)
    lines.append("")

    # OS
    os_info = report["os"]
    lines.append("🖥️ SISTEMA OPERACIONAL")
    lines.append(f"  • Sistema: {os_info.get('os_name')}")
    lines.append(f"  • Versão/Build: {os_info.get('os_version')} (Build {os_info.get('build_number', 'N/A')})")
    lines.append(f"  • Arquitetura: {os_info.get('architecture')}")
    lines.append(f"  • Nome do Computador: {os_info.get('computer_name')}")
    lines.append(f"  • Tempo de Atividade (Uptime): {os_info.get('uptime_str')}")
    lines.append(f"  • Inicializado em: {os_info.get('boot_time_str')}")
    lines.append("")

    # CPU
    cpu = report["cpu"]
    lines.append("⚡ PROCESSADOR (CPU)")
    lines.append(f"  • Modelo: {cpu.get('model')}")
    lines.append(f"  • Núcleos Físicos: {cpu.get('cores_physical')} | Processadores Lógicos: {cpu.get('cores_logical')}")
    lines.append(f"  • Frequência Atual: {cpu.get('freq_current_mhz')} MHz (Máx: {cpu.get('freq_max_mhz')} MHz)")
    lines.append(f"  • Carga Atual: {cpu.get('current_load_pct')}%")
    lines.append("")

    # RAM
    mem = report["memory"]
    lines.append("🧠 MEMÓRIA RAM")
    lines.append(f"  • Total: {mem.get('total_gb')} GB | Em Uso: {mem.get('used_gb')} GB ({mem.get('percent_used')}%) | Livre: {mem.get('available_gb')} GB")
    if mem.get("slots_info"):
        lines.append("  • Módulos Instalados:")
        for s in mem["slots_info"]:
            lines.append(f"    - {s}")
    lines.append("")

    # Placa-mãe
    mb = report["motherboard"]
    lines.append("🔌 PLACA-MÃE & BIOS")
    lines.append(f"  • Fabricante: {mb.get('manufacturer')} | Modelo: {mb.get('product')}")
    lines.append(f"  • Versão da BIOS: {mb.get('bios_version')} (Data: {mb.get('bios_date')})")
    lines.append("")

    # GPU
    lines.append("🎮 PLACAS DE VÍDEO (GPU)")
    for g in report["gpu"]:
        lines.append(f"  • {g.get('name')}")
        lines.append(f"    Driver: {g.get('driver_version')} | VRAM: {g.get('vram_gb')} GB | Resolução: {g.get('resolution')}")
    lines.append("")

    # Discos
    lines.append("💽 UNIDADES DE ARMAZENAMENTO")
    for d in report["storage"]:
        lines.append(f"  • Unidade {d.get('mountpoint')} ({d.get('model')})")
        lines.append(f"    Tipo: {d.get('media_type')} | Sistema: {d.get('fstype')}")
        lines.append(f"    Capacidade: {d.get('total_gb')} GB | Usado: {d.get('used_gb')} GB ({d.get('percent_used')}%) | Livre: {d.get('free_gb')} GB ({d.get('percent_free')}%)")
    lines.append("")

    # Rede
    lines.append("🌐 CONECTIVIDADE DE REDE")
    for n in report["network"]:
        lines.append(f"  • Adaptador: {n.get('name')} | IPv4: {n.get('ipv4')} | MAC: {n.get('mac')}")
    lines.append("")

    lines.append("=" * 65)
    lines.append("Desenvolvido para máxima performance e diagnóstico avançado.")
    lines.append("=" * 65)

    return "\n".join(lines)
