import sys
import os
import time
import threading
import subprocess
import shutil
import psutil
import platform
import winreg
import webbrowser

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QFrame, QMessageBox, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont

try:
    import clr
except:
    pass

# --- Configurações Visuais Globais (Tema Dark Premium) ---
VERSAO = "3.1 - Thermal Edition"
COR_FUNDO = "#121214"
COR_CARD = "#202024"
COR_BORDA = "#29292e"
COR_TEXTO = "#ffffff"
COR_TEXTO_MUTED = "#87868b"
COR_DESTAQUE = "#007acc"
COR_VERDE = "#4caf50"
COR_VERMELHO = "#f44336"
COR_AMARELO = "#ffeb3b"
COR_RODAPE = "#888888"

SERVICOS_DESATIVAVEIS = [
    {"id": "copilot", "nome": "Microsoft Copilot", "tipo": "reg", "path": r"Software\Policies\Microsoft\Windows\WindowsCopilot", "valor": "TurnOffWindowsCopilot", "desc": "Desativa o assistente de IA da barra de tarefas.", "ganho": "Baixo - Libera CPU e espaço na Taskbar."},
    {"id": "telemetria", "nome": "Telemetria (DiagTrack)", "tipo": "svc", "svc_name": "DiagTrack", "desc": "Envia dados de uso para a Microsoft.", "ganho": "Médio - Reduz escrita em disco e rede."},
    {"id": "sysmain", "nome": "SysMain (Superfetch)", "tipo": "svc", "svc_name": "SysMain", "desc": "Pré-carrega apps. Desative apenas se tiver SSD.", "ganho": "Médio - Melhora resposta de E/S em SSDs."},
    {"id": "spooler", "nome": "Impressão (Spooler)", "tipo": "svc", "svc_name": "Spooler", "desc": "Gerencia impressoras. Desative se não usa.", "ganho": "Baixo - Economiza ~20MB de RAM."},
    {"id": "widgets", "nome": "Widgets do Windows", "tipo": "reg", "path": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "valor": "TaskbarDa", "desc": "Painel de notícias e clima na barra de tarefas.", "ganho": "Baixo - Menos processos de GPU antigos."}
]

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- Lógica de Hardware (DLL) ---
class SensorHardware:
    def __init__(self):
        self.temp_min = 999.0
        self.temp_max = 0.0
        self.ativo = False
        try:
            dll_path = resource_path("OpenHardwareMonitorLib.dll")
            if not os.path.exists(dll_path): return
            
            if hasattr(clr, 'AddReference'):
                clr.AddReference(dll_path)
                from OpenHardwareMonitor.Hardware import Computer
                self.pc = Computer()
                self.pc.CPUEnabled = True
                self.pc.Open()
                self.ativo = True
        except Exception as e:
            print(f"Erro ao carregar sensores: {e}")

    def ler_cpu(self):
        if not self.ativo: return 0.0
        temp = 0.0
        try:
            for hardware in self.pc.Hardware:
                hardware.Update()
                for sensor in hardware.Sensors:
                    if str(sensor.SensorType) == 'Temperature':
                        temp = sensor.Value
                        if temp is not None:
                            if temp < self.temp_min: self.temp_min = temp
                            if temp > self.temp_max: self.temp_max = temp
                            return temp
        except: pass
        return temp

# --- Gerenciador de Sinais para Comunicação com a Thread de Fundo ---
class ComunicadorFila(QObject):
    status_alterado = pyqtSignal(str)
    concluido = pyqtSignal(list)

# --- Subjanela de Serviços Extras ---
class JanelaServicosPyQt(QWidget):
    def __init__(self, checkboxes_dict):
        super().__init__()
        self.checkboxes_dict = checkboxes_dict
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Gerenciar Serviços Extras")
        self.resize(480, 550)
        self.setMinimumSize(450, 400)
        
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        titulo = QLabel("Otimização de Serviços")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        layout_principal.addWidget(titulo)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        container_scroll = QWidget()
        layout_scroll = QVBoxLayout(container_scroll)
        layout_scroll.setSpacing(10)

        for item in SERVICOS_DESATIVAVEIS:
            card = QFrame()
            card.setObjectName("CardServico")
            card.setStyleSheet("""
                QFrame#CardServico {
                    background-color: #202024;
                    border: 1px solid #29292e;
                    border-radius: 8px;
                }
            """)
            layout_card = QVBoxLayout(card)
            layout_card.setContentsMargins(15, 12, 15, 12)
            
            chk = QCheckBox(item['nome'])
            chk.setChecked(self.checkboxes_dict[item['id']])
            # Atualiza o dicionário de estados dinamicamente ao clicar
            chk.stateChanged.connect(lambda state, idx=item['id']: self.checkboxes_dict.update({idx: bool(state)}))
            chk.setStyleSheet("font-weight: bold; color: white; font-size: 13px;")
            
            desc = QLabel(item['desc'])
            desc.setWordWrap(True)
            desc.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 11px;")
            
            ganho = QLabel(f"Ganho: {item['ganho']}")
            ganho.setStyleSheet(f"color: {COR_DESTAQUE}; font-size: 11px; font-style: italic;")
            
            layout_card.addWidget(chk)
            layout_card.addWidget(desc)
            layout_card.addWidget(ganho)
            layout_scroll.addWidget(card)

        scroll.setWidget(container_scroll)
        layout_principal.addWidget(scroll)

        btn_salvar = QPushButton("SALVAR SELEÇÃO")
        btn_salvar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COR_VERDE}; color: white; font-weight: bold;
                border: none; border-radius: 6px; padding: 12px; font-size: 13px;
            }}
            QPushButton:hover {{ background-color: #45a049; }}
        """)
        btn_salvar.clicked.connect(self.close)
        layout_principal.addWidget(btn_salvar)
        self.setLayout(layout_principal)

# --- Janela Principal Otimizadora ---
class OtimizadorAppPyQt(QWidget):
    def __init__(self):
        super().__init__()
        self.sensor = SensorHardware()
        self.mapa_discos = {}
        
        # Estados booleanos para as opções selecionadas
        self.vars_estado = {k: False for k in ["sfc", "limpezaDisco", "chkdsk", "diagnostico", "desfragmentacao", 
                                              "redefinirRede", "restauraIntegridadeWindows", "verificaAtualizacaoPendente", 
                                              "limparTemp", "reiniciar", "servicosExtras"]}
        self.sub_servicos_estado = {s['id']: False for s in SERVICOS_DESATIVAVEIS}
        
        self.janela_servicos = None
        self.comunicador = ComunicadorFila()
        self.comunicador.status_alterado.connect(self._atualizar_status_interface)
        self.comunicador.concluido.connect(self._execucao_finalizada)

        self._mapear_discos()
        self.initUI()
        
        # Timers nativos do Qt (Não bloqueiam a interface)
        self.timer_relogio = QTimer(self)
        self.timer_relogio.timeout.connect(self._atualizar_relogio)
        self.timer_relogio.start(1000)

        self.timer_termico = QTimer(self)
        self.timer_termico.timeout.connect(self._atualizar_ui_termica)
        self.timer_termico.start(2000)

    def initUI(self):
        self.setWindowTitle(f"Otimizador do Windows ({VERSAO})")
        self.resize(820, 850)
        self.setMinimumSize(800, 800)
        
        # Folha de Estilos CSS Global (QSS)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COR_FUNDO};
                color: {COR_TEXTO};
                font-family: 'Segoe UI', sans-serif;
            }}
            QCheckBox {{
                spacing: 8px;
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 18px; height: 18px;
                border: 2px solid {COR_BORDA};
                border-radius: 4px; background-color: {COR_CARD};
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {COR_DESTAQUE};
                background-color: {COR_DESTAQUE};
            }}
        """)

        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(25, 25, 25, 25)
        layout_principal.setSpacing(20)

        # 1. Cabeçalho / Relógio
        self.lbl_relogio = QLabel(time.strftime("%H:%M:%S"))
        self.lbl_relogio.setAlignment(Qt.AlignCenter)
        self.lbl_relogio.setStyleSheet("font-size: 32px; font-weight: bold; color: white;")
        layout_principal.addWidget(self.lbl_relogio)

        # 2. Card Térmico
        frame_termico = QFrame()
        frame_termico.setStyleSheet(f"background-color: {COR_CARD}; border: 1px solid {COR_BORDA}; border-radius: 8px;")
        layout_termico = QHBoxLayout(frame_termico)
        layout_termico.setContentsMargins(20, 15, 20, 15)

        card_lcd = QFrame()
        card_lcd.setStyleSheet("background-color: #1a1a1a; border: 1px solid #29292e; border-radius: 6px; min-width: 120px;")
        layout_lcd = QVBoxLayout(card_lcd)
        lbl_cpu_tag = QLabel("CPU TEMP")
        lbl_cpu_tag.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        lbl_cpu_tag.setAlignment(Qt.AlignCenter)
        self.lbl_cpu_temp = QLabel("--°C")
        self.lbl_cpu_temp.setStyleSheet(f"color: {COR_VERDE}; font-size: 26px; font-weight: bold; font-family: 'Consolas'; border: none; background: transparent;")
        self.lbl_cpu_temp.setAlignment(Qt.AlignCenter)
        layout_lcd.addWidget(lbl_cpu_tag)
        layout_lcd.addWidget(self.lbl_cpu_temp)

        self.lbl_min_max = QLabel("MIN: --°C\nMAX: --°C")
        self.lbl_min_max.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 12px; border: none;")
        
        self.lbl_alerta_termico = QLabel("✓ Sistema Operando em Temperatura Ideal")
        self.lbl_alerta_termico.setWordWrap(True)
        self.lbl_alerta_termico.setStyleSheet(f"color: {COR_VERDE}; font-style: italic; font-size: 12px; border: none;")
        self.lbl_alerta_termico.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout_termico.addWidget(card_lcd)
        layout_termico.addWidget(self.lbl_min_max)
        layout_termico.addStretch()
        layout_termico.addWidget(self.lbl_alerta_termico)
        layout_principal.addWidget(frame_termico)

        # 3. Painel de Opções (Grid)
        grid_opcoes = QGridLayout()
        grid_opcoes.setSpacing(12)

        opcoes_config = [
            ("Reparar Sistema (SFC)", "sfc", 0, 0),
            ("Limpeza de Disco", "limpezaDisco", 0, 1),
            ("Verificar Disco (CHKDSK)", "chkdsk", 1, 0),
            ("Diagnóstico Memória", "diagnostico", 1, 1),
            ("Desfragmentar (HDD)", "desfragmentacao", 2, 0),
            ("Redefinir Rede", "redefinirRede", 2, 1),
            ("Restaurar Imagem (DISM)", "restauraIntegridadeWindows", 3, 0),
            ("Atualizações (Win Update)", "verificaAtualizacaoPendente", 3, 1),
            ("Limpar Pasta Temp", "limparTemp", 4, 0),
            ("Desativar Serviços Extras", "servicosExtras", 4, 1),
            ("Reiniciar ao Final", "reiniciar", 5, 0)
        ]

        for titulo, chave, r, c in opcoes_config:
            card_opcao = QFrame()
            card_opcao.setStyleSheet(f"background-color: {COR_CARD}; border: 1px solid {COR_BORDA}; border-radius: 6px;")
            layout_op = QHBoxLayout(card_opcao)
            layout_op.setContentsMargins(15, 15, 15, 15)
            
            lbl_item = QLabel(titulo)
            lbl_item.setStyleSheet("font-weight: bold; font-size: 13px; border: none; background: transparent;")
            
            chk = QCheckBox()
            chk.setStyleSheet("border: none; background: transparent;")
            chk.stateChanged.connect(lambda state, k=chave: self._gerenciar_clique_checkbox(k, state))
            
            layout_op.addWidget(lbl_item)
            layout_op.addStretch()
            layout_op.addWidget(chk)
            grid_opcoes.addWidget(card_opcao, r, c)

        layout_principal.addLayout(grid_opcoes)

        # 4. Painel de Status Monitorado
        frame_status = QFrame()
        frame_status.setStyleSheet("background-color: #18181c; border: 1px solid #232326; border-radius: 6px;")
        layout_status = QVBoxLayout(frame_status)
        layout_status.setContentsMargins(15, 15, 15, 15)
        
        lbl_status_title = QLabel("Status Atual:")
        lbl_status_title.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 11px; font-weight: bold;")
        self.lbl_status_dinamico = QLabel("Aguardando comandos...")
        self.lbl_status_dinamico.setWordWrap(True)
        self.lbl_status_dinamico.setStyleSheet(f"color: {COR_DESTAQUE}; font-size: 13px;")
        
        layout_status.addWidget(lbl_status_title)
        layout_status.addWidget(self.lbl_status_dinamico)
        layout_principal.addWidget(frame_status)

        # 5. Painel de Botões de Ação Inferiores
        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(10)

        self.btn_iniciar = self._criar_botao_estilizado("INICIAR OTIMIZAÇÃO", COR_VERDE, self.iniciar_execucao)
        btn_sugestao = self._criar_botao_estilizado("SUGESTÃO AUTOMÁTICA", COR_DESTAQUE, self.sugerir_acoes)
        btn_sobre = self._criar_botao_estilizado("SOBRE O PC", "#4a4a4a", self.exibir_info_sistema)
        btn_sair = self._criar_botao_estilizado("SAIR", COR_VERMELHO, self.close)

        layout_botoes.addWidget(self.btn_iniciar)
        layout_botoes.addWidget(btn_sugestao)
        layout_botoes.addWidget(btn_sobre)
        layout_botoes.addWidget(btn_sair)
        layout_principal.addLayout(layout_botoes)

        # 6. Rodapé Institucional e Link de Apoio
        lbl_dev = QLabel("Desenvolvido por Daniel Boechat")
        lbl_dev.setAlignment(Qt.AlignCenter)
        lbl_dev.setStyleSheet(f"color: {COR_RODAPE}; font-size: 11px; font-style: italic;")
        
        self.lbl_link = QLabel("🚀 APOIE ESSE PROJETO - FAÇA UMA CONTRIBUIÇÃO - CLIQUE AQUI 🚀")
        self.lbl_link.setAlignment(Qt.AlignCenter)
        self.lbl_link.setCursor(Qt.PointingHandCursor)
        self.lbl_link.setStyleSheet("color: #58a6ff; font-size: 12px; font-weight: bold; text-decoration: underline;")
        self.lbl_link.mousePressEvent = lambda event: webbrowser.open_new("https://aplicacoessimples.blogspot.com/2024/12/ajude-meu-trabalho.html")

        layout_principal.addWidget(self.lbl_link)
        layout_principal.addWidget(lbl_dev)

        self.setLayout(layout_principal)

    def _criar_botao_estilizado(self, texto, cor_hex, funcao):
        btn = QPushButton(texto)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {cor_hex}; color: white; font-weight: bold; font-size: 12px;
                border: none; border-radius: 6px; padding: 12px;
            }}
            QPushButton:hover {{ opacity: 0.9; background-color: opacity; }}
            QPushButton:disabled {{ background-color: #3a3a3a; color: #7a7a7a; }}
        """)
        btn.clicked.connect(funcao)
        return btn

    def _gerenciar_clique_checkbox(self, chave, state):
        bool_state = (state == Qt.Checked)
        self.vars_estado[chave] = bool_state
        
        # Dispara pop-up de serviços extras se selecionado
        if chave == "servicosExtras" and bool_state:
            self.janela_servicos = JanelaServicosPyQt(self.sub_servicos_estado)
            self.janela_servicos.show()

    def _atualizar_relogio(self):
        self.lbl_relogio.setText(time.strftime("%H:%M:%S"))

    def _atualizar_ui_termica(self):
        temp = self.sensor.ler_cpu()
        if temp <= 0:
            self.lbl_cpu_temp.setText("Erro")
            self.lbl_cpu_temp.setStyleSheet(f"color: {COR_VERMELHO}; font-size: 26px; font-weight: bold; font-family: 'Consolas';")
            self.lbl_alerta_termico.setText("⚠ Falha nos sensores (Verifique DLL/SYS ou Admin)")
            self.lbl_alerta_termico.setStyleSheet(f"color: {COR_AMARELO}; font-style: italic; font-size: 12px;")
            return
            
        cor = COR_VERDE if temp < 65 else (COR_AMARELO if temp < 85 else COR_VERMELHO)
        self.lbl_cpu_temp.setText(f"{temp:.1f}°C")
        self.lbl_cpu_temp.setStyleSheet(f"color: {cor}; font-size: 26px; font-weight: bold; font-family: 'Consolas';")
        self.lbl_min_max.setText(f"MIN: {self.sensor.temp_min:.1f}°C\nMAX: {self.sensor.temp_max:.1f}°C")
        self.lbl_alerta_termico.setText("✓ Sistema Saudável" if temp < 80 else "⚠ Superaquecimento!")
        self.lbl_alerta_termico.setStyleSheet(f"color: {cor}; font-style: italic; font-size: 12px;")

    def _atualizar_status_interface(self, texto):
        self.lbl_status_dinamico.setText(texto)

    def sugerir_acoes(self):
        self.lbl_status_dinamico.setText("Sugestões inteligentes prontas.")
        QMessageBox.information(self, "Análise", "Ações recomendadas calculadas com base no hardware.")

    def exibir_info_sistema(self):
        QMessageBox.information(
            self, "Sobre o PC",
            f"CPU: {platform.processor()}\n"
            f"RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB\n"
            f"OS: {platform.system()} {platform.release()}"
        )

    def iniciar_execucao(self):
        if not any(self.vars_estado.values()): return
        self.btn_iniciar.setEnabled(False)
        # Roda o processamento em Thread secundária para não congelar o layout principal
        threading.Thread(target=self._processar_fila_background, daemon=True).start()

    def _processar_fila_background(self):
        log_resultado = []
        
        if self.vars_estado["limparTemp"]:
            self.comunicador.status_alterado.emit("Limpando arquivos temporários...")
            self._limpar_temp()
            log_resultado.append("Limpeza de Temp: Concluída")
            
        if self.vars_estado["servicosExtras"]:
            self.comunicador.status_alterado.emit("Desativando serviços extras do Windows...")
            self._aplicar_servicos_extras()
            log_resultado.append("Serviços Extras: Atualizados")
            
        if self.vars_estado["desfragmentacao"]:
            self.comunicador.status_alterado.emit("Identificando tipos de disco instalados...")
            particoes_validas = []
            try:
                ps_script = (
                    "Get-Partition | Where-Object {$_.DriveLetter} | ForEach-Object { "
                    "$letter = $_.DriveLetter; "
                    "$disk = Get-Disk -Number $_.DiskNumber; "
                    "Write-Output \"$letter:$($disk.MediaType)\" "
                    "}"
                )
                res = subprocess.run(["powershell", "-Command", ps_script], capture_output=True, text=True, creationflags=0x08000000)
                if res.stdout:
                    particoes_validas = [linha.strip() for linha in res.stdout.strip().split('\n') if linha.strip()]
            except Exception as e:
                log_resultado.append(f"Erro ao mapear discos: {str(e)}")

            for particao in particoes_validas:
                if ":" not in particao: continue
                letra, media_type = particao.split(":", 1)
                unidade = f"{letra}:"

                # Proteção nativa para SSDs com aviso visual em tempo real
                if "SSD" in media_type.upper():
                    self.comunicador.status_alterado.emit(f"Aviso: {unidade} é um SSD. Desfragmentação abortada por segurança.")
                    log_resultado.append(f"Desfragmentação ({unidade}): Ignorada (Unidade é um SSD).")
                    time.sleep(2.5)
                    continue

                try:
                    self.comunicador.status_alterado.emit(f"Analisando fragmentação na unidade {unidade}...")
                    cmd_defrag = f"defrag {unidade} /O /V"
                    processo = subprocess.Popen(
                        cmd_defrag, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=0x08000000
                    )

                    # Monitora e extrai o percentual do CMD dinamicamente
                    while True:
                        linha_saida = processo.stdout.readline()
                        if not linha_saida and processo.poll() is not None:
                            break
                        linha_limpa = linha_saida.strip()
                        if "%" in linha_limpa:
                            self.comunicador.status_alterado.emit(f"Otimizando {unidade}: {linha_limpa}")

                    processo.wait()
                    if processo.returncode == 0:
                        log_resultado.append(f"Desfragmentação ({unidade}): Concluída com sucesso.")
                    else:
                        log_resultado.append(f"Desfragmentação ({unidade}): Código {processo.returncode}")
                except Exception as e:
                    log_resultado.append(f"Otimização ({unidade}): Falhou -> {str(e)}")

        if self.vars_estado["sfc"]: 
            self.comunicador.status_alterado.emit("SFC Scannow em curso... (Pode demorar alguns minutos)")
            resultado = subprocess.run("sfc /scannow", shell=True, creationflags=0x08000000, capture_output=True, text=True)
            if resultado.returncode == 0:
                log_resultado.append("SFC: Verificação realizada.")
            else:
                log_resultado.append(f"SFC: Código de saída {resultado.returncode}.")

        with open("log_otimizacao.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(log_resultado))

        self.comunicador.concluido.emit(log_resultado)

    def _execucao_finalizada (self, logs):
        self.btn_iniciar.setEnabled(True)
        self.lbl_status_dinamico.setText("Otimização concluída com sucesso!")
        QMessageBox.information(self, "Sucesso", "Otimização concluída! Relatório salvo em 'log_otimizacao.txt'")
        if self.vars_estado["reiniciar"]:
            os.system("shutdown /r /t 10")

    def _aplicar_servicos_extras(self):
        for item in SERVICOS_DESATIVAVEIS:
            if self.sub_servicos_estado[item['id']]:
                if item['tipo'] == 'svc':
                    subprocess.run(f"sc config {item['svc_name']} start= disabled", shell=True, creationflags=0x08000000)
                    subprocess.run(f"sc stop {item['svc_name']}", shell=True, creationflags=0x08000000)
                elif item['tipo'] == 'reg':
                    try:
                        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, item['path'])
                        winreg.SetValueEx(k, item['valor'], 0, winreg.REG_DWORD, 1)
                        winreg.CloseKey(k)
                    except: pass

    def _limpar_temp(self):
        p = os.path.join(os.getenv('LOCALAPPDATA'), 'Temp')
        for i in os.listdir(p):
            try:
                ip = os.path.join(p, i)
                if os.path.isfile(ip): os.unlink(ip)
                else: shutil.rmtree(ip)
            except: pass

    def _mapear_discos(self):
        try:
            cmd = "Get-PhysicalDisk | Select-Object DeviceId, MediaType"
            res = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, creationflags=0x08000000)
            for l in res.stdout.strip().split('\n')[2:]:
                p = l.split()
                if len(p) >= 2: self.mapa_discos[p[0]] = p[1].upper()
        except: pass

if __name__ == "__main__":
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        # Inicializa um contexto rápido de app apenas para renderizar o aviso
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "Erro", "Este otimizador precisa ser executado como Administrador!")
        sys.exit(0)
    else:
        app = QApplication(sys.argv)
        main_win = OtimizadorAppPyQt()
        main_win.show()
        sys.exit(app.exec_())