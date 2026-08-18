# -*- coding: utf-8 -*-
"""batch_ocr.py v3 — 两本扫描书批量OCR（TextIn xParse 免费通道）
v3 修复: xparse --page-range 是服务端裁剪、上传按整文件算体积(40302超10M) → 必须物理切分
       临时文件用纯 ASCII 路径(绕开中文路径跨shell传参问题)
特性: 断点续跑 / 单批重试1次 / 连续2败停止 / 批体积>9.5MB自动对半降级
"""
import os, sys, json, shutil, subprocess, time
import pymupdf

TMP = r"C:\mkt_ocr_tmp"          # 纯ASCII临时目录
BASE = r"C:\Users\Administrator\Desktop\市场研究\大V研究\书籍蒸馏"
BOOKS = [
    # (书目录名, 源PDF, 目标S0_ocr_raw, 批大小)
    ("美股70年", BASE + r"\01_原文藏书\美股70年\美股70年_燕翔.pdf",
     BASE + r"\02_章节拆解\美股70年\S0_ocr_raw", 50),
    ("全球股市启示录", BASE + r"\01_原文藏书\全球股市启示录\全球股市启示录_燕翔_2022.pdf",
     BASE + r"\02_章节拆解\全球股市启示录\S0_ocr_raw", 12),
]
LIMIT = 9.5 * 1024 * 1024  # 批体积安全上限

os.makedirs(TMP, exist_ok=True)

def run_parse(pdf_ascii, out_dir):
    """调 xparse 解析一个批PDF, 成功返回输出md路径"""
    od = os.path.join(TMP, "out")
    shutil.rmtree(od, ignore_errors=True)
    os.makedirs(od, exist_ok=True)
    cmd = f'xparse-cli --profile workbuddy parse "{pdf_ascii}" --api free --view markdown --output "{od}"'
    for attempt in (1, 2):
        r = subprocess.run(["bash", "-c", cmd], capture_output=True, text=True, timeout=600)
        mds = [f for f in os.listdir(od) if f.endswith(".md")] if os.path.isdir(od) else []
        if r.returncode == 0 and mds:
            return os.path.join(od, mds[0])
        time.sleep(5)
    return None

def split_and_parse(src_pdf, out_raw, batch_size, label):
    """按页区间物理切分→解析→搬运产物, 断点续跑"""
    doc = pymupdf.open(src_pdf)
    n = doc.page_count
    consec_fail = 0
    for start in range(0, n, batch_size):
        end = min(start + batch_size - 1, n - 1)
        dest = os.path.join(out_raw, f"p{start:04d}-{end:04d}.md")
        if os.path.exists(dest) and os.path.getsize(dest) > 100:
            print(f"[SKIP] {label} p{start}-{end} 已存在", flush=True)
            consec_fail = 0
            continue
        # 物理切分(体积超限自动对半降级)
        size = batch_size
        while True:
            part = os.path.join(TMP, f"part_{start}_{size}.pdf")
            d = pymupdf.open()
            d.insert_pdf(doc, from_page=start, to_page=min(start + size - 1, n - 1))
            d.save(part); d.close()
            if os.path.getsize(part) <= LIMIT or size == 1:
                break
            size = size // 2
            os.remove(part)
        md = run_parse(part, TMP)
        try: os.remove(part)
        except OSError: pass
        if md:
            shutil.move(md, dest)
            print(f"[OK] {label} p{start}-{end}({size}页) {os.path.getsize(dest)}B", flush=True)
            consec_fail = 0
        else:
            with open(os.path.join(out_raw, "failures.txt"), "a", encoding="utf-8") as f:
                f.write(f"p{start:04d}-{end:04d}\n")
            print(f"[FAIL] {label} p{start}-{end}", flush=True)
            consec_fail += 1
            if consec_fail >= 2:
                print(f"!!! 连续2败停止 {label}, 断点start={start}(额度尽明日0点后重跑本脚本)", flush=True)
                doc.close(); return
    doc.close()

print(f"===== 批量OCR v3 启动 {time.strftime('%H:%M:%S')} =====", flush=True)
for label, src, out_raw, bs in BOOKS:
    os.makedirs(out_raw, exist_ok=True)
    print(f"--- {label} ---", flush=True)
    split_and_parse(src, out_raw, bs, label)
r = subprocess.run(["bash", "-c", 'xparse-cli --profile workbuddy quota'], capture_output=True, text=True)
print("===== 结束 =====\n" + r.stdout.strip(), flush=True)
