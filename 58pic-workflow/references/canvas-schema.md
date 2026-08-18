# 工作流画布数据协议

本文说明 `58pic workflow get`、`create --canvas-file` 和 `save --canvas-file` 使用的画布结构。读取已有工作流时，以接口实际返回为最高优先级；不要为了套用本文而删除未知字段。

## 目录

- [顶层结构](#顶层结构)
- [节点 Node](#节点-node)
- [句柄 Handle](#句柄-handle)
- [节点业务数据 customeData](#节点业务数据-customedata)
- [边 Edge](#边-edge)
- [结果状态](#结果状态)
- [保存与版本](#保存与版本)
- [编辑检查清单](#编辑检查清单)

## 顶层结构

CLI 画布文件至少包含完整 `nodes`，建议始终同时提交完整 `edges`：

```json
{
  "name": "工作流名称",
  "description": "可选描述",
  "version": "读取结果中的版本值",
  "deductPoints": 0,
  "nodes": [],
  "edges": []
}
```

规则：

- 修改已有工作流时，先保存 `workflow get` 的完整响应，再只改目标字段。
- `save` 是完整画布保存，不是节点增量接口。
- 不要把历史执行 ID 当作保存版本自行改写。`get --version` 只用于读取指定历史画布。
- 顶层可能还有状态、创建者、更新时间等只读字段。保留它们没有问题，但不得猜测或伪造。

## 节点 Node

普通业务节点使用以下结构：

```json
{
  "id": "node-unique-id",
  "type": "default",
  "position": { "x": 120, "y": 160 },
  "data": {
    "type": "default",
    "customType": "text",
    "customeData": {
      "index": 0,
      "name": "文本",
      "params": {},
      "result": {
        "status": 0,
        "message": "",
        "runTime": 0
      }
    },
    "handles": []
  },
  "handles": [],
  "lock": false,
  "selected": false
}
```

字段规则：

| 字段 | 规则 |
|---|---|
| `id` | 画布内唯一。新 ID 推荐 `node-<时间戳>-<序号>-<随机串>`。引用它的边必须同步。 |
| `type` | 普通业务节点为 `default`；分组节点为 `group`；便签可能为 `sticky_note`。不要使用旧示例里的 `custom`。 |
| `position` | 非分组节点为画布绝对坐标；有 `parentId` 的组内节点为相对父组坐标。 |
| `data.customType` | 节点业务类型。必须是节点目录中的有效值。 |
| `data.customeData` | 节点参数、结果、名称和索引。历史拼写固定为 `customeData`。 |
| `handles` | 新结构的句柄列表。兼容数据还会在 `data.handles` 存一份。修改句柄时保持两处一致。 |
| `lock` | 锁定后不可拖动；新节点通常为 `false`。 |
| `selected` | 编辑器临时状态。保存时可保留，但不要依赖它表达业务逻辑。 |
| `parentId` | 仅组内子节点使用，必须指向现存 `type: "group"` 节点。 |
| `style` | 分组节点使用 `width`、`height`；不要丢失其它未知样式字段。 |

`connectionPlaceholder: true` 是拖线落在空白画布时产生的临时节点标记。它及其临时边不应出现在保存文件中。

## 句柄 Handle

```json
{
  "id": "handle-unique-id",
  "type": "target",
  "position": "left",
  "connectable": true,
  "dataType": "text"
}
```

| 字段 | 说明 |
|---|---|
| `id` | 节点内唯一，并被 `edge.sourceHandle` 或 `edge.targetHandle` 引用。 |
| `type` | `source` 为输出；`target` 为输入。 |
| `position` | 当前输出通常为 `right`，输入通常为 `left`。 |
| `dataType` | 数据类型；决定连接是否合法。多输入类型节点的主输入通常为 `any`。 |
| `connectable` | 是否允许连接，通常为 `true`。 |
| `deletable` | 动态追加的输入句柄可能为 `true`。 |
| `label`、`color`、`className` | 可选展示数据；读取到时按原样保留。 |

创建普通节点时：

1. 无输入能力的节点不创建 `target`。
2. 仅接受一种输入类型的节点创建一个该类型 `target`。
3. 接受多种输入类型的节点创建一个 `dataType: "any"` 的 `target`。
4. 有输出能力的节点创建一个配置输出类型的 `source`。
5. 将完全相同的句柄数组同时写入节点顶层 `handles` 与 `data.handles`。

详细类型兼容规则见 [connections-and-groups.md](connections-and-groups.md)。

## 节点业务数据 customeData

多数节点包含：

```json
{
  "index": 0,
  "name": "节点名称",
  "params": {},
  "result": {
    "texts": [],
    "items": [],
    "files": [],
    "maskFiles": [],
    "status": 0,
    "message": "",
    "runTime": 0
  }
}
```

- `index`：节点创建顺序。新增节点应使用当前最大值加一。
- `name`：用户自定义名称；空字符串表示使用节点类型默认名称。
- `params`：节点配置。不同 `customType` 的稳定字段见 [node-catalog.md](node-catalog.md)。
- `result`：最近一次结果或初始状态。修改参数时不要无故删除已有结果。
- `files[].url`：持久化资源地址或存储 key。不要把短期签名预览地址覆盖到持久化字段。
- 未认识的 `params`、`result` 或同级字段必须原样保留。

## 边 Edge

```json
{
  "id": "edge-unique-id",
  "source": "node-source",
  "target": "node-target",
  "sourceHandle": "handle-source-output",
  "targetHandle": "handle-target-input",
  "type": "default"
}
```

- `source`、`target` 必须引用存在的节点。
- `sourceHandle` 必须引用源节点中 `type: "source"` 的句柄。
- `targetHandle` 必须引用目标节点中 `type: "target"` 的句柄。
- 不要仅凭节点 ID 重建边；句柄 ID 决定端口关系。
- `data` 可能包含未来或业务扩展字段，读取到时原样保留。
- 某些节点依赖 `edges` 数组顺序，例如视频拼接的输入顺序。不要随意排序。

## 结果状态

`customeData.result.status`：

| 值 | 含义 |
|---:|---|
| `0` | 未执行或初始状态 |
| `1` | 等待 |
| `2` | 运行中 |
| `3` | 成功 |
| `4` | 失败 |

常用结果字段：

- 文本：`texts: string[]`
- 文本数组：`items: string[]`
- 图片或视频：`files: { url, width?, height?, cover_image?, size? }[]`
- 遮罩：`maskFiles`
- 状态信息：`message`、`runTime`

不要手工把状态改为成功。只有真实运行响应或 `workflow get` 返回结果可以证明执行成功。

## 保存与版本

推荐流程：

```bash
58pic workflow get <workflow-id> --format json > workflow-response.json
node <skill-dir>/scripts/extract_canvas.mjs workflow-response.json workflow.json
# 对 workflow.json 做最小字段修改
node <skill-dir>/scripts/validate_canvas.mjs workflow.json
58pic workflow save <workflow-id> --canvas-file workflow.json --format json
58pic workflow get <workflow-id> --format json > saved-response.json
node <skill-dir>/scripts/extract_canvas.mjs saved-response.json saved-workflow.json
node <skill-dir>/scripts/validate_canvas.mjs saved-workflow.json
```

保存后再次读取并验证：

- 节点和边数量符合预期。
- 新增 ID 唯一，所有边引用均能解析。
- `customType` 与节点参数匹配。
- 分组子节点仍在组内且相对位置正确。
- 未修改节点的未知字段没有丢失。

## 编辑检查清单

- [ ] 使用 `customeData`，没有改成 `customData`。
- [ ] 普通节点 `type` 为 `default`。
- [ ] `nodes` 和 `edges` 是完整画布，不是增量片段。
- [ ] 顶层 `handles` 与 `data.handles` 一致。
- [ ] 每条边的四个节点/句柄引用都存在且方向正确。
- [ ] 没有保存 `connectionPlaceholder` 临时节点。
- [ ] 组内坐标没有与绝对坐标混用。
- [ ] 未删除未知字段和已有结果。
- [ ] 保存后已重新 `get` 校验。
