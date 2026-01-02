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

# --- Configurações Visuais Globais ---
VERSAO = "2.3"
COR_FUNDO = "#2b2b2b"       # Cinza escuro principal
COR_TEXTO = "#ffffff"       # Branco
COR_DESTAQUE = "#007acc"    # Azul moderno
COR_VERDE = "#4caf50"       # Verde (Ligado/Bom)
COR_VERMELHO = "#f44336"    # Vermelho (Desligado/Ruim)
COR_AMARELO = "#ffeb3b"     # Amarelo (Alerta)
COR_CARD = "#3c3c3c"        # Cor de fundo dos botões/cards
COR_RODAPE = "#888888"      # Cinza claro para assinatura

class ToolTip:
    """Classe para exibir dicas flutuantes ao passar o mouse."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        frame = tk.Frame(tw, bg="#1e1e1e", bd=1, relief=tk.SOLID)
        frame.pack()
        
        label = tk.Label(
            frame, text=self.text, justify=tk.LEFT,
            background="#1e1e1e", fg="#dcdcdc",
            font=("Segoe UI", 9), relief=tk.FLAT, padx=5, pady=3
        )
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class ModernToggle(tk.Canvas):
    """
    Widget personalizado que simula um interruptor (Switch).
    """
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
        self.root.geometry("780x850") 
        self.root.configure(bg=COR_FUNDO)
        self.root.resizable(False, False)

        # Variáveis de Controle
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
        self.status_text.set("Carregando informações do sistema...")
        self.relogio_text = tk.StringVar()

        # Dicionário para armazenar info de TODAS as unidades: {'C:': 'SSD', 'D:': 'HDD'}
        self.mapa_discos = {} 

        # Inicia detecção antes da UI
        self._mapear_discos()
        self._setup_ui()
        self._iniciar_verificacao_background()

    def _mapear_discos(self):
        """
        Mapeia todos os discos e seus tipos (HDD/SSD).
        """
        self.mapa_discos = {}
        try:
            cmd = "Get-Partition | Where-Object { $_.DriveLetter } | Select-Object DriveLetter, @{n='MediaType';e={ (Get-Disk -Id $_.DiskId).MediaType }}"
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW

            res = subprocess.run(
                ["powershell", "-Command", cmd], 
                capture_output=True, text=True, creationflags=creation_flags
            )
            
            linhas = res.stdout.strip().split('\n')
            for linha in linhas:
                partes = linha.split()
                if len(partes) >= 2:
                    letra = partes[0] + ":" # Adiciona os dois pontos (C -> C:)
                    tipo = partes[1].upper()
                    self.mapa_discos[letra] = tipo
            
        except Exception as e:
            print(f"Erro ao detectar discos: {e}")

    def _setup_ui(self):
        # --- Cabeçalho ---
        header_frame = tk.Frame(self.root, bg=COR_FUNDO)
        header_frame.pack(pady=25, fill=tk.X)

        lbl_titulo = tk.Label(header_frame, textvariable=self.relogio_text, font=("Segoe UI", 36, "bold"), bg=COR_FUNDO, fg=COR_TEXTO)
        lbl_titulo.pack()

        lbl_subtitulo = tk.Label(header_frame, text="Selecione as ações de otimização", font=("Segoe UI", 13), bg=COR_FUNDO, fg="#aaaaaa")
        lbl_subtitulo.pack()

        # --- Área de Opções (Grid) ---
        container = tk.Frame(self.root, bg=COR_FUNDO)
        container.pack(padx=25, pady=10, fill=tk.BOTH, expand=True)

        opcoes_info = [
            ("Reparar Sistema (SFC)", "sfc", "Verifica e repara arquivos corrompidos do sistema."),
            ("Limpeza de Disco", "limpezaDisco", "Remove arquivos desnecessários e libera espaço."),
            ("Verificar Disco (CHKDSK)", "chkdsk", "Verifica erros no disco rígido (requer reinicialização)."),
            ("Diagnóstico Memória", "diagnostico", "Agenda teste de memória RAM para a próxima reinicialização."),
            ("Desfragmentar (HDD)", "desfragmentacao", "Desfragmenta apenas HDDs. Ignora SSDs para segurança."),
            ("Redefinir Rede", "redefinirRede", "Reseta configurações de rede (corrige problemas de conexão)."),
            ("Restaurar Imagem (DISM)", "restauraIntegridadeWindows", "Repara a imagem do Windows online (pode demorar)."),
            ("Atualizações (Windows Update)", "verificaAtualizacaoPendente", "Força verificação e instalação de updates."),
            ("Limpar Pasta Temp", "limparTemp", "Limpa cache temporário do usuário atual."),
            ("Reiniciar ao Final", "reiniciar", "Reinicia o PC automaticamente após concluir.")
        ]

        for i, (titulo, chave, dica) in enumerate(opcoes_info):
            row = i // 2
            col = i % 2
            
            card = tk.Frame(container, bg=COR_CARD, bd=0, padx=15, pady=12)
            card.grid(row=row, column=col, sticky="ew", padx=8, pady=8)
            container.grid_columnconfigure(col, weight=1)

            lbl = tk.Label(card, text=titulo, bg=COR_CARD, fg=COR_TEXTO, font=("Segoe UI", 11, "bold"))
            lbl.pack(side=tk.LEFT, anchor="w", fill=tk.X, expand=True)
            
            comando_especifico = None
            if chave == "desfragmentacao":
                comando_especifico = self._validar_click_desfragmentar

            toggle = ModernToggle(card, self.vars[chave], command=comando_especifico)
            toggle.pack(side=tk.RIGHT)
            
            ToolTip(card, dica)
            ToolTip(lbl, dica)

        # --- Área de Status ---
        status_frame = tk.Frame(self.root, bg="#1e1e1e", padx=15, pady=15)
        status_frame.pack(fill=tk.X, padx=25, pady=10)
        
        lbl_status_titulo = tk.Label(status_frame, text="Status Atual:", font=("Segoe UI", 9, "bold"), bg="#1e1e1e", fg="#aaaaaa")
        lbl_status_titulo.pack(anchor="w")
        
        lbl_status = tk.Label(status_frame, textvariable=self.status_text, font=("Segoe UI", 10), bg="#1e1e1e", fg=COR_DESTAQUE, wraplength=700, justify=tk.LEFT)
        lbl_status.pack(anchor="w", fill=tk.X)

        # --- Botões de Ação ---
        btn_frame = tk.Frame(self.root, bg=COR_FUNDO)
        btn_frame.pack(pady=15)

        self._criar_botao(btn_frame, "INICIAR OTIMIZAÇÃO", self.iniciar_execucao, COR_VERDE).pack(side=tk.LEFT, padx=10)
        self._criar_botao(btn_frame, "SUGESTÃO AUTOMÁTICA", self.sugerir_acoes, COR_DESTAQUE).pack(side=tk.LEFT, padx=10)
        # Novo Botão
        self._criar_botao(btn_frame, "SOBRE O PC", self.exibir_info_sistema, "#5b5b5b").pack(side=tk.LEFT, padx=10)
        self._criar_botao(btn_frame, "SAIR", self.root.quit, COR_VERMELHO).pack(side=tk.LEFT, padx=10)

        # --- RODAPÉ ---
        footer_frame = tk.Frame(self.root, bg=COR_FUNDO)
        footer_frame.pack(side=tk.BOTTOM, pady=15)
        
        lbl_assinatura = tk.Label(
            footer_frame, 
            text="Desenvolvido por Daniel Boechat", 
            font=("Segoe UI", 9, "italic"), 
            bg=COR_FUNDO, 
            fg=COR_RODAPE
        )
        lbl_assinatura.pack()

        self._atualizar_relogio()

    # --- Lógica do Info Sistema ---
    def exibir_info_sistema(self):
        # Janela Modal
        info_win = tk.Toplevel(self.root)
        info_win.title("Sobre seu Computador")
        info_win.geometry("600x700")
        info_win.configure(bg="#202020")
        info_win.transient(self.root) 
        info_win.grab_set() # Foca na janela

        # Coletar dados
        cpu_nome = platform.processor()
        try:
             # Tenta pegar nome mais limpo via subprocess
             cpu_nome = subprocess.check_output("wmic cpu get name", shell=True).decode().split('\n')[1].strip()
        except: pass

        cpu_nucleos = psutil.cpu_count(logical=False)
        cpu_threads = psutil.cpu_count(logical=True)
        cpu_freq = psutil.cpu_freq()
        cpu_freq_max = f"{cpu_freq.max:.0f} MHz" if cpu_freq else "N/A"

        mem = psutil.virtual_memory()
        ram_total = f"{mem.total / (1024**3):.1f} GB"

        # Versão do Windows e Check de Atualização (Heurística baseada em Build)
        win_ver = sys.getwindowsversion()
        build = win_ver.build
        sistema_nome = f"Windows {platform.release()} ({platform.version()})"
        
        status_update = "Desconhecido"
        cor_update = "#aaaaaa"
        
        # Build 22621/22631 = Win 11 22H2/23H2. Build 19045 = Win 10 22H2
        if (build >= 22621) or (build >= 19045 and build < 22000):
            status_update = "Aparentemente Atualizado (Versão Recente)"
            cor_update = COR_VERDE
        elif build < 19044:
            status_update = "Possivelmente Desatualizado (Build Antiga)"
            cor_update = COR_AMARELO

        # --- Layout do Card ---
        main_frame = tk.Frame(info_win, bg="#202020", padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text="Informações do Hardware", font=("Segoe UI", 18, "bold"), bg="#202020", fg="white").pack(pady=(0, 20))

        # Função auxiliar para criar linhas
        def add_line(label, value, color="white"):
            f = tk.Frame(main_frame, bg="#202020")
            f.pack(fill=tk.X, pady=5)
            tk.Label(f, text=label, font=("Segoe UI", 10, "bold"), bg="#202020", fg="#aaaaaa", width=20, anchor="w").pack(side=tk.LEFT)
            tk.Label(f, text=value, font=("Segoe UI", 10), bg="#202020", fg=color, anchor="w", wraplength=350).pack(side=tk.LEFT, fill=tk.X)

        add_line("Sistema Operacional:", sistema_nome)
        add_line("Status Atualização:", status_update, cor_update)
        tk.Frame(main_frame, bg="#444", height=1).pack(fill=tk.X, pady=10)
        
        add_line("Processador:", cpu_nome)
        add_line("Núcleos / Threads:", f"{cpu_nucleos} Cores / {cpu_threads} Threads")
        add_line("Clock Máximo:", cpu_freq_max)
        tk.Frame(main_frame, bg="#444", height=1).pack(fill=tk.X, pady=10)
        
        add_line("Memória RAM:", ram_total)
        tk.Frame(main_frame, bg="#444", height=1).pack(fill=tk.X, pady=10)

        tk.Label(main_frame, text="Armazenamento", font=("Segoe UI", 12, "bold"), bg="#202020", fg="white").pack(anchor="w", pady=(0, 10))

        # Lista de Discos
        discos_frame = tk.Frame(main_frame, bg="#202020")
        discos_frame.pack(fill=tk.BOTH, expand=True)

        particoes = psutil.disk_partitions()
        for part in particoes:
            if "cdrom" in part.opts or part.fstype == "":
                continue
                
            try:
                usage = psutil.disk_usage(part.mountpoint)
                letra = part.device.replace("\\", "")
                tipo = self.mapa_discos.get(letra, "Desconhecido") # Pega do nosso mapa
                
                total_gb = f"{usage.total / (1024**3):.1f} GB"
                usado_gb = f"{usage.used / (1024**3):.1f} GB"
                livre_gb = f"{usage.free / (1024**3):.1f} GB"
                percent = usage.percent

                # Card do Disco
                d_card = tk.Frame(discos_frame, bg="#2b2b2b", bd=1, relief=tk.SOLID, padx=10, pady=10)
                d_card.pack(fill=tk.X, pady=5)

                header = tk.Frame(d_card, bg="#2b2b2b")
                header.pack(fill=tk.X)
                
                # Ícone/Texto Tipo
                cor_tipo = COR_DESTAQUE if tipo == "SSD" else "#e67e22"
                tk.Label(header, text=f"[{tipo}]", font=("Segoe UI", 9, "bold"), bg="#2b2b2b", fg=cor_tipo).pack(side=tk.LEFT)
                tk.Label(header, text=f"Unidade {letra}", font=("Segoe UI", 10, "bold"), bg="#2b2b2b", fg="white").pack(side=tk.LEFT, padx=5)
                tk.Label(header, text=f"Total: {total_gb}", font=("Segoe UI", 9), bg="#2b2b2b", fg="#aaaaaa").pack(side=tk.RIGHT)

                # Info de Uso
                tk.Label(d_card, text=f"Usado: {usado_gb} | Livre: {livre_gb}", font=("Segoe UI", 8), bg="#2b2b2b", fg="#cccccc").pack(anchor="w")

                # Barra de Progresso Customizada
                bar_frame = tk.Canvas(d_card, height=6, bg="#444", highlightthickness=0)
                bar_frame.pack(fill=tk.X, pady=5)
                bar_width = percent / 100 * 500 # Aproximação visual
                
                cor_barra = COR_VERDE
                if percent > 75: cor_barra = COR_AMARELO
                if percent > 90: cor_barra = COR_VERMELHO
                
                # O canvas precisa ser desenhado após o pack renderizar a largura real, 
                # mas aqui faremos uma barra relativa usando create_rectangle com bind se fosse complexo.
                # Simplificando: usamos place relativo no canvas ou ttk.Progressbar.
                # Vamos usar ttk.Style para manter o tema dark
                
                style = ttk.Style()
                style.theme_use('default')
                style.configure("Dark.Horizontal.TProgressbar", background=cor_barra, troughcolor="#444444", thickness=6)
                
                pb = ttk.Progressbar(d_card, style="Dark.Horizontal.TProgressbar", orient="horizontal", length=100, mode="determinate", value=percent)
                pb.pack(fill=tk.X)

            except Exception as e:
                print(e)
        
        # Botão Fechar Modal
        tk.Button(info_win, text="Fechar", command=info_win.destroy, bg="#444", fg="white", font=("Segoe UI", 9), relief=tk.FLAT).pack(pady=10)


    def _validar_click_desfragmentar(self):
        """
        Função executada ANTES de mudar o estado do botão de desfragmentação.
        """
        if self.vars["desfragmentacao"].get() == True:
            return True

        # Filtra apenas os HDDs do mapa geral
        hdds_encontrados = [letra for letra, tipo in self.mapa_discos.items() if tipo == "HDD"]

        if not hdds_encontrados:
            messagebox.showwarning(
                "Ação Bloqueada", 
                "Seu computador possui apenas armazenamento SSD.\n\n"
                "A desfragmentação não é necessária e pode reduzir a vida útil do seu SSD.\n"
                "Esta opção permanecerá desabilitada."
            )
            return False 
        else:
            unidades_str = ", ".join(hdds_encontrados)
            messagebox.showinfo(
                "Atenção - Modo Inteligente",
                f"Detectamos armazenamento misto ou HDD.\n\n"
                f"A desfragmentação será executada APENAS nas unidades: {unidades_str}.\n"
                "As unidades SSD serão ignoradas automaticamente."
            )
            return True

    def _criar_botao(self, parent, texto, comando, cor):
        btn = tk.Button(
            parent, text=texto, command=comando,
            bg=cor, fg="white", font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, bd=0, padx=20, pady=12, cursor="hand2"
        )
        btn.bind("<Enter>", lambda e: btn.config(bg=self._ajustar_brilho(cor, 1.1)))
        btn.bind("<Leave>", lambda e: btn.config(bg=cor))
        return btn
    
    def _ajustar_brilho(self, hex_color, factor):
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f"#{r:02x}{g:02x}{b:02x}"

    def _atualizar_relogio(self):
        agora = time.strftime("%H:%M:%S")
        self.relogio_text.set(agora)
        self.root.after(1000, self._atualizar_relogio)

    def _iniciar_verificacao_background(self):
        self.status_text.set("Analisando sistema para sugestões...")
        threading.Thread(target=self.sugerir_acoes, args=(True,), daemon=True).start()

    # --- Lógica de Negócio ---

    def run_command(self, command, shell_mode=False):
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NO_WINDOW
        subprocess.run(command, shell=shell_mode, creationflags=creation_flags)

    def sugerir_acoes(self, silent=False):
        if not silent: self.status_text.set("Analisando métricas do sistema...")
        sugestao = {k: False for k in self.vars}
        
        try:
            tempo_atividade = time.time() - psutil.boot_time()
            if tempo_atividade > 60 * 60 * 72: sugestao["reiniciar"] = True

            try:
                disco = psutil.disk_usage('C:')
                if disco.percent > 85: sugestao["limpezaDisco"] = True
            except: pass

            temp_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Temp')
            try:
                if len(os.listdir(temp_path)) > 30: sugestao["limparTemp"] = True
            except: pass

            try:
                subprocess.check_output("ping www.google.com -n 1", shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except: sugestao["redefinirRede"] = True

            if sys.platform == "win32": sugestao["sfc"] = True

            # Sugere desfragmentação APENAS se houver HDD
            if "HDD" in self.mapa_discos.values():
                sugestao["desfragmentacao"] = True

        except Exception as e:
            if not silent: messagebox.showerror("Erro", f"Erro na análise: {e}")

        def aplicar_gui():
            for k, v in sugestao.items():
                if v: self.vars[k].set(True)
            if not silent:
                self.status_text.set("Análise concluída. Sugestões aplicadas.")
                messagebox.showinfo("Sugestão", "Opções recomendadas foram marcadas.")
            else:
                self.status_text.set("Sistema pronto. Selecione as opções.")

        self.root.after(0, aplicar_gui)

    def iniciar_execucao(self):
        if not any(v.get() for v in self.vars.values()):
            messagebox.showwarning("Atenção", "Selecione pelo menos uma opção.")
            return

        self.status_text.set("Iniciando processos...")
        threading.Thread(target=self._processar_fila, daemon=True).start()

    def _processar_fila(self):
        selecionadas = {k: v.get() for k, v in self.vars.items()}

        if selecionadas["limparTemp"]:
            self._update_status("Limpando pasta Temp...")
            self._limpar_temp()

        if selecionadas["sfc"]:
            self._update_status("Executando SFC /Scannow...")
            self.run_command("sfc /scannow", shell_mode=True)

        if selecionadas["limpezaDisco"]:
            self._update_status("Executando Limpeza de Disco...")
            self.run_command("cleanmgr /sagerun:99", shell_mode=True)

        if selecionadas["chkdsk"]:
            self._update_status("Agendando CHKDSK...")
            self.run_command("echo y | chkdsk C: /f", shell_mode=True)

        if selecionadas["diagnostico"]:
            self._update_status("Agendando Diagnóstico de Memória...")
            self.run_command("mdsched.exe", shell_mode=True)

        if selecionadas["redefinirRede"]:
            self._update_status("Redefinindo Winsock...")
            self.run_command("netsh winsock reset", shell_mode=True)

        if selecionadas["restauraIntegridadeWindows"]:
            self._update_status("Executando DISM...")
            self.run_command("dism /online /cleanup-image /restorehealth", shell_mode=True)

        if selecionadas["verificaAtualizacaoPendente"]:
            self._update_status("Verificando Updates...")
            self.run_command("wuauclt /ddetectnow", shell_mode=True)

        # --- LÓGICA DE EXECUÇÃO SEGURA ---
        if selecionadas["desfragmentacao"]:
            hdds = [letra for letra, tipo in self.mapa_discos.items() if tipo == "HDD"]
            if not hdds:
                self._update_status("Nenhum HDD detectado. Desfragmentação ignorada.")
            else:
                for unidade in hdds:
                    self._update_status(f"Desfragmentando unidade HDD: {unidade}...")
                    try:
                        self.run_command(f"defrag {unidade} /U /V", shell_mode=True)
                    except: pass
        # -------------------------------------

        self._update_status("Processos finalizados!")
        
        if selecionadas["reiniciar"]:
            self._update_status("Reiniciando em 5 segundos...")
            time.sleep(2)
            self.run_command("shutdown /r /f /t 5", shell_mode=True)
        else:
            self.root.after(0, lambda: messagebox.showinfo("Concluído", "Otimização finalizada com sucesso!"))

    def _update_status(self, texto):
        self.root.after(0, lambda: self.status_text.set(texto))

    def _limpar_temp(self):
        temp_path = os.path.join(os.getenv('LOCALAPPDATA'), 'Temp')
        try:
            for item in os.listdir(temp_path):
                item_path = os.path.join(temp_path, item)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path): os.unlink(item_path)
                    elif os.path.isdir(item_path): shutil.rmtree(item_path)
                except: pass
        except: pass

if __name__ == "__main__":
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0

    if not is_admin:
        root = tk.Tk()
        root.withdraw()
        messagebox.showwarning("Permissão Necessária", "Este programa precisa ser executado como Administrador.")
        root.destroy()
    else:
        root = tk.Tk()
        app = OtimizadorApp(root)
        root.mainloop()