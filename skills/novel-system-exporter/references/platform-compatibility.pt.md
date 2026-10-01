# Compatibilidade de plataformas e matriz de dependências do Novel OS

<!-- language-navigation --> [繁體中文](platform-compatibility.md) | [English](platform-compatibility.en.md) | [日本語](platform-compatibility.ja.md) | [한국어](platform-compatibility.ko.md) | [Español](platform-compatibility.es.md) | [Français](platform-compatibility.fr.md) | [Deutsch](platform-compatibility.de.md) | **Português**

Este documento deve ser entregue com o ZIP. O Novel OS é uma coleção de **instruções de skills + modelos locais/validadores Python**, não um modelo independente, uma plataforma de chat, um banco de dados vetorial nem um serviço de nuvem. A possibilidade de “implantação automática” depende de o framework de IA de destino permitir ler skills com vários arquivos, gravar arquivos, executar comandos e, opcionalmente, chamar modelos/acessar a rede.

```text
- 1 coordenador + 16 skills colaboradoras, totalizando 17 Skills de runtime (o código-fonte também inclui o exportador)
- Compatibilidade de capacidades do modelo: `novel-model-capability-compatibility`, responsável por testes do endpoint real, L0–L5, adaptadores, alternativas e regressões após a troca
- Estado de realidade: `novel-reality-state-engine`, que fornece uma cadeia de validação evento → estado → capacidade → comportamento → prosa
- Bancos de dados de mundos: `novel-world-database-builder`
- Bancos de dados de objetos especiais: `special-object-database-builder`, com a raiz autoritativa em `SPECIAL_OBJECT_DATABASE_ROOT`
- Conclusão de obras abandonadas: unfinished-novel-completion
```

## 1. Componentes principais e suas dependências

| Componente/função | Sistema/formato usado | Dependências mínimas | Dependências opcionais | Alternativa se indisponível |
|---|---|---|---|---|
| Despacho de skills | Metadados YAML de `SKILL.md` + Markdown; `novel-operating-system` | Uma IA/agente que possa carregar vários arquivos de texto | Um runtime de Skills que as acione automaticamente pela descrição | Usar o coordenador como prompt de sistema/instruções do projeto e anexar manualmente as outras skills |
| Persistência do projeto | Markdown, JSON, pastas comuns | Leitura/gravação de arquivos UTF-8 | Git | Manter arquivos com os mesmos nomes no chat/Canvas/documentos de nuvem; informar explicitamente que a persistência entre turnos não é garantida |
| Inicialização de narrativa longa e controles locais | CLI do Python, biblioteca padrão | **Python 3.10+**, shell, disco gravável | Git | Copiar modelos e listas de verificação manualmente; não afirmar que os controles/snapshots foram executados |
| Grafo autoritativo de relacionamentos | JSON de nós e ligações compatível com Graphify | Python 3.10+ (inicialização, validação JSON) | `networkx`: path/affected; `graphifyy` + `networkx`: HTML, análise de comunidades, exportação Cypher | Salvar/ler graph.json; consultar relacionamentos manualmente, sem afirmar que visualizações ou caminhos mínimos foram gerados |
| Banco de dados de mundos | JSON compatível com Graphify; nós de mundo/local/facção/recurso/regra/evento/afirmação, evidências de fontes e lotes incrementais | Python 3.10+, arquivos UTF-8 persistentes | `networkx`/`graphifyy`: path, affected, HTML, GraphML, Cypher | Salvar graph.json e registros Markdown; verificar versões/conhecimento manualmente, sem afirmar que as exportações visuais foram concluídas |
| Banco de dados de objetos especiais | JSON compatível com Graphify; nós de objeto/versão/variante/módulo/capacidade/especificação/energia/restrição/posse/operação/ciclo de vida e evidências de fontes | Python 3.10+, arquivos UTF-8 persistentes | `networkx`/`graphifyy`: path, affected, HTML, GraphML, Cypher | Salvar graph.json e registros de objetos; verificar conflitos de versões/especificações manualmente, sem afirmar que as exportações visuais foram concluídas |
| Ficção interativa | Estado compatível com JSON, registro de turnos em Markdown | Leitura/gravação de arquivos; Python 3.10+ permite validação/pontos de controle | Memória de longo prazo/banco de dados | Revisar a cada turno o estado colado no chat; a retenção após reabrir uma conversa não é garantida |
| Pesquisa e validação de fontes para concluir obras | Obras inacabadas | `unfinished-novel-completion`; ferramentas de pesquisa/anexos são opcionais | `source_ingest.py` registra hashes, versões, completude e situação dos direitos; `completion_gate.py` verifica afirmações excessivas sobre intenção e limites de publicação | |
| Revisão independente por modelo | CLI/API de chamada de modelos do host | Nenhuma; não é obrigatória | Capacidade de chamar um segundo modelo ou subagente | Usar uma lista manual/do mesmo modelo; não afirmar “revisado por um modelo independente” |

### Pesquisa de fontes e ferramentas para obras inacabadas

As ferramentas básicas de `unfinished-novel-completion` usam somente a biblioteca padrão do Python: `init_completion_project.py`, `source_ingest.py`, `compare_source_versions.py`, `branch_diff.py`, `feasibility_report.py`, `sync_graph.py`, `completion_gate.py`, `provenance_report.py` e `run_regression.py`. Acesso à rede, OCR, ferramentas PDF, navegadores e um segundo modelo são opcionais. Sem eles, ainda é possível processar arquivos fornecidos pelo usuário, mas o escopo das fontes e as incógnitas devem ser identificados; não finja que a verificação ocorreu.

### Ambiente mínimo “totalmente automatizado”

- **Python 3.10 ou posterior:** os scripts principais atuais usam a sintaxe de união de tipos `X | None`; recomenda-se Python 3.11+.
- **Shell POSIX ou executor de processos equivalente:** para executar a CLI do Python.
- **Sistema de arquivos persistente e gravável:** para instalar skills e salvar projetos de romances; são necessários pelo menos um diretório de skills e um de projetos graváveis.
- **Compatibilidade com arquivos UTF-8:** histórias, modelos, JSON e conteúdo em chinês tradicional usam UTF-8.
- **Extração de ZIP:** necessária apenas para distribuição em ZIP; Git/envio de pastas pode ser usado como alternativa.
- **Biblioteca padrão local:** os scripts principais de inicialização, registros, controles, estado e pacotes dependem somente da biblioteca padrão do Python; o teste básico não exige `pip install`.

Essas funcionalidades não exigem chave de API, banco de dados, Node.js nem acesso à rede.

### Dependências opcionais (melhorias, não o fluxo básico)

```bash
# Caminhos de grafos, consultas em cascata, GraphML
python -m pip install networkx

# Exportações HTML/comunidades/Cypher do Graphify; o pacote de origem se chama graphifyy
python -m pip install graphifyy networkx

# Snapshots de versões do Git e commits protegidos por controles
git --version
```

- `relationship_graph.py init/validate/search/neighbors/timeline/add/import/snapshot` pode usar somente a biblioteca padrão do Python; `path`/algumas verificações de ciclos exigem `networkx`.
- `relationship_graph.py export` exige **`networkx` + `graphifyy`**. Sem eles, preserve `graph.json` e não afirme falsamente que saídas HTML/GraphML/Cypher foram geradas.
- `independent_review.py` atualmente é um **adaptador específico do Minis** que chama `minis-model-use`. Em outro framework, substitua-o pelo adaptador de segundo modelo/subagente/API desse framework ou desative esta etapa opcional de revisão.
- `novel_git.py` é uma camada opcional de controle de versão. Sem Git, `snapshot_project.py` ainda pode criar snapshots de arquivos.

## 3.2 Pontos de integração com o host e substituições obrigatórias

Os formatos de dados principais do pacote são portáveis, mas o integrador deve tratar estes **pontos de integração com o host/framework**:

| Ponto de integração | Uso atual no Minis | O que outros frameworks de IA devem fazer |
|---|---|---|
| Raiz padrão de romances | `<NOVEL_PROJECTS_ROOT>` | Definir `NOVEL_PROJECTS_ROOT` ou passar `--root <persistent-projects-root>` a cada inicializador; não presumir que `<MINIS_ROOT>` existe |
| Raiz do banco de dados de personagens | `<CHARACTER_DATABASE_ROOT>` | Mapear `<CHARACTER_DATABASE_ROOT>` e a preparação de lotes para `<CHARACTER_DATABASE_WORK_ROOT>`; ambos devem ser acessíveis pelo mesmo projeto/agente |
| Raiz do banco de dados de objetos especiais | `<SPECIAL_OBJECT_DATABASE_ROOT>` | Mapear `<SPECIAL_OBJECT_DATABASE_ROOT>` e a preparação de lotes para `<SPECIAL_OBJECT_DATABASE_WORK_ROOT>`; ambos devem ser acessíveis pelo mesmo projeto/agente |
| Raiz do estado de ficção interativa | `<INTERACTIVE_PROJECTS_ROOT>` | Mapear `<INTERACTIVE_PROJECTS_ROOT>` e garantir a leitura de estado/pontos de controle/registros entre execuções |
| Revisão independente | `minis-model-use run` | Reescrever o adaptador de comandos de `independent_review.py` ou criar uma função equivalente de subagente; preservar o esquema JSON, os artefatos de erro e a regra contra promoção automática a cânone |
| Descoberta de skills | Registro de skills do Minis + diretórios irmãos | Registrar **17** descrições (o coordenador + dezesseis skills especializadas) ou construir um roteador de intenções; permitir que o agente leia arquivos de recursos irmãos sob demanda |
| Estado de longo prazo | Diretório compartilhado do Minis | Conectar um volume durável, banco de dados, armazenamento de artefatos ou gerenciador de pontos de controle do framework, recuperando o estado pelo ID do projeto |
| Ferramentas de pesquisa | Navegador/shell do Minis | Conectar ferramentas de navegador/pesquisa/arquivos do framework; caso contrário, restringir a pesquisa ao material fornecido pelo usuário |

- `init_novel_project.py` já aceita `NOVEL_PROJECTS_ROOT`; um `--root` explícito tem precedência. Os marcadores `<..._ROOT>` dos bancos de dados de personagens/mundos/objetos especiais e da ficção interativa devem ser substituídos pelo roteador/configuração de implantação do framework. Cada `<MINIS_ROOT>/...` da documentação original é um **caminho padrão de exemplo** fora do Minis, não um requisito obrigatório do sistema.

## 4. Níveis de capacidade dos frameworks de IA

### A | Skills nativas + shell + sistema de arquivos (modo completo)

Para frameworks com runtime de Skills, ferramentas de agente e sandbox/terminal. Instale diretamente o pacote completo executando:

```bash
python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test
```

**O framework deve:**

1. Registrar `<SKILLS_DIR>/novel-operating-system/SKILL.md` como skill principal acionável.
2. Preservar as **17** pastas de skills (o coordenador + dezesseis skills colaboradoras) como irmãs; não enviar somente o arquivo de entrada.
3. Permitir que o agente leia `SKILL.md`, modelos, referências e scripts das skills irmãs.
4. Fornecer uma ferramenta segura de comandos ou um executor de processos para `python3`.
5. Após reindexar/reiniciar o registro de skills, usar os resultados do teste básico para aceitação.

**Melhorias recomendadas:** ferramentas de pesquisa web, um adaptador de segundo modelo, Git, `networkx` e `graphifyy`.

### B | Frameworks personalizados de agentes/chamada de ferramentas (exige adaptador)

Para frameworks com prompt de sistema, chamadas de funções e ferramentas de arquivos, mas sem interpretação de `SKILL.md`.

**O integrador do framework deve:**

1. Colocar `novel-operating-system/SKILL.md` nas instruções de sistema/desenvolvedor do agente; preservar a descrição YAML como regras de roteamento.
2. Transformar as outras **dezesseis** skills em documentos de referência recuperáveis ou construir um roteador que carregue o `SKILL.md` apropriado conforme a intenção do usuário.
3. Conectar as ferramentas:
   - shell → scripts Python;
   - leitura/gravação/listagem de arquivos → arquivos e estado do projeto;
   - pesquisa web/navegador → pesquisa de fontes públicas;
   - segundo modelo/subagente → adaptador substituto de `independent_review.py`.
4. Substituir a chamada a `minis-model-use`, específica do Minis, pelo cliente de modelos do próprio framework. Preservar o esquema JSON original de revisão, os artefatos de falha e o princípio de que “machine_suggestion não é promovida automaticamente a cânone”.
5. Especificar uma chave de armazenamento/espaço de trabalho durável para que os arquivos da mesma obra sejam mantidos entre conversas/workers.
6. Implementar o acionamento automático de skills ou desativá-lo explicitamente; colocar **17 documentos Skill** no contexto não justifica afirmar que colaborarão automaticamente.

### C | IA de chat que só permite enviar arquivos de conhecimento/instruções personalizadas (modo documental)

Convenções de escrita, modelos, esquemas de dados e listas de verificação são portáveis, mas não há automação real.

**Obrigatório:** enviar toda a subárvore `skills/`; definir o coordenador como instruções do projeto; a cada turno, anexar ou fazer a IA consultar o estado atual da obra, a bíblia narrativa, a linha do tempo, os arquivos de personagens, o registro do leitor e o resumo do capítulo anterior.

**Não prometa:** criação automática de pastas, controles CLI, verificação de hashes, Git, exportação Graphify, memória entre chats, tarefas em segundo plano nem revisão por segundo modelo.

### D | Modelos com um único prompt de sistema (alternativa manual)

Cole um coordenador condensado no prompt de sistema e use as skills especializadas e os modelos de projeto como base de conhecimento. O usuário/integrador deve salvar manualmente os documentos de estado produzidos a cada turno. Isso preserva o modelo de raciocínio, mas não equivale ao Novel OS completo.

## 5. Lista de integração de frameworks comuns

| Tipo | Onde se integra | Configuração obrigatória | Principal cuidado |
|---|---|---|---|
| Estilo OpenAI Assistants/Responses | Instruções de sistema + pesquisa vetorial/de arquivos + interpretador de código/sandbox personalizado | Construir um roteador, um armazenamento persistente de arquivos e um adaptador de execução Python | Não presumir que os arquivos se sincronizam automaticamente entre execuções; os arquivos do projeto devem ser salvos explicitamente de volta ao armazenamento |
| Estilo Claude Projects/MCP | Instruções do projeto + arquivos de conhecimento; servidor MCP de sistema de arquivos/shell | Expor skills como recursos; usar MCP para leitura/gravação/executor/web | Sem MCP, é nível C e não pode executar scripts |
| Estilo Gemini Gems/Vertex Agent | Instrução de sistema + File Search/Code Execution/Cloud Storage | Conectar armazenamento durável, um roteador de funções e um executor Python | Instruções de Gem sozinhas geralmente não oferecem fluxos de arquivos entre conversas |
| Estilo LangChain/LangGraph/CrewAI/AutoGen | Nó roteador + ferramentas de arquivos + ferramenta de subprocessos + gerenciador durável de pontos de controle | Carregar skills por intenção, preservar o ID do projeto e construir um adaptador de agente revisor | A descoberta de skills e os pontos de controle de estado devem ser implementados; a extração do pacote não os ativa sozinha |
| Estilo Open WebUI/AnythingLLM/Dify/Flowise | Base de conhecimento + fluxo de agente/nós de ferramentas | Enviar arquivos de skills, conectar ferramentas shell/Python e montar um volume persistente | Chat RAG puro é nível C; fluxos de trabalho são necessários para alcançar A/B |
| Host de banco de dados de mundos | `WORLD_DATABASE_ROOT` + `WORLD_DATABASE_WORK_ROOT` | Montar um grafo de mundo persistente e um espaço de trabalho de lotes; fornecer snapshot/validate/affected/export | Sem executor de processos, salvar apenas JSON/Markdown e não afirmar que a CLI do Graphify foi executada |
| Host de banco de dados de objetos especiais | `SPECIAL_OBJECT_DATABASE_ROOT` + `SPECIAL_OBJECT_DATABASE_WORK_ROOT` | Montar um grafo persistente de objetos especiais e um espaço de trabalho de lotes; fornecer snapshot/validate/affected/export | Sem executor de processos, salvar apenas JSON/Markdown e não afirmar que a validação ou exportação de objetos especiais foi executada |
| Agentes de programação como Cursor/Claude Code/Codex CLI | Diretório de skills/comandos + espaço de trabalho | Instalar **17** pastas e configurar Python e a raiz do espaço de trabalho | O adaptador de revisão conversacional por modelo deve ser reescrito para a CLI correspondente |

Esses nomes apenas ilustram tipos de integração. As versões, os planos e as permissões dos produtos variam; consulte a documentação mais recente antes da implantação.

## 6. Lista de aceitação da implantação

Após a integração, o host ou integrador deve verificar cada item:

- [ ] `novel-operating-system` e as dezesseis skills especializadas vizinhas podem ser lidas.
- [ ] Após gravar um arquivo de teste, uma nova execução/conversa do agente consegue lê-lo novamente.
- [ ] `python3 --version` é ≥ 3.10; se forem necessários exportadores de grafos, `networkx`/`graphifyy` podem ser importados.
- [ ] `python3 scripts/install_novel_os.py --target <SKILLS_DIR> --smoke-test` passa ou os itens que não podem executar são documentados explicitamente.
- [ ] Um novo projeto de romance de teste tem sua bíblia narrativa, estado, linha do tempo, registro do leitor e graph.json criados.
- [ ] O agente escreve uma passagem curta, atualiza o estado e continua em uma nova execução, demonstrando que a continuidade não depende apenas do contexto restante.
- [ ] Se a pesquisa estiver habilitada, é possível registrar URLs/fontes/confiança em vez de tratar trechos de pesquisa como cânone.
- [ ] Se a revisão por segundo modelo estiver habilitada, falhas do adaptador produzem somente um artefato de indisponibilidade, sem bloquear nem inventar resultados.

## 7. Limitações da plataforma e limites de responsabilidade

- As políticas de conteúdo, permissões de ferramentas, limites de tokens, retenção de dados e regras de rede do modelo de destino são independentes do Novel OS e não podem ser sobrepostas por esta Skill.
- “Implantação automática” significa instalação, criação de estruturas e carregamento do roteador automáticos dentro de um **framework de agentes com permissões de instalação/arquivos/shell**. Não significa instalar o ZIP permanentemente por entregá-lo a qualquer modelo de chat.
- Modelos externos, navegadores e Git são melhorias opcionais. Quando ausentes, informe explicitamente o modo alternativo; não esconda lacunas de capacidade afirmando que o trabalho foi concluído.
