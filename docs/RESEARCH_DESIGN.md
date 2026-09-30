# Research Design: Compliance-by-Design Simulation Testbed for City Digital Twins

# 研究设计：面向城市数字孪生的合规-by-design 仿真测试床

This document records the design of the testbed released in this repository: what it models, which
rules it formalises, how the two domain profiles are separated from the engine, and what the
experimental matrix is designed to measure. It is the design record for version 1.0.4 and describes
the code as implemented.

本文档记录本仓库发布的测试床的设计：它建模什么、形式化哪些规则、两个领域 profile 如何与引擎分离，
以及实验矩阵用来测量什么。它是 1.0.4 版本的设计记录，描述的是**代码的实际实现**。

---

## 1. Scope and positioning / 定位与范围

Operational city digital twins exchange data across public agencies, utilities, cloud services and
model providers. A compliance claim in that setting has to survive an auditor who does not control
the source system, which makes the evidence attached to each cross-organisational handover the
object of interest rather than the control catalogue as such.

运行中的城市数字孪生要在公共部门、公用事业单位、云服务和模型提供方之间交换数据。在这种场景下，
合规主张必须经得起"不掌握源系统的审计方"的检验，因此关注的对象是每次跨组织交接所附带的证据，
而不是控制项清单本身。

This testbed exists to make that object measurable. It formalises a named set of Chinese
data-security obligations as machine-checkable predicates, evaluates them over simulated
cross-organisational handovers, and reports compliance as a quantity that can be traced back to the
rules and the scenario parameters that produced it.

本测试床的目的就是让这个对象可测量：把一组具名的中国数据安全义务形式化为可机检的谓词，
在仿真的跨组织交接上求值，并把合规报告为一个可回溯到规则与场景参数的量。

The design sits between two literatures. Machine-readable compliance is a mature engineering
programme, with policy engines and policy languages already available; digital-twin governance
research has produced reference architectures and maturity models. What is absent is a coupling of
the two that is anchored in a specific national standard set and evaluated under adverse conditions
and operational load. The testbed is that coupling, and this document is its design record.

本设计处在两支文献之间。机器可读合规已是成熟的工程实践，策略引擎与策略语言都已具备；数字孪生治理
研究也已产出参考架构与成熟度模型。缺的是把两者耦合起来、锚定在特定国家标准集上、并在不利条件与
运行负载下接受检验的工作。本测试床就是这一耦合，本文档是其设计记录。

A companion systematic review of 1,182 records found that framework and conceptual contributions
outnumber empirical or validation studies by roughly 3.9 to 1, and that cross-organisational
evidence handover receives the least primary coverage of the themes examined. The practical gap is
therefore not a shortage of rules but a shortage of mechanisms that turn rules into measurable,
reproducible evidence. This design targets the second.

配套的一项系统综述（1,182 条记录）发现：框架类与概念类贡献约为实证/验证类研究的 3.9 倍，
而在所考察的主题中，跨组织证据交接获得的原始研究覆盖最少。因此实践中的缺口不是规则不足，
而是缺少把规则转化为可测量、可复现证据的机制。本设计针对的是后者。

## 2. Research questions / 研究问题

| ID | Question | Addressed by |
|---|---|---|
| RQ-A | What minimal set of machine-checkable predicates is required to formalise the selected Chinese data-security obligations in a domain-independent way?<br>把所选中国数据安全义务以**领域无关**的方式形式化为可机检的谓词，需要的最小规则集是什么？ | §4, §5 |
| RQ-B | In cross-organisational handover, how do misclassification, signature omission and adversarial tampering propagate along the evidence chain, and how quickly does an auditor detect them?<br>跨组织交接中，误标、漏签与对抗篡改如何沿证据链传播，审计方多快能检出？ | §6, S1–S4 |
| RQ-C | What does compliance-by-design gain, relative to no-design and partial-design baselines, in evidence completeness, modelled reconstruction cost and tamper resilience?<br>相较无设计与部分设计基线，合规-by-design 在证据完整度、建模重构成本与抗篡改韧性上增益几何？ | §6, B0/B1/S0 |
| RQ-D | Which measured quantities respond to structural parameters, and which are invariant by construction rather than by empirical robustness?<br>哪些观测量对结构性参数敏感？哪些是**构造上不变**而非经验上稳健的？ | §6, S3/S5, Morris |
| RQ-E | Does the same engine and rule set remain evaluable under domain-profile substitution, and what does that substitution demonstrate about transferability?<br>同一套引擎与规则集在更换领域 profile 后是否仍可评估？这一替换对可迁移性证明了什么？ | §6, S6/S6b |

RQ-D is phrased as a distinction rather than a direction because the engine routes topology and
stakeholder count only into the latency model. Invariance there is a property of the design, and
the design should say so rather than report it as evidence of robustness.

RQ-D 的措辞是"区分"而非"方向"，因为引擎只把拓扑与利益方数量接入时延模型。那里的不变性是**设计属性**，
设计应当明说，而不是把它当作稳健性证据来报告。

## 3. System model / 系统模型

### 3.1 Domain-agnostic metamodel / 通用元模型

The metamodel abstracts the four layers of GB/T 45109.1-2024 so that they carry no domain
semantics, and attaches to each layer the evidence that layer is obliged to produce.

元模型抽象 GB/T 45109.1-2024 的四层，使其不携带领域语义，并为每一层挂上该层有义务产出的证据。

| Layer / 层 | Generic semantics / 通用语义 | Evidence produced / 证据产出点 |
|---|---|---|
| Physical entity / 物理实体层 | sensing, actuation, observation / 传感、执行、观测 | acquisition authenticity, PII / 采集真实性、个人信息 |
| Data / 数据层 | data baseplate, exchange, lineage / 数据底板、交换、血缘 | classification, encryption, lineage / 分类分级、加密、血缘 |
| Virtual twin / 虚拟孪生层 | models, algorithms, simulation / 模型、算法、仿真引擎 | model V&V, component inventory / 模型 V&V、组件清单 |
| Service / application / 服务应用层 | warning, dispatch, cross-department sharing / 预警、调度、跨部门共享 | cross-organisational handover, audit / 跨组织交接、审计 |

A single handover therefore carries evidence spanning all four layers. This is why a per-item check
is insufficient and why R7 (the handover receipt) occupies a structural position: it is the artifact
that binds the layers into one object that a party without access to the source system can
re-evaluate. This is stated as a property of the design, not of federation in general; a deployment
could bind layers by other means.

因此单次交接携带横跨四层的证据。这正是逐项检查不够、且 R7（交接凭证）占据结构性位置的原因：
它是把各层绑定为一个整体、使不掌握源系统的一方也能重新求值的工件。这是**本设计**的属性，
而非联邦体制的一般属性；实际部署可以用别的方式绑定各层。

### 3.2 Profile mechanism / profile 机制

A profile is a set of mappings that plugs a domain specification into the generic metamodel. Its
fields are: entity-type table, data-item inventory, model inventory, cross-organisational interface
table, and domain standard anchors. The simulation engine reads a profile and instantiates the
process; the rule set is not consulted when profiles are swapped.

profile 是把领域规范插入通用元模型的一组映射，字段包括：实体类型表、数据项清单、模型清单、
跨组织接口表、领域标准锚点。仿真引擎读入 profile 即实例化过程；更换 profile 时**不涉及规则集**。

Two properties follow, and both are enforced in code rather than asserted:

由此得到两条性质，二者都在代码中强制实现，而非口头声称：

- **Rule invariance.** For every profile P, the rule set is unchanged. A profile cannot modify it.
  **规则不变性**：对任意 profile P，规则集保持不变；profile 无权修改规则集。
- **Checkability transfer.** The profile schema requires the facts the rules test, and refuses to
  instantiate when a required fact is missing.
  **可检性传递**：profile 模式要求提供规则所检验的事实，缺少必需要素时拒绝实例化。

### 3.3 Flood profile / 洪涝 profile

Anchored on SL/T 853–855-2025. The profile declares six sources, and their sensitivity classes are
what fixes the closed-form misclassification rate reported in the results.

锚定 SL/T 853–855-2025。该 profile 声明六个数据源，其敏感级别决定了结果中报告的误标闭式解。

| Source / 数据源 | Content / 内容 | Class / 级别 | PII |
|---|---|---|---|
| `rain_gauge` | precipitation / 降水 | general / 一般 | |
| `water_level` | hydrology / 水文 | important / 重要 | |
| `gate_control` | hydraulic control / 闸门控制 | **core / 核心** | |
| `pump_station` | drainage / 排水 | important / 重要 | |
| `cctv_river` | video surveillance / 视频监控 | important / 重要 | yes |
| `population_grid` | affected population / 受影响人口 | **core / 核心** | yes |

The mix is one general, three important and two core sources. Models cover coupled hydrodynamic and
pipe-network flood propagation; interfaces run between the water authority, emergency management,
urban management and the cloud provider.

构成为 1 个一般、3 个重要、2 个核心源。模型覆盖水动力与管网耦合的洪涝演进；
接口位于水利、应急管理、城市管理与云服务提供方之间。

### 3.4 Transport profile / 交通 profile

The second profile exists to test whether the engine and rule set remain evaluable after domain
substitution. It is deliberately a probe rather than a second validation: the same six-source shape
is preserved, and only the domain mappings differ.

第二个 profile 用于检验更换领域后引擎与规则集是否仍可评估。它是**探针而非第二个验证案例**：
保持相同的六源结构，只有领域映射不同。

| Source / 数据源 | Content / 内容 | Class / 级别 | PII |
|---|---|---|---|
| `loop_detector` | traffic flow / 交通流 | general / 一般 | |
| `signal_controller` | signal control / 信号控制 | **core / 核心** | |
| `gps_probe` | vehicle trajectory / 车辆轨迹 | important / 重要 | yes |
| `cctv_junction` | video surveillance / 路口视频 | important / 重要 | yes |
| `weather_station` | road weather / 道路气象 | general / 一般 | |
| `transit_afc` | transit ridership / 公交客流 | important / 重要 | yes |

The mix here is two general, three important and one core. The closed form therefore predicts a
different silent-misclassification rate for this profile than for the flood profile, and the
difference is a consequence of the declared class mix rather than of the domain.

此构成为 2 个一般、3 个重要、1 个核心。因此闭式解对该 profile 预测的静默误标率与洪涝 profile 不同，
这一差异源于声明的级别构成，而非领域本身。

## 4. Rule formalisation R1–R8 / 合规约束形式化

Each rule is a predicate over the evidence bundle exchanged at a handover. The mapping below is the
rule set as implemented in `ruleset/rules.py`; weights are the ones used by the conformance metric.

每条规则都是对交接时交换的证据包求值的谓词。下表是 `ruleset/rules.py` 中实现的规则集；
权重即符合分指标所用的权重。

| Rule | Source standard | Predicate as implemented | Weight |
|---|---|---|---|
| R1 | GB/T 43697-2024 | every data item carries a class label / 每条数据带分类标签 | 1.0 |
| R2 | GB/T 43697-2024 | core data encrypted, audited and stored locally / 核心数据加密、审计、境内存储 | **1.5** |
| R3 | GB/T 39786-2021 | important/core data encrypted **at rest** / 重要、核心数据**静态**加密 | 1.0 |
| R4 | GB/T 39786-2021 | evidence cryptographically signed (hash + key) / 证据密码学签名 | **1.5** |
| R5 | GB/T 22239-2019 (L3) | full-link access audit log present / 全链路访问审计日志 | 1.0 |
| R6 | GB/T 22239-2019 (L3) | data integrity check, chain untampered / 数据完整性校验 | 1.0 |
| R7 | 20262810-T-907 (**draft**) | cross-organisational handover produces a receipt (hash chain + timestamp + signer)<br>跨组织交接产生凭证（哈希链＋时间戳＋签名方） | **1.5** |
| R8 | PIPL and its audit measures | PII de-identified and consent recorded / 个人信息去标识化并记录同意 | 1.0 |

Total weight is 9.5 over eight predicates, and M6 is the weighted pass rate over this set.

八个谓词的总权重为 9.5，M6 即在该集合上的加权通过率。

Three scope limits belong with the table rather than in a footnote, because each one is visible in
the encoding and a reader should be able to check it there. R1 tests that a label is present and
well formed; it does not establish that the label is semantically correct. R3 covers encryption at
rest only, not protection of data in transit. R5 establishes that an audit record exists, not that it
is retained and protected rather than transient. Expanding the rule set to cover the omitted
obligations changes the denominator of M6 and therefore every conformance value reported here, so
the metrics in this release are specific to the eight-predicate instrument.

三条范围限制应当与表格同处，而不是塞进脚注，因为每一条在编码中都可见、读者应当能就地核对。
R1 检验标签**存在且格式正确**，不确立标签语义正确；R3 只覆盖静态加密，不覆盖传输中保护；
R5 确立审计记录存在，不区分它是被长期保存并受保护还是瞬时记录。若把遗漏的义务纳入规则集，
将改变 M6 的分母，从而改变本处报告的每一个符合度数值——因此本版本的指标专属于"八谓词"这套工具。

R7 is anchored to plan 20262810-T-907, which is a draft plan number rather than an enacted standard.
Its link to that plan is architectural: the plan is not counted as an in-force requirement anywhere
in this work.

R7 锚定于计划号 20262810-T-907，它是**起草中的计划号**而非已生效标准。它与该计划的联系是架构性的：
本工作在任何地方都不把该计划计为已生效要求。

## 5. Simulation model / 仿真模型

### 5.1 Agents and evidence artifacts / 角色与证据工件

Five roles, all domain-independent: `Source`, `Operator`, `Attacker`, `Agency` and `Auditor`. They
represent role separation within one simulated process, not a deployed federation.

五个角色，均领域无关：`Source`、`Operator`、`Attacker`、`Agency`、`Auditor`。
它们表示同一仿真过程内的角色分离，而非已部署的联邦。

Six evidence artifacts are produced and carried in each bundle: EV1 classification label (GB/T
43697), EV2 cryptographic attestation (GB/T 39786), EV3 access audit log (GB/T 22239), EV4
model-component inventory, EV5 handover receipt (20262810-T-907 pattern), EV6 personal-information
handling record (PIPL). EV5 binds the others into a single object that can be checked across an
organisational boundary.

每个证据包携带六类证据工件：EV1 分类标签（GB/T 43697）、EV2 密码学证明（GB/T 39786）、
EV3 访问审计日志（GB/T 22239）、EV4 模型组件清单、EV5 交接凭证（20262810-T-907 模式）、
EV6 个人信息处理记录（PIPL）。EV5 把其余各项绑定为一个可跨组织边界检查的整体。

### 5.2 Engine and profile separation / 引擎与 profile 分离

```
engine/       domain-independent: agents, evidence chain, rule evaluation, metrics
              （领域无关：角色、证据链、规则求值、指标）
ruleset/      R1-R8, shared by engine and profiles
              （R1-R8，引擎与 profile 共享）
profiles/     flood/ and transport/ domain mappings
              （flood/ 与 transport/ 两个领域映射）
```

Changing the profile changes the domain; the engine and the rule set are not modified. Generalisability
is therefore a property of the architecture that the experiment demonstrates by running, not a claim
about the code being "generic".

更换 profile 即更换领域，引擎与规则集**零修改**。因此通用性是架构的属性，由运行来演示，
而不是关于代码"很通用"的一句声明。

### 5.3 Process skeleton / 过程骨架

```
Source --(raw data)--> Operator
Operator: classify(EV1, may err p_err) -> sign(EV2, may skip p_skip) -> build EV5(EV1..EV4)
Operator --(EV5 handover)--> Agency
Agency: verify(EV5 chain) -> accept/reject
Attacker: with probability p_atk, tamper(EV5)
Auditor: replay(EV5 chain) -> score conformance(R1..R8)
```

Verification has two distinct outcomes, and keeping them distinct is what makes the tamper result
interpretable: a receipt is **verified** when its chain is intact, which contributes to M1, and
**recovered** when a tampered receipt can be re-derived from the signed attestation, which
contributes to M5.

验证有两种不同结果，把它们分开才能让抗篡改结果可解释：当链路完好时凭证**被验证**（计入 M1）；
当被篡改的凭证可由签名证明重新导出时**被恢复**（计入 M5）。

## 6. Experimental design / 实验方案

### 6.1 Scenario matrix / 场景矩阵

Each scenario runs 6 sources over 200 timesteps, yielding 1,200 handovers.

每个场景运行 6 个数据源、200 个时间步，产出 1,200 次交接。

| Scenario | Perturbation / 扰动 | Measures / 测什么 | Profile |
|---|---|---|---|
| B0 | no compliance-by-design / 无合规-by-design | baseline lower bound / 基线下界 | flood |
| B1 | partial design, no verifiability (see §6.4)<br>部分设计、不可验证（见 §6.4） | conformance without verifiability / 无凭证的符合度 | flood |
| S0 | full-design baseline, run in mode B2<br>全设计基线，以 mode B2 运行 | upper bound (golden) / 上界 | flood |
| S1 | single-party misclassification, p_err ↑ | downstream propagation of mislabels / 误标的下游传播 | flood |
| S2 | signature omission, p_skip ↑ | audit failure propagation / 漏签的审计失效传播 | flood |
| S3 | topology star ↔ mesh | handover latency, resilience / 交接时延与韧性 | flood |
| S4 | adversarial, p_atk ↑ | tamper resilience, violation detection / 抗篡改韧性与违规检出 | flood |
| S5 | scale, N ↑ | scalability / 可扩展性 | flood |
| S6 | profile substitution / 切换 profile | RQ-E: transferability / 可迁移性 | transport |
| S6b | profile substitution + adversarial / 切换＋对抗 | transferability under attack / 对抗下的可迁移性 | transport |

### 6.2 Parameters / 参数

| Parameter | Meaning / 含义 | Baseline | Sensitivity range / 扫描范围 |
|---|---|---|---|
| `p_err` | misclassification probability / 误标率 | 0.02 | [0, 0.20] |
| `p_skip` | signature-omission probability / 漏签率 | 0.01 | [0, 0.15] |
| `p_atk` | adversary probability / 对抗概率 | 0.01 | [0, 0.10] |
| `p_noaudit`, `p_pii_fail` | omitted audit log / PII failure<br>审计日志缺失率／个人信息处理失败率 | 0.02 | — |
| `topology` | star or mesh / 拓扑 | star / 星型 | {star, mesh} |
| `N` (`n_stakeholders`) | number of stakeholders / 利益方数 | 5 | [3, 12] |
| `timesteps` | handovers per source per run / 每源每轮时间步 | 200 | — |
| `seed` | random-stream seed / 随机种子 | 42 | — |

`N` takes exactly ten integer values across its range, which is why the binned first-order estimator
uses ten equiprobable bins: at ten bins every bin holds one distinct level of that factor. The bin
count is a reported parameter, not an implementation detail, because the estimator is not
bin-count invariant.

`N` 在其取值范围内恰有 10 个整数取值，这是分箱一阶估计器采用 10 个等概率箱的原因：
10 箱时该因子的每一箱恰好对应一个不同取值。分箱数是**应当报告的参数**而非实现细节，
因为该估计器并不满足分箱数不变性。

### 6.3 Metrics / 指标

| Metric | Definition / 定义 | Direction / 方向 |
|---|---|---|
| M1 evidence completeness / 证据完整度 | share of handovers whose receipt is well formed, signed and untampered<br>凭证格式完整、已签名且未被篡改的交接占比 | high |
| M2 reconstruction cost / 重构成本 | synthetic audit-preparation cost index (arbitrary units)<br>审计准备成本的合成分指标（任意单位） | low |
| M3 violation detection / 违规检出率 | detected injected violations / injected<br>检出注入违规 ÷ 注入违规 | high |
| M3s mislabel detection / 误标检出率 | detection over the silent misclassification channel only<br>仅针对静默误标通道的检出率 | high |
| M4 handover latency / 交接时延 | mean end-to-end latency / 端到端平均时延 | low |
| M5 tamper resilience / 抗篡改韧性 | fraction of attacked handovers still verifiable<br>受攻击交接中仍可验证的占比 | high |
| M6 conformance score / 符合分 | weighted pass rate over R1–R8 / R1–R8 加权通过率 | high |

M3s is reported separately from M3 because the two channels behave differently and averaging them
would hide the one this work is about. M2 is a synthetic index over a fixed base cost of 0.05 per
handover, plus 1.0 for an unsigned attestation, 2.0 for a tampered receipt, 1.5 for a receipt that
is not well formed and 0.5 per detected violation; it orders configurations and does not predict
auditor labour or calendar time. M5 is undefined when no handover is attacked, and is reported as
undefined rather than defaulted. The metric keys as they appear in `results/*.csv` are
`M1_evidence_completeness`, `M2_audit_prep_time`, `M3_violation_detection`,
`M3s_mislabel_detection`, `M4_handover_latency`, `M5_tamper_resilience` and `M6_conformance_score`.

M3s 与 M3 分开报告，因为两个通道行为不同，合并会掩盖本工作真正关注的那个。M2 是合成分指标，
基准成本为每次交接 0.05，另加：未签名证明 +1.0、凭证被篡改 +2.0、凭证格式不完整 +1.5、
每条检出违规 +0.5；它只对配置排序，不预测审计工时或日历时间。当没有交接受攻击时 M5 无定义，
此时如实报告为无定义而不取默认值。各指标在 `results/*.csv` 中的键名为
`M1_evidence_completeness`、`M2_audit_prep_time`、`M3_violation_detection`、
`M3s_mislabel_detection`、`M4_handover_latency`、`M5_tamper_resilience`、`M6_conformance_score`。

### 6.4 Baselines, sensitivity and validation / 基线、敏感性与验证

Baselines are B0 (no design), B1 (partial design, the analytically important one) and B2 (full
design); the full-design baseline is run as scenario S0, so B2 and S0 denote the same configuration.
B1 matters because it is the configuration a real procurement process can produce: it carries
correct labels, encrypts according to the declared class and writes an access record, yet it emits
no signature, its handover receipt is present but not well formed, and it applies no
personal-information handling. Its evidence therefore cannot be replayed by a third party. Two
consequences are visible in the encoding: B1 labels are always correct, so this baseline is
deterministic rather than sampled and its conformance is a fixed value rather than a distribution;
and because M1 is defined over signed receipts, B1 scores zero on M1 by definition as well as in
substance.

基线为 B0（无设计）、B1（部分设计，分析上最关键的）与 B2（全设计）；全设计基线以场景 S0 运行，
故 B2 与 S0 指同一配置。B1 重要是因为它是真实采购流程可能产出的配置：标签正确、按声明级别加密、
写入访问记录，但不产生签名，交接凭证存在而格式不完整，且不做个人信息处理。因此其证据无法被
第三方重放。编码中可见两条后果：B1 的标签恒为正确，因此该基线是**确定性**的而非抽样的，其符合度
是一个定值而非分布；且由于 M1 定义在签名凭证之上，B1 在 M1 上依定义即为零，同时也确实为零。

Sensitivity analysis uses Morris elementary effects for screening (r = 12 trajectories, 4 levels)
and Sobol variance decomposition for attribution. The standard Saltelli first-order estimator proved
unusable at the output variance of this model, producing values above one and negative estimates on
analytic test functions; the reported first-order indices therefore come from a binned
conditional-mean estimator (10 equiprobable bins, N = 4000), and total-order indices from
Saltelli/Jansen at N = 1024. Morris screening runs on the 200-timestep configuration, while both
Sobol designs run on a 30-timestep configuration; the shorter horizon belongs to the sensitivity
runs and does not apply to the scenario matrix. The sensitivity runs also use their own seeds
(Morris 7, Sobol 11) rather than the scenario seed of 42. First-order values should be read as
diagnostic upper bounds.

敏感性分析用 Morris 基本效应做筛选（r = 12 条轨迹、4 个水平），用 Sobol 方差分解做归因。
标准 Saltelli 一阶估计器在本模型的输出方差下不可用，在解析检验函数上产生大于 1 的值与负估计；
因此所报告的一阶指数来自分箱条件均值估计器（10 个等概率箱、N = 4000），总阶指数来自
Saltelli/Jansen（N = 1024）。Morris 筛选运行在 200 时间步配置上，两个 Sobol 设计均运行在
30 时间步配置上；较短的时间窗属于敏感性运行，不适用于场景矩阵。敏感性运行另用自己的种子
（Morris 7、Sobol 11），而非场景种子 42。一阶值应作为诊断性上界来读。

Validation of the flood case uses the SL/T 853–855 process as the operational clock: a synthetic
36-hour urban flood event is encoded as six phases (monitoring baseline, data baseplate, model
inference, early warning, dispatch, recession), each carrying an evidence load and a control-stress
profile, giving 1,464 handovers in total. Both the load and the stress profile are analyst-assigned
in a single table, so the resulting contrast measures the model's behaviour under an assumed
coupling rather than calibrating to observed data. This is the single most important quantity to
replace with field data, and the design records it as a hypothesis the testbed can falsify.

洪涝案例的验证用 SL/T 853–855 流程作为运行时钟：把一个合成的 36 小时城市洪涝事件编码为六个阶段
（监测基线、数据底板、模型推演、预警、调度、复盘），每阶段携带一个证据负载与一个控制压力剖面，
合计 1,464 次交接。负载与压力剖面均由分析者在同一张表中设定，因此所得到的对比测量的是
**给定耦合假设下模型的行为**，而非对观测数据的标定。这是最需要用现场数据替换的量，
设计把它记录为一条可被本测试床证伪的假设。

## 7. Contributions / 贡献

1. A domain-agnostic compliance-by-design simulation testbed: a reusable engine, a standard-anchored
   rule set R1–R8, and a profile interface that separates the two.
   一个领域无关的合规-by-design 仿真测试床：可复用的引擎、锚定标准的规则集 R1–R8，以及把二者分离的 profile 接口。
2. An executable account of how compliance-by-design behaves under misclassification, signature
   omission, adversarial tampering, topology change and scale change, reported through metrics that
   separate rule conformance from evidentiary adequacy.
   对合规-by-design 在误标、漏签、对抗篡改、拓扑变化与规模变化下行为的可执行刻画，
   并通过把"规则符合度"与"证据充分性"分开的指标体系来报告。
3. A closed-form analysis of the silent-misclassification channel, which locates the limitation in
   the encoding of R1 and the declared class mix rather than in the underlying standards.
   对静默误标通道的闭式分析，把该局限定位在 R1 的编码方式与声明的级别构成上，而非底层标准。
4. A reproducible flood-twin case and a cross-domain probe, released with a one-click reproduction
   script that rebuilds the reported numbers and asserts them against the results document.
   可复现的洪涝孪生案例与一个跨领域探针，随附一键复现脚本，重建所报告的数字并与结果文档逐项断言。

## 8. Scope and limitations / 适用范围与限制

- **Simulation, not deployment.** All scenarios are synthetic and generated from seeded random
  streams. No real event, facility or individual is represented. Conclusions are about the model's
  behaviour and about properties of the encoding; they are not claims about deployed federations.
  **是仿真，不是部署。** 所有场景均为合成数据、由固定随机种子生成，不表示任何真实事件、
  设施或个人。结论针对模型行为与编码属性，不是关于已部署联邦的主张。
- **Rule coverage is deliberately partial.** Cross-border transfer, audit-record retention, key
  management and approved cryptographic schemes, protection in transit, and identity, access control
  and intrusion prevention are not modelled. Extending the rule set re-specifies the M6 denominator.
  **规则覆盖是刻意不完整的。** 跨境传输、审计记录留存、密钥管理与密码方案审批、传输中保护，
  以及身份、访问控制与入侵防范均未建模。扩展规则集会重新定义 M6 的分母。
- **The silent-channel rate is a property of the instrument.** It follows from R1 testing presence
  rather than correctness, and from the profile's declared class mix. Changing either changes the
  rate without any change to the standards.
  **静默通道比率是工具属性。** 它来自 R1 检验"存在"而非"正确"，以及 profile 声明的级别构成；
  改动任一项都会改变该比率，而无需标准发生任何变化。
- **Draft-plan anchoring.** The plan 20262810-T-907 is under development and is used as a label for
  a design pattern. No result depends on its eventual content.
  **锚定于起草中计划。** 计划 20262810-T-907 仍在制定中，仅用作某一设计模式的标签；
  没有任何结果依赖它最终的内容。
- **Structural invariance is by construction.** Topology and stakeholder count enter only the latency
  model. Where a factor cannot affect a metric by construction, this design reports that rather than
  presenting the resulting invariance as robustness.
  **结构性不变性来自构造。** 拓扑与利益方数量只接入时延模型。当某因子在构造上无法影响某指标时，
  本设计如实报告这一点，而不把由此产生的不变性当作稳健性。
- **The transport profile is a probe.** It tests the interface, not a second domain's compliance
  behaviour; it has no comparable process standard to supply an operational clock, which is why it
  receives a baseline and an adversarial run rather than a stress contrast.
  **交通 profile 是探针。** 它检验接口，而非第二个领域的合规行为；该领域没有可比的过程标准来提供
  运行时钟，因此它只有基线与对抗两组运行，没有压力对比。
- **Metric boundaries.** M1 is defined over signed receipts, so a design that omits signing scores
  zero by definition as well as in substance; an alternative definition would change the headline.
  M5 is non-degenerate only because tampering is modelled as recoverable via the signed attestation.
  **指标边界。** M1 定义在签名凭证之上，因此不签名的设计在定义上即为零，同时也确实为零；
  换一种定义会改变结论数值。M5 之所以非退化，仅因为本模型把篡改设为可通过签名证明恢复。

---

*This design record describes version 1.0.4 of the testbed. Standard clauses are cited by number as
anchors for the encoding; the encoding, not the citation, is what the code implements and what the
results document. Plan 20262810-T-907 is a draft plan number and is used as a design-pattern label
only.*

*本设计记录对应测试床 1.0.4 版本。标准条款按条款号作为编码锚点引用；代码实现的是**编码**，
结果文档记录的也是编码，而非条款原文。计划号 20262810-T-907 为起草中计划，仅作设计模式标签。*
