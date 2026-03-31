import streamlit as st
import io
import zipfile
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter
from pedalboard.io import AudioFile

# 1. 페이지 설정 (가장 먼저 실행)
st.set_page_config(page_title="Kelly AI Mastering v2", layout="wide")

# 2. 캐싱 로직 (앱이 느려지는 것을 방지하는 핵심 엔진)
@st.cache_data(show_spinner=False)
def process_audio_engine(file_bytes, target_lufs, comp_db, out_ext):
    """오디오 처리를 별도 함수로 분리하여 메모리 효율 극대화"""
    try:
        with AudioFile(io.BytesIO(file_bytes)) as f:
            audio = f.read(f.frames)
            samplerate = f.samplerate
            
            # 마스터링 체인 최적화
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
    except Exception as e:
        return None

# 3. UI 및 디자인 (기존의 깔끔한 다크모드 유지)
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    .step-label { font-size: 1.2rem; font-weight: 700; margin: 20px 0 10px 0; color: #00ff88; }
    div[data-baseweb="select"] { background-color: #1a1c23 !important; border: 1px solid #3e4451 !important; }
</style>
""", unsafe_allow_html=True)

st.title("🎵 Kelly AI Mastering v2")
st.caption("Faster. Lighter. Better.")

# --- STEP 1: Upload ---
st.markdown('<div class="step-label">STEP 1. Upload Tracks</div>', unsafe_allow_html=True)
files = st.file_uploader("Upload WAV/MP3", type=["wav", "mp3"], accept_multiple_files=True, label_visibility="collapsed")

# --- STEP 2: Settings ---
st.markdown('<div class="step-label">STEP 2. Mastering Settings</div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)

with col1:
    lufs_val = st.select_slider("Target Loudness (LUFS)", options=[-14, -13, -11, -9], value=-14)
with col2:
    comp_val = st.select_slider("Compression Intensity", options=["Light", "Normal", "Strong"], value="Normal")
    comp_map = {"Light": -18, "Normal": -22, "Strong": -26}
with col3:
    ext_val = st.selectbox("Output Format", ["wav", "mp3", "flac"])

# --- STEP 3: Process ---
if st.button("🚀 START MASTERING", use_container_width=True, disabled=not files):
    results = []
    progress_bar = st.progress(0)
    
    for i, f in enumerate(files):
        # 캐싱된 엔진 호출 (이미 처리한 설정이면 즉시 반환됨)
        output = process_audio_engine(f.getvalue(), lufs_val, comp_map[comp_val], ext_val)
        if output:
            results.append({"name": f.name, "data": output})
        progress_bar.progress((i + 1) / len(files))
    
    st.success(f"✅ {len(results)} Tracks Mastered!")
    
    # 결과 출력
    for res in results:
        with st.expander(f"📥 {res['name']}"):
            st.audio(res['data'])
            st.download_button("Download", res['data'], file_name=f"Mastered_{res['name']}.{ext_val}")