import os
import sys
import psutil
import time
import subprocess
import winreg

def calculate_folder_size(folder_path: str, max_files: int = 2000) -> int:
    """Calcula rapidamente o tamanho de uma pasta sem travar o sistema."""
    total_size = 0
    file_count = 0
    try:
        if not os.path.exists(folder_path):
            return 0
        for root, _, files in os.walk(folder_path):
            for f in files:
                file_count += 1
                if file_count > max_files:
                    break
                try:
                    fp = os.path.join(root, f)
                    if os.path.isfile(fp):
                        total_size += os.path.getsize(fp)
                except Exception:
                    pass
            if file_count > max_files:
                break
    except Exception:
        pass
    return total_size


def check_pending_reboot() -> bool:
    """Verifica se o Windows possui reinicialização pendente por atualizações."""
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired")
    ]
    for root_key, subkey in reg_paths:
        try:
            k = winreg.OpenKey(root_key, subkey, 0, winreg.KEY_READ)
            winreg.CloseKey(k)
            return True
        except Exception:
            pass
    return False


def run_smart_diagnostic() -> dict:
    """
    Realiza uma varredura diagnóstica completa no sistema e calcula o Health Score (0-100%).
    Retorna lista de problemas identificados e ações recomendadas correspondentes.
    """
    issues = []
    recommended_keys = set()
    health_score = 100

    # 1. Análise de Memória RAM
    mem = psutil.virtual_memory()
    if mem.percent >= 80:
        deduction = 18
        health_score -= deduction
        issues.append({
            "title": f"Pressão Elevada de Memória RAM ({mem.percent}% em uso)",
            "desc": f"Seu sistema está com {mem.used / (1024**3):.1f} GB de {mem.total / (1024**3):.1f} GB ocupados. A otimização de Working Set liberará espaço imediatamente.",
            "severity": "alta",
            "action_key": "otimizarRAM"
        })
        recommended_keys.add("otimizarRAM")
    elif mem.percent >= 65:
        deduction = 8
        health_score -= deduction
        issues.append({
            "title": f"Uso Moderado de Memória RAM ({mem.percent}%)",
            "desc": "Processos em segundo plano podem ser otimizados para melhorar a responsividade do sistema.",
            "severity": "media",
            "action_key": "otimizarRAM"
        })
        recommended_keys.add("otimizarRAM")

    # 2. Análise de Arquivos Temporários e Lixo do Sistema
    temp_user = os.environ.get("TEMP", "")
    temp_system = r"C:\Windows\Temp"
    softwaredist = r"C:\Windows\SoftwareDistribution\Download"

    size_user_temp = calculate_folder_size(temp_user)
    size_sys_temp = calculate_folder_size(temp_system)
    size_sw_dist = calculate_folder_size(softwaredist)
    total_junk_bytes = size_user_temp + size_sys_temp + size_sw_dist
    total_junk_mb = round(total_junk_bytes / (1024 * 1024), 1)

    if total_junk_mb > 1500:
        health_score -= 15
        issues.append({
            "title": f"Grande Volume de Arquivos Temporários ({total_junk_mb} MB)",
            "desc": "Foram detectados mais de 1.5 GB de cache acumulado, logs antigos e instaladores residuais ocupando espaço no disco.",
            "severity": "alta",
            "action_key": "limparTemp"
        })
        recommended_keys.add("limparTemp")
        recommended_keys.add("limpezaDisco")
    elif total_junk_mb > 300:
        health_score -= 8
        issues.append({
            "title": f"Arquivos Temporários Acumulados ({total_junk_mb} MB)",
            "desc": "Limpar caches e pastas temporárias liberará espaço e acelerará o carregamento de arquivos.",
            "severity": "media",
            "action_key": "limparTemp"
        })
        recommended_keys.add("limparTemp")
        recommended_keys.add("limpezaDisco")

    # 3. Análise de Espaço Livre na Unidade C:
    try:
        usage_c = psutil.disk_usage("C:\\")
        free_c_gb = usage_c.free / (1024**3)
        free_c_pct = (usage_c.free / usage_c.total) * 100.0

        if free_c_pct < 12 or free_c_gb < 15.0:
            health_score -= 25
            issues.append({
                "title": f"Espaço em Disco Crítico na Unidade C: ({free_c_gb:.1f} GB livres / {free_c_pct:.1f}%)",
                "desc": "O Windows necessita de pelo menos 15% de espaço livre para paginação de memória e atualizações sem travamentos.",
                "severity": "alta",
                "action_key": "limpezaDisco"
            })
            recommended_keys.add("limpezaDisco")
            recommended_keys.add("limparTemp")
            recommended_keys.add("restauraIntegridadeWindows")
        elif free_c_pct < 20:
            health_score -= 10
            issues.append({
                "title": f"Espaço em Disco Atenção na Unidade C: ({free_c_gb:.1f} GB livres)",
                "desc": "Recomenda-se realizar uma limpeza de disco profunda para recuperar espaço útil.",
                "severity": "media",
                "action_key": "limpezaDisco"
            })
            recommended_keys.add("limpezaDisco")
    except Exception:
        pass

    # 4. Tempo de Atividade (Uptime)
    uptime_sec = time.time() - psutil.boot_time()
    uptime_hours = uptime_sec / 3600.0
    if uptime_hours > 120:  # > 5 dias
        health_score -= 12
        days = int(uptime_hours // 24)
        issues.append({
            "title": f"Computador Ligado Há Muito Tempo ({days} dias consecutivos)",
            "desc": "Longos períodos sem reiniciar causam fragmentação de memória e acúmulo de identificadores de processos órfãos.",
            "severity": "media",
            "action_key": "reiniciar"
        })
        recommended_keys.add("otimizarRAM")
        recommended_keys.add("reiniciar")
    elif uptime_hours > 48:
        health_score -= 5
        issues.append({
            "title": f"Tempo de Atividade Prolongado ({int(uptime_hours)} horas)",
            "desc": "Uma otimização de memória RAM e renovação do cache de rede é recomendada.",
            "severity": "baixa",
            "action_key": "otimizarRAM"
        })
        recommended_keys.add("otimizarRAM")

    # 5. Reinicialização Pendente do Windows
    if check_pending_reboot():
        health_score -= 10
        issues.append({
            "title": "Atualizações do Windows com Reinicialização Pendente",
            "desc": "Existem atualizações do sistema aguardando reinicialização para serem concluídas com êxito.",
            "severity": "media",
            "action_key": "reiniciar"
        })
        recommended_keys.add("reiniciar")

    # 6. Verificação de Integridade e Otimização Recomendada Padrão
    recommended_keys.add("sfc")
    recommended_keys.add("desfragmentacao")
    recommended_keys.add("redefinirRede")
    recommended_keys.add("servicosExtras")

    health_score = max(15, min(100, health_score))

    # Determina rótulo e cor
    if health_score >= 85:
        status_label = "Excelente"
        color_hex = "#10B981"
    elif health_score >= 70:
        status_label = "Bom (Otimizações Recomendadas)"
        color_hex = "#3B82F6"
    elif health_score >= 50:
        status_label = "Atenção (Gargalos Detectados)"
        color_hex = "#F59E0B"
    else:
        status_label = "Crítico (Manutenção Urgente)"
        color_hex = "#EF4444"

    return {
        "score": health_score,
        "status_label": status_label,
        "color_hex": color_hex,
        "total_junk_mb": total_junk_mb,
        "issues": issues,
        "recommended_keys": list(recommended_keys)
    }
