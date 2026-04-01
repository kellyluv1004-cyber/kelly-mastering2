import streamlit as st
import io
import pyloudnorm as pyln
import numpy as np
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter
from pedalboard.io import AudioFile

# 1. 페이지 설정 및 다크모드 스타일 적용
st.set_page_config(page_title="Kelly AI Mastering v5.2", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    .stButton>button { border-radius: 5px; height: 3em; background-color: #4facfe; color: white; border: none; width: 100%; }
    hr { border-color: #333; }
    </style>
    """, unsafe_allow_html=True)

# 2. 장르 데이터베이스
GENRE_DATA = {
    "Lo-fi": {"low": {"thr": -20, "rat": 2.0}, "mid": {"thr": -22, "rat": 1.5}, "hi": {"thr": -26, "rat": 1.2}, "glue": "Light"},
    "Hip-hop": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -18, "rat": 2.5}, "hi": {"thr": -22, "rat": 2.0}, "glue": "Normal"},
    "Pop": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "K-Pop": {"low": {"thr": -18, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.0}, "hi": {"thr": -20, "rat": 1.8}, "glue": "Normal"},
    "Electronic": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -20, "rat": 2.0}, "hi": {"thr": -20, "rat": 1.8}, "glue": "Normal"},
    "Default": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.5}, "hi": {"thr": -22, "rat": 1.2}, "glue": "Normal"}
}

# 장르 메뉴 구성
full_menu = ["   Lo-fi", "   Hip-hop", "   Pop", "   K-Pop", "   Electronic"]

# 마스터링 엔진 함수 (에러 방지 safe_rat 적용)
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

# 3. UI 본문
st.title("🎵 Kelly AI Mastering v5.2")

# STEP 1
st.markdown("### STEP 1. 오디오 파일 업로드")
files = st.file_uploader("", type=["wav", "mp3"], accept_multiple_files=True, label_visibility="collapsed")

# STEP 2
st.write("---")
st.markdown("### STEP 2. 마스터링 설정")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("**🎯 장르**")
    sel_genre = st.selectbox("G", full_menu, index=0, label_visibility="collapsed")

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

# 실행 버튼
st.write("")
if st.button("🚀 RUN MASTERING ENGINE", disabled=not files):
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

# 새로 시작하기 (맨 하단)
st.write("---")
if st.button("🔄 모든 설정 초기화 (새로 시작하기)"):
    st.rerun()
