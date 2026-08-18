---
name: 58pic-workflow
description: |
  Create, inspect, preserve, save, and run 千图工作流 through the official 58pic CLI.
  Use when users mention 千图工作流, workflow canvas, nodes, edges, customeData,
  parentId, group nodes, or Agent workflow automation.
allowed-tools: Bash
---

# 千图工作流（58pic Workflow）

把 Agent 的创意方案落到可编辑、可复用、可运行的千图工作流画布。所有操作使用 `58pic workflow` 命令完成。

完整图文教程：[千图工作流 CLI 使用指南](https://58pic-qiye.feishu.cn/docx/OIA4dBDgVomVLxxVYJgcYfeonyb)

## 这会改变什么

- Agent 能先读取真实画布，再新增或调整节点、连线和输入，最后保存并运行。
- 画布是生产资产。保存时必须保留未修改字段，尤其是 `data.customeData`、`parentId`、节点坐标和边的句柄字段。

## 适用场景

1. 将一段创意需求变成可反复执行的海报、商品图或视频生产链路。
2. 读取已有工作流，替换提示词、模型参数、参考图或输出节点配置后另存或覆盖保存。
3. 批量运行同一画布，给不同的 `prompt`、图片或 JSON 输入。
4. 让团队沉淀一份可审查、可编辑的节点编排，而不是只保留一次性的生成结果。

## 参考资料路由

按任务读取需要的资料，不要一次加载全部：

- 修改画布结构、节点通用字段或结果：读 [`references/canvas-schema.md`](references/canvas-schema.md)。
- 选择节点或修改节点参数：读 [`references/node-catalog.md`](references/node-catalog.md)。
- 新增连线、句柄、分组或调整布局：读 [`references/connections-and-groups.md`](references/connections-and-groups.md)。
- 从零创建画布或查看完整 JSON：读 [`references/canvas-examples.md`](references/canvas-examples.md)。
- 保存前运行 `scripts/validate_canvas.mjs`；处理 `workflow get --format json` 输出时先运行 `scripts/extract_canvas.mjs`。

## 前置条件与认证

确认 Node.js 18+，并检查 CLI 与认证状态：

```bash
58pic --version || npm install -g @58pic/cli
58pic auth status
```

未认证时二选一：

```bash
# 推荐：打开浏览器登录
58pic auth login

# 自动化：在“已授权应用”创建 sk_ API Key 后写入本地配置
58pic config init --api-key sk_YOUR_API_KEY
```

不要在聊天、日志、画布 JSON 或仓库中打印或提交完整 API Key / OAuth Token。

## 使用方式

### 1. 先列出并读取真实画布

```bash
58pic workflow list --page 1 --page-size 20 --format json
58pic workflow get <workflow-id> --format json > workflow-response.json
node <skill-dir>/scripts/extract_canvas.mjs workflow-response.json workflow.json
```

需要查看某次历史执行结果时才给 `get` 传 `--version`：

```bash
58pic workflow get <workflow-id> --version <execution-id> --format json
```

`version` 用于指定历史执行回显。画布保存文件必须包含 `nodes`，建议同时包含 `edges`；运行时无需传 `version`。

### 2. 创建工作流

只创建元数据：

```bash
58pic workflow create "春日活动海报" \
  --description "输入文案后生成活动海报" \
  --format json
```

从已有画布初始化（文件顶层为 `nodes`、`edges`，可选 `name`、`deductPoints`）：

```bash
58pic workflow create "春日活动海报" \
  --canvas-file ./canvas.json \
  --format json
```

### 3. 按协议编辑并完整保存

**先 `get`，后编辑，最后完整保存。** 不要根据旧的 `docs/workflow-example.md` 重新构造画布。

普通业务节点使用 `type: "default"`，业务类型放在 `data.customType`。详细结构见 [`references/canvas-schema.md`](references/canvas-schema.md)，完整示例见 [`references/text-pipeline.canvas.json`](references/text-pipeline.canvas.json)。

编辑完成后先做本地结构校验：

```bash
node <skill-dir>/scripts/validate_canvas.mjs ./canvas.json
```

保存：

```bash
58pic workflow save <workflow-id> --canvas-file ./canvas.json --format json
```

### 4. 运行

运行整个工作流：

```bash
58pic workflow run <workflow-id> \
  --input '{"prompt":"春日上新海报，清新绿色，竖版"}' \
  --format json
```

只运行一个节点：

```bash
58pic workflow run <workflow-id> \
  --node <node-id> \
  --input '{"prompt":"替换后的文案"}' \
  --regular-model \
  --format json
```

运行可能消耗积分并创建执行记录。先让用户确认会执行/扣点的操作；不要把 `--node` 当作无副作用的预览。

## 完成后返回工作流详情页

当针对单个工作流的读取、创建、保存或运行已经明确成功，并且已经取得真实工作流 ID 时，在最终回复中附上可直接打开的详情页：

```text
https://workflow.58pic.com/zh/workflow/<workflow-id>
```

例如工作流 ID 为 `4923`：

```text
https://workflow.58pic.com/zh/workflow/4923
```

推荐回复格式：

```markdown
工作流已保存：[打开工作流详情](https://workflow.58pic.com/zh/workflow/4923)
```

- `create` 必须使用成功响应返回的真实工作流 ID。
- `get`、`save`、`run` 成功后可以使用对应命令中的工作流 ID。
- 请求失败、结果状态不明确或没有取得真实 ID 时，不要声称已完成，也不要猜测详情页链接。

## 画布硬规则

- 普通业务节点使用 `type: "default"`；不要继续使用旧示例中的 `type: "custom"`。
- `data.customeData` 的历史拼写不能改成 `customData`。
- 节点句柄同时可能存在于顶层 `handles` 和 `data.handles`；修改时保持一致。
- 边必须保留 `sourceHandle` 和 `targetHandle`，并引用对应节点中真实存在的句柄。
- `parentId` 必须指向一个存在且 `type: "group"` 的节点。
- 组父节点使用画布绝对坐标；组内子节点使用相对父组坐标。
- 不要提交仅含增量节点的保存文件。`workflow save` 是完整画布保存，至少需要完整 `nodes`；建议同时提交完整 `edges`。
- 不要删除未知字段、未知节点类型、节点 `data` 中的配置和结果。Agent 无法理解的字段应原样透传。
- 不要保存 `connectionPlaceholder` 临时节点。
- 生成类节点的模型字段以真实节点和实时能力为准，不要从静态文档猜模型 ID。

## FAQ

### 为什么不要继续使用旧的 `docs/workflow-example.md`？

它可能与当前画布不一致。先执行 `workflow get`，以实际返回的画布为准再修改。

### API Key 和 OAuth 怎么选？

本地交互和 Agent 推荐 OAuth；CI 或自动化任务可使用 API Key。两种方式都不要将密钥写入仓库或日志。

### 我只想改一个字段，为什么仍要保存完整 `nodes`/`edges`？

画布中包含节点参数、端口、分组关系和坐标。增量拼装极易丢失这些持久化数据；先读取，再对最小字段做补丁，然后完整保存。
