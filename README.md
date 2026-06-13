# 基金监控仪表盘

每日自动抓取基金净值数据，生成可视化仪表盘，通过 GitHub Pages 免费部署。

你看到的是一个**功能完整、可直接运行的监控页面**，包含：
- **涨跌卡片概览** — 每只基金当日表现一目了然
- **净值走势图** — ECharts 折线图，支持近一周/近一月切换
- **AI 涨跌分析** — DeepSeek 驱动，深度解读板块联动


---

## 🙋 这个 README 是写给谁看的？

**写给 AI 看的**。你只需要打开 Trae / ChatGPT / Claude / DeepSeek Chat 等任意 AI 编辑器，把本文件拖进去，告诉它：

<<<<<<< HEAD
用 Traecn，把下面的内容复制给 AI，它 10 秒就能帮你改好：
=======
> 帮我把基金换成我自己的：XXXXXX（基金名称 + 代码）
>>>>>>> 8c8edbf (docs: rewrite README for AI-first + human ops)

AI 读完 README 会自己知道怎么操作。**你不需要逐字阅读**。

---

## 💡 给 AI 的执行指令

如果你是 AI 助手，正在帮用户配置这个基金监控项目，请按以下步骤操作：

### 第 1 步：用 `FUND_GROUPS` 字典定义基金

**不要动其他代码，只改 `FUND_GROUPS` 这一个地方**。

```python
FUND_GROUPS = {
    "宽基": [
        ("基金名称", "基金代码"),
        ("基金名称", "基金代码"),
    ],
    "行业板块": [
        ("基金名称", "基金代码"),
    ],
}
```

用户可以自己分组，比如「宽基」「行业板块」「海外」「债券」等，组名任意。

### 第 2 步：用户操作

帮用户改完 `FUND_GROUPS` 后，通知用户按下方的人肉操作步骤完成 GitHub 部署即可。

---

## 📋 人肉操作步骤

> 以下每一步都写明了在页面上**点哪里、按钮叫什么名字**。跟着走就行。

### 前置准备

| 需要什么 | 怎么获取 | 耗时 |
|---------|---------|------|
| **GitHub 账号** | 去 [github.com](https://github.com) 注册 | 3 分钟 |
| **DeepSeek API Key** | 去 [platform.deepseek.com](https://platform.deepseek.com) 注册 → 左侧 API Keys → 创建 Key | 5 分钟 |

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

> **最简单的方法**：打开 Trae / ChatGPT / Claude 等 AI 编辑器，把 `main.py` 拖进去，说一句「帮我把基金换成我自己的」，AI 会直接帮你改好。**你不需要自己动手改代码**。

如果你没有 AI 编辑器，也可以手动改：
1. 在仓库页面中，点击 `main.py` 这个文件名
2. 点击文件预览区域右上角的 ✏️ **编辑图标**（铅笔图标）
3. 找到 `FUND_GROUPS` 这一段，把示例基金换成你自己的
4. 点击页面底部的绿色按钮 **「Commit changes...」** → 再点 **「Commit changes」**

> 💡 **基金代码去哪里找？** 打开天天基金网（fund.eastmoney.com），搜索基金名称，地址栏或页面上就能看到 6 位数字代码。

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

## ❓ 常见疑问

### 网站链接会不会失效？

不会。只要你不删仓库，GitHub Pages 永久免费，永远不会过期。

### 怎么添加更多基金？

用 AI 编辑器打开 `main.py`，告诉 AI「帮我加几只基金」，它 10 秒改好。

### 想自定义更新时间？

告诉 AI「我想每天北京时间 XX 点更新」，它会帮你改好。当前默认 05:00，一般不需要改。

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
