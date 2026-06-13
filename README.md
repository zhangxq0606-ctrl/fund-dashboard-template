# 基金监控仪表盘

每日自动抓取基金净值数据，生成可视化仪表盘，通过 GitHub Pages 免费部署。

你看到的是一个**功能完整、可直接运行的监控页面**，包含：
- **涨跌卡片概览** — 每只基金当日表现一目了然
- **净值走势图** — ECharts 折线图，支持近一周/近一月切换
- **AI 涨跌分析** — DeepSeek 驱动，深度解读板块联动


---

## 💡 重要提示：用 AI 帮你改代码

**把基金换成你自己的、调整更新时间等所有代码改动，强烈建议交给 AI 去做。**

用 Traecn，把下面的内容复制给 AI，它 10 秒就能帮你改好：

> 帮我改一个 Python 项目中的代码。文件是 `main.py`，里面有 `FUND_GROUPS` 这个字典，格式是 `("基金名称", "基金代码")`。我想把基金换成以下这些：[这里写你的基金名称和代码]。另外 `.github/workflows/deploy.yml` 文件里有一个 cron 表达式，帮我改成我需要的北京时间（注意 cron 用的是 UTC 时间）。

**最省事的做法**：打开 Trae / Cursor / VS Code，把 `main.py` 和 `deploy.yml` 拖进去，告诉 AI 你想换成哪些基金——它直接帮你改好，你保存就行。**不需要懂代码**。

---

## 前置准备

| 需要什么 | 怎么获取 | 耗时 |
|---------|---------|------|
| **GitHub 账号** | 去 [github.com](https://github.com) 注册 | 3 分钟 |
| **DeepSeek API Key** | 去 [platform.deepseek.com](https://platform.deepseek.com) 注册 → 左侧 API Keys → 创建 Key | 5 分钟 |

---

## 4 步部署（超详细版）

> 以下每一步都写明了在页面上**点哪里、按钮叫什么名字**。跟着走就行。

### 第 1 步：创建你的仓库

1. 用浏览器打开本项目的 GitHub 页面
2. 点击页面上方右侧的绿色按钮 **「Use this template」**（在「Code」绿色按钮旁边）
3. 在弹出的窗口中：
   - **Repository name** 一栏输入仓库名称（随便写，比如 `fund-dashboard`）
   - 确保选择 **Public**（公开）
   - 点击页面底部的绿色按钮 **「Create repository from template」**
4. 等待几秒，浏览器会跳转到你自己的新仓库页面

### 第 2 步：配置 DeepSeek Key（密钥）

1. 在你自己的仓库页面中，点击顶部的 **「Settings」** 标签（最右边）
2. 在左侧菜单往下翻，找到 **「Secrets and variables」** 点击展开
3. 点击 **「Actions」**
4. 点击页面右侧的 **「New repository secret」** 按钮
5. 在弹出的窗口中：
   - **Name** 输入：`DEEPSEEK_API_KEY`
   - **Secret** 输入：你在 DeepSeek 官网复制的 API Key（以 `sk-` 开头的一串字符）
   - 点击绿色 **「Add secret」** 按钮
6. 页面上会显示一行 `DEEPSEEK_API_KEY`，说明配置成功

### 第 3 步：修改基金列表

> **不会改？看上面 💡 提示，把文件扔给 AI 帮你改。**

打开 `main.py` 文件：
1. 在你的仓库页面中，点击 `main.py` 这个文件名
2. 点击文件预览区域右上角的 ✏️ **编辑图标**（铅笔图标）
3. 滚动到文件中段，找到以下内容：

```python
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
```

改成你自己的基金，格式是 `("基金名称", "基金代码")`。**基金代码去哪里找？** → 打开天天基金网（fund.eastmoney.com），搜索基金名称，地址栏或页面上能看到 6 位数字代码。

改完后，点击页面底部的绿色按钮 **「Commit changes...」**，在弹出的窗口中直接点 **「Commit changes」**。

### 第 4 步：启用 GitHub Pages 并触发运行

1. 回到仓库页面，点击顶部 **「Settings」**
2. 在左侧菜单中找到 **「Pages」**（在「Security」下面）
3. 在 **「Source」** 一栏，点击下拉菜单，选择 **「GitHub Actions」**
4. 这时候页面已经设置好了。去触发第一次运行：
5. 点击顶部 **「Actions」** 标签
6. 在左侧列表中找到 **「基金仪表盘部署」** 并点击
7. 在中间区域找到 **「Run workflow」** 下拉按钮（在「This workflow has a workflow_dispatch event trigger」这行文字的右侧）
8. 点击 **「Run workflow」** → 再次点击弹出的 **「Run workflow」**
9. 页面会多出一条黄色圆点的运行记录，等待它变成 ✅ 绿色勾（约 2 分钟）

### 第 5 步：找到你的网站地址

1. 回到 **Settings** → **Pages**
2. 页面顶部会显示一行提示，类似：
   ```
   Your site is live at https://你的用户名.github.io/仓库名/
   ```
3. 点击这个链接，打开就是你自己的基金监控页面

**之后每天早上 05:00（北京时间）会自动更新**，你每天打开这个链接就能看到最新数据。

---

## 常见疑问

### 网站链接会不会失效？

不会。只要你不删仓库，GitHub Pages 永久免费，永远不会过期。

### 怎么改更新时间？

打开 `.github/workflows/deploy.yml`，找到 `- cron: '0 21 * * *'`，把 `21` 改成你想要的 UTC 小时。

**北京时间 → UTC 换算**：北京时间减 8，不够则加 24 并减一天。例如北京时间 07:00 = UTC 23:00（前一天）。

**让 AI 帮你算**：直接告诉 AI「我想每天北京时间 X 点更新」，它会把正确的 cron 值给你。

### 怎么添加更多基金？

在 `main.py` 的 `FUND_GROUPS` 对应列表里加一行 `("基金名称", "基金代码"),` 即可。同一个板块多只基金就多加几行。

### 推送微信提醒？

本版本已移除微信推送功能。如有需要，在 `main.py` 中配置 `PUSHPLUS_TOKEN` 并接入 PushPlus 服务。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 数据采集 | Python（requests） |
| AI 分析 | DeepSeek API |
| 图表 | ECharts 5 |
| 前端 | 纯 HTML + CSS + JS，无框架 |
| 部署 | GitHub Actions → GitHub Pages |
| 定时 | GitHub Actions Cron |

## 注意事项

- 数据来源：天天基金网
- 仅供个人参考，不构成投资建议
- 如有问题，在仓库提 Issue 即可
