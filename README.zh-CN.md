# Knowledgebase Studio

[English](README.md) | **简体中文**

围绕读者需要制作有用、连贯、有来源依据的知识产品，由持续负责的主作者/主编承担整体取舍和阅读质量。

## 按本次目标工作

诊断、设计、样稿、完整制作和局部修改各有自己的交付边界。复用已经明确的方向与授权。架构、教学、正文、图解和界面可以在制作中相互修正；样稿用于解决影响整体的真实不确定性，成熟路径可以直接推进，不默认增加样稿批准。

普通制作使用现有增量工具，不默认进入八个强制阶段。实际文稿、已有读者要求与相关来源，加上一次当前编辑判断即可形成检查依据；不必预先填写知识模型、教学矩阵、迁移图、逐页覆盖和自评等整套文件。复杂产品仍可维护确实有用的结构化资料。

独立审读依据当前疑点、影响和明确要求安排。新批次默认一位独立读者，主编结合当前产物作出取舍；需要另一视角时再追加复核，不循环修改到两个模型一致通过。反馈先定位问题成因，再选择增、删、合并、移动或替换。

## 能力与边界

八个技能分别支持协调、来源与旧库审计、内容结构、正文、学习审读、解释图解、应用和交付。按当前问题选用，不把这些能力排成每次都必须完成的工序。

程序保留来源与测量依据、计算、链接、必要素材、真实运行记录、版本绑定和发布包检查。专业检查辅助主编判断，不以记录齐全或多个通过结论代替整体责任。模型审读不证明真人学会，本地可用也不自动授权外部发布。

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

## 使用方式

可以直接提出目标，例如：

- `先判断这几章为什么读不下去，暂不改稿。`
- `按已经确定的方向继续写，发现结构问题就结合正文调整。`
- `只检查这两章的例子是否支撑观点，必要时独立审读。`

普通工作在候选文稿已存在后，使用：

```bash
python3 scripts/kb_update.py plan --root /path/to/knowledge-base \
  --path manuscript/chapter.md --page manuscript/chapter.md \
  --context _kb-control/reader-brief.md --context sources/relevant.md \
  --output _kb-control/updates/current/plan.json
python3 scripts/kb_update.py record --root /path/to/knowledge-base \
  --plan _kb-control/updates/current/plan.json --kind editor-review \
  --summary "Actual editorial reading judgment" \
  --output _kb-control/updates/current/plan.json
python3 scripts/kb_update.py check --root /path/to/knowledge-base \
  --plan _kb-control/updates/current/plan.json
```

新计划使用 schema 3。实际阅读、使用和检查后，直接在计划里记录当前编辑判断；不另写一份阶段报告。[局部工作说明](skills/structured-knowledgebase-builder/references/incremental-updates.md)介绍输入绑定、相关素材和交付检查。已经完成的独立编辑审读直接提供其决定，无须重复填写。

有实际需要时使用[独立执行说明](skills/structured-knowledgebase-builder/references/independent-execution.md)。`kb_execution.py init/run/decide/check` 调用已认证的现代 Codex CLI，保留真实会话与原始结论，并绑定主编决定与当前正文。无关队列、新手标签和已解决的历史反馈不再触发新审读；明确安排却未完成的审读、真实失败依赖仍会阻止相关完成结论。

## 旧项目兼容

旧八阶段状态、schema 1/2 增量计划和旧执行批次保留其原有合同，见[兼容说明](skills/structured-knowledgebase-builder/references/workflow-protocol.md)。新局部检查不会重置或提升旧的整体验收结论。`kb_execution.py migrate` 可显式把旧审读批次迁为主编决策模式：保留全部旧尝试，需要新的实际审读与编辑决定，迁移本身不产生通过。

## 按需使用的工具

- [原理解说](skills/knowledgebase-content-builder/references/novice-mental-model.md)与[校准示例](skills/knowledgebase-content-builder/references/explanation-regressions.md)：定位因果跳步，不把每页都变成教程。
- [读者任务复核](skills/knowledgebase-content-builder/references/reader-task-review.md)：准备当前正文与可用图解，材料准备不等于已经审读。
- `kb_work_comparison.py`：计算已声明的同任务工作量比较，保留教学假设、实测依据和适用边界。
- [图解设计](skills/knowledgebase-visual-explainer/references/diagram-design-system.md)与[图例](assets/visual-patterns/index.html)：支持实际解释素材，已有必要图解与交互检查继续有效。
- `kb_release_check.py`：检查实际要求的本地交付包及私有文件排除。真实应用需要检查实际显示和操作，普通文稿不自动要求应用建设。

## 开发验证

```bash
python3 -B -m unittest discover -s scripts -p 'test_*.py'
```

测试检查完整性与程序行为，不证明内容值得阅读。参见 [贡献说明](CONTRIBUTING.md) 和 [安全说明](SECURITY.md)。[从证据到判断](skills/knowledgebase-content-builder/references/evidence-to-judgment.md)参考了 [huashu-report](https://github.com/alchaincyf/huashu-report) 的部分写作思想，没有引入其版式、数量要求或渲染器。

## 许可证

[MIT License](LICENSE)。
