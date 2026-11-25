# 实际执行记录与脚本源码

这里保存本技能覆盖的混剪、本地化及画幅适配工作流中能核实实际运行的脚本，不收录仅查阅、仅看帮助或没有执行证据的脚本。临时脚本已清理的，从原对话文件变更恢复最后保存的版本。不是为文档新写然后假称运行过的脚本。

**文件是历史源码记录（`.py.txt` 或 `.ps1.txt`），不是开箱即用的 CLI。** 剪辑和质检逻辑、函数及 FFmpeg 滤镜被保留；个人和项目输入被移除。遇到 `PROJECT_INPUT`、`PROJECT_NUMBER` 或 `<PROJECT_VALUE>`，要用新项目的实际资产、样片验收值和输出要求补齐。部分脚本曾直接替换成片或写入输出，复跑应先审查文件操作并使用独立输出目录。不要将历史样例的分支结构当作产品默认值。

## AaddB 剪辑

1. 实际先用 [B 面盘点](executed-scripts/aaddb/analyze_b_library.py.txt) 读取技术规格和生成联系表，再用 [旧尾板检查](executed-scripts/aaddb/inspect_old_endcard.py.txt) 抽查尾部，人工确定正文结尾与旧尾板切点。
2. 第一批使用 [A+B 批量拼接](executed-scripts/aaddb/batch_ab_approved.py.txt)。它读取已确定好的切点，按目标画幅处理画面，合成 A、B 和新尾板，随后核对输出。
3. 另一批先用 [A+B 预览](executed-scripts/aaddb/render_aabb2_preview.py.txt) 试剪，画面和音频分别指定截止时间；再用 [多语言/画幅批次渲染](executed-scripts/aaddb/render_ab2.py.txt)。转场反馈后，用 [返工脚本](executed-scripts/aaddb/repair_ab2.py.txt) 先跑预览模式再批量，而非直接覆盖第一版。

## 本地化与画幅适配

| 当时执行的步骤 | 实际脚本 |
| --- | --- |
| 纯净版样片：复用已确认 WAV；转出词级时间；校准最终文案、配音速度和字幕；同时做原生与延展版本；探测卡套透明区。 | [词级转写](executed-scripts/localization/transcribe_batch.py.txt)、[语言样片](executed-scripts/localization/local_en_sample.py.txt)、[透明区/联系表](executed-scripts/localization/frame_inspection.py.txt) |
| 纯净版批量：按主体时长对齐每种配音，按语言和画幅合成主体、字幕、配音及尾板；探测规格、完整解码、抽帧比对尾板、测响度。 | [批量渲染](executed-scripts/localization/local_full.py.txt)、[逐条质检](executed-scripts/localization/local_qc.py.txt) |
| 纯净版返工：实测字体边界、放大字幕并重新渲染，复制原音轨；比对音轨哈希和尾板；原生画幅另做无框重渲染。 | [字幕返工](executed-scripts/localization/local_cjk_large.py.txt)、[返工比对与交付](executed-scripts/localization/local_cjk_qc.py.txt)、[原生画幅重渲染](executed-scripts/localization/local_native_vertical.py.txt) |
| 只有烧录字幕的源片：测原字幕位置和区间，先做遮盖样片；移除主体原混音，另混 BGM 和配音；再按素材、语言、尺寸批量，逐条验收，另做原生画幅返工。 | [遮盖样片](executed-scripts/localization/pov_sample.py.txt)、[遮盖与混音批量](executed-scripts/localization/pov_batch.py.txt)、[逐条质检](executed-scripts/localization/pov_qa.py.txt)、[原画幅与遮盖返工](executed-scripts/localization/pov_native_vertical.py.txt) |
| 不重做字幕和配音：原语言成片适配尺寸、添加相应尾板并按实测尺寸命名；另有一批按缺口补尺寸。 | [保留原声字幕的成片适配](executed-scripts/localization/cn_delivery.py.txt)、[补齐尺寸](executed-scripts/localization/complete_missing_sizes.py.txt) |
| 早期语言版：批量生成 LOGO 和尺寸版本，返工 LOGO，补一条素材；另试做推进样片后返工尾板。 | [语言版渲染](executed-scripts/localization/render_asset_batch.ps1.txt)、[LOGO 返工](executed-scripts/localization/revise_asset_batch_logos.ps1.txt)、[追加素材](executed-scripts/localization/render_extra_source_variants.ps1.txt)、[推进样片](executed-scripts/localization/push_transition_sample.ps1.txt)、[尾板返工](executed-scripts/localization/reprocess_endboard.ps1.txt) |

文件批量改名当时用的是当次 PowerShell 命令：先建立原名→目标名映射并逐条读出实际尺寸；确认无冲突才重命名；最后回读目录并按版本矩阵核数。没有把当时的命名映射写进可复用技能。

## VoxCPM 部署与已做的验证

官方地址和换机自动部署见 [VoxCPM 说明](voxcpm.md)。技能所带的 [安装器](../scripts/install-voxcpm.ps1) 在这次验证走了无修改计划模式，没有重新安装现有环境；[推理验收脚本](../scripts/smoke_voxcpm.py) 在既有本地 VoxCPM2 环境实际生成了 WAV。剪辑任务使用的是已确认配音文件；不把设备检查、短句冒烟测试或读取过的合成脚本夸大成在此重新生成并验收了全套配音。
