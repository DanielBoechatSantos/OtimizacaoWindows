# 🚀 Otimizador do Windows v3.0 (Thermal Edition)

Uma ferramenta gráfica moderna desenvolvida em Python para centralizar e automatizar tarefas essenciais de manutenção e otimização do Windows.

## 🛠️ Funcionalidades Principais

* **Reparo de Sistema (SFC & DISM):** Verifica a integridade dos arquivos e restaura a imagem do Windows.
* **Gestão de Armazenamento:**
    * **Limpeza de Disco:** Remove arquivos desnecessários do sistema.
    * **Limpeza de Pasta Temp:** Exclui o cache temporário do usuário.
    * **Desfragmentação Inteligente:** Detecta automaticamente se a unidade é **SSD ou HDD**. Bloqueia a desfragmentação em SSDs para preservar a vida útil e executa apenas em HDDs.
* **Rede:** Redefinição de Winsock para corrigir problemas de conexão.
* **Hardware & Diagnóstico:**
    * Agendamento de **CHKDSK** e teste de memória RAM.
    * Painel **"Sobre o PC"** com informações detalhadas de CPU, RAM e uso de disco em tempo real.
* **Sugestão Automática:** Analisa o tempo de atividade e o espaço em disco para sugerir as melhores ações ao usuário.
* **Monitoramento de Temperatura em Tempo Real** Verifica em tempo real a temperatura do processador, indicando que a temperatura elevada pode comprometer o desempenho do hardware.
**Feedback Visual por Cores**: 
  - 🟢 **Verde**: Temperatura estável (< 60°C).
  - 🟡 **Amarelo**: Carga moderada (60°C - 80°C).
  - 🔴 **Vermelho**: Alerta crítico (> 80°C).
- **Persistência de Dados**: Exibe as temperaturas **Mínima** e **Máxima** alcançadas durante a sessão.
- **Alta Precisão**: Diferente da API WMI padrão, utiliza drivers de baixo nível para leitura real do die da CPU.

## 📸 Preview
<img width="825" height="952" alt="preview" src="https://github.com/user-attachments/assets/61ad2bb7-71a5-43bf-9cae-b02a8175c735" />

## Nova Função - Desativar Serviços Extras

**Abre uma sugestão de serviços extras do Windows que podem ser desativados, onde o usuário poderá escolher. Nos serviços, é explicado o que faz e o ganho de desempenho esperado.**

<img width="501" height="635" alt="image" src="https://github.com/user-attachments/assets/8d6a68d3-62e4-48c7-8818-747279733575" />


## 🖥️ Pré-requisitos

Antes de rodar o projeto, você precisará:

1.  **Python 3.12.x** instalado.
2.  As seguintes bibliotecas Python:
    ```bash
    pip install PyQt5 pythonnet
    ```
* Privilégios de **Administrador** (necessário para executar comandos de sistema como SFC e Defrag e acessar os sensores de temperatura).

## 🛠️ Tecnologias Utilizadas

* **Python 3.12**: Lógica principal e interface.
* **C++ / .NET**: Ponte de comunicação com sensores de hardware.
* **Pythonnet**: Integração entre o ambiente Python e a DLL do Open Hardware Monitor.
* `psutil`: Monitoramento de hardware e processos.
* `tkinter`: Interface gráfica (nativa do Python).

## 🔧 Instalação e Execução

1.  Clone o repositório:
    ```bash
      git clone https://github.com/DanielBoechatSantos/OtimizacaoWindows.git
    ```    
2.  Certifique-se de que o arquivo `OpenHardwareMonitorLib.dll` está na mesma pasta que o script.
3. Instale as dependências:
   \\\ash
   pip install psutil pythonnet
   \\\
4.  **Importante**: Clique com o botão direito na DLL -> Propriedades -> Marque **Desbloquear**.
5.  Execute a aplicação:
    ```bash
      python OtimizacaoWindows.py
    ```

## ⚠️ Aviso
Este software executa comandos de manutenção de baixo nível no Windows. Use com responsabilidade.

---
**Desenvolvido por Daniel Boechat**
