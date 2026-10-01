# Contrato do pacote portátil do Novel OS

<!-- language-navigation -->

[繁體中文](bundle-contract.md) | [English](bundle-contract.en.md) | [日本語](bundle-contract.ja.md) | [한국어](bundle-contract.ko.md) | [Español](bundle-contract.es.md) | [Français](bundle-contract.fr.md) | [Deutsch](bundle-contract.de.md) | **Português**

Na estrutura do pacote `novel-os-portable-v<version>/`, `skills/` contém um coordenador e 16 skills especializadas. `public-web-research/` fornece aquisição segura e retomável de HTTP(S) público e preparação de candidatos para Evidence Run. `novel-model-capability-compatibility/` mantém os contratos de testes de capacidade do modelo/L0–L5/alternativas. `novel-reality-state-engine/` mantém as ferramentas de validação evento → estado → capacidade → comportamento → prosa. `novel-world-database-builder/` mantém esquemas de bancos de dados de mundos, modelos de lotes, pacotes de entrega e especificações de consulta. `special-object-database-builder/` mantém esquemas de versões, capacidades, especificações e ciclos de vida de objetos/armaduras/mechas/dispositivos.

```text
novel-os-portable-v<version>/
├── MANIFEST.json
├── LICENSE
├── LICENSE.zh-TW.md
├── LICENSE.ja.md
├── LICENSE.ko.md
├── LICENSE.es.md
├── LICENSE.fr.md
├── LICENSE.de.md
├── LICENSE.pt.md
├── THIRD_PARTY.md
├── THIRD_PARTY.zh-TW.md
├── THIRD_PARTY.ja.md
├── THIRD_PARTY.ko.md
├── THIRD_PARTY.es.md
├── THIRD_PARTY.fr.md
├── THIRD_PARTY.de.md
├── THIRD_PARTY.pt.md
├── docs/
│   ├── COMMERCIAL_TERMS.md
│   ├── COMMERCIAL_TERMS.zh-TW.md
│   ├── COMMERCIAL_TERMS.ja.md
│   ├── COMMERCIAL_TERMS.ko.md
│   ├── COMMERCIAL_TERMS.es.md
│   ├── COMMERCIAL_TERMS.fr.md
│   ├── COMMERCIAL_TERMS.de.md
│   └── COMMERCIAL_TERMS.pt.md
├── references/
│   ├── portable-install.md
│   ├── portable-install.en.md
│   ├── portable-install.ja.md
│   ├── portable-install.ko.md
│   ├── portable-install.es.md
│   ├── portable-install.fr.md
│   ├── portable-install.de.md
│   ├── portable-install.pt.md
│   ├── platform-compatibility.md
│   ├── platform-compatibility.en.md
│   ├── platform-compatibility.ja.md
│   ├── platform-compatibility.ko.md
│   ├── platform-compatibility.es.md
│   ├── platform-compatibility.fr.md
│   ├── platform-compatibility.de.md
│   ├── platform-compatibility.pt.md
│   ├── host-adapter-contract.md
│   ├── host-adapter-contract.en.md
│   ├── host-adapter-contract.ja.md
│   ├── host-adapter-contract.ko.md
│   ├── host-adapter-contract.es.md
│   ├── host-adapter-contract.fr.md
│   ├── host-adapter-contract.de.md
│   ├── host-adapter-contract.pt.md
│   ├── bundle-contract.md
│   ├── bundle-contract.en.md
│   ├── bundle-contract.ja.md
│   ├── bundle-contract.ko.md
│   ├── bundle-contract.es.md
│   ├── bundle-contract.fr.md
│   ├── bundle-contract.de.md
│   └── bundle-contract.pt.md
├── skills/
│   ├── novel-operating-system/      # ponto de entrada único obrigatório
│   ├── long-form-novel-writer/
│   ├── novel-character-deep-digger/
│   ├── human-behavior-personality-consultant/
│   ├── novel-worldbuilding-architect/
│   ├── novel-style-craft-director/
│   ├── novel-human-voice-editor/
│   ├── knowledge-relationship-graph/
│   ├── character-database-builder/
│   ├── immersive-interactive-fiction/
│   ├── unfinished-novel-completion/
│   ├── novel-world-database-builder/
│   ├── special-object-database-builder/
│   ├── novel-reality-state-engine/
│   ├── novel-model-capability-compatibility/
│   ├── novel-sensory-sound-prose/
│   └── public-web-research/
└── scripts/
    ├── install_novel_os.py
    ├── verify_novel_os.py
    └── build_novel_os_bundle.py
```

`MANIFEST.json` contém: esquema/versão do pacote, lista de pacotes, versões das skills de origem, um resumo SHA-256 e uma contagem de bytes para cada arquivo do conteúdo, um inventário separado `distribution_notices`, data de criação, exclusões e declarações de dependências de execução. O conteúdo também inclui uma cópia portátil do **guia de compatibilidade de plataformas**. Ele não contém segredos, caminhos absolutos locais, projetos narrativos, configurações de contas nem bancos de dados de mundos.

## Preservação de licenças e avisos

- `--source-root` identifica o diretório de origem `skills/`. Seu repositório pai deve conter os 24 documentos do projeto para oito idiomas: `LICENSE`, `LICENSE.zh-TW.md`, `LICENSE.ja.md`, `LICENSE.ko.md`, `LICENSE.es.md`, `LICENSE.fr.md`, `LICENSE.de.md`, `LICENSE.pt.md`; `THIRD_PARTY.md`, `THIRD_PARTY.zh-TW.md`, `THIRD_PARTY.ja.md`, `THIRD_PARTY.ko.md`, `THIRD_PARTY.es.md`, `THIRD_PARTY.fr.md`, `THIRD_PARTY.de.md`, `THIRD_PARTY.pt.md`; e `docs/COMMERCIAL_TERMS.md`, `docs/COMMERCIAL_TERMS.zh-TW.md`, `docs/COMMERCIAL_TERMS.ja.md`, `docs/COMMERCIAL_TERMS.ko.md`, `docs/COMMERCIAL_TERMS.es.md`, `docs/COMMERCIAL_TERMS.fr.md`, `docs/COMMERCIAL_TERMS.de.md`, `docs/COMMERCIAL_TERMS.pt.md`. A atualização do conteúdo rejeita qualquer documento obrigatório ausente, que não seja arquivo ou que seja um link simbólico antes de alterar o conteúdo. Estes são termos do projeto escolhidos pelo proprietário; os avisos dos projetos de origem mantêm seu próprio escopo.
- A lista explícita adicional de arquivos permitidos é `LICENSE.md`, `LICENSE.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt` e `docs/COMMERCIAL_LICENSE.md`. Se existirem, cada um será copiado byte a byte. Nenhum outro arquivo raiz de `docs/` é exportado. Em particular, `docs/COMMERCIAL_LICENSE_DISCUSSION.zh-TW.md` é um rascunho de discussão sem efeito e não é exportado como licença nem como termos comerciais.
- Os arquivos locais de cada skill `LICENSE`, `LICENSE.md`, `LICENSE.txt`, `COPYING`, `COPYING.md`, `COPYING.txt`, `NOTICE`, `NOTICE.md`, `NOTICE.txt`, `THIRD_PARTY.md` e todos os arquivos dentro de `THIRD_PARTY_LICENSES/` são preservados com a skill e declarados em `distribution_notices`. A atualização compara seus bytes com a origem; a construção e a instalação rejeitam declarações ausentes, arquivos faltantes, bytes alterados, caminhos inseguros ou entradas de resumo ausentes.
- O material adaptado existente do Humanizer-zh exige especificamente `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt`. Ele não pode ser removido da origem nem do manifesto enquanto esse material for distribuído.
- Novos nomes de arquivos legalmente obrigatórios devem ser adicionados a este contrato explícito antes do lançamento. Não dependa de um link para um documento não incluído no pacote. A atualização remove do conteúdo existente as cópias obsoletas de avisos raiz opcionais.
- O ZIP preserva a mesma estrutura relativa à raiz. A instalação armazena todos os documentos de avisos em `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`, preservando caminhos como `docs/COMMERCIAL_TERMS.md` e `skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt`, para que os links relativos de licença continuem funcionando. Os avisos dos projetos de origem locais às skills também permanecem em seus diretórios originais. O instalador nunca grava em `<target>/LICENSE`, `<target>/THIRD_PARTY.md` nem `<target>/docs/`.
- `novel-operating-system/INSTALLATION.json` registra o caminho original, o caminho instalado, o caminho da cópia documental, o SHA-256 e a contagem de bytes de cada aviso instalado. A preparação e a instalação final verificam ambas as cópias quando aplicável. A atualização leva o coordenador anterior e seus avisos para o backup normal das skills e os restaura se a instalação falhar. `DISTRIBUTION_NOTICES/` dentro do coordenador é reservado para documentos gerenciados pelo instalador.
- Para verificar novamente uma instalação, execute `python3 scripts/install_novel_os.py --target <SKILLS_ROOT> --verify-installed-notices` a partir do pacote extraído. Este modo somente de leitura verifica os arquivos de avisos raiz e dos projetos de origem em relação ao registro de instalação. Os resumos estabelecem integridade local, não autenticidade contra um invasor que possa substituir tanto os arquivos quanto os registros; preserve separadamente uma versão confiável.

## Declaração de dependências de execução

Cada versão deve incluir as 32 referências de portabilidade permitidas explicitamente: os quatro guias `portable-install`, `platform-compatibility`, `host-adapter-contract` e `bundle-contract` dentro de `references/`, cada um em oito idiomas. O chinês tradicional usa o nome original sem sufixo (`.md`); o inglês usa `.en.md`; japonês, coreano, espanhol, francês, alemão e português usam `.ja.md`, `.ko.md`, `.es.md`, `.fr.md`, `.de.md` e `.pt.md`. Declare estes níveis com veracidade:

- **Fluxo documental básico**: um LLM que possa ler os arquivos Skill; não exige execução de código.
- **Fluxo local automatizado (v2.7)**: Python 3.10+ (recomenda-se 3.11+), um shell/executor de processos, arquivos UTF-8 persistentes, descoberta de múltiplas skills ou um roteador equivalente, um bloqueio de ramificação, uma autoridade de produção única `ProjectRuntimeAdapter.commit()`, sete controles, eventos semânticos tipados, prontidão do projeto/atualidade das projeções, Quality Eval de feedback do autor e capacidade de extração se distribuído como ZIP. Os bancos de dados de mundos também exigem `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT` graváveis; os de objetos especiais também exigem `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT` graváveis.
- **Melhorias de grafos**: `networkx` para percorrer grafos; `graphifyy` mais `networkx` para exportações HTML/comunidades/Cypher do Graphify. O JSON do grafo continua utilizável sem qualquer um desses pacotes.
- **Integrações opcionais**: Git para commits, ferramentas web/navegador para pesquisa de fontes e um adaptador de segundo modelo/subagente específico do host para revisão independente. `independent_review.py` é específico do Minis até ser substituído.

O funcionamento local básico não exige Node.js, um servidor de banco de dados, uma chave de API nem conexão com a internet. Um framework sem acesso a arquivos/processos deve ser descrito como modo documental/manual, não como uma instalação automática completa.

## Política de construção

- O conteúdo deve incluir **17** diretórios de skills permitidos (um coordenador + 16 skills especializadas), referências de portabilidade, scripts de instalação/construção e arquivos comuns de texto/código/fixtures/modelos.
- Exclua `.git`, `.DS_Store`, `__pycache__`, `*.pyc`, `.env*`, `node_modules`, `dist`, `build`, todos os projetos de romances, bancos de dados, arquivos compactados e arquivos específicos do sistema.
- Rejeite links simbólicos no caminho das skills de origem ou em qualquer skill empacotada antes de alterar o conteúdo; nunca siga um link de skill até arquivos não relacionados do host. Documentos existentes não autorizados no conteúdo também devem fazer a atualização falhar, em vez de entrar silenciosamente em um novo manifesto.
- Preserve os bits de execução de `scripts/*.py` quando existirem na origem.
- Leia somente a árvore local de skills de origem e a lista explícita de avisos permitidos no nível do repositório. A construção é determinística, exceto por `built_at`.
- O pacote é autocontido: os auxiliares de execução usam a biblioteca padrão do Python e descobrem as dependências em relação à sua localização instalada.

## Política de verificação

`verify` deve rejeitar arquivos do conteúdo ausentes, alterados, inesperados ou com hashes divergentes; depois, deve compilar todos os arquivos Python. O teste básico do instalador também deve:

1. inicializar um projeto temporário de romance sob autoridade de produção ativa;
2. verificar que a alteração canônica direta por FileStore está bloqueada;
3. executar a suíte completa do Novel Judge, incluindo autoridade dos controles, prontidão, executor de comandos, Quality Eval v2, eventos semânticos tipados e produção tradicional de narrativa longa;
4. executar o validador de grafos e as regressões de narrativa longa/Reality/capacidades;
5. verificar o conjunto de skills incluído e sua divergência em relação ao conjunto de origem; e
6. para uma versão completa, executar o teste de contrato isolado com um segundo projeto e o piloto de narrativa longa tradicional de 100k+/inversão de conhecimento/cascata.

Uma plataforma que não possa executar Python só é compatível no nível de fluxo de trabalho/documentação; destaque essa limitação na entrega.
