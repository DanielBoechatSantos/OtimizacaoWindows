# 🚀 Otimizador do Windows v4.0 (Advanced Maintenance Edition)

Uma suíte completa, moderna e de alto desempenho para **manutenção profunda, diagnóstico e otimização do Windows**, desenvolvida com **Python, C# / .NET nativo e PyQt5** sob design Dark Glassmorphism.

Projetada para ser ao mesmo tempo **extremamente poderosa para usuários avançados e técnicos de TI**, e **simples, intuitiva e segura em 1 clique para o usuário final**.

---

## 🌟 O Que Há de Novo na Versão 4.0

* ⚡ **DLL Nativa C# (`SystemOptimizerCore.dll`) + Fallback Win32 / Ctypes**:
  - Liberação instantânea de memória RAM compactando os *Working Sets* de todos os processos ativos via `EmptyWorkingSet`.
  - Limpeza nativa de cache DNS em milissegundos (`DnsFlushResolverCache` via `dnsapi.dll`).
  - Esvaziamento silencioso e direto da Lixeira do Windows sem diálogos intrusivos.
  - Arquitetura de fallback duplo garantindo 100% de compatibilidade em qualquer versão do Python (Python 3.8 até 3.14+).

* 🔍 **Diagnóstico Inteligente com Health Score (0 a 100%)**:
  - Varredura em tempo real avaliando pressão de memória RAM, volume de arquivos temporários, espaço livre em disco, tempo de atividade (uptime) e atualizações pendentes.
  - Exibição de um Scorecard com diagnóstico visual e botão **"✨ Aplicar Otimizações Recomendadas em 1 Clique"**.

* ⚡ **Barra de Ações Rápidas (1-Click Boost)**:
  - **Otimizar RAM Instantâneo**: Recupera centenas de MB ou GB de memória RAM com relatório imediato.
  - **Limpar Cache DNS**: Resolve travamentos de navegação e rotas corrompidas.
  - **Plano de Desempenho Máximo**: Ativa o plano de energia de alto rendimento do Windows (*Ultimate Performance*).
  - **Sugestão Inteligente**: Avaliação automática do PC em segundos.

* 🛠️ **Execução Completa de Todas as Rotinas de Manutenção**:
  - **SFC Scannow**: Verificação e reparo de integridade de arquivos do Windows com streaming do percentual de progresso em tempo real.
  - **DISM (RestoreHealth & Limpeza WinSxS)**: Reparação completa da imagem do sistema e limpeza do repositório de componentes.
  - **Limpeza Profunda de Disco**: Remove instaladores antigos do Windows Update (`SoftwareDistribution\Download`), relatórios de erro (`WER`), mini-dumps de travamento e pré-busca.
  - **Limpeza de Temporários & Lixeira**: Limpa `%TEMP%`, diretório temporário do sistema e lixeira.
  - **TRIM Inteligente para SSDs & Defrag para HDDs**: Detecta automaticamente se a unidade é SSD/NVMe ou HDD magnético. Executa comando TRIM em SSDs para recuperar velocidade de escrita e prolongar a vida útil do NAND Flash, e executa desfragmentação completa apenas em discos rígidos.
  - **Redefinição da Pilha de Rede**: Restauração de Winsock, redefinição de TCP/IP e renovação de rotas.
  - **Verificação de Disco (CHKDSK)**: Análise não destrutiva do sistema de arquivos NTFS.
  - **Diagnóstico de Memória**: Testes de integridade de RAM e agendamento de diagnóstico do Windows.
  - **Verificação do Windows Update**: Consulta e detecção de atualizações e reinicializações pendentes.

* ⚙️ **Gerenciador Avançado de Serviços & Tweaks de Privacidade**:
  - Desativação segura e categorizada de telemetria da Microsoft (DiagTrack), assistente Copilot, widgets pesados da barra de tarefas, gravação GameDVR em segundo plano, otimização de entrega P2P e histórico de atividades.
  - Explicações claras do impacto e botão de **"Selecionar Recomendados"**.

* 🖥️ **Painel Detalhado "Sobre o PC"**:
  - Visão detalhada de Processador (Cores, Frequências, Carga), Memória RAM (Total, Usada, Slots e Velocidade em MHz), Armazenamento (Lista de unidades, tipo SSD/HDD, espaço livre e saúde), Placa de Vídeo (GPU, VRAM, Resolução e Driver), Placa-Mãe, BIOS e Rede.
  - Botão para **Exportar Relatório Completo do PC (.TXT)**.

* 📊 **Monitor Térmico e de Recursos em Tempo Real**:
  - Leitura multi-fonte de temperatura da CPU com rastreamento de mínimas e máximas da sessão.
  - Barra dinâmica de consumo de memória RAM com alerta por cores.

* 🛡️ **Suporte a Auto-Elevação de Privilégios (UAC)**:
  - Detecção amigável de privilégios de Administrador com botão de reinicialização elevada em 1 clique.

---

## 🛠️ Tecnologias e Arquitetura

* **Python 3.10 / 3.12 / 3.14**: Lógica central e orquestração.
* **PyQt5**: Interface gráfica responsiva com tema Dark Glassmorphism.
* **C# / .NET Framework (`SystemOptimizerCore.dll`)**: Biblioteca nativa de alta velocidade compilada via `csc.exe`.
* **Win32 APIs / Ctypes**: Integração de baixo nível com `psapi.dll`, `kernel32.dll`, `shell32.dll`, `dnsapi.dll`, `advapi32.dll` e `ntdll.dll`.
* **PowerShell / CIM**: Detecção de hardware, discos físicos e controladores.

---

## 📦 Estrutura dos Arquivos

```
OtimizacaoWindows/
├── OtimizacaoWindows.py           # Interface Gráfica Principal (PyQt5) e Ponto de Entrada
├── native_core.py                 # Integração nativa Win32, Ctypes, RAM Purge, DNS e Sensores
├── system_info.py                 # Extrator de informações avançadas de hardware e SO
├── smart_advisor.py               # Diagnóstico inteligente e cálculo de Health Score
├── optimizer_engine.py            # Motor de tarefas assíncronas com QThread e logs
├── SystemOptimizerCore.cs         # Código-fonte C# da DLL nativa
├── SystemOptimizerCore.dll        # DLL nativa de alta performance (.NET 4.0+)
├── OpenHardwareMonitorLib.dll     # Biblioteca de sensores de hardware
├── OpenHardwareMonitorLib.sys     # Driver de baixo nível para sensores
├── img/                           # Ícones e assets visuais
└── README.md                      # Documentação do projeto
```

---

## 🚀 Como Executar

### 1. Pré-requisitos
* **Python 3.8+** (Recomendado 3.10, 3.12 ou 3.14).
* Instale as dependências Python:
```bash
pip install PyQt5 psutil
```

*(Opcional: `pythonnet` se desejar usar OpenHardwareMonitorLib diretamente, caso contrário o sistema utiliza o motor nativo WMI/Win32 automaticamente).*

### 2. Compilar a DLL Nativa (Caso queira recompilar)
A DLL `SystemOptimizerCore.dll` já vem pronta. Se desejar recompilá-la utilizando o compilador nativo do próprio Windows:
```powershell
& 'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe' /target:library /optimize+ /platform:anycpu /r:System.Management.dll /out:SystemOptimizerCore.dll SystemOptimizerCore.cs
```

### 3. Iniciar o Aplicativo
Abra o terminal como **Administrador** e execute:
```bash
python OtimizacaoWindows.py
```

---

## ☕ Apoie o Projeto

Se este software ajudou a manter seu computador rápido e saudável, considere apoiar o desenvolvimento contínuo!

* **Chave PIX:** `b74ef2a3-5397-4658-9525-172ec661e73c`
* **LinkedIn:** [Daniel Boechat](https://www.linkedin.com/in/danielboechatsantos/)
* **E-mail:** [daniel.dossants@outlook.com.br](mailto:daniel.dossants@outlook.com.br)

---
**Desenvolvido com excelência por Daniel Boechat**
