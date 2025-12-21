import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# =========================
# 기본 설정
# =========================
st.set_page_config(page_title="감·수·성 인권감수성 설문", layout="centered")
st.warning("VERSION CHECK 2025-FEEDBACK + COVER ENABLED")

# =========================
# 세션 상태 초기화
# =========================
if "page" not in st.session_state:
    st.session_state.page = "cover"

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

# =========================================================
#                  ★ 0. 표지 화면 ★
# =========================================================
if st.session_state.page == "cover":
    st.title("감·수·성 인권감수성 자가 점검")
    st.markdown("""
이 설문은 **감정(感) – 기준(受) – 성찰(性)**이  
현장에서 어떻게 연결되어 작동하는지를 이해하기 위한 도구입니다.

### 🧭 이 설문을 통해 알 수 있는 것
- 내가 어떤 방식으로 상황을 판단하고 있는지  
- 감정·기준·성찰이 서로 어떤 관계를 맺고 있는지  
- 정신건강 문제가 있는 수용자 상황에서 판단이 어떻게 달라지는지  

### 🔒 안전하고 익명
- 인사평가와 무관  
- 이름·소속 등 어떤 개인정보도 수집하지 않음  
- 결과는 즉시 화면에서만 제공됨  

### ⏱ 소요시간: 약 5분

아래 버튼을 눌러 설문을 시작하십시오.
""")

    if st.button("설문 시작하기"):
        st.session_state.page = "consent"
        st.experimental_rerun()

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

    agree = st.checkbox("위 내용을 읽고 연구 참여에 동의합니다.")

    if not agree:
        st.warning("동의해야 설문을 진행할 수 있습니다.")
        st.stop()

    if st.button("설문으로 이동"):
        st.session_state.page = "survey"
        st.experimental_rerun()

    st.stop()

# =========================================================
#                  ★ 2. 설문 화면 ★
# =========================================================
if st.session_state.page == "survey":

    st.title("인권감수성 설문 (27문항)")
    st.caption("1=전혀 그렇지 않다 / 4=매우 그렇다")

    with st.form("survey"):
        answers = []
        for i, q in enumerate(QUESTIONS, 1):
            st.write(f"{i}. {q}")
            answers.append(st.radio("", [1,2,3,4], horizontal=True, key=f"q_{i}"))
        submit = st.form_submit_button("제출")

    if not submit:
        st.stop()

    # 점수 계산
    total = sum(answers)
    감 = sum(answers[0:9])
    수 = sum(answers[9:18])
    성 = sum(answers[18:27])
    mh_items = [7,8,9,16,17,18,25,26,27]
    mh_score = sum(answers[i-1] for i in mh_items)

    # 결과 저장 후 이동
    st.session_state.result = {
        "total": total,
        "감": 감,
        "수": 수,
        "성": 성,
        "정신": mh_score,
        "answers": answers
    }
    st.session_state.page = "result"
    st.experimental_rerun()

# =========================================================
#                  ★ 3. 결과 화면 ★
# =========================================================
if st.session_state.page == "result":

    r = st.session_state.result

    st.title("📊 인권감수성 결과 요약")

    st.write(f"총점: **{r['total']}점**")
    st.write(f"감: **{r['감']}점** / 수: **{r['수']}점** / 성: **{r['성']}점**")
    st.write(f"정신질환 관련 점수: **{r['정신']}점**")

    # ----------------------
    # 자동 피드백 출력
    # ----------------------
    st.subheader("📝 개인 맞춤형 피드백")

    st.markdown("### 🔹 1) 전체 감·수·성 지수 해석")
    st.write(overall_feedback(r["total"]))

    st.markdown("### 🔹 2) 요소별 해석")
    st.write("#### 감(感)")
    st.write(gam_feedback(r["감"]))
    st.write("#### 수(受)")
    st.write(su_feedback(r["수"]))
    st.write("#### 성(性)")
    st.write(seong_feedback(r["성"]))

    st.markdown("### 🔹 3) 정신질환 수용자 관련 상황 해석")
    st.write(mental_health_feedback(r["정신"]))

    st.markdown("### 🔹 4) 종합 연결 평가")
    st.write(integrated_feedback())

    # 저장
    row = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": r["total"],
        "감": r["감"],
        "수": r["수"],
        "성": r["성"],
        "정신": r["정신"],
    }
    for i, a in enumerate(r["answers"], 1):
        row[f"q{i}"] = a

    save(row)
    st.success("응답이 저장되었습니다.")

    st.caption("※ 본 설문은 연구 목적의 자가점검 도구이며 인사평가와 무관합니다.")






