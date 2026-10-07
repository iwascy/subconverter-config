# Loon 原生规则

此目录由 `scripts/convert_loon_rules.py` 生成，规则格式为
`DOMAIN-SUFFIX,example.com`，可直接用于 Loon 的 `[Remote Rule]`。
Clash 的 `payload:`、`+.example.com` 和 `type=domain` 不能直接当作此格式使用。

转换保留精确域名、域名后缀、IPv4/IPv6、ASN 和 `no-resolve` 的语义，
移除 iOS 不支持的 `PROCESS-NAME`；未知格式会报错，空规则集不再订阅。
模板中的 `# source:` 注释记录原始上游，重新生成时仍从上游获取最新规则。

安装 Python 3 和 PyYAML 后，在仓库根目录更新：

```sh
python3 scripts/convert_loon_rules.py template-loon-dialer-proxy.conf \
  --output template-loon-dialer-proxy.conf \
  --rules-dir rules/loon \
  --base-url https://raw.githubusercontent.com/iwascy/subconverter-config/main/rules/loon
python3 -m unittest discover -s tests -v
```

将模板和生成的 `.list` 文件一起发布后，客户端更新配置及远程规则即可。
这些文件是生成时的快照，更新上游后需重新运行转换命令。

部署自有服务器时，可将现有私有配置作为输入，使用单独的输出文件、规则目录
和对应的 HTTPS `--base-url`。转换只修改 `[Remote Rule]`，保留订阅、节点、
策略和本地规则；先发布规则并验证下载，再替换配置。不要提交含订阅密钥的配置。
