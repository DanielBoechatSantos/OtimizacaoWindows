from PyQt5.QtGui import QFont, QIcon, QColor
import tkinter as tk
from tkinter import messagebox, ttk
import time
import threading
import subprocess
import sys
import os
import shutil
import psutil
import platform
import winreg
try:
    import clr # pythonnet para a DLL
except:
    pass

# --- Configurações Visuais Globais ---
VERSAO = "3.1 - Thermal Edition"
COR_FUNDO = "#2b2b2b"
COR_TEXTO = "#ffffff"
COR_DESTAQUE = "#007acc"
COR_VERDE = "#4caf50"
COR_VERMELHO = "#f44336"
COR_AMARELO = "#ffeb3b"
COR_CARD = "#3c3c3c"
COR_RODAPE = "#888888"

# --- Configuração de Serviços ---
SERVICOS_DESATIVAVEIS = [
    {"id": "copilot", "nome": "Microsoft Copilot", "tipo": "reg", "path": r"Software\Policies\Microsoft\Windows\WindowsCopilot", "valor": "TurnOffWindowsCopilot", "desc": "Desativa o assistente de IA da barra de tarefas.", "ganho": "Baixo - Libera CPU e espaço na Taskbar."},
    {"id": "telemetria", "nome": "Telemetria (DiagTrack)", "tipo": "svc", "svc_name": "DiagTrack", "desc": "Envia dados de uso para a Microsoft.", "ganho": "Médio - Reduz escrita em disco e rede."},
    {"id": "sysmain", "nome": "SysMain (Superfetch)", "tipo": "svc", "svc_name": "SysMain", "desc": "Pré-carrega apps. Desative apenas se tiver SSD.", "ganho": "Médio - Melhora resposta de E/S em SSDs."},
    {"id": "spooler", "nome": "Impressão (Spooler)", "tipo": "svc", "svc_name": "Spooler", "desc": "Gerencia impressoras. Desative se não usa.", "ganho": "Baixo - Economiza ~20MB de RAM."},
    {"id": "widgets", "nome": "Widgets do Windows", "tipo": "reg", "path": r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced", "valor": "TaskbarDa", "desc": "Painel de notícias e clima na barra de tarefas.", "ganho": "Baixo - Menos processos de GPU ativos."}
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
            
            # Tenta carregar o clr do pythonnet
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

class ToolTip:
    def __init__(self, widget, text):
        self.widget, self.text, self.tip_window = widget, text, None
        widget.bind("<Enter>", self.show_tip); widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text: return
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tk.Frame(tw, bg="#1e1e1e", bd=1, relief=tk.SOLID), text=self.text, justify=tk.LEFT, 
                 background="#1e1e1e", fg="#dcdcdc", font=("Segoe UI", 9), padx=5, pady=3).pack()

    def hide_tip(self, event=None):
        if self.tip_window: self.tip_window.destroy(); self.tip_window = None

class ModernToggle(tk.Canvas):
    def __init__(self, parent, variable, command=None, width=50, height=24):
        super().__init__(parent, width=width, height=height, bg=COR_CARD, highlightthickness=0)
        self.variable, self.command = variable, command
        self.width, self.height = width, height
        self.bind("<Button-1>", self._on_click)
        self._draw()
        self.variable.trace_add("write", lambda *args: self._draw())

    def _on_click(self, event):
        if self.command:
            if self.command() is False: return
        self.variable.set(not self.variable.get())

    def _draw(self):
        self.delete("all")
        state = self.variable.get()
        bg_color = COR_VERDE if state else COR_VERMELHO
        radius = self.height / 2
        self.create_arc(0, 0, self.height, self.height, start=90, extent=180, fill=bg_color, outline=bg_color)
        self.create_arc(self.width - self.height, 0, self.width, self.height, start=-90, extent=180, fill=bg_color, outline=bg_color)
        self.create_rectangle(radius, 0, self.width - radius, self.height, fill=bg_color, outline=bg_color)
        circle_r = (self.height - 6) / 2
        cx = self.width - radius if state else radius
        self.create_oval(cx - circle_r, (self.height/2) - circle_r, cx + circle_r, (self.height/2) + circle_r, fill="#fff", outline="")

class JanelaServicos:
    def __init__(self, parent, selection_dict):
        self.win = tk.Toplevel(parent)
        self.win.title("Gerenciar Serviços Extras")
        self.win.geometry("500x600")
        self.win.configure(bg=COR_FUNDO)
        self.win.transient(parent); self.win.grab_set()
        self.selection_dict = selection_dict

        tk.Label(self.win, text="Otimização de Serviços", font=("Segoe UI", 14, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack(pady=15)
        container = tk.Frame(self.win, bg=COR_FUNDO); container.pack(fill=tk.BOTH, expand=True, padx=20)

        for item in SERVICOS_DESATIVAVEIS:
            card = tk.Frame(container, bg=COR_CARD, padx=10, pady=8, bd=1, relief=tk.RIDGE); card.pack(fill=tk.X, pady=5)
            tk.Checkbutton(card, text=item['nome'], variable=self.selection_dict[item['id']], bg=COR_CARD, fg=COR_TEXTO, 
                           selectcolor=COR_FUNDO, font=("Segoe UI", 10, "bold"), activebackground=COR_CARD).pack(anchor="w")
            tk.Label(card, text=item['desc'], bg=COR_CARD, fg="#bbb", font=("Segoe UI", 8), wraplength=420, justify=tk.LEFT).pack(anchor="w", padx=20)
            tk.Label(card, text=f"Ganho: {item['ganho']}", bg=COR_CARD, fg=COR_DESTAQUE, font=("Segoe UI", 8, "italic")).pack(anchor="w", padx=20)

        tk.Button(self.win, text="SALVAR SELEÇÃO", bg=COR_VERDE, fg="white", font=("Segoe UI", 10, "bold"), 
                  relief=tk.FLAT, pady=10, command=self.win.destroy).pack(fill=tk.X, padx=20, pady=20)

class OtimizadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Otimizador do Windows ({VERSAO})")
        self.root.geometry("820x920")
        self.root.configure(bg=COR_FUNDO); self.root.resizable(False, False)

        self.sensor = SensorHardware()
        self.vars = {k: tk.BooleanVar() for k in ["sfc", "limpezaDisco", "chkdsk", "diagnostico", "desfragmentacao", 
                                                "redefinirRede", "restauraIntegridadeWindows", "verificaAtualizacaoPendente", 
                                                "limparTemp", "reiniciar", "servicosExtras"]}
        self.sub_servicos_vars = {s['id']: tk.BooleanVar() for s in SERVICOS_DESATIVAVEIS}

        self.status_text = tk.StringVar(value="Analisando sistema...")
        self.relogio_text = tk.StringVar()
        self.mapa_discos = {}

        self._mapear_discos()
        self._setup_ui()
        self._iniciar_monitor_termico()
        self._atualizar_relogio()

    def _setup_ui(self):
        header = tk.Frame(self.root, bg=COR_FUNDO); header.pack(pady=(15, 5), fill=tk.X)
        tk.Label(header, textvariable=self.relogio_text, font=("Segoe UI", 28, "bold"), bg=COR_FUNDO, fg=COR_TEXTO).pack()

        thermal = tk.Frame(self.root, bg=COR_FUNDO); thermal.pack(pady=10, fill=tk.X, padx=25)
        self.lcd_card = tk.Frame(thermal, bg="#1a1a1a", bd=2, relief=tk.RIDGE, padx=15, pady=10); self.lcd_card.pack(side=tk.LEFT)
        tk.Label(self.lcd_card, text="CPU TEMP", font=("Segoe UI", 8, "bold"), bg="#1a1a1a", fg="#888").pack()
        self.lbl_cpu_temp = tk.Label(self.lcd_card, text="--°C", font=("Consolas", 28, "bold"), bg="#1a1a1a", fg=COR_VERDE); self.lbl_cpu_temp.pack()
        
        self.lbl_min_max = tk.Label(thermal, text="MIN: --°C\nMAX: --°C", font=("Segoe UI", 10), bg=COR_FUNDO, fg="#aaa", justify=tk.LEFT); self.lbl_min_max.pack(side=tk.LEFT, padx=15)
        self.lbl_alerta_termico = tk.Label(thermal, text="✓ Sistema Operando em Temperatura Ideal", font=("Segoe UI", 9, "italic"), bg=COR_FUNDO, fg=COR_VERDE, wraplength=350, justify=tk.LEFT); self.lbl_alerta_termico.pack(side=tk.RIGHT, padx=10)

        container = tk.Frame(self.root, bg=COR_FUNDO); container.pack(padx=25, pady=10, fill=tk.BOTH, expand=True)
        opcoes = [
            ("Reparar Sistema (SFC)", "sfc", "Verifica e repara arquivos corrompidos."),
            ("Limpeza de Disco", "limpezaDisco", "Remove arquivos desnecessários."),
            ("Verificar Disco (CHKDSK)", "chkdsk", "Verifica erros no disco (requer restart)."),
            ("Diagnóstico Memória", "diagnostico", "Agenda teste de RAM."),
            ("Desfragmentar (HDD)", "desfragmentacao", "Apenas para HDDs."),
            ("Redefinir Rede", "redefinirRede", "Reseta configurações de conexão."),
            ("Restaurar Imagem (DISM)", "restauraIntegridadeWindows", "Repara imagem do Windows."),
            ("Atualizações (Win Update)", "verificaAtualizacaoPendente", "Força busca por updates."),
            ("Limpar Pasta Temp", "limparTemp", "Limpa cache temporário."),
            ("Desativar Serviços Extras", "servicosExtras", "Abre lista de serviços específicos."),
            ("Reiniciar ao Final", "reiniciar", "Reinicia automaticamente.")
        ]

        for i, (titulo, chave, dica) in enumerate(opcoes):
            r, c = i // 2, i % 2
            card = tk.Frame(container, bg=COR_CARD, padx=15, pady=12); card.grid(row=r, column=c, sticky="ew", padx=8, pady=8)
            container.grid_columnconfigure(c, weight=1)
            tk.Label(card, text=titulo, bg=COR_CARD, fg=COR_TEXTO, font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, anchor="w", fill=tk.X, expand=True)
            
            cmd = self._abrir_popup_servicos if chave == "servicosExtras" else (self._validar_click_desfragmentar if chave == "desfragmentacao" else None)
            ModernToggle(card, self.vars[chave], command=cmd).pack(side=tk.RIGHT)
            ToolTip(card, dica)

        status_frame = tk.Frame(self.root, bg="#1e1e1e", padx=15, pady=15); status_frame.pack(fill=tk.X, padx=25, pady=10)
        tk.Label(status_frame, text="Status Atual:", font=("Segoe UI", 9, "bold"), bg="#1e1e1e", fg="#aaaaaa").pack(anchor="w")
        tk.Label(status_frame, textvariable=self.status_text, font=("Segoe UI", 10), bg="#1e1e1e", fg=COR_DESTAQUE, wraplength=700, justify=tk.LEFT).pack(anchor="w", fill=tk.X)

        btn_frame = tk.Frame(self.root, bg=COR_FUNDO); btn_frame.pack(pady=15)
        self._criar_botao(btn_frame, "INICIAR OTIMIZAÇÃO", self.iniciar_execucao, COR_VERDE).pack(side=tk.LEFT, padx=10)
        self._criar_botao(btn_frame, "SUGESTÃO AUTOMÁTICA", self.sugerir_acoes, COR_DESTAQUE).pack(side=tk.LEFT, padx=10)
        self._criar_botao(btn_frame, "SOBRE O PC", self.exibir_info_sistema, "#5b5b5b").pack(side=tk.LEFT, padx=10)
        self._criar_botao(btn_frame, "SAIR", self.root.quit, COR_VERMELHO).pack(side=tk.LEFT, padx=10)
        tk.Label(self.root, text="Desenvolvido por Daniel Boechat", font=("Segoe UI", 9, "italic"), bg=COR_FUNDO, fg=COR_RODAPE).pack(side=tk.BOTTOM, pady=10)

    def sugerir_acoes(self):
        self.status_text.set("Analisando sistema para sugestões...")
        count = 0
        if psutil.disk_usage('C:').percent > 75: self.vars["limpezaDisco"].set(True); count += 1
        if any(t == "HDD" for t in self.mapa_discos.values()): self.vars["desfragmentacao"].set(True); count += 1
        
        temp_p = os.path.join(os.getenv('LOCALAPPDATA'), 'Temp')
        if os.path.exists(temp_p) and len(os.listdir(temp_p)) > 30: self.vars["limparTemp"].set(True); count += 1
        
        self.vars["servicosExtras"].set(True)
        self.sub_servicos_vars["copilot"].set(True)
        self.sub_servicos_vars["telemetria"].set(True)
        self.status_text.set("Sugestões aplicadas com base no hardware.")
        messagebox.showinfo("Análise", f"Foram sugeridas {count} ações recomendadas.")

    def _abrir_popup_servicos(self):
        if not self.vars["servicosExtras"].get(): JanelaServicos(self.root, self.sub_servicos_vars)
        return True

    def _validar_click_desfragmentar(self):
        if self.vars["desfragmentacao"].get(): return True
        if not any(t == "HDD" for t in self.mapa_discos.values()):
            messagebox.showwarning("Bloqueado", "SSD detectado. Desfragmentação desnecessária."); return False
        return True

    def _iniciar_monitor_termico(self):
        def update():
            while self.root.winfo_exists():
                t = self.sensor.ler_cpu()
                self.root.after(0, lambda v=t: self._atualizar_ui_termica(v))
                time.sleep(2)
        threading.Thread(target=update, daemon=True).start()

    def _atualizar_ui_termica(self, temp):
        if temp <= 0: 
            self.lbl_cpu_temp.config(text="Erro", fg=COR_VERMELHO)
            self.lbl_alerta_termico.config(text="⚠ Falha nos sensores (Verifique DLL/SYS ou Admin)", fg=COR_AMARELO)
            return
        cor = COR_VERDE if temp < 65 else (COR_AMARELO if temp < 85 else COR_VERMELHO)
        self.lbl_cpu_temp.config(text=f"{temp:.1f}°C", fg=cor)
        self.lbl_min_max.config(text=f"MIN: {self.sensor.temp_min:.1f}°C\nMAX: {self.sensor.temp_max:.1f}°C")
        self.lbl_alerta_termico.config(text="✓ Sistema Saudável" if temp < 80 else "⚠ Superaquecimento!", fg=cor)

    def _mapear_discos(self):
        try:
            cmd = "Get-PhysicalDisk | Select-Object DeviceId, MediaType"
            res = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, creationflags=0x08000000)
            for l in res.stdout.strip().split('\n')[2:]:
                p = l.split()
                if len(p) >= 2: self.mapa_discos[p[0]] = p[1].upper()
        except: pass

    def _criar_botao(self, parent, texto, comando, cor):
        return tk.Button(parent, text=texto, command=comando, bg=cor, fg="white", font=("Segoe UI", 10, "bold"), relief=tk.FLAT, padx=20, pady=12, cursor="hand2")

    def _atualizar_relogio(self):
        self.relogio_text.set(time.strftime("%H:%M:%S"))
        self.root.after(1000, self._atualizar_relogio)

    def iniciar_execucao(self):
        if not any(v.get() for v in self.vars.values()): return
        threading.Thread(target=self._processar_fila, daemon=True).start()

    def _processar_fila(self):
        self.status_text.set("Iniciando limpeza...")
        if self.vars["limparTemp"].get(): self._limpar_temp()
        if self.vars["servicosExtras"].get(): self._aplicar_servicos_extras()
        if self.vars["sfc"].get(): 
            self.status_text.set("SFC Scannow em curso...")
            subprocess.run("sfc /scannow", shell=True, creationflags=0x08000000)
        self.status_text.set("Concluído!")
        messagebox.showinfo("Sucesso", "Otimização concluída!")
        if self.vars["reiniciar"].get(): os.system("shutdown /r /t 10")

    def _aplicar_servicos_extras(self):
        for item in SERVICOS_DESATIVAVEIS:
            if self.sub_servicos_vars[item['id']].get():
                if item['tipo'] == 'svc':
                    subprocess.run(f"sc config {item['svc_name']} start= disabled", shell=True, creationflags=0x08000000)
                    subprocess.run(f"sc stop {item['svc_name']}", shell=True, creationflags=0x08000000)
                elif item['tipo'] == 'reg':
                    try:
                        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, item['path'])
                        winreg.SetValueEx(k, item['valor'], 0, winreg.REG_DWORD, 1); winreg.CloseKey(k)
                    except: pass

    def _limpar_temp(self):
        p = os.path.join(os.getenv('LOCALAPPDATA'), 'Temp')
        for i in os.listdir(p):
            try:
                ip = os.path.join(p, i)
                if os.path.isfile(ip): os.unlink(ip)
                else: shutil.rmtree(ip)
            except: pass

    def exibir_info_sistema(self):
        win = tk.Toplevel(self.root); win.geometry("400x300"); win.configure(bg="#202020")
        tk.Label(win, text=f"CPU: {platform.processor()}", bg="#202020", fg="#fff", wraplength=350, pady=10).pack()
        tk.Label(win, text=f"RAM: {psutil.virtual_memory().total / (1024**3):.1f} GB", bg="#202020", fg="#fff").pack()
        tk.Label(win, text=f"OS: {platform.system()} {platform.release()}", bg="#202020", fg="#fff").pack()
        tk.Button(win, text="Fechar", command=win.destroy).pack(pady=20)

if __name__ == "__main__":
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Erro", "Execute como Administrador!")
    else:
        root = tk.Tk(); app = OtimizadorApp(root); root.mainloop()