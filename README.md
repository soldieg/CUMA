<p align="center">
  <img src="assets/cuma_logo.png" alt="Logo CUMA" width="320">
</p>

**CUMA - Conversor Ultimate de Mangás**

Aplicativo desktop para Windows voltado para limpeza e conversão de PDFs, imagens, EPUB e XTCH, com foco em leitura de mangás, quadrinhos e arquivos escaneados.
Criado para facilitar a crição de mangas apartir de imagens e pdf para Ereaders, como: Xteink X4 e X3, Kindles, kobo, e um perfil personalizado para a sua resolução, Retirando partes não necessarias deixando apenas a imagem em si. Por exemplo um manga ou quadrinho retirado em pdf de um site de leitura online.

Caso queria ajudar no projeto serei muito grato. 

Não sou programador, mas entendo um pouco da logica de programação. Criei este programa usando o Copilot e o ChatGPT para resolver um problema de ler, criar e converter alguns mangas não disponiveis de forma facil e um unico lugar.


## Apoie o projeto

<p align="center">
  <a href="https://nubank.com.br/cobrar/1i9x4q/6a39f5ae-b88c-4be2-9040-0a7d703e2a02">
    Clique aqui para apoiar via Pix
  </a>
</p>

<p align="center">
  <a href="https://www.buymeacoffee.com/soldieg" target="_blank">
      <img src="https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: 41px !important;width: 174px !important;box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;-webkit-box-shadow: 0px 3px 2px 0px rgba(190, 190, 190, 0.5) !important;" >
  </a>
</p>

## Recursos principais

- Limpeza de páginas vazias ou pouco úteis em PDFs.
- Exportação em PDF, CBZ, PDF + CBZ e imagens.
- Conversão PDF → EPUB baseado em imagens.
- Conversão PDF → XTCH.
- Conversão EPUB → XTCH.
- Criação de PDF a partir de imagens.
- Temas visuais, incluindo temas CUMA baseados no ícone.
- Configurações preservadas em `%APPDATA%\CUMA\cuma_settings.json`.
- Sistema de atualização por manifesto JSON no GitHub.

## Novidades da versão 1.100.7

Esta versão é uma atualização de documentação e manual:

- Manual da raiz e `docs/manual_do_programa.txt` atualizados para explicar melhor as funções recentes.
- Manual TXT gerado pelo botão **Manual** do aplicativo alinhado com a versão atual.
- Criado o arquivo `ATUALIZACOES_DESDE_1.100.2.txt` com o resumo consolidado das versões 1.100.2 até 1.100.7.
- `README.md`, `LEIA-ME.txt`, `docs/historico_versoes.md` e `updates/stable.json` alinhados com a versão 1.100.7.

## Novidades da versão 1.100.6

- Em **Ferramentas > Criar PDF de imagens**, agora também é possível adicionar PDFs.
- A mesma ferramenta aceita **CBZ**, **ZIP** e **EPUB com imagens**.
- Também aceita **CBR**, **RAR** e **7Z** quando o 7-Zip estiver instalado e disponível no PATH.
- A geração respeita a ordem manual da lista, inclusive com **Mover pra cima ↑**, **Mover pra baixo ↓** e arraste para reordenar.
- EPUB textual puro não é renderizado nessa função; EPUB com imagens é aceito.

## Novidades da versão 1.100.5

- Adicionados os botões **Mover pra cima ↑** e **Mover pra baixo ↓** nas filas de **Limpar**, **Ferramentas** e **Converter**.
- Adicionada reordenação por clicar, segurar e arrastar uma linha da lista.
- A ordem visível da lista é usada no processamento das funções compatíveis.
- Removido o grande espaço vazio entre os botões e a lista da aba **Converter**.

## Novidades da versão 1.100.4

Esta versão é um acabamento visual e de fluxo em cima da 1.100.3:

- A aba **Converter** ficou mais compacta e clara: as **Conversões compatíveis** agora ficam integradas ao painel **Dispositivos e conversões**.
- O botão **Metadados EPUB** agora aparece somente quando o arquivo detectado é EPUB ou quando alguma conversão de saída para EPUB está marcada.
- A aba **Limpar** não mostra mais o bloco grande de preparação visual na tela principal.
- As opções KCC/E-ink da aba Limpar foram movidas para **Configurações do PDF**, mantendo a tela principal mais simples.
- O botão antigo **Prévia** da aba Limpar foi substituído por **Prévia Limpar**, usando a prévia correta das opções de limpeza.
- Corrigido o hover da tabela/lista para manter o texto legível quando o mouse passa sobre cabeçalhos/linhas.
- A aba **Converter** continua em modo de conversão pura: ela não relimpa, não corta, não divide páginas e não reaplica presets visuais.

### Texto curto para a Release do GitHub

**CUMA 1.100.4** melhora o acabamento visual da aba Converter, integra as conversões compatíveis ao painel de dispositivos, torna os metadados EPUB contextuais, move as opções KCC/E-ink para Configurações do PDF e corrige a legibilidade do hover nas tabelas. Mantém a regra principal: **Limpar prepara/modifica o arquivo; Converter apenas converte o arquivo pronto**.

## Novidades da versão 1.100.3

Esta versão corrige a separação definitiva entre **Limpar** e **Converter**:

- A aba **Converter** agora trabalha em modo de **conversão pura**.
- O Converter não reaplica remoção de margens, presets E-ink, divisão de páginas duplas, webtoon/imagens longas ou rodapé/número de página.
- As conversões PDF→EPUB, PDF→CBZ, PDF→imagens, EPUB→PDF, compactados→EPUB/PDF e imagem→PDF/EPUB usam a página/imagem de entrada sem encaixar em canvas de dispositivo.
- A prévia do Converter foi ajustada para mostrar a entrada real e como ela será enviada ao conversor, sem adicionar faixas brancas.
- A prévia antes/depois da preparação visual não usa mais o perfil de dispositivo como alvo; ela mostra somente o efeito das opções da aba Limpar.
- XTCH continua usando o perfil de dispositivo porque o formato exige dimensões fixas, mas não reaplica os filtros da aba Limpar.

## Novidades da versão 1.100.1

Esta versão reorganiza a separação entre preparação e conversão:

- A aba **Limpar** passa a concentrar as opções que modificam/preparam o conteúdo: presets E-ink, ordem de leitura, remoção de margens, remoção de rodapé/número de página, divisão de páginas duplas, manter original ao dividir e webtoon/imagens longas.
- A aba **Converter** fica focada em formato de saída: dispositivo, pasta de saída, prévia antes/depois, metadados EPUB e conversões.
- As conversões agora são exibidas dinamicamente conforme o tipo de arquivo selecionado.
- PDF pode liberar opções como **PDF → EPUB**, **PDF → XTCH**, **PDF → CBZ** e **PDF → imagens**.
- EPUB pode liberar **EPUB → XTCH** e **EPUB → PDF**.
- CBZ/ZIP/CBR/RAR/7Z podem liberar **compactado → EPUB**, **compactado → XTCH** e **compactado → PDF**.
- Imagens podem liberar **imagem → PDF**, **imagem → EPUB** e **imagem → XTCH**.
- CBZ/ZIP continuam funcionando nativamente; CBR/RAR/7Z continuam dependendo do 7-Zip instalado no Windows.

## Novidades da versão 1.100.0

Esta versão consolida em uma única entrega o roadmap planejado para `1.082.0`, `1.090.0` e `1.100.0`.

- Perfis reais de dispositivos Kindle, Kobo e reMarkable inspirados no Kindle Comic Converter.
- Ordem de leitura **Ocidental** ou **Mangá**.
- Ordenação natural de arquivos, evitando `1, 10, 2`.
- Remoção automática de margens.
- Remoção opcional de rodapé/número de página.
- Divisão de páginas duplas, com ordem respeitando o modo de leitura.
- Presets de imagem para E-ink.
- Prévia antes/depois antes da conversão final.
- Editor simples de metadados para EPUB.
- CBZ/ZIP nativos; CBR/RAR/7Z por 7-Zip instalado no Windows.



## Novidades da versão 1.100.3

- A aba **Limpar** agora aplica de verdade as funções KCC/E-ink ao arquivo limpo.
- **Dividir páginas duplas** divide páginas muito largas em duas páginas reais no PDF final limpo.
- **Manter original ao dividir** mantém a página inteira e também adiciona as duas metades quando ativado.
- **Webtoon/imagens longas**, **remover margens**, **remover rodapé/número de página** e **presets E-ink** ficam na aba Limpar, porque modificam o conteúdo.
- A aba **Converter** continua em modo de conversão pura: ela não relimpa, não corta, não divide e não cria canvas branco novamente.
- O botão **Prévia** do Converter foi unificado; não há mais dois botões de prévia competindo na mesma aba.
- A prévia da aba Limpar mostra o antes/depois das alterações visuais antes de processar o arquivo inteiro.

## Recursos principais

- Limpeza de páginas vazias ou pouco úteis em PDFs.
- Exportação em PDF, CBZ, PDF + CBZ e imagens.
- Conversão PDF → EPUB baseado em imagens.
- Conversão PDF → XTCH.
- Conversão EPUB → XTCH.
- Conversão EPUB → PDF para EPUBs baseados em imagens.
- Conversão PDF → CBZ e PDF → imagens.
- Conversão CBZ/ZIP/CBR/RAR/7Z → EPUB, XTCH ou PDF.
- Conversão imagem → PDF, EPUB ou XTCH.
- Criação de PDF a partir de imagens.
- Temas visuais, incluindo temas CUMA baseados no ícone.
- Configurações preservadas em `%APPDATA%\CUMA\cuma_settings.json`.
- Sistema de atualização por manifesto JSON no GitHub.

## Download

A versão compilada para Windows deve ser publicada em **GitHub Releases**:

`https://github.com/soldieg/CUMA/releases`

Baixe o arquivo `CUMA_windows.zip`, extraia a pasta e abra `cuma.exe`.

## Instalação para usuário final

1. Baixe `CUMA_windows.zip` em Releases.
2. Extraia o ZIP inteiro.
3. Abra `cuma.exe`.
4. Não apague a pasta `_internal`.

Não é necessário instalar Python para usar a versão compilada.

## Configurações do usuário

As configurações, logs e estado do usuário ficam fora da pasta do programa:

```text
%APPDATA%\CUMA\
  cuma_settings.json
  CUMA.log
  erro.txt
```

Isso permite atualizar o programa sem perder preferências.

## Desenvolvimento

Para rodar pelo Python:

```bash
pip install -r requirements.txt
python cuma.py
```

Para compilar no Windows:

```bat
criar_exe_windows_e_zip.bat
```

## Atualizações

O aplicativo consulta o manifesto:

```text
https://raw.githubusercontent.com/soldieg/CUMA/main/updates/stable.json
```



## Atualizações via GitHub Releases

O CUMA consulta:

```text
https://raw.githubusercontent.com/soldieg/CUMA/main/updates/stable.json
```

Para publicar uma nova versão:

1. Compile o programa no Windows e gere `CUMA_windows.zip`.
2. Crie uma Release com tag no formato `Stable` no seu fluxo atual, ou tags versionadas como `v1.100.0` se preferir histórico por versão.
3. Anexe exatamente o arquivo `CUMA_windows.zip`.
4. Publique a Release.

O workflow `.github/workflows/atualizar_stable_json.yml` baixa o ZIP da Release, calcula SHA256 e tamanho automaticamente, atualiza `updates/stable.json` e faz commit no `main`.

Caso prefira fazer manualmente/localmente:

```bat
python scripts\preparar_manifesto_release.py soldieg CUMA 1.100.1 C:\caminho\para\CUMA_windows.zip Stable
```


## Roadmap consolidado na versão 1.100.0

As etapas planejadas foram consolidadas nesta entrega:

- `1.082.0` — Perfis e leitura.
- `1.090.0` — Otimização E-ink.
- `1.100.0` — Experiência avançada.

O próximo ciclo recomendado é estabilização, testes com arquivos reais e refinamento dos algoritmos de corte/divisão.

## Fontes, referências e componentes utilizados

Esta seção lista as fontes de código, bibliotecas, repositórios, serviços e especificações técnicas identificados no projeto. Não se trata de fontes tipográficas.

### Código-fonte e distribuição do CUMA

- **Repositório do CUMA:** `https://github.com/soldieg/CUMA`
- **GitHub Releases do CUMA:** `https://github.com/soldieg/CUMA/releases`
- **Manifesto de atualização estável:** `https://raw.githubusercontent.com/soldieg/CUMA/main/updates/stable.json`
- **Arquivo de atualização distribuído:** `https://github.com/soldieg/CUMA/releases/download/Stable/CUMA_windows.zip`

### Referência XTCH/XTH/XTEINK

- **xtcjs / referência relacionada ao formato XTC/XTCH:** `https://github.com/varo6/xtcjs`

O código do CUMA mantém uma referência explícita a esse repositório em `XTCJS_REPO_URL`. As rotinas atuais do CUMA geram XTCH/XTH nativamente em Python, sem executar Node, npm, Bun ou workers externos, mas essa referência deve ser mantida nos créditos por estar relacionada à implementação/entendimento do formato.


### Referência técnica de otimização para e-readers

- **Kindle Comic Converter / KCC:** `https://github.com/ciromattia/kcc`
- **Licença:** ISC License
- **Uso no CUMA:** referência técnica para perfis de dispositivos, otimização de mangás/quadrinhos e possíveis algoritmos futuros de corte, página dupla e processamento de imagem.

### Bibliotecas Python usadas pelo aplicativo

- **Python / CPython:** `https://github.com/python/cpython`
- **PyMuPDF:** `https://github.com/pymupdf/PyMuPDF`
- **MuPDF, motor base usado pelo PyMuPDF:** `https://github.com/ArtifexSoftware/mupdf`
- **Pillow / PIL:** `https://github.com/python-pillow/Pillow`
- **NumPy:** `https://github.com/numpy/numpy`
- **tkinterdnd2, drag-and-drop opcional:** `https://github.com/pmgagne/tkinterdnd2`
- **PyInstaller, empacotamento do executável Windows:** `https://github.com/pyinstaller/pyinstaller`
- **OpenCV, usado apenas se disponível para detecção CUDA/OpenCL:** `https://github.com/opencv/opencv`

### Bibliotecas padrão do Python usadas no código

O CUMA também usa módulos da biblioteca padrão do Python, incluindo:

- `html`
- `json`
- `os`
- `queue`
- `re`
- `shutil`
- `subprocess`
- `sys`
- `threading`
- `traceback`
- `time`
- `collections`
- `concurrent.futures`
- `uuid`
- `hashlib`
- `struct`
- `zipfile`
- `colorsys`
- `dataclasses`
- `datetime`
- `io`
- `pathlib`
- `typing`
- `ctypes`
- `winreg`
- `urllib.request`
- `locale`
- `webbrowser`

Esses módulos fazem parte do Python/CPython e não precisam ser instalados separadamente.

### Interface gráfica

- **Tkinter:** biblioteca gráfica incluída com Python em builds comuns do Windows.
- **Tcl/Tk:** `https://www.tcl.tk/`
- **Tk/Ttk:** usado para widgets, abas, botões, comboboxes, treeviews, barras de rolagem e temas.

### Serviços externos usados pelo projeto

- **GitHub:** `https://github.com/`
- **GitHub Releases:** usado para hospedar `CUMA_windows.zip`.
- **GitHub raw content:** usado para servir `updates/stable.json`.
- **GitHub Actions:** usado pelo workflow `.github/workflows/atualizar_stable_json.yml`.
- **actions/checkout:** `https://github.com/actions/checkout`
- **GitHub CLI / gh:** `https://github.com/cli/cli`
- **Buy Me a Coffee:** `https://www.buymeacoffee.com/soldieg`
- **Buy Me a Coffee button API:** `https://img.buymeacoffee.com/button-api/`

### Especificações e formatos usados

- **PDF:** manipulado via PyMuPDF/MuPDF.
- **EPUB:** pacote ZIP com estrutura OPF/XHTML/imagens.
- **CBZ:** arquivo ZIP contendo imagens, usado por leitores de quadrinhos.
- **ZIP:** usado por EPUB, CBZ e pacotes de atualização.
- **XHTML:** `http://www.w3.org/1999/xhtml`
- **OPF / IDPF:** `http://www.idpf.org/2007/opf`
- **OPS / IDPF:** `http://www.idpf.org/2007/ops`
- **Dublin Core Metadata:** `http://purl.org/dc/elements/1.1/`
- **JPEG/JPG, PNG, WebP, BMP, TIFF:** formatos de imagem lidos/escritos via Pillow.
- **SHA-256:** usado para validar integridade do ZIP de atualização.
- **MD5:** usado internamente em páginas XTH/XTCH para digest curto de dados de página.

### Observação de créditos

Esta lista foi montada a partir das referências explícitas, imports, URLs, arquivos de build e formatos encontrados no projeto. Se alguma rotina tiver sido adaptada de fórum, gist, issue, conversa técnica ou repositório externo que não esteja registrado no código, o link original deve ser adicionado aqui antes do lançamento público.


## Conexões oficiais do GitHub configuradas para a versão 1.100.1

Esta versão está configurada para usar o repositório oficial:

```text
https://github.com/soldieg/CUMA
```

Endereços usados pelo aplicativo e pelos arquivos de release:

```text
Repositório:       https://github.com/soldieg/CUMA
Releases:          https://github.com/soldieg/CUMA/releases
Manifesto stable:  https://raw.githubusercontent.com/soldieg/CUMA/main/updates/stable.json
ZIP Stable:        https://github.com/soldieg/CUMA/releases/download/Stable/CUMA_windows.zip
Workflow:          .github/workflows/atualizar_stable_json.yml
Arquivo do app:    CUMA_windows.zip
```

Para o botão **Procurar atualizações** funcionar, o arquivo abaixo precisa existir no repositório, na branch `main`:

```text
updates/stable.json
```

A Release usada pelo fluxo atual é a tag:

```text
Stable
```

O ZIP anexado nessa Release deve se chamar exatamente:

```text
CUMA_windows.zip
```


## Alterações acrescentadas na versão 1.100.1

- Reorganização da UI: funções que modificam imagem/conteúdo foram movidas para **Limpar**.
- O Converter mantém os perfis de dispositivo, a prévia antes/depois e os metadados EPUB.
- As opções de conversão agora são liberadas por tipo de arquivo selecionado.
- Novas rotas de conversão: PDF→CBZ, PDF→imagens, EPUB→PDF, compactados→PDF e imagem→PDF/EPUB/XTCH.
- Mantida a base de atualização via `https://github.com/soldieg/CUMA` e Release `Stable`.

## Alterações acrescentadas na versão 1.100.0

A versão `1.100.0` consolida as etapas planejadas `1.082.0`, `1.090.0` e `1.100.0` em uma única entrega:

- Perfis reais de dispositivos Kindle, Kobo e reMarkable.
- Ordem de leitura **Ocidental** e **Mangá**.
- Ordenação natural de arquivos.
- Remoção automática de margens.
- Remoção opcional de rodapé/número de página.
- Divisão de páginas duplas.
- Presets E-ink.
- Prévia antes/depois.
- Editor simples de metadados para EPUB.
- Conversão CBZ/ZIP nativa.
- Suporte a CBR/RAR/7Z por 7-Zip instalado no Windows.
- Correção das URLs oficiais de atualização para `soldieg/CUMA`.
- Migração automática de configurações antigas de atualização que ainda apontem para URLs antigas.

## Fontes e referências acrescentadas neste update

Além das bibliotecas já listadas, a versão `1.100.0` registra como referências principais:

- **Kindle Comic Converter / KCC:** `https://github.com/ciromattia/kcc`
- **Licença do KCC:** ISC License
- **Uso no CUMA:** referência técnica para perfis de dispositivos, leitura de mangá/quadrinhos, otimização para e-readers, corte de páginas, páginas duplas e processamento de imagens.
- **xtcjs:** `https://github.com/varo6/xtcjs`
- **Uso no CUMA:** referência relacionada ao entendimento do formato XTC/XTCH/XTH.
- **7-Zip:** `https://www.7-zip.org/`
- **Uso no CUMA:** ferramenta externa opcional para abrir CBR/RAR/7Z no Windows.
