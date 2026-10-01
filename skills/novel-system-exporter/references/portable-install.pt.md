# Importação e implantação do Novel OS

<!-- language-navigation --> [繁體中文](portable-install.md) | [English](portable-install.en.md) | [日本語](portable-install.ja.md) | [한국어](portable-install.ko.md) | [Español](portable-install.es.md) | [Français](portable-install.fr.md) | [Deutsch](portable-install.de.md) | **Português**

## Comece com um inventário de capacidades: escolha o modo de implantação adequado

Antes da entrega, peça ao ambiente de destino que responda:

```text
1. Ele pode instalar várias Skills/comandos? Onde fica o diretório ou a configuração do ponto de entrada?
2. O agente pode ler e gravar arquivos persistentes, listar diretórios e executar comandos de Python/shell?
3. Qual versão do Python está disponível? É permitido instalar networkx, graphifyy e Git?
4. Há ferramentas web/navegador, um segundo modelo ou subagentes disponíveis, e como são chamados por ferramentas?
5. Onde os arquivos do projeto ficam entre novas conversas, novos workers ou reinicializações?
```

Escolha conforme as respostas: **A: instalação completa** (Skills + shell + armazenamento), **B: integração por adaptador** (ferramentas de agente personalizadas), **C: modo de arquivos de conhecimento** ou **D: modo manual com um único prompt**. Consulte [platform-compatibility.pt.md](platform-compatibility.pt.md) para a avaliação completa, os pacotes e os requisitos de adaptadores de cada framework. Sem os pré-requisitos de A/B, não afirme que a “implantação automática” foi concluída.

## Plataformas de IA com diretórios de skills personalizados (A: modo completo)

1. Extraia o ZIP.
2. Execute o seguinte a partir do diretório raiz extraído:

   ```bash
   python3 scripts/install_novel_os.py --target /path/to/agent/skills --smoke-test
   ```

3. Faça a plataforma examinar novamente as skills ou reinicie seu índice de skills.
4. Teste com “Criar um projeto de romance longo”. Isso deve acionar `novel-operating-system`, criar a estrutura do projeto, determinar se são necessários trabalhos de pesquisa/construção de mundos/comportamento/estilo/grafos e concluir o planejamento e os controles antes de redigir a prosa.

**Atualizações:** acrescente `--upgrade`. Antes de substituí-las, o instalador move as skills existentes com os mesmos nomes para `<target>/backups/novel-os-<timestamp>-<unique>/`; em caso de falha, restaura os arquivos originais.

### Licenciamento e avisos de terceiros

O ZIP completo deve preservar as oito versões linguísticas da licença raiz, do guia de terceiros e dos termos comerciais (24 documentos; os nomes exatos estão no contrato do pacote), junto com os arquivos originais de licenças de terceiros de cada skill. O instalador armazena esses avisos em `<target>/novel-operating-system/DISTRIBUTION_NOTICES/`, preservando seus caminhos relativos originais para que os links de licença nos documentos continuem funcionando. Os avisos dos projetos de origem contidos nas skills também permanecem em suas localizações originais. Ele não sobrescreve o `LICENSE` nem o diretório `docs/` da raiz do host. Os avisos anteriores à atualização são salvos com as skills originais no backup daquela atualização.

`novel-operating-system/INSTALLATION.json` registra os caminhos de origem/instalação, o SHA-256 e a contagem de bytes de cada aviso. Após a instalação, execute esta verificação somente de leitura a partir do ZIP extraído:

```bash
python3 scripts/install_novel_os.py --target /path/to/agent/skills --verify-installed-notices
```

Arquivos ausentes ou modificados causam falha. Esta é uma verificação de integridade local, não um substituto para uma fonte confiável de versões. Consulte o inventário explícito de documentos em [bundle-contract.pt.md](bundle-contract.pt.md). Rascunhos de discussão não constituem licenças vigentes e não são exportados como termos formais.

Os modos de adaptação manual B/C/D também devem entregar a licença do projeto/os termos comerciais e todos os avisos dos projetos de origem em conjunto. Não copie apenas `skills/` omitindo os documentos de licença.

## Frameworks de agentes personalizados ou de chamada de ferramentas (B: exige adaptador)

Se um framework não tem um runtime nativo de `SKILL.md`, mas oferece um prompt de sistema, chamadas de funções e ferramentas de arquivos/comandos, extrair o ZIP por si só não conclui a implantação. O integrador deve:

1. Colocar `novel-operating-system/SKILL.md` nas instruções de sistema/desenvolvedor e usar sua descrição para criar um roteador de intenções.
2. Disponibilizar as dezesseis skills especializadas como recursos que o roteador possa ler sob demanda; preservar as relações relativas entre as pastas.
3. Para uma obra abandonada ou inacabada, primeiro concluir a entrega de fontes/cânone/evidências/intenção/viabilidade/ramificações/direitos/proveniência em `unfinished-novel-completion` e, depois, encaminhar a ramificação selecionada ao escritor de narrativa longa.
4. Conectar leitura/gravação de arquivos, listagem de diretórios, processos Python, um espaço de trabalho persistente, `WORLD_DATABASE_ROOT`/`WORLD_DATABASE_WORK_ROOT`, `SPECIAL_OBJECT_DATABASE_ROOT`/`SPECIAL_OBJECT_DATABASE_WORK_ROOT` e pesquisa web à API de ferramentas do framework.
5. Substituir a chamada a `minis-model-use` em `independent_review.py` pela integração de segundo modelo/subagente/API da plataforma. Se nenhuma estiver disponível, desativar esta etapa e registrá-la como não executada.
6. Usar a lista de aceitação da implantação da documentação para testar a persistência de arquivos entre execuções e as atualizações de estado após cada capítulo.

Consulte [platform-compatibility.pt.md](platform-compatibility.pt.md) para os pontos de integração comuns de LangGraph/CrewAI/AutoGen, MCP, OpenAI/Claude/Gemini e Dify/Flowise/Open WebUI. Todos exigem que o integrador do framework construa um roteador/adaptador de ferramentas; este ZIP não pode fazer isso automaticamente em uma conta de nuvem desconhecida.

## Plataformas com um único campo de importação de Skill (C: modo de arquivos de conhecimento)

Envie ou cole todo o diretório `skills/novel-operating-system/`, incluindo suas referências, e mantenha as outras dezesseis pastas de skills no mesmo nível como anexos/arquivos de conhecimento. Instrua a IA:

> Leia primeiro novel-operating-system/SKILL.md. Todas as skills irmãs são colaboradoras obrigatórias deste sistema. Sem shell, crie arquivos de projeto equivalentes em Markdown/JSON e mostre quais controles não podem ser executados. Não afirme falsamente ter criado snapshots do Git, executado validadores ou concluído exportações de grafos.

## Plataformas somente de chat ou de instruções personalizadas (D: alternativa manual)

Use `novel-operating-system/SKILL.md` como instruções principais e o pacote completo `skills/` como documentos de consulta. Este modo permite portar fluxos de trabalho, modelos de documentos, esquemas, formatos de saída, regras e listas de verificação. Não pode garantir a criação automática de arquivos, a persistência entre turnos, a validação por CLI, a instalação do ZIP nem a detecção de acionadores.

### Verificações de implantação para concluir obras inacabadas

Ao entregar uma obra abandonada, preserve os arquivos usuais do projeto de romance, além de `completion-brief.md`, `source-manifest.json`, dos registros de evidências/intenção/versões/ramificações, de `rights-and-publication.md`, `completion-provenance.md`, `completion-state.json` e do controle de conclusão. Obras com direitos desconhecidos ou não autorizados usam por padrão o modo `private-only`/`research`; não publique sua prosa diretamente.

Não coloque o projeto diretamente no ZIP de skills. Entregue uma pasta de projeto separada ou um ZIP limpo:

1. Primeiro verifique se há informações sensíveis sobre pessoas reais, fontes privadas, credenciais, texto de origem não autorizado ou rascunhos que não devam ser compartilhados.
2. Execute `snapshot_project.py`, `deep_consistency.py` e `chapter_gate.py` do sistema existente; inclua os resultados na nota de entrega.
3. Identifique claramente o último capítulo canônico, os capítulos em rascunho inacabados, a autoridade do autor para sobrepor decisões e os riscos conhecidos em `project-brief.md`.
4. Após importar, o destinatário deve ler a bíblia narrativa, o estado atual, a linha do tempo, o registro do leitor, os fios da trama, o registro de entidades e o resumo mais recente antes de continuar a história.
