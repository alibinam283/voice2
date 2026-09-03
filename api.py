# api.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import gtts
import os
import uuid
import time
from pathlib import Path
from typing import Optional
import logging

# ========== تنظیمات لاگ ==========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent

# ========== ایجاد اپلیکیشن ==========
app = FastAPI(
    title="🎤 Text-to-Speech API",
    description="""
    ### API برای تبدیل متن به گفتار با استفاده از Google TTS
    
    **قابلیت‌ها:**
    - تبدیل متن به فایل صوتی MP3
    - پشتیبانی از زبان‌های مختلف
    - سرعت قابل تنظیم (Normal/Slow)
    - پاسخ JSON یا فایل مستقیم
    - مدیریت فایل‌های موقت
    
    **زبان‌های پشتیبانی شده:**
    - فارسی (fa)
    - انگلیسی (en)
    - عربی (ar)
    - فرانسوی (fr)
    - آلمانی (de)
    - اسپانیایی (es)
    - ترکی (tr)
    - اردو (ur)
    - روسی (ru)
    - چینی (zh-CN)
    - ژاپنی (ja)
    """,
    version="1.0.0",
    contact={
        "name": "TTS API Support",
        "email": "support@example.com",
    }
)

# ========== CORS ==========
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== مدل‌های داده ==========
class TTSRequest(BaseModel):
    text: str = Field(..., description="متن برای تبدیل به گفتار", min_length=1, max_length=5000)
    lang: str = Field("fa", description="کد زبان (مثلاً: fa, en, ar)", example="fa")
    slow: bool = Field(False, description="آیا سرعت گفتار آهسته باشد؟", example=False)

class TTSResponse(BaseModel):
    success: bool = Field(..., description="وضعیت موفقیت")
    message: str = Field(..., description="پیام وضعیت")
    file_id: Optional[str] = Field(None, description="شناسه فایل برای دانلود")
    file_size: Optional[float] = Field(None, description="حجم فایل به کیلوبایت")
    download_url: Optional[str] = Field(None, description="لینک دانلود فایل")
    duration_seconds: Optional[int] = Field(None, description="مدت زمان تقریبی صدا (ثانیه)")

class LanguageInfo(BaseModel):
    code: str = Field(..., description="کد زبان")
    name: str = Field(..., description="نام زبان به فارسی")
    native_name: str = Field(..., description="نام زبان به زبان اصلی")

# ========== دیتابیس زبان‌ها ==========
LANGUAGES = {
    "fa": {"name": "فارسی", "native": "فارسی"},
    "en": {"name": "انگلیسی", "native": "English"},
    "ar": {"name": "عربی", "native": "العربية"},
    "fr": {"name": "فرانسوی", "native": "Français"},
    "de": {"name": "آلمانی", "native": "Deutsch"},
    "es": {"name": "اسپانیایی", "native": "Español"},
    "tr": {"name": "ترکی", "native": "Türkçe"},
    "ur": {"name": "اردو", "native": "اردو"},
    "ru": {"name": "روسی", "native": "Русский"},
    "zh-CN": {"name": "چینی", "native": "中文"},
    "ja": {"name": "ژاپنی", "native": "日本語"},
}

# ========== مدیریت فایل‌های موقت ==========
temp_files = {}

def cleanup_old_files():
    """حذف فایل‌های قدیمی (بیش از 1 ساعت)"""
    current_time = time.time()
    to_delete = []
    for file_id, data in temp_files.items():
        if current_time - data['created_at'] > 3600:  # 1 ساعت
            to_delete.append(file_id)
            try:
                os.remove(data['path'])
                logger.info(f"حذف فایل قدیمی: {file_id}")
            except Exception as e:
                logger.error(f"خطا در حذف فایل {file_id}: {e}")
    
    for file_id in to_delete:
        del temp_files[file_id]


def validate_request(request: TTSRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="متن نمی‌تواند خالی باشد")
    if request.lang not in LANGUAGES:
        raise HTTPException(status_code=400, detail=f"زبان {request.lang} پشتیبانی نمی‌شود")

# ========== اندپوینت‌ها ==========
@app.get("/", response_class=HTMLResponse)
async def root():
    """صفحه اصلی API"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>TTS API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #4CAF50; }
            .endpoint { background: #f4f4f4; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .endpoint code { background: #333; color: #fff; padding: 3px 8px; border-radius: 3px; }
            .nav { background: #333; padding: 15px; border-radius: 5px; }
            .nav a { color: #fff; margin-right: 15px; text-decoration: none; }
            .nav a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>🎤 Text-to-Speech API</h1>
        <div class="nav">
            <a href="/docs">📚 Swagger Docs</a>
            <a href="/redoc">📖 ReDoc</a>
            <a href="/test">🧪 تست API</a>
            <a href="/languages">🌍 زبان‌ها</a>
        </div>
        
        <h2>📌 اندپوینت‌های موجود:</h2>
        
        <div class="endpoint">
            <h3>🎵 POST /tts</h3>
            <p><code>POST /tts</code> - تبدیل متن به گفتار (فایل MP3)</p>
            <p><strong>مثال:</strong></p>
            <pre>
curl -X POST http://localhost:8000/tts \\
  -H "Content-Type: application/json" \\
  -d '{"text": "سلام دنیا", "lang": "fa"}' \\
  --output speech.mp3
            </pre>
        </div>
        
        <div class="endpoint">
            <h3>📊 POST /tts/json</h3>
            <p><code>POST /tts/json</code> - تبدیل و دریافت پاسخ JSON</p>
        </div>
        
        <div class="endpoint">
            <h3>📥 GET /download/{file_id}</h3>
            <p><code>GET /download/{file_id}</code> - دانلود فایل صوتی</p>
        </div>
        
        <div class="endpoint">
            <h3>🌍 GET /languages</h3>
            <p><code>GET /languages</code> - لیست زبان‌های پشتیبانی شده</p>
        </div>
        
        <div class="endpoint">
            <h3>❤️ GET /health</h3>
            <p><code>GET /health</code> - بررسی سلامت سرویس</p>
        </div>
        
        <p style="margin-top: 30px; color: #666;">برای تست تعاملی به <a href="/test">🧪 تست API</a> بروید.</p>
    </body>
    </html>
    """

@app.get("/test", response_class=HTMLResponse)
async def test_page():
    """صفحه تست تعاملی API"""
    with open(BASE_DIR / "test_api.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/languages")
async def get_languages():
    """لیست زبان‌های پشتیبانی شده"""
    return {
        "success": True,
        "languages": [
            {"code": code, "name": info["name"], "native_name": info["native"]}
            for code, info in LANGUAGES.items()
        ]
    }

@app.get("/health")
async def health_check():
    """بررسی سلامت سرویس"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.post("/tts")
async def text_to_speech(request: TTSRequest):
    """
    تبدیل متن به گفتار و بازگشت مستقیم فایل MP3
    """
    validate_request(request)
    
    # پاکسازی فایل‌های قدیمی
    cleanup_old_files()
    
    try:
        # ایجاد فایل موقت
        file_id = str(uuid.uuid4())[:8]
        file_path = f"/tmp/tts_{file_id}_{int(time.time())}.mp3"
        
        logger.info(f"تبدیل متن: {request.text[:50]}... به زبان: {request.lang}")
        
        # تبدیل
        tts = gtts.gTTS(text=request.text, lang=request.lang, slow=request.slow)
        tts.save(file_path)
        
        # ذخیره در دیکشنری
        temp_files[file_id] = {
            'path': file_path,
            'created_at': time.time(),
            'lang': request.lang
        }
        
        # محاسبه مدت زمان تقریبی
        word_count = len(request.text.split())
        duration = max(1, word_count // 2)  # تقریباً 2 کلمه در ثانیه
        
        # بازگشت فایل
        return FileResponse(
            file_path,
            media_type="audio/mpeg",
            filename=f"speech_{file_id}.mp3",
            headers={
                "X-File-ID": file_id,
                "X-Duration": str(duration)
            }
        )
    
    except gtts.gTTSError as e:
        logger.error(f"خطای gTTS: {e}")
        raise HTTPException(status_code=500, detail=f"خطا در سرویس تبدیل: {str(e)}")
    except Exception as e:
        logger.error(f"خطای ناشناخته: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tts/json", response_model=TTSResponse)
async def text_to_speech_json(request: TTSRequest):
    """
    تبدیل متن به گفتار و بازگشت پاسخ JSON با لینک دانلود
    """
    validate_request(request)
    
    try:
        # ایجاد فایل موقت
        file_id = str(uuid.uuid4())[:8]
        file_path = f"/tmp/tts_{file_id}_{int(time.time())}.mp3"
        
        # تبدیل
        tts = gtts.gTTS(text=request.text, lang=request.lang, slow=request.slow)
        tts.save(file_path)
        
        # ذخیره در دیکشنری
        temp_files[file_id] = {
            'path': file_path,
            'created_at': time.time(),
            'lang': request.lang
        }
        
        # محاسبه حجم
        file_size = os.path.getsize(file_path) / 1024  # KB
        
        # محاسبه مدت زمان تقریبی
        word_count = len(request.text.split())
        duration = max(1, word_count // 2)
        
        return TTSResponse(
            success=True,
            message="تبدیل با موفقیت انجام شد",
            file_id=file_id,
            file_size=round(file_size, 2),
            download_url=f"/download/{file_id}",
            duration_seconds=duration
        )
    
    except Exception as e:
        logger.error(f"خطا: {e}")
        return TTSResponse(
            success=False,
            message=str(e)
        )

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """دانلود فایل صوتی با شناسه"""
    if file_id not in temp_files:
        raise HTTPException(status_code=404, detail="فایل پیدا نشد یا منقضی شده است")
    
    file_data = temp_files[file_id]
    file_path = file_data['path']
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="فایل پیدا نشد")
    
    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        filename=f"speech_{file_id}.mp3"
    )

@app.delete("/cleanup/{file_id}")
async def cleanup_file(file_id: str):
    """حذف یک فایل موقت"""
    if file_id not in temp_files:
        raise HTTPException(status_code=404, detail="فایل پیدا نشد")
    
    try:
        os.remove(temp_files[file_id]['path'])
        del temp_files[file_id]
        return {"success": True, "message": "فایل با موفقیت حذف شد"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== اجرا ==========
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)