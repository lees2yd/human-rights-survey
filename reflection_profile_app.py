import base64
import io
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from matplotlib import font_manager
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


st.set_page_config(
    page_title="감·수·성 인권적 직무판단 자기성찰 프로파일",
    page_icon="🫶",
    layout="centered",
)

# 배포 전에 실제 IRB 승인 내용으로 바꾸십시오.
RESEARCH_TITLE = "감·수·성 인권적 직무판단 척도의 독립표본 타당화 연구"
IRB_APPROVAL_NO = "보건복지부 지정 공용기관생명윤리위원회의 승인(IRB No. P01-202602-01-030)"
PRINCIPAL_INVESTIGATOR = "이성덕"
RESEARCH_CONTACT = "010-9619-4652, mindscaper2013@naver.com"
DATA_RETENTION = "연구 종료 후 3년"
WORKSHEET_NAME = "responses"
SCALE_PAPER_URL = "http://krscs.or.kr/html/sub6_01.html"
LOGO_PATH = Path(__file__).with_name("gam_su_seong_logo.png")
BACKGROUND_PATH = Path(__file__).with_name("human_rights_background.png")
HERO_DESKTOP_PATH = Path(__file__).with_name("hero_background_desktop.png")
HERO_MOBILE_PATH = Path(__file__).with_name("hero_background_mobile.png")


def image_data_uri(path):
    if not path.exists():
        return ""
    return f"data:image/png;base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"

st.markdown(
    """
<style>
  .stApp {background: linear-gradient(145deg,#f8fcff 0%,#eaf6ff 52%,#f8fcff 100%);}
  .block-container {max-width: 880px; padding-top: 1.6rem; padding-bottom: 4rem;}
  h1, h2, h3 {word-break: keep-all; color:#163f67;}
  p, li {line-height: 1.72; word-break: keep-all;}
  .stMarkdown, .stMarkdown p, .stMarkdown li, .stCaption, .stText, .stRadio label, .stRadio label p, .stCheckbox label, .stCheckbox label p, [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {word-break:keep-all !important; overflow-wrap:normal !important; line-break:strict;}
  .hero {padding:2.25rem 2rem 1.8rem; border-radius:26px; background:linear-gradient(145deg,rgba(255,255,255,.97),rgba(239,249,255,.94)); border:1px solid #cfe8f8; box-shadow:0 14px 34px rgba(62,135,183,.13);}
  .brand-bar {padding:.65rem 1rem; margin:.35rem 0 1.1rem; border-radius:16px; background:rgba(255,255,255,.76); border:1px solid #d8edf9; color:#28618e; font-size:.92rem; text-align:center; word-break:keep-all;}
  .logo-wrap {display:flex; justify-content:center; align-items:center; line-height:0; overflow:visible;}
  .logo-wrap img {display:block; object-fit:contain; height:auto;}
  .intro-logo {margin:.1rem 0 .65rem;}
  .intro-logo img {width:138px; max-width:38vw;}
  .page-logo {margin:1.2rem 0 .1rem;}
  .page-logo img {width:54px; max-width:18vw;}
  .intro-kicker {color:#4b94c8; font-weight:700; letter-spacing:.06em; text-align:center; margin:.3rem 0 .75rem;}
  .intro-title {color:#163f67; font-size:2.45rem; font-weight:800; line-height:1.23; text-align:center; margin:.2rem 0 .85rem;}
  .intro-lead {color:#315b7c; font-size:1.05rem; text-align:center; max-width:620px; margin:0 auto 1.4rem; line-height:1.75;}
  .factor-card {padding:1rem .65rem; min-height:106px; text-align:center; border:1px solid #d7ecf9; border-radius:17px; background:rgba(255,255,255,.84); color:#163f67; box-shadow:0 5px 14px rgba(77,147,192,.08);}
  .factor-card b {display:block; color:#2f8dca; font-size:1.25rem; margin-bottom:.25rem;}
  .factor-card span {font-size:.9rem; color:#426d8e;}
  .notice {padding:1rem 1.1rem; border-left:5px solid #55aee1; background:rgba(255,255,255,.82); border-radius:11px; color:#315b7c;}
  .question {font-weight:650; font-size:1.05rem; margin-top:1.15rem; margin-bottom:.35rem; color:#163f67; padding:1rem 1.05rem; border-radius:14px; background:rgba(255,255,255,.80); border:1px solid #d8edf9;}
  .factor-gam,.factor-su,.factor-seong {color:#278bcb;}
  .result-card {padding:1rem 1.1rem; border:1px solid #d7ecf9; border-radius:14px; background:rgba(255,255,255,.88); margin:.5rem 0;}
  .small {font-size:.9rem; color:#59738a;}
  .developer-credit {margin:.05rem 0 1rem; color:#59738a; font-size:.82rem; text-align:center; line-height:1.55;}
  .rights-footer {margin:1.7rem 0 .35rem; padding-top:.9rem; border-top:1px solid #cfe8f8; color:#59738a; font-size:.78rem; line-height:1.65; text-align:center;}
  div[data-testid="stRadio"] > div {gap:1.1rem;}
  div[data-testid="stButton"] > button {border:0; border-radius:13px; background:linear-gradient(135deg,#48a9e1,#2589c8); color:white; font-weight:700; min-height:3.1rem; box-shadow:0 7px 16px rgba(37,137,200,.22);}
  div[data-testid="stButton"] > button:hover {background:linear-gradient(135deg,#2589c8,#176fae); color:white;}
  div[data-testid="stExpander"] {border:1px solid #d4eaf8; border-radius:14px; background:rgba(255,255,255,.76);}
  @media(max-width:520px){
    .block-container{padding:2.55rem .95rem 3rem;}
    .hero{padding:1.35rem .9rem 1.25rem; border-radius:20px;}
    .intro-logo{margin:.15rem 0 .55rem;}
    .intro-logo img{width:112px; max-width:112px;}
    .page-logo{margin:1rem 0 .1rem;}
    .page-logo img{width:48px; max-width:48px;}
    .intro-title{font-size:1.52rem; line-height:1.32; margin:.15rem 0 .7rem; word-break:keep-all;}
    .intro-lead{font-size:.94rem; line-height:1.7; margin-bottom:1rem;}
    .intro-kicker{font-size:.82rem; margin:.15rem 0 .45rem;}
    .factor-card{min-height:0; padding:.82rem .6rem; margin-bottom:.15rem;}
    .factor-card b{font-size:1.08rem;}
    .factor-card span{font-size:.85rem;}
    .question{font-size:1rem; line-height:1.62; padding:.88rem .9rem; word-break:keep-all; overflow-wrap:normal;}
    .developer-credit{font-size:.76rem; margin:.05rem 0 .8rem;}
    .rights-footer{font-size:.72rem; margin-top:1.35rem;}
    div[data-testid="stRadio"] label p{font-size:.94rem; line-height:1.55; word-break:keep-all; overflow-wrap:normal;}
  }
</style>
""",
    unsafe_allow_html=True,
)

background_data_uri = image_data_uri(BACKGROUND_PATH)
if background_data_uri:
    st.markdown(
        f"""
<style>
  .stApp {{
    background-image: linear-gradient(rgba(248,252,255,.80),rgba(248,252,255,.80)), url("{background_data_uri}");
    background-repeat: no-repeat, no-repeat;
    background-size: cover, cover;
    background-position: center, center bottom;
    background-attachment: fixed, fixed;
  }}
  @media(max-width:520px) {{
    .stApp {{
      background-image: linear-gradient(rgba(248,252,255,.84),rgba(248,252,255,.84)), url("{background_data_uri}");
      background-size: auto 100%, auto 100%;
      background-position: center, center bottom;
      background-attachment: scroll, scroll;
    }}
  }}
</style>
""",
        unsafe_allow_html=True,
    )

# Streamlit의 Markdown 블록은 서로 독립적으로 렌더링됩니다. 따라서 첫 화면은
# 빈 .hero div가 아니라 앱 전체에 전용 배경을 적용해야 실제 콘텐츠 뒤에 보입니다.
hero_desktop_data_uri = image_data_uri(HERO_DESKTOP_PATH)
hero_mobile_data_uri = image_data_uri(HERO_MOBILE_PATH) or hero_desktop_data_uri


def apply_intro_background():
    """첫 화면에만 전용 배경을 적용하고, 텍스트는 개별 반투명 카드 위에 보이게 합니다."""
    if not hero_desktop_data_uri:
        return
    st.markdown(
        f"""
<style>
  .stApp {{
    background-image: linear-gradient(145deg,rgba(248,252,255,.26),rgba(239,249,255,.38)), url("{hero_desktop_data_uri}") !important;
    background-repeat: no-repeat, no-repeat !important;
    background-size: cover, cover !important;
    background-position: center, center bottom !important;
    background-attachment: fixed, fixed !important;
  }}
  .hero {{padding:0 !important; border:0 !important; background:transparent !important; box-shadow:none !important;}}
  .intro-lead {{padding:.8rem 1rem; border:1px solid rgba(207,232,248,.88); border-radius:16px; background:rgba(255,255,255,.74); box-shadow:0 5px 14px rgba(77,147,192,.08);}}
  .factor-card {{background:rgba(255,255,255,.82);}}
  @media(max-width:520px) {{
    .stApp {{
      background-image: linear-gradient(180deg,rgba(248,252,255,.20),rgba(239,249,255,.33)), url("{hero_mobile_data_uri}") !important;
      background-size: cover, cover !important;
      background-position: center, center bottom !important;
      background-attachment: scroll, scroll !important;
    }}
    .intro-lead {{padding:.72rem .8rem; background:rgba(255,255,255,.77);}}
  }}
</style>
""",
        unsafe_allow_html=True,
    )


SCALE_LABELS = {
    1: "전혀 그렇지 않다",
    2: "그렇지 않은 편이다",
    3: "그런 편이다",
    4: "매우 그렇다",
}

ITEMS = [
    (1, "감", "공감적 이해", "수용자가 소란을 피울 때, 그 안에 두려움이나 불안이 있을 수 있다고 생각한다."),
    (2, "감", "정서 인식", "수용자의 말투나 표정을 보며 화남, 슬픔, 걱정 같은 감정을 쉽게 떠올린다."),
    (3, "감", "공감적 이해", "수용자의 감정을 단정하지 않고, 대화나 관찰로 다시 확인하려 한다."),
    (4, "감", "정서 인식", "수용자와 마주할 때 내 감정이 어떠했는지 알아본다."),
    (5, "감", "정서 인식", "내 감정이 단순한 기분이 아니라 내가 원하는 욕구(안전, 존중 등)가 있음을 알아차린다."),
    (6, "감", "공감적 이해", "수용자의 감정을 이해하려는 노력 자체가 내 공감 능력을 키운다고 본다."),
    (7, "감", "취약성 이해", "정신건강 문제가 있는 수용자의 과도한 반응이 환청이나 불안 등 다양한 심리적 문제 때문일 수 있는지 먼저 살핀다."),
    (8, "감", "취약성 이해", "정신건강 문제가 있는 수용자가 흥분한 경우, 지시를 간단히 하고 짧게 말한다."),
    (9, "감", "취약성 이해", "정신건강 문제가 있는 수용자에게 불빛·소리·접촉 등이 괴로운 자극일 수 있음을 이해한다."),
    (10, "수", "비례성 판단", "내가 수용자에게 하려는 행동이 단순한 감정 배출인지, 아니면 업무에 꼭 필요한 것인지 구분한다."),
    (11, "수", "전문적 통합판단·협력", "감정이 주는 정보를 인식하고 그 정보를 바탕으로 행동한다."),
    (12, "수", "비례성 판단", "내가 취하는 조치가 목적에 맞으며, 꼭 필요한 정도인지 먼저 살핀다."),
    (13, "수", "절차적 정당성 판단", "수용자에게 조치를 할 때는 반드시 정해진 절차를 따른다."),
    (14, "수", "비례성 판단", "수용자에 대한 대응은 헌법 기준(예: 목적의 정당성, 수단의 적합성, 침해의 최소성 등)에 맞게 조정한다."),
    (15, "수", "절차적 정당성 판단", "정신건강 문제가 있는 수용자의 자해 등 위험 신호가 보이면 정해진 절차에 따라 조치한다."),
    (16, "수", "전문적 통합판단·협력", "정신건강 문제가 있는 수용자에게 환청·불안 등의 문제 상황이 발생하면 의료·심리 전문가와 상의하여 대응을 조정한다."),
    (17, "수", "전문적 통합판단·협력", "정신건강 문제가 있는 수용자에 대한 대응 방식이 그들의 정신상태에 적합한 조치인지 고려하여 결정한다."),
    (18, "성", "편견 성찰", "수용자를 대할 때, 나의 편견으로 인해 반응이 달라지지 않았는지 다시 생각해 본다."),
    (19, "성", "편견 성찰", "나는 수용자를 집단이 아닌 개인으로 이해하려고 노력한다."),
    (20, "성", "권위·관행 성찰", "스스로의 판단보다 동료들의 압력에 따라 행동한 적이 없는지 점검한다."),
    (21, "성", "권위·관행 성찰", "나는 권위에 휘둘리지 않도록 내가 판단한 대로 행동하고자 노력한다."),
    (22, "성", "자기점검·조정", "과거와 비교해 볼 때 나의 업무 습관이 달라졌다고 느낀다."),
    (23, "성", "자기점검·조정", "내가 느낀 감정이 실제 상황 때문이 아니라, 내 피로나 스트레스로 인해 과장된 것일 수도 있다고 생각한다."),
    (24, "성", "권위·관행 성찰", "동료들이 정신건강 문제가 있는 수용자에게 강하게 말할 때, 나도 그 분위기에 휩쓸린 적이 없는지 다시 생각해 본다."),
    (25, "성", "편견 성찰", "나는 정신건강 문제가 있는 수용자를 문제 수용자로 단정하지 않으려고 노력한다."),
]

# 논문의 원문항 번호를 보존하기 위한 대응표(Q12와 Q25는 논문에서 삭제됨)
ORIGINAL_ITEM_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 26, 27]

FACTOR_META = {
    "감": {
        "title": "감(感) — 정서적·상황적 인식",
        "question": "무엇을 알아차리고 있는가?",
        "meaning": "자신과 수용자의 감정·정서 신호를 알아차리고, 취약성과 인권침해 가능성의 맥락에서 이해하는 판단영역입니다.",
        "practice": "반응하기 전에 표정·말투·행동의 변화를 관찰하고, 감정을 단정하지 않은 채 확인 질문을 한 번 해보세요.",
    },
    "수": {
        "title": "수(受) — 규범적·전문적 판단",
        "question": "어떤 기준으로 판단하고 있는가?",
        "meaning": "상황정보를 목적·필요성·비례성·적법절차에 따라 검토하고, 전문적 협력을 통해 정당화 가능한 대응을 선택하는 판단영역입니다.",
        "practice": "조치 전에 ‘목적은 무엇인가, 덜 제한적인 방법은 없는가, 절차와 전문가 협력이 필요한가’를 확인해 보세요.",
    },
    "성": {
        "title": "성(性) — 성찰적 점검·조정",
        "question": "내 판단을 무엇이 움직이고 있는가?",
        "meaning": "편견·피로·감정·동료 압력·조직의 권위와 관행이 판단에 미치는 영향을 점검하고 필요한 경우 조정하는 판단영역입니다.",
        "practice": "강한 감정이 들었던 사건 하나를 골라 사실, 나의 감정, 판단 근거, 동료 분위기를 분리해 짧게 기록해 보세요.",
    },
}

SUBDOMAIN_FEEDBACK = {
    "정서 인식": "나와 상대의 감정을 구체적으로 알아차리고 이름 붙이는 연습",
    "공감적 이해": "수용자의 감정을 추정하되 단정하지 않고 질문과 관찰로 확인하는 연습",
    "취약성 이해": "정신건강·장애·위기 상태가 행동과 의사소통에 미치는 영향을 사례로 학습",
    "비례성 판단": "조치의 목적, 필요성, 적합성, 침해 최소성과 대체수단을 차례로 점검",
    "절차적 정당성 판단": "절차를 단순 규정준수가 아니라 자의적 권력행사를 막는 권리보장 장치로 적용",
    "전문적 통합판단·협력": "감정정보와 직무정보를 통합하고 의료·심리 전문가와 협력하는 기준을 구체화",
    "편견 성찰": "집단명칭이나 과거 기록보다 현재의 개인과 상황을 먼저 보는 연습",
    "권위·관행 성찰": "동료 압력과 관행을 사실상의 정답으로 받아들이지 않고 판단 근거를 언어화",
    "자기점검·조정": "피로와 스트레스가 반응 강도에 미치는 영향을 점검하고 행동을 조정",
}

PRACTICE_GUIDES = {
    "감": {
        "title": "감(感) 연습 — 고통·취약성의 신호 알아차리기",
        "steps": "그때 나와 상대에게 나타난 감정·표정·말투·행동을 구체적으로 적고, 그 신호가 존엄·안전·보호 필요성과 어떻게 연결되는지 한 문장으로 써 보세요.",
    },
    "수": {
        "title": "수(受) 연습 — 목적·필요성·절차를 다시 설계하기",
        "steps": "내 조치의 목적과 법적·직무상 근거를 적은 뒤, 덜 제한적인 대안, 필요한 절차, 의료·심리 등 전문적 협력의 필요성을 차례로 점검해 보세요.",
    },
    "성": {
        "title": "성(性) 연습 — 편견·권위·피로의 영향 점검하기",
        "steps": "내 판단에 피로, 과거 경험, 동료 분위기, 권위나 관행이 미친 영향을 적고, 상대방의 권리와 관계에 미칠 결과를 고려한 다음 행동을 한 가지 정해 보세요.",
    },
}

INTEGRATED_PRACTICE = (
    "최근 불편하거나 긴장되었던 수용자 대응 상황 하나를 떠올려 보십시오. "
    "① 감(感): 나와 상대는 어떤 감정·고통·취약성을 경험했는가? "
    "② 수(受): 나의 대응은 목적, 필요성, 침해 최소성, 절차 및 전문적 협력의 기준에 비추어 적절했는가? "
    "③ 성(性): 피로, 선입견, 동료 분위기, 권위나 관행이 내 판단에 영향을 주지는 않았는가? 다음에는 무엇을 조정할 것인가?"
)

COMMON_REFLECTION_QUESTION = (
    "위 세 문항과 관련하여, 최근 이를 실천하기 어려웠던 경험을 떠올려 보십시오. "
    "그때 개인의 감정·피로, 업무절차, 인력·조직지원 중 무엇이 영향을 주었으며, 다음에는 무엇을 다르게 조정해 볼 수 있습니까?"
)

MENTAL_ITEMS = {7, 8, 9, 15, 16, 17, 24, 25}

DEMOGRAPHIC_OPTIONS = {
    "gender": ["남성", "여성", "응답하지 않음"],
    "age": ["20대", "30대", "40대", "50대 이상", "응답하지 않음"],
    "rank": ["9급", "8급", "7급", "6급", "5급 이상", "응답하지 않음"],
    "facility": ["교도소", "구치소", "소년교도소·소년시설", "기타 교정기관", "응답하지 않음"],
    "career": ["5년 미만", "5~10년 미만", "10~20년 미만", "20년 이상", "응답하지 않음"],
    "hr_education": ["없음", "1회", "2~3회", "4회 이상", "응답하지 않음"],
    "mental_education": ["없음", "1회", "2회 이상", "응답하지 않음"],
}

DEMOGRAPHIC_LABELS = {
    "gender": "성별",
    "age": "연령대",
    "rank": "직급",
    "facility": "근무기관 유형",
    "career": "교정 경력",
    "hr_education": "최근 3년간 인권교육 경험",
    "mental_education": "정신건강 관련 교육 경험",
}


def factor_means(answers):
    grouped = {"감": [], "수": [], "성": []}
    for number, factor, _, _ in ITEMS:
        grouped[factor].append(answers[number])
    return {factor: round(float(np.mean(values)), 2) for factor, values in grouped.items()}


def subdomain_means(answers):
    grouped = {}
    for number, _, subdomain, _ in ITEMS:
        grouped.setdefault(subdomain, []).append(answers[number])
    return {name: round(float(np.mean(values)), 2) for name, values in grouped.items()}


def mental_factor_means(answers):
    grouped = {"감": [], "수": [], "성": []}
    for number, factor, _, _ in ITEMS:
        if number in MENTAL_ITEMS:
            grouped[factor].append(answers[number])
    return {factor: round(float(np.mean(values)), 2) for factor, values in grouped.items()}


def profile_summary(scores, tolerance=0.30):
    max_score = max(scores.values())
    min_score = min(scores.values())
    high_factors = [name for name, value in scores.items() if value == max_score]
    low_factors = [name for name, value in scores.items() if value == min_score]
    spread = max_score - min_score
    if spread < tolerance:
        return {
            "label": "비교적 균형적인 프로파일",
            "lead": "세 판단영역의 문항평균 차이가 크지 않습니다.",
            "detail": "특정 영역의 우열을 뜻하지 않으며, 실제 사례에서는 세 판단영역을 어떤 순서와 근거로 연결하는지 돌아보는 것이 좋습니다.",
            "focus": high_factors,
            "growth": low_factors,
        }
    high_text = "·".join(high_factors)
    low_text = "·".join(low_factors)
    return {
        "label": "영역별 차이가 나타난 프로파일",
        "lead": f"응답상 ‘{high_text}’ 영역을 상대적으로 익숙하게 활용하는 경향이 나타났으며, ‘{low_text}’ 영역은 더 의식적으로 성찰해 볼 여지가 있습니다.",
        "detail": "이 차이는 능력의 우열이나 결함을 뜻하지 않습니다. 자기보고식 응답에서 나타난 개인 내부의 상대적 경향입니다.",
        "focus": high_factors,
        "growth": low_factors,
    }


def reflection_items(answers, limit=3):
    """낮은 응답 중 감·수·성이 가능한 한 고르게 포함되도록 문항을 고릅니다."""
    values = list(answers.values())
    if len(set(values)) == 1:
        return []
    ordered = sorted(ITEMS, key=lambda item: (answers[item[0]], item[0]))
    selected, used_factors = [], set()
    for item in ordered:
        if item[1] not in used_factors:
            selected.append(item)
            used_factors.add(item[1])
        if len(selected) == limit:
            return selected
    for item in ordered:
        if item not in selected:
            selected.append(item)
        if len(selected) == limit:
            break
    return selected


def practice_topics(answers):
    """상대적으로 더 살펴볼 응답을 감·수·성별 연습주제로 바꿉니다. 별도 하위척도 판정은 하지 않습니다."""
    selected = reflection_items(answers)
    return [
        {
            "factor": factor,
            "item": text,
            "title": PRACTICE_GUIDES[factor]["title"],
            "steps": PRACTICE_GUIDES[factor]["steps"],
        }
        for _, factor, _, text in selected
    ]


def google_sheet():
    """Streamlit Secrets의 서비스 계정으로 연구자료 시트에 연결합니다."""
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=scope
    )
    client = gspread.authorize(credentials)
    spreadsheet_key = st.secrets["google_sheets"]["spreadsheet_key"]
    return client.open_by_key(spreadsheet_key).worksheet(WORKSHEET_NAME)


def research_row(answers, demographics):
    scores = factor_means(answers)
    sub_scores = subdomain_means(answers)
    headers = [
        "응답시각", "연구동의", "성별", "연령대", "직급", "근무기관유형",
        "교정경력", "인권교육경험", "정신건강교육경험",
    ]
    values = [
        datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S"),
        "동의함",
        demographics["gender"], demographics["age"], demographics["rank"],
        demographics["facility"], demographics["career"],
        demographics["hr_education"], demographics["mental_education"],
    ]
    for number, _, _, _ in ITEMS:
        headers.append(f"Q{number}")
        values.append(answers[number])
    headers += ["감평균", "수평균", "성평균"]
    values += [scores["감"], scores["수"], scores["성"]]
    for name in SUBDOMAIN_FEEDBACK:
        headers.append(name)
        values.append(sub_scores[name])
    return headers, values


def save_research_response(answers, demographics):
    sheet = google_sheet()
    headers, values = research_row(answers, demographics)
    existing_headers = sheet.row_values(1)
    if not existing_headers:
        sheet.append_row(headers, value_input_option="RAW")
    elif existing_headers != headers:
        raise ValueError("Google Sheets의 첫 행 열 제목이 현재 프로그램과 다릅니다.")
    sheet.append_row(values, value_input_option="RAW")


def find_korean_font():
    candidates = [
        "fonts/NanumGothicCoding.ttf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            font_manager.fontManager.addfont(path)
            return path
        except (FileNotFoundError, RuntimeError):
            continue
    return None


KOREAN_FONT_PATH = find_korean_font()


def radar_png(scores):
    labels = ["감", "수", "성"]
    values = [scores[label] for label in labels]
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
    values += values[:1]
    angles += angles[:1]
    fig = plt.figure(figsize=(4.5, 4.5))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, values, color="#4f6fad", linewidth=2)
    ax.fill(angles, values, color="#8ea6d5", alpha=0.35)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels)
    ax.set_ylim(1, 4)
    ax.set_yticks([1, 2, 3, 4])
    ax.grid(color="#d7dde6")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight", transparent=False)
    plt.close(fig)
    buf.seek(0)
    return buf


def make_result_pdf(scores, sub_scores, answers, action_plan):
    buffer = io.BytesIO()
    font_name = "Helvetica"
    if KOREAN_FONT_PATH:
        try:
            pdfmetrics.registerFont(TTFont("KoreanFont", KOREAN_FONT_PATH))
            font_name = "KoreanFont"
        except Exception:
            pass

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("KTitle", parent=styles["Title"], fontName=font_name, fontSize=18, leading=24, textColor=HexColor("#294b7a"), spaceAfter=12)
    h_style = ParagraphStyle("KH", parent=styles["Heading2"], fontName=font_name, fontSize=13, leading=18, textColor=HexColor("#294b7a"), spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle("KBody", parent=styles["BodyText"], fontName=font_name, fontSize=9.5, leading=15, wordWrap="CJK", spaceAfter=5)
    small_style = ParagraphStyle("KSmall", parent=body_style, fontSize=8, leading=12, textColor=HexColor("#59636e"))

    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    story = [
        Paragraph("감·수·성 인권적 직무판단 자기성찰 프로파일", title_style),
        Paragraph(f"작성 시각: {datetime.now(ZoneInfo('Asia/Seoul')).strftime('%Y-%m-%d %H:%M')}", small_style),
        Paragraph("이 결과는 개인의 인권 수준이나 직무역량을 판정하는 검사가 아니라, 자신의 응답 안에서 상대적으로 익숙하게 활용하는 판단영역과 더 성찰해 볼 영역을 찾기 위한 자료입니다.", body_style),
        Spacer(1, 4*mm),
    ]

    score_data = [["영역", "문항평균", "핵심 질문"], ["감(感)", f"{scores['감']:.2f}", FACTOR_META['감']['question']], ["수(受)", f"{scores['수']:.2f}", FACTOR_META['수']['question']], ["성(性)", f"{scores['성']:.2f}", FACTOR_META['성']['question']]]
    table = Table(score_data, colWidths=[32*mm, 28*mm, 95*mm])
    table.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),font_name),("FONTSIZE",(0,0),(-1,-1),9),("BACKGROUND",(0,0),(-1,0),HexColor("#dfe9f7")),("GRID",(0,0),(-1,-1),0.5,HexColor("#aeb8c5")),("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
    story += [table, Spacer(1, 5*mm)]

    summary = profile_summary(scores)
    story += [Paragraph("나의 프로파일 읽기", h_style), Paragraph(f"<b>{summary['label']}</b> — {summary['lead']} {summary['detail']}", body_style)]
    for factor in ["감", "수", "성"]:
        meta = FACTOR_META[factor]
        story += [Paragraph(meta["title"], h_style), Paragraph(meta["meaning"], body_style), Paragraph(f"실천 제안: {meta['practice']}", body_style)]

    story += [PageBreak(), Paragraph("한 사례를 감·수·성으로 다시 보기", h_style), Paragraph(INTEGRATED_PRACTICE, body_style)]
    story += [Paragraph("결과에 연결한 연습주제", h_style)]
    topics = practice_topics(answers)
    if topics:
        for topic in topics:
            story += [Paragraph(f"<b>{topic['title']}</b>", body_style), Paragraph(f"연결 문항: {topic['item']}", body_style), Paragraph(topic['steps'], body_style)]
    else:
        story.append(Paragraph("모든 문항에 같은 점수로 응답했습니다. 특정 문항을 우선순위로 정하지 않고, 실제 사례에서 감·수·성을 어떤 근거와 순서로 연결하는지 돌아보십시오.", body_style))

    story += [Paragraph("지금 성찰해 볼 세 문항", h_style)]
    selected_items = reflection_items(answers)
    if selected_items:
        for number, factor, _, text in selected_items:
            story.append(Paragraph(f"{number}. [{factor}] {text}", body_style))
        story += [Paragraph("성찰 질문", h_style), Paragraph(COMMON_REFLECTION_QUESTION, body_style)]
    else:
        story.append(Paragraph("모든 문항에 같은 점수로 응답했습니다. 특정 문항을 임의로 제시하지 않고, 실제 사례에서 감·수·성을 어떤 근거와 순서로 연결하는지 성찰해 보십시오.", body_style))

    story += [Paragraph("나의 한 가지 행동계획", h_style), Paragraph(action_plan.strip() if action_plan.strip() else "아직 작성하지 않았습니다.", body_style), Spacer(1, 5*mm), Paragraph("해석상 주의", h_style), Paragraph("영역 간 작은 점수 차이는 의미 있는 차이라고 단정할 수 없습니다. 다른 사람·기관과의 비교, 상·중·하 등급화, 인사평가, 법적·행정적 판단, 인권침해 가능성 예측에 사용할 수 없습니다. 점수는 최근 경험과 자기인식, 조직환경 및 사회적 바람직성의 영향을 받을 수 있습니다.", small_style)]

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def init_state():
    if "page" not in st.session_state:
        st.session_state.page = "intro"
    if "answers" not in st.session_state:
        st.session_state.answers = {}
    if "research_saved" not in st.session_state:
        st.session_state.research_saved = False
    if "question_index" not in st.session_state:
        st.session_state.question_index = 0


def save_answer_and_advance(number):
    """현재 응답을 저장하고 다음 문항으로 이동합니다."""
    value = st.session_state.get(f"q_{number}")
    if value is None:
        return
    st.session_state.answers[number] = value
    if st.session_state.question_index < len(ITEMS) - 1:
        st.session_state.question_index += 1
    else:
        st.session_state.answers = {
            item_number: st.session_state[f"q_{item_number}"]
            for item_number, _, _, _ in ITEMS
        }
        st.session_state.page = "demographics"


def previous_question():
    st.session_state.question_index = max(0, st.session_state.question_index - 1)


def next_answered_question():
    """이전에 응답한 문항을 다시 보는 경우 다음 문항으로 이동합니다."""
    number, _, _, _ = ITEMS[st.session_state.question_index]
    value = st.session_state.get(f"q_{number}")
    if value is None:
        return
    st.session_state.answers[number] = value
    if st.session_state.question_index < len(ITEMS) - 1:
        st.session_state.question_index += 1
    else:
        st.session_state.answers = {
            item_number: st.session_state[f"q_{item_number}"]
            for item_number, _, _, _ in ITEMS
        }
        st.session_state.page = "demographics"


def reset_profile():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def logo_html(css_class):
    """Streamlit 열 배치와 무관하게 로고 전체가 보이도록 고정 크기의 HTML 이미지를 만듭니다."""
    if not LOGO_PATH.exists():
        return ""
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f'<div class="logo-wrap {css_class}"><img src="data:image/png;base64,{encoded}" alt="감·수·성 로고"></div>'


def render_brand_bar():
    st.markdown(logo_html("page-logo"), unsafe_allow_html=True)
    st.markdown('<div class="brand-bar"><b>감·수·성</b> · 인권적 직무판단 자기성찰 프로파일</div>', unsafe_allow_html=True)


init_state()

if st.session_state.page == "intro":
    apply_intro_background()
    st.markdown(logo_html("intro-logo"), unsafe_allow_html=True)
    st.markdown('<div class="intro-kicker">알아차림 · 판단 · 성찰</div>', unsafe_allow_html=True)
    st.markdown('<div class="intro-title">감·수·성<br>인권적 직무판단<br>자기성찰 프로파일</div>', unsafe_allow_html=True)
    st.markdown('<div class="developer-credit">연구도구·문항 구성 및 화면 개발: 이성덕</div>', unsafe_allow_html=True)
    st.markdown('<div class="intro-lead">교정현장에서의 인권적 직무판단 경향을 감·수·성의 세 영역으로 살펴보는 25문항 자기점검입니다.</div>', unsafe_allow_html=True)
    factor_cols = st.columns(3)
    factor_intro = [
        ("감(感)", "정서와 취약성 알아차리기"),
        ("수(受)", "기준에 따라 대응 판단하기"),
        ("성(性)", "내 판단을 성찰하고 조정하기"),
    ]
    for col, (label, description) in zip(factor_cols, factor_intro):
        with col:
            st.markdown(f'<div class="factor-card"><b>{label}</b><span>{description}</span></div>', unsafe_allow_html=True)
    st.write("")
    st.markdown('<div class="notice"><b>참여 안내:</b> 최근 6개월의 근무 경험을 떠올려 가장 가까운 응답을 선택해 주세요. 예상 소요시간은 약 5~7분입니다.<br><br>정답이나 등급은 없으며, 이름·직원번호·정확한 소속기관 등 개인을 직접 식별하는 정보는 수집하지 않습니다. 응답 후에는 나의 감·수·성 프로파일 결과를 바로 확인하고 PDF로 내려받을 수 있습니다. 연구 참여에 동의한 응답은 개인을 식별할 수 없도록 처리하여 향후 척도와 교육프로그램 보완을 위한 연구자료로 활용됩니다.</div>', unsafe_allow_html=True)
    st.write("")
    if st.button("프로파일 확인 및 연구참여 안내 보기", type="primary", use_container_width=True):
        st.session_state.page = "consent"
        st.rerun()
    st.stop()


if st.session_state.page == "consent":
    render_brand_bar()
    st.title("연구 참여 설명 및 동의")
    st.markdown(f"**연구명:** {RESEARCH_TITLE}  \n**연구책임자:** {PRINCIPAL_INVESTIGATOR}  \n**IRB 승인번호:** {IRB_APPROVAL_NO}  \n**연구 문의:** {RESEARCH_CONTACT}")
    st.markdown(
        f"""
### 연구 목적

이 프로파일은 교정현장에서 인권 관련 상황을 마주할 때 자신이 평소 감.수.성의 판단영역을 어떻게 활용하고 있는지 돌아보기 위한 **교육용 자기성찰 활동**입니다. 참여자는 응답 결과를 통해 자신이 상대적으로
익숙하게 활용하는 영역과 앞으로 더 성찰해 볼 영역을 확인할 수 있습니다. 
아울러 동의한 응답자의 익명화된 자료는 감.수.성 척도의 타당성을 검토하고 향후 인권교육의 개선과 인권감수성 측정을 위한 후속연구에 활용됩니다.

### 참여 내용

- 감·수·성 자기보고 25문항과 최소한의 배경정보 7문항에 응답합니다.
- 예상 소요시간은 약 5~7분입니다.
- 이름, 직원번호, 휴대전화 번호, 정확한 소속기관명은 수집하지 않습니다.
- 성별·연령대·직급·근무기관 유형·경력·교육경험을 범주형으로 수집합니다.

### 자발성과 개인정보 보호

- 참여는 전적으로 자발적이며, 참여하지 않거나 중단해도 불이익이 없습니다.
- 제출 전에는 언제든 중단할 수 있습니다. 익명으로 제출된 뒤에는 연구자가 특정 응답을 찾아 삭제하기 어려울 수 있습니다.
- 자료는 통계적으로 분석하며 개인별 결과나 작은 집단을 식별할 수 있는 결과는 공개하지 않습니다.
- 자료 보유기간: **{DATA_RETENTION}**
- 응답은 연구 목적과 인권교육 개선을 위해서만 사용합니다.

### 예상되는 불편과 이익

일부 문항에서 자신의 편견·감정·조직관행을 돌아보며 일시적인 불편을 느낄 수 있습니다. 직접적인 보상은 없지만 개인 자기성찰 결과를 즉시 확인하고 PDF로 저장할 수 있습니다.
"""
    )
    consent = st.checkbox("위 설명을 읽고 이해했으며, 후속연구를 위한 익명 자료 제공에 자발적으로 동의합니다.", key="research_consent")
    st.caption("동의하지 않으면 연구 설문을 진행하거나 자료를 제출할 수 없습니다.")
    if st.button("동의하고 설문 시작", type="primary", use_container_width=True, disabled=not consent):
        st.session_state.page = "survey"
        st.rerun()
    st.stop()


if st.session_state.page == "survey":
    render_brand_bar()
    st.title("25개 문항 자기점검")
    answered = sum(1 for n, _, _, _ in ITEMS if st.session_state.get(f"q_{n}") is not None)
    current_index = min(st.session_state.question_index, len(ITEMS) - 1)
    number, factor, _, question_text = ITEMS[current_index]
    st.progress(
        answered / len(ITEMS),
        text=f"문항 {current_index + 1} / {len(ITEMS)} · 응답 완료 {answered} / {len(ITEMS)}",
    )
    st.caption("1 전혀 그렇지 않다 · 2 그렇지 않은 편이다 · 3 그런 편이다 · 4 매우 그렇다")

    if number == 7:
        with st.expander("‘정신건강 문제가 있는 수용자’의 의미", expanded=False):
            st.write("진단 여부와 관계없이 환청·망상, 심한 불안이나 흥분, 현저한 기능 저하 또는 자·타해 위험 등으로 인해 상황에 맞는 의사소통과 절차적·전문적 대응이 필요한 수용자를 의미합니다.")

    factor_class = {"감": "factor-gam", "수": "factor-su", "성": "factor-seong"}[factor]
    st.markdown(
        f'<div class="question"><span class="{factor_class}">{number}. [{factor}]</span> {question_text}</div>',
        unsafe_allow_html=True,
    )
    st.radio(
        f"{number}번 응답",
        options=[1, 2, 3, 4],
        format_func=lambda value: f"{value} · {SCALE_LABELS[value]}",
        index=None,
        key=f"q_{number}",
        label_visibility="collapsed",
        on_change=save_answer_and_advance,
        args=(number,),
    )

    st.caption("응답을 선택하면 자동으로 다음 문항으로 넘어갑니다.")
    navigation_columns = st.columns(2)
    with navigation_columns[0]:
        if current_index > 0:
            st.button("← 이전 문항", use_container_width=True, on_click=previous_question)
    with navigation_columns[1]:
        if st.session_state.get(f"q_{number}") is not None:
            st.button("다음 문항 →", type="primary", use_container_width=True, on_click=next_answered_question)
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
    sub_scores = subdomain_means(answers)
    mh_scores = mental_factor_means(answers)
    summary = profile_summary(scores)

    st.title("나의 자기성찰 프로파일")
    if st.session_state.research_saved:
        st.success("익명 연구자료가 정상적으로 제출되었습니다.")
    st.markdown(
        '<div class="notice">세 점수는 <b>각 영역의 1~4점 문항평균</b>입니다. 개인 내부의 상대적 경향만 살펴보며, 규준이나 절단점에 따른 높음·낮음 판정은 하지 않습니다.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("감(感)", f"{scores['감']:.2f}")
    c2.metric("수(受)", f"{scores['수']:.2f}")
    c3.metric("성(性)", f"{scores['성']:.2f}")

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=[scores["감"], scores["수"], scores["성"], scores["감"]], theta=["감", "수", "성", "감"], fill="toself", name="전체 프로파일", line=dict(color="#4f6fad")))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[1, 4], tickvals=[1, 2, 3, 4])), showlegend=False, height=410, margin=dict(l=45, r=45, t=35, b=35))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(summary["label"])
    st.write(summary["lead"])
    st.caption(summary["detail"])

    st.subheader("한 사례를 감·수·성으로 다시 보기")
    st.markdown(f'<div class="notice">{INTEGRATED_PRACTICE}</div>', unsafe_allow_html=True)

    st.subheader("결과에 연결한 연습주제")
    topics = practice_topics(answers)
    if topics:
        for topic in topics:
            with st.expander(topic["title"], expanded=True):
                st.markdown(f"**연결 문항:** {topic['item']}")
                st.write(topic["steps"])
    else:
        st.info("모든 문항에 같은 점수로 응답했습니다. 특정 문항을 우선순위로 정하지 않고, 실제 사례에서 감·수·성을 어떤 근거와 순서로 연결하는지 성찰해 보십시오.")

    st.subheader("세 판단영역의 의미와 실천 제안")
    for factor in ["감", "수", "성"]:
        meta = FACTOR_META[factor]
        with st.expander(f"{meta['title']} · {scores[factor]:.2f}", expanded=True):
            st.markdown(f"**핵심 질문:** {meta['question']}")
            st.write(meta["meaning"])
            st.info(f"실천 제안: {meta['practice']}")

    with st.expander("9개 내용영역과 연습 방향", expanded=False):
        st.caption("아래 9개 영역은 문항의 이론적 내용분류이며, 별도로 검증된 하위척도나 점수 순위가 아닙니다.")
        for name, guidance in SUBDOMAIN_FEEDBACK.items():
            st.markdown(f"**{name}**")
            st.write(guidance)

    with st.expander("정신건강 문제 상황에서의 응답 경향", expanded=False):
        st.write("문항 수가 감 3개, 수 3개, 성 2개로 다르므로 합계가 아니라 문항평균으로 제시합니다. 별도의 표준화된 하위척도나 유형 판정이 아닙니다.")
        cols = st.columns(3)
        for col, factor in zip(cols, ["감", "수", "성"]):
            col.metric(f"{factor} 평균", f"{mh_scores[factor]:.2f}")

    st.subheader("지금 성찰해 볼 세 문항")
    selected_items = reflection_items(answers)
    if selected_items:
        for number, factor, _, text in selected_items:
            st.markdown(f"**{number}. [{factor}] {text}**")
        st.markdown("**성찰 질문**")
        st.write(COMMON_REFLECTION_QUESTION)
    else:
        st.info("모든 문항에 같은 점수로 응답했습니다. 특정 문항을 임의로 제시하지 않고, 실제 사례에서 감·수·성을 어떤 근거와 순서로 연결하는지 성찰해 보십시오.")

    st.subheader("나의 한 가지 행동계획")
    action_plan = st.text_area(
        "다음 근무에서 시도할 작고 구체적인 행동을 적어보세요.",
        placeholder="예: 흥분한 수용자에게 지시하기 전, 감정을 단정하지 않고 현재 가장 불편한 점을 한 번 확인한다.",
        height=110,
    )

    st.warning("영역 간 작은 차이는 측정오차를 넘어서는 의미 있는 차이라고 단정할 수 없습니다. 결과를 타인·기관 비교, 상·중·하 등급화, 인사평가, 법적·행정적 판단 또는 인권침해 가능성 예측에 사용하지 마십시오.")

    pdf_bytes = make_result_pdf(scores, sub_scores, answers, action_plan)
    st.download_button("결과지 PDF 내려받기", data=pdf_bytes, file_name="감수성_자기성찰_프로파일_결과.pdf", mime="application/pdf", use_container_width=True)
    if st.button("처음부터 다시 하기", use_container_width=True):
        reset_profile()

    with st.expander("척도 및 문항 정보"):
        st.write(
            "이 프로그램은 이성덕의 「감(感)·수(受)·성(性) 모델 기반 "
            "교정공무원 인권감수성 예비척도 개발과 요인구조의 탐색적 검토」에 "
            "제시된 최종 25문항을 교육용 자기성찰 형식으로 구성한 것입니다."
        )
        st.write(
            "현재 단계에서는 개인의 인권 수준이나 직무역량을 판정하는 검사로 "
            "사용하지 않으며, 개인의 자기성찰과 익명화된 집단 수준의 교육 요구를 "
            "확인하기 위한 보조자료로 제한하여 활용하는 것이 적절합니다."
        )

        st.markdown(
            f"""
### 직접적인 척도 근거

- [**이성덕. 「감(感)·수(受)·성(性) 모델 기반 교정공무원 인권감수성 예비척도 개발과 요인구조의 탐색적 검토」**]({SCALE_PAPER_URL})
  - 이 프로그램에서 사용하는 최종 25문항과 3요인 구조의 직접적인 근거 논문입니다.
  - 논문 제목을 누르면 한국교정학회 「교정연구」 자료실로 이동합니다. 해당 논문의 **원문보기**를 선택할 수 있습니다.

### 감·수·성 모델 관련 연구

- [감(感)·수(受)·성(性) 인권감수성 모델을 통한 헌법 원리의 해석학적 탐색과 교육적 함의](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003327070)
- [감정 기반 인권 감수성 교육의 새로운 패러다임: ‘감(感)·수(受)·성(性)’ 모델의 이론적 정립과 철학적 기초](https://www.kci.go.kr/kciportal/landing/article.kci?arti_id=ART003245299)
- [이성덕 연구자 Google Scholar 프로필](https://scholar.google.com/citations?hl=ko&user=rcMXEpAAAAAJ)
"""
        )

    st.markdown(
        '<div class="rights-footer">© 2026 이성덕. All rights reserved.<br>감·수·성 로고 상표출원(심사 중)</div>',
        unsafe_allow_html=True,
    )
