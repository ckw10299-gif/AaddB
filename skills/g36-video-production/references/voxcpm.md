# VoxCPM2 自动部署与配音

官方源：[OpenBMB/VoxCPM](https://github.com/OpenBMB/VoxCPM)，[安装文档](https://voxcpm.readthedocs.io/en/latest/installation.html)，[启动与短句示例](https://voxcpm.readthedocs.io/en/latest/quickstart.html)。Python/PyTorch/GPU 兼容性以目标机器为准。用户当时的原始部署指令：“帮我把这个部署到本地：OpenBMB/VoxCPM”。

## 1. 优先复用

同文案有确认 WAV 时直接用，不需要启动 VoxCPM。确需合成时，先查现有的 VoxCPM 项目目录和 `.venv`。已有启动器时优先复用，保留启动日志和错误日志。默认本地地址 `http://127.0.0.1:8808/`，在用户自己的浏览器使用。端口若被其他服务占用，换端口或报告，不杀不明进程。

## 2. 自动部署（Windows）

只有用户要求部署，或确需生成且授权配置环境时，才实际安装软件。以下命令在技能目录运行；新机默认安装到 `%LOCALAPPDATA%\G36Tools\VoxCPM`，改位置用 `-InstallDir`。先计划再执行：

```powershell
powershell -NoProfile -File .\scripts\install-voxcpm.ps1 -PlanOnly
powershell -NoProfile -File .\scripts\install-voxcpm.ps1 -Device cpu
# 有 NVIDIA GPU：先在官方 PyTorch 选择器选 Windows / Pip / 支持的 CUDA，
# 把该命令里的 --index-url 传给下列参数。示例 URL 不代表所有显卡都适用。
# powershell -NoProfile -File .\scripts\install-voxcpm.ps1 -Device cuda -TorchIndexUrl https://download.pytorch.org/whl/cu128
```

自动流程：检查 Python 3.11 和 Git，缺失且有 winget 时从明确包 ID 安装；从官方仓库克隆到新目录，使用 `.venv`，只在该环境内安装 PyTorch 和项目依赖；执行 `pip check`，验证设备和导入；通过官方模型 ID下载/复用权重，实际合成短句并验证 WAV；生成 `Start-VoxCPM.cmd`。如需加速，使用 [PyTorch 官方选择器](https://pytorch.org/get-started/locally/) 的 wheel index。显式选择 CUDA 却不可用时脚本报错，不把 CPU 静默说成 GPU 成功。可选 `-Revision` 固定新克隆的 Git 版本，已有项目不自动更新。默认不会重装通过验收的已有环境。

换机交接要记录 Git commit、Python/PyTorch/设备、权重来源、验证 WAV 位置。安装器只验证模型推理能产出声音；正式使用前还须验证目标语言、参考音色和语速。已有经批准完整模型快照时用 `-ModelPath`；启动器也会使用同一快照。Windows 无 winget、代理限制、或 Python/Git 无法安装时，说明具体失败命令，让用户用官方安装渠道准备依赖再重试。

## 3. 排障与生产

- 页面能开或 HTTP 200 **不等于模型可用**。首次下载/加载可能较慢，查看下载日志和本地缓存进度，禁止重复提交。遇下载不完整，优先复用已验证快照或恢复官方下载，不删除旧模型。Windows 遇 torch.compile/Triton 故障，先用兼容模式验证推理；参考 [官方 FAQ](https://voxcpm.readthedocs.io/en/latest/faq.html)。
- 使用 UI 的 Target Text 填最终广告台词；Control Instruction 填音色、音高、语言口音、语速、情绪。先跑一句试听，再跑全文。要固定声线用已确认且有权使用的参考 WAV；若用需要原文的克隆模式，填该录音真实念的原台词，不填目标台词。
- 这批确认风格：清亮少年男声、像自然和朋友交谈、轻松自信带一点俏皮；繁中用台湾国语带笑意。没有确认原声时可先用文字设计试听，但不要把文字描述当作固定音色。
- 四语可用本地 CLI/SDK 批量，或复用历史脚本的队列逻辑；不同版本的 Gradio 接口参数可能不同，先查实际 API，不硬套旧 `predict` 位置参数。保存声线参考、台词、参数、可播放 WAV，失败只重跑对应语言。试听目标语言、产品词、漏读和最后一句，再交给本地化流程做时间对齐。
