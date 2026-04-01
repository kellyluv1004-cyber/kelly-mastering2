import streamlit as st
import io
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter, PeakFilter
from pedalboard.io import AudioFile

# 1. 페이지 설정
st.set_page_config(page_title="Kelly AI Mastering v3.4", layout="wide")

# 2. 장르별 황금값 데이터 (v3.2 유지)
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

# 4. 고음질 마스터링 엔진
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

# 5. UI 스타일링 (글씨 밝기 및 레이아웃 최적화)
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* 모든 메인 라벨 글씨를 밝게 */
    label[data-testid="stWidgetLabel"] p {
        color: #FFFFFF !important;
        font-size: 1.1rem !important;
        font-weight: 800 !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.8);
    }
    
    .step-label { 
        color: #00ff88; 
        font-weight: 800; 
        font-size: 1.3rem; 
        margin-top: 35px; 
        margin-bottom: 15px;
    }

    /* 버튼 스타일 강화 */
    .stButton > button { 
        background: linear-gradient(90deg, #00ff88, #00d4ff) !important; 
        color: #000000 !important; 
        font-weight: 800 !important; 
        height: 60px !important; 
        border-radius: 15px !important;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎵 Kelly AI Mastering v3.4")
st.caption("Album-Ready Quality | High-Contrast Pro UI")

# STEP 1
st.markdown('<div class="step-label">STEP 1. Upload Tracks</div>', unsafe_allow_html=True)
files = st.file_uploader("마스터링할 음원을 선택하세요", type=["wav", "mp3"], accept_multiple_files=True)

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
    # 상세 설명 복구
    format_options = {
        "WAV · 16bit 44.1kHz": "wav",
        "MP3 · 320kbps": "mp3",
        "FLAC · 24bit 96kHz": "flac"
    }
    selected_format_label = st.selectbox("Output Format", list(format_options.keys()))
    out_ext = format_options[selected_format_label]

with c3:
    # 상세 가이드 문구 복구
    lufs_options = {
        "Streaming (–13 LUFS)": -13.0,
        "YouTube (–14 LUFS)": -14.0,
        "CD Standard (–11 LUFS)": -11.0,
        "Loud/Club (–9 LUFS)": -9.0
    }
    selected_lufs_label = st.selectbox("Target Loudness (LUFS)", list(lufs_options.keys()))
    target_lufs = lufs_options[selected_lufs_label]

with c4:
    comp_mode = st.selectbox("Compression Intensity", ["Light", "Normal", "Strong"], index=1)

# 실행 및 결과 출력
if st.button("🚀 RUN ALBUM-READY MASTERING", use_container_width=True, disabled=not files):
    with st.spinner(f"Applying {selected_genre} Mastering..."):
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
