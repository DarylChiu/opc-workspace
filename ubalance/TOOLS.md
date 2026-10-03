# TOOLS.md - Local Notes

## 专业参考
- IFRS/IAS准则在线: https://www.ifrs.org/
- 越南国家银行(SBV): https://www.sbv.gov.vn/
- 越南银行间汇率参考: Vietcombank, Techcombank官网

## 常用数据源
- SBV每日中间价
- VND/USD Forward Point (银行报价)
- 越南CPI/贸易数据 (GSO)

## 🖼️ 图片处理（2026-10-03 Daryl 定，长期规则）
- **OCR 图片一律优先用本机 Tesseract**（`/opt/homebrew/bin/tesseract`），**不要走 OpenRouter / 云端多模态**（暂时用不了）
- `image` 工具（google/gemini-3-flash-preview）**API key 失效中（2026-09-25 起）**，遇到报错直接切 Tesseract，不要再反复重试
- 可用命令参考：
  ```bash
  tesseract <img> stdout -l eng --psm 6        # 通用文本/清单
  tesseract <img> stdout -l eng+vie --psm 11   # 稀疏文本、越南文
  ```
- 经验：低分辨率小图（如 195×187px）**前缀字符不可靠、数字部分可靠**；用业务数据（如 RM-Database 目录名）反向校正
- macOS 原生 Vision（pyobjc）在本机 python3 下**不可用**（无 Vision 模块）
