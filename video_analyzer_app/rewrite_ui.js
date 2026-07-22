// ── 洗稿重构器 Tab · v2.1（OPC 设计系统 · 分段渲染）──

// ═══ 工具函数 ═══
function escHtml(s) {
  var d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function rTag(label, className) {
  return '<span class="rw-tag ' + className + '">' + escHtml(label) + '</span>';
}

function rNumber(val) {
  return '<span style="font-variant-numeric:tabular-nums">' + escHtml(String(val)) + '</span>';
}

// ═══ 主渲染 ═══
async function renderRewriteTab() {
  var c = document.getElementById('analysisContent');

  // 加载预设
  var presets = {};
  try {
    var r = await fetch('/api/rewrite/presets');
    var d = await r.json();
    presets = d.presets || {};
  } catch(e) {}

  c.innerHTML =
    '<div style="max-width:720px;margin:0 auto;padding:var(--space-6)">'+

    // 页头
    '<div style="margin-bottom:var(--space-6)">'+
      '<h2 style="font-size:var(--text-xl);font-weight:var(--weight-semibold);color:var(--text-primary);margin-bottom:var(--space-2)">✂️ 洗稿重构</h2>'+
      '<p style="font-size:var(--text-sm);color:var(--text-secondary);line-height:var(--leading-sm)">取内核卡的经典桥段结构 → 嫁接新设定 → 5步缝合工艺 → 生成新定向脚本</p>'+
    '</div>'+

    // Step 1: 风格预设
    '<div class="r-section" style="margin-bottom:var(--space-5)">'+
      '<div style="display:flex;align-items:center;gap:var(--space-2);margin-bottom:var(--space-3)">'+
        '<span style="display:flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:var(--accent);color:var(--text-inverse);font-size:var(--text-xs);font-weight:var(--weight-semibold);flex-shrink:0">1</span>'+
        '<span style="font-size:var(--text-base);font-weight:var(--weight-medium);color:var(--text-primary)">选择风格预设</span>'+
        '<span style="font-size:var(--text-xs);color:var(--text-tertiary)">点击卡片自动填入表单，再点击已选中可取消</span>'+
      '</div>'+
      '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:var(--space-3)" id="presetCards">'+
        Object.keys(presets).map(function(k) {
          var p = presets[k];
          return '<div class="r-preset-card" onclick="togglePreset(\''+escHtml(k)+'\', event)" data-preset="'+escHtml(k)+'">'+
            '<div style="font-size:var(--text-base);font-weight:var(--weight-medium);color:var(--text-primary);margin-bottom:var(--space-1)">'+escHtml(p.new_ip_name||k)+'</div>'+
            '<div style="font-size:var(--text-xs);color:var(--text-secondary);line-height:1.4">'+escHtml(p.new_style||'')+' · '+escHtml(p.new_setting||'')+'</div>'+
            '<div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:var(--space-1)">'+escHtml(p.tone_shift||'')+'</div>'+
          '</div>';
        }).join('')+
      '</div>'+
      '<div style="margin-top:var(--space-2);font-size:var(--text-xs);color:var(--text-tertiary)">共 '+Object.keys(presets).length+' 个预设可用</div>'+
    '</div>'+

    // Step 2: 目标设定 — 渐进披露：默认折叠表单，预设卡片点击时展开
    '<div class="r-section" style="margin-bottom:var(--space-5)">'+
      '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:var(--space-3)">'+
        '<div style="display:flex;align-items:center;gap:var(--space-2)">'+
          '<span style="display:flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;background:var(--accent);color:var(--text-inverse);font-size:var(--text-xs);font-weight:var(--weight-semibold);flex-shrink:0">2</span>'+
          '<span style="font-size:var(--text-base);font-weight:var(--weight-medium);color:var(--text-primary)">目标设定</span>'+
        '</div>'+
        '<button onclick="toggleTargetForm()" id="rwFormToggle"'+
          ' style="background:none;border:1px solid rgba(255,255,255,0.06);border-radius:var(--radius-sm);color:var(--text-secondary);cursor:pointer;font-size:var(--text-xs);padding:4px var(--space-3);transition:all var(--transition-fast) ease;">'+
          '展开 ▼</button>'+
      '</div>'+
      // 摘要条 — 始终可见
      '<div id="rwFormSummary"'+
        ' style="padding:var(--space-3);background:var(--bg-surface);border:1px solid rgba(255,255,255,0.06);border-radius:var(--radius-md);font-size:var(--text-sm);color:var(--text-secondary);">'+
        '点击预设卡片或手动展开表单来配置目标</div>'+
      // 完整表单 — 默认隐藏
      '<div id="rwFormBody" class="r-card" style="padding:var(--space-4);margin-top:var(--space-3);display:none">'+
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-3)">'+
          '<div>'+
            '<label class="r-label">新IP名称</label>'+
            '<input type="text" class="r-input" id="rwName" placeholder="例: 东京恋爱物语">'+
          '</div>'+
          '<div>'+
            '<label class="r-label">风格方向</label>'+
            '<select class="r-input" id="rwStyle">'+
              '<option value="日系清新">日系清新</option><option value="韩系唯美">韩系唯美</option>'+
              '<option value="王家卫">王家卫</option><option value="市井喜剧">市井喜剧</option>'+
              '<option value="都市爱情">都市爱情</option>'+
            '</select>'+
          '</div>'+
          '<div>'+
            '<label class="r-label">新场景设定</label>'+
            '<input type="text" class="r-input" id="rwSetting" placeholder="例: 东京·下北泽">'+
          '</div>'+
          '<div>'+
            '<label class="r-label">年代</label>'+
            '<input type="text" class="r-input" id="rwEra" value="2020s" placeholder="例: 2020s">'+
          '</div>'+
        '</div>'+
        '<div style="margin-top:var(--space-3)">'+
          '<label class="r-label">母题策略</label>'+
          '<select class="r-input" id="rwTone">'+
            '<option value="保持原内核">保持原内核 — 母题不变，替换表层</option>'+
            '<option value="强化">强化 — 放大情感张力和冲突</option>'+
            '<option value="反转">反转 — 母题方向反向表达</option>'+
          '</select>'+
        '</div>'+
        '<div style="margin-top:var(--space-3)">'+
          '<label class="r-label">补充说明（可选）</label>'+
          '<textarea class="r-input" id="rwNotes" placeholder="如：角色映射、场景替换建议、想要的效果..." style="min-height:72px;resize:vertical"></textarea>'+
        '</div>'+
      '</div>'+
    '</div>'+

    // Step 3: 执行
    '<div style="text-align:center;margin-bottom:var(--space-6)">'+
      '<button class="r-btn-primary" onclick="runRewriteV2()" id="rwRunBtn">🔄 运行 5 步缝合工艺</button>'+
    '</div>'+

    // 结果区
    '<div id="rwResult" style="display:none"></div>'+
    '</div>';

  window._rwPresets = presets;
}

// ═══ 预设交互 ═══
function togglePreset(name, event) {
  event.stopPropagation();
  var card = document.querySelector('.r-preset-card[data-preset="'+escHtml(name)+'"]');
  var isSelected = card && card.classList.contains('selected');

  // 取消选中
  if (isSelected) {
    card.classList.remove('selected');
    // 清空表单摘要
    updateFormSummary(null);
    return;
  }

  // 选中：先清除其他
  document.querySelectorAll('.r-preset-card').forEach(function(c) { c.classList.remove('selected'); });
  if (card) card.classList.add('selected');

  var p = window._rwPresets ? window._rwPresets[name] : null;
  if (!p) return;

  document.getElementById('rwName').value = p.new_ip_name || '';
  document.getElementById('rwStyle').value = p.new_style || '';
  document.getElementById('rwSetting').value = p.new_setting || '';
  document.getElementById('rwEra').value = p.new_era || '';
  document.getElementById('rwTone').value = p.tone_shift || '保持原内核';
  document.getElementById('rwNotes').value = (p.character_map ? '角色映射: '+JSON.stringify(p.character_map)+'\n' : '') + (p.scene_map ? '场景映射: '+JSON.stringify(p.scene_map) : '') + (p.extra_notes ? '\n'+p.extra_notes : '');

  updateFormSummary(p);
  // 自动展开表单
  showTargetForm();
}

function toggleTargetForm() {
  var body = document.getElementById('rwFormBody');
  if (body.style.display === 'none') {
    showTargetForm();
  } else {
    hideTargetForm();
  }
}

function showTargetForm() {
  document.getElementById('rwFormBody').style.display = '';
  document.getElementById('rwFormToggle').innerHTML = '收起 ▲';
}

function hideTargetForm() {
  document.getElementById('rwFormBody').style.display = 'none';
  document.getElementById('rwFormToggle').innerHTML = '展开 ▼';
}

function updateFormSummary(preset) {
  var summary = document.getElementById('rwFormSummary');
  var name = document.getElementById('rwName').value;
  var style = document.getElementById('rwStyle').value;
  var setting = document.getElementById('rwSetting').value;
  var tone = document.getElementById('rwTone').value;

  if (!name) {
    summary.innerHTML = '<span style="color:var(--text-tertiary)">点击预设卡片或手动展开表单来配置目标</span>';
  } else {
    summary.innerHTML =
      '<span style="font-weight:var(--weight-medium);color:var(--text-primary)">'+escHtml(name)+'</span>'+
      ' · <span style="color:var(--text-secondary)">'+escHtml(style)+'</span>'+
      ' · <span style="color:var(--text-secondary)">'+escHtml(setting)+'</span>'+
      ' · <span style="color:var(--text-tertiary)">'+escHtml(tone)+'</span>';
  }
}

// ═══ 执行洗稿 ═══
async function runRewriteV2() {
  var btn = document.getElementById('rwRunBtn');
  var resultDiv = document.getElementById('rwResult');
  btn.textContent = '⏳ 洗稿中...';
  btn.disabled = true;
  resultDiv.style.display = 'block';

  // 骨架屏
  resultDiv.innerHTML = renderSkeleton();

  try {
    var charMap = {}, sceneMap = {};
    var notes = document.getElementById('rwNotes').value;
    var charMatch = notes.match(/角色映射:\s*(\{[^}]+\})/);
    var sceneMatch = notes.match(/场景映射:\s*(\{[^}]+\})/);
    try { if (charMatch) charMap = JSON.parse(charMatch[1]); } catch(e) {}
    try { if (sceneMatch) sceneMap = JSON.parse(sceneMatch[1]); } catch(e) {}

    var body = {
      new_ip_name: document.getElementById('rwName').value || '新短剧',
      new_style: document.getElementById('rwStyle').value,
      new_setting: document.getElementById('rwSetting').value || '现代都市',
      new_era: document.getElementById('rwEra').value || '2020s',
      tone_shift: document.getElementById('rwTone').value,
      character_map: charMap, scene_map: sceneMap, extra_notes: notes
    };

    var r = await fetch('/api/rewrite/run', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body)
    });
    var d = await r.json();

    if (d.error) {
      resultDiv.innerHTML = '<div class="r-card" style="padding:var(--space-4);color:var(--danger);font-size:var(--text-sm)">❌ '+escHtml(d.error)+'</div>';
    } else {
      resultDiv.innerHTML = renderResults(d);
    }
  } catch(e) {
    resultDiv.innerHTML = '<div class="r-card" style="padding:var(--space-4);color:var(--danger);font-size:var(--text-sm)">❌ '+escHtml(e.message)+'</div>';
  } finally {
    btn.textContent = '🔄 重新运行';
    btn.disabled = false;
  }
}

// ═══ 骨架屏 ═══
function renderSkeleton() {
  var blocks = [
    '<div class="r-card" style="padding:var(--space-6)">',
    '<div style="height:16px;width:40%;background:var(--bg-elevated);border-radius:var(--radius-sm);margin-bottom:var(--space-4);animation:skeleton-pulse 1.5s infinite"></div>',
    '<div style="height:12px;width:80%;background:var(--bg-elevated);border-radius:var(--radius-sm);margin-bottom:var(--space-2);animation:skeleton-pulse 1.5s infinite"></div>',
    '<div style="height:12px;width:60%;background:var(--bg-elevated);border-radius:var(--radius-sm);margin-bottom:var(--space-4);animation:skeleton-pulse 1.5s infinite"></div>',
    '<div style="height:8px;width:100%;background:var(--bg-elevated);border-radius:var(--radius-sm);margin-bottom:var(--space-2);animation:skeleton-pulse 1.5s infinite 0.15s"></div>',
    '<div style="height:8px;width:90%;background:var(--bg-elevated);border-radius:var(--radius-sm);margin-bottom:var(--space-2);animation:skeleton-pulse 1.5s infinite 0.15s"></div>',
    '<div style="height:8px;width:70%;background:var(--bg-elevated);border-radius:var(--radius-sm);animation:skeleton-pulse 1.5s infinite 0.15s"></div>',
    '</div>'
  ];
  return blocks.join('');
}

// ═══ 结果分段渲染 ═══
function renderResults(d) {
  var parts = [];

  // ── 1. KPI 统计卡片 ──
  parts.push(renderStatsCard(d));

  // ── 2. 母题声明卡片 ──
  parts.push(renderMotifCard(d));

  // ── 3. 结构骨架 — 渐进披露 ──
  parts.push(renderStructureSkeleton(d));

  // ── 4. 枢纽场景 — 渐进披露 ──
  parts.push(renderPivotalScenes(d));

  // ── 5. 转调提示 — 渐进披露 ──
  parts.push(renderTransitions(d));

  // ── 6. 主题闭环 ──
  parts.push(renderThemeClosure(d));

  // ── 7. 原始脚本 — 可展开 ──
  parts.push(renderRawScript(d));

  return parts.join('');
}

// ─── KPI 统计卡片 ───
function renderStatsCard(d) {
  var beatsCount = d.beats_rewritten || 0;
  var scenesCount = d.pivotal_scenes || 0;
  var transitionsCount = d.transitions || 0;

  return '<div class="rw-stats-card">'+
    '<div style="display:flex;gap:var(--space-6);align-items:center;flex-wrap:wrap">'+
      '<div style="display:flex;align-items:baseline;gap:var(--space-2)">'+
        '<span class="stat-value" style="color:var(--accent)">'+beatsCount+'</span>'+
        '<span style="font-size:var(--text-xs);color:var(--text-tertiary)">节拍重构</span>'+
      '</div>'+
      '<div style="display:flex;align-items:baseline;gap:var(--space-2)">'+
        '<span class="stat-value" style="color:var(--success)">'+scenesCount+'</span>'+
        '<span style="font-size:var(--text-xs);color:var(--text-tertiary)">枢纽场景</span>'+
      '</div>'+
      '<div style="display:flex;align-items:baseline;gap:var(--space-2)">'+
        '<span class="stat-value" style="color:var(--warning)">'+transitionsCount+'</span>'+
        '<span style="font-size:var(--text-xs);color:var(--text-tertiary)">转调衔接</span>'+
      '</div>'+
      '<span style="flex:1"></span>'+
      '<span style="font-size:var(--text-xs);color:var(--text-tertiary)">📁 '+escHtml(d.output_path||'')+'</span>'+
    '</div></div>';
}

// ─── 母题声明卡片 ───
function renderMotifCard(d) {
  var motif = d.motif_statement || '';
  if (!motif) return '';

  // motif 是 markdown 文本，用 pre 保留格式
  return '<div class="rw-motif-card">'+
    '<div style="font-size:var(--text-xs);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:var(--space-3)">🎯 新母题声明</div>'+
    '<pre style="font-family:var(--font-sans);font-size:var(--text-sm);color:var(--text-primary);white-space:pre-wrap;line-height:1.6;margin:0">'+
      escHtml(motif)+
    '</pre>'+
  '</div>';
}

// ─── 结构骨架 — 渐进披露（默认只显示摘要，展开看全部节拍） ───
function renderStructureSkeleton(d) {
  var skeleton = d.structure_skeleton || [];
  if (!skeleton.length) return '';

  // 分离 beats 和 dependency_chains
  var beats = [];
  var chains = [];
  skeleton.forEach(function(item) {
    if (item && typeof item === 'object') {
      if ('beat_id' in item) {
        beats.push(item);
      } else if ('dependency_chains' in item && item.dependency_chains) {
        chains = item.dependency_chains || [];
      }
    }
  });

  if (!beats.length && !chains.length) return '';

  var id = 'skel_' + Math.random().toString(36).substr(2, 6);

  // 摘要行
  var summaryHtml = '<span style="font-weight:var(--weight-medium);color:var(--text-primary)">'+
      beats.length+' 个节拍 · '+
      chains.length+' 条依赖链</span>'+
    '<span style="color:var(--text-tertiary);margin-left:var(--space-2)">（点击展开查看详情）</span>';

  var bodyHtml = '';

  // 节拍列表 — 每个节拍也是渐进披露（默认摘要，点击展开详情）
  if (beats.length) {
    bodyHtml += '<div style="margin-bottom:var(--space-3)">'+
      '<div style="font-size:var(--text-xs);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:var(--space-2)">📋 节拍详情</div>';
    beats.forEach(function(b, i) {
      var beatId = id + '_b' + i;
      var slot = b.narrative_slot || '';
      var coupling = b.coupling_degree || '';
      var slotClass = 'slot-' + (slot || 'unknown');
      var couplingClass = 'coupling-' + (coupling || 'unknown');

      bodyHtml += '<div class="rw-beat-row" onclick="toggleBeat(\''+beatId+'\')" id="'+beatId+'">'+
        '<div style="display:flex;align-items:center;gap:var(--space-2);flex-wrap:wrap">'+
          '<span style="font-size:var(--text-sm);font-weight:var(--weight-medium);color:var(--text-primary)">'+
            escHtml(b.new_name || b.original_name || ('节拍 #'+(i+1)))+
          '</span>'+
          (slot ? rTag(slot, slotClass) : '')+
          (coupling ? rTag(coupling, couplingClass) : '')+
          '<span style="flex:1"></span>'+
          '<span style="font-size:var(--text-xs);color:var(--text-tertiary);transition:transform var(--transition-fast) ease" class="beat-chevron">▶</span>'+
        '</div>'+
        // 展开的详情
        '<div class="beat-detail">'+
          (b.original_name ? '<div style="margin-bottom:var(--space-2)"><span style="font-size:var(--text-xs);color:var(--text-tertiary)">原参考：</span><span style="font-size:var(--text-sm);color:var(--text-secondary)">'+escHtml(b.original_name)+'</span></div>' : '')+
          (b.new_characters && b.new_characters.length ? '<div style="margin-bottom:var(--space-2)"><span style="font-size:var(--text-xs);color:var(--text-tertiary)">新角色：</span><span style="font-size:var(--text-sm);color:var(--text-secondary)">'+escHtml(b.new_characters.join(', '))+'</span></div>' : '')+
          (b.new_setting ? '<div style="margin-bottom:var(--space-2)"><span style="font-size:var(--text-xs);color:var(--text-tertiary)">新场景：</span><span style="font-size:var(--text-sm);color:var(--text-secondary)">'+escHtml(b.new_setting)+'</span></div>' : '')+
          (b.new_psychological_mechanism ? '<div style="margin-bottom:var(--space-2)"><span style="font-size:var(--text-xs);color:var(--text-tertiary)">心理机制：</span><span style="font-size:var(--text-sm);color:var(--text-secondary);line-height:1.5">'+escHtml(b.new_psychological_mechanism)+'</span></div>' : '')+
          (b.new_dialogue_hint ? '<div style="margin-bottom:var(--space-2)"><span style="font-size:var(--text-xs);color:var(--text-tertiary)">对白方向：</span><span style="font-size:var(--text-sm);color:var(--text-secondary)">'+escHtml(b.new_dialogue_hint)+'</span></div>' : '')+
          (b.new_action_hint ? '<div style="margin-bottom:var(--space-2)"><span style="font-size:var(--text-xs);color:var(--text-tertiary)">动作方向：</span><span style="font-size:var(--text-sm);color:var(--text-secondary)">'+escHtml(b.new_action_hint)+'</span></div>' : '')+
          (b.provenance ? '<div style="font-size:var(--text-xs);color:var(--text-tertiary)">来源：'+escHtml(b.provenance.source_work||'(未知)')+'</div>' : '')+
        '</div>'+
      '</div>';
    });
    bodyHtml += '</div>';
  }

  // 依赖链
  if (chains.length) {
    bodyHtml += '<div style="margin-bottom:var(--space-2)">'+
      '<div style="font-size:var(--text-xs);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:var(--space-2)">🔗 依赖链（锁死顺序不变）</div>';
    chains.forEach(function(chain) {
      var chainStr = (chain.beats || []).join(' → ');
      bodyHtml += '<div style="margin-bottom:var(--space-3)">'+
        '<span class="rw-chain-badge">🔒 '+escHtml(chain.name||'')+'</span>'+
        '<span style="font-size:var(--text-sm);color:var(--text-secondary)">'+escHtml(chainStr)+'</span>'+
        '<div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:var(--space-1)">'+escHtml(chain.invariant_reason||'')+'</div>'+
      '</div>';
    });
    bodyHtml += '</div>';
  }

  return '<div class="rw-collapsible open" id="'+id+'">'+
    '<div class="rw-collapsible-header" onclick="toggleCollapsible(\''+id+'\')">'+
      '<div style="display:flex;align-items:center;gap:var(--space-2)">'+
        '<span style="font-size:var(--text-sm);font-weight:var(--weight-medium);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.5px">🏗️ 结构骨架</span>'+
        summaryHtml+
      '</div>'+
      '<span class="rw-chevron">▼</span>'+
    '</div>'+
    '<div class="rw-collapsible-body">'+
      bodyHtml+
    '</div>'+
  '</div>';
}

// ─── 枢纽场景 — 渐进披露 ───
function renderPivotalScenes(d) {
  var scenes = d.pivotal_scenes_data || [];
  if (!scenes.length) return '';

  var id = 'ps_' + Math.random().toString(36).substr(2, 6);

  var bodyHtml = '';
  scenes.forEach(function(scene, i) {
    bodyHtml += '<div class="rw-scene-card">'+
      '<div style="display:flex;align-items:center;gap:var(--space-2);margin-bottom:var(--space-3)">'+
        '<span style="display:flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:var(--accent);color:var(--text-inverse);font-size:10px;font-weight:var(--weight-semibold);flex-shrink:0">'+(i+1)+'</span>'+
        '<span style="font-size:var(--text-base);font-weight:var(--weight-medium);color:var(--text-primary)">'+escHtml(scene.scene_title||('场景'+(i+1)))+'</span>'+
      '</div>'+
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-2) var(--space-4);margin-bottom:var(--space-3)">'+
        '<div><span style="font-size:var(--text-xs);color:var(--text-tertiary)">角色</span><div style="font-size:var(--text-sm);color:var(--text-primary)">'+escHtml(scene.characters||'—')+'</div></div>'+
        '<div><span style="font-size:var(--text-xs);color:var(--text-tertiary)">地点</span><div style="font-size:var(--text-sm);color:var(--text-primary)">'+escHtml(scene.setting||'—')+'</div></div>'+
      '</div>'+
      '<div style="margin-bottom:var(--space-3)"><span style="font-size:var(--text-xs);color:var(--text-tertiary)">叙事功能</span><div style="font-size:var(--text-sm);color:var(--text-secondary)">'+escHtml(scene.narrative_function||'—')+'</div></div>'+
      '<div>'+
        '<div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-bottom:var(--space-2)">对白草稿</div>'+
        '<pre style="font-family:var(--font-sans);font-size:var(--text-sm);color:var(--text-primary);white-space:pre-wrap;line-height:1.6;margin:0;padding:var(--space-3);background:var(--bg-surface);border-radius:var(--radius-sm);border:1px solid rgba(255,255,255,0.04)">'+
          escHtml(scene.dialogue_draft||'(暂无对白草稿)')+
        '</pre>'+
      '</div>'+
    '</div>';
  });

  return '<div class="rw-collapsible open" id="'+id+'">'+
    '<div class="rw-collapsible-header" onclick="toggleCollapsible(\''+id+'\')">'+
      '<div style="display:flex;align-items:center;gap:var(--space-2)">'+
        '<span style="font-size:var(--text-sm);font-weight:var(--weight-medium);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.5px">🎬 枢纽场景</span>'+
        '<span style="font-weight:var(--weight-medium);color:var(--text-primary)">'+scenes.length+' 个</span>'+
        '<span style="color:var(--text-tertiary)">（点击展开查看对白草稿）</span>'+
      '</div>'+
      '<span class="rw-chevron">▼</span>'+
    '</div>'+
    '<div class="rw-collapsible-body">'+
      bodyHtml+
    '</div>'+
  '</div>';
}

// ─── 转调提示 — 渐进披露 ───
function renderTransitions(d) {
  var transitions = d.transitions_data || [];
  if (!transitions.length) return '';

  var id = 'tr_' + Math.random().toString(36).substr(2, 6);

  var bodyHtml = '';
  transitions.forEach(function(t, i) {
    var tLabel = (t.from_beat||'') + ' → ' + (t.to_beat||'');
    if (t.transition) tLabel = t.transition;

    bodyHtml += '<div class="rw-transition-card">'+
      '<div style="font-size:var(--text-sm);font-weight:var(--weight-medium);color:var(--text-primary);margin-bottom:var(--space-3)">'+
        '🔄 '+escHtml(tLabel)+
      '</div>'+
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-2) var(--space-4)">'+
        '<div><span style="font-size:var(--text-xs);color:var(--text-tertiary)">BGM 建议</span><div style="font-size:var(--text-sm);color:var(--text-secondary)">'+escHtml(t.bgm_suggestion||'—')+'</div></div>'+
        '<div><span style="font-size:var(--text-xs);color:var(--text-tertiary)">节奏变化</span><div style="font-size:var(--text-sm);color:var(--text-secondary)">'+escHtml(t.pace_shift||'—')+'</div></div>'+
        '<div><span style="font-size:var(--text-xs);color:var(--text-tertiary)">画面切换</span><div style="font-size:var(--text-sm);color:var(--text-secondary)">'+escHtml(t.visual_shift||'—')+'</div></div>'+
        '<div><span style="font-size:var(--text-xs);color:var(--text-tertiary)">情绪桥</span><div style="font-size:var(--text-sm);color:var(--text-secondary)">'+escHtml(t.emotion_bridge||'—')+'</div></div>'+
      '</div>'+
    '</div>';
  });

  return '<div class="rw-collapsible" id="'+id+'">'+
    '<div class="rw-collapsible-header" onclick="toggleCollapsible(\''+id+'\')">'+
      '<div style="display:flex;align-items:center;gap:var(--space-2)">'+
        '<span style="font-size:var(--text-sm);font-weight:var(--weight-medium);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.5px">🎵 场景间转调提示</span>'+
        '<span style="font-weight:var(--weight-medium);color:var(--text-primary)">'+transitions.length+' 处</span>'+
        '<span style="color:var(--text-tertiary)">（点击展开查看详情）</span>'+
      '</div>'+
      '<span class="rw-chevron">▼</span>'+
    '</div>'+
    '<div class="rw-collapsible-body">'+
      bodyHtml+
    '</div>'+
  '</div>';
}

// ─── 主题闭环 ───
function renderThemeClosure(d) {
  var closure = d.theme_closure || '';
  if (!closure) return '';

  return '<div class="rw-theme-card">'+
    '<div style="font-size:var(--text-xs);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:var(--space-2)">🔄 主题闭环</div>'+
    '<div style="font-size:var(--text-sm);color:var(--text-primary);line-height:1.6;white-space:pre-wrap">'+escHtml(closure)+'</div>'+
  '</div>';
}

// ─── 原始完整脚本 — 可展开 ───
function renderRawScript(d) {
  var script = d.script || '';
  if (!script.trim()) return '';

  var id = 'raw_' + Math.random().toString(36).substr(2, 6);

  return '<div class="rw-collapsible" id="'+id+'">'+
    '<div class="rw-collapsible-header" onclick="toggleCollapsible(\''+id+'\')">'+
      '<div style="display:flex;align-items:center;gap:var(--space-2)">'+
        '<span style="font-size:var(--text-sm);font-weight:var(--weight-medium);color:var(--text-tertiary);text-transform:uppercase;letter-spacing:0.5px">📄 完整脚本</span>'+
        '<span style="color:var(--text-tertiary)">（点击展开查看 Markdown 原文）</span>'+
      '</div>'+
      '<span class="rw-chevron">▼</span>'+
    '</div>'+
    '<div class="rw-collapsible-body">'+
      '<pre style="font-family:var(--font-mono);font-size:var(--text-sm);line-height:1.6;white-space:pre-wrap;color:var(--text-primary);max-height:60vh;overflow-y:auto;padding:var(--space-4);background:var(--bg-base);border-radius:var(--radius-sm);border:1px solid var(--border-subtle)">'+escHtml(script)+'</pre>'+
    '</div>'+
  '</div>';
}

// ═══ UI 交互函数 ═══

function toggleCollapsible(id) {
  var el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle('open');
}

function toggleBeat(id) {
  var el = document.getElementById(id);
  if (!el) return;
  el.classList.toggle('expanded');
  // 更新 chevron
  var chevron = el.querySelector('.beat-chevron');
  if (chevron) {
    chevron.style.transform = el.classList.contains('expanded') ? 'rotate(90deg)' : 'rotate(0deg)';
  }
}
