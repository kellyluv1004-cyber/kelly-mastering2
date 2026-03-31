import streamlit as st
import io
import zipfile
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter
from pedalboard.io import AudioFile

# 페이지 설정
st.set_page_config(page_title="Kelly AI Mastering Studio", layout="centered")

# --- 캐싱 엔진 ---
@st.cache_data(show_spinner=False)
def process_audio_engine(file_bytes, target_lufs, comp_db, out_ext):
    try:
        with AudioFile(io.BytesIO(file_bytes)) as f:
            audio = f.read(f.frames)
            board = Pedalboard([
                HighpassFilter(30),
                Compressor(threshold_db=comp_db, ratio=4),
                Gain(target_lufs - pyln.Meter(f.samplerate).integrated_loudness(audio.T)),
                Limiter(threshold_db=-0.1)
            ])
            processed = board(audio, f.samplerate)
            out_io = io.BytesIO()
            with AudioFile(out_io, 'w', f.samplerate, f.num_channels, format=out_ext) as o:
                o.write(processed)
            return out_io.getvalue()
    except: return None

# --- UI 스타일링 (최종 가시성 보정) ---
st.markdown("""
<style>
    .stApp { background-color: #1a1c2c; color: #ffffff; }
    .label-text { font-size: 0.9rem; font-weight: 600; color: #a0a0c0; margin-bottom: 8px; margin-top: 22px; }
    
    /* 업로드 버튼 글씨 색상 고정 (검은색) */
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border: none !important;
    }
    
    /* 압축 강도 라디오 버튼 가로 정렬 및 카드 스타일 */
    [data-testid="stRadio"] > div { 
        display: flex !important; 
        flex-direction: row !important; 
        gap: 12px !important; 
        margin-top: 5px !important;
    }
    [data-testid="stRadio"] label { 
        flex: 1 !important;
        background: #252844 !important; 
        border: 1px solid #3d4163 !important; 
        border-radius: 10px !important; 
        padding: 12px 5px !important;
        text-align: center !important;
        cursor: pointer !important;
        transition: 0.2s !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    [data-testid="stRadio"] label:hover { border-color: #00ff88 !important; }
    [data-testid="stRadio"] label:has(input:checked) { 
        background: #2e3a4e !important; 
        border-color: #00ff88 !important; 
        box-shadow: 0 0 10px rgba(0,255,136,0.1) !important;
    }
    [data-testid="stRadio"] label div[data-testid="stMarkdownContainer"] p { 
        color: #ffffff !important; 
        font-size: 0.9rem !important;
        font-weight: 600 !important;
    }
    [data-testid="stRadio"] label:has(input:checked) p { color: #00ff88 !important; }
    /* 라디오 원형 버튼 숨기기 */
    [data-testid="stRadio"] input { display: none !important; }

    /* 시작 버튼 디자인 */
    .stButton > button { 
        background: #3e4461 !important; color: #ffffff !important; border: none !important; 
        width: 100% !important; height: 52px !important; font-size: 1rem !important;
        font-weight: 700 !important; border-radius: 10px !important; margin-top: 25px !important;
    }
    .stButton > button:hover:not(:disabled) { background: #00ff88 !important; color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

st.title("켈리의 AI 마스터링 스튜디오")
st.caption("Kelly Studio Engine v2.2 | Faster & Lighter")

# --- UI 레이아웃 ---
st.markdown('<p class="label-text">음악 파일</p>', unsafe_allow_html=True)
uploaded_files = st.file_uploader("Upload", type=["wav", "mp3"], accept_multiple_files=True, label_visibility="collapsed")

st.markdown('<p class="label-text">장르 프리셋</p>', unsafe_allow_html=True)
genre = st.selectbox("Genre", ["Lo-Fi", "Pop", "Electronic", "Hip-Hop", "Rock", "Acoustic"], label_visibility="collapsed")

st.markdown('<p class="label-text">출력 형식</p>', unsafe_allow_html=True)
out_ext_raw = st.selectbox("Format", ["WAV · 16bit 44.1kHz", "MP3 · 320kbps", "FLAC · 24bit 96kHz"], label_visibility="collapsed")
out_ext = "mp3" if "MP3" in out_ext_raw else ("flac" if "FLAC" in out_ext_raw else "wav")

st.markdown('<p class="label-text">LUFS 타겟</p>', unsafe_allow_html=True)
target_lufs_raw = st.selectbox("LUFS", ["Streaming –13", "YouTube –14", "Standard –11", "Loud –9"], label_visibility="collapsed")
target_lufs = -float(target_lufs_raw.split("–")[1])

st.markdown('<p class="label-text">3밴드 압축 강도</p>', unsafe_allow_html=True)
comp_mode = st.radio("Compression", ["🌙 Light", "⚡ Normal", "🔥 Strong"], label_visibility="collapsed", index=1)
comp_db = {"🌙 Light": -18, "⚡ Normal": -22, "🔥 Strong": -26}[comp_mode]

# --- 실행 ---
if st.button("AI 마스터링 시작", disabled=not uploaded_files):
    results = []
    with st.spinner("Processing..."):
        for f in uploaded_files:
            data = process_audio_engine(f.getvalue(), target_lufs, comp_db, out_ext)
            if data: results.append({"name": f.name, "data": data})
    
    if results:
        st.success("✓ 마스터링 완료!")
        for res in results:
            with st.expander(f"📥 {res['name']}"):
                st.audio(res['data'])
                st.download_button(f"저장 ({out_ext.upper()})", res['data'], file_name=f"Mastered_{res['name']}.{out_ext}", key=res['name'])
        
        if st.button("🔄 다시 시작하기"): st.rerun()
