#!/bin/bash
# batch_ocr.sh v2 — 两本扫描书断点续跑批量OCR（TextIn xParse 免费通道）
# 修复: xparse-cli 是 Windows 程序, 必须用 C:/ 风格路径; 不 rm 临时目录(避开 safe-delete 拦截)
BASE="C:/Users/Administrator/Desktop/市场研究/大V研究/书籍蒸馏"
BOOK1="$BASE/01_原文藏书/美股70年/美股70年_燕翔.pdf"
BOOK2="$BASE/01_原文藏书/全球股市启示录/全球股市启示录_燕翔_2022.pdf"
OUT1="$BASE/02_章节拆解/美股70年/S0_ocr_raw"
OUT2="$BASE/02_章节拆解/全球股市启示录/S0_ocr_raw"
XPARSE="xparse-cli --profile workbuddy"
CONSEC_FAIL=0

run_batch() {
  local pdf=$1 out=$2 start=$3 end=$4
  local fname="p$(printf %04d $start)-$(printf %04d $end).md"
  local dest="$out/$fname"
  if [ -s "$dest" ]; then echo "[SKIP] $fname 已存在"; CONSEC_FAIL=0; return 0; fi
  local tmp="$out/tmp_$start"
  mkdir -p "$tmp"
  local rng="$((start+1))-$((end+1))"
  if $XPARSE parse "$pdf" --api free --page-range "$rng" --view markdown --output "$tmp" >> "$out/parse_log.txt" 2>&1; then
    if mv "$tmp"/*.md "$dest" 2>>"$out/parse_log.txt" && [ -s "$dest" ]; then
      echo "[OK] $fname ($(wc -c < "$dest") bytes)"; CONSEC_FAIL=0; return 0
    fi
  fi
  sleep 5
  if $XPARSE parse "$pdf" --api free --page-range "$rng" --view markdown --output "$tmp" >> "$out/parse_log.txt" 2>&1; then
    if mv "$tmp"/*.md "$dest" 2>>"$out/parse_log.txt" && [ -s "$dest" ]; then
      echo "[OK-retry] $fname"; CONSEC_FAIL=0; return 0
    fi
  fi
  echo "[FAIL] $fname rng=$rng" >> "$out/failures.txt"
  echo "[FAIL] $fname"
  CONSEC_FAIL=$((CONSEC_FAIL+1))
  return 1
}

echo "===== 批量OCR v2 启动 $(date '+%H:%M:%S') ====="
rm -f "$OUT1/failures.txt" "$OUT2/failures.txt"
mkdir -p "$OUT1" "$OUT2"

echo "--- 书1: 美股70年 496页, 50页/批 ---"
for ((s=0; s<496; s+=50)); do
  e=$((s+49)); [ $e -ge 496 ] && e=495
  run_batch "$BOOK1" "$OUT1" $s $e
  [ $CONSEC_FAIL -ge 3 ] && { echo "!!! 连续3败, 停止书1, 断点start=$s"; break; }
done

echo "--- 书2: 启示录 502页, 12页/批 ---"
for ((s=0; s<502; s+=12)); do
  e=$((s+11)); [ $e -ge 502 ] && e=501
  run_batch "$BOOK2" "$OUT2" $s $e
  [ $CONSEC_FAIL -ge 2 ] && { echo "!!! 连续失败(额度可能已尽), 停止书2, 断点start=$s 明晨0点后重跑本脚本续"; break; }
done

echo "===== 批量OCR结束 $(date '+%H:%M:%S') ====="
echo "书1产物: $(ls "$OUT1"/p*.md 2>/dev/null | wc -l) 批 | 书2产物: $(ls "$OUT2"/p*.md 2>/dev/null | wc -l) 批"
[ -s "$OUT1/failures.txt" ] && echo "书1失败批:" && cat "$OUT1/failures.txt"
[ -s "$OUT2/failures.txt" ] && echo "书2失败批:" && cat "$OUT2/failures.txt"
xparse-cli --profile workbuddy quota 2>&1 | head -2
