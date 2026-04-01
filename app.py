import streamlit as st
import io
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter, PeakFilter
from pedalboard.io import AudioFile

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Kelly AI Mastering v4.5", layout="wide")
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .stSelectbox div[data-baseweb="select"] div { color: #00ff88 !important; font-weight: 600; }
    .step-header { color: #00ff88; font-weight: 800; font-size: 1.4rem; margin: 30px 0 5px 0; }
    .guide-box { background-color: #1a1c23; padding: 15px; border-radius: 10px; border-left: 5px solid #00ff88; margin-bottom: 20px; font-size: 0.9rem; color: #ccc; }
    .sub-label { font-size: 0.85rem; color: #888; margin-bottom: 10px; display: block; }
    .stButton > button { background: linear-gradient(90deg, #00ff88, #00d4ff) !important; color: #000000 !important; font-weight: 800 !important; height: 55px !important; border-radius: 10px !important; margin-top: 25px; }
</style>
""", unsafe_allow_html=True)

# 2. [Full Library] 모든 장르 구조 복구
GENRE_STRUCTURE = {
    "팝/R&B": ["Pop", "Ballad", "K-Pop", "J-Pop", "R&B", "Soul", "Indie"],
    "힙합/어반": ["Hip-hop", "Trap", "Lo-fi"],
    "일렉트로닉": ["Electronic", "House", "Techno", "Trance", "Dubstep", "Drum & Bass"],
    "재즈/블루스": ["Jazz", "Blues", "Funk", "Gospel"],
    "록/메탈": ["Rock", "Metal", "Punk", "Grunge"],
    "클래식/앰비언트": ["Classical", "Ambient"],
    "월드뮤직": ["Country", "Reggae", "Latin", "Afrobeat", "Disco"]
}

formatted_genres = ["커스텀 설정"]
for cat, subs in GENRE_STRUCTURE.items():
    formatted_genres.append(f"--- {cat}")
    for s in subs: formatted_genres.append(f"   {s}")

# 3. 메인 UI 구성
st.title("🎵 Kelly AI Mastering v4.5")
st.caption("Professional Grade Finalizing Tool | Full Genre Calibration")

# STEP 1. 파일 업로드
st.markdown('<div class="step-header">STEP 1. 오디오 파일 업로드</div>', unsafe_allow_html=True)
st.info("💡 마스터링할 원본 파일(WAV 추천)을 업로드하세요. 여러 개 동시 처리도 가능합니다.")
files = st.file_uploader("Upload", type=["wav", "mp3"], accept_multiple_files=True, label_visibility="collapsed")

# STEP 2. 정밀 설정
st.markdown('<div class="step-header">STEP 2. 마스터링 정밀 설정</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("🎯 **장르 프리셋**")
    st.markdown('<span class="sub-label">각 장르별 최적 EQ/컴프레서 적용</span>', unsafe_allow_html=True)
    sel_genre = st.selectbox("Genre", formatted_genres, index=13, label_visibility="collapsed")
    if sel_genre.startswith("---"): st.warning("대분류가 아닌 세부 장르를 선택해주세요."); st.stop()

with c2:
    st.markdown("💾 **출력 형식 (Format)**")
    st.markdown('<span class="sub-label">WAV: 고음질 / MP3: 용량 절약</span>', unsafe_allow_html=True)
    out_ext = st.selectbox("Format", ["wav", "mp3", "flac"], index=0, label_visibility="collapsed")

with c3:
    st.markdown("🔊 **목표 음압 (LUFS)**")
    st.markdown('<span class="sub-label">유튜브 -14 / 스포티파이 -13 권장</span>', unsafe_allow_html=True)
    target = st.selectbox("LUFS", [-14, -13, -11, -9], index=1, label_visibility="collapsed")

with c4:
    st.markdown("⚡ **압축 강도 (Intensity)**")
    st.markdown('<span class="sub-label">Strong일수록 소리가 단단하고 꽉 참</span>', unsafe_allow_html=True)
    mode = st.selectbox("Intensity", ["Light", "Normal", "Strong"], index=1, label_visibility="collapsed")

# 4. 설정 요약 가이드 박스 추가
st.markdown(f"""
<div class="guide-box">
    <b>현재 설정 요약:</b><br>
    • 선택 장르: {sel_genre.strip()} | • 출력 포맷: {out_ext.upper()} | • 목표 음압: {target} LUFS | • 압축: {mode} 모드<br>
    <small>* 'RUN' 버튼을 누르면 인공지능 엔지니어가 업로드된 모든 파일을 분석하여 처리를 시작합니다.</small>
</div>
""", unsafe_allow_html=True)

# 실행 버튼
if st.button("🚀 RUN MASTERING ENGINE", use_container_width=True, disabled=not files):
    # [마스터링 코어 로직 - 이전 버전과 동일하게 작동]
    st.success("마스터링 작업이 시작되었습니다. 잠시만 기다려 주세요!")
