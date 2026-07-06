# Auditoria integral e automação do repositório CUMA — 1.100.37

## 1. Material analisado

- Repositório recebido: `CUMA-main (1).zip`
- SHA-256 do ZIP recebido: `a7a2f11ee48ce3eca2adf2cf248c388203b91fddc18f45d9241fb590596d3c41`
- Versão encontrada no repositório: `1.100.30`
- Versão consolidada nesta entrega: `1.100.37`
- Arquivo principal: `cuma.py`
- Atualizador: `cuma_updater.py`
- Plataforma de publicação: `soldieg/CUMA`

A análise combinou leitura integral dos arquivos, AST, comparação entre definições, busca de referências, importação isolada, execução da interface sob Xvfb, inspeção dos comandos de widgets, testes de regressão, validação dos scripts de build e simulação local do pipeline completo de release.

A expressão “função sem uso” neste documento significa **sem referência estática direta e sem vínculo encontrado na interface executada**. Como o CUMA usa `globals()`, strings e monkey patches, essas funções não foram apagadas automaticamente sem uma suíte maior de equivalência.

## 2. Como o programa funciona atualmente

O CUMA não é uma classe única e linear. O comportamento final é montado em camadas:

1. `cuma.py` define modelos de configuração, utilitários, processamento de PDF/arquivos, a interface base e o fluxo de tarefas.
2. Ao importar o módulo, **43 instaladores de patch** executam em sequência.
3. Cada instalador captura métodos anteriores, adiciona wrappers e substitui métodos de `App`, `BaseApp` ou `PDFCleaner`.
4. A interface final é, portanto, a combinação da implementação original com todas essas camadas.
5. A limpeza abre o documento, decide remoções/divisões, grava um mapa de página original → página final e, na camada mais recente, reaplica metadados, capas, volumes, capítulos e TOC usando esse mapa.
6. O atualizador lê `updates/stable.json`, seleciona o pacote da plataforma, valida tamanho/hash e substitui a instalação.
7. Os scripts PyInstaller geram uma pasta `onedir` para cada sistema e a compactam para publicação.

Essa arquitetura explica por que um trecho antigo aparentemente “morto” ainda pode estar ativo por uma variável `OLD` capturada em uma camada posterior.

## 3. Métricas confirmadas

| Métrica | Resultado |
|---|---:|
| Linhas em `cuma.py` | 29.867 |
| Tamanho de `cuma.py` | 1.446.857 bytes |
| Funções/métodos | 1.252 |
| Funções de nível de módulo | 946 |
| Classes | 10 |
| Instaladores executados na importação | 43 |
| Nomes de função de módulo redefinidos | 41 |
| Grupos de corpos exatamente duplicados | 29 |
| Funções dentro desses grupos | 70 |
| Blocos `except` | 1.490 |
| `except Exception`/`BaseException` ou equivalente amplo | 1.477 |
| Tratadores que contêm apenas `pass` | 793 |
| Comandos de interface verificados depois da correção | 99 |
| Comandos inválidos depois da correção | 0 |
| Testes de regressão aprovados | 10/10 |

## 4. Problemas comprovados

### 4.1 Colisão que quebrava os dois botões Play — corrigida

O objeto possuía simultaneamente:

```python
self.resume_processing = tk.BooleanVar(...)
```

e:

```python
def resume_processing(self):
    ...
```

O atributo de instância escondia o método. Os botões recebiam uma variável Tcl em vez de callback. A opção foi renomeada para:

```python
self.resume_processing_enabled
```

e os dois botões continuam chamando o método `resume_processing()`.

Antes: 2 comandos inválidos.  
Depois: 99 comandos examinados, 0 inválidos.

### 4.2 Deslocamento das capas após limpeza — corrigido

A limpeza alterava a contagem de páginas, mas os metadados de volume continuavam apontando para os índices originais. A nova camada registra o destino de cada página e remapeia:

- `start_page`;
- `end_page`;
- `cover_page`;
- capa global;
- capítulos;
- bookmarks/TOC;
- JSON CUMA embutido.

O caso relatado `410 → 419` faz parte dos testes automatizados e passa.

### 4.3 Rasterização indevida do PDF — corrigida

A opção padrão de divisão podia rasterizar páginas retrato comuns. Agora a divisão é aplicada apenas a páginas realmente largas; páginas vetoriais comuns mantêm texto pesquisável.

### 4.4 Perda de bookmarks e metadados — corrigida

A gravação dos metadados podia substituir capítulos e palavras-chave. O processo agora preserva TOC, keywords e permissões existentes e recalcula o tamanho final depois da etapa de metadados.

### 4.5 Regravação de ZIP/EPUB/CBZ — corrigida

A implementação anterior podia carregar arquivos completos em memória e confundir entradas de nomes duplicados. A regravação passou a usar streaming, saída atômica e a identidade de cada `ZipInfo`.

### 4.6 Extração insegura no atualizador — corrigida

O repositório recebido utilizava extração direta de ZIP/TAR. A versão consolidada rejeita:

- path traversal;
- caminhos absolutos;
- links simbólicos e tipos especiais;
- arquivos e downloads acima dos limites;
- archive bombs;
- manifesto incompleto;
- SHA-256 ausente ou divergente.

### 4.7 Publicação do GitHub incompleta — substituída

O repositório possuía dois workflows independentes:

- um criava apenas artifacts temporários;
- outro reagia a uma Release já criada e atualizava somente o pacote Windows.

Isso não garantia uma publicação transacional de três plataformas. Os workflows antigos foram substituídos por um pipeline único.

## 5. Redundâncias e resíduos removidos

Foram removidos do repositório preparado:

- ZIP antigo de compilação dentro do próprio repositório;
- caches `__pycache__` e arquivos `.pyc`;
- log e configurações pessoais versionados;
- workflow antigo de build e workflow Windows-only do manifesto;
- árvore duplicada `arquivos necessários/`;
- `cuma.spec` genérico, substituído pelos três specs de plataforma;
- scripts antigos duplicados na raiz;
- cópias duplicadas do logotipo;
- arquivos de teste e QR codes sem referência comprovada;
- diretório `assets/` que ficou sem uso depois da consolidação.

Arquivos modificados ou acrescentados são descritos no patch que acompanha a entrega.

## 6. Código ainda redundante, mas não removido à força

As seguintes rotinas têm zero referência direta no AST e não estavam ligadas aos controles da interface observada:

| Função/método | Linha |
|---|---:|
| `_base_main` | 2144 |
| `cuma_calculate_dynamic_version` | 3157 |
| `cuma_register_version_event` | 3175 |
| `_cuma_emit_merged_patch_report` | 4483 |
| `_cuma_emit_final_patch_report` | 5039 |
| `_cuma_11001_iter_source_images` | 14722 |
| `_cuma_11014_int` | 21555 |
| `BaseApp.build_preview_tab` | 1273 |
| `BaseApp.choose_xteink_converter` | 1648 |
| `BaseApp.choose_xteink_input` | 2072 |
| `App._bind_picker_events` | 2851 |
| `App.set_color_choice` | 3049 |

`CompactSwitch.instate` também não possui referência direta, mas pode fazer parte do contrato de widget e, por isso, não é candidato seguro à remoção automática.

Esses itens devem ser eliminados somente em uma branch de refatoração, depois de testes que cubram conversão, pausa/retomada, configurações, atualização e todos os formatos suportados.

## 7. Dívida técnica que permanece

### Monólito e patches

`cuma.py` ainda possui quase 30 mil linhas e 43 instalações de patch. A consolidação total exigiria reescrever cada cadeia final em uma implementação única e comparar os efeitos antes de apagar as versões históricas.

### Exceções ocultas

Há 1.477 capturas amplas e 793 tratadores que silenciam o erro. Isso reduz a capacidade de diagnosticar falhas reais. A prioridade deve ser substituir `except Exception: pass` por exceções específicas e logging contextual nas áreas de arquivo, PDF, atualização e persistência.

### Versionamento repetido

A versão ainda aparece no Python, JSON de configuração e scripts de build. O novo pipeline sincroniza esses locais automaticamente, mas a arquitetura ideal é importar uma única fonte gerada, sem correção em tempo de execução.

### Dependências não totalmente reproduzíveis

`requirements.txt` usa faixas de versões, não um lockfile com hashes. Builds realizados em datas diferentes podem resolver versões distintas. Recomenda-se um arquivo de lock separado para CI.

### Distribuição sem assinatura

O pipeline gera hashes, porém não assina executáveis e não realiza notarização do macOS. Isso exige certificados e segredos próprios do mantenedor.

## 8. Automação implantada para `soldieg/CUMA`

Novo workflow:

```text
.github/workflows/publicar_release.yml
```

Entrada:

```text
release/inbox/<versão>/
├── release.json
├── payload/       # opcional
└── payload.zip    # alternativa opcional ao payload/
```

O `release.json` é a fonte das notas:

```json
{
  "version": "1.100.38",
  "summary": "Resumo curto da versão.",
  "notes": [
    "Nova funcionalidade.",
    "Correção importante."
  ],
  "mandatory": false,
  "minimum_supported_version": "1.080.0",
  "prerelease": false,
  "delete": []
}
```

### Fluxo automático

1. O push de uma pasta em `release/inbox/**` inicia o workflow.
2. `scripts/release_pipeline.py prepare` valida a versão e o JSON.
3. O payload é aplicado com proteção contra traversal e alterações em áreas reservadas.
4. A versão é sincronizada no fonte, configurações e scripts de build.
5. Notas, changelog e histórico são gerados com o mesmo conteúdo.
6. A auditoria, compilação sintática, 10 testes e smoke test da interface precisam passar.
7. O código preparado é registrado na branch `main`.
8. Runners nativos compilam Windows, Linux e macOS.
9. Cada pacote é aberto e validado antes da publicação.
10. SHA-256 e tamanho são calculados para os três pacotes.
11. A tag e a GitHub Release são criadas como draft.
12. São anexados:
    - `CUMA_windows.zip`;
    - `CUMA_linux.tar.gz`;
    - `CUMA_macos.zip`;
    - `SHA256SUMS.txt`;
    - `stable.json`.
13. A Release deixa de ser draft apenas após todos os assets estarem presentes.
14. `updates/stable.json` é atualizado na `main`.
15. O histórico é gravado em `release/history/<versão>/`.
16. A pasta processada sai do inbox.
17. Instalações antigas passam a encontrar a versão pelo manifesto já usado pelo atualizador.

Se qualquer build ou teste falhar, o manifesto público não é promovido para a nova versão.

## 9. Como publicar a primeira versão automatizada

A entrega contém:

```text
release/template/release-1.100.37.json
```

Para publicar a versão consolidada:

```text
1. Criar release/inbox/1.100.37/
2. Copiar release/template/release-1.100.37.json para:
   release/inbox/1.100.37/release.json
3. Commitar e enviar para a branch main.
```

Como o código 1.100.37 já está na raiz, não é necessário payload nessa primeira publicação.

Para uma versão futura, por exemplo `1.100.38`, coloque somente os arquivos alterados em `payload/` ou use um `payload.zip`. O pipeline não exige editar manualmente specs, scripts, changelog, tag ou `stable.json`.

## 10. Configuração necessária no GitHub

No repositório:

```text
Settings → Actions → General → Workflow permissions
```

habilitar:

```text
Read and write permissions
```

A proteção da branch `main` deve permitir os dois commits do `github-actions[bot]`:

- preparação da fonte;
- publicação do manifesto e histórico.

Não é necessário token pessoal para o fluxo padrão; o workflow usa o token do próprio GitHub Actions. Assinatura de código, quando adotada, exigirá secrets específicos.

## 11. Recuperação de falhas

- Falha antes dos builds: corrija a pasta no inbox e faça novo push.
- Falha em um runner: use `Actions → Publicar CUMA automaticamente → Run workflow` e informe o diretório ainda existente.
- Release draft criada: a nova execução substitui assets com `--clobber`.
- O `stable.json` anterior permanece vigente até o fim da publicação.
- A versão só sai do inbox após manifesto, Release e histórico serem validados.

## 12. Validações executadas

Resultado local da entrega:

- auditoria estrutural: aprovada, com um aviso esperado para o manifesto ainda não publicado;
- sintaxe Python: aprovada;
- JSONs: aprovados;
- smoke test da interface: versão `1.100.37`, 99 comandos, 0 inválidos;
- testes de regressão: 10/10;
- caso de volume `410 → 419`: aprovado;
- PDF vetorial preservado: aprovado;
- página larga dividida: aprovado;
- bookmarks/keywords preservados: aprovado;
- ZIP duplicado preservado: aprovado;
- traversal e archive bomb bloqueados: aprovado;
- sintaxe dos scripts shell: aprovada;
- simulação local de `prepare → verify-asset → manifest → finalize`: aprovada com três pacotes sintéticos.

O `updates/stable.json` presente no fonte continua apontando para a versão publicada anterior. Isso é intencional: ele só deve mudar depois que a primeira execução real do workflow anexar os três pacotes.

## 13. Limitações desta auditoria

- O workflow não foi executado no GitHub real nesta sessão.
- Não foram produzidos executáveis PyInstaller reais.
- Windows e macOS não foram executados localmente.
- Não houve assinatura de código nem notarização.
- A remoção completa das 43 camadas de patch não foi feita, porque seria uma refatoração de alto risco e exige uma suíte funcional maior.
- Chamadas dinâmicas por string ou `globals()` podem escapar à análise estática.

## 14. Próxima refatoração segura

A sequência recomendada é:

1. ampliar testes para todos os botões, formatos, cancelamento e atualização;
2. separar `core`, `ui`, `services` e `models`;
3. consolidar um método final por vez;
4. remover a captura `OLD` correspondente;
5. comparar PDFs, metadados e arquivos produzidos;
6. remover as funções sem uso somente depois da equivalência;
7. criar lockfile e, posteriormente, assinatura dos binários.

A automação entregue resolve a publicação. Ela não transforma automaticamente o monólito em uma arquitetura modular; isso deve ser tratado como projeto separado para não arriscar o comportamento já validado.
