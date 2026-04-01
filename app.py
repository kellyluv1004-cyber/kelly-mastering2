# STEP 2. 마스터링 설정 (오타 수정 버전)
st.markdown('<div class="step-header">STEP 2. 마스터링 설정</div>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown("**🎯 장르**")
    sel_genre = st.selectbox("G", full_menu, index=0, label_visibility="collapsed")

with c2:
    st.markdown("**💾 형식**")
    st.markdown('<span class="sub-label">WAV/MP3/FLAC</span>', unsafe_allow_html=True)
    out_ext = st.selectbox("F", ["wav", "mp3", "flac"], label_visibility="collapsed")

with c3:
    st.markdown("**🔊 음압(LUFS)**")
    st.markdown('<span class="sub-label">추천: -14 ~ -13</span>', unsafe_allow_html=True)
    # 변수 이름을 'target_lufs'로 확실히 지정했습니다.
    target_lufs = st.selectbox("L", [-14, -13, -11, -9], index=1, label_visibility="collapsed")

with c4:
    st.markdown("**⚡ 강도**")
    st.markdown('<span class="sub-label">사운드 압축 정도</span>', unsafe_allow_html=True)
    mode = st.selectbox("I", ["Light", "Normal", "Strong"], index=1, label_visibility="collapsed")

# 6. 실행 로직 (에러 수정 및 자동 연동)
if st.button("🚀 RUN MASTERING ENGINE", use_container_width=True, disabled=not files):
    if sel_genre.startswith("---"):
        st.error("세부 장르를 선택해 주세요!")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, f in enumerate(files):
            status_text.text(f"⏳ {f.name} 처리 중... ({idx+1}/{len(files)})")
            
            with AudioFile(io.BytesIO(f.getvalue())) as af:
                audio = af.read(af.frames)
                
                # 여기서 target_lufs와 mode(강도)가 에러 없이 전달됩니다.
                mastered_audio = run_mastering_process(audio, af.samplerate, sel_genre, target_lufs, mode)
                
                out_io = io.BytesIO()
                with AudioFile(out_io, 'w', af.samplerate, af.num_channels, format=out_ext) as o:
                    o.write(mastered_audio)
                
                st.success(f"✅ {f.name} 완료!")
                st.audio(out_io.getvalue())
                st.download_button(f"Download {f.name}", out_io.getvalue(), file_name=f"Mastered_{f.name}.{out_ext}")
            
            progress_bar.progress((idx + 1) / len(files))
        
        status_text.text("모든 마스터링 작업이 완료되었습니다! 🎉")
