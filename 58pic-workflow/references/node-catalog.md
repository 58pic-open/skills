# 节点目录与业务数据

本文列出当前可持久化的工作流节点类型、输入输出和稳定参数。编辑已有节点时，应保留 `workflow get` 返回的全部字段；本文只列出允许识别和修改的稳定字段，不代表可以删除其它字段。

## 目录

- [通用规则](#通用规则)
- [文本节点](#文本节点)
- [图片节点](#图片节点)
- [视频节点](#视频节点)
- [输入输出与编排节点](#输入输出与编排节点)
- [生成类共享参数](#生成类共享参数)
- [节点选择建议](#节点选择建议)

## 通用规则

- 普通业务节点：`type: "default"`，业务类型放在 `data.customType`。
- 便签：`type: "sticky_note"`，`data.customType: "sticky_note"`。
- 分组不是业务节点：`type: "group"`，不设置 `customType`。
- `loop` 已禁用，不要新建；读取旧画布时原样保留。
- 输入列中的多个类型表示该节点接受多类输入，新节点使用一个 `dataType: "any"` 的主输入句柄。
- `最大连接` 按目标句柄计算；`∞` 表示 `maxConnect: -1`。
- 面板未展示的已有节点仍应原样保留；新建节点优先使用当前可用节点类型。

## 文本节点

| `customType` | 名称 | 接受输入 | 输出 | 最大连接 | 关键 `params` 与逻辑 |
|---|---|---|---|---:|---|
| `user_input` | 用户提示词 | — | `prompt` | ∞ | `prompt`；历史输入节点，已有画布继续保留。 |
| `text` | 文本 | — | `text` | ∞ | `prompt`；保存静态文本。 |
| `system_input` | 提示词 | `prompt` | `prompt` | ∞ | `prompt`；接收上游文本或使用本地文本。 |
| `ai_rewrite` | 生成文本 | `prompt`、`system_prompt`、`image`、`file` | `prompt` | ∞ | `prompt`、模型配置、参考图配置；结果在 `result.texts`。 |
| `material_extractor` | 物料提取器 | `prompt`、`system_prompt` | `text_array` | ∞ | `prompt` 与模型配置；结果为结构化文本数组。 |
| `text_connector` | 文本拼接 | `text` | `text` | ∞ | `connector?`；按输入顺序连接多个文本。 |
| `text_cross` | 文本组合 | `text_array`、`text` | `text_array` | ∞ | `intersectionType: "cross" | "sequential"`。 |
| `text_array` | 文本拆分 | `text` | `text_array` | `1` | `splitBy`、`items`；按分隔符拆分文本。默认分隔符为逗号。 |
| `text_list` | 文本选择 | `text_array` | `text` | `1` | `selectedIndex`、可选 `items`；从数组中选择一项。 |

### 文本处理语义

- `text_array` 产生数组，不能直接连接 `output`；先经过 `text_list`、`text_cross` 等节点转换。
- `text_cross.intersectionType = "cross"` 表示笛卡尔组合；`sequential` 表示按索引对应组合。
- `text_connector` 的输入顺序依赖画布连线顺序；不要无故重排相关边。
- `text_list.params.items` 只用于无上游连线时的自定义数据源；有上游时以实际输入为准。

## 图片节点

| `customType` | 名称 | 接受输入 | 输出 | 最大连接 | 关键 `params` 与逻辑 |
|---|---|---|---|---:|---|
| `user_upload_image` | 图片 | — | `image` | ∞ | `files[]`；保存用户上传图片。通常由“上传”节点识别图片后转换而来。 |
| `system_default_image` | 图片 | — | `image` | ∞ | `files[]`；已有画布兼容节点。 |
| `ai_reference_image` | 素材搜索 | `prompt`、`image`、`system_image` | `image` | ∞ | 与图片生成共享模型参数；面板隐藏，已有节点保留。 |
| `image_model` | 图片生成 | `prompt`、`image`、`system_image` | `image` | ∞ | `prompt`、`model`、`version`、`reference_image_urls`、`Aspect`、`create_number` 等。 |
| `painter` | 涂抹 | `image` | `image` | `1` | `color`、`size`、`canvasWidth`、`canvasHeight`、`lockAspectRatio`、`backgroundColor`、`drawingData?`。 |
| `image_composite` | 图片合成 | `image` | `image` | ∞ | `canvas_id`；旧图片合成节点，已有画布保留。 |
| `canvas` | 画布编辑 | `image` | `image` | ∞ | `doc_json`；保存可编辑画布文档，结果图位于 `result.files`。 |
| `ai_matting` | AI 抠图 | `image` | `image` | `1` | `image`；通常由上游输入解析，不要用临时预览地址覆盖。 |
| `super_resolution` | 画质超清 | `image` | `image` | `1` | `image`。 |
| `extend_image` | 扩图 | `image` | `image` | `1` | `image`、`mask_image`、`extend_width`、`extend_height`、`ratio`、`x`、`y`。 |
| `crop` | 裁剪 | `image` | `image` | `1` | `x?`、`y?`、`width?`、`height?`、`lockAspectRatio?`、`aspectRatio?`。 |
| `image_list` | 图片列表 | `image` | `image` | ∞ | `selectedIndex`；从多条图片输入中选择一项。 |

### 图片字段说明

`FileItem`：

```json
{
  "url": "持久化资源地址",
  "width": "可选宽度",
  "height": "可选高度",
  "size": 0
}
```

- `crop` 不持久化原图尺寸和原图地址，它们来自上游；只保存裁剪框参数。
- `canvas.params.doc_json` 是可编辑画布文档，不是导出图片 URL；不要把它替换成截图。
- `painter.params.drawingData` 用于恢复绘制状态，未知格式时原样保留。
- 图片处理节点的 `params.image` 常由运行时根据上游解析；编辑已有节点时不要随意清空。

## 视频节点

| `customType` | 名称 | 接受输入 | 输出 | 最大连接 | 关键 `params` 与逻辑 |
|---|---|---|---|---:|---|
| `video_model` | 视频生成 | `prompt`、`image`、`system_image` | `video` | ∞ | 图片生成共享参数，加 `ref_mode`、`frame_prompts`、`ref_image_indexes`。 |
| `video_cover` | 视频截帧 | `video` | `media` | `1` | `cover_offset[]`、`cover_image_index`、`files[]`；输出可同时包含视频和截帧图。 |
| `video_concat` | 视频拼接 | `video` | `video` | ∞ | `params` 为空；拼接顺序以指向该节点的 `edges` 数组顺序为准。 |
| `video_trim` | 视频修剪 | `video` | `video` | `1` | `trim_start`、`trim_end`，且结束时间必须大于开始时间。 |
| `video_reverse` | 视频倒放 | `video` | `video` | `1` | `params` 为空。 |

### 视频参考图模式

`video_model.params.ref_mode` 可见值：

| 值 | 含义 | 相关字段 |
|---|---|---|
| `omni` | 多参考图模式 | `ref_image_indexes` |
| `fl` | 首尾帧模式 | 保留实际返回的参考图字段 |
| `imf` | 智能多帧模式 | `frame_prompts[]` |
| `subject` | 主体参考模式 | `ref_image_indexes` |

`frame_prompts[]` 结构：

```json
{
  "url": "运行时解析的图片地址",
  "prompt": "该帧描述",
  "duration": "时长"
}
```

帧与上游图片按数组位置对应。不要在不了解模型要求时重新排序或删除 `frame_prompts`、`ref_image_indexes`。

## 输入输出与编排节点

| `customType` | 名称 | 接受输入 | 输出 | 最大连接 | 关键 `params` 与逻辑 |
|---|---|---|---|---:|---|
| `upload_attachment` | 上传 | — | `file` | ∞ | `params` 本身是附件数组，不是对象；当前通常最多一项。 |
| `link_workflow` | 关联工作流 | `image`、`prompt` | `image` | ∞ | `workflow_id`、可选 `workflow_name`；引用另一工作流。 |
| `output` | 结果与下载 | 任意（目标类型 `output`） | — | ∞ | `files[]`、`texts[]` 仅表示该节点自有数据；上游结果运行时动态汇总。 |
| `sticky_note` | 便签 | — | — | `0` | `content`、`bg_color`；不参与运行。 |

附件项：

```json
{
  "url": "workflow/.../file.pdf",
  "name": "file.pdf",
  "size": 12345,
  "ext": "pdf"
}
```

`previewUrl` 是可选短期预览地址，不要用它覆盖持久化 `url`。

## 生成类共享参数

`ai_rewrite`、`material_extractor`、`image_model`、`ai_reference_image`、`video_model` 可能包含一组共享模型字段。常用稳定字段如下：

| 字段 | 说明 |
|---|---|
| `prompt` | 本地提示词；还可能与上游文本合并。 |
| `model`、`version` | 模型与版本标识。不要凭文档硬编码，优先保留真实节点返回值。 |
| `template_id` | 模板标识。 |
| `reference_image_url` | 单参考图兼容字段。 |
| `reference_image_urls` | 多参考图数组。 |
| `reference_similarity` | 参考相似度。 |
| `negative_prompt` | 负向提示词。 |
| `create_number` | 生成数量。 |
| `Aspect` | 比例或比例选项标识。 |
| `video_duration`、`video_resolution` | 视频模型选项。 |
| `style_image_url`、`audio_url` | 可选风格图与音频。 |

节点还可能包含模型表单扩展字段。修改提示词时只改 `prompt`；修改模型时以实时模型能力或真实节点数据为依据。不要清理看似为空或暂时不认识的模型字段。

## 节点选择建议

- 静态文字：`text`。
- 可接上游文本并继续输出提示词：`system_input`。
- 生成文案：`ai_rewrite`。
- 分割、组合、选择文本：`text_array` → `text_cross` / `text_list`。
- 上传图片：优先使用上传流程产生的 `user_upload_image`，不要伪造资源 URL。
- 生成图片或视频：从真实同类节点复制参数骨架，再替换明确字段。
- 多图可编辑合成：`canvas`。
- 最终交付：连接到 `output`。
- 复杂节点未知参数：先找一个真实同类型节点 `get`，复制完整节点后最小修改。
