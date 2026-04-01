import streamlit as st
import io
import pyloudnorm as pyln
import numpy as np
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter
from pedalboard.io import AudioFile

# 1. 페이지 설정
st.set_page_config(page_title="Kelly AI Mastering v5.3", layout="wide")

# 다크모드 및 버튼 디자인 스타일
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stButton>button { border-radius: 5px; height: 3em; background-color: #4facfe; color: white; border: none; width: 100%; }
    hr { border-color: #333; }
    </style>
    """, unsafe_allow_html=True)

# 2. [전 장르 복구] 28개 장르 정밀 데이터베이스
GENRE_DATA = {
    # 팝/R&B
    "Pop": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "Ballad": {"low": {"thr": -20, "rat": 2.0}, "mid": {"thr": -22, "rat": 1.5}, "hi": {"thr": -24, "rat": 1.2}, "glue": "Light"},
    "K-Pop": {"low": {"thr": -18, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.0}, "hi": {"thr": -20, "rat": 1.8}, "glue": "Normal"},
    "J-Pop": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "R&B": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -20, "rat": 2.0}, "hi": {"thr": -22, "rat": 1.8}, "glue": "Normal"},
    "Soul": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "Indie": {"low": {"thr": -20, "rat": 1.5}, "mid": {"thr": -22, "rat": 1.3}, "hi": {"thr": -22, "rat": 1.1}, "glue": "Light"},

    # 힙합/어반 (이미지 수치 반영)
    "Hip-hop": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -18, "rat": 2.5}, "hi": {"thr": -22, "rat": 2.0}, "glue": "Normal"},
    "Trap": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -18, "rat": 2.5}, "hi": {"thr": -22, "rat": 2.0}, "glue": "Light"},
    "Lo-fi": {"low": {"thr": -20, "rat": 2.0}, "mid": {"thr": -22, "rat": 1.5}, "hi": {"thr": -26, "rat": 1.2}, "glue": "Light"},

    # 일렉트로닉 (이미지 수치 반영)
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

    # 클래식/월드
    "Classical": {"low": {"thr": -22, "rat": 1.2}, "mid": {"thr": -24, "rat": 1.1}, "hi": {"thr": -26, "rat": 1.05}, "glue": "Light"},
    "Ambient": {"low": {"thr": -22, "rat": 1.2}, "mid": {"thr": -24, "rat": 1.1}, "hi": {"thr": -26, "rat": 1.05}, "glue": "Light"},
    "Country": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "Reggae": {"low": {"thr": -14, "rat": 2.5}, "mid": {"thr": -20, "rat": 2.2}, "hi": {"thr": -24, "rat": 1.8}, "glue": "Normal"},
    "Latin": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.2}, "hi": {"thr": -22, "rat": 2.0}, "glue": "Normal"},

    "Default": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.5}, "hi": {"thr": -22, "rat": 1.2}, "glue": "Normal"}
}

# 메뉴 구조 (카테고리 분류)
GENRE_STRUCTURE = {
    "팝/R&B": ["Pop", "Ballad", "K-Pop", "J-Pop", "R&B", "Soul", "Indie"],
    "힙합/어반": ["Hip-hop", "Trap", "Lo-fi"],
    "일렉트로닉": ["Electronic", "House", "Techno", "Trance", "Dubstep", "Drum & Bass"],
    "재즈/블루스": ["Jazz", "Blues", "Funk", "Gospel"],
    "록/메탈": ["Rock", "Metal", "Punk"],
    "클래식/기타": ["Classical", "Ambient", "Country", "Reggae", "Latin"]
}

full_menu = []
for cat, subs in GENRE_STRUCTURE.items():
    full_menu.append(f"--- {cat}")
    for s in subs: full_menu.append(f"   {s}")

# 3. 마스터링 코어 함수
def run_mastering_process(audio, sr, genre_name, target_lufs, intensity):
    g_key = genre_name.strip()
    data = GENRE_DATA.get(g_key, GENRE_DATA["Default"])
    mult = {"Light": 0.7, "Normal": 1.0, "Strong": 1.3}.get(intensity, 1.0)
    
    def safe_rat(val): return max(1.01, val * mult)

    board = Pedalboard([
        HighpassFilter(25),
        Compressor(threshold_db=data["hi"]["thr"], ratio=safe_rat(data["hi"]["rat"]), attack_ms=10, release_ms=100),
        Compressor(threshold_db=data["mid"]["thr"], ratio=safe_rat(data["mid"]["rat"]), attack_ms=20, release_ms=200),
        Compressor(threshold_db=data["low"]["thr"], ratio=safe_rat(data["low"]["rat"]), attack_ms=30, release_ms=300),
        Limiter(threshold_db=-0.5)
    ])
    
    meter = pyln.Meter(sr)
    current_lufs = meter.integrated_loudness(audio.T)
    final_gain = target_lufs - current_lufs
    
    final_chain = Pedalboard([board, Gain(final_gain), Limiter(threshold_db=-0.1)])
    return final_chain(audio, sr)

# 4. UI 본문
st.title("🎵 Kelly AI Mastering v5.3")

st.markdown("### STEP 1. 오디오 파일 업로드")
files = st.file_uploader("", type=["wav", "mp3"], accept_multiple_files=True, label_visibility="collapsed")

st.write("---")
st.markdown("### STEP 2. 마스터링 설정")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("**🎯 장르**")
    sel_genre = st.selectbox("G", full_menu, index=10, label_visibility="collapsed") # Lo-fi 위치

with c2:
    st.markdown("**💾 출력 형식**")
    out_ext = st.selectbox("F", options=["wav", "mp3", "flac"], index=0,
        format_func=lambda x: {"wav": "WAV (44.1kHz/16bit)", "mp3": "MP3 (320kbps)", "flac": "FLAC (96kHz/24bit)"}.get(x),
        label_visibility="collapsed")

with c3:
    st.markdown("**🔊 음압(LUFS)**")
    target_lufs = st.selectbox("L", options=[-14, -13, -11, -9], index=1,
        format_func=lambda x: {-14: "-14 (유튜브/스포티파이)", -13: "-13 (스트리밍 표준)", -11: "-11 (디지털 싱글)", -9: "-9 (클럽/EDM)"}.get(x),
        label_visibility="collapsed")

with c4:
    st.markdown("**⚡ 강도**")
    mode = st.selectbox("I", ["Light", "Normal", "Strong"], index=1, label_visibility="collapsed")

st.write("")
if st.button("🚀 RUN MASTERING ENGINE", disabled=not files):
    if sel_genre.startswith("---"):
        st.error("세부 장르를 선택해 주세요!")
    else:
        for f in files:
            with st.status(f"🎧 {f.name} 처리 중..."):
                with AudioFile(io.BytesIO(f.getvalue())) as af:
                    audio = af.read(af.frames)
                    mastered_audio = run_mastering_process(audio, af.samplerate, sel_genre, target_lufs, mode)
                    out_io = io.BytesIO()
                    with AudioFile(out_io, 'w', af.samplerate, af.num_channels, format=out_ext) as o:
                        o.write(mastered_audio)
                    st.audio(out_io.getvalue())
                    st.download_button(f"📥 {f.name} 다운로드", out_io.getvalue(), file_name=f"Master_{f.name}.{out_ext}")

st.write("---")
if st.button("🔄 모든 설정 초기화 (새로 시작하기)"):
    st.rerun()
