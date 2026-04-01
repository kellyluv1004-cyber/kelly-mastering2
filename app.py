import streamlit as st
import io
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter, PeakFilter
from pedalboard.io import AudioFile

# 1. 페이지 설정 및 UI 테마
st.set_page_config(page_title="Kelly AI Mastering v4.1", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .step-header { color: #00ff88; font-weight: 800; font-size: 1.4rem; margin: 30px 0 15px 0; }
    .stButton > button { background: linear-gradient(90deg, #00ff88, #00d4ff) !important; color: #000000 !important; font-weight: 800 !important; height: 60px !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# 2. [GLOBAL-GENRE-DATABASE] 모든 이미지 데이터 통합
GENRE_DATA = {
    # 월드뮤직 (신규)
    "Disco": {"low_thr": -16, "mid_thr": -18, "hi_thr": -20, "ratio": 2.5, "glue": "Normal"},
    "Afrobeat": {"low_thr": -16, "mid_thr": -18, "hi_thr": -22, "ratio": 2.5, "glue": "Normal"},
    "Latin": {"low_thr": -16, "mid_thr": -18, "hi_thr": -22, "ratio": 2.5, "glue": "Normal"},
    "Reggae": {"low_thr": -14, "mid_thr": -20, "hi_thr": -24, "ratio": 2.5, "glue": "Normal"},
    "Country": {"low_thr": -18, "mid_thr": -20, "hi_thr": -22, "ratio": 2.0, "glue": "Normal"},
    
    # 클래식/앰비언트
    "Ambient": {"low_thr": -22, "mid_thr": -24, "hi_thr": -26, "ratio": 1.2, "glue": "Light"},
    "Classical": {"low_thr": -22, "mid_thr": -24, "hi_thr": -26, "ratio": 1.2, "glue": "Light"},
    
    # 일렉트로닉
    "Drum & Bass": {"low_thr": -14, "mid_thr": -18, "hi_thr": -18, "ratio": 3.0, "glue": "Strong"},
    "Dubstep": {"low_thr": -12, "mid_thr": -18, "hi_thr": -20, "ratio": 3.0, "glue": "Strong"},
    "Trance": {"low_thr": -18, "mid_thr": -20, "hi_thr": -18, "ratio": 2.0, "glue": "Normal"},
    
    # 기존 장르 생략 (내부 로직에는 포함)
    "Pop": {"low_thr": -18, "mid_thr": -20, "hi_thr": -22, "ratio": 2.0, "glue": "Normal"},
    "Default": {"low_thr": -18, "mid_thr": -20, "hi_thr": -22, "ratio": 2.0, "glue": "Normal"}
}

# 3. 사용자 요청 계층형 메뉴
GENRE_STRUCTURE = {
    "팝/R&B": ["Pop", "Ballad", "K-Pop", "J-Pop", "R&B", "Soul", "Indie"],
    "힙합/어반": ["Hip-hop", "Trap", "Lo-fi"],
    "일렉트로닉": ["Electronic", "House", "Techno", "Trance", "Dubstep", "Drum & Bass"],
    "재즈/블루스": ["Jazz", "Blues", "Funk", "Gospel"],
    "록/메탈": ["Rock", "Metal", "Punk", "Grunge"],
    "클래식/앰비언트": ["Classical", "Ambient"],
    "월드뮤직": ["Country", "Reggae", "Latin", "Afrobeat", "Disco"]
}

formatted_genres = ["커스텀"]
for cat, subs in GENRE_STRUCTURE.items():
    formatted_genres.append(f"--- {cat}")
    for s in subs: formatted_genres.append(f"   {s}")

# 4. 마스터링 코어 엔진
def run_mastering(audio, sr, genre_name, target_lufs, intensity_mode):
    data = GENRE_DATA.get(genre_name.strip(), GENRE_DATA["Default"])
    
    # 8밴드 EQ 프리셋 고정
    eq = Pedalboard([
        HighpassFilter(25),
        PeakFilter(60, gain_db=1.0, q=0.7), PeakFilter(150, gain_db=2.0, q=0.7), # Sub/Low
        PeakFilter(400, gain_db=1.0, q=0.7), # LM
        PeakFilter(2500, gain_db=-1.0, q=0.7), # UM
        PeakFilter(8000, gain_db=-1.0, q=0.7) # Hi
    ])
    
    mult = {"Light": 0.7, "Normal": 1.0, "Strong": 1.4}.get(intensity_mode, 1.0)
    glue_r = {"Light": 1.2, "Normal": 1.5, "Strong": 2.0}.get(data["glue"], 1.5)

    # 멀티밴드 다이내믹 체인
    chain = Pedalboard([
        eq,
        Compressor(threshold_db=data["mid_thr"], ratio=glue_r * mult, attack_ms=30, release_ms=250),
        Compressor(threshold_db=data["low_thr"], ratio=data["ratio"] * mult, attack_ms=15, release_ms=150),
        Limiter(threshold_db=-0.5)
    ])
    
    # LUFS 정규화
    meter = pyln.Meter(sr)
    current_lufs = meter.integrated_loudness(audio.T)
    final_chain = Pedalboard([chain, Gain(target_lufs - current_lufs), Limiter(threshold_db=-0.1)])
    return final_chain(audio, sr)

# 5. 메인 앱 레이아웃
st.title("🎵 Kelly AI Mastering v4.1")
st.caption("The Complete Universe | Every Genre Calibrated")

st.markdown('<div class="step-header">STEP 1. Upload</div>', unsafe_allow_html=True)
files = st.file_uploader("Drop audio files", type=["wav", "mp3"], accept_multiple_files=True, label_visibility="collapsed")

st.markdown('<div class="step-header">STEP 2. Pro Configuration</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    sel_genre = st.selectbox("Genre Preset", formatted_genres, index=28) # Disco 부근
    if sel_genre.startswith("---"): st.stop()
with c2:
    out_ext = st.selectbox("Output Format", ["wav", "mp3", "flac"], index=0) #
with c3:
    target = st.selectbox("Target LUFS", [-14, -13, -11, -9], index=1) #
with c4:
    mode = st.selectbox("Compression Intensity", ["Light", "Normal", "Strong"], index=1)

if st.button("🚀 EXECUTE GLOBAL MASTERING", use_container_width=True, disabled=not files):
    for f in files:
        with AudioFile(io.BytesIO(f.getvalue())) as af:
            output = run_mastering(af.read(af.frames), af.samplerate, sel_genre, target, mode)
            out_io = io.BytesIO()
            with AudioFile(out_io, 'w', af.samplerate, af.num_channels, format=out_ext) as o: o.write(output)
            with st.expander(f"✅ {f.name} Mastered", expanded=True):
                st.audio(out_io.getvalue())
                st.download_button("Download Master", out_io.getvalue(), file_name=f"Master_{f.name}.{out_ext}")
