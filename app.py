import streamlit as st
import io
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter, PeakFilter
from pedalboard.io import AudioFile

# 1. 페이지 설정
st.set_page_config(page_title="Kelly AI Mastering v3.3", layout="wide")

# 2. 장르별 데이터 (v3.2 유지)
GENRE_DATA = {
    "Pop": {"sub": 0.5, "low": 1.2, "um": 1.0, "hi": 1.5, "ratio": 2.5},
    "Ballad": {"sub": 1.0, "low": 1.5, "um": -1.0, "hi": -1.0, "ratio": 1.8},
    "Lo-Fi": {"sub": 1.5, "low": 2.5, "um": -1.8, "hi": -2.2, "ratio": 1.6},
    "Hip-Hop": {"sub": 3.0, "low": 3.5, "um": -0.5, "hi": 0.8, "ratio": 3.5},
    "Rock": {"low": 1.5, "mid": 2.0, "um": 1.0, "hi": 0.5, "ratio": 3.0},
    "Default": {"sub": 0.0, "low": 0.0, "um": 0.0, "hi": 0.0, "ratio": 2.0}
}

# 3. 계층형 장르 구조
GENRE_STRUCTURE = {
    "커스텀": ["커스텀"],
    "록/메탈": ["Rock", "Metal", "Punk", "Grunge"],
    "팝/R&B": ["Pop", "Ballad", "K-Pop", "J-Pop", "R&B", "Soul", "Indie"],
    "힙합/어반": ["Hip-Hop", "Trap", "Lo-Fi"],
    "일렉트로닉": ["Electronic", "House", "Techno", "Trance", "Dubstep", "Drum & Bass"],
    "재즈/블루스": ["Jazz", "Blues", "Funk", "Gospel"],
    "클래식/앰비언트": ["Classical", "Ambient"],
    "월드뮤직": ["Country", "Reggae", "Latin", "Afrobeat", "Disco"]
}

formatted_genres = []
for header, subs in GENRE_STRUCTURE.items():
    formatted_genres.append(f"--- {header}")
    for sub in subs:
        formatted_genres.append(f"   {sub}")

# 4. 마스터링 엔진 로직 (v3.2 동일)
def get_album_quality_engine(selected_genre, target_lufs, comp_mode):
    g = selected_genre.strip()
    data = GENRE_DATA.get(g, GENRE_DATA["Default"])
    eq = Pedalboard([
        HighpassFilter(25),
        PeakFilter(60, gain_db=data.get("sub", 0), q=0.7),
        PeakFilter(150, gain_db=data.get("low", 0), q=0.7),
        PeakFilter(1000, gain_db=data.get("mid", 0), q=0.7),
        PeakFilter(2500, gain_db=data.get("um", 0), q=0.7),
        PeakFilter(8000, gain_db=data.get("hi", 0), q=0.7),
    ])
    intensity_map = {"Light": 0.7, "Normal": 1.0, "Strong": 1.4}
    mult = intensity_map.get(comp_mode, 1.0)
    return Pedalboard([
        eq,
        Compressor(threshold_db=-20, ratio=data["ratio"] * mult, attack_ms=20, release_ms=200),
        Limiter(threshold_db=-1.0, release_ms=100)
    ])

# 5. UI 디자인 (글씨 밝기 대폭 강화)
st.markdown("""
<style>
    /* 배경 및 기본 텍스트 */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* 섹션 라벨 (STEP 1, 2...) */
    .step-label { 
        color: #00ff88; 
        font-weight: 800; 
        font-size: 1.2rem; 
        margin-top: 30px; 
        text-shadow: 0px 0px 10px rgba(0, 255, 136, 0.3);
    }
    
    /* 설정 항목 글씨 (Genre, Format, LUFS, Compression) */
    .stSelectbox label, .stFileUploader label {
        color: #FFFFFF !important;  /* 완전한 화이트 */
        font-size: 1.05rem !important;
        font-weight: 700 !important;
        opacity: 1 !important;
        margin-bottom: 10px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5); /* 가독성용 그림자 */
    }

    /* 버튼 스타일 */
    .stButton > button { 
        background: linear-gradient(90deg, #00ff88, #00d4ff) !important; 
        color: #000000 !important; 
        font-weight: 800 !important; 
        height: 55px !important; 
        border-radius: 12px !important;
        border: none !important;
        transition: 0.3s;
    }
    .stButton > button:hover {
        transform: scale(1.01);
        box-shadow: 0px 0px 20px rgba(0, 255, 136, 0.5);
    }
</style>
""", unsafe_allow_html=True)

st.title("🎵 Kelly AI Mastering v3.3")
st.caption("Album-Ready Quality | Enhanced Visibility UI")

# STEP 1
st.markdown('<div class="step-label">STEP 1. Upload Tracks</div>', unsafe_allow_html=True)
files = st.file_uploader("음악 파일을 올려주세요", type=["wav", "mp3"], accept_multiple_files=True)

# STEP 2
st.markdown('<div class="step-label">STEP 2. Professional Settings</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

with c1:
    raw_genre = st.selectbox("Genre Preset", formatted_genres, index=11)
    if raw_genre.startswith("---"):
        st.warning("세부 장르를 선택해 주세요.")
        st.stop()
    selected_genre = raw_genre.strip()

with c2:
    out_ext = st.selectbox("Output Format", ["wav", "mp3", "flac"])

with c3:
    target_lufs = st.selectbox("Target Loudness (LUFS)", [-14, -13, -11, -9], index=1)

with c4:
    comp_mode = st.selectbox("Compression Intensity", ["Light", "Normal", "Strong"], index=1)

# 실행
if st.button("🚀 RUN ALBUM-READY MASTERING", use_container_width=True, disabled=not files):
    with st.spinner(f"Processing..."):
        for f in files:
            with AudioFile(io.BytesIO(f.getvalue())) as audio_f:
                audio = audio_f.read(audio_f.frames)
                engine = get_album_quality_engine(selected_genre, target_lufs, comp_mode)
                
                meter = pyln.Meter(audio_f.samplerate)
                curr_lufs = meter.integrated_loudness(audio.T)
                board = Pedalboard([engine, Gain(target_lufs - curr_lufs), Limiter(threshold_db=-0.1)])
                
                processed = board(audio, audio_f.samplerate)
                out_io = io.BytesIO()
                with AudioFile(out_io, 'w', audio_f.samplerate, audio_f.num_channels, format=out_ext) as o:
                    o.write(processed)
                
                with st.expander(f"📥 {f.name}", expanded=True):
                    st.audio(out_io.getvalue())
                    st.download_button("저장하기", out_io.getvalue(), file_name=f"Mastered_{f.name}.{out_ext}")
