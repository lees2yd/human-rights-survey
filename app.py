import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components 

# ✅ 반드시 가장 먼저
st.set_page_config(page_title="감·수·성 인권감수성 설문", layout="centered")

# ✅ 그 다음 CSS
st.markdown("""
<style>
.progress-fixed{
    position: fixed;
    top: 3.25rem;
    left: 0;
    right: 0;
    z-index: 100000;
    background: white;
    padding: 12px 16px;
    border-bottom: 1px solid #e5e7eb;
}

.progress-wrap{
    width: 100%;
    height: 12px;
    background: #e5e7eb;
    border-radius: 999px;
    overflow: hidden;
}

.progress-bar{
    height: 100%;
    background: linear-gradient(90deg,#3b82f6,#2563eb);
    transition: width 0.3s ease;
}

.progress-text{
    margin-top: 6px;
    font-size: 0.9rem;
    text-align: right;
    color: #374151;
}

/* ✅ 추가: 진행률바 아래에 뜨는 고정 메시지 */
.progress-milestone{
    margin-top: 10px;
    padding: 10px 12px;
    border-radius: 12px;
    background: #f3f4f6;
    border: 1px solid #e5e7eb;
    font-size: 0.95rem;
    color: #111827;
}

/* ✅ 추가: 메시지 숨김 */
.hidden{ display:none; }

.body-pad-top{
    padding-top: calc(110px + 3.25rem); /* 메시지 공간까지 고려해 조금 늘림 */
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>

/* ===================================== */
/* 1) 전체 레이아웃 폭 & 패딩            */
/* ===================================== */

/* PC에서 내용 폭을 너무 넓지 않게 제한 */
[data-testid="stAppViewContainer"] > .main > div {
    max-width: 780px;
    margin: 0 auto;
}

/* 모바일에서 좌우 패딩 조금 줄이기 */
@media (max-width: 480px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
}

/* ===================================== */
/* 2) 일반 텍스트(표지/동의/결과) 설정    */
/* ===================================== */

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    word-break: keep-all;     /* 한국어 단어 중간 끊김 방지 */
    overflow-wrap: break-word;/* 너무 긴 단어는 강제로 줄바꿈 */
    line-height: 1.7;
    font-size: 1rem;
}

/* 제목은 왼쪽 정렬(폰에서 더 자연스러움) */
h1, h2, h3 {
    text-align: left !important;
}

/* 모바일에서는 글자 살짝 줄이고 줄간격도 살짝 줄임 */
@media (max-width: 480px) {
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li {
        font-size: 0.95rem;
        line-height: 1.6;
    }
}

/* ===================================== */
/* 3) 진행률바 모바일 간격 조정          */
/* ===================================== */

@media (max-width: 480px) {
    .progress-fixed{
        top: 2.8rem;
        padding: 8px 10px;
    }
    .body-pad-top{
        padding-top: calc(95px + 2.8rem);
    }
    .progress-text{
        font-size: 0.8rem;
    }
}

</style>
""", unsafe_allow_html=True)

st.caption("감.수.성 판단설계연구소  |  감정·기준·성찰 기반 판단구조 연구")

# =======================================
# PC + Mobile 자동 최적화 CSS
# =======================================
st.markdown("""
<style>

    /* ---- 문항 전체 블록 ---- */
    .question-block {
        margin-bottom: 26px;   /* 문항 간 전체 간격 */
    }

    /* ---- 문항 텍스트 ---- */
    .question-text {
        font-size: 1.05rem;
        font-weight: 500;
        margin-bottom: 4px;    /* 문항과 응답 사이를 좁게 */
        line-height: 1.6;      /* 줄간격 조금 넉넉하게 */
        word-break: keep-all;  /* 한국어 단어 중간 끊기 방지 */
    }

    /* ---- 라디오 버튼 사이 간격 ---- */
    .stRadio > div {
        margin-top: -2px !important;   /* 위쪽 간격 줄임 */
        margin-bottom: 6px !important; /* 아래쪽은 기본 유지 */
        display: flex !important;
        gap: 12px !important;
    }

    /* ---- 응답 아래 구분선 ---- */
    .answer-divider {
        border-bottom: 1px solid #dddddd;
        margin-top: 6px;
        margin-bottom: 12px;
    }

    /* ---- 모바일 최적화 ---- */
    @media (max-width: 480px) {

        .question-text {
            font-size: 0.95rem !important;
            margin-bottom: 2px !important;
        }

        .stRadio > div {
            gap: 8px !important;
            margin-top: -6px !important;
        }

        .answer-divider {
            margin-top: 4px !important;
            margin-bottom: 10px !important;
        }
    }

</style>
""", unsafe_allow_html=True)

# =========================
# 세션 상태 초기화
# =========================
if "page" not in st.session_state:
    st.session_state.page = "cover"

if "answers" not in st.session_state:
    st.session_state.answers = {}
    
# =========================
# 문항
# =========================
QUESTIONS = [
    "수용자가 소란을 피울 때, 그 안에 두려움이나 불안이 있을 수 있다고 생각한다.",   #1
    "수용자의 말투나 표정을 보며 화남, 슬픔, 걱정 같은 감정을 쉽게 떠올린다.",           #2
    "수용자의 감정을 단정하지 않고, 대화나 관찰로 다시 확인하려 한다.",                 #3
    "수용자와 마주할 때 내 감정이 어떠했는지 알아본다.",                               #4
    "내 감정에 원하는 욕구(안전, 존중 등)가 있음을 알아차린다.",                      #5
    "수용자의 감정을 이해하려는 노력 자체가 내 공감능력을 키운다고 본다.",              #6
    "정신건강 문제 있는 수용자의 과도한 반응이 심리적 문제 때문일 수 있는지 살핀다.",   #7
    "정신건강 문제 있는 수용자가 흥분한 경우, 지시를 간단히 하고 짧게 말한다.",         #8
    "정신문제 있는 수용자에게 불빛·소리·접촉 등이 괴로운 자극일 수 있음을 이해한다.",   #9
    "내 행동이 감정 배출인지 업무상 필요한 것인지 구분한다.",                          #10
    "감정이 주는 정보를 인식하고 그 정보를 바탕으로 행동한다.",                      #11
    "나는 편리함을 포기하더라도 규정을 지키려고 노력한다.",                           #12
    "취하는 조치가 목적에 맞고 꼭 필요한지 먼저 살핀다.",                            #13
    "수용자에게 조치를 할 때 반드시 정해진 절차를 따른다.",                           #14
    "대응은 언제나 헌법 기준(목적·수단·최소침해)에 맞게 조정한다.",                    #15
    "정신건강 문제가 있는 수용자의 위험 신호가 보이면 절차에 따라 조치한다.",           #16
    "문제 상황 발생 시 의료·심리 전문가와 상의해 대응을 조정한다.",                    #17
    "대응방식이 정신상태에 적합한지 고려한다.",                                        #18
    "내 편견으로 인해 반응이 달라지지 않았는지 다시 생각한다.",                       #19
    "나는 수용자를 집단이 아닌 개인으로 이해하려 노력한다.",                          #20
    "동료 압력에 따라 행동한 적이 없는지 점검한다.",                                   #21
    "권위에 휘둘리지 않도록 스스로 판단하려 노력한다.",                               #22
    "과거와 비교해 업무 습관이 달라졌다고 느낀다.",                                   #23
    "내 감정이 피로나 스트레스로 과장되었을 수 있음을 고려한다.",                     #24
    "정신질환을 이유로 수용자를 구분하지 않으려 노력한다.",                            #25
    "동료 분위기에 휩쓸린 적이 없는지 다시 생각한다.",                                #26
    "정신건강 문제가 있는 수용자를 단정하지 않으려 노력한다."                          #27
]

# =========================
# 피드백 함수
# =========================
def overall_feedback(total):
    if total >= 88:
        return """전반적으로 감정, 기준, 성찰이 유기적으로 연결되어 작동하고 있는 것으로 보입니다.
이는 인권 판단이 하나의 사고 습관으로 자리잡아 가고 있음을 보여줍니다."""
    elif total >= 68:
        return """감정이나 기준 중 일부는 잘 작동하지만, 상황에 따라 연결이 느슨해지는 지점도 나타날 수 있습니다.
이는 인권 감수성이 발달하는 자연스러운 과정입니다."""
    elif total >= 48:
        return """판단이 빠르게 이루어지며 감정·기준·성찰을 점검할 여유가 부족했을 수 있습니다.
이는 개인의 문제가 아니라 업무 환경과 정서적 부담의 영향을 반영한 결과일 수 있습니다."""
    else:
        return """업무 압박과 정서적 피로가 판단 과정 전반에 영향을 주었을 가능성이 큽니다.
이는 부족함이 아니라 상황적 부담을 드러내는 결과로 이해할 수 있습니다."""

def gam_feedback(score):
    if score >= 28:
        return "감정 변화를 민감하게 알아차리는 경향이 있으며, 이는 인권 판단의 중요한 출발점이 되는 강점입니다."
    elif score >= 19:
        return "감정을 느끼지만 바쁜 상황에서는 충분히 인식하기 전에 행동으로 넘어갔을 가능성이 있습니다."
    else:
        return "업무에 집중해 온 시간이 길어 감정을 들여다볼 여유가 부족했을 수 있습니다. 이는 몰입의 신호이지 결함이 아닙니다."

def su_feedback(score):
    if score >= 28:
        return "정당성·필요성·최소침해 등 기준을 판단 과정에 비교적 잘 포함시키고 있습니다."
    elif score >= 19:
        return "기준을 인식하고 있지만 실제 상황에서는 적용이 쉽지 않았던 순간도 있었을 수 있습니다."
    else:
        return "상황의 속도가 빨라 기준을 충분히 적용하기 전에 상황이 지나갔을 가능성이 큽니다."

def seong_feedback(score):
    if score >= 28:
        return "자신의 반응을 돌아보고 다음을 생각해 보는 성찰 과정이 잘 작동하고 있는 것으로 보입니다."
    elif score >= 19:
        return "성찰의 필요성은 느끼지만 항상 여유가 있었던 것은 아닐 수 있습니다."
    else:
        return "정서적 피로로 성찰의 에너지가 부족했을 가능성이 있으며, 이는 부담의 신호일 뿐 결핍이 아닙니다."

def mental_health_feedback(score):
    if score >= 27:
        return """정신질환 수용자를 대할 때에도 감정·기준·성찰을 비교적 안정적으로 유지하려는 노력이 나타납니다."""
    elif score >= 20:
        return """정신질환 수용자를 대하는 상황에서 판단의 어려움이 더 크게 느껴졌을 가능성이 있습니다.
이는 많은 실무자가 공통으로 경험하는 부분입니다."""
    else:
        return """정서적·인지적 부담이 상당했음을 보여주는 결과로, 이는 인권 감수성의 부족이 아니라 지원이 필요한 영역임을 의미합니다."""

def integrated_feedback():
    return """전체적으로 인권 감수성은 단순한 성향이 아니라 상황에 따라 다르게 작동하는 판단 구조입니다.
정신질환 수용자 관련 상황은 일반적인 상황보다 더 많은 자원이 필요하며,
이 영역에서 어려움이 나타나는 것은 자연스러운 현상입니다.
이 지점을 인식하는 것 자체가 인권 감수성의 중요한 출발점입니다."""

# -------------------------
# 총점 해석
# -------------------------
def interpret(total):
    if total <= 47:
        return "매우 낮음: 감정·기준·성찰 연결이 제한적일 수 있습니다."
    elif total <= 67:
        return "낮음: 일부 요소 작동하지만 흔들림 가능성 있음."
    elif total <= 87:
        return "중간: 균형적이나 상황 따라 편차 있음."
    else:
        return "높음: 감정–기준–성찰이 일관되게 작동할 가능성이 큼."

# =========================
# Google Sheets 저장
# =========================
SPREADSHEET_KEY = "12l-MzIhszbWb5kV3muWyGoqyfBaKD4CARjqKktndiAg"

def save(row):
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)

    sh = client.open_by_key(SPREADSHEET_KEY)
    sheet = sh.worksheet("sheet1")
    sheet.append_row(list(row.values()))

def save_phone(phone):
    """커피 쿠폰 발송을 위한 휴대폰 번호를 별도 시트에 저장"""
    if not phone:
        return
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)

    sh = client.open_by_key(SPREADSHEET_KEY)
    # 📌 미리 구글시트 안에 'phone' 이라는 워크시트 만들어 두세요.
    sheet = sh.worksheet("phone")
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        phone
    ])
# =========================================================
#                  ★ 0. 표지 화면 ★
# =========================================================
if st.session_state.page == "cover":
    st.title("나의 인권감수성 점수는?")
    st.subheader("감·수·성 인권감수성 실천구조를 확인해 보자")

    st.markdown("""
이 설문은 **감정(感) – 기준(受) – 성찰(性)**의 상호작용을 기반으로  
교도관이 현장에서 어떤 방식으로 인권 관련 상황을 판단하는지 살펴보기 위한 도구입니다.

당신의 응답은 다음과 같은 연구에 활용됩니다.

- 감·수·성 인권감수성 지표의 구조 확인
- 요소 간 관계 검증(CFA·상관 분석)
- 정신건강 문제가 있는 수용자 문항의 민감도 평가

이 설문은 개인을 평가하기 위한 것이 아니라,  
**교정현장의 판단 구조를 이해하고 실천 가능한 인권감수성 지표를 개발하기 위한 연구 도구**입니다.

---

### 🧭 이 설문의 결과에서 확인할 수 있는 것

- 인권이 문제되는 상황을 나는 어떤 방식으로 판단하는가?
- 나의 **감정·기준·성찰이 어떤 관계 구조**로 작동하는가?
- **정신건강 문제가 있는 수용자**를 대할 때 나의 감수성 구조는 어떻게 달라지는가?

---

### 🔒 본 설문은 안전하고 익명으로 진행

- 인사평가와 무관합니다.
- 이름·소속 등 개인정보를 수집하지 않습니다.
- 모든 응답은 익명 처리되며 결과는 즉시 화면에서만 확인됩니다.
- 점수는 평가가 아니라, **나의 판단 작동 방식을 이해하기 위한 참고 정보**입니다.

---

### ⏱ 예상 소요시간: 약 8~10분

아래 버튼을 눌러 설문을 시작해 주세요.
""")

    if st.button("설문 시작하기"):
        st.session_state.page = "consent"
        st.rerun()

    st.stop()

# =========================================================
#                  ★ 1. 연구 참여 동의 ★
# =========================================================
if st.session_state.page == "consent":
    st.header("연구참여 동의서")
    st.markdown("""
본 설문은 교정 현장에서 근무하는 교도관의  
인권감수성 구조를 탐색하기 위한 연구입니다.

- 익명 설문이며 인사평가와 전혀 무관합니다.  
- 응답은 연구 목적에 한해 사용됩니다.  
""")

    agree = st.checkbox("위 내용을 이해하고 연구 참여에 동의합니다.")

    if not agree:
        st.warning("동의해야 설문을 진행할 수 있습니다.")
        st.stop()

    if st.button("설문으로 이동"):
        st.session_state.page = "survey"
        st.rerun()

    st.stop()

# =========================================================
#                  ★ 2. 설문 화면 ★
# =========================================================
if st.session_state.page == "survey":

    st.title("인권감수성 설문 (27문항)")
    st.caption("1=전혀 그렇지 않다 / 4=매우 그렇다")

    answered = sum(
        1 for x in range(1, 28)
        if st.session_state.get(f"q_{x}") is not None
    )
    progress = answered / 27
    pct = int(progress * 100)

    # ✅ (1) 상단 고정 진행률 (milestoneBox 포함 버전으로 수정)
    st.markdown(f"""
    <div class="progress-fixed">
      <div class="progress-wrap">
        <div class="progress-bar" style="width:{pct}%"></div>
      </div>
      <div class="progress-text">진행률: <b>{answered} / 27 문항</b> ({pct}%)</div>

      <!-- ✅ 메시지 자리 -->
      <div id="milestoneBox" class="progress-milestone hidden"></div>
    </div>
    """, unsafe_allow_html=True)

    # ✅ (3) 그리고 그 다음 줄에 기존 body-pad-top 그대로
    st.markdown('<div class="body-pad-top"></div>', unsafe_allow_html=True)

   
    answers = []

    for i, q in enumerate(QUESTIONS, 1):

        if i == 1:
            disabled = False
        else:
            disabled = (st.session_state.get(f"q_{i-1}") is None)

        st.markdown(
            f"<div class='question-block'><div class='question-text'>{i}. {q}</div>",
            unsafe_allow_html=True
        )

        ans = st.radio(
            "",
            [1, 2, 3, 4],
            horizontal=True,
            index=None,
            key=f"q_{i}",
            disabled=disabled
        )

        answers.append(ans)

        if ans is not None:
            st.session_state.answers[i] = ans

        st.markdown("<div class='answer-divider'></div>", unsafe_allow_html=True)

# =========================
    # 제출 가능 여부 체크
    # =========================
    can_submit = all(
        st.session_state.get(f"q_{i}") is not None
        for i in range(1, 28)
    )

    # ---------------------------------------------------------
    # 제출 버튼
    # ---------------------------------------------------------
   
    submit = st.button("제출", disabled=not can_submit)

    if submit:
        answers = [st.session_state.get(f"q_{i}") for i in range(1, 28)]

        total = sum(answers)
        감 = sum(answers[0:9])
        수 = sum(answers[9:18])
        성 = sum(answers[18:27])

        mh_items = [7, 8, 9, 16, 17, 18, 25, 26, 27]
        mh_score = sum(answers[i - 1] for i in mh_items)

        st.session_state.result = {
            "total": total,
            "감": 감,
            "수": 수,
            "성": 성,
            "정신": mh_score,
            "answers": answers
        }

        st.session_state.page = "demographic" 
        st.session_state.scroll_to_top = True
        st.rerun()

# =========================================================
#          ★ 3. 인구학적 정보 (선택 항목) 추가 페이지 ★
# =========================================================

if st.session_state.page == "demographic":
    st.header("기본 정보 (선택 사항)")
    st.caption("※ 익명이며 연구 목적 외 사용되지 않습니다.")

    age = st.radio("연령대", ["20대","30대","40대","50대","60대 이상","응답하지 않음"], key="age")
    gender = st.radio("성별", ["남성","여성","응답하지 않음"], horizontal=True, key="gender")
    career = st.radio("교정 경력", ["5년 미만","5~10년 미만","10~20년 미만","20년 이상"], key="career")
    jobtype = st.radio("근무 유형", ["수용자 직접 관리","교정·교화/상담·심리","의료·보건","행정·관리","기타"], key="jobtype")
    facil = st.radio("근무 기관", ["교도소","구치소","소년시설","치료감호/의료","기타"], key="facil")
    shift = st.radio("교대 형태", ["주간 중심","교대(야간 포함)","혼합/불규칙"], key="shift")

    hr_edu = st.radio("인권 관련 교육 경험(최근 3년)", ["전혀 없음","1회","2~3회","4회 이상"], key="edu_hr")
    edu = st.radio("정신질환 관련 교육 경험", ["없다","1회","2회 이상"], key="edu_mental")
    exposure = st.radio("정신질환 수용자 대면 빈도", ["거의 없음","가끔","자주","매우 자주"], key="exposure")
    degree = st.radio("최종 학력", ["고졸","전문대","학사","석사 이상","응답하지 않음"], key="degree")

    st.markdown("---")
    st.subheader("☕ 설문 참여 감사 커피 쿠폰 (선택 사항)")
    st.caption("원하시는 경우에만 휴대폰 번호를 남겨 주시면, 추첨을 통해 커피 쿠폰을 발송드립니다.")

    want_coupon = st.checkbox(
        "커피 쿠폰 추첨을 위해 연락처(휴대폰 번호)를 남기겠습니다. (선택)",
        key="want_coupon"
    )

    if want_coupon:
        st.text_input(
            "휴대폰 번호를 입력해 주세요. ('-' 포함 또는 미포함 모두 가능)",
            key="phone_input",
            placeholder="예: 01012345678 또는 010-1234-5678"
        )
    else:
        st.session_state["phone_input"] = ""

    if st.button("결과 보기"):
        st.session_state.demographic = {
            "연령대": age, "성별": gender, "경력": career, "직무": jobtype,
            "기관": facil, "교대": shift, "인권교육": hr_edu, "정신교육": edu,
            "대면빈도": exposure, "학력": degree
        }

        # ☕ 여기에서 전화번호를 세션에 저장
        phone = None
        if st.session_state.get("want_coupon"):
            phone = st.session_state.get("phone_input", "").strip()
        st.session_state["phone"] = phone
        
        st.session_state.page = "result"
        st.rerun()
        
# =========================================================
#                  ★ 3. 결과 화면 ★
# =========================================================
import time
import streamlit.components.v1 as components
import plotly.graph_objects as go

if st.session_state.page == "result":

    # 1) (선택) 스크롤 맨 위: 결과 화면에서 1회만 실행
    if st.session_state.get("scroll_to_top", False):
        token = str(time.time())  # 캐시 방지용
        components.html(
            f"""
            <!-- scroll-token: {token} -->
            <script>
            (function() {{
              function scrollTopAll() {{
                try {{
                  window.scrollTo(0, 0);
                  document.documentElement.scrollTop = 0;
                  document.body.scrollTop = 0;

                  if (window.parent) {{
                    window.parent.scrollTo(0, 0);
                    window.parent.document.documentElement.scrollTop = 0;
                    window.parent.document.body.scrollTop = 0;

                    const selectors = [
                      '[data-testid="stAppViewContainer"]',
                      '[data-testid="stApp"]',
                      'section.main',
                      '.main',
                      'div.block-container'
                    ];
                    selectors.forEach(sel => {{
                      const el = window.parent.document.querySelector(sel);
                      if (el) el.scrollTop = 0;
                    }});
                  }}
                }} catch (e) {{}}
              }}

              let n = 0;
              function loop() {{
                scrollTopAll();
                n++;
                if (n < 60) requestAnimationFrame(loop);
              }}
              requestAnimationFrame(loop);

              setTimeout(scrollTopAll, 100);
              setTimeout(scrollTopAll, 300);
              setTimeout(scrollTopAll, 700);
              setTimeout(scrollTopAll, 1200);
              setTimeout(scrollTopAll, 2000);
            }})();
            </script>
            """,
            height=0,
        )
        st.session_state.scroll_to_top = False

    # 2) 결과 데이터 가져오기
    r = st.session_state.get("result", None)
    if r is None:
        st.warning("결과 데이터가 없습니다. 설문을 다시 진행해주세요.")
        st.stop()

    total = r["total"]
    gam = r["감"]
    su = r["수"]
    seong = r["성"]
    mental = r["정신"]

    # 3) 점수 요약
    st.title("📊 인권감수성 결과 요약")
    st.write(f"총점: **{total}점**")
    st.write(f"감: **{gam}점** / 수: **{su}점** / 성: **{seong}점**")
    st.write(f"정신질환 관련 점수: **{mental}점**")

    # 4) 레이더 차트 (✅ 제출 후 결과 화면에서 항상 렌더)
    st.subheader("🕸 감·수·성 인권감수성 프로파일 (Radar Chart)")

    categories = ["감", "수", "성"]
    values_total = [gam, su, seong]

    # 정신질환 상황 점수 — 감·수·성별 3문항씩 자동 분리
    mh_gam = sum([r['answers'][6], r['answers'][7], r['answers'][8]])     # 7~9번
    mh_su = sum([r['answers'][15], r['answers'][16], r['answers'][17]])   # 16~18번
    mh_seong = sum([r['answers'][24], r['answers'][25], r['answers'][26]])# 25~27번
    values_mh = [mh_gam, mh_su, mh_seong]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values_total,
        theta=categories,
        fill='toself',
        name='전체 점수',
        line=dict(color='blue')
    ))

    fig.add_trace(go.Scatterpolar(
        r=values_mh,
        theta=categories,
        fill='toself',
        name='정신질환 상황 점수',
        line=dict(color='red')
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 36])
        ),
        showlegend=True,
        title="감·수·성 인권감수성 프로파일"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 5) 피드백
    st.subheader("📝 개인 맞춤형 피드백")

    st.markdown("### 🔹 1) 전체 감·수·성 지수 해석")
    st.write(overall_feedback(total))

    st.markdown("### 🔹 2) 요소별 해석")
    st.write("#### 감(感)")
    st.write(gam_feedback(gam))
    st.write("#### 수(受)")
    st.write(su_feedback(su))
    st.write("#### 성(性)")
    st.write(seong_feedback(seong))

    st.markdown("### 🔹 3) 정신질환 수용자 관련 상황 해석")
    st.write(mental_health_feedback(mental))

    st.markdown("### 🔹 4) 종합 연결 평가")
    st.write(integrated_feedback())

    # 6) 저장
    row = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total,
        "감": gam,
        "수": su,
        "성": seong,
        "정신": mental,
    }
    for i, a in enumerate(r["answers"], 1):
        row[f"q{i}"] = a

    demo = st.session_state.get("demographic", {})
    for k, v in demo.items():
        row[k] = v  # row에 추가
    
      # ☕ 커피 쿠폰용 휴대폰 번호 별도 저장
    phone = st.session_state.get("phone", None)
    if phone:
        try:
            save_phone(phone)
        except Exception as e:
            st.warning("휴대폰 번호 저장 중 오류가 발생했습니다. 쿠폰 발송에 문제가 생길 수 있습니다.")
            st.caption(str(e))

    save(row)
    st.success("응답이 저장되었습니다.")
    st.caption("※ 본 설문은 연구 목적의 자가점검 도구이며 인사평가와 무관합니다.")




































































