# CrossDebate - Plataforma Multimodal de Análise e Interação com Debates

**CrossDebate** é uma plataforma inovadora projetada para analisar e interagir com debates complexos de forma multimodal. Ela combina o poder de grandes modelos de linguagem (LLMs) no formato GGUF com uma representação dinâmica das interações através de um **Hipergrafo de Pensamentos (HoT)**, permitindo uma análise profunda e uma interação refinada com a inteligência artificial.

## Funcionalidades Principais

*   **Interação via Chat com Modelos GGUF:** Converse diretamente com uma variedade de modelos de linguagem GGUF otimizados, explorando diferentes perspectivas sobre um tópico.
*   **Hipergrafo de Pensamentos (HoT) Dinâmico:** Visualize a estrutura das interações e argumentos como um hipergrafo que evolui em tempo real com a conversa.
*   **Ajuste Interativo do HoT:** **(Funcionalidade Chave)** Manipule diretamente as hiperarestas e nós do HoT para refinar, guiar ou corrigir a linha de raciocínio do modelo GGUF, obtendo respostas mais alinhadas com sua intenção.
*   **Análise Multimodal:** Integração planejada para dados textuais, comportamentais (interação do usuário) e neurofisiológicos (EEG, Eye-tracking) para uma compreensão holística do debate. *(Nota: Implementação multimodal completa pode variar)*.
*   **Visualizações Interativas:** Explore os dados e a estrutura do debate através de gráficos e dashboards interativos (Plotly, D3.js).

## Arquitetura e Fluxo de Interação

O CrossDebate opera com uma arquitetura cliente-servidor:

1.  **Frontend:** Uma interface web (HTML/CSS/JS) onde o usuário interage via chat, visualiza o HoT e realiza ajustes.
2.  **Backend (API FastAPI):** Orquestra a lógica principal:
    *   Gerencia a comunicação com os modelos GGUF.
    *   Mantém e atualiza o estado do Hipergrafo de Pensamentos (HoT).
    *   Processa os ajustes do HoT feitos pelo usuário.
    *   Realiza análises e serve dados para o frontend.
3.  **Modelos GGUF:** Armazenados localmente (em `C:\crossdebate\models`), acessados pelo backend para geração de respostas.
4.  **Hipergrafo de Pensamentos (HoT):** Estrutura de dados no backend que modela a dinâmica da conversa.

**Fluxo de Interação Principal:**


Instalação
Pré-requisitos
Python 3.10+

pip (Gerenciador de pacotes Python)

Git
![Uploading crossdebate.png…]()

Passos
Clonar o Repositório:

git clone https://github.com/crossdebate/app.git
cd CrossDebate
Use code with caution.
Bash
Instalar Dependências:

pip install -r requirements.txt
Use code with caution.
Bash
(Certifique-se de que requirements.txt esteja atualizado com as dependências necessárias, incluindo fastapi, uvicorn, llama-cpp-python, bibliotecas de visualização, etc.)

Baixar e Organizar Modelos GGUF:

Crie a pasta models na raiz do projeto: C:\crossdebate\models.

Baixe os modelos GGUF desejados (ex: de Hugging Face) e coloque os arquivos .gguf diretamente dentro desta pasta. O backend irá procurar por eles lá.

Configuração (Opcional):

Verifique o arquivo config.py (ou similar) no backend para ajustar portas, caminhos ou outras configurações, se necessário.

Iniciar os Serviços:

Backend (API): Abra um terminal na pasta raiz do projeto e execute:

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
Use code with caution.
Bash
(Ajuste backend.main:app conforme a estrutura final do seu entrypoint FastAPI)

Frontend: A interface principal é composta por arquivos HTML/CSS/JS. Você pode servi-los localmente usando um servidor simples. Abra outro terminal na pasta raiz e execute:

python -m http.server 8080
Use code with caution.
Bash
(Ou use outra ferramenta como live-server se preferir)

Acessar a Plataforma:

Abra seu navegador e acesse http://localhost:8080 (ou a porta que você usou para o frontend).

A documentação da API estará disponível em http://localhost:8000/docs.

Uso
Acesse a interface web no seu navegador.

Use a interface de chat para interagir com os modelos GGUF sobre um tópico.

Observe a visualização do Hipergrafo de Pensamentos (HoT) que representa a conversa.

Refine as Respostas: Se desejar, interaja com a visualização do HoT (clicando, arrastando, ajustando conexões - dependendo da implementação da UI) para guiar a próxima resposta do modelo.

Continue a conversa, notando como os ajustes no HoT podem influenciar as respostas da IA.

Explore as outras seções (Dashboard, Análise) para visualizar métricas e análises do debate.

Desenvolvimento
Testes: Execute testes unitários e de integração usando pytest.

pytest tests/
Use code with caution.
Bash
Linting: Verifique a qualidade do código com pylint ou flake8.

pylint backend/ src/
Use code with caution.
Bash
Type Checking: Use mypy para verificação estática de tipos.

mypy backend/ src/
Use code with caution.
Bash
Contribuição
Contribuições são bem-vindas! Por favor, abra uma issue para discutir mudanças ou um pull request com suas melhorias.

Licença
MIT License (Ou a licença apropriada para o seu projeto)

---

## Contagem de Arquivos Necessários (HTML, CSS, JS, PY)

Com base na análise e na reestruturação focada, a contagem inicial de arquivos *essenciais* para a funcionalidade principal descrita (interface web, API backend, interação HoT-GGUF) seria:

*   **HTML:** 6 arquivos (`index.html`, `analise.html`, `configuracoes.html`, `dashboard.html`, `performance.html`, `visualizacao.html`)
*   **CSS:** 2 arquivos (`css/style.css`, `css/interactivity.css`)
*   **JavaScript:** 4 arquivos (`js/interactivity.js`, `static/js/analysis.js`, `js/chat.js`, `js/hypergraph_interaction.js`)
*   **Python:** 9 arquivos (Estimativa inicial para o núcleo do backend: `main.py`, `config.py`, `gguf_service.py`, `hot_service.py`, `api/chat.py`, `api/hot.py`, `api/analysis_endpoints.py`, `utils/logging_config.py`, `models.py`)

**Total Estimado:** **21 arquivos**

**Observações:**

*   Esta contagem é uma **estimativa inicial** focada nos tipos de arquivo solicitados e na funcionalidade central. A estrutura real em `crossdebate.txt` é muito mais extensa.
*   Muitos arquivos Python listados em `crossdebate.txt` (como os de monitoramento, otimização, validação, feedback, etc.) são importantes para um sistema robusto, mas podem ser considerados secundários para a *funcionalidade principal* de interação HoT-GGUF e foram omitidos desta contagem inicial.
*   Arquivos de configuração (`.json`, `.yaml`), testes (`test_*.py`), notebooks (`.ipynb`), e outros (`.md`, `.toml`, `.yml`, `.conf`) não foram incluídos na contagem, conforme solicitado.
*   A interface pode precisar de bibliotecas JS adicionais para visualização de grafos (como D3.js ou uma biblioteca específica de hipergrafos), que não estão explicitamente contadas como arquivos `.js` individuais, mas seriam dependências.
