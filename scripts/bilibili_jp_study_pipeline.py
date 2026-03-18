import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Dict

import yt_dlp
from deep_translator import GoogleTranslator
from faster_whisper import WhisperModel
import fugashi


@dataclass
class SentenceItem:
    start: float
    end: float
    ja: str
    zh: str
    keywords: List[str]
    is_focus: bool


LOW_INFO_PATTERNS = [
    r"^(はい|ええ|うん|あの|えっと|えーと|なるほど|そうですね)[。！!？?…]*$",
    r"^(じゃあ|では|それでは|さて)[、。！!？?…]*$",
    r"^(よろしくお願いします|ありがとうございます|お疲れ様です)[。！!？?…]*$",
]
LOW_INFO_REGEX = [re.compile(p) for p in LOW_INFO_PATTERNS]

PUNCT_SPLIT = re.compile(r"(?<=[。！？!?])")


def ts(t: float) -> str:
    ms = int(round(t * 1000))
    h = ms // 3600000
    ms %= 3600000
    m = ms // 60000
    ms %= 60000
    s = ms // 1000
    return f"{h:02d}:{m:02d}:{s:02d}"


def clean_text(s: str) -> str:
    s = s.replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def download_audio(url: str, out_dir: Path, use_browser_cookies: bool) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(out_dir / "source.%(ext)s")

    base_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "noplaylist": True,
        "quiet": False,
        "restrictfilenames": True,
    }

    attempts = []
    if use_browser_cookies:
        opts = dict(base_opts)
        opts["cookiesfrombrowser"] = ("chrome",)
        attempts.append(opts)
    attempts.append(base_opts)

    last_err = None
    for opts in attempts:
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                requested = info.get("requested_downloads") or []
                if requested and requested[0].get("filepath"):
                    return Path(requested[0]["filepath"]) 
                path = Path(ydl.prepare_filename(info))
                if path.exists():
                    return path
                candidates = sorted(out_dir.glob("source.*"), key=lambda p: p.stat().st_mtime, reverse=True)
                if candidates:
                    return candidates[0]
                raise FileNotFoundError("Audio downloaded but file not found")
        except Exception as e:  # noqa: BLE001
            last_err = e
            continue

    raise RuntimeError(f"Download failed: {last_err}")


def transcribe(audio_path: Path, model_size: str) -> List[Tuple[float, float, str]]:
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(str(audio_path), language="ja", vad_filter=True)

    results = []
    for seg in segments:
        txt = clean_text(seg.text)
        if not txt:
            continue
        results.append((float(seg.start), float(seg.end), txt))
    return results


def split_segments(segments: List[Tuple[float, float, str]]) -> List[Tuple[float, float, str]]:
    out = []
    for start, end, text in segments:
        parts = [p.strip() for p in PUNCT_SPLIT.split(text) if p.strip()]
        if len(parts) <= 1:
            out.append((start, end, text))
            continue

        dur = max(end - start, 0.01)
        total_chars = sum(len(p) for p in parts)
        cur = start
        for i, p in enumerate(parts):
            ratio = len(p) / total_chars if total_chars else 1 / len(parts)
            piece = dur * ratio
            p_start = cur
            p_end = end if i == len(parts) - 1 else cur + piece
            out.append((p_start, p_end, p))
            cur = p_end
    return out


def translate_lines(lines: List[str]) -> List[str]:
    translator = GoogleTranslator(source="ja", target="zh-CN")
    translated = []
    for line in lines:
        try:
            translated.append(translator.translate(line) or "")
        except Exception:
            translated.append("[翻译失败]")
    return translated


def extract_keywords(sentence: str, tagger: fugashi.Tagger) -> List[str]:
    words = []
    for tok in tagger(sentence):
        pos1 = tok.feature.pos1
        lemma = tok.feature.lemma if hasattr(tok.feature, "lemma") else str(tok)
        base = lemma if lemma and lemma != "*" else str(tok)
        if pos1 in {"名詞", "動詞"} and len(base) > 1:
            words.append(base)
    # de-dup keep order
    seen = set()
    result = []
    for w in words:
        if w not in seen:
            seen.add(w)
            result.append(w)
    return result


def is_low_info(sentence: str, keywords: List[str]) -> bool:
    s = sentence.strip()
    if any(r.match(s) for r in LOW_INFO_REGEX):
        return True
    # very short with little lexical info
    if len(s) <= 8 and len(keywords) == 0:
        return True
    if len(keywords) == 0 and re.fullmatch(r"[ぁ-んァ-ンー。、！？!?,，\s]+", s):
        return True
    return False


def build_items(split_lines: List[Tuple[float, float, str]]) -> List[SentenceItem]:
    ja_lines = [x[2] for x in split_lines]
    zh_lines = translate_lines(ja_lines)
    tagger = fugashi.Tagger()

    items = []
    for (start, end, ja), zh in zip(split_lines, zh_lines):
        kws = extract_keywords(ja, tagger)
        low = is_low_info(ja, kws)
        items.append(SentenceItem(start, end, ja, zh, kws, not low))
    return items


def render_markdown(items: List[SentenceItem]) -> str:
    vocab_counter: Dict[str, int] = {}
    for it in items:
        for k in it.keywords:
            vocab_counter[k] = vocab_counter.get(k, 0) + 1

    focus_items = [it for it in items if it.is_focus]
    vocab_sorted = sorted(vocab_counter.items(), key=lambda kv: (-kv[1], kv[0]))

    lines = []
    lines.append("# Bilibili 日语精听笔记")
    lines.append("")
    lines.append("## 时间轴日文字幕")
    lines.append("")
    for i, it in enumerate(items, 1):
        lines.append(f"### {i}. [{ts(it.start)} - {ts(it.end)}]")
        lines.append(f"- 日文：{it.ja}")
        lines.append(f"- 中文：{it.zh}")
        lines.append(f"- 生词：{', '.join(it.keywords) if it.keywords else '无'}")
        lines.append("")

    lines.append("## 精听重点句列表")
    lines.append("")
    if not focus_items:
        lines.append("- 无（当前规则下未筛出重点句）")
    else:
        for it in focus_items:
            lines.append(f"- [{ts(it.start)}] {it.ja}")
    lines.append("")

    lines.append("## 生词汇总列表（去重）")
    lines.append("")
    if not vocab_sorted:
        lines.append("- 无")
    else:
        for w, c in vocab_sorted:
            lines.append(f"- {w}（{c}）")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Bilibili Japanese subtitle learning pipeline")
    parser.add_argument("url", help="Bilibili video URL")
    parser.add_argument("--output-dir", default="outputs", help="Output directory")
    parser.add_argument("--model", default="small", help="Whisper model size (tiny/base/small/medium/large-v3)")
    parser.add_argument("--use-browser-cookies", action="store_true", help="Use Chrome login cookies for download")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    audio_path = download_audio(args.url, out_dir, args.use_browser_cookies)
    segments = transcribe(audio_path, args.model)
    split_lines = split_segments(segments)
    items = build_items(split_lines)

    md = render_markdown(items)
    md_path = out_dir / "bilibili_jp_study.md"
    md_path.write_text(md, encoding="utf-8")

    json_path = out_dir / "raw_segments.json"
    json_path.write_text(
        json.dumps(
            [
                {"start": s, "end": e, "text": t}
                for s, e, t in split_lines
            ],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Done. Markdown: {md_path}")
    print(f"Raw segments: {json_path}")


if __name__ == "__main__":
    main()
