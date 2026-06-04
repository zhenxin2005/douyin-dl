# douyin-dl

抖音无水印视频下载工具。一个不到 200 行的 Python 脚本，无需 cookie、无需登录、无需浏览器。

## 功能

- 支持抖音短链 (`v.douyin.com`)、长链 (`www.douyin.com/video/xxx`)、分享链接
- 无水印 MP4 下载
- 零外部依赖（仅需 Python 内置的 `requests` 库）
- 跨平台：Linux / macOS / Windows
- 支持打包为独立 `.exe`，无需安装 Python 也能用

---

## 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 下载视频

```bash
python douyin-dl.py "https://v.douyin.com/xxxx/"
```

示例：

```bash
python douyin-dl.py "https://v.douyin.com/MntwLAeBQBo/"

# 输出：
# 🔍 解析抖音链接: https://v.douyin.com/MntwLAeBQBo/
# 📁 输出目录: ./downloads
#
# 📡 获取页面数据...
# 🔎 解析视频信息...
#   📹 标题: 千川全域投放分享一起号
#   👤 作者: 千川全域威哥
#   ⏱️  时长: 14:15
#   📐 分辨率: 1438x1080
#
# ⬇️  下载视频中...
#
# ✅ 下载完成！
#   📁 文件: ./downloads/千川全域投放分享一起号.mp4
#   📦 大小: 29.1 MB
#   🎬 无水印 MP4
```

视频默认下载到 `downloads/` 目录。

### 3. 指定输出目录

```bash
python douyin-dl.py "https://v.douyin.com/xxxx/" ./my_videos
```

---

## 三种使用方式

### 方式一：在 Claude Code 中作为 Skill 使用（推荐）

在 Claude Code 对话中直接输入：

```
/douyin "https://v.douyin.com/xxxx/"
```

**首次使用需配置：**

1. 将 `douyin.md` 复制到项目的 `.claude/skills/` 目录
2. 将 `douyin-dl.py` 复制到项目的 `scripts/` 目录
3. 确保 `douyin.md` 中的脚本路径与实际路径一致

**文件结构：**

```
你的项目/
├── .claude/
│   └── skills/
│       └── douyin.md          # Skill 配置文件
└── scripts/
    ├── douyin-dl.py            # 主程序
    ├── douyin-dl.sh            # Bash 包装器（可选）
    └── requirements.txt        # Python 依赖
```

### 方式二：命令行独立运行

不依赖 Claude Code，直接在终端使用：

```bash
# Linux / macOS
python3 douyin-dl.py "抖音链接"

# 指定输出目录
python3 douyin-dl.py "抖音链接" ~/Videos/
```

### 方式三：Windows 11 下运行

**第一步：安装 Python**

1. 打开 [python.org](https://www.python.org/downloads/)
2. 下载最新版 Python 安装包
3. **重要：安装时勾选「Add Python to PATH」**
4. 完成后打开 PowerShell 或 CMD，验证安装：

```powershell
python --version
# 应显示: Python 3.x.x
```

**第二步：安装依赖**

```powershell
pip install requests
```

**第三步：下载脚本**

将本项目中的 `douyin-dl.py` 下载到你的电脑，例如存放到 `C:\tools\douyin-dl.py`。

**第四步：运行**

```powershell
python C:\tools\douyin-dl.py "https://v.douyin.com/xxxx/"
```

视频会下载到 `C:\tools\downloads\` 目录。

**进阶①：使用批处理文件（双击运行）**

项目中已包含 `下载抖音.bat`，双击即可运行：

1. 将整个 `scripts/` 文件夹复制到 `C:\tools\` 下
2. 双击 `下载抖音.bat`
3. 粘贴抖音链接，回车下载

**进阶②：打包成独立 .exe（无需安装 Python）**

如果想分享给完全不懂技术的朋友，可以打包成一个 `.exe` 文件：

1. 在 Windows 上安装 Python（一次性）
2. 双击 `打包成exe.bat`
3. 在 `dist/` 目录下得到 `douyin-dl.exe`
4. 把这个 `.exe` 复制到任何 Windows 电脑，双击即用，**Python 都不需要装**

---

## 原理

```
抖音短链（v.douyin.com）
      │
      ▼
  跟随重定向，获取页面 HTML
      │
      ▼
  解析 window._ROUTER_DATA（JSON）
      │
      ▼
  提取 play_addr.url_list[0]
      │
      ▼
  playwm → play（去掉水印）
      │
      ▼
  携带 Referer 请求，下载 MP4
```

无须 cookie、无须 Selenium/Playwright、无须登录，纯 HTTP 请求即可。

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `scripts/douyin-dl.py` | 主程序，核心下载逻辑 |
| `scripts/douyin-dl.sh` | Bash 包装器，方便 Linux 用户 |
| `scripts/requirements.txt` | Python 依赖（仅有 `requests`） |
| `.claude/skills/douyin.md` | Claude Code Skill 配置文件 |

---

## 常见问题

**Q: 提示"无法解析页面数据"？**

A: 抖音页面结构可能发生了变化，请提交 Issue 告知。

**Q: 下载速度慢？**

A: 与你的网络到抖音 CDN 的连接速度有关，建议使用国内网络环境。

**Q: 需要登录吗？**

A: 不需要。本工具不依赖 cookie 或登录状态，完全匿名下载公开视频。

**Q: 支持其他平台吗？**

A: 当前只支持抖音（douyin.com）。如需支持 TikTok、B站 等，可提 Issue。

---

## License

MIT
