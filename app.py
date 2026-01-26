import streamlit as st
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import gspread
from google.oauth2.service_account import Credentials
import streamlit.components.v1 as components

# ✅ PDF 생성
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

import matplotlib.pyplot as plt
import numpy as np
from reportlab.lib.utils import ImageReader

# -------------------------------------------
# 📌 matplotlib 한글 폰트 설정 (레이더 차트용)
# -------------------------------------------
from matplotlib import font_manager

font_path = "fonts/NanumGothicCoding.ttf"
font_manager.fontManager.addfont(font_path)
nanum_font = font_manager.FontProperties(fname=font_path)

plt.rcParams["font.family"] = nanum_font.get_name()
plt.rcParams["axes.unicode_minus"] = False

# -------------------------------------------
# 📌 reportlab 한글 폰트 등록
# -------------------------------------------
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
pdfmetrics.registerFont(TTFont("NanumGothic", "fonts/NanumGothicCoding.ttf"))

# ✅ 원문(설명문·동의서) PDF 링크
CONSENT_PDF_URL = "https://drive.google.com/file/d/1Qy1SSYDXaRY0EsNrcx7i-5aKXVsedOmP/view?usp=drive_link"

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
.hidden{ display:none; }
.body-pad-top{
    padding-top: calc(110px + 3.25rem);
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main > div {
    max-width: 780px;
    margin: 0 auto;
}
@media (max-width: 480px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {
    word-break: keep-all;
    overflow-wrap: break-word;
    line-height: 1.7;
    font-size: 1rem;
}
h1, h2, h3 { text-align: left !important; }
@media (max-width: 480px) {
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li {
        font-size: 0.95rem;
        line-height: 1.6;
    }
}
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
.question-block { margin-bottom: 26px; }
.question-text {
    font-size: 1.05rem;
    font-weight: 500;
    margin-bottom: 4px;
    line-height: 1.6;
    word-break: keep-all;
}
.stRadio > div {
    margin-top: -2px !important;
    margin-bottom: 6px !important;
    display: flex !important;
    gap: 12px !important;
}
.answer-divider {
    border-bottom: 1px solid #dddddd;
    margin-top: 6px;
    margin-bottom: 12px;
}
@media (max-width: 480px) {
    .question-text { font-size: 0.95rem !important; margin-bottom: 2px !important; }
    .stRadio > div { gap: 8px !important; margin-top: -6px !important; }
    .answer-divider { margin-top: 4px !important; margin-bottom: 10px !important; }
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
if "saved_to_sheet" not in st.session_state:
    st.session_state.saved_to_sheet = False

# =========================
# 📌 상단 진행률 바 (설문 + 인구학)
# =========================
TOTAL_SURVEY_Q = 27
TOTAL_DEMO_Q = 11

DEMO_KEYS = [
    "age", "gender", "career", "jobtype", "facil",
    "shift", "edu_hr", "edu_mental", "exposure", "degree",
    "burnout_detach"
]

progress_pct = None
progress_label = ""

if st.session_state.page == "survey":
    answered = sum(
        1 for i in range(1, TOTAL_SURVEY_Q + 1)
        if st.session_state.get(f"q_{i}") is not None
    )
    progress_pct = int((answered / TOTAL_SURVEY_Q) * 100)
    progress_label = f"{answered} / {TOTAL_SURVEY_Q} 문항 완료 ({progress_pct}%)"

elif st.session_state.page == "demographic":
    answered = sum(1 for k in DEMO_KEYS if st.session_state.get(k) is not None)
    progress_pct = int((answered / TOTAL_DEMO_Q) * 100)
    progress_label = f"인구학 정보 {answered} / {TOTAL_DEMO_Q}개 완료 ({progress_pct}%)"

if progress_pct is not None:
    st.markdown(f"""
    <div class="progress-fixed">
        <div class="progress-wrap">
            <div class="progress-bar" style="width:{max(progress_pct,1)}%"></div>
        </div>
        <div class="progress-text">{progress_label}</div>
    </div>
    <div class="body-pad-top"></div>
    """, unsafe_allow_html=True)
else:
    st.markdown('<div class="body-pad-top"></div>', unsafe_allow_html=True)

# =========================
# 문항
# =========================
QUESTIONS = [
    "수용자가 소란을 피울 때, 그 안에 두려움이나 불안이 있을 수 있다고 생각한다.",   #1
    "수용자의 말투나 표정을 보며 화남, 슬픔, 걱정 같은 감정을 쉽게 떠올린다.",           #2
    "수용자의 감정을 단정하지 않고, 대화나 관찰로 다시 확인하려 한다.",                 #3
    "수용자와 마주할 때 내 감정이 어떠했는지 알아본다.",                               #4
    "내 감정이 단순한 기분이 아니라 그 감정안에 내가 원하는 욕구(안전, 존중 등)가 있음을 알아차린다.",                      #5
    "수용자의 감정을 이해하려는 노력 자체가 내 공감능력을 키운다고 본다.",              #6
    "정신건강 문제 있는 수용자의 과도한 반응이 환청이나 불안 등 다양한 심리적 문제 때문일 수 있는지 먼저 살핀다.",   #7
    "정신건강 문제 있는 수용자가 흥분한 경우, 지시를 간단히 하고 짧게 말한다.",         #8
    "정신문제 있는 수용자에게 불빛·소리·접촉 등이 괴로운 자극일 수 있음을 이해한다.",   #9
    "내가 수용자에 대해여 하려는 행동이 단순히 감정 배출인지, 아니면 업무에 꼭 필요한 것인지 구분한다.",                          #10
    "나의 감정이 주는 정보를 인식하고 그 정보를 바탕으로 행동한다.",                      #11
    "나는 편리함을 포기하더라도 규정을 지키려고 의식적으로 노력한다.",                           #12
    "내가 취하는 조치가 목적에 맞으며, 꼭 필요한 정도인지 먼저 살핀다.",                            #13
    "수용자에게 조치를 할 때 반드시 정해진 절차를 따른다.",                           #14
    "수용자에 대한 대응은 언제나 헌법 기준(예: 목적의 정당성, 수단의 적합성, 그리고 침해의 최소성 등)에 맞게 조정한다.",                    #15
    "정신건강 문제가 있는 수용자의 자해 등 위험 신호가 보이면 정해진 절차에 따라 조치한다.",           #16
    "정신건강 문제가 있는 수용자에게 문제(예,환청 불안 등) 상황 발생시 의료·심리 전문가와 상의해 대응을 조정한다.",                    #17
    "정신건강 문제가 있는 수용자에 대한 대응방식이 그들의 정신상태에 적합한 조치인지 고려해서 결정한다.",                                        #18
    "수용자를 대할 때, 나의 편견으로 인해 반응이 달라지진 않았는지 다시 생각해 본다.",                       #19
    "나는 수용자를 집단이 아닌 개인으로 이해하려 노력한다.",                          #20
    "나 자신 스스로의 판단보다는 동료들의 압력에 따라 행동한 적이 없는지 점검한다.",                                   #21
    "나는 권위에 휘둘리지 않도록 내가 판단한 대로 행동하고자 노력한다.",                               #22
    "과거와 비교해 볼 때면 나의 업무 습관이 달라졌다고 느낀다.",                                   #23
    "내가 느낀 감정이 실제 상황 때문이 아니라, 내 피로나 스트레스로 인해 과장된 것일 수도 있다고 생각한다.",                     #24
    "정신질환 등을 이유로 정신건강 문제가 있는 수용자를 일반 수용자들과 구분하지 않고 대하려고 한다.",                            #25
    "동료들의 태도에 휩쓸려 정신건강 문제가 있는 수용자에게 더 강하게 대하지 않았는지를 돌아본다.",                                #26
    "나는 정신건강 문제가 있는 수용자를 문제 수용자로 단정하지 않으려고 한다."                          #27
]

# =========================
# ✅ 총점 기준 “보통형 vs 4유형” 분류 로직
# =========================
def overall_level(total: int) -> str:
    # 27~108
    if total <= 67:
        return "low"
    elif total <= 87:
        return "mid"
    else:
        return "high"

def mental_level(score: int) -> str:
    # 9~36 (정신질환 9문항 합)
    if score >= 27:
        return "high"
    elif score >= 20:
        return "mid"
    else:
        return "low"

TYPE_TEXT_MAIN = {
    "balance": """✅ 균형형
본 설문 응답에서 감·수·성 3요인이 비교적 고르게 분포한 유형입니다. 판단 과정에서 감정 인식, 기준 적용, 성찰이 함께 고려되는 양상이 반영되었습니다.""",

    "emotion": """✅ 감우수형
본 설문 응답에서 감(감정 인식·공감) 요인이 상대적으로 두드러진 분포를 보인 유형입니다. 판단 과정에서 정서적 신호나 관계적 단서가 먼저 고려되는 경향이 반영되었습니다.""",

    "norm": """✅ 수우수형
본 설문 응답에서 수(기준·절차·비례성) 요인이 상대적으로 두드러진 분포를 보인 유형입니다. 판단 시 규정과 기준을 중심으로 상황을 정리하려는 양상이 반영되었습니다.""",

    "reflect": """✅ 성우수형
본 설문 응답에서 성(성찰·자기점검) 요인이 상대적으로 두드러진 분포를 보인 유형입니다. 사건 이후 자신의 판단과 대응을 돌아보는 양상이 응답에 반영되었습니다.""",

    "normal": """✅ 보통형
본 설문 응답에서 감·수·성 요인이 전반적으로 중간 범위에 분포한 유형입니다. 특정 요인이 두드러지기보다는, 상황이나 조건에 따라 판단 구조가 달라질 가능성이 응답에 반영되었습니다."""
}

TYPE_TEXT_MH = {
    "balance": """✅ (정신질환 상황) 균형형
정신질환 수용자 관련 문항 응답에서 감·수·성 요인이 비교적 고르게 분포한 유형입니다. 해당 상황에서도 여러 판단 요소가 함께 고려되는 양상이 반영되었습니다.""",

    "emotion": """✅ (정신질환 상황) 감우수형
정신질환 수용자 관련 문항 응답에서 감(정서 인식·공감) 요인이 상대적으로 두드러진 분포를 보인 유형입니다. 정서적 신호를 중심으로 상황을 인식하는 양상이 반영되었습니다.""",

    "norm": """✅ (정신질환 상황) 수우수형
정신질환 수용자 관련 문항 응답에서 수(기준·절차·비례성) 요인이 상대적으로 두드러진 분포를 보인 유형입니다. 기준과 절차를 중심으로 판단을 정리하려는 양상이 반영되었습니다.""",

    "reflect": """✅ (정신질환 상황) 성우수형
정신질환 수용자 관련 문항 응답에서 성(성찰·자기점검) 요인이 상대적으로 두드러진 분포를 보인 유형입니다. 대응 이후 판단을 되돌아보는 양상이 응답에 반영되었습니다.""",

    "normal": """✅ (정신질환 상황) 보통형
정신질환 수용자 관련 문항 응답에서 전반적인 점수 분포가 중간 범위에 위치한 유형입니다. 이 영역은 상황의 난이도, 경험, 지원 조건 등의 영향을 크게 받을 수 있음이 응답 양상에 반영되었습니다."""
}

# =========================
# ✅ 유형 코드(명목척도) 매핑
# - 서열 의미 없음(단순 식별 코드)
# =========================
TYPE_CODE_MAIN = {
    "balance": 1,   # 균형형
    "emotion": 2,   # 감우수형
    "norm": 3,      # 수우수형
    "reflect": 4,   # 성우수형
    "normal": 5     # 보통형
}

TYPE_CODE_MH = {
    "balance": 11,  # 정신질환 상황: 균형형
    "emotion": 12,  # 정신질환 상황: 감우수형
    "norm": 13,     # 정신질환 상황: 수우수형
    "reflect": 14,  # 정신질환 상황: 성우수형
    "normal": 15    # 정신질환 상황: 보통형
}

def classify_4type_by_scores(gam_score: int, su_score: int, seong_score: int,
                             mid_cut: int, balance_gap: int) -> str:
    # 균형형: 모두 mid_cut 이상 & max-min이 작음
    if (gam_score >= mid_cut) and (su_score >= mid_cut) and (seong_score >= mid_cut):
        if (max(gam_score, su_score, seong_score) - min(gam_score, su_score, seong_score)) <= balance_gap:
            return "balance"

    # 우수형: 최댓값 축(동점이면 감 > 수 > 성)
    scores = {"emotion": gam_score, "norm": su_score, "reflect": seong_score}
    max_val = max(scores.values())
    for k in ["emotion", "norm", "reflect"]:
        if scores[k] == max_val:
            return k
    return "balance"

def classify_main_type(total: int, gam: int, su: int, seong: int) -> str:
    # 총점이 중간 미만(low) -> 보통형
    if overall_level(total) == "low":
        return "normal"
    # 9문항 합(9~36)에서 중간 시작점 19, 균형 허용 격차 3
    return classify_4type_by_scores(gam, su, seong, mid_cut=19, balance_gap=3)

def classify_mental_type(mental_total: int, mh_gam: int, mh_su: int, mh_seong: int) -> str:
    # 정신질환 9문항 총점이 중간 미만(low) -> 보통형
    if mental_level(mental_total) == "low":
        return "normal"
    # 3문항 합(3~12)에서 중간 시작점 7, 균형 허용 격차 2
    return classify_4type_by_scores(mh_gam, mh_su, mh_seong, mid_cut=7, balance_gap=2)

# =========================
# 레이더 차트(PDF용 matplotlib)
# =========================
def make_radar_image(gam, su, seong, mh_gam, mh_su, mh_seong):
    labels = np.array(["감", "수", "성"])
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)

    values_total = np.array([gam, su, seong])
    values_mh = np.array([mh_gam, mh_su, mh_seong])

    values_total = np.concatenate((values_total, [values_total[0]]))
    values_mh = np.concatenate((values_mh, [values_mh[0]]))
    angles_closed = np.concatenate((angles, [angles[0]]))

    fig = plt.figure(figsize=(3, 3))
    ax = fig.add_subplot(111, polar=True)

    ax.plot(angles_closed, values_total)
    ax.fill(angles_closed, values_total, alpha=0.2)

    ax.plot(angles_closed, values_mh)
    ax.fill(angles_closed, values_mh, alpha=0.2)

    ax.set_thetagrids(angles * 180 / np.pi, labels)
    ax.set_ylim(0, 36)

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf

# =========================
# PDF 결과지 생성 (유형 중심)
# =========================
def make_result_pdf(result: dict, demographic=None) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    margin_x = 25 * mm
    margin_y = 20 * mm
    y = height - margin_y

    total = result["total"]
    gam = result["감"]
    su = result["수"]
    seong = result["성"]
    mental = result["정신"]

    ans = result.get("answers", [])
    if len(ans) >= 27:
        mh_gam = ans[6] + ans[7] + ans[8]        # 7~9
        mh_su = ans[15] + ans[16] + ans[17]      # 16~18
        mh_seong = ans[24] + ans[25] + ans[26]   # 25~27
    else:
        mh_gam = mh_su = mh_seong = 0

    main_type_key = result.get("main_type_key", "normal")
    mh_type_key = result.get("mh_type_key", "normal")

    c.setFont("NanumGothic", 18)
    c.drawString(margin_x, y, "나의 감·수·성 인권감수성 결과")
    y -= 10 * mm

    c.setFont("NanumGothic", 9)
    c.drawString(margin_x, y, "※ 자가점검용 요약 결과지(비진단·비평가)")
    y -= 8 * mm

    c.setFont("NanumGothic", 9)
    c.drawString(margin_x, y, f"응답 일시: {result.get('time_str', '')}")
    y -= 6 * mm

    c.setFont("NanumGothic", 10)
    c.drawString(
        margin_x, y,
        f"총점: {total}점 | 감: {gam}점  수: {su}점  성: {seong}점 | (정신질환 9문항: {mental}점)"
    )
    y -= 10 * mm

    chart_size = 55 * mm
    chart_x = (width - chart_size) / 2
    chart_y_bottom = y - chart_size + 5 * mm

    radar_buf = make_radar_image(gam, su, seong, mh_gam, mh_su, mh_seong)
    radar_img = ImageReader(radar_buf)
    c.drawImage(
        radar_img, chart_x, chart_y_bottom,
        width=chart_size, height=chart_size,
        preserveAspectRatio=True, mask="auto"
    )

    y = chart_y_bottom - 12 * mm

    def draw_paragraph(title, body):
        nonlocal y
        if y < margin_y + 40 * mm:
            c.showPage()
            y = height - margin_y

        c.setFont("NanumGothic", 11)
        c.drawString(margin_x, y, title)
        y -= 6 * mm

        c.setFont("NanumGothic", 9)
        max_chars = 85
        words = body.replace("\n", " ").split(" ")
        line = ""
        for w in words:
            if len(line) + len(w) + 1 <= max_chars:
                line = (line + " " + w).strip()
            else:
                c.drawString(margin_x, y, line)
                y -= 4 * mm
                line = w
        if line:
            c.drawString(margin_x, y, line)
            y -= 6 * mm

    draw_paragraph("【전체(27문항) 유형】", TYPE_TEXT_MAIN.get(main_type_key, TYPE_TEXT_MAIN["normal"]))
    draw_paragraph("【정신질환 상황(9문항) 유형】", TYPE_TEXT_MH.get(mh_type_key, TYPE_TEXT_MH["normal"]))

    disclaimer = (
        "※ 본 결과지는 자가점검용 비임상·비진단 자료이며, "
        "인사평가·법적 판단의 근거로 사용할 수 없습니다."
    )
    c.setFont("NanumGothic", 8)
    c.drawString(margin_x, margin_y, disclaimer)

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

# =========================
# 인구학 정보 → 숫자 코드 매핑
# =========================
AGE_MAP = {"20대": 1, "30대": 2, "40대": 3, "50대": 4, "60대 이상": 5}
GENDER_MAP = {"남성": 1, "여성": 2}
CAREER_MAP = {"5년 미만": 1, "5~10년 미만": 2, "10~20년 미만": 3, "20년 이상": 4}
JOBTYPE_MAP = {"보안과": 1, "사회복귀과": 2, "의료과": 3, "총무과/직훈과": 4, "기타": 9}
FACIL_MAP = {"교도소": 1, "구치소": 2, "소년시설": 3, "치료감호/의료": 4, "기타": 9}
SHIFT_MAP = {"주간 중심": 1, "교대(야간 포함)": 2, "혼합/불규칙": 3}
EDU_HR_MAP = {"전혀 없음": 0, "1회": 1, "2~3회": 2, "4회 이상": 3}
EDU_MENTAL_MAP = {"없다": 0, "1회": 1, "2회 이상": 2}
EXPOSURE_MAP = {"거의 없음": 0, "가끔": 1, "자주": 2, "매우 자주": 3}
DEGREE_MAP = {"고졸": 1, "전문대": 2, "학사": 3, "석사 이상": 4}
BURNOUT_DETACH_MAP = {"전혀 아니다": 1, "대체로 아니다": 2, "대체로 그렇다": 3, "매우 그렇다": 4}

# =========================
# Google Sheets 저장
# =========================
SPREADSHEET_KEY = "12l-MzIhszbWb5kV3muWyGoqyfBaKD4CARjqKktndiAg"

def save(row):
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(SPREADSHEET_KEY)
    sheet = sh.worksheet("sheet1")
    sheet.append_row(list(row.values()))

def save_phone(phone):
    if not phone:
        return
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(SPREADSHEET_KEY)
    sheet = sh.worksheet("phone")  # 미리 생성 필요
    sheet.append_row([
        datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S"),
        phone,
    ])

def save_feedback(feedback_text: str):
    if not feedback_text or not feedback_text.strip():
        return
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(SPREADSHEET_KEY)
    sheet = sh.worksheet("feedback")  # 미리 생성 필요
    sheet.append_row([
        datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S"),
        feedback_text.strip(),
    ])

# =========================================================
#                  ★ 0. 표지 화면 ★
# =========================================================
if st.session_state.page == "cover":
    st.title("나의 인권감수성 점수는?")
    st.subheader("감·수·성 인권감수성 실천구조를 확인해 보자")

    st.markdown(f"""
이 설문은 **감정–기준–성찰(감·수·성)**의 상호작용을 바탕으로,  
교정현장에서 인권 관련 상황을 **어떤 방식으로 판단하는지**를 살펴보기 위한 연구/자가점검 도구입니다.

- 참여는 **자발적**이며 언제든지 중단할 수 있고 불이익이 없습니다.
- 익명 설문이며 **인사평가와 무관**합니다.
- 이름·소속 등 **개인식별정보를 수집하지 않습니다.**
- 일부 문항에서 **일시적 불편감**이 있을 수 있습니다.
- (선택) 쿠폰 수령을 위한 휴대폰 번호는 **응답과 분리 저장**되며 발송 후 삭제됩니다.

""")

    # ✅ 링크 주소 노출 없이 "원문 보기" 클릭 링크
    st.markdown(f"[📄 원문 설명문과 동의서 보기]({CONSENT_PDF_URL})")

    st.markdown("""
---

### ⏱ 예상 소요시간: 약 7~10분
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

    st.markdown(f"""
### 연구 참여 안내(요약)

- 본 설문은 교정현장에서의 인권 관련 판단 구조(감·수·성)를 탐색하기 위한 연구입니다.
- 참여는 **자발적**이며 언제든지 **이유 없이 중단**할 수 있습니다.
- 설문은 **익명 처리**되며 이름·소속 등 **개인식별정보는 수집하지 않습니다.**
- 응답 과정에서 일부 문항이 **불편하거나 부담**될 수 있으며, 원하면 중단 가능합니다.
- (선택) 쿠폰 수령용 휴대폰 번호는 설문 응답과 **분리 저장**되며 발송 후 삭제됩니다.
""")

    st.markdown("---")

    agree = st.checkbox("위 요약 내용을 확인했으며, 자발적으로 연구 참여에 동의합니다.")
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
    st.caption("※ 최근 근무 경험을 바탕으로 응답해 주세요.")

    st.markdown("""
    <style>
    .stRadio > div {
        display: flex !important;
        justify-content: center !important;
        gap: 18px !important;
        margin: 6px 0 12px 0 !important;
    }
    @media (max-width: 480px) {
        .stRadio > div { gap: 12px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(
        """
        <p style="color:red; font-weight:700; text-decoration:underline; font-size:1.1rem;">
        최근 6개월간 근무 경험을 기준으로 작성해 주시기 바랍니다.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        본 설문은 **4점 척도**입니다.
        - **1점:** 전혀 그렇지 않다  
        - **2점:** 그렇지 않은 편이다  
        - **3점:** 그렇다  
        - **4점:** 매우 그렇다  
        """,
        unsafe_allow_html=True,
    )

    answers = []
    for i, q in enumerate(QUESTIONS, 1):
        disabled = False if i == 1 else (st.session_state.get(f"q_{i-1}") is None)

        st.markdown(
            f"<div style='font-weight:600; font-size:1rem; margin-bottom:6px;'>{i}. {q}</div>",
            unsafe_allow_html=True
        )

        col_left, col_center, col_right = st.columns([1, 2, 1])
        with col_center:
            ans = st.radio(
                "",
                [1, 2, 3, 4],
                horizontal=True,
                index=None,
                key=f"q_{i}",
                disabled=disabled,
                label_visibility="collapsed",
            )

        answers.append(ans)
        if ans is not None:
            st.session_state.answers[i] = ans

        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

    can_submit = all(st.session_state.get(f"q_{i}") is not None for i in range(1, 28))
    submit = st.button("다음", key="survey_next_btn", disabled=not can_submit)

    if submit:
        answers = [st.session_state.get(f"q_{i}") for i in range(1, 28)]
        total = sum(answers)
        감 = sum(answers[0:9])
        수 = sum(answers[9:18])
        성 = sum(answers[18:27])

        mh_items = [7, 8, 9, 16, 17, 18, 25, 26, 27]  # 1-indexed
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
        st.rerun()

# =========================================================
#          ★ 3. 인구학적 정보 페이지 ★
# =========================================================
if st.session_state.page == "demographic":

    st.markdown("""
    <style>
    .question-label {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #111827 !important;
        margin-top: 18px !important;
        margin-bottom: 6px !important;
        display: block;
        line-height: 1.45;
    }
    .stRadio > div > label, .stRadio label {
        font-size: 1.05rem !important;
        color: #111 !important;
    }
    @media (max-width: 480px) {
        .question-label { font-size: 1.05rem !important; }
        .stRadio label { font-size: 1rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

    components.html("<script>window.scrollTo(0, 0);</script>", height=0)

    st.header("📌 인구학적 정보")
    st.caption("※ 선택 응답, 익명 처리 / 연구 목적 외 사용되지 않습니다.")

    st.markdown('<span class="question-label">1. 연령대</span>', unsafe_allow_html=True)
    age = st.radio("", ["20대","30대","40대","50대","60대 이상"], key="age", index=None)

    st.markdown('<span class="question-label">2. 성별</span>', unsafe_allow_html=True)
    gender = st.radio("", ["남성","여성"], key="gender", index=None, disabled=(age is None))

    st.markdown('<span class="question-label">3. 교정 경력</span>', unsafe_allow_html=True)
    career = st.radio("", ["5년 미만","5~10년 미만","10~20년 미만","20년 이상"], key="career", index=None,
                      disabled=(gender is None))

    st.markdown('<span class="question-label">4. 근무 유형</span>', unsafe_allow_html=True)
    jobtype = st.radio("", ["보안과","사회복귀과","의료과","총무과/직훈과","기타"], key="jobtype", index=None,
                       disabled=(career is None))

    st.markdown('<span class="question-label">5. 근무 기관</span>', unsafe_allow_html=True)
    facil = st.radio("", ["교도소","구치소","소년시설","치료감호/의료","기타"], key="facil", index=None,
                     disabled=(jobtype is None))

    st.markdown('<span class="question-label">6. 교대 형태</span>', unsafe_allow_html=True)
    shift = st.radio("", ["주간 중심","교대(야간 포함)","혼합/불규칙"], key="shift", index=None,
                     disabled=(facil is None))

    st.markdown('<span class="question-label">7. 인권 관련 교육 경험(최근 3년)</span>', unsafe_allow_html=True)
    edu_hr = st.radio("", ["전혀 없음","1회","2~3회","4회 이상"], key="edu_hr", index=None,
                      disabled=(shift is None))

    st.markdown('<span class="question-label">8. 정신질환 관련 교육 경험</span>', unsafe_allow_html=True)
    edu_mental = st.radio("", ["없다","1회","2회 이상"], key="edu_mental", index=None,
                          disabled=(edu_hr is None))

    st.markdown('<span class="question-label">9. 정신질환 수용자 대면 빈도</span>', unsafe_allow_html=True)
    exposure = st.radio("", ["거의 없음","가끔","자주","매우 자주"], key="exposure", index=None,
                        disabled=(edu_mental is None))

    st.markdown('<span class="question-label">10. 최종 학력</span>', unsafe_allow_html=True)
    degree = st.radio("", ["고졸","전문대","학사","석사 이상"], key="degree", index=None,
                      disabled=(exposure is None))

    st.markdown(
        '<span class="question-label">11. 최근 6개월간, 업무로 인해 마음이 지치거나 감정이 무뎌졌다고 느낀 적이 있다.</span>',
        unsafe_allow_html=True
    )
    burnout_detach = st.radio(
        "",
        ["전혀 아니다", "대체로 아니다", "대체로 그렇다", "매우 그렇다"],
        key="burnout_detach",
        index=None,
        disabled=(degree is None)
    )

    st.markdown("---")
    st.markdown("### ☕ 커피 쿠폰 수령 (선택)")
    want_coupon = st.checkbox(
        "커피 쿠폰을 받기 위해 휴대폰 번호를 입력하겠습니다. 수집된 번호는 본 연구와 분리저장되고 쿠폰발송 후 즉시 폐기합니다.",
        key="want_coupon"
    )

    if want_coupon:
        st.text_input("휴대폰 번호 입력 (예: 01012345678)", key="phone_input")
        st.caption("※ '-' 없이 숫자만 입력 / 쿠폰 발송 전용 저장")

    demo_keys = ["age","gender","career","jobtype","facil","shift","edu_hr","edu_mental","exposure","degree","burnout_detach"]
    base_filled = all(st.session_state.get(k) is not None for k in demo_keys)
    phone_filled = bool(st.session_state.get("phone_input", "").strip())
    can_next = base_filled and (not want_coupon or phone_filled)

    if st.button("다음 (결과 보기)", disabled=not can_next):
        st.session_state.demographic = {
            "연령대": age, "성별": gender, "경력": career, "직무": jobtype, "기관": facil,
            "교대": shift, "인권교육": edu_hr, "정신교육": edu_mental,
            "대면빈도": exposure, "학력": degree,
            "직무소진_거리두기": burnout_detach
        }
        st.session_state["phone"] = st.session_state.get("phone_input", "").strip() if want_coupon else None
        st.session_state.page = "result"
        st.rerun()

# =========================================================
#                  ★ 4. 결과 화면 ★
# =========================================================
import plotly.graph_objects as go

if st.session_state.page == "result":

    components.html("<script>window.scrollTo(0, 0);</script>", height=0)

    r = st.session_state.get("result", None)
    if r is None:
        st.warning("결과 데이터가 없습니다. 설문을 다시 진행해주세요.")
        st.stop()

    total = r["total"]
    gam = r["감"]
    su = r["수"]
    seong = r["성"]
    mental = r["정신"]

    # 정신질환 상황 축 점수(3문항 합)
    mh_gam = sum([r["answers"][6], r["answers"][7], r["answers"][8]])      # 7~9
    mh_su = sum([r["answers"][15], r["answers"][16], r["answers"][17]])    # 16~18
    mh_seong = sum([r["answers"][24], r["answers"][25], r["answers"][26]]) # 25~27

    # ✅ 유형키 산출
    main_type_key = classify_main_type(total, gam, su, seong)
    mh_type_key = classify_mental_type(mental, mh_gam, mh_su, mh_seong)

    # ✅ 유형코드 산출(분석용)
    main_type_code = TYPE_CODE_MAIN.get(main_type_key, TYPE_CODE_MAIN["normal"])
    mh_type_code = TYPE_CODE_MH.get(mh_type_key, TYPE_CODE_MH["normal"])

    # ✅ 세션에 저장(PDF/저장/추적용)
    st.session_state.result["main_type_key"] = main_type_key
    st.session_state.result["mh_type_key"] = mh_type_key
    st.session_state.result["main_type_code"] = main_type_code
    st.session_state.result["mh_type_code"] = mh_type_code

    # 1) 점수 요약
    st.title("📊 인권감수성 결과 요약")
    st.write(f"총점: **{total}점**")
    st.write(f"감: **{gam}점** / 수: **{su}점** / 성: **{seong}점**")
    st.write(f"정신질환 9문항 총점: **{mental}점**")

    # 2) 레이더 차트
    st.subheader("🕸 감·수·성 프로파일 (Radar Chart)")
    categories = ["감", "수", "성"]
    values_total = [gam, su, seong]
    values_mh = [mh_gam, mh_su, mh_seong]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_total, theta=categories, fill="toself",
        name="전체(27문항)", line=dict(color="blue")
    ))
    fig.add_trace(go.Scatterpolar(
        r=values_mh, theta=categories, fill="toself",
        name="정신질환 상황(3×3문항)", line=dict(color="red")
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 36])),
        showlegend=True,
        title="감·수·성 인권감수성 프로파일"
    )
    st.plotly_chart(fig, use_container_width=True)

    # 3) 유형 결과(표시는 텍스트로)
    st.subheader("🧭 결과 유형(총점 기준 분기)")
    st.markdown("### 🔹 1) 전체(27문항) 유형")
    st.write(TYPE_TEXT_MAIN[main_type_key])

    st.markdown("### 🔹 2) 정신질환 수용자 상황(9문항) 유형")
    st.write(TYPE_TEXT_MH[mh_type_key])

    # 4) 고지문
    st.markdown("""
---
### 🔒 안전한 해석을 위한 고지문
본 결과는 **자가점검용·비임상·비진단 도구**이며,
개인의 성향·역량·적합성을 판정하거나 평가하기 위한 목적이 아닙니다.

※ 법적·행정적 판단, 인사평가, 기질/병리 추정에 사용될 수 없습니다.
""")

    # 5) 자유 의견(선택)
    st.markdown("---")
    st.subheader("🗣 설문에 대한 의견 (선택)")
    st.caption("문항 구성, 길이, 표현, 결과지 내용, 전반적인 느낌, 개선점 등에 대해 자유롭게 적어 주세요.")
    st.caption("※ 입력은 선택 사항입니다. 적지 않아도 설문 제출이 가능합니다.")

    feedback_text = st.text_area(
        "자유 의견",
        key="survey_feedback",
        height=120,
        placeholder="예) 문항이 조금 길게 느껴졌습니다.\n정신질환 관련 문항이 인상 깊었습니다.\n개선점을 적어 주세요."
    )

    st.markdown("---")

    # 6) 설문 종료 및 제출(저장)
    if st.button("✅ 설문 종료 및 제출", key="final_submit"):

        if not st.session_state.get("saved_to_sheet", False):

            row = {
                "time": datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S"),
                "total": total,
                "감": gam,
                "수": su,
                "성": seong,
                "정신": mental,

                # ✅ 분석용(숫자)
                "전체유형코드": main_type_code,
                "정신질환유형코드": mh_type_code,
            }

            for i, a in enumerate(r["answers"], 1):
                row[f"q{i}"] = a

            demo = st.session_state.get("demographic", {})
            row["연령대"]   = AGE_MAP.get(demo.get("연령대"))
            row["성별"]     = GENDER_MAP.get(demo.get("성별"))
            row["경력"]     = CAREER_MAP.get(demo.get("경력"))
            row["직무"]     = JOBTYPE_MAP.get(demo.get("직무"))
            row["기관"]     = FACIL_MAP.get(demo.get("기관"))
            row["교대"]     = SHIFT_MAP.get(demo.get("교대"))
            row["인권교육"] = EDU_HR_MAP.get(demo.get("인권교육"))
            row["정신교육"] = EDU_MENTAL_MAP.get(demo.get("정신교육"))
            row["대면빈도"] = EXPOSURE_MAP.get(demo.get("대면빈도"))
            row["학력"]     = DEGREE_MAP.get(demo.get("학력"))
            row["직무소진_거리두기"] = BURNOUT_DETACH_MAP.get(demo.get("직무소진_거리두기"))

            phone = st.session_state.get("phone", None)
            if phone:
                try:
                    save_phone(phone)
                except Exception as e:
                    st.warning("휴대폰 번호 저장 중 오류가 발생했습니다. 쿠폰 발송에 문제가 생길 수 있습니다.")
                    st.caption(str(e))

            try:
                save(row)
                st.session_state.saved_to_sheet = True
                st.success("응답이 저장되었습니다. 설문에 참여해 주셔서 감사합니다.")
            except Exception as e:
                st.error("응답 저장 중 오류가 발생했습니다.")
                st.caption(str(e))

            if feedback_text and feedback_text.strip():
                try:
                    save_feedback(feedback_text.strip())
                    st.info("작성해 주신 의견도 함께 저장되었습니다.")
                except Exception as e:
                    st.warning("의견 저장 중 오류가 발생했습니다. (설문 응답은 정상 저장되었습니다.)")
                    st.caption(str(e))

            st.caption("※ 본 설문은 연구 목적의 자가점검 도구이며 인사평가와 무관합니다.")

        else:
            st.info("이미 제출된 설문입니다. 참여해 주셔서 감사합니다.")











































































































































