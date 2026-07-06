# Auditoria e debug completo — CUMA 1.100.35

## Escopo

Arquivo analisado: `CUMA_1.100.35.zip`

SHA-256 do arquivo original:

`05869871BE1D9FB1B23CF6D568F2496E15B04DC0A4F6DBD7FC831E23324DAB45`

A análise foi feita de forma estática e dinâmica controlada. Binários desconhecidos não foram executados. O código Python foi importado em diretórios temporários, a interface foi aberta sob Xvfb e as funções de PDF, ZIP, metadados, atualização e geração de manifesto foram testadas com arquivos sintéticos.

## Visão geral do pacote original

- 39 entradas no ZIP.
- Aproximadamente 2,6 MB descompactados.
- Núcleo principal: `cuma.py`, com 29,307 linhas e cerca de 1,4 MB.
- Atualizador externo: `cuma_updater.py`, com 1,085 linhas.
- Scripts de compilação para Windows, Linux e macOS.
- Specs do PyInstaller, manifesto de atualização, configurações e documentação.
- Nenhum path traversal, link simbólico malicioso ou entrada criptografada foi encontrado no ZIP original.
- Todos os arquivos Python e specs compilavam sintaticamente.

## Defeitos críticos reproduzidos

### 1. A limpeza padrão rasterizava PDFs comuns

**Gravidade: alta — perda de qualidade e de dados pesquisáveis**

A opção `split_double_pages` vinha ativada por padrão. O pós-processamento considerava essa opção suficiente para rasterizar todas as páginas, inclusive páginas retrato normais que não eram duplas.

Reprodução no original:

- PDF vetorial antes: texto extraível `TEXTO PESQUISAVEL CUMA`.
- Depois da limpeza padrão: nenhum texto extraível.
- O arquivo simples aumentou de aproximadamente 898 bytes para mais de 20 KB.
- Vetores, acessibilidade, busca e possibilidade de copiar texto eram perdidos.

Correção aplicada:

- A opção de página dupla só transforma páginas cuja proporção realmente indica uma página larga.
- Páginas normais são copiadas com o mecanismo PDF, preservando texto, vetores, links e qualidade.
- Se nenhuma página precisar de transformação, o PDF não é regravado.
- Bookmarks são remapeados quando uma página larga gera duas páginas.

### 2. Salvar metadados apagava capítulos e bookmarks existentes

**Gravidade: alta — perda de estrutura editorial**

A função `_cuma_11013_write_pdf_metadata()` executava `doc.set_toc()` com apenas os volumes do CUMA. Isso substituía integralmente o sumário existente.

Reprodução no original:

Antes:

- Volume 1
  - Capítulo 1
  - Capítulo 2
- Apêndice

Depois:

- Volume 1

Correção aplicada:

- Um sumário existente nunca é substituído.
- Marcadores de volume só são criados quando o PDF ainda não possui sumário.
- Keywords existentes são preservadas e combinadas com as tags do CUMA.
- A gravação passou de `saveIncr()` para arquivo temporário adjacente seguido de `os.replace()`, reduzindo risco de corrupção por interrupção.
- Permissões do arquivo são preservadas.

### 3. `Result.final_size` ficava incorreto

**Gravidade: média**

O tamanho final era calculado antes da incorporação de metadados. O objeto retornado podia informar um tamanho diferente do arquivo realmente salvo.

Correção aplicada:

- `final_size` e `saved_bytes` são recalculados após a etapa de metadados.

## Outros problemas corrigidos

### Regravação ZIP/EPUB/CBZ

Problemas encontrados:

- Entradas duplicadas eram lidas por nome, o que podia copiar o conteúdo da última entrada para todas as ocorrências.
- Cada entrada era carregada integralmente na memória.
- Não havia preservação explícita do comentário do ZIP.

Correções:

- Leitura por objeto `ZipInfo`, preservando a identidade de entradas duplicadas.
- Cópia por streaming em blocos.
- Troca atômica do arquivo.
- Preservação do comentário.
- `mimetype` de EPUB continua sem compressão e pode ser mantido como primeira entrada.

### Armazenamento e logs

Problemas encontrados:

- Importar `cuma.py` podia criar configurações em:
  - diretório atual;
  - pasta do código/aplicativo;
  - pasta de dados do usuário.
- O log inicial podia ser escrito ao lado do executável/script.
- Isso gerava estados divergentes e falhas silenciosas em instalações somente leitura.

Correções:

- Uma única pasta de dados por usuário é usada também em modo fonte.
- `CUMA_USER_DATA_DIR` continua funcionando para portabilidade e testes.
- Configuração e log geral ficam na pasta de dados do usuário.
- As várias funções históricas de sincronização foram redirecionadas ao arquivo consolidado.
- O snapshot de diagnóstico agora mostra o arquivo de configuração realmente ativo.

### Atualizador externo

Problemas encontrados:

- Uma solicitação JSON feita manualmente podia omitir SHA-256 e ainda instalar.
- O nome padrão do executável era `cuma.exe` até em Linux/macOS quando o atualizador era chamado diretamente.
- O caminho do log persistente podia ser controlado pela solicitação.
- Não havia limites de número de membros, tamanho descompactado, tamanho individual ou download.
- O download parcial podia permanecer após falha.
- Schema e campos da solicitação não eram validados de forma suficiente.

Correções:

- Schema `CUMA_UPDATE_REQUEST` obrigatório.
- SHA-256 válido e tamanho positivo obrigatórios.
- Nome do executável precisa ser apenas um basename seguro.
- Pacote precisa estar na pasta temporária da solicitação.
- Pasta de instalação precisa existir e não pode ser a raiz do sistema.
- Log persistente é derivado da instalação, não do JSON.
- Limites defensivos:
  - até 100.000 membros;
  - até 8 GiB descompactados no total;
  - até 4 GiB por membro;
  - até 4 GiB de download.
- ZIP/TAR rejeitam traversal, links e tipos especiais.
- Downloads parciais são removidos em erro.
- O padrão do executável agora é específico da plataforma.
- Erros de solicitação são capturados e retornam código 1 de forma controlada.

### Manifesto e pipeline de release

Problemas encontrados:

- `updates/stable.json` original contém SHA placeholders e `size_bytes: 0`; portanto, a atualização automática fica corretamente bloqueada pelo próprio aplicativo.
- Cada plataforma gerava seu manifesto em um job isolado. Os três hashes nunca eram combinados.
- O manifesto alterado não era publicado na branch `main`.
- Os pacotes não eram enviados automaticamente a uma GitHub Release.
- A versão `1.100.35` estava repetida no workflow.
- Um caminho de pacote inexistente com extensão `.zip`/`.tar.gz` era aceito e gerava placeholder com sucesso.

Correções:

- Caminho de pacote inexistente agora encerra o script com erro.
- Escrita de JSON é atômica.
- O workflow:
  - extrai a versão do código;
  - compara a versão com a tag;
  - compila e audita as fontes;
  - cria os três pacotes em runners próprios;
  - baixa os três artefatos em um job agregador;
  - gera um único `stable.json`;
  - valida SHA-256 e tamanho de todas as plataformas;
  - cria/atualiza a GitHub Release;
  - envia os três pacotes;
  - atualiza `updates/stable.json` e `cuma_settings_template.json` na branch `main`.
- Em execução manual, o canal usa a tag lógica `Stable`; em push de tag, usa a tag real.

## Riscos estruturais ainda existentes

Esses pontos não foram refatorados porque exigem mudança arquitetural ampla e revisão funcional de longo prazo:

- `cuma.py` possui 29,307 linhas.
- Há 943 definições de topo e 41 nomes redefinidos no mesmo módulo.
- `ensure_manual` é redefinida 12 vezes.
- Foram encontrados 1,453 blocos `except Exception`; 782 deles são apenas `pass`.
- O comportamento depende de muitas camadas históricas que monkey-patcham classes e funções em ordem de importação.
- Os scripts de build usam intervalos de dependência, sem lockfile/hashes.
- Actions do GitHub usam tags de versão (`@v4`, `@v5`) em vez de commits imutáveis.
- O caminho CBR/RAR/7Z depende do executável externo 7-Zip. A validação do atualizador ZIP/TAR foi reforçada, mas a extração de quadrinhos por 7-Zip ainda merece uma sandbox específica e limites pré-extração.
- O encerramento forçado por PID no atualizador não confirma a identidade do processo; existe um risco raro de reutilização de PID.
- Branch protection no GitHub pode impedir o passo que publica `stable.json`; nesse caso, será necessário permitir o bot ou usar uma pull request automatizada.

## Testes executados na versão corrigida

| Teste | Resultado |
|---|---|
| Compilação sintática de todos os `.py` e `.spec` | OK |
| Auditoria de integridade fornecida pelo projeto | OK |
| `bash -n` nos scripts Linux/macOS | OK |
| Modo `--check` nos scripts Linux/macOS | OK |
| Parse estrutural do workflow YAML | OK |
| Importação isolada sem criar `.cuma_user_data` no projeto/CWD | OK |
| Smoke test da interface com Xvfb | OK — janela `CUMA`, classe `App` |
| PDF retrato vetorial com página dupla padrão | OK — hash e texto preservados |
| PDF paisagem realmente duplo | OK — dividido em duas páginas |
| Metadados PDF com capítulos existentes | OK — TOC preservado |
| Keywords PDF existentes | OK — preservadas |
| Tamanho do `Result` após metadados | OK |
| ZIP com nomes duplicados | OK — conteúdos distintos preservados |
| ZIP traversal no atualizador | Bloqueado |
| ZIP com tamanho descompactado acima do limite | Bloqueado |
| Caminho de pacote inexistente no gerador de manifesto | Bloqueado com exit code 2 |
| Agregação de Windows/Linux/macOS | OK — três SHA-256 válidos e tamanhos positivos |

A suíte adicionada contém 8 testes automatizados em `scripts/testes_regressao_debug.py`.

## Limitações da validação

- Não foi feito um build PyInstaller real neste ambiente.
- Não foi possível executar binários Windows ou macOS.
- O workflow do GitHub Actions não foi disparado de verdade; foi validado estruturalmente e seus scripts foram exercitados localmente com pacotes sintéticos.
- Não havia 7-Zip instalado, portanto CBR/RAR/7Z não foi testado dinamicamente.
- O erro `artifact_tool ... hydrateCrdtFromProto` visto no stderr durante alguns testes pertence ao ambiente de execução desta análise e não ao CUMA; os processos testados retornaram sucesso quando aplicável.

## Arquivos entregues

- `CUMA_1.100.35_debugado.zip`: cópia corrigida, sem `__pycache__`.
- `AUDITORIA_DEBUG_CUMA_1.100.35.md`: este relatório.
- `PATCH_DEBUG_CUMA_1.100.35.diff`: diff unificado das mudanças.
- `scripts/testes_regressao_debug.py`: testes automatizados.
