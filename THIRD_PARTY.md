# Third-party components and references

<!-- language-navigation --> [繁體中文](THIRD_PARTY.zh-TW.md) | **English** | [日本語](THIRD_PARTY.ja.md) | [한국어](THIRD_PARTY.ko.md) | [Español](THIRD_PARTY.es.md) | [Français](THIRD_PARTY.fr.md) | [Deutsch](THIRD_PARTY.de.md) | [Português](THIRD_PARTY.pt.md)

Novel OS contains original project code and documentation that interoperates with, or discusses, third-party projects. Unless a file explicitly says otherwise, third-party projects are **not vendored** into this repository.

## Runtime or optional dependencies

| Component | Use | License / source |
|---|---|---|
| Python | Runtime (3.10+) | Python Software Foundation License |
| NetworkX | Graph algorithms and GraphML export | BSD-3-Clause; https://networkx.org/ |
| PyYAML | YAML state input for the NPC projection utility | MIT; https://pyyaml.org/ |
| MCP Python SDK | Optional local Instagram MCP client | MIT; https://github.com/modelcontextprotocol/python-sdk |
| Graphify (`graphifyy`) | Optional graph analysis/export interoperability | Upstream reports Apache-2.0 and includes MIT license material; https://github.com/Graphify-Labs/graphify |

The anonymous Instagram MCP server and Instaloader are separate optional components and are not included here. Operators are responsible for installing them and following platform terms, applicable law, robots/access controls, and the project's public-data-only constraints.

## Research references

Documentation links to articles, specifications, books, tools, and public projects as research citations. Links and descriptions do not incorporate those works' code or prose into Novel OS. If contributed material adapts code or text rather than merely citing ideas, the contribution must identify the exact source, license, modifications, and required attribution.

## Adapted material included in this distribution

- **Humanizer-zh**, copyright (c) 2026 歸藏, MIT: [upstream source at commit f4518a8eab97b8bfebc66a89d34320a89bef6930](https://github.com/op7418/Humanizer-zh/tree/f4518a8eab97b8bfebc66a89d34320a89bef6930)
  - Adaptation: `skills/novel-human-voice-editor/references/humanizer-zh-checkpoints.md` translates/condenses the 31 editorial checkpoints into Traditional Chinese and adds fiction-specific preservation and conflict rules
  - Retained [upstream MIT notice](skills/novel-human-voice-editor/THIRD_PARTY_LICENSES/Humanizer-zh-MIT.txt), verified against that exact upstream commit
  - The notice travels with the skill in source, portable bundle, and installed runtime. It applies to the upstream material, **not** to Novel OS as a whole; project-authored material is governed separately by `LICENSE`

## External host integrations not distributed here

`lieflat-less-ai-tone` is an optional host-supplied editing pass, not one of the 17 runtime skills. Its integration document records an external revision, but this repository does not contain a verified upstream URL/license or its implementation. Do not fetch, vendor, or claim it ran automatically. If absent, retain the built-in human-voice workflow and record this additional pass as not run. Verify provenance and licensing separately before installing or distributing it.

The `minis-model-use` independent-review adapter requires its original host. Other hosts must supply an explicitly configured replacement or record independent model review as not run. Local regression tests do not exercise live models, Graphify, MCP, or Instagram services.

## Dependency boundary

The optional packages above are not bundled or installed by the core distribution. Their license obligations remain with their respective distributions; review the exact upstream version before enabling an integration or redistributing a combined package. Core tests run without these dependencies. This inventory is a review aid, not legal advice.
