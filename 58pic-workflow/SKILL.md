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
58pic workflow get <workflow-id> --format json > workflow.json
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

`canvas.json` 的最小骨架如下；实际节点的 `data` 需保留 `get` 返回的原字段：

```json
{
  "name": "春日活动海报",
  "nodes": [
    {
      "id": "node-input",
      "type": "custom",
      "position": { "x": 120, "y": 160 },
      "data": {
        "customType": "user_input",
        "customeData": {
          "params": { "prompt": "春日活动海报" }
        }
      }
    }
  ],
  "edges": []
}
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

## 当前画布数据约定（以 master 为准）

| 对象 | 必须保留的字段 | 说明 |
|---|---|---|
| 工作流 | `id`、`version`、`name`、`nodes`、`edges` | `version` 随读取结果保留；仅 `get --version` 用于指定历史执行回显。 |
| 节点 | `id`、`type`、`position`、`data` | `data.customType` 标识节点业务类型；不要只保留展示文本。 |
| 节点业务数据 | `data.customeData` | 历史字段拼写就是 `customeData`，**不能**改成 `customData`。其内的 `params`、`result`、`name`、`index` 等按原样保留，按目标字段做最小修改。 |
| 边 | `id`、`source`、`target`、`sourceHandle`、`targetHandle`、`type`、`data` | 句柄字段决定节点端口的连接关系；不能只按 source/target 重新生成。 |
| 分组 | `type: "group"`、`style.width/height`、`parentId` | 分组父节点在画布坐标系中定位；组内子节点以 `parentId` 关联，并使用相对父组的坐标。解组时子节点才恢复画布绝对坐标。编辑既有分组时必须保留返回的坐标体系，不要自行把子节点全部绝对化或相对化。 |

补充规则：

- `parentId` 必须指向一个存在且 `type: "group"` 的节点。
- 新建组需要父节点的 `style.width` / `style.height` 覆盖子节点区域；子节点位置须与父组坐标匹配。
- 不要提交仅含增量节点的保存文件。`workflow save` 是完整画布保存，至少需要完整 `nodes`；建议同时提交完整 `edges`。
- 不要删除未知字段、未知节点类型、节点 `data` 中的配置和结果。Agent 无法理解的字段应原样透传。

## FAQ

### 为什么不要继续使用旧的 `docs/workflow-example.md`？

它可能与当前画布不一致。先执行 `workflow get`，以实际返回的画布为准再修改。

### API Key 和 OAuth 怎么选？

本地交互和 Agent 推荐 OAuth；CI 或自动化任务可使用 API Key。两种方式都不要将密钥写入仓库或日志。

### 我只想改一个字段，为什么仍要保存完整 `nodes`/`edges`？

画布中包含节点参数、端口、分组关系和坐标。增量拼装极易丢失这些持久化数据；先读取，再对最小字段做补丁，然后完整保存。
