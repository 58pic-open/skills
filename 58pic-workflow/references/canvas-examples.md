# 画布示例与修改方式

## 完整文本流水线

[`text-pipeline.canvas.json`](text-pipeline.canvas.json) 是一个不依赖模型 ID 或外部资源的完整示例：

```text
text → text_array → text_list → output
```

它展示了：

- 普通节点使用 `type: "default"`。
- `customType` 与 `customeData.params` 的对应关系。
- 句柄同时保存在节点顶层和 `data.handles`。
- 边通过节点 ID 与句柄 ID 建立连接。
- `text_array` 先经过 `text_list`，再连接 `output`。

复制到工作目录后先验证：

```bash
node <skill-dir>/scripts/validate_canvas.mjs \
  <skill-dir>/references/text-pipeline.canvas.json
```

创建工作流：

```bash
58pic workflow create "文本拆分与选择示例" \
  --canvas-file <skill-dir>/references/text-pipeline.canvas.json \
  --format json
```

创建会产生真实工作流数据。执行前应先打开详情页确认节点和连线。

## 修改已有工作流

不要从示例覆盖已有画布。先读取，再做最小修改：

```bash
58pic workflow get <workflow-id> --format json > workflow-response.json
node <skill-dir>/scripts/extract_canvas.mjs workflow-response.json workflow.json
```

例如只修改一个 `text` 节点：

```json
{
  "data": {
    "customType": "text",
    "customeData": {
      "params": {
        "prompt": "新的静态文本"
      }
    }
  }
}
```

这只是“要修改的路径”，不是保存文件。实际操作必须在完整 `workflow.json` 中更新该字段，保留节点其它 `customeData`、句柄和结果。

验证并保存：

```bash
node <skill-dir>/scripts/validate_canvas.mjs workflow.json
58pic workflow save <workflow-id> --canvas-file workflow.json --format json
58pic workflow get <workflow-id> --format json > saved-response.json
node <skill-dir>/scripts/extract_canvas.mjs saved-response.json saved-workflow.json
node <skill-dir>/scripts/validate_canvas.mjs saved-workflow.json
```

## 新增生成类节点

不要从文档硬编码模型 ID。正确流程：

1. 找到一个可用的同类工作流。
2. 使用 `workflow get` 读取真实节点。
3. 复制整个同类型节点，包括全部 `params`、`result` 和未知字段。
4. 生成新的节点 ID、句柄 ID，并修正新边引用。
5. 只替换用户明确要求的 `prompt`、比例、参考图等字段。
6. 验证完整画布后保存。

如果没有真实同类节点或实时模型信息，不要猜测 `model`、`version`、比例枚举等值。

## 新增边

新增边前找到：

- 源节点的 `source` 句柄 ID。
- 目标节点的 `target` 句柄 ID。
- 两个句柄的 `dataType`。
- 目标节点允许的输入类型与连接数量。

然后创建：

```json
{
  "id": "edge-unique-id",
  "source": "node-source-id",
  "target": "node-target-id",
  "sourceHandle": "handle-source-id",
  "targetHandle": "handle-target-id",
  "type": "default"
}
```

不要遗漏句柄 ID，也不要引用 `data.handles` 与顶层 `handles` 中不存在的句柄。

## 新建分组

假设两个节点绝对坐标分别为 `(180, 160)`、`(520, 160)`，新组位置为 `(100, 80)`：

1. 创建 `type: "group"` 的组节点，位置为 `(100, 80)`。
2. 为两个子节点设置同一个 `parentId`。
3. 子节点坐标分别改为 `(80, 80)`、`(420, 80)`。
4. 设置组 `style.width/height` 覆盖全部节点并留出边距。
5. 边仍引用原节点和句柄 ID，无需因打组重建。

详细公式见 [connections-and-groups.md](connections-and-groups.md)。

## 不应执行的操作

- 用示例中的 ID 与现有节点混合，造成重复 ID。
- 把 `customeData` 改名为 `customData`。
- 用只含一个新增节点的文件调用 `workflow save`。
- 删除未知节点、未知参数或现有结果。
- 给组内节点写 `parentId` 后继续保留绝对坐标。
- 重新排列 `video_concat` 的入边。
- 手工填写成功状态或伪造运行结果。
