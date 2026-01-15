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
import clr # pythonnet para a DLL

# --- Configurações Visuais Globais ---
VERSAO = "3.0 - Thermal Edition"
COR_FUNDO = "#2b2b2b"
COR_TEXTO = "#ffffff"
COR_DESTAQUE = "#007acc"
COR_VERDE = "#4caf50"
COR_VERMELHO = "#f44336"
COR_AMARELO = "#ffeb3b"
COR_CARD = "#3c3c3c"
COR_RODAPE = "#888888"

def resource_path(relative_path):
    """ Obtém o caminho absoluto para recursos, compatível com PyInstaller/auto-py-to-exe """
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Lógica de Hardware (DLL) ---
class SensorHardware:
    def __init__(self):
        self.temp_min = 999.0
        self.temp_max = 0.0
        self.ativo = False
        try:
            # Busca a DLL no caminho correto (seja pasta local ou temporária do EXE)
            dll_path = resource_path("OpenHardwareMonitorLib.dll")
            
            if not os.path.exists(dll_path):
                print(f"DLL não encontrada em: {dll_path}")
                return

            clr.AddReference(dll_path)
            from OpenHardwareMonitor.Hardware import Computer
            self.pc = Computer()
            self.pc.CPUEnabled = True
            self.pc.Open()
            self.ativo = True
        except Exception as e:
            print(f"Erro crítico ao carregar sensores: {e}")

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
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text: return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        frame = tk.Frame(tw, bg="#1e1e1e", bd=1, relief=tk.SOLID)
        frame.pack()
        label = tk.Label(frame, text=self.text, justify=tk.LEFT, background="#1e1e1e", fg="#dcdcdc",
                         font=("Segoe UI", 9), relief=tk.FLAT, padx=5, pady=3)
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class ModernToggle(tk.Canvas):
    def __init__(self, parent, variable, command=None, width=50, height=24):
        super().__init__(parent, width=width, height=height, bg=COR_CARD, highlightthickness=0)
        self.variable = variable
        self.command = command
        self.width = width
        self.height = height
        self.bind("<Button-1>", self._on_click)
        self._draw()
        self.variable.trace_add("write", lambda *args: self._draw())

    def _on_click(self, event):
        if self.command:
            resultado = self.command()
            if resultado is False: return
        self.variable.set(not self.variable.get())

    def _draw(self):
        self.delete("all")
        state = self.variable.get()
        bg_color = COR_VERDE if state else COR_VERMELHO
        circle_color = "#ffffff"
        radius = self.height / 2
        self.create_arc(0, 0, self.height, self.height, start=90, extent=180, fill=bg_color, outline=bg_color)
        self.create_arc(self.width - self.height, 0, self.width, self.height, start=-90, extent=180, fill=bg_color, outline=bg_color)
        self.create_rectangle(radius, 0, self.width - radius, self.height, fill=bg_color, outline=bg_color)
        padding = 3
        circle_r = (self.height - 2 * padding) / 2
        cx = self.width - radius if state else radius
        cy = self.height / 2
        self.create_oval(cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r, fill=circle_color, outline="")

class OtimizadorApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Otimizador do Windows ({VERSAO})")
        self.root.geometry("820x920")
        self.root.configure(bg=COR_FUNDO)
        self.root.resizable(False, False)

        self.sensor = SensorHardware()
        
        self.vars = {
            "sfc": tk.BooleanVar(),
            "limpezaDisco": tk.BooleanVar(),
            "chkdsk": tk.BooleanVar(),
            "diagnostico": tk.BooleanVar(),
            "desfragmentacao": tk.BooleanVar(),
            "redefinirRede": tk.BooleanVar(),
            "restauraIntegridadeWindows": tk.BooleanVar(),
            "verificaAtualizacaoPendente": tk.BooleanVar(),
            "limparTemp": tk.BooleanVar(),
            "reiniciar": tk.BooleanVar()
        }

        self.status_text = tk.StringVar()
        self.status_text.set("Analisando sistema...")
        self.relogio_text = tk.StringVar()
        self.mapa_discos = {} 

        self._mapear_discos()
        self._setup_ui()
        self._iniciar_verificacao_background()
        self._iniciar_monitor_termico()

    def _setup_ui(self):
        header_frame = tk.Frame(self.root, bg=COR_FUNDO)
        header_frame.pack(pady=(15, 5), fill=tk.X)

        lbl_relogio = tk.Label(header_frame, textvariable=self.relogio_text, font=("Segoe UI", 28, "bold"), bg=COR_FUNDO, fg=COR_TEXTO)
        lbl_relogio.pack()

        thermal_frame = tk.Frame(self.root, bg=COR_FUNDO)
        thermal_frame.pack(pady=10, fill=tk.X, padx=25)

        self.lcd_card = tk.Frame(thermal_frame, bg="#1a1a1a", bd=2, relief=tk.RIDGE, padx=15, pady=10)
        self.lcd_card.pack(side=tk.LEFT)

        tk.Label(self.lcd_card, text="CPU TEMP", font=("Segoe UI", 8, "bold"), bg="#1a1a1a", fg="#888").pack()
        self.lbl_cpu_temp = tk.Label(self.lcd_card, text="--°C", font=("Consolas", 28, "bold"), bg="#1a1a1a", fg=COR_VERDE)
        self.lbl_cpu_temp.pack()

        stats_frame = tk.Frame(thermal_frame, bg=COR_FUNDO, padx=15)
        stats_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.lbl_min_max = tk.Label(stats_frame, text="MIN: --°C\nMAX: --°C", font=("Segoe UI", 10), bg=COR_FUNDO, fg="#aaa", justify=tk.LEFT)
        self.lbl_min_max.pack(pady=5)

        self.lbl_alerta_termico = tk.Label(thermal_frame, text="✓ Sistema Operando em Temperatura Ideal", 
                                          font=("Segoe UI", 9, "italic"), bg=COR_FUNDO, fg=COR_VERDE, wraplength=350, justify=tk.LEFT)
        self.lbl_alerta_termico.pack(side=tk.RIGHT, padx=10)

        container = tk.Frame(self.root, bg=COR_FUNDO)
        container.pack(padx=25, pady=10, fill=tk.BOTH, expand=True)

        opcoes_info = [
            ("Reparar Sistema (SFC)", "sfc", "Verifica e repara arquivos corrompidos."),
            ("Limpeza de Disco", "limpezaDisco", "Remove arquivos desnecessários."),
            ("Verificar Disco (CHKDSK)", "chkdsk", "Verifica erros no disco (requer restart)."),
            ("Diagnóstico Memória", "diagnostico", "Agenda teste de RAM."),
            ("Desfragmentar (HDD)", "desfragmentacao", "Apenas para HDDs."),
            ("Redefinir Rede", "redefinirRede", "Reseta configurações de conexão."),
            ("Restaurar Imagem (DISM)", "restauraIntegridadeWindows", "Repara imagem do Windows."),
            ("Atualizações (Win Update)", "verificaAtualizacaoPendente", "Força busca por updates."),
            ("Limpar Pasta Temp", "limparTemp", "Limpa cache temporário."),
            ("Reiniciar ao Final", "reiniciar", "Reinicia automaticamente.")
        ]

        for i, (titulo, chave, dica) in enumerate(opcoes_info):
            row, col = i // 2, i % 2
            card = tk.Frame(container, bg=COR_CARD, bd=0, padx=15, pady=12)
            card.grid(row=row, column=col, sticky="ew", padx=8, pady=8)
            container.grid_columnconfigure(col, weight=1)

            lbl = tk.Label(card, text=titulo, bg=COR_CARD, fg=COR_TEXTO, font=("Segoe UI", 11, "bold"))
            lbl.pack(side=tk.LEFT, anchor="w", fill=tk.X, expand=True)
            
            cmd = self._validar_click_desfragmentar if chave == "desfragmentacao" else None
            toggle = ModernToggle(card, self.vars[chave], command=cmd)
            toggle.pack(side=tk.RIGHT)
            ToolTip(card, dica)

        status_frame = tk.Frame(self.root, bg="#1e1e1e", padx=15, pady=15)
        status_frame.pack(fill=tk.X, padx=25, pady=10)
        tk.Label(status_frame, text="Status Atual:", font=("Segoe UI", 9, "bold"), bg="#1e1e1e", fg="#aaaaaa").pack(anchor="w")
        tk.Label(status_frame, textvariable=self.status_text, font=("Segoe UI", 10), bg="#1e1e1e", fg=COR_DESTAQUE, wraplength=700, justify=tk.LEFT).pack(anchor="w", fill=tk.X)

        btn_frame = tk.Frame(self.root, bg=COR_FUNDO)
        btn_frame.pack(pady=15)
        self._criar_botao(btn_frame, "INICIAR OTIMIZAÇÃO", self.iniciar_execucao, COR_VERDE).pack(side=tk.LEFT, padx=10)
        self._criar_botao(btn_frame, "SUGESTÃO AUTOMÁTICA", self.sugerir_acoes, COR_DESTAQUE).pack(side=tk.LEFT, padx=10)
        self._criar_botao(btn_frame, "SOBRE O PC", self.exibir_info_sistema, "#5b5b5b").pack(side=tk.LEFT, padx=10)
        self._criar_botao(btn_frame, "SAIR", self.root.quit, COR_VERMELHO).pack(side=tk.LEFT, padx=10)

        tk.Label(self.root, text="Desenvolvido por Daniel Boechat", font=("Segoe UI", 9, "italic"), bg=COR_FUNDO, fg=COR_RODAPE).pack(side=tk.BOTTOM, pady=10)
        self._atualizar_relogio()

    def _iniciar_monitor_termico(self):
        def update():
            while True:
                if not self.root.winfo_exists(): break
                temp = self.sensor.ler_cpu()
                self.root.after(0, lambda t=temp: self._atualizar_ui_termica(t))
                time.sleep(2)
        threading.Thread(target=update, daemon=True).start()

    def _atualizar_ui_termica(self, temp):
        if temp <= 0: 
            self.lbl_cpu_temp.config(text="Erro", fg=COR_VERMELHO)
            self.lbl_alerta_termico.config(text="⚠ Falha ao ler sensores (DLL não carregada ou requer Admin)", fg=COR_AMARELO)
            return
            
        if temp < 60:
            cor, status = COR_VERDE, "✓ Sistema Operando em Temperatura Ideal"
        elif temp < 80:
            cor, status = COR_AMARELO, "⚠ Alerta: Temperatura Elevada. Desempenho pode ser afetado."
        else:
            cor, status = COR_VERMELHO, "✖ CRÍTICO: Superaquecimento! Otimizações podem não funcionar."

        self.lbl_cpu_temp.config(text=f"{temp:.1f}°C", fg=cor)
        self.lcd_card.config(highlightbackground=cor, highlightcolor=cor, highlightthickness=1)
        self.lbl_min_max.config(text=f"MIN: {self.sensor.temp_min:.1f}°C\nMAX: {self.sensor.temp_max:.1f}°C")
        self.lbl_alerta_termico.config(text=status, fg=cor)

    def _mapear_discos(self):
        self.mapa_discos = {}
        try:
            cmd = "Get-Partition | Where-Object { $_.DriveLetter } | Select-Object DriveLetter, @{n='MediaType';e={ (Get-Disk -Id $_.DiskId).MediaType }}"
            res = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            for linha in res.stdout.strip().split('\n'):
                partes = linha.split()
                if len(partes) >= 2: self.mapa_discos[partes[0] + ":"] = partes[1].upper()
        except: pass

    def exibir_info_sistema(self):
        info_win = tk.Toplevel(self.root)
        info_win.title("Sobre seu Computador")
        info_win.geometry("600x400")
        info_win.configure(bg="#202020")
        info_win.transient(self.root)
        info_win.grab_set()

        main_frame = tk.Frame(info_win, bg="#202020", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        def add_line(label, value, color="white"):
            f = tk.Frame(main_frame, bg="#202020")
            f.pack(fill=tk.X, pady=5)
            tk.Label(f, text=label, font=("Segoe UI", 10, "bold"), bg="#202020", fg="#aaaaaa", width=20, anchor="w").pack(side=tk.LEFT)
            tk.Label(f, text=value, font=("Segoe UI", 10), bg="#202020", fg=color, anchor="w", wraplength=350).pack(side=tk.LEFT, fill=tk.X)

        add_line("Processador:", platform.processor())
        add_line("RAM:", f"{psutil.virtual_memory().total / (1024**3):.1f} GB")
        add_line("S.O:", f"{platform.system()} {platform.release()}")
        
        tk.Button(info_win, text="Fechar", command=info_win.destroy, bg="#444", fg="white", relief=tk.FLAT).pack(pady=10)

    def _validar_click_desfragmentar(self):
        if self.vars["desfragmentacao"].get(): return True
        hdds = [l for l, t in self.mapa_discos.items() if t == "HDD"]
        if not hdds:
            messagebox.showwarning("Bloqueado", "SSD detectado. Desfragmentação desnecessária em SSDs.")
            return False
        return True

    def _criar_botao(self, parent, texto, comando, cor):
        btn = tk.Button(parent, text=texto, command=comando, bg=cor, fg="white", font=("Segoe UI", 10, "bold"),
                        relief=tk.FLAT, bd=0, padx=20, pady=12, cursor="hand2")
        btn.bind("<Enter>", lambda e: btn.config(bg=self._ajustar_brilho(cor, 1.1)))
        btn.bind("<Leave>", lambda e: btn.config(bg=cor))
        return btn

    def _ajustar_brilho(self, hex_color, factor):
        try:
            r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
            return f"#{min(255, int(r*factor)):02x}{min(255, int(g*factor)):02x}{min(255, int(b*factor)):02x}"
        except: return hex_color

    def _atualizar_relogio(self):
        self.relogio_text.set(time.strftime("%H:%M:%S"))
        self.root.after(1000, self._atualizar_relogio)

    def _iniciar_verificacao_background(self):
        threading.Thread(target=self.sugerir_acoes, args=(True,), daemon=True).start()

    def run_command(self, command, shell_mode=False):
        subprocess.run(command, shell=shell_mode, creationflags=subprocess.CREATE_NO_WINDOW)

    def sugerir_acoes(self, silent=False):
        try:
            if psutil.disk_usage('C:').percent > 85: self.vars["limpezaDisco"].set(True)
            temp_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Temp')
            if os.exists(temp_path) and len(os.listdir(temp_path)) > 30: self.vars["limparTemp"].set(True)
        except: pass
        self._update_status("Sistema pronto.")

    def iniciar_execucao(self):
        if not any(v.get() for v in self.vars.values()): 
            messagebox.showwarning("Aviso", "Selecione ao menos uma opção.")
            return
        self.status_text.set("Iniciando otimização...")
        threading.Thread(target=self._processar_fila, daemon=True).start()

    def _processar_fila(self):
        sel = {k: v.get() for k, v in self.vars.items()}
        if sel["limparTemp"]: 
            self._update_status("Limpando arquivos temporários...")
            self._limpar_temp()
        if sel["sfc"]: 
            self._update_status("Executando SFC Scannow (pode demorar)...")
            self.run_command("sfc /scannow", True)
        
        self._update_status("Concluído!")
        messagebox.showinfo("Sucesso", "Otimização concluída!")

    def _update_status(self, texto):
        if self.root.winfo_exists():
            self.root.after(0, lambda: self.status_text.set(texto))

    def _limpar_temp(self):
        p = os.path.join(os.getenv('LOCALAPPDATA'), 'Temp')
        for i in os.listdir(p):
            try:
                ip = os.path.join(p, i)
                if os.path.isfile(ip): os.unlink(ip)
                else: shutil.rmtree(ip)
            except: pass

if __name__ == "__main__":
    import ctypes
    if not ctypes.windll.shell32.IsUserAnAdmin():
        root = tk.Tk(); root.withdraw()
        messagebox.showwarning("Permissão Necessária", "Este aplicativo precisa de privilégios de Administrador para acessar os sensores de temperatura e reparar o sistema.")
        root.destroy()
    else:
        root = tk.Tk()
        app = OtimizadorApp(root)
        root.mainloop()