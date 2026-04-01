# 3. UI 및 실행 로직
st.title("🎵 Kelly AI Mastering v5.2")

# 배경을 다크모드로 유지하고 버튼 디자인을 맞추는 스타일
st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: white; }
    div[data-testid="stExpander"] { background-color: #1e2127; border-radius: 10px; }
    .stButton>button { border-radius: 5px; height: 3em; background-color: #4facfe; color: white; border: none; }
    </style>
    """, unsafe_allow_html=True)

# STEP 1. 파일 업로드
files = st.file_uploader("STEP 1. 오디오 파일 업로드", type=["wav", "mp3"], accept_multiple_files=True)

# STEP 2. 설정 레이아웃
st.write("---")
st.markdown("### STEP 2. 마스터링 설정")
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("**🎯 장르**")
    sel_genre = st.selectbox("G", full_menu, index=5, label_visibility="collapsed")

with c2:
    st.markdown("**💾 출력 형식**")
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

# 실행 버튼
st.write("")
run_btn = st.button("🚀 RUN MASTERING ENGINE", use_container_width=True, disabled=not files)

if run_btn:
    if sel_genre.startswith("---"):
        st.error("세부 장르를 선택해 주세요!")
    else:
        for f in files:
            with st.status(f"🎧 {f.name} 처리 중...", expanded=True):
                with AudioFile(io.BytesIO(f.getvalue())) as af:
                    audio = af.read(af.frames)
                    # 위에서 정의한 마스터링 함수 호출
                    mastered_audio = run_mastering_process(audio, af.samplerate, sel_genre, target_lufs, mode)
                    
                    out_io = io.BytesIO()
                    with AudioFile(out_io, 'w', af.samplerate, af.num_channels, format=out_ext) as o:
                        o.write(mastered_audio)
                    
                    st.audio(out_io.getvalue())
                    st.download_button(f"📥 Download: {f.name}", out_io.getvalue(), file_name=f"Mastered_{f.name}.{out_ext}")

# 새로 시작하기 버튼 (맨 하단 배치)
st.write("")
if st.button("🔄 모든 설정 초기화 (새로 시작하기)", use_container_width=True):
    st.rerun()
