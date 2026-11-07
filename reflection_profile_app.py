    with left:
        if current > 0:
            st.button("← 이전 문항", use_container_width=True, on_click=previous_burnout_question, key="bat_previous")
    with right:
        if st.session_state.get(key) in (1, 2, 3, 4, 5):
            st.button("응답 완료 · 기본정보로" if current == len(BAT_ITEMS) - 1 else "다음 문항 →",
                      type="primary", use_container_width=True,
                      on_click=save_burnout_and_advance, args=(original,), key="bat_next")
    st.stop()


if st.session_state.page == "demographics":
    render_brand_bar()
    st.title("기본정보")
    st.markdown('<div class="notice">정확한 기관명은 수집하지 않습니다. 모든 항목은 범주형이며 각 문항에서 ‘응답하지 않음’을 선택할 수 있습니다.</div>', unsafe_allow_html=True)
    st.write("")
    selections = {}
    for key in ["gender", "age", "rank", "facility", "career", "hr_education", "mental_education"]:
        selections[key] = st.radio(
            DEMOGRAPHIC_LABELS[key],
            DEMOGRAPHIC_OPTIONS[key],
            index=None,
            key=f"demo_{key}",
        )
    complete_demo = all(value is not None for value in selections.values())
    if st.button("익명 자료 제출 및 결과 보기", type="primary", use_container_width=True, disabled=not complete_demo):
        st.session_state.demographics = selections
        try:
            save_research_response(st.session_state.answers, selections)
            st.session_state.research_saved = True
            st.session_state.page = "result"
            st.rerun()
        except Exception as error:
            st.error("자료를 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.")
            st.caption(f"관리자 확인용 오류: {error}")
            st.info("저장에 실패한 경우 응답은 제출된 것으로 처리되지 않습니다.")
    st.stop()


if st.session_state.page == "result":
    render_brand_bar()
    answers = st.session_state.answers
    scores = factor_means(answers)
    burnout = bat_scores(st.session_state.get("burnout_answers", {}))

    st.title("나의 자기점검 결과")
    if st.session_state.research_saved:
        st.success("익명 연구자료가 제출되었습니다.")
    st.caption("두 결과는 자기성찰을 위한 참고자료입니다. 인사평가나 진단에 사용하지 않습니다.")
    gam_tab, burnout_tab = st.tabs(["감·수·성 결과", "직무소진 결과"])

    with gam_tab:
        st.subheader("나의 응답 한눈에 보기")
        st.write(" · ".join(f"**{factor} {value:.2f}**" for factor, value in scores.items()))
        st.caption(PROFILE_NOTE)
        st.image(radar_png(scores), width=290)

        st.subheader("한 장면을 감·수·성으로 다시 보기")
        st.write(SCENE_PROMPT)
        for label, question in SCENE_QUESTIONS.items():
            st.markdown(f"**{label}**  \n{question}")
        st.subheader("다음 근무에서 해볼 한 가지")
        action_plan = st.text_area(
            "해보고 싶은 행동을 한 문장으로 적어 보세요. (선택)",
            placeholder="예: 안전이 확보되면 무엇이 불편한지 짧게 확인해 보겠습니다.",
            max_chars=300,
        )
        st.caption("작성한 행동계획은 내려받는 PDF에 포함됩니다.")
        with st.expander("내 응답에서 돌아볼 문항과 근거자료"):
            selected = {factor: item for _, factor, _, item in reflection_items(answers)}
            for factor in scores:
                if factor in selected:
                    st.write(f"{factor} · {selected[factor]}")
            st.markdown("**9개 내용영역과 연습 방향**")
            st.caption("문항의 내용 분류입니다. 별도 하위척도 점수로 해석하지 않습니다.")
            for name, guidance in SUBDOMAIN_FEEDBACK.items():
                st.write(f"**{name}** · {guidance}")
            st.markdown("**정신건강 관련 상황의 응답 경향**")
            mental_scores = mental_factor_means(answers)
            st.write(" · ".join(f"{factor} {value:.2f}" for factor, value in mental_scores.items()))
            st.caption("관련 문항 평균(1~4점)입니다. 영역별 문항 수는 감 3개, 수 3개, 성 2개입니다.")
            st.markdown(f"[감·수·성 예비척도 개발 논문]({SCALE_PAPER_URL})")
            st.markdown("[감·수·성 모델의 이론적 정립과 철학적 기초](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003245299)")
            st.markdown("[헌법 원리의 해석학적 탐색과 교육적 함의](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003327070)")

    with burnout_tab:
        st.subheader("나의 직무소진 경험")
        if burnout is None:
            st.info("직무소진 결과를 산출할 수 없습니다.")
        else:
            labels = [BURNOUT_NAMES[factor] for factor in burnout]
            values = list(burnout.values())
            fig = go.Figure(go.Bar(
                x=values, y=labels, orientation="h", marker_color="#409773",
                text=[f"{value:.2f}" for value in values], textposition="inside",
            ))
            fig.update_xaxes(range=[0, 5], dtick=1)
            fig.update_yaxes(autorange="reversed", automargin=True)
            fig.update_layout(height=265, margin=dict(l=12, r=12, t=10, b=35))
            st.plotly_chart(fig, use_container_width=True)
            st.caption(BURNOUT_NOTE)
            st.write(f"**{RECOVERY_QUESTION}**")
            with st.expander("영역 설명과 선행연구 참고값"):
                st.caption(REFERENCE_NOTE)
                for factor in burnout:
                    mean, sd = BAT_REFERENCE[factor]
                    st.markdown(f"**{BURNOUT_NAMES[factor]}** · {BAT_PLAIN_MEANINGS[factor]}")
                    st.caption(f"평균 {mean:.2f} · 평균 ± 1표준편차 {mean-sd:.2f}~{mean+sd:.2f}")

    st.download_button(
        "통합 PDF 내려받기", data=make_result_pdf(scores, action_plan, burnout),
        file_name="나의_감수성_직무소진_자기점검.pdf", mime="application/pdf",
        use_container_width=True,
    )
    if st.button("처음부터 다시 하기", use_container_width=True):
        reset_profile()

    st.markdown(
        '<div class="rights-footer">© 2026 이성덕. All rights reserved.<br>'
        '감·수·성 로고 상표출원(심사 중)</div>',
        unsafe_allow_html=True,
    )
