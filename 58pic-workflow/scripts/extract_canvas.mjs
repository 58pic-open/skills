#!/usr/bin/env node

import { readFile, writeFile } from 'node:fs/promises';
import process from 'node:process';

const [inputPath, outputPath] = process.argv.slice(2);

if (!inputPath || !outputPath) {
  console.error('用法: node extract_canvas.mjs <workflow-get.json> <canvas.json>');
  process.exit(2);
}

let raw;
try {
  raw = JSON.parse(await readFile(inputPath, 'utf8'));
} catch (error) {
  console.error(`无法读取 JSON: ${error instanceof Error ? error.message : String(error)}`);
  process.exit(1);
}

const apiBody = raw?.body && typeof raw.body === 'object' ? raw.body : raw;
if (typeof apiBody?.code === 'number' && apiBody.code !== 200) {
  console.error(`工作流读取失败: code=${apiBody.code} message=${apiBody.message ?? apiBody.msg ?? ''}`);
  process.exit(1);
}

const canvas = apiBody?.data && typeof apiBody.data === 'object' ? apiBody.data : apiBody;
if (!canvas || typeof canvas !== 'object' || !Array.isArray(canvas.nodes)) {
  console.error('没有找到工作流画布；期望 body.data.nodes 或 data.nodes 为数组');
  process.exit(1);
}

await writeFile(outputPath, `${JSON.stringify(canvas, null, 2)}\n`, 'utf8');
console.log(`已提取画布: ${outputPath} (${canvas.nodes.length} nodes, ${Array.isArray(canvas.edges) ? canvas.edges.length : 0} edges)`);
