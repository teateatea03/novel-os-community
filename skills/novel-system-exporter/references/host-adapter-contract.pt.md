# Contrato do adaptador de host do Novel OS

<!-- language-navigation -->

[繁體中文](host-adapter-contract.md) | [English](host-adapter-contract.en.md) | [日本語](host-adapter-contract.ja.md) | [한국어](host-adapter-contract.ko.md) | [Español](host-adapter-contract.es.md) | [Français](host-adapter-contract.fr.md) | [Deutsch](host-adapter-contract.de.md) | **Português**

Este contrato destina-se a integradores de frameworks de IA diferentes do Minis. O Novel OS não é um plugin capaz de obter acesso a arquivos, acesso a modelos ou memória entre conversas simplesmente enviando um ZIP. Para que a implantação seja considerada automatizada, o host deve fornecer as capacidades a seguir.

## A. Interfaces mínimas que o host deve fornecer

| Capacidade | Operações mínimas | Uso no Novel OS | Se indisponível |
|---|---|---|---|
| Roteador de skills | `load_skill(name)`/leitura de arquivos de recursos | O coordenador carrega dezesseis skills especializadas conforme a intenção | Incluir manualmente a Skill adequada no prompt |
| Armazenamento persistente | `read(path)`, `write(path)`, `list(path)`, `mkdir(path)` | Bíblia do projeto, capítulos, registros, estado, grafos e snapshots | Modo exclusivamente documental; sem garantia de continuidade entre execuções |
| Executor de processos | `run(argv, cwd)` | Executar ferramentas Python de inicialização, controles, estado e grafos | Usar modelos e listas de verificação manualmente; não afirmar que a validação foi executada |
| Identidade do projeto | `project_id` estável → raiz de armazenamento | Ler o estado do mesmo romance em uma nova conversa/worker | O usuário fornece arquivos/resumos manualmente a cada vez |
| Bloqueio de escrita da ramificação | `lock(project,session,branch)`/bloqueio de transações | Serializar a recuperação, as verificações de hashes obsoletos e os commits de eventos, estado e manifesto | Permitir apenas um escritor; não afirmar segurança com vários workers |
| Adaptador de tarefas do modelo | Aceitar `minis.model-task.v1`, persistir primeiro o agendamento, permitir que workers reivindiquem tarefas com uma concessão temporária e retornar um esquema fixo | Restringir modelos L1/L2 a tarefas individuais de extração/planejamento/renderização/reparo; permitir repetição/cancelamento/resultados obsoletos/recuperação após reinício | Modo documental ou formulários manuais; modelos não têm autoridade sobre o estado |
| Versionamento de runtime/eventos | Versão do runtime, esquema de eventos, contrato de transição, fixture de reprodução de referência | Reproduzir o histórico antigo após uma atualização continua produzindo o mesmo hash de estado; contratos desconhecidos são rejeitados por segurança | Congelar o runtime antigo; atualizar somente após migração manual |
| Solucionador narrativo | Exploração limitada dos estados de storylets | Encontrar estados inalcançáveis, destinos inválidos e bloqueios de avanço, informando os limites de exploração | Revisar caminhos manualmente; não afirmar que todos foram validados |
| Controle de sugestões de eventos aleatórios | `off`/`on-suggestion` por ramificação, janela semântica, conjunto com semente, auditoria não canônica | Oferecer cartões de direção opcionais somente em janelas elegíveis, preservando resultados sem evento e proveniência reproduzível | Manter fixo em `off`; não fazer sorteios ocultos por prompts nem tratar sugestões como cânone |
| Projetor de memória/grafos | Evento → memória episódica; eventos → projeção Graphify | Memória rastreável e grafos reconstruíveis | Preservar eventos; marcar índices derivados como não atualizados |
| Índice Graphify de conclusão | `sync_graph.py` sincroniza fontes, afirmações e ramificações com o `graph.json` existente | Fontes, evidências, versões e hipóteses de conclusão consultáveis | O grafo é um índice derivado e não deve sobrescrever a prosa/o cânone no sentido inverso |

O executor de processos deve preferir **arrays argv a strings de shell concatenadas**, permanecer nos espaços de trabalho do projeto/das skills e preservar stdout, stderr e o código de saída como artefatos dos controles.

## B. Mapeamento de caminhos

A configuração de implantação deve fornecer os valores a seguir. Não fixe caminhos do Minis em outro ambiente:

```text
SKILLS_ROOT=/agent/skills
NOVEL_PROJECTS_ROOT=/agent/data/novels
CHARACTER_DATABASE_ROOT=/agent/data/character-databases
CHARACTER_DATABASE_WORK_ROOT=/agent/work/character-db-batches
WORLD_DATABASE_ROOT=/agent/data/world-databases
SPECIAL_OBJECT_DATABASE_ROOT=/agent/data/special-object-databases
SPECIAL_OBJECT_DATABASE_WORK_ROOT=/agent/work/special-object-db-batches
INTERACTIVE_PROJECTS_ROOT=/agent/data/interactive-fiction
```

- `init_novel_project.py` pode ler `NOVEL_PROJECTS_ROOT` ou aceitar um `--root` explícito.
- `SPECIAL_OBJECT_DATABASE_ROOT` armazena o banco de dados autoritativo de objetos especiais em `graphify-out/graph.json`; `SPECIAL_OBJECT_DATABASE_WORK_ROOT` armazena JSON de lotes e pacotes de entrega e não pode substituir a cópia autoritativa.
- `WORLD_DATABASE_ROOT` armazena o banco de dados autoritativo de mundos em `graphify-out/graph.json`; `WORLD_DATABASE_WORK_ROOT` armazena JSON de lotes de mundos e pacotes de entrega e não pode substituir a cópia autoritativa.
- As outras raízes são configurações do roteador/adaptador do framework. Substitua os marcadores `<..._ROOT>` nas Skills pertinentes por caminhos persistentes reais.
- Todos os arquivos de um romance devem ficar sob a mesma raiz de projeto, que possa ser lida novamente; não mantenha apenas o capítulo mais recente no contexto temporário do chat.

## C. Procedimento obrigatório de implantação

1. Extraia o pacote e execute primeiro o seguinte:

   ```bash
   # Confirme primeiro que Python, hashes e o teste básico completo estão disponíveis:
   python3 scripts/install_novel_os.py --target "$SKILLS_ROOT" --smoke-test
   ```

2. Registre **17** Skills (o coordenador + 16 Skills especializadas). `novel-reality-state-engine` deve fornecer JSON de eventos/estado, uma Reality Card e um Reality Gate executável. `novel-model-capability-compatibility` deve fornecer testes de texto/JSON/ferramentas/estado do endpoint real, níveis de capacidade e alternativas. `novel-sensory-sound-prose` deve preservar seu contrato de prosa de som/cinco sentidos. Mantenha os caminhos relativos entre diretórios irmãos.
3. Mapeie `project_id` para as raízes persistentes acima e autorize o agente a ler e gravar os arquivos daquele projeto.
4. Execute o inicializador para um projeto novo e confirme que Markdown/JSON/`graphify-out/graph.json` são criados com sucesso.
5. Encerre e inicie uma nova execução do agente, pedindo que ele leia o estado antes de continuar a história, para verificar que não depende do contexto temporário.
6. Faça dois workers tentarem commits simultâneos sobre o mesmo hash de estado de origem: exatamente um deve ter sucesso, e o outro deve receber stale-hash/conflito. Depois, verifique o hash do estado atual por reprodução de eventos.
7. Crie duas memórias episódicas e verifique que a reflexão cite pelo menos dois IDs de evidências existentes. Compile uma tarefa de renderização L1 e confirme que o pacote não contém verdade oculta e tem `may_commit_state=false`.
8. Reconstrua a projeção interativa do Graphify a partir dos eventos. Excluí-la e reconstruí-la deve produzir o mesmo hash de origem.
9. Preserve pelo menos um fixture de histórico de referência. Reproduzi-lo com um novo runtime deve produzir o hash de estado esperado, e contratos de transição desconhecidos devem ser rejeitados.
10. Crie uma atividade de modelo e verifique a recuperação após o vencimento da concessão temporária, a marcação de resultados antigos como obsoletos após o avanço do estado e o bloqueio do console do autor enquanto houver uma atividade pendente.
11. Crie um fixture de storylets com estados inalcançáveis, destinos inválidos e bloqueios de avanço; confirme que o solucionador detecte todos e informe explicitamente a profundidade máxima e o máximo de estados.
12. Após compactar os eventos, exclua o índice e altere o arquivo histórico. O controle de integridade do manifesto deve rejeitá-lo antes da reconstrução do índice.
13. Verifique que uma nova ramificação use `off` por padrão, sem sorteios nem gravações de auditoria. Depois que o usuário ativar `on-suggestion`, use uma semente fixa em um limite de cena para obter o mesmo resultado de sugestão/sem evento e confirme que o registro de eventos canônicos, State, Graph, Knowledge e a prosa permaneçam inalterados.
14. Envie solicitações de entrada meta, uma consequência direta pendente, situações de alta pressão sem pausa natural, uma consequência determinística existente e uma ameaça não antecipada; todas devem ser suprimidas. Adotar uma sugestão só pode criar uma entrega de planejamento e deve listar os controles Reality/Knowledge/Agency/Behavior/World/Canon.
15. Verifique o hash/bytes/contagem do manifesto do segmento ativo: após excluir o índice de eventos, alterar o registro ativo deve provocar uma rejeição segura. As reivindicações de atividade retornam um token de exclusão; a conclusão deve ser rejeitada com tokens antigos, tokens ausentes ou concessões expiradas. Todos os IDs baseados em arquivos devem rejeitar travessia de diretórios. Repetir o mesmo `request_id` de evento aleatório não deve refazer o sorteio nem criar uma segunda entrada de auditoria. Uma cadeia de hashes de auditoria alterada não deve ser reproduzida, e sugestões expiradas não devem criar entregas de adoção.

## D. Adaptadores de ferramentas opcionais

### Pesquisa web

Se o host fornecer ferramentas de navegador/pesquisa, o roteador deve registrar resultados de pesquisa, URLs, editores, datas e citações curtas nos campos de evidências de pesquisa/grafos. Sem navegador, só pode processar material fornecido pelo usuário, deve usar `【待定】` (“indeterminado”)/`【提案】` (“proposta”) e não deve fingir ter verificado as fontes.

### Revisão por segundo modelo/subagente

`long-form-novel-writer/scripts/independent_review.py` atualmente chama o `minis-model-use` do Minis. Frameworks diferentes do Minis devem fazer uma destas duas coisas:

1. Escrever um adaptador de framework que aceite `role`, `prompt` e `max_tokens`, chame outro modelo/subagente e salve o texto original e o JSON analisado em `reviews/`; ou
2. Desativar a revisão independente, usar controles locais/listas manuais em seu lugar e marcar “segundo modelo não executado” na entrega.

Em ambos os casos, preserve estas regras de saída: `machine_suggestion` não pode ser promovida diretamente a `[CANON]`; problemas sem duas evidências de apoio vão apenas para `questions`; falhas devem produzir um artefato `unavailable` e nunca contar silenciosamente como aprovação.

### Grafos e controle de versão

- `networkx`: habilita path, affected, GraphML e funcionalidades relacionadas.
- `graphifyy` + `networkx`: habilita HTML do Graphify, análise de comunidades e exportações Cypher.
- Git: usado apenas para commits/ramificações; snapshots de arquivos continuam disponíveis sem Git.

São melhorias, não pré-requisitos para começar um romance.

## E. Lógica mínima do roteador

```text
if a solicitação é criar/atualizar/consultar/comparar/exportar um banco de dados de objetos especiais:
    carregar special-object-database-builder
    adicionar novel-worldbuilding-architect + knowledge-relationship-graph
    adicionar character-db + behavior quando o operador/a máquina autônoma/a personalidade importar
    adicionar long-form quando houver vínculo com um projeto de romance ou estado de capítulo
elif a solicitação é criar/atualizar/consultar/exportar um banco de dados de mundos:
    carregar novel-world-database-builder
    adicionar novel-worldbuilding-architect + knowledge-relationship-graph
    adicionar long-form quando houver vínculo com um projeto de romance ou estado de capítulo
elif a solicitação é escrita entre capítulos/continuação/revisão do esboço:
    carregar long-form + behavior
    adicionar world/style/graph somente quando o estado da história precisar
elif a solicitação é pesquisa de personagens:
    carregar character-deep-digger
    adicionar behavior + character-db/graph quando evidências ou persistência forem necessárias
elif a solicitação é revisão de voz humana/chinês tradicional de Taiwan/voz do personagem:
    carregar human-voice-editor após verificar conteúdo/continuidade/estilo
elif a solicitação é concluir um romance abandonado/inacabado, a intenção do autor original ou um final alternativo:
    carregar unfinished-novel-completion
    adicionar long-form + ferramentas de evidências/fontes + world/behavior/style/graph conforme necessário
elif a solicitação é ficção interativa de entrada livre:
    carregar immersive-interactive-fiction
    adicionar world/behavior/style/graph conforme a complexidade da cena
```

O coordenador deve cuidar primeiro deste roteador. Não coloque indiscriminadamente todas as Skills no contexto do modelo a cada turno.

## F. O que o pacote não pode fazer automaticamente

- Instalar Skills, configurar chaves de API, habilitar permissões de ferramentas ou criar bancos de dados em contas de nuvem não autorizadas.
- Dar a um modelo somente de chat um shell, um sistema de arquivos, memória permanente ou capacidades de múltiplos modelos.
- Sobrepor as políticas de conteúdo, limites de tokens, regras de privacidade ou restrições de rede do modelo/plataforma de destino.

Se faltar algum pré-requisito, use os modos alternativos B/C/D de [platform-compatibility.pt.md](platform-compatibility.pt.md) e liste cada funcionalidade desativada no relatório de implantação.
