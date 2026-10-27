# 跨对话交接 Skill

一个用于长 ChatGPT／Codex 对话迁移的显式调用 Skill：保存可访问的完整可见消息记录、详细语义交接和可验证清单，让新对话能从可靠断点继续。

> A verified long-conversation handoff skill with a complete visible transcript, detailed working memory, and manifest-based integrity checks.

[![Skill](https://img.shields.io/badge/skill-1-2563eb)](#核心能力)
[![Explicit only](https://img.shields.io/badge/invocation-explicit--only-d97706)](#安全边界)
[![Offline](https://img.shields.io/badge/network-none-16a34a)](#安全边界)
[![License: MIT](https://img.shields.io/badge/license-MIT-16a34a)](LICENSE)

## 为什么不能只写一段摘要

长对话中的纠正、拒绝方案、文件状态、测试证据和未完成事项往往散落在不同位置。一段摘要可能很好读，却无法证明有没有漏掉关键上下文。

本 Skill 同时保存两层材料：

1. `FULL_TRANSCRIPT.jsonl`：可访问的全部用户可见 user／assistant 消息；
2. `DETAILED_HANDOFF.md`：带消息序号依据的详细工作记忆。

接收方必须先验证清单和哈希，再阅读语义交接与关键原文。它不会把“99%记忆”伪装成可测量保证。

## 核心能力

| 模式 | 用途 | 输出或行为 |
|---|---|---|
| Create | 从明确指定的 Codex 会话或用户提供的完整 JSONL 建立交接包 | 新目录、完整可见记录、索引、详细交接模板和 ZIP |
| Audit | 检查目录或 ZIP 是否完整、安全且与清单一致 | 只报告验证证据，不自动恢复任务 |
| Resume | 从验证通过的交接包恢复上下文 | 先给出继承上下文报告，再继续未完成工作 |

## 安装

正式版本请从 GitHub Releases 下载，并核对同一版本的 `SHA256SUMS.txt`。

1. 下载 `conversation-handoff-<version>.zip`。
2. 核对 SHA-256。
3. 阅读 `SKILL.md`、`agents/openai.yaml`、脚本和安全说明。
4. 将完整目录复制到公共 Skill 位置：

   ```text
   C:\Users\<你的用户名>\.agents\skills\conversation-handoff
   ```

5. 重启 Codex 后，通过 `$conversation-handoff` 显式调用。

整套仓库下载文件名为 `conversation-handoff-v0.1.0.zip`。

## 安全边界

- `allow_implicit_invocation: false`，不会因为普通“总结”请求自动介入。
- 不导出 system／developer 指令、隐藏推理、原始工具负载或无关对话。
- 不读取浏览器资料、Cookie、登录态或环境变量凭据。
- 疑似文本凭据会阻止准备或定稿，且不会在错误消息中回显秘密。
- 不联网、不上传、不发送；发布或外传交接包需要新的明确授权。
- 输出必须是新目录和新 ZIP，禁止覆盖；目标不能位于 Git 仓库、Skill 目录、符号链接或 Junction 下。
- ZIP 验证会拒绝路径穿越、重复或大小写冲突名称、链接、加密成员及清单外文件。
- 图片只做字节完整性验证，不能识别图片内文字秘密；分享前仍需人工查看。
- 旧对话只提供历史证据，不会自动延续旧授权。

完整边界见 [`security-and-permissions.md`](skills/conversation-handoff/references/security-and-permissions.md)。

## 主机能力限制

Skill 是否能读取完整旧对话取决于当前宿主。没有本机 Codex 会话访问能力时，必须由用户提供完整导出或 JSONL；不能凭当前窗口中残留的上下文伪造“完整交接”。

## 开发与验证

```powershell
python -X utf8 scripts/build_catalog.py
python -X utf8 scripts/validate_repo.py
python -X utf8 scripts/package_release.py --release all --verify-only
python -X utf8 -m unittest discover -s scripts/tests -v
python -X utf8 -m unittest discover -s skills/conversation-handoff/tests -v
```

