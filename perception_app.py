import streamlit as st
import pandas as pd
from datetime import datetime

# ---------------- 기본 설정 ----------------
st.set_page_config(
    page_title="정신질환 수용자 인식 설문조사",
    layout="wide"
)

st.title("교도관의 정신질환 수용자 인식 설문조사")

# 공통 척도 정의
LIKERT5 = [
    "1 - 매우 부동의",
    "2 - 부동의",
    "3 - 중립",
    "4 - 동의",
    "5 - 매우 동의",
]

SDIFF_7 = ["1", "2", "3", "4", "5", "6", "7"]

FREQ3 = [
    "1 - 항상 그렇다",
    "2 - 가끔 그렇다",
    "3 - 전혀 아니다",
]

YESNO3 = [
    "1 - 거의 없다",
    "2 - 가끔 있다",
    "3 - 매우 자주 있다",
]

TOTAL_SECTIONS = 7  # 태도, 관계, 소진, 인식, 교육, 보상, 인구학

# ---------------- 연구 설명 및 동의 ----------------
with st.expander("연구 설명 및 참여 동의", expanded=True):
    st.markdown(
        """
        #### 연구 설명

        - 연구과제명: **교도관의 정신질환 수용자 인식 및 감·수·성 인권감수성 지표 개발 연구**
        - 현재 설문: **정신질환 수용자 인식·태도·교육·직무소진 설문(감·수·성 27문항 제외)**

        이 설문은 교정시설에서 근무하는 교도관을 대상으로  
        정신질환 수용자에 대한 인식, 태도, 직무환경과 소진, 교육 경험 등을 파악하기 위한 것입니다.  
        설문 응답은 익명으로 처리되며, 연구 목적 외에는 사용되지 않습니다.

        - 참여는 **전적으로 자발적**입니다.
        - 언제든지 원하실 때 설문을 중단하실 수 있으며, 중단으로 인한 불이익은 없습니다.
        - 이름, 주민등록번호 등 직접적인 식별 정보는 수집하지 않습니다.
        - 보상을 원하시는 경우에 한해 휴대전화 번호를 선택적으로 입력하실 수 있습니다.
        """
    )

consent = st.checkbox("위 설명을 이해하였으며, 자발적으로 연구 참여에 동의합니다.")

if not consent:
    st.warning("연구 참여에 동의하셔야 설문을 진행하실 수 있습니다.")
    st.stop()

st.markdown("---")

# ============================================================
# Ⅰ. 정신문제 수용자와 일반 수용자에 대한 태도
# ============================================================
section = 1
st.header("Ⅰ. 정신문제 수용자와 일반 수용자에 대한 태도 (38문항)")
st.progress(section / TOTAL_SECTIONS)
st.caption(f"진행률: {section} / {TOTAL_SECTIONS} 섹션")

st.write(
    """
    각 문항은 **정신문제 수용자**와 **일반 수용자**에 대해 각각 응답해 주십시오.  
    응답: 1(매우 부동의) ~ 5(매우 동의)
    """
)

attitude_items = [
    "(정신문제) 수용자는 대부분의 사람들과 다르다.",
    "(정신문제) 수용자 중 실제로 위험한 사람은 소수에 불과하다.",
    "(정신문제) 수용자는 결코 변하지 않는다.",
    "대부분의 (정신문제) 수용자는 상황의 희생자이며 도움을 받을 자격이 있다.",
    "(정신문제) 수용자도 우리와 마찬가지로 감정을 가지고 있다.",
    "(정신문제) 수용자를 지나치게 신뢰하는 것은 현명하지 않다.",
    "나는 (정신문제) 수용자 중 많은 사람을 좋아한다.",
    "열악한 수용 환경은 (정신문제) 수용자를 더 부정적으로 만든다.",
    "(정신문제) 수용자는 호의가 계속되면 권리인 줄 안다.",
    "대부분의 (정신문제) 수용자는 지적능력이 부족하다.",
    "(정신문제) 수용자도 다른 사람들처럼 애정과 칭찬이 필요하다.",
    "(정신문제) 수용자에게 너무 많은 기대를 하는 것은 바람직하지 않다.",
    "(정신문제) 수용자의 교정·재활을 시도하는 것은 시간과 비용의 낭비다.",
    "(정신문제) 수용자는 진실을 말하지 않는다.",
    "(정신문제) 수용자는 다른 사람들과 크게 다르지 않다.",
    "(정신문제) 수용자를 대할 때는 항상 경계심을 가져야 한다.",
    "일반적으로 (정신문제) 수용자는 비슷한 방식으로 생각하고 행동한다.",
    "(정신문제) 수용자를 존중하면, 그도 존중으로 보답한다.",
    "(정신문제) 수용자는 자기 자신만 생각한다.",
    "나는 어떤 (정신문제) 수용자는 목숨을 맡길 만큼 신뢰할 수 있다고 생각한다.",
    "(정신문제) 수용자는 이성적인 설득에 귀 기울일 수 있다.",
    "대부분의 (정신문제) 수용자는 정직하게 살아갈 만큼 부지런하지 못하다.",
    "출소한 (정신문제) 수용자가 내 이웃으로 사는 것은 괜찮다.",
    "(정신문제) 수용자는 심성이 나쁘다.",
    "(정신문제) 수용자는 항상 누군가에게서 무엇인가를 얻으려 한다.",
    "대부분의 (정신문제) 수용자는 우리와 비슷한 가치관을 가지고 있다.",
    "나는 내 자녀가 출소한 (정신문제) 수용자와 교제하는 것을 절대 원하지 않는다.",
    "대부분의 (정신문제) 수용자는 사랑할 수 있는 능력이 있다.",
    "(정신문제) 수용자는 본질적으로 도덕적 기준이 부족하다.",
    "(정신문제) 수용자는 엄격하고 강한 규율 아래 있어야 한다.",
    "일반적으로 (정신문제) 수용자는 본질적으로 부정적 성향이 있다.",
    "대부분의 (정신문제) 수용자는 교정·재활될 수 있다.",
    "일부 (정신문제) 수용자는 꽤 좋은 사람들이다.",
    "나는 일부 (정신문제) 수용자와 어울리고 싶다.",
    "(정신문제) 수용자는 힘과 강압만을 존중한다.",
    "(정신문제) 수용자가 교도소에서 모범적으로 생활하면 가석방을 허용해야 한다.",
    "정신문제 수용자와 일반 수용자의 응답란 모두에 3-중립을 선택해 주세요. (읽음 여부 확인 문항)",
    "(정신문제) 수용자에게 인권적 처우가 중요하다.",
]

attitude_responses = {}
for i, text in enumerate(attitude_items, start=1):
    st.subheader(f"문항 {i}")
    st.markdown(text)
    c1, c2 = st.columns(2)
    with c1:
        attitude_responses[f"ATT_{i:02d}_MENTAL"] = st.selectbox(
            f"정신문제 수용자 - 문항 {i}",
            ["선택하세요"] + LIKERT5,
            key=f"att_m_{i}",
        )
    with c2:
        attitude_responses[f"ATT_{i:02d}_GENERAL"] = st.selectbox(
            f"일반 수용자 - 문항 {i}",
            ["선택하세요"] + LIKERT5,
            key=f"att_g_{i}",
        )

st.markdown("---")

# ============================================================
# Ⅱ. 수용자·동료·가족·의료팀과의 관계
# ============================================================
section = 2
st.header("Ⅱ. 수용자·동료·가족·의료(심리치료)팀과의 관계")
st.progress(section / TOTAL_SECTIONS)
st.caption(f"진행률: {section} / {TOTAL_SECTIONS} 섹션")

st.subheader("1. 관리하는 수용자와의 관계 (형용사 쌍)")

rel_items = [
    "통제할 수 있음 ↔ 통제할 수 없음",
    "실패함 ↔ 성공적임",
    "적극적임 ↔ 소극적임",
    "도울 수 없는 ↔ 도울 수 있는",
    "효과적임 ↔ 비효과적임",
    "힘이 없음 ↔ 힘이 있음",
    "자신감 있음 ↔ 자신감 부족함",
]

rel_responses = {}
for i, text in enumerate(rel_items, start=1):
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"정신문제 수용자 - {text}")
        rel_responses[f"REL_M_{i:02d}"] = st.selectbox(
            f"정신문제 수용자 관계 {i}",
            ["선택하세요"] + SDIFF_7,
            key=f"rel_m_{i}",
        )
    with c2:
        st.write(f"일반 수용자 - {text}")
        rel_responses[f"REL_G_{i:02d}"] = st.selectbox(
            f"일반 수용자 관계 {i}",
            ["선택하세요"] + SDIFF_7,
            key=f"rel_g_{i}",
        )

st.subheader("2. 동료 지지 관계")
peer_support_1 = st.selectbox("나는 동료를 지지한다.", ["선택하세요"] + FREQ3)
peer_support_2 = st.selectbox("나는 동료로부터 지지를 받는다.", ["선택하세요"] + FREQ3)

st.subheader("3. 가족 지지 관계")
family_view = st.selectbox(
    "가족들은 귀하가 교도소에서 근무하는 것에 대해 어떻게 느끼고 있습니까?",
    [
        "선택하세요",
        "매우 기쁘며 긍정적임",
        "대체로 긍정적임",
        "중립적임",
        "부정적이거나 걱정이 많음",
    ],
)
family_safety = st.selectbox(
    "가족들은 교도소에서 근무할 때 당신의 안전을 걱정하는 경우가 있습니까?",
    ["선택하세요"] + YESNO3,
)

st.subheader("4. 의료과 또는 심리치료과(팀)과의 상호관계")

med_items = [
    "나는 의료과 또는 심리치료과(팀) 직원들이 내가 알고 있는 것에 기초하여 제공하는 수용자 관련 정보에 대해 열린 태도를 보인다고 느낀다.",
    "나는 의료과 또는 심리치료과(팀) 직원들이 알면 도움이 될 만한 수용자 관련 정보를 관찰했다고 느낀다.",
    "의료과 또는 심리치료과(팀) 직원들은 수용자의 특정 행동이나 정신질환 징후를 살펴보는 방법에 대해 나에게 조언이나 훈련을 제공한 적이 있다.",
    "나는 의료과 또는 심리치료과(팀) 직원들과 대화하기가 쉽다고 느낀다.",
    "나는 수용자에 대해 우려가 생길 경우, 그를 의료과 또는 심리치료과(팀) 직원에게 의뢰할 수 있는 위치에 있다고 느낀다.",
]

med_responses = {}
for i, text in enumerate(med_items, start=1):
    med_responses[f"MED_{i:02d}"] = st.selectbox(
        text, ["선택하세요"] + LIKERT5, key=f"med_{i}"
    )

st.markdown("---")

# ============================================================
# Ⅲ. 직무소진 평가 (K-BAT)
# ============================================================
section = 3
st.header("Ⅲ. 직무소진 평가 (K-BAT)")
st.progress(section / TOTAL_SECTIONS)
st.caption(f"진행률: {section} / {TOTAL_SECTIONS} 섹션")

st.write("현재 귀하의 상태에 가장 가까운 정도를 선택해 주십시오. (1-매우 부동의 ~ 5-매우 동의)")

burnout_items = [
    "직장에서 나는 정신적으로 지친다.",
    "직장에서 내가 하는 모든 일은 상당한 노력을 요한다.",
    "피로 후, 기운을 회복하는 것이 어렵다.",
    "난 일을 할 때, 집중하기가 힘들다.",
    "아침에 일어나면, 직장에서 새로운 하루를 시작할 힘이 부족하다.",
    "직장에서 나는 적극적이고 싶지만, 왠지 그렇지 못한다.",
    "업무에 열중할 경우, 평소보다 빨리 지친다.",
    "업무가 끝난 후, 나는 정신적으로 지치고 진이 빠진다.",
    "직장에서 나는 내가 무엇을 하는지에 대해 생각하지 않고 기계적으로 일한다.",
    "나는 내가 하는 업무가 싫다.",
    "나는 내 일에 무관심하다.",
    "나는 내 업무가 다른 사람에게 어떠한 의미가 있을 지에 대해서 냉소적이다.",
    "나는 직장에서 한 가지 일에 집중하는 것이 힘들다.",
    "나는 직장에서 명료하게 생각하는 것이 힘들다.",
    "나는 직장에서 잘 까먹고 주의가 산만하다.",
    "직장에서 나는 체력적으로 지친다.",
    "직장에서 나는 뜻하지 않게 과하게 반응하곤 한다.",
    "나는 직장에서 다른 일에 신경 쓰다가 실수를 하곤 한다.",
    "직장에서 나는 내 감정을 다스릴 수가 없다.",
    "직장에서 내가 감정적으로 어떤 반응을 하는지 인식하지 못한다.",
    "직장에서 일이 내가 원하는 대로 흘러가지 않을 경우에 짜증이 난다.",
    "직장에서 나는 이유 없이 화가 나거나 슬퍼지곤 한다.",
]

burnout_responses = {}
for i, text in enumerate(burnout_items, start=1):
    burnout_responses[f"BO_{i:02d}"] = st.selectbox(
        text, ["선택하세요"] + LIKERT5, key=f"bo_{i}"
    )

st.markdown("---")

# ============================================================
# Ⅳ. 교도관의 인식 (4집단, 18 형용사)
# ============================================================
section = 4
st.header("Ⅳ. 교도관의 인식 (정신문제 수용자 / 일반 수용자 / 정신질환 일반인 / 일반인)")
st.progress(section / TOTAL_SECTIONS)
st.caption(f"진행률: {section} / {TOTAL_SECTIONS} 섹션")

st.write(
    """
    각 문항은 서로 반대되는 형용사 쌍으로 구성되어 있습니다.  
    - 1에 가까울수록 왼쪽 형용사, 7에 가까울수록 오른쪽 형용사에 더 가깝습니다.
    """
)

percep_items = [
    "안전한 ↔ 위험한",
    "해가 없는 ↔ 해로운",
    "비폭력적인 ↔ 폭력적인",
    "여유로운 ↔ 긴장된",
    "자기개념이 높은 ↔ 자기통제력이 낮은",
    "좋은 ↔ 나쁜",
    "예측 가능한 ↔ 예측 불가능한",
    "이해할 수 있는 ↔ 알기 힘든",
    "지적인 ↔ 지적수준이 낮은",
    "변할 수 있는 ↔ 변할 수 없는",
    "비공격적인 ↔ 공격적인",
    "충동이 낮은 ↔ 충동이 높은",
    "강한 ↔ 약한",
    "활동적인 ↔ 수동적인",
    "타인을 조종하지 않는 ↔ 타인을 조종하는",
    "합리적인 ↔ 비합리적인",
    "자신감 있는 ↔ 겁이 있는",
    "도덕적인 ↔ 도덕성이 낮은",
]

percep_responses = {}
for i, text in enumerate(percep_items, start=1):
    st.subheader(f"형용사 문항 {i}: {text}")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        percep_responses[f"P_MENTAL_{i:02d}"] = st.selectbox(
            "정신문제 수용자", ["선택하세요"] + SDIFF_7, key=f"p_m_{i}"
        )
    with c2:
        percep_responses[f"P_GENERAL_{i:02d}"] = st.selectbox(
            "일반 수용자", ["선택하세요"] + SDIFF_7, key=f"p_g_{i}"
        )
    with c3:
        percep_responses[f"P_MENTAL_GEN_{i:02d}"] = st.selectbox(
            "정신질환 일반인", ["선택하세요"] + SDIFF_7, key=f"p_mg_{i}"
        )
    with c4:
        percep_responses[f"P_GENERAL_GEN_{i:02d}"] = st.selectbox(
            "일반인", ["선택하세요"] + SDIFF_7, key=f"p_gg_{i}"
        )

st.markdown("---")

# ============================================================
# Ⅴ. 교육 경험 및 교육훈련 필요성
# ============================================================
section = 5
st.header("Ⅴ. 교육 경험 및 교육훈련 필요성")
st.progress(section / TOTAL_SECTIONS)
st.caption(f"진행률: {section} / {TOTAL_SECTIONS} 섹션")

st.subheader("1. 교육 경험 (중복 선택 가능)")
edu_experience = st.multiselect(
    "정신문제 수용자와 관련하여 받은 교육은 무엇인가요?",
    [
        "업무관련 정신질환 교육(직무교육)",
        "업무와 무관한 정신질환 교육(예: 대학교 강의나 외부 강의)",
        "인권(감수성) 교육",
        "기타 교육",
        "없음",
    ],
)

st.subheader("2. 교육 및 훈련 필요성")

edu_items = [
    "나는 (정신질환) 수용자를 다루는 데 필요한 추가적인 교육 훈련을 더 받고 싶다.",
    "(정신질환) 수용자는 별도의 시설에서 관리되어야 한다.",
    "지금까지 내가 받은 직무 교육은 (정신질환) 수용자를 관리하는 데 도움이 되었다.",
    "나는 (정신질환) 수용자의 인권보호에 필요한 추가적인 훈련을 받고 싶다.",
    "(정신질환) 수용자와 함께 일하는 것은 교도관 업무의 스트레스를 더 크게 만든다.",
]

edu_responses = {}
for i, text in enumerate(edu_items, start=1):
    edu_responses[f"EDU_{i:02d}"] = st.selectbox(
        text, ["선택하세요"] + LIKERT5, key=f"edu_{i}"
    )

st.markdown("---")

# ============================================================
# Ⅵ. 보상 관련 (선택 사항)
# ============================================================
section = 6
st.header("Ⅵ. 보상 관련 (선택 사항)")
st.progress(section / TOTAL_SECTIONS)
st.caption(f"진행률: {section} / {TOTAL_SECTIONS} 섹션")

st.write(
    "설문을 마치신 분들 중 일부를 추첨하여 소정의 모바일 커피 쿠폰을 드릴 예정입니다.\n"
    "보상을 원하시는 경우에만 휴대전화 번호를 입력해 주세요."
)

want_reward = st.radio(
    "보상(모바일 쿠폰) 추첨에 참여하시겠습니까?",
    ["아니요", "예"],
    index=0,
)
phone_number = ""
if want_reward == "예":
    phone_number = st.text_input("휴대전화 번호 (예: 010-0000-0000)")

st.markdown("---")

# ============================================================
# Ⅶ. 인구학적 정보 (맨 마지막)
# ============================================================
section = 7
st.header("Ⅶ. 인구학적 정보")
st.progress(section / TOTAL_SECTIONS)
st.caption(f"진행률: {section} / {TOTAL_SECTIONS} 섹션 (마지막)")

col1, col2 = st.columns(2)
with col1:
    gender = st.selectbox("1. 성별", ["선택하세요", "남", "여", "응답하지 않음"])
    age = st.number_input("2. 연령(만)", min_value=20, max_value=70, step=1)

with col2:
    years = st.number_input("3. 교정공무원 근무 연수(년)", min_value=0, max_value=40, step=1)

org = st.text_input("4. 근무지 (예: ○○교도소, ○○구치소 등)")
dept = st.text_input("5. 부서 (예: 경비과, 보안과, 의료과 등)")

freq_mental = st.selectbox(
    "6. 지난 6개월 동안 정신문제 수용자를 얼마나 대면하였는지요?",
    [
        "선택하세요",
        "거의 대면하지 않았다",
        "가끔 대면했다",
        "자주 대면했다",
        "매우 자주 대면했다",
    ],
)

st.text_area(
    "7. 현재 교도소에서 정신질환 수용자를 관리하는 데 가장 큰 장애물은 무엇이라고 생각하십니까?",
    key="barrier"
)
st.text_area(
    "8. 현재 교도소에서 정신질환 수용자의 관리를 향상시키기 위한 필요한 사항은 무엇이라고 생각하십니까?",
    key="improve"
)
st.text_area(
    "9. 현재 교도소에서 정신문제 수용자의 인권 보호에 가장 필요한 사항은 무엇이라고 생각하십니까?",
    key="rights_need"
)

st.markdown("---")

# ---------------- 제출 및 저장 ----------------
st.header("설문 제출")

st.write("모든 문항을 확인하신 뒤, 아래 버튼을 눌러 설문을 제출해 주세요.")

if st.button("설문 제출"):
    # 아주 기본적인 필수 체크
    missing = []
    if gender == "선택하세요":
        missing.append("성별")
    if org.strip() == "":
        missing.append("근무지")
    if freq_mental == "선택하세요":
        missing.append("정신문제 수용자 대면 빈도")

    if missing:
        st.error(f"다음 항목(들)을 모두 응답해 주세요: {', '.join(missing)}")
    else:
        data = {
            "timestamp": datetime.now().isoformat(),
            "gender": gender,
            "age": age,
            "org": org,
            "dept": dept,
            "difficulty": st.session_state.get("difficulty", ""),  # 없으면 공란
            "years": years,
            "freq_mental": freq_mental,
            "barrier": st.session_state.get("barrier", ""),
            "improve": st.session_state.get("improve", ""),
            "rights_need": st.session_state.get("rights_need", ""),
            "peer_support_1": peer_support_1,
            "peer_support_2": peer_support_2,
            "family_view": family_view,
            "family_safety": family_safety,
            "edu_experience": ";".join(edu_experience),
            "want_reward": want_reward,
            "phone_number": phone_number,
        }

        # 나머지 응답 병합
        data.update(attitude_responses)
        data.update(rel_responses)
        data.update(med_responses)
        data.update(burnout_responses)
        data.update(percep_responses)
        data.update(edu_responses)

        df_new = pd.DataFrame([data])
        csv_path = "perception_survey_responses.csv"

        try:
            df_old = pd.read_csv(csv_path)
            df_all = pd.concat([df_old, df_new], ignore_index=True)
        except FileNotFoundError:
            df_all = df_new

        df_all.to_csv(csv_path, index=False, encoding="utf-8-sig")

        st.success("설문이 성공적으로 제출되었습니다. 참여해 주셔서 감사합니다.")
        st.info("※ 현재 예시는 서버 내 CSV 파일에 저장합니다. 실제 연구에서는 보안 규정에 맞는 저장 방식(DB, 암호화 등)을 적용해 주세요.")
