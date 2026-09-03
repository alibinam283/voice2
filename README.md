# voice2

تبدیل متن فارسی و چند زبان دیگر به فایل صوتی با Streamlit و gTTS.

## اجرا

```bash
pip install -r requirements.txt
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

مستندات Swagger در `http://localhost:8000/docs` و صفحه تست در `http://localhost:8000/test` در دسترس است. برای اجرای رابط Streamlit در ترمینال دوم، `streamlit run streamlit_app.py --server.port 8501` را اجرا کنید.

این برنامه از ورودی مستقیم متن و فایل‌های `TXT` و `DOCX` پشتیبانی می‌کند و فایل MP3 تولیدشده را برای پخش و دانلود نگه می‌دارد.