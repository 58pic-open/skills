#!/usr/bin/env node

import { readFile } from 'node:fs/promises';
import process from 'node:process';

const [inputPath] = process.argv.slice(2);

if (!inputPath) {
  console.error('用法: node validate_canvas.mjs <canvas.json>');
  process.exit(2);
}

const ACTIVE_NODE_TYPES = new Set([
  'user_input',
  'text',
  'system_input',
  'user_upload_image',
  'system_default_image',
  'upload_attachment',
  'ai_reference_image',
  'link_workflow',
  'painter',
  'image_composite',
  'canvas',
  'ai_matting',
  'super_resolution',
  'extend_image',
  'crop',
  'ai_rewrite',
  'material_extractor',
  'image_model',
  'video_model',
  'text_connector',
  'text_cross',
  'text_array',
  'text_list',
  'image_list',
  'output',
  'video_cover',
  'video_concat',
  'video_trim',
  'sticky_note',
  'video_reverse',
]);

const errors = [];
const warnings = [];

function error(message) {
  errors.push(message);
}

function warn(message) {
  warnings.push(message);
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function duplicateValues(values) {
  const seen = new Set();
  const duplicates = new Set();
  for (const value of values) {
    if (seen.has(value)) duplicates.add(value);
    seen.add(value);
  }
  return [...duplicates];
}

let raw;
try {
  raw = JSON.parse(await readFile(inputPath, 'utf8'));
} catch (readError) {
  console.error(`无法读取 JSON: ${readError instanceof Error ? readError.message : String(readError)}`);
  process.exit(1);
}

const apiBody = isObject(raw?.body) ? raw.body : raw;
const canvas = isObject(apiBody?.data) ? apiBody.data : apiBody;
if (canvas !== raw) {
  warn('输入是 CLI/API 响应封装；校验的是其中画布。保存前请先用 extract_canvas.mjs 提取 data');
}

if (!isObject(canvas)) {
  console.error('画布顶层必须是 JSON 对象');
  process.exit(1);
}

if (!Array.isArray(canvas.nodes)) error('顶层 nodes 必须是数组');
if (!Array.isArray(canvas.edges)) warn('顶层 edges 缺失；完整保存建议显式提供 edges 数组');

const nodes = Array.isArray(canvas.nodes) ? canvas.nodes : [];
const edges = Array.isArray(canvas.edges) ? canvas.edges : [];
const nodeIds = nodes.map((node) => node?.id).filter((id) => typeof id === 'string');

for (const id of duplicateValues(nodeIds)) error(`重复 node.id: ${id}`);

const nodeById = new Map();
const handlesByNode = new Map();

for (const [index, node] of nodes.entries()) {
  const path = `nodes[${index}]`;
  if (!isObject(node)) {
    error(`${path} 必须是对象`);
    continue;
  }
  if (typeof node.id !== 'string' || node.id.length === 0) {
    error(`${path}.id 必须是非空字符串`);
    continue;
  }
  nodeById.set(node.id, node);

  if (!isObject(node.position) || !Number.isFinite(node.position.x) || !Number.isFinite(node.position.y)) {
    error(`${path}.position 必须包含有限数字 x/y`);
  }

  if (!isObject(node.data)) error(`${path}.data 必须是对象`);
  if (isObject(node.data) && Object.hasOwn(node.data, 'customData')) {
    error(`${path}.data.customData 拼写错误，应使用 customeData`);
  }
  if (node.data?.connectionPlaceholder === true) {
    error(`${path} 是 connectionPlaceholder 临时节点，保存前必须删除`);
  }

  const customType = node.data?.customType;
  if (typeof customType === 'string') {
    if (!ACTIVE_NODE_TYPES.has(customType)) warn(`${path} 使用未知 customType=${customType}；已有节点应保留，新建前确认实时协议`);
    if (!isObject(node.data?.customeData)) error(`${path}.data.customeData 必须是对象`);
    if (customType !== 'sticky_note' && node.type !== 'default') {
      warn(`${path} 普通业务节点通常使用 type=default，当前为 ${String(node.type)}`);
    }
    if (customType === 'sticky_note' && node.type !== 'sticky_note') {
      warn(`${path} 便签节点通常使用 type=sticky_note`);
    }
    const status = node.data?.customeData?.result?.status;
    if (status !== undefined && ![0, 1, 2, 3, 4].includes(status)) {
      error(`${path}.data.customeData.result.status 必须为 0..4`);
    }
  } else if (node.type === 'default') {
    error(`${path} 是没有 data.customType 的临时节点，保存前必须删除或选择具体节点类型`);
  } else if (node.type !== 'group') {
    warn(`${path} 没有 data.customType`);
  }

  if (node.type === 'group') {
    if (node.parentId) warn(`${path} 是 group 且仍有 parentId；当前分组通常不嵌套`);
    if (!isObject(node.style) || !Number.isFinite(node.style.width) || !Number.isFinite(node.style.height)) {
      error(`${path} 分组节点必须有有限数字 style.width/height`);
    }
  }

  const topHandles = Array.isArray(node.handles) ? node.handles : [];
  const dataHandles = Array.isArray(node.data?.handles) ? node.data.handles : [];
  const handles = topHandles.length > 0 ? topHandles : dataHandles;
  const handlesForNode = new Map();
  if (topHandles.length > 0 && dataHandles.length > 0) {
    const topSignature = topHandles.map((handle) => `${handle?.id}:${handle?.type}:${handle?.dataType}`).join('|');
    const dataSignature = dataHandles.map((handle) => `${handle?.id}:${handle?.type}:${handle?.dataType}`).join('|');
    if (topSignature !== dataSignature) warn(`${path} 顶层 handles 与 data.handles 不一致`);
  }

  for (const [handleIndex, handle] of handles.entries()) {
    const handlePath = `${path}.handles[${handleIndex}]`;
    if (!isObject(handle) || typeof handle.id !== 'string' || handle.id.length === 0) {
      error(`${handlePath}.id 必须是非空字符串`);
      continue;
    }
    if (handlesForNode.has(handle.id)) error(`${path} 内重复 handle.id: ${handle.id}`);
    handlesForNode.set(handle.id, handle);
    if (handle.type !== 'source' && handle.type !== 'target') error(`${handlePath}.type 必须是 source 或 target`);
    if (typeof handle.dataType !== 'string') warn(`${handlePath}.dataType 缺失；新句柄必须显式声明`);
  }
  handlesByNode.set(node.id, handlesForNode);
}

for (const [index, node] of nodes.entries()) {
  if (!isObject(node) || typeof node.parentId !== 'string') continue;
  const parent = nodeById.get(node.parentId);
  if (!parent) error(`nodes[${index}].parentId 引用不存在的节点: ${node.parentId}`);
  else if (parent.type !== 'group') error(`nodes[${index}].parentId 必须引用 type=group 节点: ${node.parentId}`);
}

const edgeIds = edges.map((edge) => edge?.id).filter((id) => typeof id === 'string');
for (const id of duplicateValues(edgeIds)) error(`重复 edge.id: ${id}`);

for (const [index, edge] of edges.entries()) {
  const path = `edges[${index}]`;
  if (!isObject(edge)) {
    error(`${path} 必须是对象`);
    continue;
  }
  if (typeof edge.id !== 'string' || edge.id.length === 0) error(`${path}.id 必须是非空字符串`);
  if (!nodeById.has(edge.source)) error(`${path}.source 引用不存在的节点: ${String(edge.source)}`);
  if (!nodeById.has(edge.target)) error(`${path}.target 引用不存在的节点: ${String(edge.target)}`);
  if (edge.source === edge.target) error(`${path} 不允许节点连接自身`);

  const sourceHandle = handlesByNode.get(edge.source)?.get(edge.sourceHandle);
  const targetHandle = handlesByNode.get(edge.target)?.get(edge.targetHandle);
  if (!sourceHandle) error(`${path}.sourceHandle 引用不存在的句柄: ${String(edge.sourceHandle)}`);
  else {
    if (sourceHandle.type !== 'source') error(`${path}.sourceHandle 必须是 source 句柄`);
  }
  if (!targetHandle) error(`${path}.targetHandle 引用不存在的句柄: ${String(edge.targetHandle)}`);
  else {
    if (targetHandle.type !== 'target') error(`${path}.targetHandle 必须是 target 句柄`);
  }

  const sourceType = nodeById.get(edge.source)?.data?.customType;
  const targetType = nodeById.get(edge.target)?.data?.customType;
  if (sourceType === 'text_array' && targetType === 'output') {
    error(`${path} 不允许 text_array 直接连接 output`);
  }
}

for (const message of warnings) console.warn(`WARN  ${message}`);
for (const message of errors) console.error(`ERROR ${message}`);

if (errors.length > 0) {
  console.error(`校验失败: ${errors.length} error(s), ${warnings.length} warning(s)`);
  process.exit(1);
}

console.log(`校验通过: ${nodes.length} nodes, ${edges.length} edges, ${warnings.length} warning(s)`);
