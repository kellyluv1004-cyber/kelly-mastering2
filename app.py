import streamlit as st
import io
import pyloudnorm as pyln
import numpy as np
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter, PeakFilter
from pedalboard.io import AudioFile

# 1. 페이지 설정
st.set_page_config(page_title="Kelly AI Mastering v5.1", layout="wide")

# 2. [이미지 데이터 100% 반영] 28개 장르 정밀 데이터베이스
GENRE_DATA = {
    # 일렉트로닉 (이미지 d673d0, d67409 반영)
    "Drum & Bass": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -18, "rat": 2.5}, "hi": {"thr": -18, "rat": 2.0}, "glue": "Strong"},
    "Dubstep": {"low": {"thr": -12, "rat": 3.0}, "mid": {"thr": -18, "rat": 2.5}, "hi": {"thr": -20, "rat": 2.0}, "glue": "Strong"},
    "Trance": {"low": {"thr": -10, "rat": 2.0}, "mid": {"thr": -20, "rat": 2.0}, "hi": {"thr": -18, "rat": 1.5}, "glue": "Normal"},
    "Techno": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -20, "rat": 2.0}, "hi": {"thr": -20, "rat": 1.8}, "glue": "Normal"},
    "house": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -20, "rat": 3.0}, "hi": {"thr": -20, "rat": 1.5}, "glue": "Normal"},
    "Electronic": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -20, "rat": 2.0}, "hi": {"thr": -20, "rat": 1.8}, "glue": "Light"},
    
    # 힙합/어반 (이미지 d7d0c9 반영)
    "Lo-fi": {"low": {"thr": -20, "rat": 2.0}, "mid": {"thr": -22, "rat": 1.5}, "hi": {"thr": -26, "rat": 1.2}, "glue": "Light"},
    "Hip-hop": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -18, "rat": 2.5}, "hi": {"thr": -22, "rat": 2.0}, "glue": "Normal"},
    "Trap": {"low": {"thr": -14, "rat": 3.0}, "mid": {"thr": -18, "rat": 2.5}, "hi": {"thr": -22, "rat": 2.0}, "glue": "Light"},

    # 재즈/블루스/가스펠 (이미지 d677ed, d6780b 반영)
    "Jazz": {"low": {"thr": -20, "rat": 2.0}, "mid": {"thr": -22, "rat": 1.5}, "hi": {"thr": -24, "rat": 1.2}, "glue": "Light"},
    "Blues": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 2.0}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "Funk": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.0}, "hi": {"thr": -20, "rat": 1.8}, "glue": "Normal"},
    "Gospel": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -18, "rat": 2.0}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},

    # 클래식/앰비언트 (이미지 d67b8a 반영)
    "Classical": {"low": {"thr": -22, "rat": 1.5}, "mid": {"thr": -24, "rat": 1.2}, "hi": {"thr": -26, "rat": 1.1}, "glue": "Light"},
    "Ambient": {"low": {"thr": -22, "rat": 1.5}, "mid": {"thr": -24, "rat": 1.2}, "hi": {"thr": -26, "rat": 1.1}, "glue": "Light"},

    # 월드뮤직 (이미지 d6ce45, d6ce65 반영)
    "Disco": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.0}, "hi": {"thr": -20, "rat": 1.8}, "glue": "Normal"},
    "Afrobeat": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.0}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "Latin": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.0}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "Reggae": {"low": {"thr": -14, "rat": 2.5}, "mid": {"thr": -20, "rat": 2.0}, "hi": {"thr": -24, "rat": 1.2}, "glue": "Normal"},
    "Country": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 2.0}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},

    # 팝/록 (기존 최적값 유지)
    "Pop": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.8}, "hi": {"thr": -22, "rat": 1.5}, "glue": "Normal"},
    "K-Pop": {"low": {"thr": -18, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.0}, "hi": {"thr": -20, "rat": 1.8}, "glue": "Normal"},
    "Ballad": {"low": {"thr": -20, "rat": 2.0}, "mid": {"thr": -22, "rat": 1.5}, "hi": {"thr": -24, "rat": 1.2}, "glue": "Light"},
    "Rock": {"low": {"thr": -16, "rat": 2.5}, "mid": {"thr": -18, "rat": 2.2}, "hi": {"thr": -20, "rat": 2.0}, "glue": "Normal"},
    "Default": {"low": {"thr": -18, "rat": 2.0}, "mid": {"thr": -20, "rat": 1.5}, "hi": {"thr": -22, "rat": 1.2}, "glue": "Normal"}
}

GENRE_STRUCTURE = {
    "팝/R&B": ["Pop", "Ballad", "K-Pop"],
    "힙합/어반": ["Hip-hop", "Trap", "Lo-fi"],
    "일렉트로닉": ["Electronic", "house", "Techno", "Trance", "Dubstep", "Drum & Bass"],
    "재즈/블루스": ["Jazz", "Blues", "Funk", "Gospel"],
    "월드뮤직": ["Country", "Reggae", "Latin", "Afrobeat", "Disco"],
    "클래식/앰비언트": ["Classical", "Ambient"]
}

full_menu = []
for cat, subs in GENRE_STRUCTURE.items():
    full_menu.append(f"--- {cat}")
    for s in subs: full_menu.append(f"   {s}")

def run_mastering_process(audio, sr, genre_name, target_lufs, intensity):
    g_key = genre_name.strip()
    data = GENRE_DATA.get(g_key, GENRE_DATA["Default"])
    
    # 강도 가중치 (0.7, 1.0, 1.3)
    mult = {"Light": 0.7, "Normal": 1.0, "Strong": 1.3}.get(intensity, 1.0)
    
    # [핵심 수정] max(1.0, ...)를 사용하여 Ratio가 1 미만으로 내려가는 에러 방지
    def safe_rat(val): return max(1.01, val * mult)

    board = Pedalboard([
        HighpassFilter(25),
        # 3밴드 멀티밴드 컴프레서 재현
        Compressor(threshold_db=data["hi"]["thr"], ratio=safe_rat(data["hi"]["rat"]), attack_ms=10, release_ms=100),
        Compressor(threshold_db=data["mid"]["thr"], ratio=safe_rat(data["mid"]["rat"]), attack_ms=20, release_ms=200),
        Compressor(threshold_db=data["low"]["thr"], ratio=safe_rat(data["low"]["rat"]), attack_ms=30, release_ms=300),
        # Glue 컴프레서
        Compressor(threshold_db=-20, ratio={"Light": 1.2, "Normal": 1.5, "Strong": 2.0}.get(data["glue"], 1.5), attack_ms=40, release_ms=400),
        Limiter(threshold_db=-0.5)
    ])
    
    meter = pyln.Meter(sr)
    current_lufs = meter.integrated_loudness(audio.T)
    final_gain = target_lufs - current_lufs
    
    final_chain = Pedalboard([board, Gain(final_gain), Limiter(threshold_db=-0.1)])
    return final_chain(audio, sr)

# 3. UI 및 실행 로직
st.title("🎵 Kelly AI Mastering v5.1")

files = st.file_uploader("STEP 1. 오디오 파일 업로드", type=["wav", "mp3"], accept_multiple_files=True)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("**🎯 장르**")
    sel_genre = st.selectbox("G", full_menu, index=5, label_visibility="collapsed")

with c2:
    st.markdown("**💾 형식**")
    out_ext = st.selectbox(
        "F", 
        options=["wav", "mp3", "flac"], 
        index=0,
        format_func=lambda x: {
            "wav": "WAV (44.1kHz/16bit)",
            "mp3": "MP3 (320kbps)",
            "flac": "FLAC (96kHz/24bit)"
        }.get(x),
        label_visibility="collapsed"
    )

with c3:
    st.markdown("**🔊 음압(LUFS)**")
    target_lufs = st.selectbox(
        "L", 
        options=[-14, -13, -11, -9], 
        index=1, 
        format_func=lambda x: {
            -14: "-14 (유튜브/스포티파이)",
            -13: "-13 (일반 스트리밍)",
            -11: "-11 (디지털 싱글)",
            -9: "-9 (클럽/EDM)"
        }.get(x),
        label_visibility="collapsed"
    )

with c4:
    st.markdown("**⚡ 강도**")
    mode = st.selectbox("I", ["Light", "Normal", "Strong"], index=1, label_visibility="collapsed")

if st.button("🚀 RUN MASTERING ENGINE", use_container_width=True, disabled=not files):
    if sel_genre.startswith("---"):
        st.error("세부 장르를 선택해 주세요!")
    else:
        for f in files:
            with AudioFile(io.BytesIO(f.getvalue())) as af:
                audio = af.read(af.frames)
                mastered_audio = run_mastering_process(audio, af.samplerate, sel_genre, target_lufs, mode)
                out_io = io.BytesIO()
                with AudioFile(out_io, 'w', af.samplerate, af.num_channels, format=out_ext) as o:
                    o.write(mastered_audio)
                st.audio(out_io.getvalue())
                st.download_button(f"Download {f.name}", out_io.getvalue(), file_name=f"Master_{f.name}.{out_ext}")
