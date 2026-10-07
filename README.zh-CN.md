# Knowledgebase Studio

[English](README.md) | **简体中文**

Knowledgebase Studio 是一个面向 Codex 的知识库生产插件。它能把零散资料整理成一套可追溯、可学习、可验证，并且达到发布标准的 Markdown 知识库。

它不把“文件齐了”“链接能开”或“报告写完了”当作完成，而是把资料理解、知识建模、学习设计、内容生产、应用验收和发布质检串成一条可以中断续跑的工作流。每个阶段都有语义门禁：只有真实交付物和当前证据同时通过检查，流程才能继续。

## 它能做什么

插件采用证据优先的八阶段流程：

```text
需求锁定 intake → 资料审计 audit → 架构设计 architecture → 样章试做 pilot
→ 内容生产 content → 应用验收 app → 质量检查 QC → 本地发布 release
```

- 正式生产前先锁定产品形态、目标读者、学习压力、资料呈现方式和发布边界。
- 审计来源资料，记录其中的主张、机制、适用边界、相互冲突和未知项。
- 建立可追溯的知识单元，明确每个页面应该回答什么问题。
- 面向课程型知识库，检查先修关系、案例、练习、反馈、阅读负荷和知识迁移证据。
- 从“资料齐全”走向“能解释、会判断”：补充机制、可推理的比喻、贴近结论的不确定性和可迁移的判断方法。重要数字可在现有资料账本中记录口径、核验状态和跨来源比较条件，由内容检查器核验。
- 操作课串起“做什么—可能看到什么—怎么检查—如何继续或恢复”，支持纯文字教学，不强制录屏。
- 学习设计、内容、页面与质检共用教学活动约定：按依据反馈、可选分层提示、修订、变式迁移和文字说明；不把点击或填空当成掌握。
- 支持只更新几课的增量检查，保留整库旧验收的真实状态；功能检查、编辑审查与真实学员学习效果分开记录。
- 判断视觉解释是否真的必要；需要时验收已经嵌入页面的静态图或动效，以及来源一致性、替代文本和静态回退。
- 验证读者真正看到的内容和应用，而不是只检查总结报告。
- 为阶段证据和真实交付物生成指纹；内容一旦变化，下游的旧结论会自动失效。
- 先生成隔离的本地发布包。除非用户另行授权，流程不会擅自上传、托管或公开发布。

## 内置技能

| 技能 | 负责什么 |
| --- | --- |
| `structured-knowledgebase-builder` | 编排整条工作流，保存进度，并从断点继续 |
| `knowledgebase-auditor` | 盘点现有知识库，审计资料和内容基础 |
| `knowledgebase-architect` | 设计知识模型、信息架构和迁移方案 |
| `knowledgebase-learning-reviewer` | 检查学习路径、练习反馈和迁移设计 |
| `knowledgebase-visual-explainer` | 在文字不足时制作并验收忠于来源的图解或解释动效 |
| `knowledgebase-content-builder` | 先做代表性样章，再生产忠于来源的完整内容 |
| `knowledgebase-app-builder` | 构建或验收本地 Markdown 知识库应用 |
| `knowledgebase-qc-release` | 执行最终质检，并验证隔离的发布包 |

仓库还提供一组不依赖第三方库的 Python 工具，用于资料审计、内容一致性检查、视觉素材验收、阶段语义门禁、发布包检查和工作流状态管理。

## 运行要求

- 支持插件市场的 Codex 版本
- Python 3.10 或更高版本
- Git，用于从源码安装

所有验证脚本只使用 Python 标准库。

## 从源码安装

把插件克隆到个人插件市场使用的插件目录：

```bash
git clone https://github.com/zhongky1995/knowledgebase-studio.git ~/plugins/knowledgebase-studio
```

确认 `~/.agents/plugins/marketplace.json` 的 `plugins` 数组中已有一个本地插件条目，并且路径指向 `./plugins/knowledgebase-studio`。然后安装插件：

```bash
codex plugin add knowledgebase-studio@personal
```

如果你的插件市场不叫 `personal`，请替换成实际名称。安装完成后新建一个 Codex 任务，让八个技能重新加载。

## 怎么使用

直接用自然语言告诉 Codex 你想完成什么，例如：

- `完整审计并修复这个知识库，做到本地发布可用。`
- `把这些资料做成有学习坡度、案例和练习反馈的课程型知识库。`
- `从上次断点继续知识库自动流程。`
- `只完善这两课的操作步骤和可选判断练习，验证当前改动，不重建整库。`

如果需要手动启动完整工作流，可以在目标知识库下初始化持久状态：

```bash
python3 scripts/kb_workflow.py init \
  --root /path/to/knowledge-base \
  --goal "完成一个可以发布的课程型知识库" \
  --mode auto \
  --app auto
```

查看下一阶段，或核验当前证据是否仍然有效：

```bash
python3 scripts/kb_workflow.py next --root /path/to/knowledge-base
python3 scripts/kb_workflow.py check --root /path/to/knowledge-base
```

只想检查某一类问题时，可以单独运行对应工具：

```bash
python3 scripts/kb_audit.py /path/to/knowledge-base --strict
python3 scripts/kb_content_check.py /path/to/knowledge-base --phase content
python3 scripts/kb_visual_check.py /path/to/knowledge-base
python3 scripts/kb_learning_check.py /path/to/knowledge-base --phase content
python3 scripts/kb_stage_check.py /path/to/knowledge-base --stage qc
python3 scripts/kb_release_check.py /path/to/release-root
```

工作流证据会保存在 `<knowledge-base>/_kb-control/`。请不要手动修改 `workflow.json`；通过控制器命令更新状态，才能保证阶段修订、证据指纹和失效关系一致。

只更新部分课节时，使用 `scripts/kb_update.py plan` 和 `check`。操作与证据要求见[增量更新说明](skills/structured-knowledgebase-builder/references/incremental-updates.md)。新模板采用学习设计 schema 3、内容覆盖 schema 2，旧版设计仍可读取。交互不是必选项；共享字段与检查边界见[教学活动设计说明](skills/knowledgebase-learning-reviewer/references/learning-activity-design.md)。

## 工作原则

1. **先理解资料，再组织页面。** 先弄清主张和边界，避免只是重新排列原文。
2. **先确定产品形态，再打磨表现。** 页面做得漂亮，不代表它引导了正确的学习或使用行为。
3. **先验证样章，再批量生产。** 用一个有代表性的内容切片验证方向，避免把错误放大到整个知识库。
4. **用证据决定状态。** 阶段报告、当前证据和真实交付物必须同时通过，才能标记完成。
5. **先解释，再装饰。** 只有当图解或动效确实让关系与变化更容易理解时才添加视觉素材。
6. **先达到本地发布标准，再决定是否公开。** 生成发布包不等于授权上传、托管或对外发送。

## 参与开发

[从证据到判断的设计说明](skills/knowledgebase-content-builder/references/evidence-to-judgment.md)吸收了 [huashu-report](https://github.com/alchaincyf/huashu-report) 的读者用途优先、先核数据再写作、解释深度和机械规则工具化理念；未照搬报告版式、篇幅配额或渲染代码，也不宣称已经证明学习效果。

运行完整测试：

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py'
```

贡献代码或文档前，请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。如果发现安全问题，请按 [SECURITY.md](SECURITY.md) 的方式私密报告，不要直接创建公开 Issue。

## 开源许可

Knowledgebase Studio 使用 [MIT License](LICENSE) 开源。

## 零基础原理解说

当目标是“理解系统如何工作”时，可采用 `novice_mental_model` 解释配置：先用一个完整日常事件连接全貌，再拆分概念页。机制示范直接展示参与者、动作、传递过程、结果和变化条件；判断与创作案例继续使用初稿、判断和修改过程。样章检查要求定位到真实正文的理解证据，并区分编辑审读、模拟审读与真实读者观察。图解要让关系可见，Markdown 要检查最终页面。配置与字段见 [零基础原理解说指南](skills/knowledgebase-content-builder/references/novice-mental-model.md)。这些检查能拦住缺项和无效证据，不能自动证明读者理解。

## 图解设计与实际样例

[图解规范](skills/knowledgebase-visual-explainer/references/diagram-design-system.md)提供字阶、间距、语义配色、箭头、边框和移动端布局标准。[本地图型样例](assets/visual-patterns/index.html)包含四组可编辑 SVG 与反例，可用 `python3 scripts/kb_visual_examples.py --output <目录>` 重建。新制作或重设计的图解使用视觉清单 schema 2，保存实际手机/桌面截图、显示字号、具体设计观察和文件指纹；检查程序验证记录与文件的一致性，实际效果仍需审图。旧 schema 1 保持兼容并明确提示缺少新版设计审读。
