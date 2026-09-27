# 基于教师参考模型的超燃/双模态冲压发动机准一维 CFD 求解器开发、验证与工程化实现

**版本：v0.1（2026-09-27）**  
**项目仓库：LBW-and-YBW-**  
**论文性质：持续维护的项目主论文初稿**

## 摘要

针对超燃冲压发动机与双模态冲压发动机快速性能分析、课程设计与控制研究中对低成本、高可解释性数值工具的需求，本文开发了一套面向燃烧室准一维流动的可复现 CFD 求解与证据管理框架。项目以教师提供的《高超声速气动布局理论及应用》第 11 章“双模态冲压发动机一维数值模拟”以及曹瑞峰博士学位论文《超燃冲压发动机燃烧模态转换及其控制方法研究》为主要模型依据，在有限体积框架下求解准一维可压缩守恒方程，并逐步集成变截面、壁面摩阻、燃料喷注、混合/燃烧效率、变组分热化学、边界条件、伪时间推进和稳态收敛判据。当前 H₂/C₂H₄ 教师路径采用 Rusanov 数值通量、SSP-RK3 时间积分和教师 Eq.11.46 最大相对密度变化作为主要稳态诊断；教师 Steger-Warming 公式保留为独立审计路径，但由于变热化学绝对组分能量参考下的生产级兼容性尚未得到教师/Cao 来源的直接闭合，当前未强制替换已验证的 Rusanov 生产路径。

为避免将“代码能运行”误当作“物理模型被验证”，项目将数值验证、模型确认、源资料复现和项目自定义敏感性研究严格区分。已完成的证据包括：项目定义 H₂ 综合算例、20/40/80 三层网格趋势、离散质量/动量/能量库存率审计、NASA Burrows-Kurkov 公开资料驱动的降阶计算参考 benchmark、当量比响应计算、基于曹瑞峰 Eq.(3-2) 的热喉判据应用、GitHub Actions 自动回归测试以及面向导师使用的 Web 控制台。20/40/80 网格结果表明，关键极值随网格加密持续变化但差异逐步缩小，因此本文仅声明“网格收敛趋势”，不宣称已达到严格渐近区或 GCI 意义下的网格无关。P12 项目定义 H₂ 响应研究中，φ=0.10、0.20 可在项目选定的 2×10⁻⁵ Eq.11.46 数值容差下收敛；采用组成一致 warm-start 后，φ=0.22、0.24 也可收敛并保持在所采用的 Cao Eq.(3-2) scram-side 范围内，而 φ=0.26 触发当前正向流摩阻适配器的模型域保护。该保护仅解释为“求解器/模型域不可接受”，不被直接解释为 unstart 或燃烧模态转换。

工程实现方面，项目建立了机器可读 acceptance JSON、来源/假设 ledger、运行 commit/workflow/artifact/SHA-256 provenance，并提供本地和 Render 部署的导师控制台，可查看已接受结果、运行冻结算例、导出 JSON/CSV 及完整性摘要。本文同时明确保留若干 source-gated 问题：教师 Eq.11.26 壁面换热经验多项式到 Eq.11.38 能量源项的唯一有量纲映射、变热化学 Steger-Warming 生产兼容性、C10H22 热化学、Cao Case 2 精确 A(x)、Yi(x) 与源项空间约定，以及完整隔离段/激波串模态分类变量。研究表明，在课程与本科阶段工程研究尺度上，采用“来源分级—公式审计—单元测试—数值验证—证据冻结—可视化交付”的开发路线，可以显著提高准一维超燃冲压数值项目的可复现性与科学可辩护性。

**关键词：** 超燃冲压发动机；双模态冲压发动机；准一维 CFD；有限体积法；变热化学；数值验证；燃烧模态；可复现计算

## Abstract

A reproducible quasi-one-dimensional CFD and evidence-management framework is developed for rapid analysis of scramjet and dual-mode ramjet combustors. The teacher-provided Chapter 11 model and the doctoral dissertation of Ruifeng Cao are treated as the primary project authorities. The solver integrates variable-area compressible conservation equations, wall-friction and fuel-injection source terms, mixing/combustion closures, composition-dependent thermochemistry, teacher-compatible boundary conditions, SSP-RK3 pseudo-time marching, and the Eq.11.46 maximum relative density-change diagnostic. The current integrated H₂/C₂H₄ production path uses a Rusanov interface flux. The teacher Steger-Warming formulation is retained as an audited constant-property path, while its direct production use with the current absolute-species-energy thermochemistry remains gated pending an explicit compatibility derivation.

The project separates numerical verification, model validation, source reproduction, and project-defined sensitivity studies. Accepted evidence includes an integrated project-defined H₂ case, 20/40/80-cell grid-trend analysis, discrete conservation audits, a NASA Burrows-Kurkov reduced-order computational-reference benchmark, equivalence-ratio response studies, scoped application of the Cao thermal-throat criterion, automated regression testing, and a mentor-facing web dashboard. The project deliberately avoids claiming formal grid independence, exact Cao Case 2 reproduction, experimental validation of the current project-defined H₂ case, or complete dual-mode/unstart prediction where the required source variables are unavailable. Machine-readable acceptance records, provenance metadata, GitHub Actions and SHA-256 artifact integrity are used to make each accepted conclusion traceable and reproducible.

**Keywords:** scramjet; dual-mode ramjet; quasi-one-dimensional CFD; finite-volume method; thermochemistry; verification; combustion-mode transition; reproducibility

---

## 1 引言

超燃冲压发动机通过在高速来流条件下维持燃烧室内高马赫数流动实现高超声速推进，是高超声速飞行器的重要动力方案之一。与二维/三维 RANS、LES 或更高保真度数值模拟相比，准一维模型不能解析横向涡结构、边界层细节和复杂激波-燃烧相互作用，但其计算成本低、参数含义清晰，适合用于前期方案设计、参数敏感性分析、控制研究和大量工况快速计算[3-10]。

本文项目的目标并非构建一个“功能越多越好”的黑箱求解器，而是建立一条可追溯的计算链：任何物理模型必须区分教师来源、公开论文来源与项目自定义假设；任何数值结论必须能够追溯至输入、代码版本、工作流和结果文件；对缺少资料的公式不使用经验猜测补齐。该开发思想与 CFD 验证/确认领域强调的“verification 与 validation 分离”相一致[11,17]。

本项目最初从理想气体、一维 Euler 方程和基础数值通量开始，随后逐步发展为以教师 Chapter 11 为主线的 H₂/C₂H₄ 准一维燃烧室求解器。当前系统已经不仅包含数值求解模块，还包括源资料审计、热化学数据库、教师公式适配器、网格与守恒验证、公开 NASA benchmark、自动化 CI、结果 provenance、Web 导师控制台以及后续参数研究框架。图 1 给出了整体科学证据和软件架构。

![图1 项目科学证据与软件架构](assets/fig1_architecture.svg)

## 2 模型来源与证据分级

### 2.1 主要来源

本项目的首要模型来源为教师提供的《高超声速气动布局理论及应用》第 11 章“双模态冲压发动机一维数值模拟”[1]。其中使用了混合效率、完全混合长度、化学计量关系、壁面摩阻、壁面换热经验式、燃料/动量/能量源项、Steger-Warming 通量分裂、CFL 时间步以及稳态判据等关系。

第二类主要来源为曹瑞峰 2016 年博士学位论文《超燃冲压发动机燃烧模态转换及其控制方法研究》[2]。本项目已经冻结了该论文 Case 2 的入口条件与 Eq.(3-2) 热喉判据，但尚未获得正式复现所需的完整 A(x)、Yi(x) 空间分布与燃料/源项空间约定，因此项目定义 H₂ 算例始终标记为 PROJECT_DEFINED，而不是 Cao Case 2 reproduction。

### 2.2 外部同行评议文献的作用

公开文献主要用于三类用途。第一类是证明准一维 scramjet 模型、混合受限燃烧、壁面摩阻、燃料喷注与热交换等处理属于已建立的工程建模路线[5-10]。第二类是用于数值方法与 Steger-Warming 扩展的背景审计[12-15]。第三类是用于验证燃烧模态转换边界并非一个脱离几何、壁面状态和喷注方式的“通用 φ 阈值”[3,4]。

本文不允许外部文献覆盖教师公式，也不允许从另一篇论文直接拷贝缺失系数来“补齐”教师模型。外部来源仅在状态变量、假设和适用范围明确兼容时才可进入生产路径。
