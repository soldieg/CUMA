# Correção de remapeamento de capas e volumes — CUMA 1.100.36

## Problema reproduzido

O PDF original já possuía metadados CUMA com as páginas de início/capa de cada
volume. Durante a limpeza, algumas páginas anteriores às capas eram divididas
em duas. O total final de páginas era atualizado, mas os campos `start_page`,
`cover_page` e `end_page` continuavam usando a numeração do arquivo original.

Exemplo informado:

- capa do Volume 3 no original: página 410;
- nove páginas anteriores geraram uma página adicional cada;
- posição correta no arquivo limpo: página 419;
- comportamento anterior: o metadado continuava apontando para 410.

A validação antiga apenas limitava números ao novo total de páginas. Ela não
mantinha a relação entre cada página original e a página correspondente no
arquivo final.

## Correção implementada

A limpeza agora trabalha com um mapa de linhagem de páginas:

1. A etapa básica registra, para cada página original mantida, sua posição no
   PDF limpo.
2. A etapa visual registra quantas páginas cada página de entrada produziu.
   Uma página comum produz um intervalo de uma página; uma página dupla pode
   produzir duas; um webtoon pode produzir mais.
3. Os dois mapas são compostos em:
   `página original -> intervalo de páginas no arquivo final`.
4. Os metadados existentes são remapeados usando esse mapa, sem tentar
   redetectar visualmente os volumes.
5. `start_page`, `cover_page`, `end_page`, capa global, capítulos, bookmarks e
   o JSON CUMA embutido são regravados com a numeração final.

Assim, se nove páginas anteriores à página 410 acrescentarem uma página cada,
o mapa aponta diretamente `410 -> 419`.

## Proteção das capas existentes

As páginas já cadastradas como `start_page`, `cover_page` ou capa global passam
a ser âncoras estruturais. Quando estão dentro do intervalo escolhido para
limpeza, não são removidas por baixa densidade, mesmo que sejam capas quase
brancas.

Isso evita que o programa tente remapear uma capa que foi descartada durante a
própria limpeza.

## Regras de intervalo

- O fim de cada volume é recalculado como a página anterior ao início do próximo.
- O último volume termina na última página do arquivo final.
- Se um intervalo personalizado excluir completamente um volume, esse volume
  não é criado artificialmente na saída.
- Se uma página de capítulo/bookmark for removida, o marcador usa a próxima
  página preservada dentro do mapa; na ausência dela, usa a anterior.
- A saída PDF usa o mapa posterior às divisões visuais.
- A saída CBZ paralela usa o mapa da limpeza básica, pois o pipeline atual gera
  esse CBZ antes da etapa visual aplicada ao PDF.

## Teste de regressão adicionado

Foi criado um PDF sintético de 12 páginas com três volumes:

- inícios originais: 1, 5 e 10;
- páginas duplas: 2 e 7;
- a página 5 foi deixada vazia para validar a proteção da capa.

Resultado esperado e obtido:

| Campo | Antes | Depois |
|---|---:|---:|
| Total de páginas | 12 | 14 |
| Volume 1 | 1–4 | 1–5 |
| Volume 2 | 5–9 | 6–11 |
| Volume 3 | 10–12 | 12–14 |
| Capa do Volume 2 | 5 | 6 |
| Capa do Volume 3 | 10 | 12 |

O TOC final foi relido como:

```text
Volume 1 -> 1
Volume 2 -> 6
Volume 3 -> 12
```

A capa vazia do Volume 2 foi preservada.

## Validações executadas

- Auditoria estrutural com `--version 1.100.36`: aprovada.
- Compilação de todos os arquivos Python: aprovada.
- Dez testes de regressão: aprovados.
- Teste ponta a ponta de remapeamento de volumes: aprovado.
- Smoke test da interface sob Xvfb: aprovado.
- Versão exibida pela interface: `1.100.36`.

## Limitações

Não foram gerados executáveis PyInstaller de Windows, Linux ou macOS nesta
sessão. A correção foi validada no código-fonte e em PDFs sintéticos. Metadados
que já apontavam para a página errada no arquivo original continuarão
representando a âncora errada; o remapeamento preserva a identidade informada,
não tenta adivinhar outra capa.
