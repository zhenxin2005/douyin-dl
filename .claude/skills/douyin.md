---
name: douyin
description: 下载抖音（www.douyin.com）无水印视频到本地。用法：/douyin <链接>
---

# 抖音视频下载

## 用法

```
/douyin <抖音视频链接>
```

支持以下链接格式：
- `https://www.douyin.com/video/xxxxxxxxxxxxx`
- `https://v.douyin.com/xxxxxxxx/`
- `https://www.iesdouyin.com/share/video/xxx`
- 以及抖音分享短链

## 执行流程

1. **执行下载** — 调用下载脚本:
   ```bash
   python3 /mnt/workspace/KSHIN/scripts/douyin-dl.py "<用户提供的链接>"
   ```

2. **报告结果** — 告知用户:
   - 视频标题、作者、时长、分辨率
   - 文件保存路径和大小
   - 如有问题，说明原因和解决建议
