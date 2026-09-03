import io
import time
from pathlib import Path

import streamlit as st
from gtts import gTTS


st.set_page_config(
    page_title="آوا | تبدیل متن به گفتار",
    page_icon="🔊",
    layout="centered",
    initial_sidebar_state="collapsed",
)


LANGUAGES = {
    "فارسی": "fa",
    "English": "en",
    "العربية": "ar",
    "Français": "fr",
    "Deutsch": "de",
    "Español": "es",
    "Türkçe": "tr",
    "اردو": "ur",
}
MAX_CHARACTERS = 5000


def read_uploaded_file(uploaded_file):
    """Read supported text files and return their content."""
    file_bytes = uploaded_file.getvalue()
    suffix = Path(uploaded_file.name).suffix.lower()

    if suffix == ".txt":
        return file_bytes.decode("utf-8-sig")
    if suffix == ".docx":
        from docx import Document

        document = Document(io.BytesIO(file_bytes))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)
    raise ValueError("فرمت فایل پشتیبانی نمی‌شود.")


def create_audio(text, language_code, slow):
    audio_buffer = io.BytesIO()
    gTTS(text=text, lang=language_code, slow=slow).write_to_fp(audio_buffer)
    return audio_buffer.getvalue()


def show_audio_result(audio_data):
    st.success("تبدیل با موفقیت انجام شد")
    st.subheader("پخش صوتی")
    st.audio(audio_data, format="audio/mp3")

    file_name = f"speech_{int(time.time())}.mp3"
    st.download_button(
        "دانلود فایل MP3",
        data=audio_data,
        file_name=file_name,
        mime="audio/mpeg",
        use_container_width=True,
        type="primary",
    )
    st.caption(f"حجم فایل: {len(audio_data) / 1024:.1f} KB")


st.markdown(
    """
    <div class="hero">
      <div class="hero-mark">◖</div>
      <div>
        <p class="eyebrow">آزمایشگاه صوتی شخصی شما</p>
        <h1>کلماتت را به صدا تبدیل کن</h1>
        <p class="intro">متن را وارد کن، زبان و ریتم را انتخاب کن، و یک فایل صوتی واضح تحویل بگیر.</p>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap');
      :root { --ink:#17211f; --muted:#68746f; --mint:#c8f2dc; --coral:#ff765f; --paper:#fffdf8; }
      .stApp { background: radial-gradient(circle at 7% 0%, #d7f5e4 0, transparent 28%), linear-gradient(135deg, #fffdf8 0%, #f4f6ef 100%); color:var(--ink); }
      .block-container { max-width: 760px; padding: 4.5rem 1.5rem 3rem; }
      * { font-family:'Vazirmatn', sans-serif; }
      .hero { display:flex; gap:1rem; align-items:flex-start; margin-bottom:2.5rem; direction:rtl; }
      .hero-mark { width:3.3rem; height:3.3rem; display:grid; place-items:center; flex:none; border-radius:14px; background:var(--coral); color:white; font-size:2.7rem; line-height:1; transform:rotate(35deg); box-shadow:7px 7px 0 #f7c3a7; }
      .eyebrow { margin:0 0 .35rem; color:#ef654e; font-size:.78rem; font-weight:700; letter-spacing:.04em; }
      h1 { margin:0; color:var(--ink); font-size:clamp(2rem, 6vw, 3.45rem); line-height:1.15; font-weight:800; }
      .intro { margin:.75rem 0 0; color:var(--muted); font-size:1rem; }
      [data-testid="stTextArea"] textarea { direction:rtl; text-align:right; border:1px solid #dfe6df; border-radius:12px; background:rgba(255,255,255,.75); min-height:170px; }
      [data-testid="stFileUploader"] { direction:rtl; }
      [data-testid="stTabs"] button { font-weight:600; }
      .stButton button, .stDownloadButton button { border-radius:10px; min-height:2.75rem; font-weight:700; }
      [data-testid="stAlert"] { direction:rtl; text-align:right; }
      .stCaption { color:var(--muted); }
      @media (max-width: 600px) { .block-container { padding-top:2.5rem; } .hero { margin-bottom:1.75rem; } .hero-mark { width:2.8rem; height:2.8rem; font-size:2.2rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)

if "audio_data" not in st.session_state:
    st.session_state.audio_data = None

tab_text, tab_file = st.tabs(["ورود متن", "آپلود فایل"])

with tab_text:
    text_input = st.text_area(
        "متن مورد نظر",
        height=180,
        max_chars=MAX_CHARACTERS,
        placeholder="متن خود را اینجا بنویسید...",
        label_visibility="collapsed",
    )
    st.caption(f"{len(text_input)} / {MAX_CHARACTERS} کاراکتر")

    settings_col, speed_col = st.columns(2)
    with settings_col:
        language_name = st.selectbox("زبان", list(LANGUAGES), index=0)
    with speed_col:
        speed = st.radio("سرعت گفتار", ["عادی", "آهسته"], horizontal=True)

    if st.button("🔊  تبدیل به گفتار", type="primary", use_container_width=True, key="text_convert"):
        if not text_input.strip():
            st.warning("لطفاً ابتدا متن خود را وارد کنید.")
        else:
            with st.spinner("در حال ساخت فایل صوتی..."):
                try:
                    st.session_state.audio_data = create_audio(text_input, LANGUAGES[language_name], speed == "آهسته")
                except Exception as error:
                    st.error(f"تبدیل انجام نشد: {error}")

with tab_file:
    uploaded_file = st.file_uploader("فایل TXT یا DOCX را انتخاب کنید", type=["txt", "docx"])
    file_text = ""
    if uploaded_file:
        try:
            file_text = read_uploaded_file(uploaded_file)
            st.text_area("پیش‌نمایش متن فایل", file_text, height=150, disabled=True)
            if len(file_text) > MAX_CHARACTERS:
                st.error(f"متن فایل بیش از {MAX_CHARACTERS} کاراکتر است.")
            elif st.button("🔊  تبدیل فایل", type="primary", use_container_width=True, key="file_convert"):
                with st.spinner("در حال ساخت فایل صوتی..."):
                    st.session_state.audio_data = create_audio(file_text, "fa", False)
        except Exception as error:
            st.error(f"خواندن فایل انجام نشد: {error}")

if st.session_state.audio_data:
    st.divider()
    show_audio_result(st.session_state.audio_data)

with st.expander("راهنمای استفاده"):
    st.markdown(
        """
        - زبان‌های فارسی، انگلیسی، عربی، فرانسوی، آلمانی، اسپانیایی، ترکی و اردو پشتیبانی می‌شوند.
        - طول متن در هر تبدیل حداکثر ۵۰۰۰ کاراکتر است.
        - برای ارتباط با سرویس Google، اتصال اینترنت لازم است.
        - نمونه: سلام! این یک متن آزمایشی برای تبدیل به گفتار است.
        """
    )

st.divider()
st.caption("آوا · ساخته‌شده با Streamlit و gTTS")