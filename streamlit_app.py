# streamlit_app.py
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
    """)
    
    st.subheader("📝 نمونه درخواست با Python")
    st.code("""
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
    """, language="python")
    
    st.subheader("📱 نمونه با JavaScript")
    st.code("""
// دریافت فایل
fetch('http://localhost:8000/tts', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        text: 'سلام دنیا',
        lang: 'fa'
    })
})
.then(response => response.blob())
.then(blob => {
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play();
});
    """, language="javascript")
    
    st.subheader("🔧 تست با curl")
    st.code("""
# دریافت فایل
curl -X POST http://localhost:8000/tts \\
  -H "Content-Type: application/json" \\
  -d '{"text": "سلام دنیا", "lang": "fa"}' \\
  --output speech.mp3

# دریافت JSON
curl -X POST http://localhost:8000/tts/json \\
  -H "Content-Type: application/json" \\
  -d '{"text": "سلام دنیا", "lang": "fa"}'
    """, language="bash")
    
    # نمایش زبان‌ها
    st.subheader("🌍 زبان‌های پشتیبانی شده")
    languages = {
        "fa": "فارسی",
        "en": "انگلیسی",
        "ar": "عربی",
        "fr": "فرانسوی",
        "de": "آلمانی",
        "es": "اسپانیایی",
        "tr": "ترکی",
        "ur": "اردو",
        "ru": "روسی",
        "zh-CN": "چینی",
        "ja": "ژاپنی"
    }
    
    cols = st.columns(4)
    for i, (code, name) in enumerate(languages.items()):
        cols[i % 4].markdown(f"- **{code}**: {name}")

# ========== صفحه 3: تست API ==========
elif page == "🧪 تست API":
    st.title("🧪 تست API")
    st.markdown("---")
    
    st.info("💡 این بخش به شما امکان می‌دهد API را به صورت تعاملی تست کنید")
    
    # تنظیمات
    col1, col2, col3 = st.columns(3)
    with col1:
        api_url = st.text_input("🌐 آدرس API", "http://localhost:8000")
    with col2:
        test_lang = st.selectbox("🌍 زبان", ["fa", "en", "ar", "fr", "de", "es", "tr", "ur"])
    with col3:
        test_mode = st.selectbox("📤 حالت خروجی", ["فایل MP3", "JSON"])
    
    test_text = st.text_area(
        "📝 متن تست:",
        "سلام! این یک تست از API تبدیل متن به گفتار است.",
        height=100
    )
    
    if st.button("🚀 ارسال درخواست", type="primary", use_container_width=True):
        if not test_text.strip():
            st.warning("⚠️ لطفاً متن را وارد کنید!")
        else:
            with st.spinner("⏳ در حال ارسال درخواست..."):
                try:
                    is_json = test_mode == "JSON"
                    endpoint = f"{api_url}/tts{ '/json' if is_json else ''}"
                    
                    response = requests.post(
                        endpoint,
                        json={
                            "text": test_text,
                            "lang": test_lang,
                            "slow": False
                        },
                        timeout=30
                    )
                    
                    if is_json:
                        # نمایش پاسخ JSON
                        data = response.json()
                        st.subheader("📊 پاسخ JSON:")
                        st.json(data)
                        
                        if data.get('success'):
                            st.success("✅ تبدیل موفق!")
                            if data.get('download_url'):
                                st.info(f"📥 لینک دانلود: {api_url}{data['download_url']}")
                    else:
                        # نمایش فایل صوتی
                        if response.status_code == 200:
                            st.success("✅ تبدیل موفق!")
                            st.audio(response.content, format="audio/mp3")
                            
                            st.download_button(
                                label="📥 دانلود فایل",
                                data=response.content,
                                file_name=f"test_{int(time.time())}.mp3",
                                mime="audio/mp3",
                                use_container_width=True
                            )
                        else:
                            st.error(f"❌ خطا: {response.status_code}")
                            try:
                                st.json(response.json())
                            except ValueError:
                                st.text(response.text)
                            
                except requests.exceptions.ConnectionError:
                    st.error("❌ خطا: اتصال به API برقرار نیست. لطفاً API را اجرا کنید.")
                except Exception as e:
                    st.error(f"❌ خطا: {str(e)}")
    
    # نمایش کد نمونه
    with st.expander("📋 کد نمونه برای این درخواست"):
        st.code(f"""
import requests

response = requests.post(
    "{api_url}/tts{ '/json' if test_mode == 'JSON' else '' }",
    json={{
        "text": "{test_text}",
        "lang": "{test_lang}",
        "slow": false
    }}
)

if response.status_code == 200:
    {'print(response.json())' if test_mode == 'JSON' else 'with open("speech.mp3", "wb") as f: f.write(response.content)'}
        """, language="python")

# ========== صفحه 4: وضعیت سرویس ==========
else:
    st.title("📊 وضعیت سرویس")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✅ وضعیت")
        st.markdown("""
        - **سرویس**: 🟢 فعال
        - **نسخه**: 1.0.0
        - **API**: `/tts` و `/tts/json`
        """)
        
    with col2:
        st.subheader("📊 آمار")
        st.markdown("""
        - **زبان‌های پشتیبانی شده**: 11 زبان
        - **حداکثر متن**: 5000 کاراکتر
        - **فرمت خروجی**: MP3
        """)
    
    st.subheader("🌐 وضعیت API")
    
    api_check_url = st.text_input("آدرس API برای بررسی:", "http://localhost:8000")
    
    if st.button("🔍 بررسی وضعیت"):
        try:
            response = requests.get(f"{api_check_url}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ API فعال است!")
                st.json(response.json())
            else:
                st.warning(f"⚠️ پاسخ غیرمنتظره: {response.status_code}")
        except requests.exceptions.ConnectionError:
            st.error("❌ API در دسترس نیست. لطفاً آن را اجرا کنید.")
        except Exception as e:
            st.error(f"❌ خطا: {str(e)}")
    
    # اطلاعات سیستم
    with st.expander("ℹ️ اطلاعات سیستم"):
        st.markdown(f"""
        - **پلتفرم**: Streamlit
        - **Python**: {os.sys.version}
        - **gTTS**: نسخه {gtts.__version__ if hasattr(gtts, '__version__') else 'نصب شده'}
        """)

# ========== فوتر ==========
st.sidebar.markdown("---")
st.sidebar.caption("🔊 ساخته شده با ❤️")
st.sidebar.caption("نسخه 1.0.0")