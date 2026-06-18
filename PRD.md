# Amazon Sorftime Product Selection Research PRD

## 1. 背景

Amazon 运营选品需要把市场容量、竞争强度、利润空间、差异化机会、VOC 痛点、关键词入口和风险放在同一个判断框架内。普通市场报告容易停留在概览，页面全案调研又容易过早进入 Listing、图片和 A+ 执行。本 skill 收敛为“选品决策优先”，用 Sorftime MCP 全量数据作为默认主数据源。

## 2. 目标

- 建立一个通用、脱敏、可复用、可执行闭环的 Amazon 选品与类目调研决策 skill。
- 基于 Sorftime MCP 输出可验证的 `enter/cautious/weak/no-enter` 判断；blocked 状态单独交付。
- 输出 `dist/product_selection_report.html`、`dist/product_selection_data.json` 和 `dist/source_manifest.json`。
- 为下游 Listing、图片、A+ skill 提供 brief，但不生成最终页面内容。
- 支持 GitHub public-safe 模板发布、本地隐私扫描和 `private_internal` 真实 MCP 分析。

## 3. 非目标

- 不把真实 Sorftime MCP 配置、token、原始响应、真实报告或私有数据发布到 GitHub。
- 不修改 Amazon Ops APP、workflow、SOP、Excel 模板或 UI。
- 不使用浏览器、公开网络、旧文件或人工表格作为默认主证据。
- 不提交 `dist/*.html`、`dist/*.json`、真实导出、私有词表或凭证文件。

## 4. 用户场景

- 用户给出关键词，想判断是否值得进入。
- 用户给出类目，想比较市场容量、竞争和利润机会。
- 用户给出 ASIN，想判断该产品方向是否适合跟进或差异化开发。
- 用户给出产品想法，想知道应从哪个人群、场景、规格或关键词切入。
- 开发者要用 public-safe fixture 测试完整 normalize、render、validate、privacy scan 闭环。

## 5. 数据源原则

- 默认主数据源只使用 Sorftime MCP / Sorftime 全量数据接口。
- 数据不可用时必须阻断，不得编造数据或改用未授权来源。
- 所有结论必须区分事实、基于数据的推断、假设和缺失数据。
- 公开样例只能使用 public-safe template sample。

## 6. 数据模式

| 模式 | 用途 | 规则 |
|---|---|---|
| `public_safe_real_world` | GitHub 默认测试模式 | 可保留公开世界类目名和通用关键词；竞品、ASIN、品牌必须匿名。 |
| `strict_anonymized` | 严格匿名测试 | 类目、关键词、产品想法、竞品标识全部样例化。 |
| `private_internal` | 本地真实运营分析 | 允许接入真实 Sorftime MCP / Sorftime-compatible MCP，允许使用真实市场数据、类目、关键词、竞品、ASIN 和品牌；不得提交 GitHub。 |

`private_internal` 规则：

- 允许输出真实选品分析报告到本地 `dist` 或指定 private output 目录。
- 不允许写入 fixtures、examples 或 public-safe 文档。
- 不允许把 token、cookie、账号、endpoint secret 或 MCP 密钥写入报告、manifest 或公开文档。
- 真实配置建议使用 `private_config.local.json`，真实 token 只能通过环境变量读取，例如 `SORFTIME_MCP_TOKEN`。

允许公开样例词：

- `Best Sellers in On-Ear Headphones`
- `Amazon US`
- `on-ear headphones`
- `wireless on-ear headphones`
- `wired on-ear headphones`

匿名编号示例：

- `example_brand_a`
- `example_asin_001`
- `example_competitor_001`

## 7. 禁止数据

公开文件和生成报告不得包含：

- 用户品牌、用户 ASIN、用户店铺、用户后台数据。
- 用户 Sorftime 原始导出。
- 本地路径、聊天软件路径、邮箱、手机号、账号。
- API key、token、cookie、secret、password。
- 内部 MCP endpoint。
- 原始评论全文。
- 完整真实 Top 100 导出表。

## 8. 核心流程

1. 接收 `keyword/category/asin/product_idea/site/target_price/target_cost/constraints`。
2. 检查 Sorftime MCP 可用性或读取 Sorftime-style fixture。
3. 标准化市场容量、竞品结构、关键词、VOC、价格带和风险数据。
4. 生成 `source_manifest.json`。
5. 判断数据是否为空或字段不足。
6. 按 7 个维度评分。
7. 输出 `enter/cautious/weak/no-enter` 或 blocked 状态。
8. 生成 HTML 报告、JSON 数据包和下游 brief。
9. 使用 package validator 校验 dist 包。
10. 使用 privacy scanner 扫描整个 skill 或 repo。

## 9. 选品分析维度

1. 需求切入：容量、趋势、季节性和稳定性。
2. 竞争切入：品牌集中度、评论门槛、头部壁垒和竞品质量。
3. 价格利润切入：价格带、目标成本、毛利安全线和促销空间。
4. 关键词入口切入：核心词、长尾词、场景词、属性词和自然语言需求。
5. VOC 痛点切入：好评动机、差评问题、Q&A 顾虑和未满足需求摘要。
6. 人群切入：目标用户、购买动机和决策因素。
7. 场景切入：使用场景、季节场景、礼品场景和专业场景。
8. 规格差异切入：尺寸、材质、套装、结构、功能组合和变体。
9. 供应链切入：可开发性、采购难度、质检、包装、物流和交期。
10. 合规风险切入：认证、敏感 claim、侵权词、安全和平台限制。

## 10. 评分模型

| 维度 | 分值 |
|---|---:|
| 需求容量 | 20 |
| 竞争强度 | 20 |
| 利润空间 | 20 |
| 差异化机会 | 15 |
| VOC 痛点机会 | 10 |
| 关键词入口 | 10 |
| 合规与供应链风险 | 5 |

结论阈值：

- `80-100`: `enter`
- `65-79`: `cautious`
- `50-64`: `weak`
- `<50`: `no-enter`

blocked 状态不套用评分阈值。

## 10.1 选品判断模型扩展

新增字段只用于解释和风险约束，不改变 `scores.total` 的计算方式：

- `market_stage`: `growth / mature / price_war / seasonal / declining / unknown`。
- `new_product_ramp_difficulty`: 包含 `level`、`ramp_reason` 和新品爬坡子项。
- `entry_strategy`: 记录进入类型、切入点、原因和必需验证。
- `voc_productization_score`: 每个痛点必须包含 `painpoint` 和 0-10 的 `productization_score`。
- `disqualifiers`: 每项包含 `type/status/severity/reason/required_validation`；`status` 只能是 `active/inactive/unknown`，`severity` 只能是 `info/warning/critical`。
- `evidence_level`: 标记证据等级。
- `competitor_clusters`: 每个 cluster item 至少包含 `cluster_name/summary/competition_pressure/entry_implication/evidence_level`。
- `profit_space_detail`: 记录 8 个利润字段；public-safe 样例只能使用 `unknown` 或 `template_sample`。

如果存在 `status=active` 且 `severity=critical` 的 disqualifier，`decision.label` 不能为 `enter`。若原规则计算为 `enter`，降级为 `cautious`。

## 11. 输出结构

主报告：`dist/product_selection_report.html`

固定章节：

1. 执行摘要
2. 输入信息
3. 数据源状态
4. 类目容量判断
5. 关键词机会判断
6. 竞品结构判断
7. 价格带与利润判断
8. 评论 VOC 痛点判断
9. 差异化机会判断
10. 风险判断
11. 评分表
12. 选品结论
13. 证据表
14. 假设与缺失数据
15. 下一步验证动作
16. 下游 Listing / 图片 / A+ 交接 Brief

HTML 报告默认中文输出，并使用离线视觉样式：蓝色渐变 Hero、KPI 卡片、双栏面板、表格、评分条、Callout、痛点排行、结论卡片和页脚说明。

HTML 报告必须明确：On-Ear Headphones fixture 是 public-safe template sample，不是实时市场数据，不是完整真实 Top 100，不是真实 Sorftime 原始导出，不代表真实选品结论。

价格利润章节必须显示：`公开安全样例中的利润明细仅用于模板展示，不代表实时利润估算。`，并保留英文兼容说明：`Profit detail in public-safe fixtures is template-level only and not a live margin estimate.`

## 12. 数据结构

主数据包：`dist/product_selection_data.json`

必须符合 `schemas/product_selection_data.schema.json`，关键对象包括：

- `privacy_mode`
- `report_language`
- `generated_at`
- `input`
- `sorftime_status`
- `data_quality`
- `scores`
- `decision`
- `analysis`
- `evidence`
- `assumptions`
- `missing_data`
- `next_validation_actions`
- `downstream_brief`
- `public_safe_notice`
- `normalized_blocks`
- `source_manifest`

关键结论对象必须包含：

- `conclusion`
- `evidence`
- `source`
- `confidence`
- `assumption`
- `missing_data`

## 13. Source Manifest

`dist/source_manifest.json` 顶层必须包含：

- `privacy_mode`
- `generated_at`
- `query`
- `data_blocks`
- `confidence`
- `blocked_status`
- `no_user_private_data: true`
- `contains_user_private_data: false`
- `contains_raw_sorftime_export: false`
- `contains_review_text: false`
- `public_data_reference: true`
- `data_freshness`：public-safe 为 `template_sample_not_live_market_data`；private_internal 为 `live_or_latest_available_sorftime_data`
- `sources`

blocked 状态也必须生成完整 source manifest。

## 14. 错误与阻断状态

- `blocked_sorftime_unavailable`: Sorftime MCP 不可用、未配置、授权失败或健康检查失败。
- `blocked_no_data`: Sorftime MCP 可用但没有返回真实可分析数据。
- `blocked_missing_fields`: 数据存在但缺少关键字段，无法可靠评分。

blocked 状态必须生成完整 dist 包并通过 package validator；但报告必须明确不能形成成功选品结论。

## 15. 脚本边界

- `scripts/normalize_market_data_response.py`: 公开标准化主入口。
- `scripts/normalize_sorftime_response.py`: 本地兼容 wrapper。
- `scripts/render_product_selection_report.py`: HTML 渲染。
- `scripts/validate_product_selection_package.py`: 只校验 `dist` 包。
- `scripts/privacy_scan.py`: 独立扫描整个 skill 或 repo。

`privacy_scan.py` 不硬编码用户真实品牌或真实 ASIN；如需扫描私有词，只读取本地 `private_terms.txt`。仓库只提供 `private_terms.example.txt`。

真实 MCP 私有输入预留：

```bash
python scripts/normalize_market_data_response.py --input inputs/on_ear_headphones_us_live_input.json --provider sorftime_mcp --config private_config.local.json --out dist/product_selection_data.json
```

如果 standalone provider 暂不能完成真实 MCP 调用，必须输出 `blocked_sorftime_unavailable`，不得伪造成功或 fallback 到公开网页。

## 16. GitHub 文件

公开模板必须包含：

- `LICENSE`
- `SECURITY.md`
- `CONTRIBUTING.md`
- `.gitignore`
- `adapters/README.md`
- `adapters/sorftime_mcp_contract.example.json`
- `adapters/private_config.example.json`
- `private_terms.example.txt`

`.gitignore` 必须阻止 `private_config.local.json`、`*.local.json`、`runtime/`、`dist/*.html`、`dist/*.json`、私有目录、真实导出、密钥、缓存和本地私有词表。

## 17. 验收标准

- `quick_validate.py` 通过。
- 正常 fixture 完成 normalize、render、package validate。
- 三类 blocked fixture 都生成完整 dist 包并通过 package validator。
- On-Ear Headphones public-safe fixture 完成闭环并通过 package validator。
- 负向测试覆盖缺失 dist 文件、未完成占位符、通用敏感信息、private terms 命中。
- `privacy_scan.py` 扫描整个 skill 目录通过。
- 公开样例不包含用户私有数据、真实本地路径、聊天软件路径、账号、凭证、内部 endpoint、原始评论全文或完整真实 Top 100。
