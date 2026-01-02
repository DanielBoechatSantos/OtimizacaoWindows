# 🚀 Otimizador do Windows v2.3

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

## 🖥️ Pré-requisitos

Para rodar este projeto, você precisará de:
* Python 3.x instalado.
* Privilégios de **Administrador** (necessário para executar comandos de sistema como SFC e Defrag).

## 📦 Bibliotecas Utilizadas

* `psutil`: Monitoramento de hardware e processos.
* `tkinter`: Interface gráfica (nativa do Python).

## 🚀 Como Executar

1. Clone o repositório:
   \\\ash
   git clone https://github.com/DanielBoechatSantos/OtimizacaoWindows.git
   \\\
2. Instale as dependências:
   \\\ash
   pip install psutil
   \\\
3. Execute o script como **Administrador**:
   \\\ash
   python OtimizacaoWindows.py
   \\\

## ⚠️ Aviso
Este software executa comandos de manutenção de baixo nível no Windows. Use com responsabilidade.

---
**Desenvolvido por Daniel Boechat**
