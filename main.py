import requests
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

# 北京时间 (+8)
BJT = timezone(timedelta(hours=8))
def beijing_now():
    return datetime.now(BJT)
from openai import OpenAI

# -------------------------- 配置区域 --------------------------
# ================================================================
# 👇 在这里修改为你自己的基金代码
# 格式: ("基金名称", "基金代码")
# 基金代码可以在天天基金网搜索基金名称获得
# ================================================================
FUND_GROUPS = {
    "宽基": [
        ("沪深300", "110020"),
        ("中证500", "007028"),
    ],
    "行业板块": [
        ("机器人", "018344"),
        ("科创AI", "023564"),
    ],
}
# ================================================================
# 添加更多基金：在对应板块的列表里加一行 ("基金名称", "代码") 即可
# 也可以新增板块：在 FUND_GROUPS 里加新的 key
# ================================================================

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY")

OUTPUT_DIR = os.path.join(os.getcwd(), "output")

# 展平基金列表，方便迭代
ALL_FUNDS = []
for group, funds in FUND_GROUPS.items():
    for name, code in funds:
        ALL_FUNDS.append({"name": name, "code": code, "group": group})

if not DEEPSEEK_KEY:
    print("❌ 未检测到 DEEPSEEK_API_KEY，AI分析将不可用")
else:
    print("✅ DEEPSEEK_API_KEY 已加载")


# -------------------------- 数据获取 --------------------------
def get_fund_data_from_eastmoney(fund_code, max_days=90):
    """从天天基金网获取基金历史净值数据，最多返回 max_days 条"""
    url = f"http://fund.eastmoney.com/pingzhongdata/{fund_code}.js"
    try:
        response = requests.get(url, timeout=10)
        response.encoding = "utf-8"
        content = response.text

        start = content.find("Data_netWorthTrend = ") + len("Data_netWorthTrend = ")
        end = content.find(";", start)
        net_worth_json = content[start:end]

        if not net_worth_json.strip():
            print(f"❌ 基金{fund_code}：未找到净值数据字段")
            return None

        net_worth_list = json.loads(net_worth_json)

        days_data = []
        for item in net_worth_list:
            beijing_time = datetime.fromtimestamp(item["x"] / 1000) + timedelta(hours=8)
            date = beijing_time.strftime("%Y-%m-%d")
            nav = round(float(item["y"]), 4)
            change = round(float(item["equityReturn"]), 2)
            days_data.append({"date": date, "nav": nav, "change": change})

        days_data.reverse()  # 最新日期在前
        days_data = days_data[:max_days]
        print(f"✅ 基金{fund_code} 数据获取成功，共{len(days_data)}条，最新：{days_data[0]['date']}")
        return days_data

    except Exception as e:
        print(f"❌ 获取基金{fund_code}数据失败: {repr(e)}")
        return None


def calc_weekly_change(days_data):
    """计算周涨跌幅（基于最近完整的自然周）"""
    today = beijing_now()
    week_start = today - timedelta(days=today.weekday())
    week_start_str = week_start.strftime("%Y-%m-%d")
    week_data = [d for d in days_data if d["date"] >= week_start_str]
    if len(week_data) >= 2:
        week_data_sorted = sorted(week_data, key=lambda x: x["date"])
        first_nav = week_data_sorted[0]["nav"]
        last_nav = week_data_sorted[-1]["nav"]
        return round((last_nav - first_nav) / first_nav * 100, 2)
    return None


def calc_monthly_change(days_data):
    """计算月涨跌幅"""
    if len(days_data) < 2:
        return None
    first_nav = days_data[-1]["nav"]
    last_nav = days_data[0]["nav"]
    return round((last_nav - first_nav) / first_nav * 100, 2)


# -------------------------- AI 分析 (DeepSeek) --------------------------
def _build_fund_summary(all_funds_data):
    """按板块汇总基金数据，附带周涨跌幅"""
    groups = {"宽基": [], "行业板块": []}
    for fund in all_funds_data:
        if not fund["data"]:
            continue
        latest = fund["data"][0]
        # 找近一周前的最早净值（取 5~7 天前数据点）
        week_change = None
        for d in fund["data"]:
            if d["date"] < (beijing_now() - timedelta(days=7)).strftime("%Y-%m-%d"):
                base_nav = d["nav"]
                week_change = round((latest["nav"] - base_nav) / base_nav * 100, 2)
                break
        groups[fund["group"]].append({
            "name": fund["name"],
            "code": fund["code"],
            "nav": latest["nav"],
            "day_change": latest["change"],
            "week_change": week_change,
        })
    return groups


def call_deepseek_analysis(all_funds_data):
    """调用 DeepSeek 分析涨跌原因（深度、板块联动）"""
    if not DEEPSEEK_KEY:
        return "DeepSeek API Key 未配置，无法生成分析"

    client = OpenAI(api_key=DEEPSEEK_KEY, base_url="https://api.deepseek.com")
    groups = _build_fund_summary(all_funds_data)
    today = beijing_now().strftime("%Y-%m-%d")

    prompt = f"你是一位资深 A 股/美股分析师。今天是 {today}。请基于以下基金净值数据，给出深度、专业的板块级市场分析报告。\n\n"

    prompt += "【宽基板块表现】\n"
    for f in groups["宽基"]:
        wc = f"{f['week_change']:+.2f}%" if f['week_change'] is not None else "数据不足"
        prompt += f"- {f['name']}（{f['code']}）：今日 {f['day_change']:+.2f}%，近一周累计 {wc}\n"

    prompt += "\n【行业板块表现】\n"
    for f in groups["行业板块"]:
        wc = f"{f['week_change']:+.2f}%" if f['week_change'] is not None else "数据不足"
        prompt += f"- {f['name']}（{f['code']}）：今日 {f['day_change']:+.2f}%，近一周累计 {wc}\n"

    prompt += """
请按以下结构输出（Markdown 格式，不要用代码块包裹）：

## 📊 整体市场定调
用 2-3 句话概括今日 A 股与美股的整体表现，包括主要宽基的强弱对比、风格切换迹象。

## 🌐 宽基板块联动分析
解读宽基之间涨跌差异背后的逻辑（如：A股 vs 美股、大盘 vs 中小盘、消费/科技/金融轮动等），要分析清楚"为什么"。

## 🏭 行业板块深度分析
分别解读机器人、航空装备、科创 AI 三个行业板块的独立表现：是否有政策、事件、资金推动？强弱分化的原因是什么？

## 💡 资金面与情绪面
结合近期北向资金、成交量、市场情绪、汇率等，判断当前资金流向与风险偏好。

## 🔮 短期关键观察点
列出 2-3 个未来 1-2 周需要重点关注的信号（政策窗口、行业事件、外部冲击等）。

严格要求：
1. 深度优先，重在"为什么"而非"是什么"，避免泛泛而谈
2. 严禁编造不存在的政策/事件/数据，未知可写"待确认"或省略
3. 不要重复罗列每只基金的数字，重点在解读
4. 总字数 600-1000 字
"""

    try:
        print(f"🤖 正在调用 DeepSeek 深度分析...")
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一位严谨的金融市场分析师，只陈述有依据的事实和逻辑推演，不编造数据。"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
            temperature=0.4,
        )
        text = resp.choices[0].message.content
        print(f"✅ DeepSeek 分析成功，{len(text)}字符")
        return text
    except Exception as e:
        print(f"❌ DeepSeek 调用失败: {repr(e)}")
        return f"AI 分析暂时不可用：{e}"


def markdown_to_html(md):
    """轻量 Markdown → HTML 转换（仅处理标题、加粗、列表、换行）"""
    if not md:
        return ""
    # 转义 HTML
    s = md.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    lines = s.split("\n")
    out = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            if in_list:
                out.append("</ul>")
                in_list = False
            level = len(m.group(1))
            out.append(f"<h{min(level + 2, 6)}>{m.group(2)}</h{min(level + 2, 6)}>")
            continue
        # 列表项
        if re.match(r"^[-*]\s+", stripped):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>" + re.sub(r"^[-*]\s+", "", stripped) + "</li>")
            continue
        # 普通行
        if in_list:
            out.append("</ul>")
            in_list = False
        if not stripped:
            out.append("")
        else:
            out.append(f"<p>{stripped}</p>")
    if in_list:
        out.append("</ul>")
    html = "\n".join(out)
    # 加粗
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    return html


# -------------------------- HTML 仪表盘生成 --------------------------
def generate_dashboard_html(all_funds_data, ai_analysis_text, update_time_str):
    """生成完整的自包含仪表盘 HTML"""
    update_time = update_time_str or beijing_now().strftime("%Y-%m-%d %H:%M")
    ai_text_html = markdown_to_html(ai_analysis_text)

    # 构建前端数据 JSON（只传必要的字段）
    chart_payload = {}
    for fund in all_funds_data:
        chart_payload[fund["code"]] = {
            "name": fund["name"],
            "group": fund["group"],
            "data": [{"d": d["date"], "n": d["nav"], "c": d["change"]} for d in fund["data"]],
        }
    json_data_str = json.dumps(chart_payload, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>基金监控</title>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; background:#f5f6fa; color:#333; line-height:1.5; }}
.container {{ max-width:860px; margin:0 auto; padding:12px; }}

/* Header */
.header {{ background:#fff; border-radius:12px; padding:16px; margin-bottom:12px; box-shadow:0 1px 4px rgba(0,0,0,0.06); display:flex; flex-wrap:wrap; align-items:center; gap:8px; }}
.header h1 {{ font-size:20px; margin:0; }}
.header .meta {{ font-size:12px; color:#999; margin-left:auto; }}

/* Section */
.section {{ margin-bottom:16px; }}
.section-title {{ font-size:16px; font-weight:600; margin-bottom:10px; padding-left:4px; }}

/* Cards */
.card-grid {{ display:grid; gap:8px; }}
.card-grid.broad {{ grid-template-columns:repeat(2, 1fr); }}
.card-grid.sector {{ grid-template-columns:repeat(3, 1fr); }}
.card {{ background:#fff; border-radius:10px; padding:12px; box-shadow:0 1px 4px rgba(0,0,0,0.06); }}
.card .name {{ font-size:13px; font-weight:600; color:#555; }}
.card .code {{ font-size:11px; color:#bbb; margin-left:4px; }}
.card .change-big {{ font-size:22px; font-weight:700; margin-top:6px; letter-spacing:-0.5px; }}
.card .changes {{ font-size:13px; display:flex; gap:10px; }}
.up {{ color:#e74c3c; }}
.down {{ color:#27ae60; }}
.flat {{ color:#999; }}

/* Tab bar */
.tab-bar {{ display:flex; gap:0; margin-bottom:10px; }}
.tab {{ flex:1; padding:10px; text-align:center; border:1px solid #e0e0e0; background:#fff; font-size:14px; cursor:pointer; }}
.tab:first-child {{ border-radius:8px 0 0 8px; }}
.tab:last-child {{ border-radius:0 8px 8px 0; }}
.tab.active {{ background:#4361ee; color:#fff; border-color:#4361ee; }}

/* Chart */
.chart-box {{ background:#fff; border-radius:12px; padding:12px; margin-bottom:16px; box-shadow:0 1px 4px rgba(0,0,0,0.06); }}
.chart-box h3 {{ font-size:14px; margin-bottom:8px; }}
.chart {{ width:100%; height:380px; }}

/* 自定义图例 pill */
.legend-pills {{ display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; }}
.legend-pill {{ display:inline-flex; align-items:center; gap:5px; padding:4px 10px; border:1px solid #e0e0e0; border-radius:14px; background:#fff; font-size:12px; color:#555; cursor:pointer; transition:all .15s; }}
.legend-pill .dot {{ width:8px; height:8px; border-radius:50%; background:var(--c); display:inline-block; }}
.legend-pill.off {{ opacity:0.4; }}
.legend-pill.off .dot {{ background:#ccc !important; }}
.legend-pill:active {{ transform:scale(0.96); }}

/* Table */
.table-wrapper {{ overflow-x:auto; background:#fff; border-radius:12px; box-shadow:0 1px 4px rgba(0,0,0,0.06); }}
table {{ width:100%; border-collapse:collapse; font-size:13px; min-width:600px; }}
th, td {{ padding:10px 8px; text-align:center; border-bottom:1px solid #f0f0f0; }}
th {{ background:#fafafa; font-weight:600; color:#666; position:sticky; top:0; }}
tr:last-child td {{ border-bottom:none; }}
td:first-child {{ text-align:left; font-weight:500; }}

/* AI */
.ai-box {{ background:#fff; border-radius:12px; padding:16px; box-shadow:0 1px 4px rgba(0,0,0,0.06); }}
.ai-box h3 {{ font-size:14px; margin-bottom:10px; }}
.ai-box p {{ font-size:13px; color:#555; line-height:1.7; }}

/* Footer */
.footer {{ text-align:center; padding:20px 0 30px; font-size:11px; color:#bbb; }}
.footer a {{ color:#999; text-decoration:none; }}

@media (max-width:480px) {{
  .card-grid.broad {{ grid-template-columns:repeat(2, 1fr); }}
  .card-grid.sector {{ grid-template-columns:repeat(1, 1fr); }}
  .header h1 {{ font-size:17px; }}
  .chart {{ height:260px; }}
  .tab {{ padding:8px 6px; font-size:13px; }}
}}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>📊 基金监控</h1>
    <span class="meta">更新于 {update_time}</span>
  </div>

  <!-- 宽基卡片 -->
  <div class="section">
    <div class="section-title">📈 宽基</div>
    <div class="card-grid broad" id="broadCards"></div>
  </div>

  <!-- 行业板块卡片 -->
  <div class="section">
    <div class="section-title">⚙️ 行业板块</div>
    <div class="card-grid sector" id="sectorCards"></div>
  </div>

  <!-- Tab 切换 -->
  <div class="tab-bar">
    <button class="tab active" data-range="week" onclick="switchRange('week')">近一周</button>
    <button class="tab" data-range="month" onclick="switchRange('month')">近一月</button>
  </div>

  <!-- 宽基走势 -->
  <div class="chart-box">
    <h3>📈 宽基走势对比</h3>
    <div class="legend-pills" id="chartBroadLegend"></div>
    <div class="chart" id="chartBroad"></div>
  </div>

  <!-- 行业走势 -->
  <div class="chart-box">
    <h3>📈 行业板块走势对比</h3>
    <div class="legend-pills" id="chartSectorLegend"></div>
    <div class="chart" id="chartSector"></div>
  </div>

  <!-- 数据表 -->
  <div class="section">
    <div class="section-title">📋 详细数据</div>
    <div class="table-wrapper">
      <table>
        <thead><tr>
          <th>基金</th><th>代码</th><th>最新净值</th><th>日涨跌</th><th>周涨跌</th><th>月涨跌</th>
        </tr></thead>
        <tbody id="dataTableBody"></tbody>
      </table>
    </div>
  </div>

  <!-- AI 分析 -->
  <div class="section">
    <div class="section-title">🤖 AI 涨跌分析</div>
    <div class="ai-box">
      <p>{ai_text_html}</p>
    </div>
  </div>

  <div class="footer">
    <p>数据来源：天天基金网 · 每日自动更新</p>
    <p>仅供个人参考，不构成投资建议</p>
    <p><a href="#">GitHub</a></p>
  </div>
</div>

<script>
// ===== 嵌入数据 =====
const FUND_DATA = {json_data_str};
const GROUP_ORDER = ["宽基", "行业板块"];
const RANGE_DAYS = {{ week: 7, month: 30 }};
let currentRange = "week";

// ===== 工具函数 =====
function cls(v) {{ return v > 0 ? "up" : v < 0 ? "down" : "flat"; }}
function fmt(v) {{ let s = v.toFixed(2); return (v > 0 ? "+" : "") + s + "%"; }}

// ===== 渲染卡片 =====
function renderCards() {{
  let broadHtml = "", sectorHtml = "";
  for (const [code, f] of Object.entries(FUND_DATA)) {{
    const latest = f.data[0];
    if (!latest) continue;
    const card = '<div class="card">' +
      '<div class="name">' + f.name + '<span class="code">' + code + '</span></div>' +
      '<div class="change-big ' + cls(latest.c) + '">' + fmt(latest.c) + '</div>' +
    '</div>';
    if (f.group === "宽基") broadHtml += card; else sectorHtml += card;
  }}
  document.getElementById("broadCards").innerHTML = broadHtml;
  document.getElementById("sectorCards").innerHTML = sectorHtml;
}}

// ===== 渲染表格 =====
function renderTable() {{
  let html = "";
  for (const group of GROUP_ORDER) {{
    for (const [code, f] of Object.entries(FUND_DATA)) {{
      if (f.group !== group) continue;
      const latest = f.data[0];
      if (!latest) continue;
      const weekChange = calcLatestChange(f.data, 7);
      const monthChange = calcLatestChange(f.data, 30);
      html += '<tr>' +
        '<td>' + f.name + '</td><td>' + code + '</td>' +
        '<td>' + latest.n.toFixed(4) + '</td>' +
        '<td class="' + cls(latest.c) + '">' + fmt(latest.c) + '</td>' +
        '<td class="' + cls(weekChange) + '">' + (weekChange !== null ? fmt(weekChange) : "-") + '</td>' +
        '<td class="' + cls(monthChange) + '">' + (monthChange !== null ? fmt(monthChange) : "-") + '</td>' +
      '</tr>';
    }}
  }}
  document.getElementById("dataTableBody").innerHTML = html;
}}

function calcLatestChange(data, days) {{
  if (data.length < 2) return null;
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  const recent = data.filter(d => new Date(d.d) >= cutoff);
  if (recent.length < 2) return null;
  const first = recent[recent.length - 1].n;
  const last = recent[0].n;
  return (last - first) / first * 100;
}}

// ===== 图表 =====
let chartBroad, chartSector;

function getFilteredData(data, range) {{
  const days = RANGE_DAYS[range];
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  return data.filter(d => new Date(d.d) >= cutoff);
}}

function buildChartOption(group, range) {{
  // 7 色调色板：色相分离、明度均衡
  const palette = ["#3b82f6", "#ef4444", "#f59e0b", "#a855f7", "#10b981", "#0ea5e9", "#ec4899"];
  const fundsInGroup = Object.values(FUND_DATA).filter(f => f.group === group);

  // 收集该组所有基金按日期对齐的数据
  const allDates = new Set();
  const fundData = [];
  fundsInGroup.forEach((f, idx) => {{
    const filtered = getFilteredData(f.data, range);
    if (filtered.length < 2) return;
    filtered.forEach(d => allDates.add(d.d));
    fundData.push({{ name: f.name, data: filtered, color: palette[idx % palette.length] }});
  }});

  const sortedDates = Array.from(allDates).sort();
  const series = fundData.map(fd => {{
    const valueMap = {{}};
    fd.data.forEach(d => valueMap[d.d] = d.n);
    let baseNav = null;
    for (const d of sortedDates) {{
      if (valueMap[d] !== undefined) {{ baseNav = valueMap[d]; break; }}
    }}
    return {{
      name: fd.name, type: "line",
      data: sortedDates.map(d => {{
        if (valueMap[d] === undefined) return null;
        return baseNav ? ((valueMap[d] - baseNav) / baseNav * 100) : 0;
      }}),
      smooth: true, symbol: "none", lineStyle: {{ width: 2.5 }},
      color: fd.color,
      connectNulls: false,
    }};
  }});

  const formatterPct = (v) => {{
    if (v === null || v === undefined) return "-";
    const s = v.toFixed(2);
    return (v > 0 ? "+" : "") + s + "%";
  }};

  // X 轴日期：转成 MM-DD 格式，自动间隔避免全显示
  const xAxisData = sortedDates.map(d => d.slice(5));

  return {{
    tooltip: {{ trigger: "axis", valueFormatter: formatterPct, axisPointer: {{ type: "cross" }} }},
    legend: {{ show: false }},
    grid: {{ left: 48, right: 16, top: 16, bottom: 56 }},
    xAxis: {{
      type: "category", data: xAxisData,
      axisLabel: {{ fontSize: 10, rotate: 0, interval: Math.max(0, Math.floor(xAxisData.length / 8) - 1), hideOverlap: true }},
    }},
    yAxis: {{ type: "value", scale: true, axisLabel: {{ formatter: (v) => v.toFixed(0) + "%" }} }},
    series: series,
  }};
}}

// ===== 渲染自定义图例（pill 按钮组，可点击切换显隐） =====
function renderLegend(chartId, group) {{
  const palette = ["#3b82f6", "#ef4444", "#f59e0b", "#a855f7", "#10b981", "#0ea5e9", "#ec4899"];
  const funds = Object.values(FUND_DATA).filter(f => f.group === group);
  const container = document.getElementById(chartId + "Legend");
  if (!container) return;
  container.innerHTML = funds.map((f, idx) => {{
    const color = palette[idx % palette.length];
    return '<button class="legend-pill" data-color="' + color + '" data-name="' + f.name + '" style="--c:' + color + '">' +
      '<span class="dot"></span>' + f.name + '</button>';
  }}).join("");

  container.querySelectorAll(".legend-pill").forEach(btn => {{
    btn.addEventListener("click", () => {{
      btn.classList.toggle("off");
      const chart = chartId === "chartBroad" ? chartBroad : chartSector;
      const name = btn.dataset.name;
      const series = chart.getOption().series;
      const idx = series.findIndex(s => s.name === name);
      if (idx >= 0) {{
        const isOff = btn.classList.contains("off");
        // 通过修改 lineStyle.opacity 隐藏
        chart.setOption({{
          series: series.map((s, i) => i === idx ? {{
            ...s,
            lineStyle: {{ ...s.lineStyle, opacity: isOff ? 0.15 : 1, width: isOff ? 1 : 2.5 }},
            itemStyle: {{ ...s.itemStyle, opacity: isOff ? 0.15 : 1 }},
          }} : s),
        }});
      }}
    }});
  }});
}}

function renderCharts(range) {{
  if (!chartBroad) chartBroad = echarts.init(document.getElementById("chartBroad"));
  if (!chartSector) chartSector = echarts.init(document.getElementById("chartSector"));
  chartBroad.setOption(buildChartOption("宽基", range), true);
  chartSector.setOption(buildChartOption("行业板块", range), true);
  renderLegend("chartBroad", "宽基");
  renderLegend("chartSector", "行业板块");
}}

// ===== Tab 切换 =====
function switchRange(range) {{
  currentRange = range;
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.range === range));
  renderCharts(range);
}}

// ===== 启动 =====
renderCards();
renderTable();
renderCharts("week");
window.addEventListener("resize", () => {{ chartBroad && chartBroad.resize(); chartSector && chartSector.resize(); }});
</script>
</body>
</html>"""


# -------------------------- 主流程 --------------------------
if __name__ == "__main__":
    print(f"🔍 开始执行基金监控任务 - {beijing_now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 拉取所有基金数据
    all_funds_data = []
    fetch_ok = True
    for fund in ALL_FUNDS:
        data = get_fund_data_from_eastmoney(fund["code"])
        if data:
            all_funds_data.append({**fund, "data": data})
        else:
            fetch_ok = False

    if not all_funds_data:
        print("❌ 所有基金数据获取失败，终止")
        sys.exit(1)

    print(f"📊 成功获取 {len(all_funds_data)}/{len(ALL_FUNDS)} 只基金数据")

    # 2. 调用 DeepSeek AI 分析
    ai_text = call_deepseek_analysis(all_funds_data)

    # 3. 生成 HTML 仪表盘
    update_time = beijing_now().strftime("%Y-%m-%d %H:%M")
    html = generate_dashboard_html(all_funds_data, ai_text, update_time)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTML 仪表盘已生成: {output_path} ({len(html)} 字节)")

    print(f"✅ 基金监控任务完成 - {beijing_now().strftime('%Y-%m-%d %H:%M:%S')}")
