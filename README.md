# subconverter-config

用于生成 Clash、Loon 和 subconverter 分流配置的个人配置仓库。

## 主要文件

- `config.ini`：通用 subconverter 配置。
- `AI.list` / `AI.yaml`：MetaCubeX AI 兜底规则的本地兼容快照；Clash 与 subconverter 直接读取上游，Loon 使用转换后的原生规则。
- `relay.ini`：使用规范节点名称的完整分流配置，不包含客户端链式代理。
- `template-clash-dialer-proxy.yaml`：Clash Meta 本地模板。
- `template-loon-dialer-proxy.conf`：Loon 本地模板。
- `scripts/substore-canonical-names.jq`：全部 Sub-Store 节点的命名迁移。
- `scripts/reorganize_substore_catalog.py`：规范 Sub-Store 子订阅目录并维护集合成员引用。
- `scripts/audit_substore_names.py`：逐个审计 Sub-Store 子订阅的实际输出名称。
- `DESIGN.md`：节点命名协议、分组规则和迁移说明。

## 校验

节点分组正则可使用 Node.js 内置测试运行：

```bash
node --test tests/node-group-regex.test.js
```

## AI 规则来源

AI 分流统一使用 [MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat/tree/meta/geo/geosite)：Claude → `anthropic`，Gemini → `google-gemini`，Grok → `xai`，Perplexity → `perplexity`；专用规则之后使用 `category-ai-!cn` 进入 AI 组，覆盖 ChatGPT/OpenAI、Sora、Cursor、Copilot 等服务。保留 OpenAI 独立规则源的旧配置使用 `openai`，仍指向 AI 组。

Clash 使用 `behavior: domain`，Loon 使用 `rules/loon/*.list` 原生规则快照（转换源为 MetaCubeX），subconverter 使用 `clash-domain:`。上游 YAML 已实测可访问；本地 `.list` 和 `rules/*.yaml` 保留 classical 格式快照，`AI.yaml` 保留 domain 格式，快照日期见文件头。

`google-gemini` 包含 AI Studio、NotebookLM、Jules、Antigravity 等 Google AI 产品；综合 AI 集按上游完整接入，分类范围可能包含配套网站，不代表这些服务均需要代理。

Muse AI（`muse.ai` 及其子域名）通过显式 `DOMAIN-SUFFIX` 规则进入 AI 分组；Clash、Loon 与 subconverter 配置均保留此规则，远程 AI 规则集也已包含该域名。
