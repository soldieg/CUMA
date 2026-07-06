# Publicação automática do CUMA

A pasta `release/inbox` é a entrada do pipeline. Cada envio deve conter **uma única versão**.

## Estrutura recomendada

```text
release/inbox/1.100.38/
├── release.json
└── payload/
    ├── cuma.py
    ├── cuma_updater.py
    └── qualquer outro arquivo alterado
```

O `payload/` é opcional. Sem payload, o pipeline publica o código que já está na raiz do repositório. Também é aceito um `payload.zip`, desde que ele contenha caminhos relativos à raiz do projeto.

Exemplo de `release.json`:

```json
{
  "version": "1.100.38",
  "summary": "Correções na limpeza e nos metadados.",
  "notes": [
    "Corrige o deslocamento das capas após divisões de página.",
    "Melhora a validação do atualizador."
  ],
  "mandatory": false,
  "minimum_supported_version": "1.080.0",
  "prerelease": false,
  "delete": []
}
```

Depois do commit na branch `main`, o workflow `.github/workflows/publicar_release.yml`:

1. valida o `release.json` e aplica o payload;
2. sincroniza a versão do código, configurações e scripts;
3. executa auditoria, testes de regressão e smoke test da interface;
4. compila Windows, Linux e macOS em runners próprios;
5. valida a estrutura dos três pacotes e calcula SHA-256;
6. cria a tag e a GitHub Release;
7. publica os pacotes, `SHA256SUMS.txt` e o manifesto;
8. atualiza `updates/stable.json` na branch `main`;
9. registra o histórico em `release/history/<versão>/`;
10. remove a pasta processada do `release/inbox`.


## Primeira publicação desta entrega

Para publicar a versão `1.100.37`, copie:

```text
release/template/release-1.100.37.json
```

para:

```text
release/inbox/1.100.37/release.json
```

e envie esse diretório para `main`. O código dessa versão já está na raiz, então não é necessário incluir `payload/`.

## Regras

- Envie uma versão por vez.
- O número da pasta deve ser igual ao campo `version`.
- A versão precisa ser maior que a publicada em `updates/stable.json`.
- O payload não pode alterar `.github/workflows`, `.git`, `release/` nem `updates/stable.json`.
- O pipeline não publica se qualquer teste ou build falhar.
- Para repetir um fluxo interrompido, use **Actions → Publicar CUMA automaticamente → Run workflow** e informe a pasta ainda existente no inbox.

## Configuração necessária no GitHub

Em **Settings → Actions → General → Workflow permissions**, habilite **Read and write permissions**. Branch protection precisa permitir que `github-actions[bot]` grave os commits de preparação e de manifesto na branch `main`.
