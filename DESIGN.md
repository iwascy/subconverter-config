# 节点命名与分组设计

## 节点命名协议

所有可用节点只分为机场节点和个人服务器节点：

```text
AIRPORT-<EXIT>-<SOURCE>-<ID>
SELF-<EXIT>-DIRECT-<NAME>
SELF-<EXIT>-VIA-<ENTRY>-<NAME>
```

`EXIT` 是实际出口地区，使用大写地区码，例如 `HK`、`SG`、`US`。机场节点的 `SOURCE` 是稳定来源标识，`ID` 是来源内编号。

个人服务器节点直接连接即可使用。`VIA` 仅描述服务器端已经完成的入口到出口路径，不表示客户端链式代理：

```text
AIRPORT-HK-LINGYUN-01
SELF-HK-DIRECT-SHOII-Zouter-HK2-v4
SELF-SG-VIA-HK2-SHOII-Zouter-v4-SS
```

最后一个节点表示客户端连接香港 HK2 入口，但最终从新加坡出口；它只能进入 SG 分组。

## 分组规则

节点池和地区组只使用锚定前缀：

```text
SELECT:          ^(AIRPORT|SELF)-
HK:              ^(AIRPORT|SELF)-HK-
SG:              ^(AIRPORT|SELF)-SG-
Self-Hosted-HK: ^SELF-HK-
Self-Hosted-SG: ^SELF-SG-
Self-Hosted-US: ^SELF-US-
```

不扫描名称后半段的地区关键字，不保留旧名称兼容规则。名称后半段的 `VIA-HK2` 不会改变 `SELF-SG-*` 的 SG 出口归属。

## Sub-Store 重命名

所有 31 个子订阅均配置 `Regex Rename Operator`。机场节点按来源名称中的国家和编号转换，个人服务器节点按实际出口转换。无法识别地区的机场节点使用：

```text
AIRPORT-UN-<SOURCE>-<ORIGINAL>
```

`UN` 节点不会进入任何地区组，便于发现新地区而不是错误分组。机场的流量、到期时间和防失联提示通过独立元数据过滤器移除。迁移只修改展示名称、无用信息过滤和重复组合成员，不修改订阅源与节点连接参数。

## 迁移策略

1. 新增节点必须输出 `AIRPORT-*` 或 `SELF-*`。
2. Sub-Store 负责所有命名，客户端配置不再猜测节点类型和地区。
3. 正式地区组不接受 `UN` 或未规范名称。
4. 客户端不定义 `EXIT`、`TRANSIT` 或 `RELAY-CHAIN` 分组。

完整迁移映射记录在 `scripts/substore-canonical-names.jq`。

## AI 分流

Claude、Gemini、Grok 和 Perplexity 优先进入各自的专用策略组。OpenAI、ChatGPT、OpenCode 以及其他已收录但没有独立策略组的 AI 服务随后进入 `AI` 兜底组。规则只收录明确的 AI 服务域名，不使用整个 `.ai` 顶级域名作为通配规则。

`AI` 直接提供地区组和全部规范节点，避免必须先进入 `SELECT` 才能选择具体节点。Clash 使用 `ALL_PROVIDER`，Loon 使用 `Filter-All`，subconverter 使用 `^(AIRPORT|SELF)-`，三种配置共享相同的节点边界。

## 变更历史

### 2026-07-30 - 引入出口优先命名协议

**变更内容**：新增 `SELF-<EXIT>-DIRECT/VIA-*` 命名协议，并同步 Clash、Loon 与 subconverter 分组正则。

**变更理由**：原规则扫描名称任意位置的地区码，转发节点同时包含 `HK`、`SG` 时会错分或漏分。

**影响范围**：自建节点筛选、地区自动测速组、中转组和 Sub-Store 节点展示名称。

**决策依据**：出口地区决定代理用途和内容可用性；入口地区仅是链路属性，因此出口必须成为可机器解析的固定前缀。

### 2026-07-30 - 全量规范 Sub-Store 节点

**变更内容**：将全部机场和个人服务器节点规范为 `AIRPORT-*`、`SELF-*`，删除客户端链式代理组和历史兼容正则。

**变更理由**：当前转发已在服务器端完成，客户端只需要按完整节点的实际出口分组。

**影响范围**：31 个 Sub-Store 子订阅、主组合订阅、subconverter、Clash 和 Loon 配置。

**决策依据**：让 Sub-Store 成为节点角色和地区的唯一命名来源，客户端只解析固定字段，避免多套模糊规则继续分叉。

### 2026-08-11 - 引入统一 AI 兜底分流

**变更内容**：将 OpenCode 加入 AI 规则，统一 Clash、Loon 和 subconverter 的 `AI` 策略组，并把专用厂商规则置于 AI 兜底规则之前。

**变更理由**：未单独分类的 AI 服务原本会落入 `Final`，而不同客户端还混用 `ChatGPT`、`OpenAI` 和 `AI` 名称。

**影响范围**：AI 规则源、subconverter 配置、Clash/Loon 模板及实际客户端配置。

**决策依据**：专用策略保持独立控制，统一兜底组承接其余 AI 流量；直接暴露地区组和全部节点，减少策略选择层级。
