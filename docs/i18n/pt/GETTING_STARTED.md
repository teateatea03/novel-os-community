# Configuração local e instalação portátil

<!-- language-navigation -->

[繁體中文](../zh-TW/GETTING_STARTED.md) | [English](../../GETTING_STARTED.md) | [日本語](../ja/GETTING_STARTED.md) | [한국어](../ko/GETTING_STARTED.md) | [Español](../es/GETTING_STARTED.md) | [Français](../fr/GETTING_STARTED.md) | [Deutsch](../de/GETTING_STARTED.md) | **Português**

Este guia abrange o ambiente de execução local e o pacote portátil. A utilização e a redistribuição são regidas por [LICENSE](LICENSE.md); os detalhes de declaração comercial e pagamento estão em [COMMERCIAL_TERMS.md](COMMERCIAL_TERMS.md).

## Cobertura de idiomas

A documentação pública está disponível em chinês tradicional, inglês, japonês, coreano, espanhol, francês, alemão e português. As habilidades de execução, os modelos e as suas referências técnicas mantêm atualmente o idioma original. Esta versão da documentação em oito idiomas não traduz o ambiente de execução.

## Escolher um modo

- **Ferramentas locais:** Python 3.10+ e ficheiros UTF-8 persistentes. A validação principal, a criação de estruturas de projeto e os testes utilizam a biblioteca padrão
- **Execução de agentes:** o anterior mais um anfitrião capaz de carregar pacotes `SKILL.md` irmãos, ler/escrever ficheiros de projeto e executar Python. Registe `novel-operating-system` como ponto de entrada
- **Modo documental/manual:** um anfitrião sem shell nem ficheiros persistentes pode seguir os modelos, mas não pode afirmar que executou controlos CLI, instalação ou estado duradouro

O Novel OS não inclui um modelo, uma conta de API, um serviço web ou um manuscrito privado. Existem 18 diretórios-fonte de habilidades: 17 habilidades de execução instaláveis (um coordenador e 16 colaboradores) e o exportador.

## Verificar uma cópia nova

Execute estes comandos a partir da raiz do repositório num shell POSIX:

```sh
python3 --version
python3 scripts/privacy_scan.py .
python3 scripts/validate_json.py .
python3 -m compileall -q skills scripts
python3 scripts/run_tests.py
```

Utilize um diretório de projeto privado separado para trabalho real. Não copie manuscritos ou bases de dados existentes para esta cópia. Para um primeiro projeto sintético, utilize o exemplo `mktemp` do [README](README.md). Um `--root` explícito tem prioridade sobre `NOVEL_PROJECTS_ROOT`; sem nenhum deles, os inicializadores utilizam `~/.novel-os/novels`.

## Construir e testar um pacote local

Estes comandos utilizam apenas ficheiros do repositório e diretórios temporários. Não envolvem uploads, modelos em produção, chaves de API ou investigação externa. A saída da construção deve ficar fora da cópia de fontes para evitar que conteúdos gerados sejam incluídos acidentalmente nos commits.

```sh
BUNDLE_WORK="$(mktemp -d)"
INSTALL_WORK="$(mktemp -d)"
EXPORTER="skills/novel-system-exporter/scripts"

python3 "$EXPORTER/build_novel_os_bundle.py" refresh \
  --source-root skills --bundle-root "$BUNDLE_WORK"
python3 "$EXPORTER/build_novel_os_bundle.py" verify \
  --bundle-root "$BUNDLE_WORK/payload"
python3 scripts/privacy_scan.py "$BUNDLE_WORK/payload"
python3 "$EXPORTER/verify_novel_os.py" --profile full \
  --bundle-root "$BUNDLE_WORK/payload" --output "$BUNDLE_WORK/verification.json"
python3 "$EXPORTER/install_novel_os.py" \
  --bundle-root "$BUNDLE_WORK/payload" --target "$INSTALL_WORK" --smoke-test
```

O perfil completo de verificação executa um piloto sintético de ficção longa com mais de 100 mil caracteres, além das baterias de regressão locais. É uma verificação de correção local, não uma certificação de qualidade de modelos em produção ou de múltiplas plataformas. O instalador recusa sobrescrever habilidades existentes salvo se `--upgrade` for explicitamente fornecido; as atualizações criam cópias de segurança locais. Não utilize um diretório de habilidades ativo no primeiro teste.

Para criar um arquivo depois de estas verificações passarem:

```sh
python3 "$EXPORTER/build_novel_os_bundle.py" build \
  --bundle-root "$BUNDLE_WORK/payload" \
  --output "$BUNDLE_WORK/novel-os-review.zip"
```

O manifesto lista e calcula hashes de todos os ficheiros empacotados, incluindo as oito versões linguísticas da licença do projeto, das condições comerciais e do guia de terceiros, além do aviso Humanizer-zh inalterado dentro da respetiva habilidade adaptada. Mantenha esses avisos com o arquivo e a instalação. O instalador conserva os avisos do projeto em `novel-operating-system/DISTRIBUTION_NOTICES/` em vez de sobrescrever a licença raiz do anfitrião.

## Funcionalidades opcionais

Instale apenas o que o anfitrião necessita, num ambiente isolado:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-optional.txt
```

O ficheiro lista intervalos de compatibilidade, não um bloqueio reproduzível de versões. Se ativar uma integração opcional, escolha/teste a versão exata e reveja as condições originais. Nenhuma dependência opcional é necessária para o percurso principal acima.

- NetworkX ativa algoritmos de grafos/GraphML opcionais; Graphify é instalado separadamente para os seus exportadores adicionais
- PyYAML ativa a entrada YAML de projeção NPC; MCP e o respetivo servidor externo do Instagram são integrações opcionais
- A revisão independente por modelo exige uma alternativa específica do anfitrião para `minis-model-use` fora do anfitrião original. Se indisponível, registe-a como não executada
- `lieflat-less-ai-tone` não está incluído. A sua fonte/licença deve ser verificada separadamente; sem ele, utilize o fluxo integrado de voz humana e registe a etapa adicional como não executada

Consulte [THIRD_PARTY.md](THIRD_PARTY.md), a [compatibilidade de plataformas](../../../skills/novel-system-exporter/references/platform-compatibility.pt.md) e o [contrato do adaptador do anfitrião](../../../skills/novel-system-exporter/references/host-adapter-contract.pt.md). Os testes de Windows/anfitrião nativo e serviços opcionais são trabalho de aceitação separado; um teste básico em Linux não os verifica.
