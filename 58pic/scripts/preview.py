#!/usr/bin/env python3
"""
千图网统一预览管理页面 v4
架构：Python 组装 JSON 数据 → 内嵌到 HTML → JS 动态渲染三个 Tab

数据结构 (window.PIC58_DATA)：
{
  "version": 2,
  "generated_at": "...",
  "search": {
    "keyword": "", "page": 1, "total_page": 1,
    "kid_name": "", "ai_search": false, "search_time": "",
    "items": [
      { "pid": "", "title": "", "preview_url": "", "type": "", "width": "", "height": "" }
    ]
  },
  "downloads": [
    { "pid": "", "filename": "", "file_url": "file:///abs/path/...", "size": "", "timestamp": "" }
  ],
  "ai_results": [
    {
      "ai_id": "", "model": "", "prompt": "", "timestamp": "",
      "images": [ { "filename": "", "file_url": "file:///abs/path/...", "size": "" } ]
    }
  ]
}
"""

import argparse
import json
import os
import time

CONFIG_FILE = os.path.expanduser("~/.58pic_config.json")
SESSION_FILENAME = "session.json"


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_config_output_dir():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("output_dir", "")
        except Exception:
            pass
    return ""


def load_session_file(session_file):
    if session_file and os.path.exists(session_file):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"searches": [], "downloads": [], "ai_results": []}


def file_url(path):
    """将本地文件绝对路径转为 file:// URI（供 <img src> 直接加载）"""
    return "file://" + os.path.abspath(path).replace("\\", "/")


def fmt_size(path):
    try:
        b = os.path.getsize(path)
        if b < 1024:        return f"{b} B"
        if b < 1024*1024:   return f"{b//1024} KB"
        return f"{b/1024/1024:.1f} MB"
    except Exception:
        return ""


# ── Data assembler ────────────────────────────────────────────────────────────

def build_data(session, results_file=None, cur_image_files=None,
               cur_prompt="", cur_model="", extra_download_files=None):
    """
    组装 window.PIC58_DATA JSON 对象。
    - search.items 保留原始 preview_url，浏览器直接加载
    - downloads / ai_results 的图片编为 base64（本地文件）
    """

    # ── 搜索数据（全部历史，最新在前） ──
    def _load_search_result(rf):
        try:
            with open(rf, "r", encoding="utf-8") as f:
                raw = json.load(f)
            items = [
                {
                    "pid":         str(it.get("pid", "")),
                    "title":       it.get("title", "") or it.get("keyword", "") or "无标题",
                    "preview_url": it.get("preview_url", "") or it.get("thumbnail", ""),
                    "type":        it.get("type", "image"),
                    "width":       str(it.get("width", "")),
                    "height":      str(it.get("height", "")),
                }
                for it in raw.get("items", [])
            ]
            return {
                "keyword":    raw.get("keyword", ""),
                "page":       raw.get("page", 1),
                "total_page": raw.get("total_page", 1),
                "did_name":   raw.get("did_name", "") or raw.get("kid_name", ""),
                "ai_search":  raw.get("ai_search", False),
                "search_time": raw.get("search_time", ""),
                "items":      items,
            }
        except Exception:
            return None

    search_history = []

    # 如果显式传入了 results_file，放在最前面
    if results_file and os.path.exists(results_file):
        entry = _load_search_result(results_file)
        if entry:
            search_history.append(entry)

    # 从 session 中加载其余历史（去重）
    loaded_files = {results_file} if results_file else set()
    for rec in session.get("searches", []):
        rf = rec.get("results_file", "")
        if rf and rf not in loaded_files and os.path.exists(rf):
            loaded_files.add(rf)
            entry = _load_search_result(rf)
            if entry:
                search_history.append(entry)

    # 兜底空状态
    if not search_history:
        search_history.append({"keyword": "", "page": 1, "total_page": 1,
                                "kid_name": "", "ai_search": False,
                                "search_time": "", "items": []})

    search_data = {"history": search_history}

    # ── 下载数据（session + extra） ──
    dl_list = []
    seen_paths = set()

    for entry in session.get("downloads", []):
        path = entry.get("path", "")
        if not path or path in seen_paths:
            continue
        seen_paths.add(path)
        dl_list.append({
            "pid":         entry.get("pid", ""),
            "filename":    entry.get("filename", os.path.basename(path)),
            "file_url":    file_url(path) if os.path.exists(path) else "",
            "size":        fmt_size(path),
            "preview_url": entry.get("preview_url", ""),
            "timestamp":   entry.get("timestamp", ""),
        })

    for path in (extra_download_files or []):
        if path and path not in seen_paths and os.path.exists(path):
            seen_paths.add(path)
            dl_list.append({
                "pid":       "",
                "filename":  os.path.basename(path),
                "file_url":  file_url(path),
                "size":      fmt_size(path),
                "timestamp": "",
            })

    # 最新的排在前面
    dl_list.reverse()

    # ── AI 生成数据（session + cur_image_files） ──
    ai_list = []
    all_ai_entries = list(reversed(session.get("ai_results", [])))  # 最新在前

    # 把当前新增文件临时加入头部（如果不在 session 中）
    session_paths = {p for r in all_ai_entries for p in r.get("files", [])}
    new_files = [f for f in (cur_image_files or []) if f not in session_paths and os.path.exists(f)]
    if new_files:
        all_ai_entries.insert(0, {
            "ai_id":     "",
            "model":     cur_model,
            "prompt":    cur_prompt,
            "files":     new_files,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    for entry in all_ai_entries:
        images = []
        for path in entry.get("files", []):
            if not os.path.exists(path):
                continue
            images.append({
                "filename": os.path.basename(path),
                "file_url": file_url(path),
                "size":     fmt_size(path),
            })
        if not images:
            continue
        ai_list.append({
            "ai_id":     entry.get("ai_id", ""),
            "model":     entry.get("model", ""),
            "prompt":    entry.get("prompt", ""),
            "timestamp": entry.get("timestamp", ""),
            "images":    images,
        })

    return {
        "version":      2,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "search":       search_data,
        "downloads":    dl_list,
        "ai_results":   ai_list,
    }


# ── HTML template ─────────────────────────────────────────────────────────────

HTML_TMPL = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>58pic 预览</title>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --brand:#E8401A;--brand-l:#FF6B35;--brand-bg:#FFF4F0;
  --dark:#1d1d1f;--mid:#424245;--gray:#86868b;
  --border:#d2d2d7;--bg:#f5f5f7;--card:#fff;
  --r:14px;--r-sm:8px
}
body{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Helvetica Neue',sans-serif;
  background:var(--bg);color:var(--dark);min-height:100vh;-webkit-font-smoothing:antialiased}
.hd{background:#000;padding:14px 24px;display:flex;align-items:center;gap:12px;
  position:sticky;top:0;z-index:200}
.logo{width:32px;height:32px;border-radius:8px;
  background:linear-gradient(135deg,var(--brand),var(--brand-l));
  display:flex;align-items:center;justify-content:center;font-size:15px;font-weight:800;color:#fff}
.hd-info{flex:1}
.hd-title{font-size:14px;font-weight:600;color:#fff}
.hd-sub{font-size:11px;color:rgba(255,255,255,.4);margin-top:1px}
.hd-time{font-size:11px;color:rgba(255,255,255,.28)}
.tabs{background:rgba(245,245,247,.95);backdrop-filter:blur(20px);
  border-bottom:1px solid var(--border);padding:0 24px;display:flex;
  position:sticky;top:61px;z-index:190}
.tab{padding:12px 16px;font-size:13px;font-weight:500;color:var(--gray);cursor:pointer;
  border-bottom:2px solid transparent;transition:color .15s,border-color .15s;white-space:nowrap}
.tab:hover{color:var(--brand)}
.tab.on{color:var(--brand);border-bottom-color:var(--brand)}
.tc{background:var(--bg);color:var(--gray);font-size:11px;font-weight:600;
  border-radius:10px;padding:1px 7px;margin-left:5px}
.tab.on .tc{background:var(--brand-bg);color:var(--brand)}
.panel{display:none;min-height:calc(100vh - 120px)}
.panel.on{display:block}
/* Tip bar */
.tip{display:flex;gap:8px;align-items:flex-start;background:var(--brand-bg);
  border:1px solid #ffc4b2;border-radius:var(--r-sm);padding:10px 14px;
  margin:13px 22px 0;font-size:13px;color:#7a1e06;line-height:1.6}
.tip-i{flex-shrink:0;font-size:15px}
/* Stats */
.stats{padding:10px 22px;font-size:13px;color:var(--gray);
  display:flex;align-items:center;gap:6px;flex-wrap:wrap;
  border-bottom:1px solid var(--border);background:var(--card)}
.stats b{color:var(--brand)}
.sep{color:var(--border)}
/* Empty state */
.empty{text-align:center;padding:64px 24px;color:var(--gray)}
.empty-i{font-size:48px;opacity:.4;margin-bottom:12px}
.empty p{font-size:15px}
.empty small{font-size:13px;display:block;margin-top:5px;opacity:.7}
/* Search panel layout (main + sidebar) */
.s-panel{display:flex;min-height:calc(100vh - 120px)}
.s-main{flex:1;min-width:0}
.s-sidebar{width:180px;flex-shrink:0;background:var(--card);
  border-left:1px solid var(--border);
  position:sticky;top:120px;height:calc(100vh - 120px);overflow-y:auto}
.sb-head{padding:11px 13px 8px;font-size:10px;font-weight:600;color:var(--gray);
  text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border)}
.sb-item{display:flex;flex-direction:column;gap:2px;
  padding:9px 13px;cursor:pointer;border-bottom:1px solid #f0f0f2;
  transition:background .12s}
.sb-item:hover{background:var(--bg)}
.sb-item.on{background:var(--brand-bg)}
.sb-kw{font-size:12px;font-weight:500;color:var(--dark);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.sb-item.on .sb-kw{color:var(--brand)}
.sb-ts{font-size:10px;color:var(--gray)}
/* Search grid */
.s-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(185px,1fr));gap:13px;padding:16px 22px}
.card{background:var(--card);border-radius:var(--r);overflow:hidden;
  border:1px solid var(--border);transition:transform .18s,box-shadow .18s}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(0,0,0,.09)}
.img-wrap{width:100%;height:155px;background:#f0f0f2;display:flex;
  align-items:center;justify-content:center;overflow:hidden;position:relative}
.img-wrap img{max-width:100%;max-height:100%;object-fit:contain;
  display:block;transition:transform .22s;cursor:zoom-in}
.card:hover .img-wrap img{transform:scale(1.05)}
.img-ph{font-size:32px;color:#ccc}
.img-ratio{position:absolute;top:5px;right:5px;background:rgba(0,0,0,.42);
  color:#fff;font-size:9px;padding:2px 5px;border-radius:4px;font-family:monospace}
.card-body{padding:9px 11px 11px}
.card-title{font-size:12px;font-weight:500;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis;margin-bottom:6px}
.card-row{display:flex;align-items:center;justify-content:space-between;gap:5px}
.mt6{margin-top:6px}
.badge{font-size:10px;font-weight:500;border-radius:5px;padding:2px 7px}
.b-image,.b-photo{background:#e8f4fd;color:#0070c9}
.b-template{background:#fef3e2;color:#c87a00}
.b-vector{background:#e8faf0;color:#1a7a2a}
.b-psd{background:#f3e8ff;color:#6e2fa0}
.b-gif{background:#fff0e8;color:var(--brand)}
.sz{font-size:11px;color:var(--gray)}
.pid-tag{font-family:monospace;font-size:10px;color:var(--gray);
  background:var(--bg);padding:2px 6px;border-radius:4px;
  flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.copy-btn{flex-shrink:0;background:none;border:1px solid var(--border);
  border-radius:6px;padding:3px 9px;font-size:11px;color:var(--gray);cursor:pointer;transition:all .14s}
.copy-btn:hover{background:var(--brand);color:#fff;border-color:var(--brand)}
.copy-btn.ok{background:#34c759;color:#fff;border-color:#34c759}
/* AI grid */
.ai-section{padding-bottom:4px}
.session-ts{font-size:11px;color:var(--gray);padding:14px 22px 4px;
  border-top:1px solid var(--border);margin-top:4px}
.session-ts:first-child{border-top:none;margin-top:0}
.ai-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(255px,1fr));gap:14px;padding:6px 22px 12px}
.ai-card{background:var(--card);border-radius:var(--r);border:1px solid var(--border);
  overflow:hidden;transition:transform .18s,box-shadow .18s}
.ai-card:hover{transform:translateY(-3px);box-shadow:0 10px 26px rgba(0,0,0,.09)}
.ai-img{width:100%;background:#1c1c1e;display:flex;align-items:center;
  justify-content:center;cursor:zoom-in;min-height:120px;max-height:480px;overflow:hidden}
.ai-img img{width:100%;height:auto;max-height:480px;object-fit:contain;display:block}
.ai-body{padding:10px 13px 12px}
.ai-body h4{font-size:12px;font-weight:600;margin-bottom:3px}
.ai-meta{font-size:11px;color:var(--gray)}
.ai-prompt{background:var(--bg);border-radius:var(--r-sm);padding:6px 10px;
  font-size:11px;color:var(--mid);margin:6px 0;line-height:1.5;border-left:3px solid var(--brand)}
.dl-btn{display:flex;align-items:center;justify-content:center;gap:5px;width:100%;
  background:linear-gradient(135deg,var(--brand),var(--brand-l));
  color:#fff;border:none;border-radius:var(--r-sm);padding:8px;font-size:12px;
  font-weight:600;cursor:pointer;text-decoration:none;margin-top:8px;transition:opacity .15s}
.dl-btn:hover{opacity:.85}
/* Download grid */
.dl-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:13px;padding:14px 22px}
.dl-card{background:var(--card);border-radius:var(--r);border:1px solid var(--border);
  overflow:hidden;transition:transform .18s,box-shadow .18s}
.dl-card:hover{transform:translateY(-3px);box-shadow:0 8px 22px rgba(0,0,0,.08)}
.dl-img{width:100%;height:160px;background:#f0f0f2;display:flex;
  align-items:center;justify-content:center;overflow:hidden;cursor:zoom-in}
.dl-img img{max-width:100%;max-height:100%;object-fit:contain}
.dl-body{padding:9px 11px 10px}
.dl-fn{font-size:12px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:2px}
.dl-sz{font-size:11px;color:var(--gray);margin-bottom:6px}
.dl-open{display:block;width:100%;background:var(--bg);border:1px solid var(--border);
  border-radius:var(--r-sm);padding:6px;font-size:12px;font-weight:500;
  color:var(--mid);text-align:center;text-decoration:none;transition:all .14s}
.dl-open:hover{background:var(--brand-bg);color:var(--brand);border-color:var(--brand)}
/* Lightbox */
.lb{display:none;position:fixed;inset:0;z-index:999;background:rgba(0,0,0,.9);
  align-items:center;justify-content:center;cursor:zoom-out;backdrop-filter:blur(14px)}
.lb.open{display:flex}
.lb img{max-width:92vw;max-height:92vh;object-fit:contain;border-radius:10px}
.lb-x{position:fixed;top:16px;right:20px;width:34px;height:34px;border-radius:50%;
  background:rgba(255,255,255,.12);color:#fff;font-size:17px;display:flex;
  align-items:center;justify-content:center;cursor:pointer;border:none}
.lb-x:hover{background:rgba(255,255,255,.22)}
.lb-cap{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
  background:rgba(0,0,0,.55);color:rgba(255,255,255,.8);font-size:12px;
  padding:5px 16px;border-radius:20px;backdrop-filter:blur(8px);
  white-space:nowrap;max-width:80vw;overflow:hidden;text-overflow:ellipsis}
footer{text-align:center;padding:24px;font-size:12px;color:var(--gray);
  border-top:1px solid var(--border);margin-top:16px}
footer a{color:var(--brand);text-decoration:none}
@media(max-width:640px){
  .s-grid,.ai-grid,.dl-grid{grid-template-columns:repeat(2,1fr);gap:10px;padding:12px}
}
</style>
</head>
<body>
<div class="hd">
  <div class="logo">千</div>
  <div class="hd-info">
    <div class="hd-title" id="hd-title">58pic 预览</div>
    <div class="hd-sub">千图网 AI 开放平台</div>
  </div>
  <div class="hd-time" id="hd-time"></div>
</div>
<div class="tabs" id="tabs"></div>
<div id="panels"></div>
<div class="lb" id="lb" onclick="closeLb()">
  <button class="lb-x" onclick="closeLb()">✕</button>
  <img id="lb-img" src="" alt="">
  <div class="lb-cap" id="lb-cap"></div>
</div>
<footer>
  58pic AI 开放平台 · <a href="https://ai.58pic.com" target="_blank">ai.58pic.com</a>
  · <span id="ft-time"></span>
</footer>
<script>
// ─── Embedded data ───────────────────────────────────────────────────────────
const DATA = __PIC58_DATA__;

// ─── Utilities ───────────────────────────────────────────────────────────────
function h(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;') }
function openLb(src,cap){
  document.getElementById('lb-img').src=src;
  document.getElementById('lb-cap').textContent=cap||'';
  document.getElementById('lb').classList.add('open');
  document.body.style.overflow='hidden';
}
function closeLb(){
  document.getElementById('lb').classList.remove('open');
  document.body.style.overflow='';
}
document.addEventListener('keydown',e=>{ if(e.key==='Escape') closeLb(); });

function copyPid(pid,btn){
  navigator.clipboard.writeText(pid).then(()=>{
    btn.textContent='已复制 ✓'; btn.classList.add('ok');
    setTimeout(()=>{ btn.textContent='复制PID'; btn.classList.remove('ok'); },1700);
  });
}

// ─── Badge ───────────────────────────────────────────────────────────────────
const BADGE_MAP={image:'b-image 图片',photo:'b-image 摄影',vector:'b-vector 矢量',
  psd:'b-psd PSD',template:'b-template 模板',gif:'b-gif GIF'};
function badge(type){
  const t=(type||'').toLowerCase();
  const v=BADGE_MAP[t]||('b-image '+(type||'素材'));
  const[cls,lbl]=v.split(' ');
  return `<span class="badge ${cls}">${lbl}</span>`;
}

// ─── Render: Search ──────────────────────────────────────────────────────────
let _curSearchIdx=0;

function renderSearchItems(s){
  const items=s.items||[];
  const kw=h(s.keyword||'');
  const dn=h(s.did_name||'');
  const stats=`<div class="stats">
    关键词：<b>「${kw}」</b>
    ${dn?`<span class="sep">·</span>分类：<b>${dn}</b>`:''}
    <span class="sep">·</span>第 <b>${s.page||1}</b> 页 / 共 <b>${s.total_page||1}</b> 页
    <span class="sep">·</span>本页 <b>${items.length}</b> 条
    ${s.ai_search?'<span class="sep">·</span><b>AI向量搜索</b>':''}
  </div>`;
  const tip=`<div class="tip"><span class="tip-i">💡</span>
    找到心仪素材？点击「复制PID」，然后告诉我「下载 PID xxxxx」或「用 PID xxxxx 做同款」</div>`;

  if(!items.length){
    return stats+tip+`<div class="empty"><div class="empty-i">🔍</div>
      <p>未找到相关素材</p><small>换个关键词试试</small></div>`;
  }

  const cards=items.map(it=>{
    const pid=h(it.pid||'');
    const title=h(it.title||'无标题');
    const url=it.preview_url||'';
    const w=it.width||''; const h_=it.height||'';
    const sz=w&&h_?`${w}×${h_}`:''
    const imgHtml=url
      ? `<img src="${url}" alt="${title}" loading="lazy"
           onerror="this.parentElement.innerHTML='<div class=img-ph>🖼</div>'"
           onclick="event.stopPropagation();openLb('${url.replace(/'/g,"\\'")}','PID:${pid} · ${title.replace(/'/g,"\\'")}')">
         ${w&&h_?`<div class="img-ratio">${w}×${h_}</div>`:''}`
      : `<div class="img-ph">🖼</div>`;

    return `<div class="card">
  <div class="img-wrap">${imgHtml}</div>
  <div class="card-body">
    <div class="card-title" title="${title}">${title}</div>
    <div class="card-row">${badge(it.type)}<span class="sz">${sz}</span></div>
    <div class="card-row mt6">
      <span class="pid-tag">PID: ${pid}</span>
      <button class="copy-btn" onclick="copyPid('${pid}',this)">复制PID</button>
    </div>
  </div>
</div>`;
  });

  return stats+tip+`<div class="s-grid">${cards.join('')}</div>`;
}

function switchSearchIdx(idx){
  _curSearchIdx=idx;
  const history=(DATA.search||{}).history||[];
  const s=history[idx]||{};
  const mc=document.getElementById('s-main-content');
  if(mc) mc.innerHTML=renderSearchItems(s);
  document.getElementById('hd-title').textContent=`搜索：${s.keyword||''}`;
  document.querySelectorAll('.sb-item').forEach((el,i)=>el.classList.toggle('on',i===idx));
}

function renderSearch(){
  const history=(DATA.search||{}).history||[];
  const el=document.getElementById('panel-search');

  if(!history.length){
    el.innerHTML=`<div class="empty"><div class="empty-i">🔍</div>
      <p>暂无搜索记录</p><small>请先搜索千图素材</small></div>`;
    return;
  }

  const sbItems=history.map((s,i)=>`<div class="sb-item${i===0?' on':''}" onclick="switchSearchIdx(${i})">
    <span class="sb-kw" title="${h(s.keyword||'')}">${h(s.keyword||'')}</span>
    <span class="sb-ts">${h((s.search_time||'').slice(5,16))}</span>
  </div>`).join('');

  el.innerHTML=`<div class="s-panel">
    <div class="s-main" id="s-main-content"></div>
    <div class="s-sidebar"><div class="sb-head">搜索历史</div>${sbItems}</div>
  </div>`;

  const s=history[0]||{};
  document.getElementById('s-main-content').innerHTML=renderSearchItems(s);
  document.getElementById('hd-title').textContent=`搜索：${s.keyword||''}`;
}

// ─── Render: AI results ───────────────────────────────────────────────────────
function renderAi(){
  const results=DATA.ai_results||[];
  const el=document.getElementById('panel-ai');
  const tip=`<div class="tip"><span class="tip-i">✅</span>
    AI 图片已生成！点击图片全屏查看，点击「保存图片」下载到本地。</div>`;

  if(!results.length){
    el.innerHTML=tip+`<div class="empty"><div class="empty-i">🎨</div>
      <p>暂无 AI 生成结果</p></div>`;
    return;
  }

  const sections=results.map(r=>{
    const ts=h(r.timestamp||'');
    const model=h(r.model||'');
    const prompt=h(r.prompt||'');
    const header=ts||model
      ? `<div class="session-ts">🕐 ${ts}${model?' · '+model:''}</div>`
      : '';
    const cards=(r.images||[]).filter(im=>im.file_url).map(im=>{
      const fn=h(im.filename||'');
      const sz=h(im.size||'');
      const src=im.file_url||'';
      return `<div class="ai-card">
  <div class="ai-img" onclick="openLb('${src}','${fn}')">
    <img src="${src}" alt="${fn}" loading="lazy"
         onerror="this.parentElement.innerHTML='<div style=padding:20px;color:#888>文件已移动或删除</div>'">
  </div>
  <div class="ai-body">
    <h4>${fn}</h4>
    <div class="ai-meta">${sz}${model?' · '+model:''}</div>
    ${prompt?`<div class="ai-prompt">📝 ${prompt}</div>`:''}
    <a href="${src}" target="_blank" class="dl-btn">⬇ 在 Finder 中查看</a>
  </div>
</div>`;
    }).join('');
    if(!cards) return '';
    return `<div class="ai-section">${header}<div class="ai-grid">${cards}</div></div>`;
  }).filter(Boolean);

  if(!sections.length){
    el.innerHTML=tip+`<div class="empty"><div class="empty-i">⚠️</div>
      <p>图片文件不存在或已删除</p></div>`;
    return;
  }
  el.innerHTML=tip+sections.join('');
}

// ─── Render: Downloads ────────────────────────────────────────────────────────
function renderDownloads(){
  const list=DATA.downloads||[];
  const el=document.getElementById('panel-downloads');
  const tip=`<div class="tip"><span class="tip-i">📁</span>
    已下载的素材文件。点击图片全屏预览，点击「打开文件」在本地查看。</div>`;

  if(!list.length){
    el.innerHTML=tip+`<div class="empty"><div class="empty-i">📥</div>
      <p>还没有下载任何素材</p><small>搜索素材后告诉我「下载 PID xxxxx」</small></div>`;
    return;
  }

  const IMG_EXTS=/\.(jpe?g|png|webp|gif)$/i;
  const cards=list.map(d=>{
    const fn=h(d.filename||'');
    const sz=h(d.size||'');
    const src=d.file_url||'';
    const pid=d.pid?`<div class="dl-sz">PID: ${h(d.pid)}</div>`:'';
    const isImg=src&&IMG_EXTS.test(d.filename||'');
    const imgHtml=isImg
      ? `<img src="${src}" alt="${fn}" loading="lazy"
             onerror="this.parentElement.innerHTML='<div class=img-ph>📄</div>'">`
      : `<div class="img-ph" style="font-size:36px">📄</div>`;
    const clickAttr=isImg?`onclick="openLb('${src}','${fn}')"`:''

    return `<div class="dl-card">
  <div class="dl-img" ${clickAttr}>${imgHtml}</div>
  <div class="dl-body">
    <div class="dl-fn" title="${fn}">${fn}</div>
    <div class="dl-sz">${sz}${d.timestamp?' · '+h(d.timestamp):''}</div>
    ${pid}
    <a href="${src}" target="_blank" class="dl-open">打开文件</a>
  </div>
</div>`;
  }).join('');

  el.innerHTML=tip+`<div class="dl-grid">${cards}</div>`;
}

// ─── Tab switching ────────────────────────────────────────────────────────────
const TABS=[
  {id:'search',  label:'🔍 搜索结果',  cnt:()=>(DATA.search?.history?.[0]?.items||[]).length},
  {id:'ai',      label:'🤖 AI 生成',   cnt:()=>(DATA.ai_results||[]).reduce((s,r)=>s+(r.images||[]).length,0)},
  {id:'downloads',label:'⬇ 已下载',   cnt:()=>(DATA.downloads||[]).length},
];

function switchTab(id){
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('on', t.dataset.tab===id));
  document.querySelectorAll('.panel').forEach(p=>p.classList.toggle('on', p.id==='panel-'+id));
}

function buildTabs(){
  const tabsEl=document.getElementById('tabs');
  const panelsEl=document.getElementById('panels');
  TABS.forEach((t,i)=>{
    const cnt=t.cnt();
    const cntTag=cnt>0?`<span class="tc">${cnt}</span>`:'';
    const tab=document.createElement('div');
    tab.className='tab'+(i===0?' on':'');
    tab.dataset.tab=t.id;
    tab.innerHTML=t.label+cntTag;
    tab.onclick=()=>switchTab(t.id);
    tabsEl.appendChild(tab);

    const panel=document.createElement('div');
    panel.className='panel'+(i===0?' on':'');
    panel.id='panel-'+t.id;
    panelsEl.appendChild(panel);
  });
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('hd-time').textContent=DATA.generated_at||'';
  document.getElementById('ft-time').textContent=DATA.generated_at||'';
  buildTabs();
  renderSearch();
  renderAi();
  renderDownloads();
});
</script>
</body>
</html>
"""


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    _cfg_dir = get_config_output_dir() or "./58pic_output"

    parser = argparse.ArgumentParser(description="千图网统一预览管理页面 v4")
    parser.add_argument("--results-file",   help="搜索结果 JSON 文件路径（覆盖 session 中的最近一次）")
    parser.add_argument("--image-file",     help="AI 生成单张图片（向后兼容）")
    parser.add_argument("--image-files",    nargs="+", help="AI 生成多张图片（向后兼容）")
    parser.add_argument("--download-files", nargs="+", help="已下载素材文件（向后兼容）")
    parser.add_argument("--prompt",         default="", help="AI 描述词")
    parser.add_argument("--model",          default="", help="AI 模型")
    parser.add_argument("--session-file",   help="session.json 路径，动态加载全部历史数据")
    parser.add_argument("--output",
                        help=f"输出 HTML 路径（默认：session 同目录 or {_cfg_dir}/preview.html）")
    args = parser.parse_args()

    # 加载 session
    session = load_session_file(args.session_file)

    # 确定输出路径
    if args.output:
        output_path = args.output
    elif args.session_file:
        output_path = os.path.join(os.path.dirname(os.path.abspath(args.session_file)), "preview.html")
    else:
        output_path = os.path.join(_cfg_dir, "preview.html")

    # 组装数据
    cur_files = args.image_files or ([args.image_file] if args.image_file else [])
    data = build_data(
        session       = session,
        results_file  = args.results_file,
        cur_image_files    = cur_files,
        cur_prompt    = args.prompt,
        cur_model     = args.model,
        extra_download_files = args.download_files,
    )

    # 生成 HTML（将 JSON 数据内嵌到模板）
    data_json = json.dumps(data, ensure_ascii=False)
    html = HTML_TMPL.replace("__PIC58_DATA__", data_json)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ 预览页面已生成: {output_path}")
    search_items = data['search'].get('items') or (data['search'].get('history') or [{}])[0].get('items', [])
    print(f"   搜索结果: {len(search_items)} 条")
    print(f"   已下载:   {len(data['downloads'])} 个")
    print(f"   AI 生成:  {sum(len(r['images']) for r in data['ai_results'])} 张")
    return output_path


if __name__ == "__main__":
    main()
