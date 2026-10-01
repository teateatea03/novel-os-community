# Novel OS

<!-- language-navigation -->

[繁體中文](../zh-TW/README.md) | [English](../../../README.md) | [日本語](../ja/README.md) | [한국어](../ko/README.md) | [Español](../es/README.md) | [Français](../fr/README.md) | [Deutsch](../de/README.md) | **Português**

O Novel OS é uma coleção reutilizável de habilidades para agentes de IA e ferramentas locais em Python para ficção longa, ficção interativa, continuidade, investigação de personagens e mundos, coerência comportamental, grafos com informação de proveniência e validação narrativa.

> **Licença:** código-fonte disponível sob a [licença de participação nos lucros comerciais do Novel OS](LICENSE.md), copyright teateatea03. A utilização não comercial é gratuita; a utilização comercial deve pagar 0.5% do lucro líquido positivo anual relacionado. Modificações e redistribuição mantêm as mesmas condições e avisos. Não é MIT, GPL nem uma licença de código aberto da OSI.

Para detalhes de utilização comercial e pagamento com dois tokens, consulte as [informações de participação nos lucros e pagamento](COMMERCIAL_TERMS.md). Os direitos sobre os romances e outros resultados dos utilizadores não são transferidos para o proprietário do sistema.

## Cobertura de idiomas

A documentação pública está disponível em chinês tradicional, inglês, japonês, coreano, espanhol, francês, alemão e português. As habilidades de execução, os modelos e as suas referências técnicas mantêm atualmente o idioma original. Esta versão da documentação em oito idiomas não traduz o ambiente de execução.

## Limite de privacidade

Este repositório de código-fonte exclui intencionalmente:

- manuscritos, rascunhos de capítulos, sessões de jogo interativo, estado narrativo e conjuntos de dados de comentários do autor;
- bases de dados de investigação sobre personagens, mundos, objetos especiais e pessoas reais;
- memórias de chat, estado local do dispositivo, cópias de segurança, exportações, credenciais, endpoints privados e ficheiros de ambiente.

Os exemplos públicos e os dados de teste devem ser sintéticos. Antes de cada envio ou publicação, execute o analisador de privacidade e reveja o manifesto dos ficheiros preparados.

## Estrutura do repositório

- `skills/`: pacotes de habilidades reutilizáveis, scripts, modelos e dados de teste sintéticos
- `scripts/`: utilitários de privacidade, validação e testes
- `docs/`: documentação de governação do projeto e limites de publicação

A árvore de fontes tem 18 diretórios de habilidades: 17 habilidades de execução instaláveis (um coordenador e 16 colaboradores), mais o exportador de pacotes. O exportador é uma ferramenta de empacotamento e não é instalado como habilidade de execução.

## Requisitos

- Python 3.10+
- Armazenamento persistente UTF-8
- Funcionalidades principais apenas com a biblioteca padrão
- Funcionalidades opcionais: consulte `requirements-optional.txt` e `THIRD_PARTY.pt.md`

Instale as dependências opcionais de Python num ambiente isolado:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

A integração com Graphify é opcional e instalada separadamente conforme a documentação original.

## Primeira execução local (sem modelo nem rede)

A partir da raiz do repositório, utilize Python 3.10+ e Git. As verificações principais e a demonstração sintética não precisam de pacotes opcionais, chaves de API nem manuscritos privados:

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 scripts/run_tests.py

# Mantenha o estado de projeto gerado fora do repositório de fontes.
DEMO_ROOT="$(mktemp -d)"
python3 skills/long-form-novel-writer/scripts/init_novel_project.py \
  --title "Synthetic Demo" --slug synthetic-demo --root "$DEMO_ROOT"
python3 skills/knowledge-relationship-graph/scripts/relationship_graph.py \
  validate --root "$DEMO_ROOT/synthetic-demo"
```

O inicializador cria uma estrutura vazia de planeamento e estado; não gera um romance nem chama um modelo. Mantenha as suas histórias num diretório privado separado. O inicializador recusa sobrescrever um projeto existente.

Para um anfitrião de agentes, mantenha as habilidades de execução como diretórios irmãos e registe `novel-operating-system` como ponto de entrada. Anfitriões sem ficheiros persistentes ou executor de processos Python só suportam o modo documental/manual. Consulte o [guia de construção e instalação local testado](GETTING_STARTED.md) para comandos do pacote, testes básicos, integrações opcionais e limites de plataforma.

## Verificação

```sh
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

A bateria Novel Judge deve ser executada através de `scripts/run_tests.py`; não é suportada a invocação individual dos seus ficheiros de teste relativos ao pacote.

As verificações de privacidade e JSON inspecionam os ficheiros-fonte, incluindo os não rastreados e os ignorados pelo Git. Excluem metadados do Git, caches geradas de Python/testes e ambientes virtuais confirmados na raiz; os ficheiros rastreados continuam a ser verificados. Ligações simbólicas, ficheiros ilegíveis e texto que não seja UTF-8 causam rejeição por segurança. Mantenha os pacotes gerados e o estado narrativo fora desta cópia de trabalho. O analisador apresenta nomes de ficheiro e categorias de ocorrências, nunca o conteúdo encontrado; é uma verificação heurística, não uma prova de privacidade nem uma análise do histórico.

## Caminhos de plataforma

A documentação utiliza marcadores como `<SKILLS_ROOT>`, `<WORKSPACE_ROOT>` e `<NOVEL_PROJECTS_ROOT>`. Configure-os para a plataforma anfitriã. Os inicializadores executáveis utilizam por omissão `~/.novel-os/novels`, salvo se for fornecido `NOVEL_PROJECTS_ROOT` ou um `--root` explícito.

## Segurança e âmbito de investigação

As habilidades de investigação destinam-se a material lícito e publicamente acessível e não devem contornar barreiras de autenticação, CAPTCHA, paywalls, controlos de robots/acesso ou restrições da plataforma. A investigação sobre pessoas reais exige proveniência das fontes e não deve transformar material não verificado ou sensível em afirmações factuais.

## Governação

Leia:

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- [SECURITY.md](SECURITY.md)
- [THIRD_PARTY.md](THIRD_PARTY.md)

## Licença e contribuições

Leia [LICENSE](LICENSE.md) e os [detalhes de pagamento comercial](COMMERCIAL_TERMS.md) antes da utilização comercial. Apenas o lucro líquido anual positivo de produtos, serviços e romances relacionados é incluído; as atividades não relacionadas são excluídas. A declaração é feita pelo próprio utilizador, sem telemetria oculta ou cobrança automática. Os componentes de terceiros mantêm as suas próprias licenças e avisos.

Os utilizadores comerciais aceitam explicitamente a versão da licença antes da utilização. Comece por uma issue do GitHub sem detalhes privados ou financeiros para combinar um canal privado de declaração; não publique demonstrações financeiras ou registos de pagamentos. As regras de contribuição e redistribuição estão em [CONTRIBUTING.md](CONTRIBUTING.md).

## Limites da verificação

São fornecidos testes principais em Linux e verificações sintéticas de instalação. Não são certificados os serviços opcionais Graphify/MCP/Instagram, modelos em produção, integrações de agentes nativos nem uma matriz de plataformas/versões de Python. Os relatórios de modelos apresentados como exemplo são ilustrações sintéticas, não provas de desempenho medido de fornecedores ou modelos.
