# Correção dos BATs do CUMA 1.100.37

## Erro recebido

A compilação chegava à auditoria e parava com:

```text
[ERRO] Artefatos gerados dentro do repositório:
.venv/.../__pycache__/*.pyc
__pycache__/cuma.cpython-314.pyc
scripts/__pycache__/*.pyc
```

O problema não era o PyInstaller nem as dependências. O próprio BAT criava a
`.venv` e executava `py_compile`; logo depois, a auditoria percorria a árvore
inteira e tratava os bytecodes recém-criados como se fossem arquivos indevidos
do projeto. Assim, o processo produzia os arquivos e em seguida se bloqueava.

## Causas confirmadas

1. `compilacao/Windows/criar_windows.bat` instalava as dependências antes da
   auditoria e chamava `py_compile`, criando `__pycache__`.
2. `scripts/auditoria_integridade.py` não ignorava `.venv`, `build`, `dist`,
   `ZIP final` nem caches Python na verificação de artefatos.
3. Uma segunda compilação também poderia falhar ao encontrar o ZIP produzido
   pela compilação anterior.
4. O launcher verificava `cuma.py` e `requirements.txt` antes de tentar abrir
   um EXE já compilado.
5. Os wrappers não propagavam explicitamente o código de saída.
6. Nomes antigos de launchers, usados nas versões anteriores, não existiam na
   estrutura automatizada.
7. A compactação interpolava caminhos diretamente em uma expressão
   PowerShell, o que era frágil para caminhos especiais.
8. Não havia um teste dedicado para a sintaxe, os labels, os wrappers e os
   recursos obrigatórios dos BATs.

## Correções aplicadas

### `compilacao/Windows/criar_windows.bat`

- auditoria executada sem `py_compile`;
- `PYTHONDONTWRITEBYTECODE=1`;
- `.venv` reutilizada e validada;
- descoberta de Python 3.10 a 3.14 por caminhos comuns, launcher `py`,
  `python` e `python3`;
- opções `--check`, `--clean`, `--diagnostico` e `--help`;
- limpeza segura de `build`, `dist`, ZIP anterior e caches do projeto;
- log do PyInstaller em `CUMA_build_windows.log`;
- validação dos imports essenciais;
- compactação via variáveis de ambiente do PowerShell, segura para caminhos
  com espaços e apóstrofos;
- validação do ZIP final com `release_pipeline.py verify-asset`;
- mensagens de erro por etapa;
- compatibilidade com `CI=true` sem pausa interativa.

### `compilacao/Windows/rodar_cuma.bat`

- modo automático abre o EXE quando ele existe e só usa o fonte quando
  necessário;
- modos `--fonte`, `--compilado`, `--check`, `--diagnostico` e `--help`;
- o modo compilado não exige `cuma.py`, `requirements.txt` ou Python;
- criação e validação da `.venv`;
- instalação das dependências somente quando faltam;
- auditoria antes de abrir o fonte;
- código de saída preservado;
- logs e instruções de recuperação.

### Wrappers

Foram revisados ou adicionados:

```text
rodar_cuma.bat
criar_exe_windows_e_zip.bat
compilacao/Windows/rodar_cuma_windows.bat
```

Todos usam `%~dp0`, funcionam fora do diretório atual e propagam o
`ERRORLEVEL` do launcher real.

### Auditoria

`scripts/auditoria_integridade.py` agora:

- ignora `.venv`, `venv`, `env`, `.git`, `build`, `dist`, `ZIP final` e
  `.release-runtime`;
- considera `__pycache__`, `.pyc` e `.pyo` produtos locais normais já cobertos
  pelo `.gitignore`;
- não despeja milhares de caminhos na tela;
- executa a auditoria dedicada dos BATs.

### GitHub Actions

O job Windows agora executa:

```text
python scripts\testar_bats_windows.py --execute-checks
```

antes da compilação. No runner `windows-latest`, isso chama os launchers reais
com `cmd.exe` e bloqueia a Release se algum wrapper ou `--check` falhar.

## Comandos para uso local

Executar:

```text
rodar_cuma.bat
rodar_cuma.bat --fonte
rodar_cuma.bat --compilado
rodar_cuma.bat --check
rodar_cuma.bat --diagnostico
```

Compilar:

```text
criar_exe_windows_e_zip.bat
criar_exe_windows_e_zip.bat --check
criar_exe_windows_e_zip.bat --clean
criar_exe_windows_e_zip.bat --diagnostico
```

## Validações realizadas

- reprodução da presença de `.venv`, `__pycache__`, `.pyc` e ZIP anterior;
- auditoria corrigida: 0 erros;
- 5 BATs analisados estaticamente;
- labels e destinos de `goto`/`call` verificados;
- parênteses e wrappers verificados;
- finais de linha CRLF e formato DOS confirmados;
- 10 testes de regressão do CUMA aprovados;
- YAML do workflow carregado sem erro;
- versões e JSONs validados;
- SHA e integridade do ZIP de entrega verificados.

## Limitação da validação local

O ambiente usado para a correção é Linux e não possui `cmd.exe`, PowerShell
Windows ou PyInstaller Windows. Por isso, não foi produzido um executável
Windows nesta sessão. A execução dinâmica dos BATs foi adicionada ao próprio
GitHub Actions em `windows-latest`; a primeira execução do workflow é a
validação final no sistema operacional real.
