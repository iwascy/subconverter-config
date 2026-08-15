def rename_operator($rules):
  {
    "type": "Regex Rename Operator",
    "args": $rules,
    "customName": "Canonical node naming",
    "id": "20260730.001",
    "disabled": false
  };

def metadata_filter:
  {
    "type": "Regex Filter",
    "args": {
      "keep": false,
      "regex": [
        "剩余流量",
        "距离下次重置",
        "套餐到期",
        "防失联",
        "超时请更新",
        "官网",
        "群",
        "频道"
      ]
    },
    "customName": "Canonical metadata filter",
    "id": "20260730.002",
    "disabled": false
  };

def set_rename($subscription; $rules):
  if .name == $subscription then
    .process |= (
      map(
        if .type == "Quick Setting Operator" then
          .args.useless = "ENABLED"
        else
          .
        end
      )
      | map(select(.type != "Regex Rename Operator"))
      + [rename_operator($rules)]
    )
  else
    .
  end;

def exact_name($name):
  [{"expr": "^.*$", "now": $name}];

def airport_rules($source):
  [
    {"expr": "^.*香港([0-9]+).*$", "now": "AIRPORT-HK-\($source)-$1"},
    {"expr": "^.*新加坡([0-9]+).*$", "now": "AIRPORT-SG-\($source)-$1"},
    {"expr": "^.*马来西亚([0-9]+).*$", "now": "AIRPORT-MY-\($source)-$1"},
    {"expr": "^.*台湾([0-9]+).*$", "now": "AIRPORT-TW-\($source)-$1"},
    {"expr": "^.*日本([0-9]+).*$", "now": "AIRPORT-JP-\($source)-$1"},
    {"expr": "^.*美国([0-9]+).*$", "now": "AIRPORT-US-\($source)-$1"},
    {"expr": "^.*韩国([0-9]+).*$", "now": "AIRPORT-KR-\($source)-$1"},
    {"expr": "^.*澳大利亚.*$", "now": "AIRPORT-AU-\($source)-01"},
    {"expr": "^.*菲律宾.*$", "now": "AIRPORT-PH-\($source)-01"},
    {"expr": "^.*印度尼西亚.*$", "now": "AIRPORT-ID-\($source)-01"},
    {"expr": "^.*印尼.*$", "now": "AIRPORT-ID-\($source)-01"},
    {"expr": "^.*印度.*$", "now": "AIRPORT-IN-\($source)-01"},
    {"expr": "^.*英国.*$", "now": "AIRPORT-UK-\($source)-01"},
    {"expr": "^.*土耳其.*$", "now": "AIRPORT-TR-\($source)-01"},
    {"expr": "^.*法国.*$", "now": "AIRPORT-FR-\($source)-01"},
    {"expr": "^.*尼日利亚.*$", "now": "AIRPORT-NG-\($source)-01"},
    {"expr": "^.*加拿大.*$", "now": "AIRPORT-CA-\($source)-01"},
    {"expr": "^.*俄罗斯.*$", "now": "AIRPORT-RU-\($source)-01"},
    {"expr": "^.*巴基斯坦.*$", "now": "AIRPORT-PK-\($source)-01"},
    {"expr": "^.*荷兰.*$", "now": "AIRPORT-NL-\($source)-01"},
    {"expr": "^(?!AIRPORT-)(.*)$", "now": "AIRPORT-UN-\($source)-$1"}
  ];

def set_airport($subscription; $source):
  set_rename($subscription; airport_rules($source))
  | if .name == $subscription then
      .process |= (
        map(select(.customName != "Canonical metadata filter"))
        + [metadata_filter]
      )
    else
      .
    end;

def hk_v2_rules($source):
  [
    {"expr": "^(?:EXIT-)?BRDE-(.*?)(?:-落地)?$", "now": "SELF-DE-DIRECT-\($source)-BRDE-$1"},
    {"expr": "^(?:EXIT-)?WWHK-(.*?)(?:-落地)?$", "now": "SELF-HK-DIRECT-\($source)-WWHK-$1"},
    {"expr": "^(?:EXIT-)?LYUK-(.*?)(?:-落地)?$", "now": "SELF-UK-DIRECT-\($source)-LYUK-$1"},
    {"expr": "^(?:EXIT-)?LYJP-(.*?)(?:-落地)?$", "now": "SELF-JP-DIRECT-\($source)-LYJP-$1"},
    {"expr": "^(?:EXIT-)?AKTW-(.*?)(?:-落地)?$", "now": "SELF-TW-DIRECT-\($source)-AKTW-$1"},
    {"expr": "^(?:EXIT-)?AKHK-(.*?)(?:-落地)?$", "now": "SELF-HK-DIRECT-\($source)-AKHK-$1"},
    {"expr": "^(?:EXIT-)?HINET-(.*?)(?:-落地)?$", "now": "SELF-TW-DIRECT-\($source)-HINET-$1"},
    {"expr": "^(?:EXIT-)?USAK-(.*?)(?:-落地)?$", "now": "SELF-US-DIRECT-\($source)-USAK-$1"},
    {"expr": "^(?:EXIT-)?JPRF-(.*?)(?:-落地)?$", "now": "SELF-JP-DIRECT-\($source)-JPRF-$1"},
    {"expr": "^(?!SELF-)(.*)$", "now": "SELF-UN-DIRECT-\($source)-$1"}
  ];

.subs |= map(
  set_airport("忍者云"; "NINJA")
  | set_airport("凌云50G"; "LINGYUN")
  | set_airport("TRANSIT-忍者云"; "NINJA-ALT")
  | set_airport("TRANSIT-凌云"; "LINGYUN-ALT")
  | set_rename("HKv2-香港落地"; hk_v2_rules("HKV2"))
  | set_rename("Exit-香港落地"; hk_v2_rules("HKV2-ALT"))
  | set_rename("Oracle-SG-SS"; [
      {"expr": "^(?!SELF-)(.*)$", "now": "SELF-SG-DIRECT-ORACLE-SS-$1"}
    ])
  | set_rename("Bagevm-vless"; exact_name("SELF-US-DIRECT-BAGEVM-LA2"))
  | set_rename("马硕-Vless-落地"; exact_name("SELF-US-DIRECT-BWG-MASHUO"))
  | set_rename("BWG-公共"; [
      {"expr": "^.*public.*$", "now": "SELF-US-DIRECT-BWG-PUBLIC"},
      {"expr": "^.*bak1.*$", "now": "SELF-US-DIRECT-BWG-BAK1"},
      {"expr": "^.*bxnskzh6.*$", "now": "SELF-US-DIRECT-BWG-BXNSKZH6"},
      {"expr": "^(?!SELF-)(.*)$", "now": "SELF-US-DIRECT-BWG-$1"}
    ])
  | set_rename("BWG-洛杉矶备用"; exact_name("SELF-US-DIRECT-BWG-BXNSKZH6"))
  | set_rename("香港-Yecao-Self-hosted"; exact_name("SELF-HK-DIRECT-YECAO"))
  | set_rename("香港-Yecao-Self-hosted-IPV6"; exact_name("SELF-HK-DIRECT-YECAO-v6"))
  | set_rename("LightLayer HK Jing"; exact_name("SELF-HK-DIRECT-LIGHTLAYER-JING"))
  | set_rename("LightLayer HK"; exact_name("SELF-HK-DIRECT-LIGHTLAYER"))
  | set_rename("LightLayer HK Direct"; exact_name("SELF-HK-DIRECT-LIGHTLAYER-ALT"))
  | set_rename("LightLayer HK Hinet"; exact_name("SELF-HK-DIRECT-LIGHTLAYER-HINET"))
  | set_rename("LightLayer HK Jing-copy6112"; exact_name("SELF-HK-DIRECT-LIGHTLAYER-JING-ALT"))
  | set_rename("SG-Lightlayer"; exact_name("SELF-SG-VIA-HK-LIGHTLAYER"))
  | set_rename("weiheng-hinet"; exact_name("SELF-TW-DIRECT-WEIHENG-HINET"))
  | set_rename("Oracle-SG-Yecaoo"; exact_name("SELF-SG-DIRECT-ORACLE-YECAO"))
  | set_rename("SG-Oracle"; [
      {"expr": "^.*v6.*$", "now": "SELF-SG-DIRECT-ORACLE-v6"},
      {"expr": "^.*v4.*$", "now": "SELF-SG-DIRECT-ORACLE-v4"},
      {"expr": "^(?!SELF-)(.*)$", "now": "SELF-SG-DIRECT-ORACLE-$1"}
    ])
  | set_rename("Shoii-Zouter-HK"; exact_name("SELF-HK-DIRECT-SHOII-Zouter"))
  | set_rename("Shoii-Zouter-HK-v4"; exact_name("SELF-HK-DIRECT-SHOII-Zouter-v4"))
  | set_rename("Shoii-Zouter-HK-v6"; exact_name("SELF-HK-DIRECT-SHOII-Zouter-v6"))
  | set_rename("Shoii-Zouter-HK-SG-v4"; exact_name("SELF-SG-VIA-HK-SHOII-Zouter-v4"))
  | set_rename("Shoii-Zouter-HK-SG-v6"; exact_name("SELF-SG-VIA-HK-SHOII-Zouter-v6"))
  | set_rename("Shoii-Zouter-HK2-v4-Direct"; exact_name("SELF-HK-DIRECT-SHOII-Zouter-HK2-v4"))
  | set_rename("Shoii-Zouter-HK2-v6-Direct"; exact_name("SELF-HK-DIRECT-SHOII-Zouter-HK2-v6"))
  | set_rename("Shoii-Zouter-HK2-v4-SG-SS"; exact_name("SELF-SG-VIA-HK2-SHOII-Zouter-v4-SS"))
  | set_rename("Shoii-Zouter-HK2-v6-SG-SS"; exact_name("SELF-SG-VIA-HK2-SHOII-Zouter-v6-SS"))
)
| .collections |= map(
    if .name == "忍者云-凌云-Vless-落地转发-copy1485" then
      .subscriptions |= map(select(. != "BWG-洛杉矶备用"))
    else
      .
    end
  )
