# Seneschal

[![PyPI](https://img.shields.io/pypi/v/seneschal?label=pypi&color=blueviolet)](https://pypi.org/project/seneschal/)
[![License](https://img.shields.io/badge/license-MIT-green)](../LICENSE)

Seneschal 是一个本地优先的控制层，让 AI 工作更便宜、更安全。

它决定发送哪些上下文、哪些保留在本地、哪些必须拦截，以及某项任务是否值得动用更强的模型。目标是真正节省 token：减少整库粘贴、减少重试、缩小提示词、收窄工具权限范围，并让任务交接更清晰。

> 家宰（seneschal）负责管理家族资源，并代表主人批准行动。这个工具做的正是同一件事：**分配开销**与**授权能力**。

## 功能

- 估算 token 预算，不绑定任何特定服务商
- 在明确的预算内打包仓库上下文
- 推荐足以完成该任务的最便宜模型路径
- 保存上下文快照，避免重复发送未更改的文件
- 使用 BM25 词法相关度挑选最相关的邻近上下文
- 扫描不可信的文本与文件，检测提示注入与机密信息
- 校验以 **Ed25519 签名**的最小权限能力授权

## 安装

```bash
pip install seneschal
seneschal --help
```

可选扩展：

```bash
pip install "seneschal[measure]"    # 实测分词器 (tiktoken)
pip install "seneschal[security]"   # 签名授权 (cryptography)
```

## 签名的能力授权

未签名的授权只是一个任何进程都能编辑的 JSON 文件——代理可以伪造自己的权限。有了 Ed25519 签名，授权代理会以「失败即关闭」的方式拒绝以下情况：缺少有效签名、由不受信任的密钥签署、签名后被篡改（权限提升），或已过期。

```bash
seneschal keygen
seneschal grant --sign --task-id RH-001 --capability read --allowed-path src/ --out grant.json
seneschal grant --grant-file grant.json --require-signed --task-id RH-001 --action read --path src/main.py
```

## 它不是什么

它不是沙箱，也不是代理执行引擎。它只决定**是否**调用模型以及**发送哪些**上下文；至于模型或代理拿到权限之后做了什么，它并不加以约束。

## 状态

核心零运行时依赖。MIT 许可证。无遥测。

仓库：https://github.com/SteveBlackbeard/SENESCHAL-by-Ethernium
