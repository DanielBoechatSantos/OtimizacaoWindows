import sys
import os
import time
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QCheckBox, QFrame, QMessageBox, QScrollArea,
    QProgressBar, QTextEdit, QFileDialog, QDialog, QTabWidget, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor, QTextCursor

import native_core
import system_info
import smart_advisor
from optimizer_engine import OptimizerWorkerThread, SERVICOS_TWEAKS_DISPONIVEIS

# --- Identidade Visual Premium (Dark Glassmorphism) ---
VERSAO = "4.0 - Advanced Maintenance Edition"
COR_BG_DARK = "#0F1117"
COR_CARD = "#1A1D27"
COR_CARD_HOVER = "#222736"
COR_BORDA = "#2D3345"
COR_TEXTO = "#F3F4F6"
COR_TEXTO_MUTED = "#9CA3AF"
COR_AZUL_ACCENT = "#3B82F6"
COR_AZUL_HOVER = "#2563EB"
COR_VERDE = "#10B981"
COR_VERDE_HOVER = "#059669"
COR_VERMELHO = "#EF4444"
COR_AMARELO = "#F59E0B"
COR_ROXO = "#8B5CF6"
COR_CONSOLE_BG = "#0B0C10"

def get_app_icon():
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img", "favicon.png")
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    return QIcon()


# --- Subjanela de Serviços Extras & Tweaks ---
class JanelaServicosExtras(QDialog):
    def __init__(self, sub_servicos_estado: dict, parent=None):
        super().__init__(parent)
        self.sub_servicos_estado = sub_servicos_estado
        self.checkboxes = {}
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Configuração Avançada de Serviços e Privacidade")
        self.resize(650, 680)
        self.setMinimumSize(580, 500)
        self.setWindowIcon(get_app_icon())
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COR_BG_DARK};
                color: {COR_TEXTO};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(24, 24, 24, 24)
        layout_principal.setSpacing(16)

        # Cabeçalho
        lbl_titulo = QLabel("⚙️ Gerenciador de Serviços & Desempenho")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout_principal.addWidget(lbl_titulo)

        lbl_desc = QLabel(
            "Desative recursos e serviços de telemetria desnecessários para reduzir consumo de CPU, "
            "memória RAM e tempo de resposta do sistema operacional."
        )
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 12px;")
        layout_principal.addWidget(lbl_desc)

        # Barra de Ações Rápidas da Janela
        layout_acoes_topo = QHBoxLayout()
        btn_sel_recomendados = QPushButton("✨ Selecionar Recomendados")
        btn_sel_recomendados.setStyleSheet(f"""
            QPushButton {{
                background-color: #2D3748; color: #E2E8F0; font-size: 12px; font-weight: bold;
                border: 1px solid #4A5568; border-radius: 6px; padding: 8px 14px;
            }}
            QPushButton:hover {{ background-color: #4A5568; }}
        """)
        btn_sel_recomendados.clicked.connect(self._selecionar_recomendados)

        btn_limpar_tudo = QPushButton("Desmarcar Todos")
        btn_limpar_tudo.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {COR_TEXTO_MUTED}; font-size: 12px;
                border: 1px solid #374151; border-radius: 6px; padding: 8px 14px;
            }}
            QPushButton:hover {{ color: white; border-color: #4B5563; }}
        """)
        btn_limpar_tudo.clicked.connect(self._desmarcar_todos)

        layout_acoes_topo.addWidget(btn_sel_recomendados)
        layout_acoes_topo.addWidget(btn_limpar_tudo)
        layout_acoes_topo.addStretch()
        layout_principal.addLayout(layout_acoes_topo)

        # Scroll Area com os cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout_cards = QVBoxLayout(container)
        layout_cards.setSpacing(12)
        layout_cards.setContentsMargins(0, 0, 8, 0)

        for item in SERVICOS_TWEAKS_DISPONIVEIS:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: {COR_CARD};
                    border: 1px solid {COR_BORDA};
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    border: 1px solid #3E465E;
                    background-color: {COR_CARD_HOVER};
                }}
            """)
            layout_card = QVBoxLayout(card)
            layout_card.setContentsMargins(16, 14, 16, 14)
            layout_card.setSpacing(6)

            layout_card_header = QHBoxLayout()
            chk = QCheckBox(item["nome"])
            chk.setChecked(self.sub_servicos_estado.get(item["id"], False))
            chk.setStyleSheet("font-weight: bold; color: white; font-size: 13px; border: none; background: transparent;")
            chk.stateChanged.connect(lambda state, idx=item["id"]: self.sub_servicos_estado.update({idx: bool(state)}))
            self.checkboxes[item["id"]] = chk

            badge_cat = QLabel(item["categoria"])
            badge_cat.setStyleSheet(f"""
                color: {COR_AZUL_ACCENT}; background-color: #1E293B; font-size: 10px; font-weight: bold;
                border: 1px solid #2563EB; border-radius: 4px; padding: 2px 8px;
            """)

            layout_card_header.addWidget(chk)
            layout_card_header.addStretch()
            layout_card_header.addWidget(badge_cat)
            layout_card.addLayout(layout_card_header)

            desc = QLabel(item["desc"])
            desc.setWordWrap(True)
            desc.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 11px; border: none; background: transparent; padding-left: 24px;")
            layout_card.addWidget(desc)

            ganho = QLabel(f"⚡ Ganho estimado: {item['ganho']}")
            ganho.setStyleSheet(f"color: {COR_VERDE}; font-size: 11px; font-style: italic; border: none; background: transparent; padding-left: 24px;")
            layout_card.addWidget(ganho)

            layout_cards.addWidget(card)

        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

        # Botão Salvar
        btn_salvar = QPushButton("SALVAR CONFIGURAÇÃO")
        btn_salvar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COR_VERDE}; color: white; font-weight: bold;
                border: none; border-radius: 6px; padding: 12px; font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {COR_VERDE_HOVER}; }}
        """)
        btn_salvar.clicked.connect(self.accept)
        layout_principal.addWidget(btn_salvar)

    def _selecionar_recomendados(self):
        for item in SERVICOS_TWEAKS_DISPONIVEIS:
            if item.get("recomendado", False):
                self.checkboxes[item["id"]].setChecked(True)
                self.sub_servicos_estado[item["id"]] = True

    def _desmarcar_todos(self):
        for item_id, chk in self.checkboxes.items():
            chk.setChecked(False)
            self.sub_servicos_estado[item_id] = False


# --- Subjanela de Diagnóstico & Sugestão Inteligente ---
class JanelaSugestaoInteligente(QDialog):
    def __init__(self, diagnostico: dict, callback_aplicar=None, parent=None):
        super().__init__(parent)
        self.diag = diagnostico
        self.callback_aplicar = callback_aplicar
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Diagnóstico Inteligente do Sistema")
        self.resize(620, 600)
        self.setWindowIcon(get_app_icon())
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COR_BG_DARK};
                color: {COR_TEXTO};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Card de Health Score
        score = self.diag.get("score", 100)
        color = self.diag.get("color_hex", COR_VERDE)
        status_label = self.diag.get("status_label", "Excelente")

        card_score = QFrame()
        card_score.setStyleSheet(f"""
            QFrame {{
                background-color: {COR_CARD};
                border: 2px solid {color};
                border-radius: 12px;
            }}
        """)
        layout_score = QHBoxLayout(card_score)
        layout_score.setContentsMargins(20, 16, 20, 16)

        lbl_score_num = QLabel(f"{score}")
        lbl_score_num.setStyleSheet(f"font-size: 42px; font-weight: bold; color: {color}; font-family: 'Consolas';")
        
        layout_score_text = QVBoxLayout()
        lbl_score_title = QLabel("Índice de Saúde do Sistema")
        lbl_score_title.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 11px; font-weight: bold; text-transform: uppercase;")
        lbl_score_status = QLabel(status_label)
        lbl_score_status.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        lbl_junk = QLabel(f"Lixo e Caches Acumulados no Disco: {self.diag.get('total_junk_mb', 0)} MB")
        lbl_junk.setStyleSheet(f"color: {COR_AZUL_ACCENT}; font-size: 12px;")

        layout_score_text.addWidget(lbl_score_title)
        layout_score_text.addWidget(lbl_score_status)
        layout_score_text.addWidget(lbl_junk)

        layout_score.addWidget(lbl_score_num)
        layout_score.addSpacing(20)
        layout_score.addLayout(layout_score_text)
        layout_score.addStretch()
        layout.addWidget(card_score)

        # Título da lista de problemas
        lbl_issues_title = QLabel("🔍 Diagnóstico Detalhado e Oportunidades de Otimização:")
        lbl_issues_title.setStyleSheet("font-size: 13px; font-weight: bold; color: white;")
        layout.addWidget(lbl_issues_title)

        # Scroll com problemas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        container = QWidget()
        layout_issues = QVBoxLayout(container)
        layout_issues.setSpacing(10)
        layout_issues.setContentsMargins(0, 0, 8, 0)

        issues = self.diag.get("issues", [])
        if not issues:
            lbl_sem_prob = QLabel("✓ Nenhum gargalo crítico detectado. Seu computador está operando em excelente estado!")
            lbl_sem_prob.setStyleSheet(f"color: {COR_VERDE}; font-size: 13px; padding: 20px;")
            layout_issues.addWidget(lbl_sem_prob)
        else:
            for issue in issues:
                card_i = QFrame()
                sev = issue.get("severity", "media")
                b_color = COR_VERMELHO if sev == "alta" else (COR_AMARELO if sev == "media" else COR_AZUL_ACCENT)
                card_i.setStyleSheet(f"""
                    QFrame {{
                        background-color: {COR_CARD};
                        border-left: 4px solid {b_color};
                        border-top: 1px solid {COR_BORDA};
                        border-right: 1px solid {COR_BORDA};
                        border-bottom: 1px solid {COR_BORDA};
                        border-radius: 6px;
                    }}
                """)
                layout_ci = QVBoxLayout(card_i)
                layout_ci.setContentsMargins(14, 10, 14, 10)

                lbl_it = QLabel(issue.get("title", ""))
                lbl_it.setStyleSheet("font-size: 13px; font-weight: bold; color: white;")
                lbl_id = QLabel(issue.get("desc", ""))
                lbl_id.setWordWrap(True)
                lbl_id.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 11px;")

                layout_ci.addWidget(lbl_it)
                layout_ci.addWidget(lbl_id)
                layout_issues.addWidget(card_i)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Botões de Ação
        layout_botoes = QHBoxLayout()
        btn_aplicar = QPushButton("✨ APLICAR OTIMIZAÇÕES RECOMENDADAS")
        btn_aplicar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COR_AZUL_ACCENT}; color: white; font-weight: bold; font-size: 13px;
                border: none; border-radius: 6px; padding: 12px;
            }}
            QPushButton:hover {{ background-color: {COR_AZUL_HOVER}; }}
        """)
        btn_aplicar.clicked.connect(self._aplicar_e_fechar)

        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet(f"""
            QPushButton {{
                background-color: #2D3748; color: white; font-weight: bold; font-size: 13px;
                border: none; border-radius: 6px; padding: 12px; min-width: 100px;
            }}
            QPushButton:hover {{ background-color: #4A5568; }}
        """)
        btn_fechar.clicked.connect(self.close)

        layout_botoes.addWidget(btn_aplicar)
        layout_botoes.addWidget(btn_fechar)
        layout.addLayout(layout_botoes)

    def _aplicar_e_fechar(self):
        if self.callback_aplicar:
            self.callback_aplicar(self.diag.get("recommended_keys", []))
        self.accept()


# --- Subjanela Completa "Sobre o PC" ---
class JanelaSobrePC(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.report = system_info.generate_full_system_report()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Informações Completas do Sistema & Hardware")
        self.resize(750, 720)
        self.setMinimumSize(680, 550)
        self.setWindowIcon(get_app_icon())
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COR_BG_DARK};
                color: {COR_TEXTO};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QTabWidget::pane {{
                border: 1px solid {COR_BORDA};
                background: {COR_CARD};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: #151821;
                color: {COR_TEXTO_MUTED};
                padding: 10px 18px;
                font-weight: bold;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background: {COR_CARD};
                color: {COR_AZUL_ACCENT};
                border-bottom: 2px solid {COR_AZUL_ACCENT};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Cabeçalho
        layout_topo = QHBoxLayout()
        lbl_titulo = QLabel("🖥️ Painel de Hardware & Sistema")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        
        btn_exportar = QPushButton("📄 Exportar Relatório (.TXT)")
        btn_exportar.setStyleSheet(f"""
            QPushButton {{
                background-color: #2D3748; color: #E2E8F0; font-weight: bold; font-size: 11px;
                border: 1px solid #4A5568; border-radius: 6px; padding: 6px 14px;
            }}
            QPushButton:hover {{ background-color: #4A5568; }}
        """)
        btn_exportar.clicked.connect(self._exportar_relatorio)

        layout_topo.addWidget(lbl_titulo)
        layout_topo.addStretch()
        layout_topo.addWidget(btn_exportar)
        layout.addLayout(layout_topo)

        # Abas
        tabs = QTabWidget()

        # Aba 1: Visão Geral / Sistema
        tabs.addTab(self._criar_aba_visao_geral(), "Visão Geral")
        # Aba 2: Processador & Memória
        tabs.addTab(self._criar_aba_cpu_ram(), "CPU & Memória")
        # Aba 3: Armazenamento (Discos)
        tabs.addTab(self._criar_aba_discos(), "Armazenamento")
        # Aba 4: Gráficos & Rede
        tabs.addTab(self._criar_aba_gpu_rede(), "GPU & Rede")

        layout.addWidget(tabs)

        btn_fechar = QPushButton("FECHAR")
        btn_fechar.setStyleSheet(f"""
            QPushButton {{
                background-color: #2D3748; color: white; font-weight: bold; font-size: 12px;
                border: none; border-radius: 6px; padding: 10px;
            }}
            QPushButton:hover {{ background-color: #4A5568; }}
        """)
        btn_fechar.clicked.connect(self.close)
        layout.addWidget(btn_fechar)

    def _criar_item_info(self, rotulo: str, valor: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: transparent;")
        l = QVBoxLayout(w)
        l.setContentsMargins(0, 4, 0, 4)
        l.setSpacing(2)
        
        lbl_r = QLabel(rotulo)
        lbl_r.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 11px; font-weight: bold; text-transform: uppercase;")
        lbl_v = QLabel(valor)
        lbl_v.setStyleSheet("color: white; font-size: 13px;")
        lbl_v.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        l.addWidget(lbl_r)
        l.addWidget(lbl_v)
        return w

    def _criar_aba_visao_geral(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        l = QVBoxLayout(container)
        l.setContentsMargins(18, 18, 18, 18)
        l.setSpacing(12)

        os_i = self.report["os"]
        mb_i = self.report["motherboard"]

        l.addWidget(self._criar_item_info("Sistema Operacional", f"{os_i.get('os_name')} (Build {os_i.get('build_number')})"))
        l.addWidget(self._criar_item_info("Arquitetura do SO", os_i.get("architecture", "")))
        l.addWidget(self._criar_item_info("Nome do Computador", os_i.get("computer_name", "")))
        l.addWidget(self._criar_item_info("Tempo de Atividade (Uptime)", os_i.get("uptime_str", "")))
        l.addWidget(self._criar_item_info("Inicializado em", os_i.get("boot_time_str", "")))
        l.addWidget(self._criar_item_info("Placa-Mãe", f"{mb_i.get('manufacturer')} {mb_i.get('product')}"))
        l.addWidget(self._criar_item_info("BIOS", f"Versão {mb_i.get('bios_version')} (Data: {mb_i.get('bios_date')})"))
        l.addStretch()

        scroll.setWidget(container)
        return scroll

    def _criar_aba_cpu_ram(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        l = QVBoxLayout(container)
        l.setContentsMargins(18, 18, 18, 18)
        l.setSpacing(12)

        cpu = self.report["cpu"]
        mem = self.report["memory"]

        l.addWidget(self._criar_item_info("Modelo do Processador", cpu.get("model", "")))
        l.addWidget(self._criar_item_info("Núcleos & Threads", f"{cpu.get('cores_physical')} Núcleos Físicos / {cpu.get('cores_logical')} Processadores Lógicos"))
        l.addWidget(self._criar_item_info("Frequência de Operação", f"Atual: {cpu.get('freq_current_mhz')} MHz | Máxima: {cpu.get('freq_max_mhz')} MHz"))
        l.addWidget(self._criar_item_info("Capacidade Total de Memória RAM", f"{mem.get('total_gb')} GB"))
        l.addWidget(self._criar_item_info("Uso Atual de Memória", f"{mem.get('used_gb')} GB ocupados ({mem.get('percent_used')}%) | {mem.get('available_gb')} GB disponíveis"))
        
        if mem.get("slots_info"):
            slots_str = "\n".join([f"• {s}" for s in mem["slots_info"]])
            l.addWidget(self._criar_item_info("Módulos de Memória Instalados", slots_str))

        l.addStretch()
        scroll.setWidget(container)
        return scroll

    def _criar_aba_discos(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        l = QVBoxLayout(container)
        l.setContentsMargins(18, 18, 18, 18)
        l.setSpacing(14)

        for d in self.report["storage"]:
            card_d = QFrame()
            card_d.setStyleSheet(f"background-color: #12141C; border: 1px solid {COR_BORDA}; border-radius: 8px;")
            ld = QVBoxLayout(card_d)
            ld.setContentsMargins(14, 12, 14, 12)
            ld.setSpacing(6)

            header_d = QHBoxLayout()
            lbl_mount = QLabel(f"Unidade {d.get('mountpoint')} ({d.get('model')})")
            lbl_mount.setStyleSheet("font-weight: bold; color: white; font-size: 13px;")
            
            lbl_tipo = QLabel(d.get("media_type"))
            lbl_tipo.setStyleSheet(f"color: {COR_AZUL_ACCENT}; font-size: 11px; font-weight: bold;")

            header_d.addWidget(lbl_mount)
            header_d.addStretch()
            header_d.addWidget(lbl_tipo)
            ld.addLayout(header_d)

            lbl_det = QLabel(
                f"Capacidade Total: {d.get('total_gb')} GB  |  Em Uso: {d.get('used_gb')} GB ({d.get('percent_used')}%)  |  Livre: {d.get('free_gb')} GB  |  Sistema: {d.get('fstype')}"
            )
            lbl_det.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 11px;")
            ld.addWidget(lbl_det)

            pbar = QProgressBar()
            pbar.setValue(int(d.get("percent_used", 0)))
            pbar.setTextVisible(False)
            pbar.setFixedHeight(8)
            pbar_color = COR_VERDE if d.get("percent_used", 0) < 80 else (COR_AMARELO if d.get("percent_used", 0) < 90 else COR_VERMELHO)
            pbar.setStyleSheet(f"""
                QProgressBar {{ background-color: #2D3345; border: none; border-radius: 4px; }}
                QProgressBar::chunk {{ background-color: {pbar_color}; border-radius: 4px; }}
            """)
            ld.addWidget(pbar)

            l.addWidget(card_d)

        l.addStretch()
        scroll.setWidget(container)
        return scroll

    def _criar_aba_gpu_rede(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        l = QVBoxLayout(container)
        l.setContentsMargins(18, 18, 18, 18)
        l.setSpacing(12)

        l.addWidget(QLabel("🎮 Placas de Vídeo (GPU)"))
        for g in self.report["gpu"]:
            l.addWidget(self._criar_item_info(g.get("name", "GPU"), f"Driver: {g.get('driver_version')} | VRAM: {g.get('vram_gb')} GB | Resolução: {g.get('resolution')}"))

        l.addSpacing(10)
        l.addWidget(QLabel("🌐 Adaptadores de Rede Ativos"))
        for n in self.report["network"]:
            l.addWidget(self._criar_item_info(n.get("name", "Rede"), f"IPv4: {n.get('ipv4')} | Endereço Físico (MAC): {n.get('mac')}"))

        l.addStretch()
        scroll.setWidget(container)
        return scroll

    def _exportar_relatorio(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar Relatório do Sistema", "relatorio_pc.txt", "Arquivos de Texto (*.txt)")
        if caminho:
            try:
                texto = system_info.export_report_as_text(self.report)
                with open(caminho, "w", encoding="utf-8") as f:
                    f.write(texto)
                QMessageBox.information(self, "Exportado", "Relatório de Hardware exportado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao exportar relatório: {e}")


# --- Janela Principal da Aplicação ---
class OtimizadorApp(QWidget):
    def __init__(self):
        super().__init__()
        self.sensor = native_core.HardwareMonitor()
        
        # Estados das checkboxes de manutenção
        self.vars_estado = {
            "otimizarRAM": False,
            "limparTemp": True,
            "limpezaDisco": True,
            "servicosExtras": True,
            "redefinirRede": False,
            "desfragmentacao": True,
            "sfc": True,
            "restauraIntegridadeWindows": False,
            "chkdsk": False,
            "diagnostico": False,
            "verificaAtualizacaoPendente": False,
            "reiniciar": False
        }
        
        # Sub-serviços desativáveis (Tweaks)
        self.sub_servicos_estado = {s['id']: s.get('recomendado', False) for s in SERVICOS_TWEAKS_DISPONIVEIS}
        
        self.worker_thread = None
        self.checkbox_widgets = {}

        self.initUI()

        # Timers Nativos do Qt para atualização de relógio e métricas
        self.timer_relogio = QTimer(self)
        self.timer_relogio.timeout.connect(self._atualizar_relogio)
        self.timer_relogio.start(1000)

        self.timer_termico = QTimer(self)
        self.timer_termico.timeout.connect(self._atualizar_monitor_hardware)
        self.timer_termico.start(2000)
        self._atualizar_monitor_hardware()

    def initUI(self):
        self.setWindowTitle(f"Otimizador do Windows ({VERSAO})")
        self.resize(960, 920)
        self.setMinimumSize(880, 820)
        self.setWindowIcon(get_app_icon())

        # QSS Global Premium
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COR_BG_DARK};
                color: {COR_TEXTO};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QCheckBox {{
                spacing: 10px;
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 20px; height: 20px;
                border: 2px solid {COR_BORDA};
                border-radius: 5px; background-color: {COR_CARD};
            }}
            QCheckBox::indicator:hover {{
                border-color: {COR_AZUL_ACCENT};
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {COR_AZUL_ACCENT};
                background-color: {COR_AZUL_ACCENT};
            }}
            QScrollBar:vertical {{
                background: {COR_BG_DARK};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #374151;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #4B5563;
            }}
        """)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(24, 20, 24, 20)
        layout_principal.setSpacing(16)

        # 1. Top Header Bar (Título, Badge Admin, Uptime e Relógio)
        layout_header = QHBoxLayout()
        
        layout_titulo = QVBoxLayout()
        lbl_app_title = QLabel("🚀 Otimizador do Windows")
        lbl_app_title.setStyleSheet("font-size: 24px; font-weight: 800; color: white;")
        
        lbl_app_sub = QLabel(f"Versão {VERSAO} • Manutenção Avançada e Performance")
        lbl_app_sub.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 12px;")
        layout_titulo.addWidget(lbl_app_title)
        layout_titulo.addWidget(lbl_app_sub)

        layout_header.addLayout(layout_titulo)
        layout_header.addStretch()

        # Admin Badge
        is_adm = native_core.is_admin()
        badge_adm = QLabel("🛡️ ADMINISTRADOR" if is_adm else "⚠️ MODO PADRÃO")
        adm_color = COR_VERDE if is_adm else COR_AMARELO
        badge_adm.setStyleSheet(f"""
            color: {adm_color}; background-color: #1A202C; font-size: 11px; font-weight: bold;
            border: 1px solid {adm_color}; border-radius: 6px; padding: 4px 10px;
        """)
        layout_header.addWidget(badge_adm)

        # Relógio Digital
        self.lbl_relogio = QLabel(time.strftime("%H:%M:%S"))
        self.lbl_relogio.setStyleSheet("font-size: 26px; font-weight: bold; color: white; font-family: 'Consolas';")
        layout_header.addWidget(self.lbl_relogio)

        layout_principal.addLayout(layout_header)

        # 2. Painel de Monitoramento de Hardware em Tempo Real
        frame_hw = QFrame()
        frame_hw.setStyleSheet(f"background-color: {COR_CARD}; border: 1px solid {COR_BORDA}; border-radius: 10px;")
        layout_hw = QHBoxLayout(frame_hw)
        layout_hw.setContentsMargins(20, 14, 20, 14)
        layout_hw.setSpacing(20)

        # Card Térmico CPU
        card_lcd = QFrame()
        card_lcd.setStyleSheet("background-color: #11131A; border: 1px solid #252A3A; border-radius: 8px; min-width: 140px;")
        layout_lcd = QVBoxLayout(card_lcd)
        layout_lcd.setContentsMargins(12, 8, 12, 8)
        layout_lcd.setSpacing(2)
        
        lbl_cpu_tag = QLabel("TEMPERATURA CPU")
        lbl_cpu_tag.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        lbl_cpu_tag.setAlignment(Qt.AlignCenter)
        
        self.lbl_cpu_temp = QLabel("--°C")
        self.lbl_cpu_temp.setStyleSheet(f"color: {COR_VERDE}; font-size: 26px; font-weight: bold; font-family: 'Consolas'; border: none; background: transparent;")
        self.lbl_cpu_temp.setAlignment(Qt.AlignCenter)
        
        layout_lcd.addWidget(lbl_cpu_tag)
        layout_lcd.addWidget(self.lbl_cpu_temp)
        layout_hw.addWidget(card_lcd)

        # Resumo Térmico e Min/Max
        layout_term_info = QVBoxLayout()
        layout_term_info.setSpacing(2)
        self.lbl_min_max = QLabel("MÍN: --°C | MÁX: --°C")
        self.lbl_min_max.setStyleSheet("color: white; font-size: 12px; font-weight: bold; border: none;")
        
        self.lbl_alerta_termico = QLabel("✓ Sensores operando normalmente")
        self.lbl_alerta_termico.setStyleSheet(f"color: {COR_VERDE}; font-size: 11px; border: none;")
        
        layout_term_info.addWidget(self.lbl_min_max)
        layout_term_info.addWidget(self.lbl_alerta_termico)
        layout_hw.addLayout(layout_term_info)

        layout_hw.addStretch()

        # Medidor de Memória RAM em Tempo Real
        layout_ram_metric = QVBoxLayout()
        layout_ram_metric.setSpacing(4)
        self.lbl_ram_title = QLabel("MEMÓRIA RAM EM USO: --")
        self.lbl_ram_title.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 11px; font-weight: bold; border: none;")
        
        self.pbar_ram = QProgressBar()
        self.pbar_ram.setValue(50)
        self.pbar_ram.setFixedWidth(180)
        self.pbar_ram.setFixedHeight(10)
        self.pbar_ram.setTextVisible(False)
        self.pbar_ram.setStyleSheet(f"""
            QProgressBar {{ background-color: #252A3A; border: none; border-radius: 5px; }}
            QProgressBar::chunk {{ background-color: {COR_AZUL_ACCENT}; border-radius: 5px; }}
        """)
        layout_ram_metric.addWidget(self.lbl_ram_title)
        layout_ram_metric.addWidget(self.pbar_ram)
        layout_hw.addLayout(layout_ram_metric)

        layout_principal.addWidget(frame_hw)

        # 3. Toolbar de Ações Rápidas (1-Click Boost)
        layout_quick_actions = QHBoxLayout()
        layout_quick_actions.setSpacing(10)

        btn_boost_ram = self._criar_botao_acao_rapida("⚡ Otimizar RAM", COR_VERDE, self._acao_rapida_otimizar_ram)
        btn_boost_dns = self._criar_botao_acao_rapida("🌐 Limpar DNS", COR_AZUL_ACCENT, self._acao_rapida_limpar_dns)
        btn_boost_power = self._criar_botao_acao_rapida("⚡ Desempenho Máximo", COR_ROXO, self._acao_rapida_plano_energia)
        btn_boost_diag = self._criar_botao_acao_rapida("🔍 Sugestão Inteligente", COR_AMARELO, self._abrir_sugestao_inteligente)

        layout_quick_actions.addWidget(btn_boost_ram)
        layout_quick_actions.addWidget(btn_boost_dns)
        layout_quick_actions.addWidget(btn_boost_power)
        layout_quick_actions.addWidget(btn_boost_diag)
        layout_principal.addLayout(layout_quick_actions)

        # 4. Grid de Opções de Manutenção do Sistema
        lbl_sec_opcoes = QLabel("Selecione as Tarefas de Manutenção:")
        lbl_sec_opcoes.setStyleSheet("font-size: 14px; font-weight: bold; color: white;")
        layout_principal.addWidget(lbl_sec_opcoes)

        # Scroll Area para as opções em Grid
        scroll_opcoes = QScrollArea()
        scroll_opcoes.setWidgetResizable(True)
        scroll_opcoes.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll_opcoes.setMaximumHeight(310)

        container_grid = QWidget()
        container_grid.setStyleSheet("background: transparent;")
        grid_opcoes = QGridLayout(container_grid)
        grid_opcoes.setSpacing(10)
        grid_opcoes.setContentsMargins(0, 0, 6, 0)

        opcoes_catalogo = [
            ("Reparar Arquivos de Sistema (SFC)", "sfc", "Executa sfc /scannow para restaurar arquivos corrompidos.", "Recomendado", COR_VERDE, 0, 0),
            ("Limpeza Profunda de Disco", "limpezaDisco", "Limpa cache de updates, mini-dumps e logs de erro.", "Recomendado", COR_VERDE, 0, 1),
            ("Limpar Pastas Temporárias & Lixeira", "limparTemp", "Exclui %TEMP%, Temp do Windows e esvazia a lixeira.", "Recomendado", COR_VERDE, 1, 0),
            ("Otimizar Armazenamento (TRIM / Defrag)", "desfragmentacao", "TRIM para SSDs ou desfragmentação inteligente para HDDs.", "Recomendado", COR_VERDE, 1, 1),
            ("Redefinir Pilha de Rede & TCP/IP", "redefinirRede", "Redefine Winsock, rotas de rede e flush DNS.", "Recomendado", COR_VERDE, 2, 0),
            ("Desativar Serviços Extras & Bloatware", "servicosExtras", "Ajusta telemetria, Copilot, widgets e segundo plano.", "Personalizável", COR_AZUL_ACCENT, 2, 1),
            ("Restaurar Imagem do Windows (DISM)", "restauraIntegridadeWindows", "Repara repositório de componentes e saúde da imagem.", "Avançado", COR_ROXO, 3, 0),
            ("Verificar Integridade de Disco (CHKDSK)", "chkdsk", "Examina o sistema de arquivos NTFS em busca de falhas.", "Seguro", COR_AZUL_ACCENT, 3, 1),
            ("Diagnóstico de Memória RAM", "diagnostico", "Configura ferramenta de diagnóstico de integridade de RAM.", "Avançado", COR_ROXO, 4, 0),
            ("Verificar Atualizações Pendentes", "verificaAtualizacaoPendente", "Consulta se há updates ou reinicialização requerida.", "Seguro", COR_AZUL_ACCENT, 4, 1),
            ("Reiniciar Computador ao Concluir", "reiniciar", "Reinicia o sistema de forma segura após as correções.", "Opcional", COR_AMARELO, 5, 0)
        ]

        for titulo, chave, desc, badge_txt, badge_cor, r, c in opcoes_catalogo:
            card_op = QFrame()
            card_op.setStyleSheet(f"""
                QFrame {{
                    background-color: {COR_CARD};
                    border: 1px solid {COR_BORDA};
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    border: 1px solid #3E465E;
                    background-color: {COR_CARD_HOVER};
                }}
            """)
            layout_op = QHBoxLayout(card_op)
            layout_op.setContentsMargins(14, 10, 14, 10)
            layout_op.setSpacing(8)

            layout_textos = QVBoxLayout()
            layout_textos.setSpacing(2)

            layout_top_item = QHBoxLayout()
            lbl_item_titulo = QLabel(titulo)
            lbl_item_titulo.setStyleSheet("font-weight: bold; font-size: 12px; color: white; border: none; background: transparent;")
            
            badge = QLabel(badge_txt)
            badge.setStyleSheet(f"""
                color: {badge_cor}; background-color: #11131A; font-size: 9px; font-weight: bold;
                border: 1px solid {badge_cor}; border-radius: 4px; padding: 1px 6px;
            """)

            layout_top_item.addWidget(lbl_item_titulo)
            layout_top_item.addStretch()
            layout_top_item.addWidget(badge)
            layout_textos.addLayout(layout_top_item)

            lbl_desc = QLabel(desc)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 10px; border: none; background: transparent;")
            layout_textos.addWidget(lbl_desc)

            chk = QCheckBox()
            chk.setChecked(self.vars_estado.get(chave, False))
            chk.setStyleSheet("border: none; background: transparent;")
            chk.stateChanged.connect(lambda state, k=chave: self._gerenciar_clique_checkbox(k, state))
            self.checkbox_widgets[chave] = chk

            layout_op.addLayout(layout_textos)
            layout_op.addWidget(chk)
            grid_opcoes.addWidget(card_op, r, c)

        scroll_opcoes.setWidget(container_grid)
        layout_principal.addWidget(scroll_opcoes)

        # 5. Barra de Progresso e Console de Logs Colorido
        frame_status_box = QFrame()
        frame_status_box.setStyleSheet(f"background-color: {COR_CONSOLE_BG}; border: 1px solid #232736; border-radius: 8px;")
        layout_status_box = QVBoxLayout(frame_status_box)
        layout_status_box.setContentsMargins(14, 12, 14, 12)
        layout_status_box.setSpacing(8)

        layout_status_header = QHBoxLayout()
        self.lbl_status_dinamico = QLabel("Aguardando início dos comandos...")
        self.lbl_status_dinamico.setStyleSheet(f"color: {COR_AZUL_ACCENT}; font-size: 12px; font-weight: bold;")
        
        self.lbl_progresso_num = QLabel("0%")
        self.lbl_progresso_num.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")

        layout_status_header.addWidget(self.lbl_status_dinamico)
        layout_status_header.addStretch()
        layout_status_header.addWidget(self.lbl_progresso_num)
        layout_status_box.addLayout(layout_status_header)

        self.pbar_tarefas = QProgressBar()
        self.pbar_tarefas.setValue(0)
        self.pbar_tarefas.setFixedHeight(8)
        self.pbar_tarefas.setTextVisible(False)
        self.pbar_tarefas.setStyleSheet(f"""
            QProgressBar {{ background-color: #1F2433; border: none; border-radius: 4px; }}
            QProgressBar::chunk {{ background-color: {COR_VERDE}; border-radius: 4px; }}
        """)
        layout_status_box.addWidget(self.pbar_tarefas)

        # Console de logs em tempo real
        self.console_logs = QTextEdit()
        self.console_logs.setReadOnly(True)
        self.console_logs.setFixedHeight(90)
        self.console_logs.setStyleSheet(f"""
            QTextEdit {{
                background-color: #08090D;
                color: #A0AEC0;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                border: 1px solid #1A1D27;
                border-radius: 4px;
                padding: 6px;
            }}
        """)
        layout_status_box.addWidget(self.console_logs)
        layout_principal.addWidget(frame_status_box)

        # 6. Painel de Botões de Ação Inferiores
        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(12)

        self.btn_iniciar = QPushButton("INICIAR OTIMIZAÇÃO COMPLETA")
        self.btn_iniciar.setStyleSheet(f"""
            QPushButton {{
                background-color: {COR_VERDE}; color: white; font-weight: bold; font-size: 13px;
                border: none; border-radius: 8px; padding: 14px 24px;
            }}
            QPushButton:hover {{ background-color: {COR_VERDE_HOVER}; }}
            QPushButton:disabled {{ background-color: #374151; color: #9CA3AF; }}
        """)
        self.btn_iniciar.clicked.connect(self.iniciar_execucao)

        btn_sobre = QPushButton("SOBRE O PC")
        btn_sobre.setStyleSheet(f"""
            QPushButton {{
                background-color: #2D3748; color: white; font-weight: bold; font-size: 13px;
                border: 1px solid #4A5568; border-radius: 8px; padding: 14px 20px;
            }}
            QPushButton:hover {{ background-color: #4A5568; }}
        """)
        btn_sobre.clicked.connect(self._abrir_sobre_pc)

        btn_tweaks = QPushButton("GERENCIAR SERVIÇOS")
        btn_tweaks.setStyleSheet(f"""
            QPushButton {{
                background-color: #1E293B; color: {COR_AZUL_ACCENT}; font-weight: bold; font-size: 13px;
                border: 1px solid #2563EB; border-radius: 8px; padding: 14px 20px;
            }}
            QPushButton:hover {{ background-color: #2563EB; color: white; }}
        """)
        btn_tweaks.clicked.connect(self._abrir_janela_servicos)

        btn_sair = QPushButton("SAIR")
        btn_sair.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent; color: {COR_VERMELHO}; font-weight: bold; font-size: 13px;
                border: 1px solid {COR_VERMELHO}; border-radius: 8px; padding: 14px 20px;
            }}
            QPushButton:hover {{ background-color: {COR_VERMELHO}; color: white; }}
        """)
        btn_sair.clicked.connect(self.close)

        layout_botoes.addWidget(self.btn_iniciar, 2)
        layout_botoes.addWidget(btn_sobre, 1)
        layout_botoes.addWidget(btn_tweaks, 1)
        layout_botoes.addWidget(btn_sair)
        layout_principal.addLayout(layout_botoes)

        # 7. Rodapé
        layout_rodape = QHBoxLayout()
        lbl_dev = QLabel("Desenvolvido por Daniel Boechat • Engenharia de Software")
        lbl_dev.setStyleSheet(f"color: {COR_TEXTO_MUTED}; font-size: 11px;")

        lbl_link = QLabel("🚀 Apoie este projeto com uma contribuição")
        lbl_link.setCursor(Qt.PointingHandCursor)
        lbl_link.setStyleSheet(f"color: {COR_AZUL_ACCENT}; font-size: 11px; font-weight: bold; text-decoration: underline;")
        lbl_link.mousePressEvent = lambda e: webbrowser.open_new("https://aplicacoessimples.blogspot.com/2024/12/ajude-meu-trabalho.html")

        layout_rodape.addWidget(lbl_dev)
        layout_rodape.addStretch()
        layout_rodape.addWidget(lbl_link)
        layout_principal.addLayout(layout_rodape)

    # --- Ações de Inicialização e Métodos Auxiliares ---

    def _criar_botao_acao_rapida(self, texto: str, cor_hex: str, funcao) -> QPushButton:
        btn = QPushButton(texto)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COR_CARD}; color: {COR_TEXTO}; font-weight: bold; font-size: 12px;
                border: 1px solid {COR_BORDA}; border-radius: 6px; padding: 10px 14px;
            }}
            QPushButton:hover {{
                border-color: {cor_hex}; background-color: {COR_CARD_HOVER}; color: white;
            }}
        """)
        btn.clicked.connect(funcao)
        return btn

    def _gerenciar_clique_checkbox(self, chave: str, state):
        bool_state = (state == Qt.Checked)
        self.vars_estado[chave] = bool_state
        if chave == "servicosExtras" and bool_state:
            self._abrir_janela_servicos()

    def _atualizar_relogio(self):
        self.lbl_relogio.setText(time.strftime("%H:%M:%S"))

    def _atualizar_monitor_hardware(self):
        # 1. Leitura Térmica
        temp = self.sensor.ler_temperatura_cpu()
        if temp > 0:
            texto_status, cor_status, nivel = self.sensor.obter_status_termico(temp)
            self.lbl_cpu_temp.setText(f"{temp:.1f}°C")
            self.lbl_cpu_temp.setStyleSheet(f"color: {cor_status}; font-size: 26px; font-weight: bold; font-family: 'Consolas'; border: none; background: transparent;")
            self.lbl_min_max.setText(f"MÍN: {self.sensor.temp_min:.1f}°C | MÁX: {self.sensor.temp_max:.1f}°C")
            self.lbl_alerta_termico.setText(texto_status)
            self.lbl_alerta_termico.setStyleSheet(f"color: {cor_status}; font-size: 11px; border: none;")

        # 2. Leitura de Memória RAM
        try:
            import psutil
            vm = psutil.virtual_memory()
            used_gb = vm.used / (1024**3)
            total_gb = vm.total / (1024**3)
            pct = int(vm.percent)
            self.lbl_ram_title.setText(f"MEMÓRIA RAM: {used_gb:.1f} GB / {total_gb:.1f} GB ({pct}%)")
            self.pbar_ram.setValue(pct)
            ram_color = COR_VERDE if pct < 70 else (COR_AMARELO if pct < 85 else COR_VERMELHO)
            self.pbar_ram.setStyleSheet(f"""
                QProgressBar {{ background-color: #252A3A; border: none; border-radius: 5px; }}
                QProgressBar::chunk {{ background-color: {ram_color}; border-radius: 5px; }}
            """)
        except Exception:
            pass

    # --- Ações Rápidas (Toolbar) ---

    def _acao_rapida_otimizar_ram(self):
        self.lbl_status_dinamico.setText("Otimizando memória RAM nativamente...")
        res = native_core.purge_ram_working_sets()
        msg = f"✓ Otimização Concluída: {res['freed_mb']} MB liberados em {res['processes_optimized']} processos.\nUso de RAM reduziu para {res['mem_after_pct']}%."
        self._adicionar_log("SUCCESS", msg)
        self._atualizar_monitor_hardware()
        QMessageBox.information(self, "RAM Otimizada", msg)

    def _acao_rapida_limpar_dns(self):
        sucesso = native_core.flush_dns_cache()
        if sucesso:
            msg = "✓ Cache do resolvedor DNS limpo com sucesso!"
            self._adicionar_log("SUCCESS", msg)
            QMessageBox.information(self, "DNS Limpo", msg)
        else:
            msg = "Aviso ao limpar cache DNS."
            self._adicionar_log("WARNING", msg)

    def _acao_rapida_plano_energia(self):
        ok = native_core.activate_ultimate_performance()
        if ok:
            msg = "⚡ Plano de Desempenho Máximo ativado no Windows!"
            self._adicionar_log("SUCCESS", msg)
            QMessageBox.information(self, "Plano de Energia", msg)
        else:
            QMessageBox.warning(self, "Aviso", "Não foi possível alterar o plano de energia.")

    def _abrir_sugestao_inteligente(self):
        diag = smart_advisor.run_smart_diagnostic()
        janela = JanelaSugestaoInteligente(diag, callback_aplicar=self._aplicar_chaves_recomendadas, parent=self)
        janela.exec_()

    def _aplicar_chaves_recomendadas(self, keys: list):
        for k, chk in self.checkbox_widgets.items():
            if k in keys:
                chk.setChecked(True)
                self.vars_estado[k] = True
            else:
                if k != "reiniciar":
                    chk.setChecked(False)
                    self.vars_estado[k] = False
        self._adicionar_log("INFO", "Configuração de manutenção ajustada automaticamente com base no diagnóstico do hardware.")

    def _abrir_sobre_pc(self):
        janela = JanelaSobrePC(self)
        janela.exec_()

    def _abrir_janela_servicos(self):
        janela = JanelaServicosExtras(self.sub_servicos_estado, self)
        janela.exec_()

    # --- Execução Principal de Manutenção ---

    def iniciar_execucao(self):
        if not any(self.vars_estado.values()):
            QMessageBox.warning(self, "Aviso", "Selecione pelo menos uma tarefa de manutenção para continuar.")
            return

        self.btn_iniciar.setEnabled(False)
        self.pbar_tarefas.setValue(0)
        self.lbl_progresso_num.setText("0%")
        self.console_logs.clear()

        self.worker_thread = OptimizerWorkerThread(self.vars_estado, self.sub_servicos_estado)
        self.worker_thread.status_changed.connect(self._ao_mudar_status)
        self.worker_thread.progress_percent.connect(self._ao_atualizar_progresso)
        self.worker_thread.log_added.connect(self._adicionar_log)
        self.worker_thread.task_finished.connect(self._ao_finalizar_tarefas)
        self.worker_thread.start()

    def _ao_mudar_status(self, texto: str):
        self.lbl_status_dinamico.setText(texto)

    def _ao_atualizar_progresso(self, pct: int):
        self.pbar_tarefas.setValue(pct)
        self.lbl_progresso_num.setText(f"{pct}%")

    def _adicionar_log(self, nivel: str, mensagem: str):
        cor = {
            "SUCCESS": "#10B981",
            "STEP": "#3B82F6",
            "WARNING": "#F59E0B",
            "ERROR": "#EF4444",
            "INFO": "#D1D5DB"
        }.get(nivel, "#D1D5DB")
        
        hora = time.strftime("%H:%M:%S")
        html_msg = f"<span style='color: #6B7280;'>[{hora}]</span> <span style='color: {cor};'>{mensagem}</span>"
        self.console_logs.append(html_msg)
        self.console_logs.moveCursor(QTextCursor.End)

    def _ao_finalizar_tarefas(self, relatorio: list):
        self.btn_iniciar.setEnabled(True)
        self.lbl_status_dinamico.setText("Otimização concluída com sucesso!")
        self._atualizar_monitor_hardware()

        msg = "Otimização e manutenção do Windows concluídas com êxito!\n\nRelatório salvo em 'log_otimizacao.txt'."
        QMessageBox.information(self, "Sucesso", msg)

        if self.vars_estado.get("reiniciar", False):
            os.system('shutdown /r /t 20 /c "O computador sera reiniciado em 20 segundos para concluir a otimizacao."')


# --- Ponto de Entrada da Aplicação com Tratamento de Administrador ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("Otimizador do Windows")
    app.setWindowIcon(get_app_icon())

    if not native_core.is_admin():
        # Exibe janela amigável oferecendo reinicialização como Administrador
        dialog_admin = QMessageBox()
        dialog_admin.setIcon(QMessageBox.Warning)
        dialog_admin.setWindowTitle("Permissão de Administrador Necessária")
        dialog_admin.setText(
            "Para executar tarefas de manutenção avançada (como SFC, DISM, TRIM de SSD, "
            "redefinição de rede e leitura de sensores), o aplicativo precisa de privilégios de Administrador."
        )
        btn_exec_admin = dialog_admin.addButton("🛡️ Executar como Administrador", QMessageBox.AcceptRole)
        btn_continuar = dialog_admin.addButton("Continuar sem Admin", QMessageBox.RejectRole)
        dialog_admin.setDefaultButton(btn_exec_admin)
        
        dialog_admin.exec_()

        if dialog_admin.clickedButton() == btn_exec_admin:
            native_core.restart_as_admin()
            sys.exit(0)

    janela_principal = OtimizadorApp()
    janela_principal.show()
    sys.exit(app.exec_())