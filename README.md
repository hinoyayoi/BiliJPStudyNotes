# BiliJPStudyNotes

Bilibili の日本語動画から、字幕・翻訳・重要文・語彙リストを自動生成する学習用パイプラインです。  
这是一个面向日语学习的 Bilibili 视频处理工具：自动生成日文字幕、中文翻译、重点句和词汇汇总。

Keywords: Bilibili, Whisper, Japanese subtitle, 日本語 字幕, 精听, JLPT, Anki, 学习笔记

## Features | 主要功能
- Download audio from a Bilibili video URL (supports browser login cookies).  
  从 B 站链接下载音频（支持浏览器登录态）。
- Generate Japanese subtitles with timestamps using Whisper (`faster-whisper`).  
  使用 Whisper 生成带时间戳的日文字幕。
- Split subtitles into sentence-level items.  
  按句切分字幕。
- Generate Chinese translation for each sentence.  
  为每句生成中文翻译。
- Extract keywords (nouns/verbs) from each sentence.  
  提取每句关键词（名词/动词）。
- Filter low-information sentences and produce focus-list.  
  过滤低信息密度句子并生成精听重点句。
- Output Markdown report.  
  输出 Markdown 学习文档。

## Project Structure | 项目结构
- `scripts/bilibili_jp_study_pipeline.py`  
  Main pipeline script.  
  主处理脚本。
- `run.ps1`  
  Convenience runner for Windows PowerShell.  
  Windows 一键运行脚本。
- `requirements.txt`  
  Python dependencies.  
  Python 依赖。
- `outputs/`  
  Generated artifacts.  
  生成结果目录。

## Quick Start | 快速开始
### 1) Setup | 环境准备
```powershell
cd "C:\Users\hinoy\Documents\BiliJPStudyNotes"
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 2) Run | 运行
```powershell
.\run.ps1 -Url "https://www.bilibili.com/video/BV1JgwZzUEC2/" -Model base -UseBrowserCookies
```

or / 或者：
```powershell
.\.venv\Scripts\python.exe .\scripts\bilibili_jp_study_pipeline.py "https://www.bilibili.com/video/BV1JgwZzUEC2/" --output-dir .\\outputs\\BV1JgwZzUEC2 --model base --use-browser-cookies
```

## Output | 输出文件
- `outputs/<BV号>/bilibili_jp_study.md`  
  Timeline Japanese subtitle + Chinese translation + keywords + focus sentences + vocabulary summary.  
  含时间轴字幕、中文翻译、生词、重点句和词汇汇总。
- `outputs/<BV号>/raw_segments.json`  
  Raw sentence-level subtitle data.  
  原始句级字幕数据。
- `outputs/<BV号>/source.m4a`  
  Downloaded audio source.  
  下载音频源文件。

## Notes | 说明
- Long videos may take significant time (transcription + per-line translation).  
  长视频处理时间较长（转写 + 逐句翻译）。
- If video access is restricted, use browser cookies (`--use-browser-cookies`).  
  若视频受限，建议启用浏览器登录态。
- This project does not store account credentials; it only reads local browser cookies when enabled.  
  本项目不保存账号密码，仅在启用参数时读取本机浏览器 Cookie。

## GitHub Upload | 上传到 GitHub
```powershell
cd "C:\Users\hinoy\Documents\BiliJPStudyNotes"
git init
git add .
git commit -m "Initialize BiliJPStudyNotes"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

