# app.py
import streamlit as st
import gtts
import os
import tempfile
import time
import requests
import json

st.set_page_config(
    page_title="🎤 تبدیل متن به گفتار",
    page_icon="🔊",
    layout="wide"
)

# ========== منوی کناری ==========
st.sidebar.title("📱 منو")
page = st.sidebar.radio(
    "انتخاب بخش:",
    ["🎤 تبدیل متن", "🔗 مستندات API", "🧪 تست API", "📊 وضعیت سرویس"]
)

# ========== صفحه 1: تبدیل متن ==========
if page == "🎤 تبدیل متن":
    st.title("🔊 تبدیل متن به گفتار")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        text_input = st.text_area(
            "📝 متن خود را وارد کنید:",
            height=150,
            placeholder="متن خود را اینجا بنویسید...",
            help="حداکثر 5000 کاراکتر"
        )
    
    with col2:
        st.markdown("### ⚙️ تنظیمات")
        language = st.selectbox(
            "🌍 زبان",
            [
                ("فارسی", "fa"),
                ("English", "en"),
                ("العربية", "ar"),
                ("Français", "fr"),
                ("Deutsch", "de"),
                ("Español", "es"),
                ("Türkçe", "tr"),
                ("اردو", "ur")
            ],
            format_func=lambda x: x[0],
            index=0
        )
        lang_code = language[1]
        
        speed = st.selectbox(
            "🐢 سرعت",
            ["Normal", "Slow"],
            index=0
        )
        
        slow_mode = True if speed == "Slow" else False
    
    # دکمه تبدیل
    if st.button("🎵 تبدیل به گفتار", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("⚠️ لطفاً متن خود را وارد کنید!")
        elif len(text_input) > 5000:
            st.error("❌ متن طولانی است! حداکثر 5000 کاراکتر مجاز است.")
        else:
            with st.spinner("⏳ در حال تبدیل متن به گفتار..."):
                try:
                    # ایجاد فایل موقت
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                        audio_path = tmp.name
                    
                    # تبدیل
                    tts = gtts.gTTS(text=text_input, lang=lang_code, slow=slow_mode)
                    tts.save(audio_path)
                    
                    # خواندن فایل
                    with open(audio_path, "rb") as f:
                        audio_bytes = f.read()
                    
                    # نمایش نتیجه
                    st.success("✅ تبدیل با موفقیت انجام شد!")
                    
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.audio(audio_bytes, format="audio/mp3")
                    with col2:
                        file_size = os.path.getsize(audio_path) / 1024
                        st.info(f"📊 حجم: {file_size:.1f} KB")
                        st.download_button(
                            label="📥 دانلود MP3",
                            data=audio_bytes,
                            file_name=f"speech_{int(time.time())}.mp3",
                            mime="audio/mp3",
                            use_container_width=True
                        )
                    
                    # پاک کردن فایل موقت
                    os.remove(audio_path)
                    
                except Exception as e:
                    st.error(f"❌ خطا: {str(e)}")

# ========== صفحه 2: مستندات API ==========
elif page == "🔗 مستندات API":
    st.title("🔗 مستندات API")
    st.markdown("---")
    
    st.markdown("""
    ### 🌐 آدرس‌های API
    
    | روش | آدرس | توضیح |
    |-----|------|-------|
    | POST | `/tts` | تبدیل متن به گفتار (فایل MP3) |
    | POST | `/tts/json` | تبدیل متن به گفتار (پاسخ JSON) |
    | GET | `/download/{file_id}` | دانلود فایل صوتی |
    | GET | `/languages` | لیست زبان‌های پشتیبانی شده |
    | GET | `/health` | بررسی سلامت سرویس |
    
    ### 📝 نمونه درخواست با Python
    
    ```python
    import requests
    
    # روش 1: دریافت فایل مستقیم
    response = requests.post(
        "http://localhost:8000/tts",
        json={
            "text": "سلام دنیا",
            "lang": "fa",
            "slow": False
        }
    )
    
    if response.status_code == 200:
        with open("speech.mp3", "wb") as f:
            f.write(response.content)
        print("✅ فایل ذخیره شد!")
    
    # روش 2: دریافت JSON
    response = requests.post(
        "http://localhost:8000/tts/json",
        json={
            "text": "سلام دنیا",
            "lang": "fa"
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ {data['message']}")
        print(f"📥 دانلود: {data['download_url']}")