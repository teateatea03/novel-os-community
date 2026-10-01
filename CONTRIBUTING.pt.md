# Contribuir para o Novel OS

<!-- language-navigation --> [繁體中文](CONTRIBUTING.zh-TW.md) | [English](CONTRIBUTING.md) | [日本語](CONTRIBUTING.ja.md) | [한국어](CONTRIBUTING.ko.md) | [Español](CONTRIBUTING.es.md) | [Français](CONTRIBUTING.fr.md) | [Deutsch](CONTRIBUTING.de.md) | **Português**

[Modelo de pedido de alterações](.github/PULL_REQUEST_TEMPLATE/pt.md)

Obrigado por ajudar a melhorar o Novel OS. As contribuições devem preservar as condições comerciais de código-fonte disponível do projeto e o limite de privacidade.

## A privacidade e os direitos bloqueiam a publicação

Contribua apenas com material reutilizável do sistema que tenha o direito de partilhar. **Não** envie:

- manuscritos, rascunhos de capítulos, sessões interativas, estado narrativo, comentários do autor ou dados de teste de projetos privados;
- bases de dados de personagens, mundos ou investigação, ou registos sobre pessoas reais;
- memórias de chat, logs locais, cópias de segurança geradas, credenciais, cookies, caminhos de dispositivos ou endpoints privados;
- texto-fonte protegido por direitos de autor, material divulgado ilicitamente, cópias de conteúdos pagos ou código de terceiros sem licenciamento compatível e atribuição.

Utilize dados de teste fictícios, mínimos e claramente sintéticos. Não se limite a mudar os nomes de dados privados reais.

Construa pacotes e crie projetos narrativos fora da cópia de fontes. É permitido um ambiente virtual na raiz para desenvolvimento local, mas não deve ser incluído nos commits.

## Antes de abrir um pedido de alterações

```sh
python3 scripts/privacy_scan.py .
python3 -m compileall -q skills scripts
python3 scripts/validate_json.py .
python3 scripts/run_tests.py
```

O analisador e o validador JSON verificam os ficheiros da árvore de trabalho, incluindo os não rastreados e os ignorados pelo Git. Excluem metadados do Git, caches geradas de Python/testes e ambientes virtuais confirmados na raiz; os ficheiros rastreados continuam abrangidos. Rejeitam ligações simbólicas, ficheiros ilegíveis e fontes que não sejam UTF-8. Reveja separadamente as diferenças preparadas: uma aprovação da árvore de trabalho não é uma análise do índice preparado, do histórico Git ou dos objetos retidos pelo GitHub.

Inspecione também:

```sh
git diff --cached --name-only
git diff --cached
```

Explique no pedido de alterações qualquer nova dependência, fonte externa, artefacto gerado ou comportamento específico da plataforma.

## Expectativas das alterações

- Mantenha o código e a documentação portáveis; as predefinições de plataforma devem poder ser substituídas
- Adicione ou atualize testes para alterações de comportamento
- Preserve a autoridade do cânone e do autor e os contratos de segurança que rejeitam em caso de incerteza
- Mantenha os exemplos públicos sintéticos e sem informações de identificação pessoal
- Não enfraqueça silenciosamente os controlos de privacidade, proveniência ou validação

## Modelo de commits e revisão

Utilize commits focados com um resumo no imperativo. Os pedidos de alterações exigem revisão do responsável. As correções de segurança ou privacidade devem usar comunicação privada em vez de uma issue pública.

## Licenciamento

Contribua apenas com material que tenha o direito de distribuir sob [LICENSE](LICENSE.pt.md). Identifique modificações, mantenha a mesma licença para alterações derivadas do projeto e preserve todos os avisos de terceiros exigidos. Isto não transfere os seus direitos de autor para o responsável. Os pedidos de alterações públicos não devem incluir relatórios financeiros, dados de pagamento ou material criativo privado.
