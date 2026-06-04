# douyin-dl

抖音无水印视频下载工具。纯 Python 脚本，无需 cookie、无需登录、无需浏览器。

## 功能

- 单个 / 批量下载抖音视频
- 支持从文本文件导入链接列表
- **智能提取**：直接粘贴抖音口令文本，自动识别其中的链接
- 无水印 MP4
- 零外部依赖（仅需 `requests`）
- 跨平台：Linux / macOS / Windows
- 可打包为独立 `.exe`，无需装 Python

---

## 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 下载视频

```bash
# 单个
python douyin-dl.py "https://v.douyin.com/xxxx/"

# 批量（多个链接）
python douyin-dl.py "链接1" "链接2" "链接3"

# 从文件读取（一行一个链接）
python douyin-dl.py urls.txt

# 混合输入
python douyin-dl.py urls.txt "额外链接"
```

### 3. 直接粘贴抖音口令

不需要手动提取链接，直接把抖音复制的内容贴进去就行：

```bash
python douyin-dl.py "2.89 03/09 A@g.oq :7pm NJV:/ # 气质优雅 https://v.douyin.com/xxxx/ 复制此链接..."
```

脚本会自动识别并提取其中的 `https://v.douyin.com/...` 链接。

### 4. 指定输出目录

```bash
python douyin-dl.py "链接" /path/to/output
```

视频默认下载到 `downloads/` 目录。

---

## 示例输出

```bash
python douyin-dl.py "链接1" "链接2" "链接3"

============================================================
📋 共 3 个视频待下载
📁 输出目录: ./downloads

[1/3] 📡 获取: https://v.douyin.com/xxxx/...
[1/3] 🔎 解析...
[1/3] 📹 视频标题
[1/3] 👤 作者 | ⏱️ 02:18 | 📐 1080x1920
[1/3] ⬇️  下载中...
[1/3] ✅ 完成！18.7 MB → downloads/视频标题.mp4

[2/3] ✅ 完成！1.8 MB → downloads/另一个视频.mp4
[3/3] ✅ 完成！2.6 MB → downloads/第三个视频.mp4

============================================================
📊 下载汇总: 成功 3 / 失败 0 / 总计 3
```

---

## urls.txt 格式

```txt
# 一行一个链接，# 开头为注释

https://v.douyin.com/xxxx/
https://v.douyin.com/yyyy/
https://www.douyin.com/video/zzzz
```

---

## 三种使用方式

### 方式一：在 Claude Code 中作为 Skill 使用

在对话中直接粘贴抖音口令即可，或使用命令：

```
/douyin "https://v.douyin.com/xxxx/"
```

**首次配置：**

1. 将 `douyin.md` 复制到项目的 `.claude/skills/` 目录
2. 将 `douyin-dl.py` 复制到 `scripts/` 目录
3. 确保 `douyin.md` 中的脚本路径与实际一致

### 方式二：命令行独立运行

不依赖 Claude Code，直接在任何终端使用。

### 方式三：Windows 11

**第一步：安装 Python**

[python.org](https://www.python.org/downloads/) 下载安装包，**勾选「Add Python to PATH」**。

```powershell
python --version   # 验证安装
```

**第二步：安装依赖**

```powershell
pip install requests
```

**第三步：运行**

```powershell
python douyin-dl.py "抖音口令或链接"
```

**进阶①：双击运行**

将 `scripts/` 文件夹复制到 `C:\tools\`，双击 `下载抖音.bat`：
- 选择 ① 单视频 / ② urls.txt 文件 / ③ 粘贴多链接

**进阶②：打包成 .exe（免装 Python）**

1. 在 Windows 上装好 Python（一次性）
2. 双击 `打包成exe.bat`
3. 在 `dist/` 目录得到 `douyin-dl.exe`
4. 复制到任何 Windows 电脑，双击即用，**Python 都不需要**

---

## 原理

```
抖音口令 / 短链
      │
      ▼
  提取纯 URL → 跟随重定向 → 获取 HTML
      │
      ▼
  解析 window._ROUTER_DATA（JSON）
      │
      ▼
  提取 play_addr.url_list[0]
      │
      ▼
  playwm → play（去水印）
      │
      ▼
  带 Referer 下载 MP4
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `scripts/douyin-dl.py` | 主程序 |
| `scripts/douyin-dl.sh` | Bash 包装器 |
| `scripts/下载抖音.bat` | Windows 批处理（双击运行） |
| `scripts/打包成exe.bat` | Windows 打包脚本 |
| `scripts/urls.txt` | 批量下载链接示例 |
| `scripts/requirements.txt` | Python 依赖 |
| `.claude/skills/douyin.md` | Claude Code Skill 配置 |

---

## 常见问题

**Q: 可以直接粘贴抖音口令吗？**

A: 可以。直接粘贴从抖音复制的整段文本，脚本会自动提取链接。

**Q: 需要登录吗？**

A: 不需要。

**Q: 支持其他平台吗？**

A: 当前只支持抖音。如需 TikTok、B站 等，可提 Issue。

---

## License

MIT
