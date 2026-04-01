import streamlit as st
import io
import zipfile
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter, HighShelfFilter, LowShelfFilter
from pedalboard.io import AudioFile

# --- 엔진: 소리 질감 개선 (Soft Knee & Multi-stage Gain) ---
def get_safe_mastering_chain(target_lufs, comp_mode, genre_name):
    # 장르별 부드러운 EQ 세팅
    low_gain, high_gain = 0, 0
    g = genre_name.lower()
    if "lo-fi" in g or "acoustic" in g:
        low_gain, high_gain = 1.2, -1.5 # 따뜻하고 부드럽게
    elif "hip-hop" in g or "trap" in g:
        low_gain, high_gain = 2.0, 0.5 # 저음 강조
        
    # 압축 강도 세밀화 (뻑뻑함 방지)
    comp_settings = {
        "🌙  Light": {"thresh": -16, "ratio": 1.5}, 
        "⚡  Normal": {"thresh": -20, "ratio": 2.2}, 
        "🔥  Strong": {"thresh": -24, "ratio": 3.0}
    }
    c = comp_settings.get(comp_mode, comp_settings["⚡  Normal"])

    return Pedalboard([
        HighpassFilter(30),
        # 1차 부드러운 톤 조절
        LowShelfFilter(cutoff_frequency_hz=150, gain_db=low_gain),
        HighShelfFilter(cutoff_frequency_hz=5000, gain_db=high_gain),
        # 2차 부드러운 압축 (낮은 Ratio로 뻑뻑함 해소)
        Compressor(threshold_db=c["thresh"], ratio=c["ratio"], attack_ms=15, release_ms=200),
        # 3차 정밀 게인 매칭
        Gain(target_lufs + 1.0), # 내부 헤드룸 확보 후 매칭
        # 4차 투명한 리미팅 (잡음 방지)
        Limiter(threshold_db=-1.0, release_ms=100) 
    ])

# --- Streamlit UI 및 실행 로직 ---
# (기본 UI 구조는 유지하며 엔진만 교체)
@st.cache_data(show_spinner=False)
def process_audio_v25(file_bytes, target_lufs, comp_mode, out_ext, genre_name):
    try:
        with AudioFile(io.BytesIO(file_bytes)) as f:
            audio = f.read(f.frames)
            # 현재 음량 측정
            meter = pyln.Meter(f.samplerate)
            curr_lufs = meter.integrated_loudness(audio.T)
            
            # 엔진 적용
            chain = get_safe_mastering_chain(target_lufs, comp_mode, genre_name)
            
            # 최종 음량 보정 포함
            board = Pedalboard([
                chain,
                Gain(target_lufs - curr_lufs), 
                Limiter(threshold_db=-0.1)
            ])
            
            processed = board(audio, f.samplerate)
            out_io = io.BytesIO()
            with AudioFile(out_io, 'w', f.samplerate, f.num_channels, format=out_ext) as o:
                o.write(processed)
            return out_io.getvalue()
    except Exception as e:
        return None

# [이하 UI 코드는 v2.4와 동일하게 유지하되 위 함수 호출로 변경]
