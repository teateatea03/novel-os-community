# Componentes e referências de terceiros

<!-- language-navigation --> [繁體中文](THIRD_PARTY.zh-TW.md) | [English](THIRD_PARTY.md) | [日本語](THIRD_PARTY.ja.md) | [한국어](THIRD_PARTY.ko.md) | [Español](THIRD_PARTY.es.md) | [Français](THIRD_PARTY.fr.md) | [Deutsch](THIRD_PARTY.de.md) | **Português**

O Novel OS contém código e documentação originais do projeto que interoperam com projetos de terceiros ou os descrevem. Salvo indicação explícita num ficheiro, os projetos de terceiros **não estão incorporados** neste repositório.

## Dependências de execução ou opcionais

| Componente | Utilização | Licença / fonte |
|---|---|---|
| Python | Execução (3.10+) | Python Software Foundation License |
| NetworkX | Algoritmos de grafos e exportação GraphML | BSD-3-Clause; https://networkx.org/ |
| PyYAML | Entrada de estado YAML para o utilitário de projeção NPC | MIT; https://pyyaml.org/ |
| MCP Python SDK | Cliente MCP local opcional do Instagram | MIT; https://github.com/modelcontextprotocol/python-sdk |
| Graphify (`graphifyy`) | Interoperabilidade opcional de análise/exportação de grafos | O projeto original indica Apache-2.0 e inclui material com licença MIT; https://github.com/Graphify-Labs/graphify |

O servidor MCP anónimo do Instagram e o Instaloader são componentes opcionais separados e não estão incluídos aqui. Os operadores são responsáveis pela sua instalação e pelo cumprimento das condições da plataforma, da legislação aplicável, dos controlos de robots/acesso e das restrições do projeto que permitem apenas dados públicos.

## Referências de investigação

A documentação contém ligações para artigos, especificações, livros, ferramentas e projetos públicos como citações de investigação. As ligações e descrições não incorporam o código nem o texto dessas obras no Novel OS. Se o material contribuído adaptar código ou texto em vez de apenas citar ideias, a contribuição deve identificar a fonte exata, a licença, as modificações e a atribuição necessária.

## Material adaptado incluído nesta distribuição

- **Humanizer-zh**, copyright (c) 2026 歸藏, MIT: [fonte original no commit f4518a8eab97b8bfebc66a89d34320a89bef6930](https://github.com/op7418/Humanizer-zh/tree/f4518a8eab97b8bfebc66a89d34320a89bef6930)
  - Adaptação: `skills/novel-human-voice-editor/references/humanizer-zh-checkpoints.md` traduz e condensa os 31 pontos de revisão editorial para chinês tradicional e acrescenta regras de preservação e conflito específicas da ficção
  - É conservado o [aviso MIT original](skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt), verificado contra esse commit original exato
  - O aviso acompanha a habilidade nas fontes, no pacote portátil e no ambiente instalado. Aplica-se ao material original de terceiros, **não** ao Novel OS no seu conjunto; o material criado pelo projeto é regido separadamente por `LICENSE`

## Integrações externas do anfitrião não distribuídas aqui

`lieflat-less-ai-tone` é uma etapa de edição opcional fornecida pelo anfitrião, não uma das 17 habilidades de execução. O seu documento de integração regista uma revisão externa, mas este repositório não contém uma URL/licença original verificada nem a sua implementação. Não a descarregue, incorpore ou afirme que foi executada automaticamente. Se estiver ausente, mantenha o fluxo integrado de voz humana e registe esta etapa adicional como não executada. Verifique separadamente a proveniência e o licenciamento antes de instalar ou distribuir.

O adaptador de revisão independente `minis-model-use` exige o seu anfitrião original. Outros anfitriões devem fornecer uma alternativa explicitamente configurada ou registar a revisão independente por modelo como não executada. Os testes de regressão locais não utilizam modelos em produção nem serviços Graphify, MCP ou Instagram.

## Limite das dependências

Os pacotes opcionais acima não são incluídos nem instalados pela distribuição principal. As obrigações das respetivas licenças permanecem com as suas distribuições; reveja a versão original exata antes de ativar uma integração ou redistribuir um pacote combinado. Os testes principais funcionam sem estas dependências. Este inventário é um auxílio à revisão, não aconselhamento jurídico.
