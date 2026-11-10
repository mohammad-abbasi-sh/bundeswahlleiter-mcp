# bundeswahlleiter-mcp 🗳️

mcp-name: io.github.mohammad-abbasi-sh/bundeswahlleiter-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **[bundeswahlleiterin.de](https://www.bundeswahlleiterin.de)** — نتایج رسمی انتخابات بوندستاگ از bundeswahlleiterin.de (داده‌های باز رایگان، بدون کلید): نتایج کشوری، نتایج احزاب، حوزه‌های انتخابیه و میزان مشارکت برای ۲۰۱۷، ۲۰۲۱ و ۲۰۲۵. بدون کلید، بدون ورود.

> ساختهٔ محمد عباسی، بخشی از «کارخانهٔ MCP آلمان». وابسته به bundeswahlleiterin.de نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی MCP کلاینت اضافه کنید (stdio):

```json
{
  "mcpServers": {
    "bundeswahlleiter": {
      "command": "uvx",
      "args": ["bundeswahlleiter-mcp==0.1.0"]
    }
  }
}
```

یا به‌صورت محلی اجرا کنید: `python -m bundeswahlleiter_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `bwl_national_results` | نتایج کشوری یک انتخابات بوندستاگ |
| `bwl_party_results` | نتایج یک حزب، کشوری و به تفکیک ایالت |
| `bwl_constituency_results` | نتایج یک حوزهٔ انتخابیه |
| `bwl_constituencies` | فهرست حوزه‌ها با برنده و میزان مشارکت |
| `bwl_turnout` | میزان مشارکت به تفکیک ایالت و کشوری |
| `bwl_health` | بررسی دسترس‌پذیری (ok / blocked / error) — یک درخواست مؤدبانه |

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## لایسنس

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
