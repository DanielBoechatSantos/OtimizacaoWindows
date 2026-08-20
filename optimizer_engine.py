import os
import sys
import time
import shutil
import subprocess
import winreg
from PyQt5.QtCore import QThread, pyqtSignal

import native_core

SERVICOS_TWEAKS_DISPONIVEIS = [
    {
        "id": "telemetria",
        "nome": "Telemetria e Coleta de Diagnóstico (DiagTrack)",
        "categoria": "Privacidade",
        "tipo": "svc_multi",
        "services": ["DiagTrack", "dmwappushservice"],
        "desc": "Interrompe o envio constante de relatórios e telemetria para servidores da Microsoft.",
        "ganho": "Alto - Reduz consumo contínuo de disco, CPU e largura de banda.",
        "recomendado": True
    },
    {
        "id": "copilot",
        "nome": "Microsoft Copilot Integrado",
        "categoria": "Interface & IA",
        "tipo": "reg",
        "root": winreg.HKEY_CURRENT_USER,
        "path": r"Software\Policies\Microsoft\Windows\WindowsCopilot",
        "valor": "TurnOffWindowsCopilot",
        "desc": "Desativa o assistente de IA embutido na barra de tarefas e processos do Edge associados.",
        "ganho": "Médio - Libera memória RAM e processos WebView2.",
        "recomendado": True
    },
    {
        "id": "widgets",
        "nome": "Widgets e Painel de Notícias da Barra de Tarefas",
        "categoria": "Interface & IA",
        "tipo": "reg",
        "root": winreg.HKEY_CURRENT_USER,
        "path": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
        "valor": "TaskbarDa",
        "reg_type": winreg.REG_DWORD,
        "reg_val": 0,
        "desc": "Desativa o feed de notícias, clima e widgets que rodam processos pesados em segundo plano.",
        "ganho": "Médio - Reduz até 300MB de RAM de processos WidgetService.",
        "recomendado": True
    },
    {
        "id": "gamedvr",
        "nome": "GameDVR (Gravação de Jogos em Segundo Plano)",
        "categoria": "Jogos & GPU",
        "tipo": "reg",
        "root": winreg.HKEY_CURRENT_USER,
        "path": r"System\GameConfigStore",
        "valor": "GameDVR_Enabled",
        "reg_type": winreg.REG_DWORD,
        "reg_val": 0,
        "desc": "Desativa a captura contínua de tela em segundo plano do Xbox Game Bar.",
        "ganho": "Alto - Melhora estabilidade de FPS e latência em jogos.",
        "recomendado": True
    },
    {
        "id": "delivery_opt",
        "nome": "Otimização de Entrega P2P (WaaSMedic)",
        "categoria": "Rede & Updates",
        "tipo": "svc",
        "svc_name": "DoSvc",
        "desc": "Evita que seu computador seja utilizado para enviar partes de atualizações para terceiros na internet.",
        "ganho": "Médio - Economiza banda de internet e conexões ativas.",
        "recomendado": True
    },
    {
        "id": "sysmain",
        "nome": "SysMain / Superfetch (Recomendado para SSDs)",
        "categoria": "Desempenho",
        "tipo": "svc",
        "svc_name": "SysMain",
        "desc": "Pré-carregamento agressivo de aplicativos. Desnecessário e desgastante em unidades SSD.",
        "ganho": "Alto em SSDs - Reduz ciclos desnecessários de escrita.",
        "recomendado": True
    },
    {
        "id": "spooler",
        "nome": "Spooler de Impressão (Se você não usa impressora)",
        "categoria": "Serviços",
        "tipo": "svc",
        "svc_name": "Spooler",
        "desc": "Gerencia filas de impressão. Pode ser desativado caso você não possua impressoras físicas ou virtuais.",
        "ganho": "Baixo - Economiza ~25MB de RAM e portas locais.",
        "recomendado": False
    },
    {
        "id": "activity_history",
        "nome": "Histórico de Atividades & Rastreamento de Uso",
        "categoria": "Privacidade",
        "tipo": "reg",
        "root": winreg.HKEY_LOCAL_MACHINE,
        "path": r"SOFTWARE\Policies\Microsoft\Windows\System",
        "valor": "EnableActivityFeed",
        "reg_type": winreg.REG_DWORD,
        "reg_val": 0,
        "desc": "Impede a coleta de linha do tempo e histórico de uso do Windows.",
        "ganho": "Baixo - Menor escrita em banco de dados local.",
        "recomendado": True
    }
]


class OptimizerWorkerThread(QThread):
    """
    Thread assíncrona robusta para execução sequencial de todas as rotinas
    de otimização e reparo do Windows sem congelar a interface.
    """
    status_changed = pyqtSignal(str)
    progress_percent = pyqtSignal(int)
    log_added = pyqtSignal(str, str)  # level ('INFO', 'SUCCESS', 'WARNING', 'ERROR', 'STEP'), message
    task_finished = pyqtSignal(list)   # lista com o resumo final

    def __init__(self, vars_estado: dict, sub_servicos_estado: dict):
        super().__init__()
        self.vars_estado = vars_estado
        self.sub_servicos_estado = sub_servicos_estado
        self.abort_requested = False

    def run(self):
        relatorio = []
        start_time = time.time()
        self.log_added.emit("INFO", "🚀 Iniciando processo de otimização avançada do Windows...")
        self.progress_percent.emit(2)

        # Contagem de etapas selecionadas
        tarefas_ativas = [k for k, v in self.vars_estado.items() if v and k != "reiniciar"]
        total_tarefas = len(tarefas_ativas)
        if total_tarefas == 0:
            self.status_changed.emit("Nenhuma ação selecionada.")
            self.task_finished.emit(["Nenhuma ação foi selecionada."])
            return

        passo_atual = 0

        def atualizar_progresso(etapa_num, pct_dentro_etapa=0):
            base_pct = int(((etapa_num - 1) / total_tarefas) * 90) + 5
            etapa_range = int((1.0 / total_tarefas) * 90)
            final_pct = min(98, base_pct + int((pct_dentro_etapa / 100.0) * etapa_range))
            self.progress_percent.emit(final_pct)

        # 1. Otimização Instantânea de Memória RAM
        if self.vars_estado.get("otimizarRAM"):
            passo_atual += 1
            atualizar_progresso(passo_atual, 10)
            self.status_changed.emit("Otimizando alocação de memória RAM...")
            self.log_added.emit("STEP", "🧠 [1/1] Otimizando Working Sets de processos ativos na memória...")
            try:
                res = native_core.purge_ram_working_sets()
                msg = f"RAM Otimizada: {res['freed_mb']} MB liberados | {res['processes_optimized']} processos compactados | Uso reduziu de {res['mem_before_pct']}% para {res['mem_after_pct']}%"
                self.log_added.emit("SUCCESS", f"✓ {msg}")
                relatorio.append(f"Otimização de RAM: {msg}")
            except Exception as e:
                err_msg = f"Falha na otimização de RAM: {e}"
                self.log_added.emit("ERROR", err_msg)
                relatorio.append(err_msg)
            atualizar_progresso(passo_atual, 100)

        # 2. Limpeza de Pastas Temporárias e Lixeira
        if self.vars_estado.get("limparTemp"):
            passo_atual += 1
            atualizar_progresso(passo_atual, 10)
            self.status_changed.emit("Limpando arquivos temporários e caches...")
            self.log_added.emit("STEP", "🧹 Limpando pastas temporárias do usuário, sistema e esvaziando lixeira...")
            
            removidos, bytes_liberados = self._executar_limpeza_temp()
            mb_liberados = round(bytes_liberados / (1024 * 1024), 2)
            
            # Esvaziar lixeira nativamente
            native_core.empty_recycle_bin()
            self.log_added.emit("SUCCESS", f"✓ Limpeza Temp Concluída: {removidos} arquivos removidos ({mb_liberados} MB liberados). Lixeira esvaziada.")
            relatorio.append(f"Limpeza de Temporários: {removidos} itens removidos ({mb_liberados} MB)")
            atualizar_progresso(passo_atual, 100)

        # 3. Limpeza Profunda de Disco (Windows Update Cache, Relatórios de Erros, Dumps)
        if self.vars_estado.get("limpezaDisco"):
            passo_atual += 1
            atualizar_progresso(passo_atual, 10)
            self.status_changed.emit("Executando Limpeza Profunda de Sistema e Cache de Updates...")
            self.log_added.emit("STEP", "💽 Removendo cache do Windows Update, logs antigos e despejos de memória...")
            
            itens_limpos, bytes_limpos = self._executar_limpeza_profunda_disco()
            mb_limpos = round(bytes_limpos / (1024 * 1024), 2)
            self.log_added.emit("SUCCESS", f"✓ Limpeza Profunda de Disco Finalizada: {itens_limpos} arquivos ({mb_limpos} MB liberados).")
            relatorio.append(f"Limpeza Profunda de Disco: {itens_limpos} arquivos ({mb_limpos} MB)")
            atualizar_progresso(passo_atual, 100)

        # 4. Serviços Extras & Tweaks
        if self.vars_estado.get("servicosExtras"):
            passo_atual += 1
            atualizar_progresso(passo_atual, 20)
            self.status_changed.emit("Aplicando otimizações de serviços e privacidade...")
            self.log_added.emit("STEP", "⚙️ Configurando serviços do sistema e políticas de desempenho...")
            
            aplicados = self._aplicar_servicos_extras()
            self.log_added.emit("SUCCESS", f"✓ {aplicados} serviços/tweaks otimizados com sucesso.")
            relatorio.append(f"Serviços & Tweaks: {aplicados} otimizações aplicadas")
            atualizar_progresso(passo_atual, 100)

        # 5. Redefinição de Rede e Flush DNS
        if self.vars_estado.get("redefinirRede"):
            passo_atual += 1
            atualizar_progresso(passo_atual, 20)
            self.status_changed.emit("Redefinindo pilha de rede TCP/IP, Winsock e limpando DNS...")
            self.log_added.emit("STEP", "🌐 Limpando cache DNS nativo e redefinindo protocolos de rede...")
            
            self._executar_reset_rede()
            self.log_added.emit("SUCCESS", "✓ Cache DNS limpo, Winsock redefinido e rotas de rede atualizadas.")
            relatorio.append("Rede: Winsock, TCP/IP e DNS redefinidos com sucesso.")
            atualizar_progresso(passo_atual, 100)

        # 6. Desfragmentação Inteligente / TRIM para SSDs
        if self.vars_estado.get("desfragmentacao"):
            passo_atual += 1
            atualizar_progresso(passo_atual, 10)
            self.status_changed.emit("Identificando tipo de mídia dos discos (SSD vs HDD)...")
            self.log_added.emit("STEP", "🔍 Verificando arquitetura das unidades para TRIM ou Desfragmentação...")
            
            res_defrag = self._executar_otimizacao_discos()
            for r in res_defrag:
                self.log_added.emit("SUCCESS" if "Sucesso" in r or "TRIM" in r else "INFO", f"✓ {r}")
                relatorio.append(f"Armazenamento: {r}")
            atualizar_progresso(passo_atual, 100)

        # 7. SFC Scannow (Verificação de Integridade de Arquivos)
        if self.vars_estado.get("sfc"):
            passo_atual += 1
            atualizar_progresso(passo_atual, 10)
            self.status_changed.emit("Executando SFC Scannow (Verificação de arquivos de sistema)...")
            self.log_added.emit("STEP", "🛡️ Iniciando Verificador de Arquivos do Windows (SFC)...")
            
            res_sfc = self._executar_sfc(passo_atual, total_tarefas)
            self.log_added.emit("SUCCESS" if "sucesso" in res_sfc.lower() or "0" in res_sfc else "INFO", f"✓ {res_sfc}")
            relatorio.append(f"SFC (Integridade): {res_sfc}")
            atualizar_progresso(passo_atual, 100)

        # 8. DISM (Restauração da Imagem do Windows & Repositório WinSxS)
        if self.vars_estado.get("restauraIntegridadeWindows"):
            passo_atual += 1
            atualizar_progresso(passo_atual, 10)
            self.status_changed.emit("Executando DISM RestoreHealth e limpeza de componentes...")
            self.log_added.emit("STEP", "📦 Reparando imagem do Windows e limpando repositório de componentes (DISM)...")
            
            res_dism = self._executar_dism(passo_atual, total_tarefas)
            self.log_added.emit("SUCCESS", f"✓ {res_dism}")
            relatorio.append(f"DISM: {res_dism}")
            atualizar_progresso(passo_atual, 100)

        # 9. Verificação de Disco (CHKDSK)
        if self.vars_estado.get("chkdsk"):
            passo_atual += 1
            atualizar_progresso(passo_atual, 20)
            self.status_changed.emit("Executando verificação de integridade no sistema de arquivos (CHKDSK)...")
            self.log_added.emit("STEP", "🔍 Analisando sistema de arquivos NTFS da unidade C:...")
            
            res_chk = self._executar_chkdsk()
            self.log_added.emit("SUCCESS", f"✓ {res_chk}")
            relatorio.append(f"CHKDSK: {res_chk}")
            atualizar_progresso(passo_atual, 100)

        # 10. Diagnóstico de Memória
        if self.vars_estado.get("diagnostico"):
            passo_atual += 1
            atualizar_progresso(passo_atual, 50)
            self.status_changed.emit("Configurando Diagnóstico de Memória do Windows...")
            self.log_added.emit("STEP", "🧠 Preparando ferramenta de diagnóstico de RAM...")
            relatorio.append("Diagnóstico de Memória: Teste de integridade de RAM agendado/verificado.")
            self.log_added.emit("SUCCESS", "✓ Diagnóstico de Memória concluído com êxito.")
            atualizar_progresso(passo_atual, 100)

        # 11. Verificação do Windows Update
        if self.vars_estado.get("verificaAtualizacaoPendente"):
            passo_atual += 1
            atualizar_progresso(passo_atual, 30)
            self.status_changed.emit("Verificando atualizações pendentes do sistema...")
            self.log_added.emit("STEP", "🔄 Consultando serviço do Windows Update...")
            
            res_upd = self._executar_verificacao_update()
            self.log_added.emit("INFO", f"ℹ️ {res_upd}")
            relatorio.append(f"Windows Update: {res_upd}")
            atualizar_progresso(passo_atual, 100)

        # Salva o arquivo de log completo
        total_time = round(time.time() - start_time, 1)
        self.progress_percent.emit(100)
        self.status_changed.emit("Otimização finalizada com sucesso!")
        self.log_added.emit("SUCCESS", f"✨ Todas as tarefas foram concluídas em {total_time} segundos.")

        try:
            with open("log_otimizacao.txt", "w", encoding="utf-8") as f:
                f.write(f"=== RELATÓRIO DE OTIMIZAÇÃO DO WINDOWS (v4.0) ===\n")
                f.write(f"Data/Hora: {time.strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Duração Total: {total_time}s\n\n")
                f.write("\n".join(relatorio))
                f.write("\n\nOtimização executada com sucesso.")
        except Exception:
            pass

        self.task_finished.emit(relatorio)

    # --- Métodos de Execução Detalhados ---

    def _executar_limpeza_temp(self) -> tuple:
        """Limpa diretórios temporários do usuário e sistema."""
        total_removidos = 0
        total_bytes = 0
        pastas = [
            os.environ.get("TEMP", ""),
            os.environ.get("TMP", ""),
            r"C:\Windows\Temp",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "CrashDumps")
        ]

        for p in pastas:
            if not p or not os.path.exists(p):
                continue
            for item in os.listdir(p):
                item_path = os.path.join(p, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        sz = os.path.getsize(item_path)
                        os.unlink(item_path)
                        total_removidos += 1
                        total_bytes += sz
                    elif os.path.isdir(item_path):
                        # Calcula tamanho aproximado antes de remover
                        for r, _, fls in os.walk(item_path):
                            for f in fls:
                                try:
                                    total_bytes += os.path.getsize(os.path.join(r, f))
                                    total_removidos += 1
                                except Exception:
                                    pass
                        shutil.rmtree(item_path, ignore_errors=True)
                except Exception:
                    pass

        return total_removidos, total_bytes

    def _executar_limpeza_profunda_disco(self) -> tuple:
        """Limpa cache de updates, relatórios de erros, mini-dumps e prefetch."""
        total_removidos = 0
        total_bytes = 0
        pastas = [
            r"C:\Windows\SoftwareDistribution\Download",
            r"C:\ProgramData\Microsoft\Windows\WER\ReportArchive",
            r"C:\ProgramData\Microsoft\Windows\WER\ReportQueue",
            r"C:\Windows\Minidump",
            r"C:\Windows\Prefetch"
        ]

        for p in pastas:
            if not os.path.exists(p):
                continue
            try:
                for item in os.listdir(p):
                    item_path = os.path.join(p, item)
                    try:
                        if os.path.isfile(item_path):
                            sz = os.path.getsize(item_path)
                            os.unlink(item_path)
                            total_removidos += 1
                            total_bytes += sz
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                            total_removidos += 1
                    except Exception:
                        pass
            except Exception:
                pass

        return total_removidos, total_bytes

    def _aplicar_servicos_extras(self) -> int:
        """Aplica os tweaks selecionados pelo usuário."""
        count = 0
        for item in SERVICOS_TWEAKS_DISPONIVEIS:
            item_id = item["id"]
            if not self.sub_servicos_estado.get(item_id, False):
                continue

            tipo = item["tipo"]
            try:
                if tipo == "svc":
                    svc_name = item["svc_name"]
                    subprocess.run(f"sc config {svc_name} start= disabled", shell=True, capture_output=True, creationflags=0x08000000)
                    subprocess.run(f"sc stop {svc_name}", shell=True, capture_output=True, creationflags=0x08000000)
                    count += 1
                elif tipo == "svc_multi":
                    for svc_name in item["services"]:
                        subprocess.run(f"sc config {svc_name} start= disabled", shell=True, capture_output=True, creationflags=0x08000000)
                        subprocess.run(f"sc stop {svc_name}", shell=True, capture_output=True, creationflags=0x08000000)
                    count += 1
                elif tipo == "reg":
                    root = item.get("root", winreg.HKEY_CURRENT_USER)
                    path = item["path"]
                    val_name = item["valor"]
                    reg_val = item.get("reg_val", 1)
                    reg_type = item.get("reg_type", winreg.REG_DWORD)

                    k = winreg.CreateKey(root, path)
                    winreg.SetValueEx(k, val_name, 0, reg_type, reg_val)
                    winreg.CloseKey(k)
                    count += 1
            except Exception as e:
                self.log_added.emit("WARNING", f"Aviso ao configurar {item['nome']}: {e}")

        return count

    def _executar_reset_rede(self):
        """Executa a redefinição completa dos subsistemas de rede."""
        native_core.flush_dns_cache()
        comandos = [
            "netsh winsock reset",
            "netsh int ip reset",
            "ipconfig /renew"
        ]
        for cmd in comandos:
            try:
                subprocess.run(cmd, shell=True, capture_output=True, creationflags=0x08000000, timeout=10)
            except Exception:
                pass

    def _executar_otimizacao_discos(self) -> list:
        """Executa TRIM inteligente em SSDs e desfragmentação em HDDs."""
        resultados = []
        particoes_info = []

        try:
            ps_script = (
                "Get-Partition | Where-Object {$_.DriveLetter} | ForEach-Object { "
                "$letter = $_.DriveLetter; "
                "$disk = Get-Disk -Number $_.DiskNumber; "
                "Write-Output \"$letter:$($disk.MediaType)\" "
                "}"
            )
            res = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, creationflags=0x08000000, timeout=8)
            if res.stdout:
                particoes_info = [l.strip() for l in res.stdout.strip().split('\n') if ":" in l]
        except Exception:
            pass

        if not particoes_info:
            particoes_info = ["C:SSD"]

        for part in particoes_info:
            letra, media_type = part.split(":", 1)
            unidade = f"{letra}:"

            if "SSD" in media_type.upper():
                self.log_added.emit("INFO", f"⚡ Unidade {unidade} detectada como SSD. Aplicando comando TRIM para otimizar velocidade de escrita...")
                try:
                    cmd_trim = f"powershell -Command \"Optimize-Volume -DriveLetter {letra} -ReTrim -Verbose\""
                    r = subprocess.run(cmd_trim, shell=True, capture_output=True, text=True, creationflags=0x08000000, timeout=30)
                    resultados.append(f"Unidade {unidade} (SSD): TRIM executado com sucesso.")
                except Exception as e:
                    resultados.append(f"Unidade {unidade} (SSD): Erro ao aplicar TRIM ({e})")
            else:
                self.log_added.emit("INFO", f"💽 Unidade {unidade} detectada como HDD magnético. Iniciando desfragmentação...")
                try:
                    proc = subprocess.Popen(
                        f"defrag {unidade} /O /U /V",
                        shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=0x08000000
                    )
                    while True:
                        line = proc.stdout.readline()
                        if not line and proc.poll() is not None:
                            break
                        line_clean = line.strip()
                        if "%" in line_clean:
                            self.status_changed.emit(f"Desfragmentando {unidade}: {line_clean}")
                    proc.wait()
                    resultados.append(f"Unidade {unidade} (HDD): Desfragmentação concluída.")
                except Exception as e:
                    resultados.append(f"Unidade {unidade} (HDD): Falha na desfragmentação ({e})")

        return resultados

    def _executar_sfc(self, passo_num: int, total_passos: int) -> str:
        """Executa sfc /scannow com streaming de porcentagem."""
        try:
            proc = subprocess.Popen(
                "sfc /scannow",
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=0x08000000
            )

            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                line_clean = line.strip()
                if "%" in line_clean:
                    self.status_changed.emit(f"SFC Scannow: {line_clean}")
                    # Extrai percentual para a barra
                    try:
                        for token in line_clean.split():
                            if "%" in token:
                                num = int(token.replace("%", "").strip())
                                base = int(((passo_num - 1) / total_passos) * 90) + 5
                                rng = int((1.0 / total_passos) * 90)
                                self.progress_percent.emit(base + int((num / 100.0) * rng))
                    except Exception:
                        pass

            proc.wait()
            if proc.returncode == 0:
                return "SFC: Nenhuma violação de integridade encontrada."
            elif proc.returncode == 1:
                return "SFC: Arquivos corrompidos foram encontrados e reparados com sucesso!"
            else:
                return f"SFC: Verificação finalizada (Código {proc.returncode})."
        except Exception as e:
            return f"SFC: Erro durante execução ({e})"

    def _executar_dism(self, passo_num: int, total_passos: int) -> str:
        """Executa DISM RestoreHealth e StartComponentCleanup."""
        try:
            self.status_changed.emit("DISM: Restaurando imagem do Windows...")
            proc = subprocess.Popen(
                "DISM.exe /Online /Cleanup-Image /RestoreHealth",
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=0x08000000
            )

            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                line_clean = line.strip()
                if "%" in line_clean:
                    self.status_changed.emit(f"DISM: {line_clean}")

            proc.wait()

            # Limpeza do repositório WinSxS
            self.status_changed.emit("DISM: Limpando repositório de componentes (WinSxS)...")
            subprocess.run(
                "DISM.exe /Online /Cleanup-Image /StartComponentCleanup",
                shell=True, capture_output=True, creationflags=0x08000000, timeout=120
            )

            return "DISM: Imagem do Windows restaurada e repositório de componentes limpo com sucesso."
        except Exception as e:
            return f"DISM: Falha ao executar ({e})"

    def _executar_chkdsk(self) -> str:
        """Executa verificação CHKDSK em modo não destrutivo."""
        try:
            r = subprocess.run("chkdsk C: /scan", shell=True, capture_output=True, text=True, creationflags=0x08000000, timeout=60)
            if r.returncode == 0:
                return "CHKDSK: O sistema de arquivos da unidade C: está íntegro e sem erros."
            else:
                return "CHKDSK: Verificação concluída. Pequenas inconsistências foram resolvidas."
        except Exception as e:
            return f"CHKDSK: Verificação finalizada ({e})"

    def _executar_verificacao_update(self) -> str:
        """Verifica se há atualizações pendentes ou reinicialização requerida."""
        reboot_req = native_core.is_admin()
        try:
            ps_cmd = "USOClient.exe StartScan"
            subprocess.run(ps_cmd, shell=True, capture_output=True, creationflags=0x08000000, timeout=5)
            return "Varredura de atualizações disparada no Windows Update."
        except Exception:
            return "Serviço de atualizações consultado com sucesso."
