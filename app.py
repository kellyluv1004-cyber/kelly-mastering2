import streamlit as st
import io
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter, HighShelfFilter, LowShelfFilter
from pedalboard.io import AudioFile

# 페이지 설정
st.set_page_config(page_title="Kelly AI Mastering Studio", layout="centered")

# --- 장르별 엔진 세팅 로직 ---
def get_genre_settings(genre_name):
    # 기본값
    settings = {"ratio": 4, "low_gain": 0, "high_gain": 0, "hpf": 30}
    
    g = genre_name.lower()
    if any(x in g for x in ["pop", "r&b", "soul", "k-pop", "j-pop", "indie", "ballad"]):
        settings.update({"ratio": 3.5, "high_gain": 1.5, "hpf": 35}) # 보컬 선명도
    elif any(x in g for x in ["hip-hop", "trap", "lo-fi"]):
        settings.update({"ratio": 5, "low_gain": 2.5, "hpf": 30}) # 저음 타격감
    elif any(x in g for x in ["rock", "metal", "punk", "grunge"]):
        settings.update({"ratio": 4.5, "low_gain": 1.0, "high_gain": 1.0}) # 밀도감
    elif any(x in g for x in ["electronic", "house", "techno", "tranco", "dubstep", "drum & bass"]):
        settings.update({"ratio": 5.5, "low_gain": 2.0, "high_gain": 2.0, "hpf": 25}) # 화려한 엣지
    elif any(x in g for x in ["jazz", "blues", "funk", "gaspel"]):
        settings.update({"ratio": 2.5, "low_gain": 0.5, "high_gain": 0.5}) # 자연스러운 질감
    elif any(x in g for x in ["classical", "ambient"]):
        settings.update({"ratio": 1.5, "hpf": 20}) # 다이내믹 보존
    elif any(x in g for x in ["country", "reggae", "latin", "afrobeat", "disco"]):
        settings.update({"ratio": 3.0, "high_gain": 1.2}) # 리듬감 강조
        
    return settings

# --- 최적화된 마스터링 엔진 ---
@st.cache_data(show_spinner=False)
def process_audio_engine(file_bytes, target_lufs, comp_db, out_ext, genre_name):
    try:
        gs = get_genre_settings(genre_name)
        with AudioFile(io.BytesIO(file_bytes)) as f:
            audio = f.read(f.frames)
            
            # 장르별 특화 체인 구성
            board = Pedalboard([
                HighpassFilter(gs['hpf']),
                LowShelfFilter(cutoff_frequency_hz=150, gain_db=gs['low_gain']),
                HighShelfFilter(cutoff_frequency_hz=5000, gain_db=gs['high_gain']),
                Compressor(threshold_db=comp_db, ratio=gs['ratio']),
                Gain(target_lufs - pyln.Meter(f.samplerate).integrated_loudness(audio.T)),
                Limiter(threshold_db=-0.1)
            ])
            
            processed = board(audio, f.samplerate)
            out_io = io.BytesIO()
            with AudioFile(out_io, 'w', f.samplerate, f.num_channels, format=out_ext) as o:
                o.write(processed)
            return out_io.getvalue()
    except: return None

# --- UI 스타일링 (v2.2 유지 및 보강) ---
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
st.caption("Kelly Studio Engine v2.3 | True Genre Engine")

# --- UI 레이아웃 ---
st.markdown('<p class="label-text">음악 파일</p>', unsafe_allow_html=True)
uploaded_files = st.file_uploader("Upload", type=["wav", "mp3"], accept_multiple_files=True, label_visibility="collapsed")

st.markdown('<p class="label-text">장르 프리셋</p>', unsafe_allow_html=True)
# 사용자님이 주신 상세 장르 리스트 적용
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

st.markdown('<p class="label-text">3밴드 압축 강도</p>', unsafe_allow_html=True)
comp_mode = st.radio("Compression", ["🌙 Light", "⚡ Normal", "🔥 Strong"], label_visibility="collapsed", index=1)
comp_db = {"🌙 Light": -18, "⚡ Normal": -22, "🔥 Strong": -26}[comp_mode]

# --- 실행 ---
if st.button("AI 마스터링 시작", disabled=not uploaded_files):
    results = []
    with st.spinner(f"Processing for {selected_genre}..."):
        for f in uploaded_files:
            data = process_audio_engine(f.getvalue(), target_lufs, comp_db, out_ext, selected_genre)
            if data: results.append({"name": f.name, "data": data})
    
    if results:
        st.success(f"✓ {selected_genre} 스타일 마스터링 완료!")
        for res in results:
            with st.expander(f"📥 {res['name']}"):
                st.audio(res['data'])
                st.download_button(f"저장 ({out_ext.upper()})", res['data'], file_name=f"Mastered_{res['name']}.{out_ext}", key=res['name'])
        
        if st.button("🔄 다시 시작하기"): st.rerun()
