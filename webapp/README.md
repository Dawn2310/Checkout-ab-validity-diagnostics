# Webapp — A/B Test Validity Diagnostics

Multi-page Flask site (8 trang, điều hướng bằng click) + chatbot OpenAI.

## Chạy local

```bash
pip install flask openai python-dotenv pandas

# Cấu hình API key cho chatbot
copy webapp\.env.example webapp\.env
# rồi mở webapp/.env, dán OPENAI_API_KEY=sk-...

python webapp/app.py
# → mở http://localhost:5000
```

## Các trang

| Route | Nội dung |
|---|---|
| `/` | Hero + KPI tiles + 3 RQ + nav cards |
| `/dataset` | Bảng aggregate, claim-boundary, time series CR |
| `/diagnostics` | SRM, A/A simulation, outlier days — phát hiện trung tâm |
| `/results` | Click-level vs day-level, quasi-binomial GLM, Plotly CR chart |
| `/funnel` | Waterfall interactive (Plotly), compositional confounding |
| `/weekday` | Forest plot interactive (Plotly), hypothesis-generating |
| `/paper` | Abstract, cấu trúc, references, download .tex/.bib |
| `/chatbot` | Chat UI gọi `/api/chat` (OpenAI gpt-4o-mini) |

## Chatbot

- RAG-lite: toàn bộ `output/statistical_results.txt`, `diagnostics_report.txt`,
  `hte_weekday.csv` + tóm tắt paper được nhúng vào system prompt
  (xem `context_builder.py`).
- Không có API key → trang vẫn chạy, chat trả lời hướng dẫn cấu hình.
- Đổi model qua env `OPENAI_MODEL`.

## Deploy

- **Render / Railway**: thêm `gunicorn`, start command
  `gunicorn --chdir webapp app:app`, set env `OPENAI_API_KEY`.
- Lưu ý: app đọc số liệu từ `output/tables/*.csv` — giữ folder này trong repo
  hoặc chạy `python main.py` trong build step.
