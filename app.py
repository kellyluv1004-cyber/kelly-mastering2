import streamlit as st
import io
import zipfile
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter
from pedalboard.io import AudioFile

# 페이지 설정
st.set_page_config(page_title="Kelly AI Mastering v2", layout="wide")

# 1. 요청하신 장르 계층 구조 정의 (스크린샷 기반)
GENRE_MAP = {
    "--- 커스텀": ["커스텀"],
    "--- 록/메탈": ["Rock", "Metal", "Punk", "Grunge"],
    "--- 팝/R&B": ["Pop", "Ballad", "K-Pop", "J-Pop", "R&B", "Soul", "Indie"],
    "--- 힙합/어반": ["Hip-Hop", "Trap", "Lo-Fi"],
    "--- 일렉트로닉": ["Electronic", "House", "Techno", "Trance", "Dubstep", "Drum & Bass"],
    "--- 재즈/블루스": ["Jazz", "Blues", "Funk", "Gospel"],
    "--- 클래식/앰비언트": ["Classical", "Ambient"],
    "--- 월드뮤직": ["Country", "Reggae", "Latin", "Afrobeat", "Disco"]
}

# selectbox에 넣을 평탄화된 리스트 생성
formatted_genres = []
for header, subs in GENRE_MAP.items():
    formatted_genres.append(header) # 대분류 헤더
    for sub in subs:
        formatted_genres.append(f"   {sub}") # 세부 장르 (들여쓰기)

# 2. 가벼운 배포 전용 캐싱 엔진
@st.cache_data(show_spinner=False)
def process_audio_engine(file_bytes, target_lufs, comp_db, out_ext):
    try:
        with AudioFile(io.BytesIO(file_bytes)) as f:
            audio = f.read(f.frames)
            samplerate = f.samplerate
            board = Pedalboard([
                HighpassFilter(30),
                Compressor(threshold_db=comp_db, ratio=4),
                Gain(target_lufs - pyln.Meter(samplerate).integrated_loudness(audio.T)),
                Limiter(threshold_db=-0.1)
            ])
            processed = board(audio, samplerate)
            out_io = io.BytesIO()
            with AudioFile(out_io, 'w', samplerate, f.num_channels, format=out_ext) as o:
                o.write(processed)
            return out_io.getvalue()
    except Exception as e: return None

# 3. 디자인 CSS (v2의 고급스런 다크 UI)
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stSlider [data-baseweb="typography"] { color: #00ff88; font-weight: bold; }
    .stButton > button { background: #00ff88 !important; color: #000000; font-weight: 800; border: none; }
    .step-label { color: #00ff88; font-weight: 700; font-size: 1.1rem; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🎵 Kelly AI Mastering v2")
st.caption("Faster. Lighter. Better.")

# STEP 1. 업로드
st.markdown('<div class="step-label">STEP 1. Upload Tracks</div>', unsafe_allow_html=True)
files = st.file_uploader("Upload", type=["wav", "mp3"], accept_multiple_files=True, label_visibility="collapsed")

# STEP 2. 설정
st.markdown('<div class="step-label">STEP 2. Mastering Settings</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)

with c1:
    # 요청하신 장르 배치 적용
    raw_genre = st.selectbox("Genre Preset", formatted_genres, index=12) # Lo-Fi 기본값
    
    # 헤더(---) 선택 시 방어 로직
    if raw_genre.startswith("---"):
        st.warning("대분류 헤더 대신 아래의 세부 장르를 선택해 주세요.")
        st.stop()
    selected_genre = raw_genre.strip() # 들여쓰기 제거

with c2:
    out_ext = st.selectbox("Output Format", ["wav", "mp3", "flac"])

st.write("")
col_l, col_r = st.columns(2)
with col_l:
    target_lufs = st.select_slider("Target Loudness (LUFS)", options=[-14, -13, -11, -9], value=-14)
with col_r:
    comp_mode = st.select_slider("Compression Intensity", options=["Light", "Normal", "Strong"], value="Normal")
    comp_db = {"Light": -18, "Normal": -22, "Strong": -26}[comp_mode]

st.write("")

# STEP 3. 실행
if st.button("🚀 RUN AI MASTERING", use_container_width=True, disabled=not files):
    results = []
    with st.spinner("Processing..."):
        for f in files:
            output = process_audio_engine(f.getvalue(), target_lufs, comp_db, out_ext)
            if output: results.append({"name": f.name, "data": output})
    
    if results:
        st.success(f"✅ {len(results)} Tracks Ready!")
        for res in results:
            with st.expander(f"📥 {res['name']}"):
                st.audio(res['data'])
                st.download_button("Download", res['data'], file_name=f"Mastered_{res['name']}.{out_ext}")
