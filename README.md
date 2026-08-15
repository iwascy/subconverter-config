# subconverter-config

用于生成 Clash、Loon 和 subconverter 分流配置的个人配置仓库。

## 主要文件

- `config.ini`：通用 subconverter 配置。
- `AI.list` / `AI.yaml`：在专用厂商规则之后匹配的 AI 服务兜底规则。
- `relay.ini`：使用规范节点名称的完整分流配置，不包含客户端链式代理。
- `template-clash-dialer-proxy.yaml`：Clash Meta 本地模板。
- `template-loon-dialer-proxy.conf`：Loon 本地模板。
- `scripts/substore-canonical-names.jq`：全部 Sub-Store 节点的命名迁移。
- `scripts/audit_substore_names.py`：逐个审计 Sub-Store 子订阅的实际输出名称。
- `DESIGN.md`：节点命名协议、分组规则和迁移说明。

## 校验

节点分组正则可使用 Node.js 内置测试运行：

```bash
node --test tests/node-group-regex.test.js
```
