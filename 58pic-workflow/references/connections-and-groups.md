# 连线、句柄与分组规则

本文用于新增或调整句柄、边和分组。已有画布中的未知句柄与边字段应原样保留。

## 目录

- [统一输入句柄](#统一输入句柄)
- [数据类型兼容](#数据类型兼容)
- [特殊连接规则](#特殊连接规则)
- [连接验证顺序](#连接验证顺序)
- [多输入与边顺序](#多输入与边顺序)
- [分组坐标](#分组坐标)
- [分组示例](#分组示例)
- [图完整性校验](#图完整性校验)

## 统一输入句柄

新节点不会再为每一种可接受数据都创建一个输入句柄。主输入句柄按节点接受的类型数确定：

- 只接受一种类型：保留该具体类型，例如 `crop` 使用 `image`。
- 接受两种及以上类型：使用一个 `dataType: "any"` 的输入句柄，例如 `image_model`。
- 没有输入能力：不创建 `target` 句柄。

`any` 不表示任何连接都合法。校验时会读取目标节点 `customType` 对应的可接受类型，再逐项匹配。

示例：图片生成节点接受 `prompt`、`image`、`system_image`，新建时使用：

```json
{
  "id": "handle-image-model-input",
  "type": "target",
  "position": "left",
  "connectable": true,
  "dataType": "any"
}
```

旧画布可能保留多个具体类型输入句柄。它们仍可工作，不要为了“升级”而批量重建 ID，否则已有边会断开。

## 数据类型兼容

| 源类型 | 可连接目标类型 |
|---|---|
| `prompt` | `prompt`、`system_prompt`、`text`、`output` |
| `system_prompt` | `prompt`、`system_prompt`、`text`、`output` |
| `text` | `prompt`、`system_prompt`、`text`、`output` |
| `text_array` | `text_array`；以及白名单节点的文本输入；不能直接到 `output` |
| `array` | `array`、`output` |
| `image` | `image`、`system_image`、`output` |
| `system_image` | `image`、`system_image`、`output` |
| `video` | `video`、`output` |
| `media` | `image`、`system_image`、`video`、`output` |
| `file` | `file`、`output`；符合条件的 MP4 可到视频处理节点 |
| `loop` | `loop`、`prompt`、`system_prompt`、`output` |
| `mask` | `mask`、`output` |
| `image_list` | `image_list`、`output` |
| 任意有效类型 | `output` |

同类型默认可以连接，文本三类和图片两类支持互通。

## 特殊连接规则

### text_array 白名单

`text_array` 输出允许连接到以下节点的 `prompt` 或统一输入：

- `system_input`
- `ai_rewrite`
- `text_connector`
- `image_model`
- `video_model`

但 `text_array` 不能直接连接 `output`。如果需要输出数组中的内容，先经过 `text_list` 或其它文本转换节点。

### 附件视频

`file → video` 只有同时满足以下条件才合法：

1. 源节点是 `upload_attachment`。
2. 附件是 MP4 或可识别的视频文件。
3. 目标节点是 `video_trim`、`video_concat`、`video_reverse` 或 `video_cover`。

不要仅把句柄类型改成 `video` 来绕过资源检查。

### media 输出

`video_cover` 输出 `media`，其中可能同时有视频和截帧图片。下游节点按自身输入类型选择文件，因此可以连接图片、系统图片或视频节点。

### 旧数据兼容

旧句柄可能没有 `dataType`。读取已有画布时保留它们；不要因为校验层会兼容放行，就在新节点中省略 `dataType`。

## 连接验证顺序

新增边前依次检查：

1. `source`、`target`、`sourceHandle`、`targetHandle` 都能解析。
2. 禁止节点连接自身。
3. 禁止 `text_array → output`。
4. 源数据类型满足目标句柄或目标节点接受类型。
5. 特殊规则通过，例如附件视频和 `text_array` 白名单。
6. 目标句柄尚未达到 `maxConnect`。

`maxConnect` 按同一个 `targetHandle` 的现有入边数计算。不要把它误解为整个节点所有输入句柄的总数。

## 多输入与边顺序

- `maxConnect: -1`：同一目标句柄允许多条入边。
- 正整数 `maxConnect`：目标句柄达到上限后拒绝连接。
- 可动态追加输入的节点可能拥有多个 `target` 句柄；新增句柄必须同步更新顶层 `handles` 与 `data.handles`。
- `video_concat` 使用指向该节点的 `edges` 数组顺序决定视频拼接顺序。
- 文本拼接、图片列表等多输入节点也应保留有意义的连线顺序。

新增边使用 `type: "default"`。推荐 ID：

```text
edge-<毫秒时间戳>-<序号>-<随机串>
```

## 分组坐标

分组使用 xyflow 父子结构：

```json
{
  "id": "group-1",
  "type": "group",
  "position": { "x": 100, "y": 80 },
  "data": {
    "groupOrdinal": 1,
    "customeData": { "name": "内容生成" }
  },
  "style": { "width": 720, "height": 420 },
  "zIndex": 0,
  "lock": false
}
```

组节点的 `position` 是画布绝对坐标。子节点设置 `parentId` 后，`position` 必须改成相对父组坐标：

```text
childRelative.x = childAbsolute.x - group.position.x
childRelative.y = childAbsolute.y - group.position.y
```

解组或移出分组时恢复绝对坐标：

```text
childAbsolute.x = childRelative.x + group.position.x
childAbsolute.y = childRelative.y + group.position.y
```

组尺寸必须覆盖全部子节点并留出边距。不要只写 `parentId` 而保留子节点原绝对坐标，否则节点会在编辑器中产生大幅偏移。

## 分组示例

父组位于 `(100, 80)`，原节点绝对坐标为 `(180, 160)`，则保存后的子节点位置为 `(80, 80)`：

```json
[
  {
    "id": "group-1",
    "type": "group",
    "position": { "x": 100, "y": 80 },
    "data": {
      "groupOrdinal": 1,
      "customeData": { "name": "内容生成" }
    },
    "style": { "width": 720, "height": 420 },
    "zIndex": 0,
    "lock": false,
    "selected": false
  },
  {
    "id": "node-text",
    "type": "default",
    "parentId": "group-1",
    "position": { "x": 80, "y": 80 },
    "data": {
      "type": "default",
      "customType": "text",
      "customeData": {
        "index": 0,
        "name": "",
        "params": { "prompt": "春日海报" },
        "result": { "texts": [], "status": 0, "message": "", "runTime": 0 }
      }
    },
    "lock": false,
    "selected": false
  }
]
```

规则：

- `parentId` 必须指向 `type: "group"`。
- 至少两个可分组叶子节点才适合新建组。
- 便签可以放入组，但不参与组运行。
- 分组运行只处理有 `customType`、非临时占位、非便签的子节点。
- 删除或解组时先恢复子节点绝对坐标，再移除 `parentId` 和组节点。

## 图完整性校验

保存前检查：

```text
nodeIds = 所有 node.id
handleIds[nodeId] = 该节点所有 handles[].id

对每条 edge：
  edge.source ∈ nodeIds
  edge.target ∈ nodeIds
  edge.sourceHandle ∈ handleIds[edge.source]
  edge.targetHandle ∈ handleIds[edge.target]
  sourceHandle.type == source
  targetHandle.type == target

对每个有 parentId 的 node：
  parentId ∈ nodeIds
  parent.type == group
```

另外确认：

- 节点、句柄、边 ID 均唯一。
- 没有 `connectionPlaceholder: true` 节点及其边。
- 没有引用已删除句柄的孤立边。
- 顶层 `handles` 与 `data.handles` 内容一致。
- `video_concat` 等顺序敏感节点的入边顺序未改变。
