## 10 主要局限与未解决问题

### 10.1 Eq.11.26 有量纲映射

Eq.11.26 多项式已正确转录，但目前未找到能够同时说明物理意义、单位及其到 Eq.11.38 \(d(\delta q)/dx\) 的唯一来源链。Eckert/reference-enthalpy 或 regenerative-cooling 文献虽然可以建立另一套壁面换热模型，但那属于新模型，而不是恢复教师 Eq.11.26。

### 10.2 变热化学 Steger-Warming

广义真实气体/多组分 FVS 文献证明理论路线存在[12-15]，但当前尚缺对本项目状态向量、绝对能量参考与代数组分闭合的兼容性推导。后续若实现，应至少验证：通量重构、能量参考不变性、常比热极限、接触面行为、正性和 smooth-case 收敛阶。

### 10.3 Cao Case 2 正式复现

已冻结的来源数据包括 H₂、Ma=2.12、ρ=0.28 kg/m³、p=46.7 kPa、T=521 K、u=977 m/s、γ=1.33、φ=0.2、入口组分、Tw=900 K 和报告网格间距。但仍缺少精确 A(x)、预设 Yi(x) 规则和原始源项/喷注空间约定。因此不能用当前项目定义几何替代正式复现。

### 10.4 完整双模态/unstart 分类

当前燃烧室模型缺少与曹论文 Table 3-1 完全兼容的隔离段/激波串状态变量和几何。只有 Eq.(3-2) scoped thermal-throat indicator 可以在满足适用条件时使用。forward-flow guard、单一 Mach 值或非收敛本身都不能独立定义物理模态。

## 11 后续工作

1. 完成 P13 教师来源范围 \(C_m=25\sim60\) 的敏感性研究，并在 20/40 网格上检查结论稳健性；
2. 在不改变模型边界的条件下扩展入口 Mach、喷注位置等 one-factor-at-a-time 参数研究，并严格标注 source-anchored 与 project-defined 输入；
3. 若获得教师 Eq.11.26 完整定义，建立并验证有量纲壁面热源适配器；
4. 若获得 Cao Case 2 精确几何/组分/源项空间信息，建立独立 formal reproduction 分支；
5. 对 generalized Steger-Warming 建立专门的状态向量与 Jacobian 推导，并通过常比热极限、smooth manufactured case、shock/nozzle 及生产 baseline 回归后再考虑切换；
6. 若需要完整燃烧模态分类，加入来源兼容的 isolator/shock-train 低阶模型与相应实验/论文验证；
7. 将论文与 acceptance/evidence 记录建立自动版本映射，每次新增正式 accepted evidence 时同步更新本文结果章节。

## 12 结论

本文完成了一套面向超燃/双模态冲压发动机燃烧室的准一维 CFD 求解与可复现科研工作流。项目的核心价值不仅在于实现变截面、喷注、摩阻、混合/燃烧、变热化学和数值推进，还在于建立了明确的科学边界：来源能够证明的内容才进入 source-backed 模型；项目自行选择的参数被明确标为 project-defined；求解器保护和非收敛不被直接解释为物理模态；缺少关键来源的公式保持 gated，而不是通过“看起来合理”的经验补齐。

现有 H₂ 综合路径已经通过基础回归、三层网格趋势、离散守恒审计与公开 NASA computational-reference benchmark 等多层验证，并能够开展当量比响应和受限的 Cao thermal-throat criterion 应用。导师控制台、GitHub Actions、机器可读 acceptance/provenance 与 SHA-256 完整性记录进一步使项目从“单机脚本”发展为可重复运行、可审查和可持续维护的工程计算系统。

因此，在当前证据范围内，可以将本项目定位为一套达到课程/本科工程研究交付要求、具有明确科学边界和继续扩展能力的准一维 scramjet CFD 平台；而 Eq.11.26、变热化学 Steger-Warming、Cao Case 2 正式复现及完整双模态分类仍应作为后续研究问题，而非当前已解决结论。

---

## 参考文献

[1] 《高超声速气动布局理论及应用》. 第11章：双模态冲压发动机一维数值模拟. 教师提供项目资料.

[2] 曹瑞峰. 超燃冲压发动机燃烧模态转换及其控制方法研究[D]. 2016.

[3] Cao R F, Lu Y, Yu D, Chang J. Study on influencing factors of combustion mode transition boundary for a scramjet engine based on one-dimensional model[J]. Aerospace Science and Technology, 2020, 96: 105590. DOI: 10.1016/j.ast.2019.105590.

[4] Zhang Y, Chen B, Liu G, Wei B X, Xu X. Influencing factors on the mode transition in a dual-mode scramjet[J]. Acta Astronautica, 2014, 103: 1-15. DOI: 10.1016/j.actaastro.2014.06.006.

[5] Pulsonetti M V, Erdos J I, Early K. Engineering model for analysis of scramjet combustor performance with finite-rate chemistry[J]. Journal of Propulsion and Power, 1991, 7(6): 1055-1063. DOI: 10.2514/3.23427.

[6] Heiser W H, Pratt D T. Hypersonic Airbreathing Propulsion[M]. AIAA Education Series, 1994.

[7] Birzer C, Doolan C J. Quasi-One-Dimensional Model of Hydrogen-Fueled Scramjet Combustors[J]. Journal of Propulsion and Power, 2009, 25(6): 1220-1225. DOI: 10.2514/1.43716.

[8] Torrez S M, Driscoll J F, Ihme M, Fotia M A. Reduced-Order Modeling of Turbulent Reacting Flows with Application to Ramjets and Scramjets[J]. Journal of Propulsion and Power, 2011, 27(2): 371-382. DOI: 10.2514/1.50272.

[9] Tian L, Chen L H, Chen Q, Li F, Chang X. Quasi-One-Dimensional Multimodes Analysis for Dual-Mode Scramjet[J]. Journal of Propulsion and Power, 2014, 30(6): 1559-1567. DOI: 10.2514/1.B35177.

[10] Zhang D, Feng Y, Zhang S L, Qin J, Cheng K L, Bao W, Yu D. Quasi-One-Dimensional Model of Scramjet Combustor Coupled with Regenerative Cooling[J]. Journal of Propulsion and Power, 2016, 32(3): 687-697. DOI: 10.2514/1.B35887.

[11] Burrows M C, Kurkov A P. Analytical and Experimental Study of Supersonic Combustion of Hydrogen in a Vitiated Airstream[R]. NASA TM X-2828, 1973.

[12] Liu Y, Vinokur M. Nonequilibrium Flow Computations. I. An Analysis of Numerical Formulations of Conservation Laws[J]. Journal of Computational Physics, 1989, 83(2): 373-397. DOI: 10.1016/0021-9991(89)90125-3.

[13] Grossman B, Walters R W. Analysis of Flux-Split Algorithms for Euler's Equations with Real Gases[J]. AIAA Journal, 1989, 27(5): 524-531. DOI: 10.2514/3.10142.

[14] Liou M S, van Leer B, Shuen J S. Splitting of Inviscid Fluxes for Real Gases[J]. Journal of Computational Physics, 1990, 87(1): 1-24. DOI: 10.1016/0021-9991(90)90222-M.

[15] Bertolazzi E, Manzini G. A Triangle-Based Unstructured Finite-Volume Method for Chemically Reactive Hypersonic Flows[J]. Journal of Computational Physics, 2001, 166(1): 84-115. DOI: 10.1006/jcph.2001.6644.

[16] Smith G P, Golden D M, Frenklach M, et al. GRI-Mech 3.0[DB/OL]. 1999.

[17] ASME. V&V 20-2009: Standard for Verification and Validation in Computational Fluid Dynamics and Heat Transfer[S]. New York: ASME, 2009.

---

## 附录 A 论文维护规则

本文作为项目主论文持续维护。后续修改遵循以下规则：

1. 只有已经进入 repository acceptance/evidence workflow 的计算结果才能从“在研”升级为正文结论；
2. 每一次新增正式研究结果时，同步修改“结果”“局限”“结论”和参考文献，不只追加图表；
3. source-gated 项目在来源未补齐前不得通过论文文字“视为已解决”；
4. 项目自定义阈值、参数与网格设计必须始终标记为 project-defined；
5. 当某个历史结论被更严格证据替代时，保留历史 provenance，同时在正文采用最新 accepted evidence；
6. Word/PDF 为发布快照，GitHub 中的 Markdown 主稿为持续维护源稿。

## 附录 B v0.1 状态说明

- 本版本纳入已接受的 P11.4、NASA benchmark 和 P12 证据；
- P13 \(C_m\) 敏感性 study 的定义、来源范围与预注册协议已经建立，但专用 CFD workflow 在本版成稿时仍在运行，因此正文仅将其列为“在研”，不写入结果结论；
- 后续 P13 acceptance 生成后，优先更新第 7/11 节并新增参数敏感性图表。
