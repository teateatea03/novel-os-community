# Política de segurança e privacidade

<!-- language-navigation -->

[繁體中文](SECURITY.zh-TW.md) | [English](SECURITY.md) | [日本語](SECURITY.ja.md) | [한국어](SECURITY.ko.md) | [Español](SECURITY.es.md) | [Français](SECURITY.fr.md) | [Deutsch](SECURITY.de.md) | **Português**

## Versões suportadas

As correções de segurança e privacidade destinam-se ao ramo `main` atual.

## Comunicação de problemas

Não abra issues públicas contendo dados pessoais, credenciais, manuscritos privados, logs de sessões, material narrativo inédito ou registos de investigação. Utilize a comunicação privada de vulnerabilidades quando estiver ativada. Se não houver contacto privado disponível, abra uma issue pedindo ao responsável um canal privado de comunicação, sem incluir detalhes sensíveis.

## Limite das contribuições

Os colaboradores devem enviar apenas material que tenham o direito de partilhar. Nunca inclua nos commits:

- chaves de API, palavras-passe, tokens, chaves SSH, cookies, ficheiros de ambiente ou caminhos de dispositivos;
- conversas privadas, memórias de agentes, logs, cópias de segurança ou exportações;
- ficção inédita, estado de sessões interativas ou dados de investigação pessoal;
- dados sobre pessoas reais inadequados para redistribuição pública.

## Antes de publicar uma alteração

1. Reveja `git diff --cached --name-only`.
2. Execute `python3 scripts/privacy_scan.py .`.
3. Inspecione manualmente cada ocorrência; não suprima uma ocorrência sem motivo escrito.
4. Confirme que cada ficheiro incluído pertence ao sistema reutilizável, não a um projeto ativo ou conjunto de dados privado.

## Processo de divulgação

Se material privado for incluído num commit ou exposto, interrompa a distribuição, torne o repositório privado se necessário, revogue as credenciais afetadas, preserve evidências para revisão e remova o material dos objetos Git atuais e históricos antes de reabrir o acesso.
