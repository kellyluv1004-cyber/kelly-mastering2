import streamlit as st
import io
import pyloudnorm as pyln
import numpy as np
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter, PeakFilter
from pedalboard.io import AudioFile

# 1. 페이지 설정
st.set_page_config(page_title="Kelly AI Mastering v4.8", layout="wide")

# 2. 전 장르 데이터베이스 (28개 전체 반영)
GENRE_DATA = {
    "Pop": {"low_thr": -18, "mid_thr": -20, "hi_thr": -22, "ratio": 2.0, "glue": "Normal"},
    "Ballad": {"low_thr": -20, "mid_thr": -22, "hi_thr": -24, "ratio": 2.0, "glue": "Light"},
    "K-Pop": {"low_thr": -18, "mid_thr": -18, "hi_thr": -20, "ratio": 2.5, "glue": "Normal"},
    "J-Pop": {"low_thr": -18, "mid_thr": -20, "hi_thr": -22, "ratio": 2.0, "glue": "Normal"},
    "R&B": {"low_thr": -16, "mid_thr": -20, "hi_thr": -22, "ratio": 2.5, "glue": "Normal"},
    "Soul": {"low_thr": -18, "mid_thr": -20, "hi_thr": -22, "ratio": 2.0, "glue": "Normal"},
    "Indie": {"low_thr": -20, "mid_thr": -22, "hi_thr": -22, "ratio": 1.5, "glue": "Light"},
    "Hip-hop": {"low_thr": -14, "mid_thr": -18, "hi_thr": -22, "ratio": 3.0, "glue": "Normal"},
    "Trap": {"low_thr": -14, "mid_thr": -18, "hi_thr": -22, "ratio": 3.0, "glue": "Light"},
    "Lo-fi": {"low_thr": -20, "mid_thr": -22, "hi_thr": -26, "ratio": 1.5, "glue": "Light"},
    "Electronic": {"low_thr": -16, "mid_thr": -20, "hi_thr": -20, "ratio": 2.5, "glue": "Light"},
    "House": {"low_thr": -16, "mid_thr": -20, "hi_thr": -20, "ratio": 2.5, "glue": "Normal"},
    "Techno": {"low_thr": -16, "mid_thr": -20, "hi_thr": -20, "ratio": 2.5, "glue": "Normal"},
    "Trance": {"low_thr": -18, "mid_thr": -20, "hi_thr": -18, "ratio": 2.0, "glue": "Normal"},
    "Dubstep": {"low_thr": -12, "mid_thr": -18, "hi_thr": -20, "ratio": 3.0, "glue": "Strong"},
    "Drum & Bass": {"low_thr": -14, "mid_thr": -18, "hi_thr": -18, "ratio": 3.0, "glue": "Strong"},
    "Jazz": {"low_thr": -20, "mid_thr": -22, "hi_thr": -24, "ratio": 1.5, "glue": "Light"},
    "Blues": {"low_thr": -18, "mid_thr": -20, "hi_thr": -22, "ratio": 2.0, "glue": "Normal"},
    "Funk": {"low_thr": -16, "mid_thr": -18, "hi_thr": -20, "ratio": 2.5, "glue": "Normal"},
    "Gospel": {"low_thr": -18, "mid_thr": -18, "hi_thr": -22, "ratio": 2.0, "glue": "Normal"},
    "Rock": {"low_thr": -16, "mid_thr": -18, "hi_thr": -20, "ratio": 2.5, "glue": "Normal"},
    "Metal": {"low_thr": -14, "mid_thr": -16, "hi_thr": -18, "ratio": 3.0, "glue": "Strong"},
    "Punk": {"low_thr": -14, "mid_thr": -16, "hi_thr": -18, "ratio": 3.0, "glue": "Strong"},
    "Grunge": {"low_thr": -14, "mid_thr": -18, "hi_thr": -20, "ratio": 3.0, "glue": "Strong"},
    "Classical": {"low_thr": -22, "mid_thr": -24, "hi_thr": -26, "ratio": 1.2, "glue": "Light"},
    "Ambient": {"low_thr": -22, "mid_thr": -24, "hi_thr": -26, "ratio": 1.2, "glue": "Light"},
    "Country": {"low_thr": -18, "mid_thr": -20, "hi_thr": -22, "ratio": 2.0, "glue": "Normal"},
    "Reggae": {"low_thr": -14, "mid_thr": -20, "hi_thr": -24, "ratio": 2.5, "glue": "Normal"},
    "Latin": {"low_thr": -16, "mid_thr": -18, "hi_thr": -22, "ratio": 2.5, "glue": "Normal"},
    "Afrobeat": {"low_thr": -16, "mid_thr": -18, "hi_thr": -22, "ratio": 2.5, "glue": "Normal"},
    "Disco": {"low_thr": -16, "mid_thr": -18, "hi_thr": -20, "ratio": 2.5, "glue": "Normal"},
    "Default": {"low_thr": -18, "mid_thr": -20, "hi_thr": -22, "ratio": 2.0, "glue": "Normal"}
}

# 3. 메뉴 구조화
GENRE_STRUCTURE = {
    "팝/R&B": ["Pop", "Ballad", "K-Pop", "J-Pop", "R&B", "Soul", "Indie"],
    "힙합/어반": ["Hip-hop", "Trap", "Lo-fi"],
    "일렉트로닉": ["Electronic", "House", "Techno", "Trance", "Dubstep", "Drum & Bass"],
    "재즈/블루스": ["Jazz", "Blues", "Funk", "Gospel"],
    "록/메탈": ["Rock", "Metal", "Punk", "Grunge"],
    "클래식/앰비언트": ["Classical", "Ambient"],
    "월드뮤직": ["Country", "Reggae", "Latin", "Afrobeat", "Disco"]
}

full_menu = []
for cat, subs in GENRE_STRUCTURE.items():
    full_menu.append(f"--- {cat}")
    for s in subs: full_menu.append(f"   {s}")

# 4. 마스터링 코어 함수
def run_mastering_process(audio, sr, genre_name, target_lufs, intensity):
    g_key = genre_name.strip()
    data = GENRE_DATA.get(g_key, GENRE_DATA["Default"])
    
    eq = Pedalboard([
        HighpassFilter(25),
        PeakFilter(60, gain_db=1.0, q=0.7), PeakFilter(150, gain_db=2.0, q=0.7),
        PeakFilter(400, gain_db=1.0, q=0.7), PeakFilter(2500, gain_db=-1.0, q=0.7),
        PeakFilter(8000, gain_db=-1.0, q=0.7)
    ])
    
    mult = {"Light": 0.7, "Normal": 1.0, "Strong": 1.4}.get(intensity, 1.0)
    glue_r = {"Light": 1.2, "Normal": 1.5, "Strong": 2.0}.get(data["glue"], 1.5)

    board = Pedalboard([
        eq,
        Compressor(threshold_db=data["mid_thr"], ratio=glue_r * mult, attack_ms=30, release_ms=250),
        Compressor(threshold_db=data["low_thr"], ratio=data["ratio"] * mult, attack_ms=15, release_ms=150),
        Limiter(threshold_db=-0.5)
    ])
    
    meter = pyln.Meter(sr)
    current_lufs = meter.integrated_loudness(audio.T)
    final_gain = target_lufs - current_lufs
    
    final_chain = Pedalboard([board, Gain(final_gain), Limiter(threshold_db=-0.1)])
    return final_chain(audio, sr)

# 5. UI 디자인
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stSelectbox div[data-baseweb="select"] div { color: #00ff88 !important; font-weight: 600; }
    .step-header { color: #00ff88; font-weight: 800; font-size: 1.4rem; margin-top: 20px; }
    .sub-label { font-size: 0.82rem; color: #888; display: block; margin-bottom: 5px; }
    .stButton > button { background: linear-gradient(90deg, #00ff88, #00d4ff) !important; color: #000000 !important; font-weight: 800 !important; height: 50px !important; border-radius: 8px !important; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

st.title("🎵 Kelly AI Mastering v4.8")

# STEP 1
st.markdown('<div class="step-header">STEP 1. 오디오 파일 업로드</div>', unsafe_allow_html=True)
files = st.file_uploader("Upload", type=["wav", "mp3"], accept_multiple_files=True, label_visibility="collapsed")

# STEP 2
st.markdown('<div class="step-header">STEP 2. 마스터링 설정</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("**🎯 장르**")
    sel_genre = st.selectbox("G", full_menu, index=1, label_visibility="collapsed")
with c2:
    st.markdown("**💾 형식**")
    out_ext = st.selectbox("F", ["wav", "mp3", "flac"], label_visibility="collapsed")
with c3:
    st.markdown("**🔊 음압(LUFS)**")
    target_lufs = st.selectbox("L", [-14, -13, -11, -9], index=1, label_visibility="collapsed")
with c4:
    st.markdown("**⚡ 강도**")
    mode = st.selectbox("I", ["Light", "Normal", "Strong"], index=1, label_visibility="collapsed")

# 6. 실행 로직
if st.button("🚀 RUN MASTERING ENGINE", use_container_width=True, disabled=not files):
    if sel_genre.startswith("---"):
        st.error("세부 장르를 선택해 주세요!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        for idx, f in enumerate(files):
            status_text.text(f"⏳ {f.name} 처리 중...")
            with AudioFile(io.BytesIO(f.getvalue())) as af:
                audio = af.read(af.frames)
                mastered_audio = run_mastering_process(audio, af.samplerate, sel_genre, target_lufs, mode)
                out_io = io.BytesIO()
                with AudioFile(out_io, 'w', af.samplerate, af.num_channels, format=out_ext) as o:
                    o.write(mastered_audio)
                st.success(f"✅ {f.name} 완료!")
                st.audio(out_io.getvalue())
                st.download_button(f"Download {f.name}", out_io.getvalue(), file_name=f"Master_{f.name}.{out_ext}")
            progress_bar.progress((idx + 1) / len(files))
        status_text.text("모든 작업 완료!")
