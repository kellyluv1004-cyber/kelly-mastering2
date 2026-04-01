import streamlit as st
import io
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter, HighShelfFilter, LowShelfFilter
from pedalboard.io import AudioFile

# 1. 페이지 설정 및 세션 초기화
st.set_page_config(page_title="Kelly AI Mastering Studio", layout="centered")

if 'mastered_results' not in st.session_state:
    st.session_state.mastered_results = []

# 2. 고성능 부드러운 마스터링 엔진 (v2.5 Pure Sound)
def get_safe_mastering_chain(target_lufs, comp_mode, genre_name):
    # 장르별 부드러운 EQ 세팅 (소리가 뻑뻑해지는 것을 방지)
    low_gain, high_gain = 0, 0
    g = genre_name.lower()
    if any(x in g for x in ["lo-fi", "acoustic", "classical", "ambient"]):
        low_gain, high_gain = 1.2, -1.5  # 따뜻하고 부드러운 톤
    elif any(x in g for x in ["hip-hop", "trap", "electronic", "dance"]):
        low_gain, high_gain = 1.8, 0.5   # 저음 타격감 강조
    elif any(x in g for x in ["pop", "k-pop", "r&b"]):
        low_gain, high_gain = 0.5, 1.2   # 선명한 보컬

    # 압축 설정 (낮은 Ratio로 자연스러운 다이내믹 유지)
    comp_settings = {
        "🌙 Light": {"thresh": -16, "ratio": 1.5, "attack": 25}, 
        "⚡ Normal": {"thresh": -20, "ratio": 2.2, "attack": 15}, 
        "🔥 Strong": {"thresh": -24, "ratio": 3.0, "attack": 10}
    }
    c = comp_settings.get(comp_mode, comp_settings["⚡ Normal"])

    return Pedalboard([
        HighpassFilter(30),
        LowShelfFilter(cutoff_frequency_hz=150, gain_db=low_gain),
        HighShelfFilter(cutoff_frequency_hz=5000, gain_db=high_gain),
        # 부드러운 컴프레션 (Knee가 부드럽게 작용하도록 낮은 Ratio 사용)
        Compressor(threshold_db=c["thresh"], ratio=c["ratio"], attack_ms=c["attack"], release_ms=200),
        # 투명한 리미팅 (디지털 잡음 방지 위해 -1.0dB 여유)
        Limiter(threshold_db=-1.0, release_ms=100)
    ])

@st.cache_data(show_spinner=False)
def process_audio_engine(file_bytes, target_lufs, comp_mode, out_ext, genre_name):
    try:
        with AudioFile(io.BytesIO(file_bytes)) as f:
            audio = f.read(f.frames)
            samplerate = f.samplerate
            
            # 1단계: 현재 음량 측정
            meter = pyln.Meter(samplerate)
            curr_lufs = meter.integrated_loudness(audio.T)
            
            # 2단계: 엔진 적용
            chain = get_safe_mastering_chain(target_lufs, comp_mode, genre_name)
            
            # 3단계: 최종 음량 보정 및 피크 방지
            board = Pedalboard([
                chain,
                Gain(target_lufs - curr_lufs), 
                Limiter(threshold_db=-0.1)
            ])
            
            processed = board(audio, samplerate)
            out_io = io.BytesIO()
            with AudioFile(out_io, 'w', samplerate, f.num_channels, format=out_ext) as o:
                o.write(processed)
            return out_io.getvalue()
    except:
        return None

# 3. UI 스타일링 (디자인 유지)
st.markdown("""
<style>
    .stApp { background-color: #1a1c2c; color: #ffffff; }
    .label-text { font-size: 0.9rem; font-weight: 600; color: #a0a0c0; margin-bottom: 8px; margin-top: 22px; }
    [data-testid="stFileUploaderDropzone"] button { background-color: #ffffff !important; color: #000000 !important; font-weight: 700 !important; }
    [data-testid="stRadio"] > div { display: flex !important; flex-direction: row !important; gap: 12px !important; }
    [data-testid="stRadio"] label { flex: 1; background: #252844; border: 1px solid #3d4163; border-radius: 10px; padding: 12px 5px; text-align: center; cursor: pointer; }
    [data-testid="stRadio"] label:has(input:checked) { border-color: #00ff88; color: #00ff88 !important; }
    [data-testid="stRadio"] input { display: none !important; }
    .stButton > button { background: #3e4461 !important; color: #ffffff !important; width: 100%; height: 52px; font-weight: 700; border-radius: 10px; margin-top: 25px; }
    .stButton > button:hover:not(:disabled) { background: #00ff88 !important; color: #000000 !important; }
</style>
""", unsafe_allow_html=True)

st.title("켈리의 AI 마스터링 스튜디오")
st.caption("Kelly Studio Engine v2.5 | Pure Analog Sound")

# 4. UI 레이아웃
st.markdown('<p class="label-text">음악 파일</p>', unsafe_allow_html=True)
uploaded_files = st.file_uploader("Upload", type=["wav", "mp3"], accept_multiple_files=True, label_visibility="collapsed")

st.markdown('<p class="label-text">장르 프리셋</p>', unsafe_allow_html=True)
genre_list = [
    "POP", "Ballad", "K-POP", "J-POP", "R&B", "Soul", "Indie",
    "Hip-Hop", "Trap", "Lo-Fi", "Rock", "Metal", "Punk", "Grunge",
    "Electronic", "House", "Techno", "Tranco", "Dubstep", "Drum & Bass",
    "Jazz", "Blues", "Funk", "Gaspel", "Classical", "Ambient",
    "Country", "Reggae", "Latin", "Afrobeat", "Disco"
]
selected_genre = st.selectbox("Genre", genre_list, label_visibility="collapsed")

st.markdown('<p class="label-text">출력 형식</p>', unsafe_allow_html=True)
out_ext_raw = st.selectbox("Format", ["WAV · 16bit 44.1kHz", "MP3 · 320kbps", "FLAC · 24bit 96kHz"], label_visibility="collapsed")
out_ext = "mp3" if "MP3" in out_ext_raw else ("flac" if "FLAC" in out_ext_raw else "wav")

st.markdown('<p class="label-text">LUFS 타겟</p>', unsafe_allow_html=True)
target_lufs_raw = st.selectbox("LUFS", ["Streaming –13", "YouTube –14", "Standard –11", "Loud –9"], label_visibility="collapsed")
target_lufs = -float(target_lufs_raw.split("–")[1])

st.markdown('<p class="label-text">압축 강도 (뻑뻑하면 Light 추천)</p>', unsafe_allow_html=True)
comp_mode = st.radio("Compression", ["🌙 Light", "⚡ Normal", "🔥 Strong"], label_visibility="collapsed", index=1)

# 5. 실행 로직
if st.button("AI 마스터링 시작", disabled=not uploaded_files):
    st.session_state.mastered_results = []
    with st.spinner(f"Processing {selected_genre} style..."):
        for f in uploaded_files:
            data = process_audio_engine(f.getvalue(), target_lufs, comp_mode, out_ext, selected_genre)
            if data:
                st.session_state.mastered_results.append({"name": f.name, "data": data, "ext": out_ext})

# 6. 결과 출력
if st.session_state.mastered_results:
    st.success("✓ 소리가 더 부드러워진 마스터링이 완료되었습니다!")
    for idx, res in enumerate(st.session_state.mastered_results):
        with st.expander(f"📥 {res['name']}", expanded=True):
            st.audio(res['data'])
            st.download_button(label=f"저장 ({res['ext'].upper()})", data=res['data'], 
                               file_name=f"Mastered_{res['name']}.{res['ext']}", key=f"dl_{idx}")
    
    if st.button("🔄 새로운 작업 시작하기"):
        st.session_state.mastered_results = []
        st.rerun()
