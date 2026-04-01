import streamlit as st
import io
import pyloudnorm as pyln
import numpy as np
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter, PeakFilter
from pedalboard.io import AudioFile

# 1. 페이지 설정
st.set_page_config(page_title="Kelly AI Mastering v5.0", layout="wide")

# 2. [완전 재설정] 28개 장르 3밴드 정밀 데이터베이스
# 이미지 수치를 바탕으로 저(Low), 중(Mid), 고(Hi) 대역의 Ratio를 각각 다르게 설정했습니다.
GENRE_DATA = {
    # 팝/R&B
    "Pop": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "Ballad": {"low": {"thr": -20, "rat": 2.0}, "mid": {"thr": -22, "rat": 1.5}, "hi": {"thr": -24, "rat": 1.2}, "glue": "Light"},
    "K-Pop": {"low": {"thr": -18, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.0}, "hi": {"thr": -20, "rat": 1.8}, "glue": "Normal"},
    "J-Pop": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "R&B": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -20, "rat": 2.0}, "hi": {"thr": -22, "rat": 1.8}, "glue": "Normal"},
    "Soul": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "Indie": {"low": {"thr": -20, "rat": 1.5}, "mid": {"thr": -22, "rat": 1.3}, "hi": {"thr": -22, "rat": 1.1}, "glue": "Light"},

    # 힙합/어반
    "Hip-hop": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -18, "rat": 2.5}, "hi": {"thr": -22, "rat": 2.0}, "glue": "Normal"},
    "Trap": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -18, "rat": 2.5}, "hi": {"thr": -22, "rat": 2.0}, "glue": "Light"},
    "Lo-fi": {"low": {"thr": -20, "rat": 2.0}, "mid": {"thr": -22, "rat": 1.5}, "hi": {"thr": -26, "rat": 1.2}, "glue": "Light"},

    # 일렉트로닉
    "Electronic": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -20, "rat": 2.0}, "hi": {"thr": -20, "rat": 1.8}, "glue": "Light"},
    "House": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -20, "rat": 2.2}, "hi": {"thr": -20, "rat": 2.0}, "glue": "Normal"},
    "Techno": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -20, "rat": 2.2}, "hi": {"thr": -20, "rat": 2.0}, "glue": "Normal"},
    "Trance": {"low": {"thr": -10, "rat": 2.0}, "mid": {"thr": -20, "rat": 2.0}, "hi": {"thr": -18, "rat": 1.5}, "glue": "Normal"},
    "Dubstep": {"low": {"thr": -12, "rat": 3.5}, "mid": {"thr": -18, "rat": 3.0}, "hi": {"thr": -20, "rat": 2.5}, "glue": "Strong"},
    "Drum & Bass": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -18, "rat": 2.5}, "hi": {"thr": -15, "rat": 2.0}, "glue": "Strong"},

    # 재즈/블루스
    "Jazz": {"low": {"thr": -20, "rat": 1.5}, "mid": {"thr": -22, "rat": 1.3}, "hi": {"thr": -24, "rat": 1.1}, "glue": "Light"},
    "Blues": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "Funk": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.2}, "hi": {"thr": -20, "rat": 2.0}, "glue": "Normal"},
    "Gospel": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -18, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},

    # 록/메탈
    "Rock": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.2}, "hi": {"thr": -20, "rat": 2.0}, "glue": "Normal"},
    "Metal": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -16, "rat": 2.5}, "hi": {"thr": -18, "rat": 2.0}, "glue": "Strong"},
    "Punk": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -16, "rat": 2.5}, "hi": {"thr": -18, "rat": 2.0}, "glue": "Strong"},
    "Grunge": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -18, "rat": 2.5}, "hi": {"thr": -20, "rat": 2.0}, "glue": "Strong"},

    # 클래식/앰비언트
    "Classical": {"low": {"thr": -22, "rat": 1.2}, "mid": {"thr": -24, "rat": 1.1}, "hi": {"thr": -26, "rat": 1.05}, "glue": "Light"},
    "Ambient": {"low": {"thr": -22, "rat": 1.2}, "mid": {"thr": -24, "rat": 1.1}, "hi": {"thr": -26, "rat": 1.05}, "glue": "Light"},

    # 월드뮤직
    "Country": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "Reggae": {"low": {"thr": -14, "rat": 2.5}, "mid": {"thr": -20, "rat": 2.2}, "hi": {"thr": -24, "rat": 1.8}, "glue": "Normal"},
    "Latin": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.2}, "hi": {"thr": -22, "rat": 2.0}, "glue": "Normal"},
    "Afrobeat": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.2}, "hi": {"thr": -22, "rat": 2.0}, "glue": "Normal"},
    "Disco": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.2}, "hi": {"thr": -20, "rat": 2.0}, "glue": "Normal"},
    
    "Default": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.5}, "hi": {"thr": -22, "rat": 1.2}, "glue": "Normal"}
}

# 3. 메뉴 구조
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

# 4. 마스터링 코어 (3밴드 개별 Ratio 적용 로직)
def run_mastering_process(audio, sr, genre_name, target_lufs, intensity):
    g_key = genre_name.strip()
    data = GENRE_DATA.get(g_key, GENRE_DATA["Default"])
    
    # 공통 EQ 설정
    eq = Pedalboard([
        HighpassFilter(25),
        PeakFilter(60, gain_db=1.0, q=0.7), PeakFilter(150, gain_db=2.0, q=0.7),
        PeakFilter(400, gain_db=1.0, q=0.7), PeakFilter(2500, gain_db=-1.0, q=0.7),
        PeakFilter(8000, gain_db=-1.0, q=0.7)
    ])
    
    # 강도 가중치
    mult = {"Light": 0.7, "Normal": 1.0, "Strong": 1.4}.get(intensity, 1.0)
    glue_r = {"Light": 1.2, "Normal": 1.5, "Strong": 2.0}.get(data["glue"], 1.5)

    # 이펙트 체인 구성 (3밴드 개별 압축)
    board = Pedalboard([
        eq,
        # 1. 고음 대역 압축
        Compressor(threshold_db=data["hi"]["thr"], ratio=data["hi"]["rat"] * mult, attack_ms=10, release_ms=100),
        # 2. 중음 대역 압축
        Compressor(threshold_db=data["mid"]["thr"], ratio=data["mid"]["rat"] * mult, attack_ms=20, release_ms=200),
        # 3. 저음 대역 압축
        Compressor(threshold_db=data["low"]["thr"], ratio=data["low"]["rat"] * mult, attack_ms=30, release_ms=300),
        # 4. 전체 Glue
        Compressor(threshold_db=-20, ratio=glue_r, attack_ms=40, release_ms=400),
        Limiter(threshold_db=-0.5)
    ])
    
    meter = pyln.Meter(sr)
    current_lufs = meter.integrated_loudness(audio.T)
    final_gain = target_lufs - current_lufs
    
    final_chain = Pedalboard([board, Gain(final_gain), Limiter(threshold_db=-0.1)])
    return final_chain(audio, sr)

# 5. UI 및 실행 로직
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stSelectbox div[data-baseweb="select"] div { color: #00ff88 !important; font-weight: 600; }
    .step-header { color: #00ff88; font-weight: 800; font-size: 1.4rem; margin-top: 20px; }
    .stButton > button { background: linear-gradient(90deg, #00ff88, #00d4ff) !important; color: #000000 !important; font-weight: 800 !important; height: 50px !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

st.title("🎵 Kelly AI Mastering v5.0")

st.markdown('<div class="step-header">STEP 1. 오디오 파일 업로드</div>', unsafe_allow_html=True)
files = st.file_uploader("Upload", type=["wav", "mp3"], accept_multiple_files=True, label_visibility="collapsed")

st.markdown('<div class="step-header">STEP 2. 마스터링 설정</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown("**🎯 장르**")
    sel_genre = st.selectbox("G", full_menu, index=9, label_visibility="collapsed") # 기본값 Lo-fi 근처 세팅
with c2:
    st.markdown("**💾 형식**")
    out_ext = st.selectbox("F", ["wav", "mp3", "flac"], label_visibility="collapsed")
with c3:
    st.markdown("**🔊 음압(LUFS)**")
    target_lufs = st.selectbox("L", [-14, -13, -11, -9], index=1, label_visibility="collapsed")
with c4:
    st.markdown("**⚡ 강도**")
    mode = st.selectbox("I", ["Light", "Normal", "Strong"], index=1, label_visibility="collapsed")

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
                # 정밀 연산 실행
                mastered_audio = run_mastering_process(audio, af.samplerate, sel_genre, target_lufs, mode)
                out_io = io.BytesIO()
                with AudioFile(out_io, 'w', af.samplerate, af.num_channels, format=out_ext) as o:
                    o.write(mastered_audio)
                st.success(f"✅ {f.name} 완료!")
                st.audio(out_io.getvalue())
                st.download_button(f"Download {f.name}", out_io.getvalue(), file_name=f"Master_{f.name}.{out_ext}")
            progress_bar.progress((idx + 1) / len(files))
        status_text.text("모든 작업 완료!")
