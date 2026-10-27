# 贡献指南

1. Skill 位于 `skills/conversation-handoff/`，必须保持 UTF-8 `SKILL.md` 与 `agents/openai.yaml`。
2. 禁止提交真实对话、交接包、附件、账号、邮箱、设备名、路径、登录态、Token、Cookie、密码、密钥或运行日志。
3. 必须保持 `allow_implicit_invocation: false`；普通摘要、会议纪要或无关文档任务不得触发本 Skill。
4. 不得扩大为云同步、自动上传、账号切换或旧授权重放工具。
5. 带脚本的改动必须增加或更新离线测试；测试只使用临时目录和虚构消息。
6. 打包或提取逻辑必须继续拒绝路径穿越、链接、名称冲突、覆盖和清单不一致。
7. 提交前运行 README 中的全部验证命令。

