from burnout_support import BAT_ITEMS, BAT_COLUMNS, BAT_LABELS, BAT_REFERENCE, BAT_PLAIN_MEANINGS, bat_scores
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
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.platypus import KeepTogether, Spacer, PageBreak, Image as RLImage, Paragraph, SimpleDocTemplate


st.set_page_config(
    page_title="감·수·성 모델로 돌아보는 나의 인권감수성",
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
SCALE_PAPER_URL = "https://doi.org/10.14819/krscs.2026.36.2.1.3"
MODEL_REFERENCES = (
    ("이론적 정립과 철학적 기초", "2025 · 법과인권교육연구 18(3), 117–145",
     "https://doi.org/10.35881/HLER.2025.18.3.6",
     "감정 인식, 규범적 판단, 성찰적 조정을 연결하는 모델의 이론적 토대입니다."),
    ("헌법 원리의 해석학적 탐색과 교육적 함의", "2026 · 법과인권교육연구 19(1), 99–128",
     "https://doi.org/10.35881/HLER.2026.19.1.5",
     "헌법재판소 판례 9건을 살펴 교정 현장의 인권적 판단을 돌아볼 교육적 질문에 근거를 제공합니다."),
    ("교정공무원 인권감수성 예비척도 개발과 요인구조의 탐색적 검토",
     "2026 · 교정연구 36(2), 3–27", SCALE_PAPER_URL,
     "결과지에서 사용하는 25문항과 감 9문항, 수 8문항, 성 8문항 구성의 직접 근거입니다."),
    ("감·수·성 구성요소 간 횡단적 관계에 관한 예비적 경험연구",
     "2026 · 법과인권교육연구 19(3), 37–67",
     "https://doi.org/10.35881/HLER.2026.19.3.2",
     "동일한 교정공무원 125명의 횡단 자기보고 자료에서 세 영역의 관련성을 예비적으로 확인했습니다. 시간적 순서나 인과관계는 별도의 검증이 필요합니다."),
)
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

DEMOGRAPHIC_OPTIONS = {
    "gender": ["남성", "여성"],
    "age": ["20대", "30대", "40대", "50대 이상"],
    "rank": ["9급", "8급", "7급", "6급", "5급 이상"],
    "facility": ["교도소", "구치소", "소년교도소·소년시설", "기타 교정기관"],
    "career": ["5년 미만", "5~10년 미만", "10~20년 미만", "20년 이상"],
    "hr_education": ["없음", "1회", "2~3회", "4회 이상"],
    "mental_education": ["없음", "1회", "2회 이상"],
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


REFLECTION_QUESTIONS = {
    1: "소란이 있었던 장면에서 두려움이나 불안을 짐작하게 한 말이나 행동이 있었나요?",
    2: "말투나 표정에서 어떤 감정을 떠올렸고, 그렇게 생각한 단서는 무엇이었나요?",
    3: "짐작한 감정을 확인하려면 무엇을 묻거나 더 관찰할 수 있었나요?",
    4: "수용자를 마주했을 때 어떤 감정이 들었고, 말투나 몸의 긴장에 어떻게 드러났나요?",
    5: "불안하거나 화가 났을 때 안전, 존중, 상황을 파악할 시간 중 무엇이 필요했나요?",
    6: "한 번 더 듣거나 관찰한 뒤 상대의 반응을 다르게 이해한 적이 있었나요?",
    7: "반응이 강했던 상황에서 환청이나 불안 등 다른 어려움의 가능성을 살피기 위해 무엇을 확인할 수 있었나요?",
    8: "흥분한 수용자에게 그 순간 꼭 필요한 말을 한 문장으로 어떻게 전달할 수 있을까요?",
    9: "불빛·소리·접촉 중 어떤 자극이 부담이 되었을 수 있고, 무엇을 조정할 수 있었나요?",
    10: "업무상 꼭 필요했던 조치는 무엇이었고, 그때 내 감정은 대응 강도에 어떤 영향을 주었나요?",
    11: "그때 느낀 감정은 무엇을 확인하라는 신호였고, 확인한 사실을 바탕으로 어떤 대응을 선택했나요?",
    12: "내 조치의 목적은 무엇이었고, 그 목적을 이루는 데 어느 정도의 조치가 필요했나요?",
    13: "서두를 때 놓치기 쉬운 절차는 무엇이며, 다음에는 어느 시점에 확인할 수 있을까요?",
    14: "권리를 제한한 조치의 근거는 무엇이었고, 같은 목적을 이루면서 권리를 덜 제한할 방법이 있었나요?",
    15: "자해 위험이 의심되는 장면이 있었다면, 어떤 신호를 확인하고 정해진 절차에 따라 누구에게 무엇을 알렸나요?",
    16: "내 판단으로 파악하기 어려웠던 점은 무엇이며, 전문가에게 어떤 관찰 내용을 전달할 수 있었나요?",
    17: "수용자의 당시 상태를 고려해 설명 방식, 대응 속도, 지원 요청 중 무엇을 조정할 수 있었나요?",
    18: "비슷한 행동에 다르게 대응한 적이 있다면, 관찰한 사실과 기존 인상이 각각 어떤 영향을 주었나요?",
    19: "그 사람의 현재 상황과 개별적인 필요를 파악하기 위해 무엇을 더 확인할 수 있었나요?",
    20: "동료의 기대가 내 선택에 영향을 주었나요? 내 판단 근거를 어떤 말로 설명할 수 있었나요?",
    21: "상급자나 선임과 의견이 달랐을 때, 판단 근거를 함께 확인하기 위해 어떤 질문을 할 수 있었나요?",
    22: "예전과 지금의 대응 방식에서 무엇이 달라졌고, 어떤 경험이 그 변화에 영향을 주었나요?",
    23: "실제 상황이 주는 부담과 그날 쌓인 피로나 스트레스를 어떻게 구분해 볼 수 있을까요?",
    24: "동료의 강한 말투가 내 대응에도 영향을 주었나요? 다음에는 무엇을 조정할 수 있을까요?",
    25: "‘문제 수용자’라는 인상에 어떤 관찰과 해석이 섞여 있었나요? 확인한 행동과 지원 필요를 중심으로 다시 설명해 보세요.",
}


def reflection_items(answers):
    groups = {}
    for factor in ("감", "수", "성"):
        rows = [(answers.get(number), number, item) for number, area, _, item in ITEMS
                if area == factor and answers.get(number) in SCALE_LABELS]
        rows.sort()
        picked = rows[:2]
        if len(rows) < 2:
            note = "유효한 응답 문항만 표시합니다."
        elif rows[0][0] == rows[-1][0]:
            note = "이 영역의 응답 점수가 모두 같아 설문 순서대로 두 문항을 골랐습니다."
        elif picked[0][0] >= 3:
            note = "두 문항 모두 ‘그런 편이다’ 이상입니다. 이 영역 안에서 상대적으로 낮은 응답입니다."
        elif picked[1][0] >= 3:
            note = "첫 문항에는 ‘그렇지 않다’ 쪽으로 응답했고, 두 번째는 함께 돌아볼 문항입니다."
        else:
            note = "두 문항 모두 ‘그렇지 않다’ 쪽으로 응답했습니다. 당시 상황과 근무 여건을 떠올려 보세요."
        if len(rows) > 2 and rows[1][0] == rows[2][0] and rows[0][0] != rows[-1][0]:
            note += " 선정 경계에서 동점인 문항은 설문 순서로 골랐습니다."
        groups[factor] = (note, picked)
    return groups


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
    burnout = st.session_state.get("burnout_answers", {})
    if bat_scores(burnout) is None:
        raise ValueError("직무소진 22문항을 모두 응답해 주세요.")
    headers += [*BAT_COLUMNS, "소진설문버전"]
    values += [burnout[c] for c in BAT_COLUMNS] + ["K-BAT22-table3-v1"]
    return headers, values


def save_research_response(answers, demographics):
    if not st.session_state.get("research_data_consent", False):
        raise PermissionError("연구자료 제공에 동의하지 않아 저장할 수 없습니다.")
    sheet = google_sheet()
    headers, values = research_row(answers, demographics)
    existing_headers = sheet.row_values(1)
    if not existing_headers:
        if sheet.col_count < len(headers):
            sheet.resize(cols=len(headers))
        sheet.append_row(headers, value_input_option="RAW")
    elif existing_headers != headers:
        # 기존 헤더가 정확한 접두부일 때에만 뒤에 확장한다. 기존 자료는 이동하지 않는다.
        if existing_headers != headers[:len(existing_headers)]:
            raise ValueError("기존 응답 시트의 열 순서가 다릅니다. 관리자에게 문의하십시오.")
        if sheet.col_count < len(headers):
            sheet.resize(cols=len(headers))
        sheet.update(range_name="A1", values=[headers], value_input_option="RAW")
    sheet.append_row(values, value_input_option="RAW")


def find_korean_font():
    candidates = [
        Path(__file__).parent / "fonts" / "NanumGothicCoding.ttf",
        Path(__file__).parent / "fonts" / "NotoSansKR-Regular.ttf",
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
    fig = plt.figure(figsize=(3.2, 3.2), facecolor="#f8fcff")
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor("#f8fcff")
    ax.plot(angles, values, color="#2589c8", linewidth=2.3, marker="o", markersize=4)
    ax.fill(angles, values, color="#75c0e8", alpha=0.34)
    ax.set_xticks(angles[:-1])
    tick_labels = ax.set_xticklabels([f"{label}\n{scores[label]:.2f}" for label in labels], color="#164b79", fontweight="bold")
    if KOREAN_FONT_PATH:
        font_prop = font_manager.FontProperties(fname=KOREAN_FONT_PATH)
        for label in tick_labels:
            label.set_fontproperties(font_prop)
    ax.set_ylim(1, 4)
    ax.set_yticks([1, 2, 3, 4])
    ax.set_yticklabels(["1", "2", "3", "4"], color="#7d9aae", fontsize=7)
    ax.grid(color="#cfe8f8", linewidth=0.8)
    ax.spines["polar"].set_color("#9fd3ef")
    ax.spines["polar"].set_linewidth(1)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight", transparent=False)
    plt.close(fig)
    buf.seek(0)
    return buf


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

BAT_PRACTICE = {
    "탈진": (
        "피로가 오래 남았던 근무를 며칠간 살펴보고, 연속 야간근무나 휴식이 밀린 날처럼 반복되는 조건을 찾아보세요.",
        "휴식이 반복해서 밀리면 교대 중 휴식 시간이나 업무 분담을 동료·책임자와 상의해 보세요.",
    ),
    "심적거리": (
        "업무에 마음이 멀어졌던 순간이 있다면 어떤 업무나 상황이었는지 한 가지 짚어보세요.",
        "특정 갈등이나 반복 업무 뒤에 이런 경험이 이어지면 동료와 그 상황을 짧게 돌아보거나 역할 분담을 상의해 보세요.",
    ),
    "인지적 조절 손상": (
        "인계나 기록에서 빠뜨리기 쉬운 항목을 짧게 적고, 업무가 중단됐다가 재개되면 마지막으로 확인한 지점부터 점검해 보세요.",
        "중요한 인계에서 누락이 반복되면 동료와 함께 재확인할 항목을 정해 보세요.",
    ),
    "정서적 조절 손상": (
        "말이 빨라지거나 목소리가 높아지는 신호를 살펴보세요. 안전이 확보되면 잠시 멈추고 전달할 핵심을 한 문장으로 정리해 보세요.",
        "긴장이 높은 대응 뒤 동료와 상황을 짧게 돌아보고, 비슷한 상황에서 지원을 요청할 시점을 정해 보세요.",
    ),
}

SCENE_PROMPT = "최근 수용자에게 대응했던 근무 장면 하나를 떠올려 보세요."
SCENE_QUESTIONS = {
    "감 · 알아차림": "그때 나와 상대에게 어떤 감정이나 도움이 필요한 신호가 있었나요?",
    "수 · 판단": "내 조치는 왜 필요했고, 어떤 절차나 권리를 덜 제한하는 방법을 고려했나요?",
    "성 · 성찰과 조정": "내 피로, 선입견, 동료 분위기는 대응에 어떤 영향을 주었고, 다음에는 무엇을 조정할까요?",
}
BURNOUT_NAMES = {
    "탈진": "몸과 마음의 탈진",
    "심적거리": "일에 대한 거리감",
    "인지적 조절 손상": "집중과 기억의 어려움",
    "정서적 조절 손상": "감정 조절의 어려움",
}
PROFILE_NOTE = (
    "각 점수는 이번에 해당 영역의 문항에 응답한 값의 평균(1~4점)입니다. "
    "높을수록 문항에 제시된 알아차림·판단·성찰 행동이 자신의 경험에 해당한다고 더 많이 응답한 것입니다. "
    "낮을수록 해당 행동이 자신의 경험에 해당한다고 응답한 정도가 낮으며, 어떤 상황에서 실천이 어려웠는지 돌아보는 단서가 됩니다. "
    "점수는 자기보고 결과로 인권 수준이나 실제 직무역량의 등급을 뜻하지 않습니다."
)
BURNOUT_NOTE = (
    "각 점수는 해당 영역의 경험 빈도에 답한 값의 평균(1~5점)입니다. "
    "1점에 가까울수록 해당 경험을 덜 자주, 5점에 가까울수록 더 자주 보고했습니다. "
    "예를 들어 3.50점은 여러 문항 응답을 평균한 값입니다."
)
REFERENCE_NOTE = (
    "선행연구 평균은 공기업 사무직 345명이 보고한 경험 빈도의 평균입니다. "
    "직무와 응답 여건이 다른 표본의 참고값이며 교정공무원 규준이나 위험 판정 기준으로 사용하지 않습니다. 실천 제안은 실제 근무 경험에 맞춰 골라 보세요."
)



def response_summary(scores):
    high, low = max(scores.values()), min(scores.values())
    if high == low:
        return ["이번 응답에서 세 영역의 문항평균이 같았습니다."]
    meanings = {
        "감": "나와 상대의 감정, 고통과 도움이 필요한 신호를 알아차리는 내용",
        "수": "조치의 목적과 필요성, 절차와 전문적 기준을 검토하는 내용",
        "성": "감정·편견·주변 분위기가 판단에 미친 영향을 돌아보고 대응을 조정하는 내용",
    }
    result = []
    for label, value, degree in (("가장 높은 평균", high, "더"), ("가장 낮은 평균", low, "덜")):
        factors = [factor for factor, score in scores.items() if score == value]
        topics = " / ".join(meanings[factor] for factor in factors)
        result.append(f"{label} · {'·'.join(factors)} {value:.2f}점. {topics}에 세 영역 중 상대적으로 {degree} 동의했습니다.")
    result.append("이번 응답 안에서의 비교입니다. 작은 점수 차이만으로 실제 직무역량 차이를 판단하기는 어렵습니다.")
    return result


def burnout_summary(burnout):
    displayed = {factor: round(score, 2) for factor, score in burnout.items()}
    high, low = max(displayed.values()), min(displayed.values())
    if high == low:
        return [f"이번 응답에서 네 영역의 평균은 모두 {high:.2f}점으로 같았습니다."]
    lines = []
    for label, value in (("가장 자주 보고한 경험", high), ("가장 덜 자주 보고한 경험", low)):
        names = ", ".join(BURNOUT_NAMES[factor] for factor, score in displayed.items() if score == value)
        lines.append(f"{label} · {names} {value:.2f}점")
    lines.append("이번에 응답한 네 영역 안에서 비교한 결과입니다.")
    return lines


def burnout_comparison(factor, score):
    mean = BAT_REFERENCE[factor][0]
    difference = round(round(score, 2) - round(mean, 2), 2)
    if difference == 0:
        return f"내 평균 {score:.2f}점과 선행연구 평균 {mean:.2f}점은 표시된 소수 둘째 자리까지 같습니다."
    direction = "높습니다" if difference > 0 else "낮습니다"
    return f"내 평균 {score:.2f}점은 선행연구 평균 {mean:.2f}점보다 {abs(difference):.2f}점 {direction}."


BURNOUT_REFERENCES = (
    ("한국판 직무소진평가척도(K-BAT) 타당화를 위한 예비연구",
     "조수현 (2020). 한국심리학회지: 산업 및 조직, 33(4), 461–499.",
     "https://doi.org/10.24230/kjiop.v33i4.461-499",
     "한국판 22문항과 네 영역 구성의 직접 근거입니다. 결과지의 비교 평균은 이 논문 표 5의 공기업 사무직 345명 자료를 사용합니다."),
    ("Burnout Assessment Tool (BAT)—Development, Validity, and Reliability",
     "Schaufeli, Desart, & De Witte (2020). International Journal of Environmental Research and Public Health, 17(24), 9495.",
     "https://doi.org/10.3390/ijerph17249495",
     "탈진, 심적거리, 인지적 조절 손상, 정서적 조절 손상을 구분한 원척도 개발 연구입니다. 네 영역의 의미를 설명하는 데 참고했습니다."),
)

BURNOUT_DETAILS = {
    "탈진": "근무가 끝난 뒤에도 기운이 돌아오지 않거나, 다음 근무를 시작할 때 이미 지쳐 있는 날이 반복되는지 살펴보세요.",
    "심적거리": "특정 업무나 갈등 이후 일에 대한 관심이 떨어지거나 사람을 대하는 일이 부담스러워지는 상황을 돌아보세요.",
    "인지적 조절 손상": "인계 중 다른 요청이 들어와 확인한 항목을 잊거나, 기록을 읽고도 핵심을 다시 확인해야 하는 장면을 떠올려 보세요.",
    "정서적 조절 손상": "긴장이 높은 대응에서 평소보다 말이 빨라지거나, 상황이 끝난 뒤에도 짜증이나 긴장이 오래 남는지 살펴보세요.",
}


def result_heading(title, *, green=False):
    from html import escape

    background, border, color = (
        ("#EDF6EF", "#AFCFBB", "#24644F") if green else ("#EDF5FB", "#A9CDE4", "#163752")
    )
    st.markdown(
        f'<h2 style="background:{background};border:1px solid {border};'
        f'border-radius:12px;color:{color};padding:12px 16px;margin:16px 0 12px;'
        f'font-size:clamp(1.15rem, 3vw, 1.55rem);line-height:1.4">'
        f'{escape(title)}</h2>',
        unsafe_allow_html=True,
    )


CIRCLED_NUMBERS = "①②③④⑤"


def burnout_detail_lines(factor, value):
    personal, shared = BAT_PRACTICE[factor]
    return (
        BAT_PLAIN_MEANINGS[factor],
        f"근무 장면 · {BURNOUT_DETAILS[factor]}",
        burnout_comparison(factor, value),
        f"내가 해볼 일 · {personal}",
        f"함께 조정할 일 · {shared}",
    )


def web_numbered_detail(index, text, followup=""):
    from html import escape

    extra = f'<div class="result-detail-followup">{escape(followup)}</div>' if followup else ""
    st.markdown(
        f'<div class="result-detail"><span>{CIRCLED_NUMBERS[index]}</span>'
        f'<div>{escape(text)}{extra}</div></div>',
        unsafe_allow_html=True,
    )


# 개인 결과 화면과 PDF에서 같은 해석 자료를 사용합니다.
EASY_GAM = {
    '감': ('감정과 상황 알아차리기', '나와 상대의 감정, 고통과 도움이 필요한 신호를 살펴보는 영역입니다.'),
    '수': ('사실과 기준에 따라 판단하기', '조치의 필요성, 권리를 덜 제한하는 대안, 절차와 전문가의 도움을 확인하는 영역입니다.'),
    '성': ('내 판단을 돌아보고 조정하기', '내 감정이나 선입견, 익숙한 관행이 판단에 미친 영향을 돌아보고 대응을 조정하는 영역입니다.'),
}
EASY_BAT = {
    '탈진': ('몸과 마음이 지치는 경험', '일하면서 몸과 마음이 지치고, 일을 마친 뒤에도 기운을 회복하기 어려운 경험입니다.'),
    '심적거리': ('일에서 마음이 멀어지는 경험', '일에 대한 관심이나 의미가 줄어드는 경험입니다. 동료와의 인간관계가 멀다는 뜻은 아닙니다.'),
    '인지적 조절 손상': ('집중과 생각 정리가 어려운 경험', '집중이 잘되지 않거나 깜빡하고, 생각을 또렷하게 정리하기 어려운 경험입니다. 지능이나 업무능력을 평가한 결과가 아닙니다.'),
    '정서적 조절 손상': ('감정을 다스리기 어려운 경험', '일하면서 짜증이나 슬픔이 생기거나, 감정적인 반응을 조절하기 어려운 경험입니다.'),
}
# 각 조합의 의미와 업무 질문은 교육용 탐색 제안이며, 검증된 심리유형이나 인과적 해석이 아닙니다.
COMBINED_THEMES = {
 ('감', '탈진'): {
  'title':'지친 날, 나와 상대의 신호 알아차리기',
  'meaning':'피로가 쌓인 상황에서 내 몸과 마음, 상대의 어려움을 알아차리는 데 무엇이 도움이 되는지 살펴보자는 제안입니다.',
  'question':'지친 날, 상대의 표정이나 호소를 지나치거나 내 피로 신호를 뒤늦게 알아차린 적이 있나요?',
  'practice':'근무 중 가능한 짧은 점검 시간에 내 몸의 신호 하나와 상대에게서 관찰한 신호 하나를 찾아보세요.',
  'resources':'쉴 수 있는 시간, 업무 분담, 동료와의 인계가 충분한지 함께 살펴보세요.'},
 ('감', '심적거리'): {
  'title':'익숙한 요구 속, 한 사람 다시 보기',
  'meaning':'반복되는 업무에서도 눈앞의 사람과 상황의 차이를 살펴볼 여지가 있는지 돌아보자는 제안입니다.',
  'question':'수용자의 요구를 듣기 전에 ‘또 같은 민원’이라고 생각한 적이 있나요? 이번 상황에서 달라진 점은 없었나요?',
  'practice':'익숙한 요구 한 가지에서 이전과 달라진 사실이나 도움이 필요한 신호를 하나 확인해 보세요.',
  'resources':'반복 민원에 대한 팀의 대응 기준, 역할 분담, 경험을 나눌 동료가 도움이 될 수 있습니다.'},
 ('감', '인지적 조절 손상'): {
  'title':'놓치기 쉬운 신호, 메모로 붙잡기',
  'meaning':'업무가 겹치거나 생각을 정리하기 어려울 때 상황의 신호를 놓치지 않을 방법을 찾아보자는 제안입니다.',
  'question':'여러 요구를 동시에 받으면서 상대의 호소나 상태 변화를 놓칠 뻔한 장면이 있었나요?',
  'practice':'인계할 내용을 ‘관찰한 사실, 상대의 호소, 확인할 사항’으로 나누어 짧게 적어보세요.',
  'resources':'인계 양식, 업무 중단을 줄이는 환경, 동료의 재확인이 도움이 되는지 살펴보세요.'},
 ('감', '정서적 조절 손상'): {
  'title':'내 감정과 상대의 상황, 나누어 보기',
  'meaning':'감정이 올라오는 상황에서 내 반응과 상대의 상태를 구분해 알아차릴 방법을 살펴보자는 제안입니다.',
  'question':'상대의 말에 화가 났을 때, 내 감정과 상대가 처한 어려움을 구분해서 살펴볼 수 있었나요?',
  'practice':'안전이 확보되면 내 감정에 이름을 붙이고, 상대의 상태는 추측으로 단정하지 말고 질문과 관찰로 확인해 보세요.',
  'resources':'긴장을 낮출 시간과 공간, 동료의 교대나 협력, 경험을 나눌 자원을 살펴보세요.'},
 ('수', '탈진'): {
  'title':'지친 날, 판단의 기준 확인하기',
  'meaning':'피로한 상황에서도 사실과 기준을 확인하는 데 무엇이 도움이 되는지 살펴보자는 제안입니다.',
  'question':'반복되는 요구를 받았을 때, 지쳐서 익숙한 방식으로 빨리 처리하고 싶었던 적이 있나요? 추가로 확인할 사실이나 다른 대응 방법은 없었나요?',
  'practice':'안전이 확보된 상황에서 주요 조치 전 ‘목적, 덜 제한적인 대안, 필요한 절차’를 한 번씩 확인해 보세요.',
  'resources':'충분한 휴식, 명확한 인계, 동료와의 판단 확인, 업무량과 역할 조정을 함께 살펴보세요.'},
 ('수', '심적거리'): {
  'title':'익숙한 절차의 이유 다시 찾기',
  'meaning':'의미 없이 느껴지는 절차에서도 무엇을 보호하려는 것인지 확인해 보자는 제안입니다.',
  'question':'설명이나 절차를 ‘해도 달라지지 않는 형식’으로 느낀 적이 있나요? 그 절차가 지키는 권리는 무엇인가요?',
  'practice':'자주 하는 조치 하나를 골라 ‘이 절차는 누구의 어떤 권리를 보호하는가?’를 동료와 이야기해 보세요.',
  'resources':'현장 사례를 다루는 교육, 판단 기준을 확인할 자료, 절차를 지킬 수 있는 업무 여건을 살펴보세요.'},
 ('수', '인지적 조절 손상'): {
  'title':'복잡한 상황, 한 단계씩 확인하기',
  'meaning':'정보가 많거나 집중하기 어려운 상황에서 사실과 기준을 차례로 정리하는 방법을 찾아보자는 제안입니다.',
  'question':'관찰한 사실, 다른 사람의 이야기, 나의 추정이 섞여 판단하기 어려웠던 장면이 있었나요?',
  'practice':'‘확인된 사실, 적용할 기준, 가능한 대응’ 순서로 적고 중요한 판단은 동료와 교차 확인해 보세요.',
  'resources':'확인 목록과 인계 기록, 판단을 함께 검토할 동료, 동시 업무 부담을 줄일 여건을 살펴보세요.'},
 ('수', '정서적 조절 손상'): {
  'title':'감정이 올라올 때, 기준으로 돌아오기',
  'meaning':'감정이 강하게 느껴지는 상황에서도 대응의 기준을 확인할 방법을 살펴보자는 제안입니다.',
  'question':'화나거나 억울한 상황에서 조치의 강도나 설명 방식이 달라졌던 적이 있나요?',
  'practice':'안전이 확보되면 ‘같은 사실이라면 다른 사람에게도 같은 조치를 할까?’를 확인해 보세요.',
  'resources':'동료와의 협력, 대응 후 검토 시간, 명확한 조치 기준이 도움이 되는지 살펴보세요.'},
 ('성', '탈진'): {
  'title':'지친 하루, 한 장면만 돌아보기',
  'meaning':'많이 지친 날에도 부담을 늘리지 않으면서 대응을 짧게 돌아볼 방법을 찾아보자는 제안입니다.',
  'question':'근무를 마치면 지쳐서 잘한 점과 바꿀 점을 돌아볼 여유가 없었던 적이 있나요?',
  'practice':'하루 한 장면만 골라 ‘잘한 점 하나, 다음에 바꿀 점 하나’를 한 줄씩 적어보세요.',
  'resources':'실제로 쉴 수 있는 시간, 짧은 인계와 되돌아보기 시간, 동료의 피드백을 살펴보세요.'},
 ('성', '심적거리'): {
  'title':'작은 변화로 일의 의미 다시 잇기',
  'meaning':'달라질 것이 없다고 느끼는 상황에서도 조정할 수 있는 행동과 업무 여건을 나누어 살펴보자는 제안입니다.',
  'question':'‘어차피 달라지지 않는다’는 생각으로 다른 대응을 시도할 가능성을 닫았던 적이 있나요?',
  'practice':'내가 바꿀 수 있는 작은 행동 하나와 팀이나 기관이 함께 바꿔야 할 문제 하나를 나누어 적어보세요.',
  'resources':'의견을 나눌 동료, 업무 개선 제안 경로, 작은 변화를 확인할 피드백을 살펴보세요.'},
 ('성', '인지적 조절 손상'): {
  'title':'흐릿한 기억, 기록으로 돌아보기',
  'meaning':'기억에만 기대지 않고 상황과 대응을 되짚어 볼 방법을 찾아보자는 제안입니다.',
  'question':'업무를 마친 뒤 상황의 순서나 내가 대응한 이유가 잘 떠오르지 않은 적이 있나요?',
  'practice':'‘사건, 내 대응, 상대 반응, 다음 대안’ 네 칸으로 짧게 정리해 보세요. 기록에는 필요한 사실만 남기세요.',
  'resources':'안전하게 관리되는 기록 양식, 되돌아볼 시간, 동료와의 사실 확인이 도움이 되는지 살펴보세요.'},
 ('성', '정서적 조절 손상'): {
  'title':'감정이 가라앉은 뒤, 다음 대응 고르기',
  'meaning':'감정적인 장면을 정당화하거나 자책하는 데 머무르지 않고 다음 대응으로 연결할 방법을 살펴보자는 제안입니다.',
  'question':'감정적으로 반응한 뒤 내 대응을 정당화하거나 자책하는 데 머문 적이 있나요?',
  'practice':'진정된 뒤 ‘내 감정, 실제 행동, 상대에게 미친 영향’을 구분하고 다음에 쓸 표현이나 협력 요청을 하나 정해보세요.',
  'resources':'비난 없이 검토할 동료, 대응 후 회복 시간, 필요하면 상담 자원을 함께 살펴보세요.'},
}
COMBINATION_NOTE = ('이 주제는 두 결과를 연결한 교육용 제안입니다. 고정된 성격유형이나 진단명이 아니며, '
                    '두 영역 사이의 원인과 결과를 확인한 것이 아닙니다. 경험에 맞지 않으면 자신을 설명에 맞출 필요가 없습니다.')


def burnout_total_mean(burnout):
    if not burnout or any(f not in burnout for f in EASY_BAT):
        return None
    counts = {f: sum(1 for _, domain, _ in BAT_ITEMS if domain == f) for f in EASY_BAT}
    return sum(float(burnout[f]) * counts[f] for f in counts) / sum(counts.values())


def combined_profile(scores, burnout):
    """반올림 전 문항평균으로 비교하고 동점은 모두 보존합니다. 임의의 차이 기준을 사용하지 않습니다."""
    result = {'low': [], 'high': [], 'pairs': [], 'note': ''}
    if not burnout or any(f not in scores for f in EASY_GAM) or any(f not in burnout for f in EASY_BAT):
        result['note'] = '두 설문의 유효한 점수가 있어야 함께 돌아볼 주제를 제안할 수 있습니다.'
        return result
    low = min(float(scores[f]) for f in EASY_GAM)
    high = max(float(burnout[f]) for f in EASY_BAT)
    result['low'] = [f for f in EASY_GAM if np.isclose(scores[f], low, rtol=0, atol=1e-9)]
    result['high'] = [f for f in EASY_BAT if np.isclose(burnout[f], high, rtol=0, atol=1e-9)]
    if len(result['low']) == 3 or len(result['high']) == 4:
        result['note'] = '한 설문의 모든 영역 점수가 같아 특정 조합을 우선 제안하지 않습니다. 아래의 관심 주제를 스스로 골라 살펴보셔도 됩니다.'
    else:
        result['pairs'] = [(g, b) for g in result['low'] for b in result['high']]
        result['note'] = ('동점인 영역이 있어 관련 주제를 함께 제안합니다. ' if len(result['pairs']) > 1 else '')
        result['note'] += '영역 간 차이가 작으면 다른 주제도 비슷하게 해당할 수 있습니다. 이 조합은 순위나 부족함을 판정한 결과가 아닙니다.'
    return result


def profile_reason(profile):
    if not profile['pairs']:
        return profile['note']
    g = ', '.join(f'{x} · {EASY_GAM[x][0]}' for x in profile['low'])
    b = ', '.join(BURNOUT_NAMES[x] for x in profile['high'])
    return f'내 응답에서 인권감수성은 {g}의 평균이 상대적으로 낮고, 소진 경험은 {b}의 평균이 상대적으로 높았습니다.'


def render_easy_results(scores, burnout):
    from html import escape as html_escape
    st.markdown('''<style>
    .easy-report{background:linear-gradient(135deg,#f6fbff,white 75%);padding:1.2rem;border:1px solid #d8e7f0;border-radius:18px;margin:.5rem 0 1.2rem}
    .easy-domain{border-bottom:1px solid #dce6ed;padding:.85rem 0;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:1rem}
    .easy-domain h4{font-size:1.12rem;margin:0 0 .25rem;color:#163752}
    .easy-domain p{font-size:1rem;margin:0;color:#40586a;line-height:1.6}
    .easy-score{font-size:1.2rem;font-weight:700;white-space:nowrap;color:#216f9e}
    .easy-green .easy-score{color:#24644f}.easy-green{background:linear-gradient(135deg,#f0f8f1,white 75%)}
    @media(max-width:520px){.easy-report{padding:1rem}.easy-domain{gap:.5rem}.easy-score{font-size:1.05rem}}
    </style>''', unsafe_allow_html=True)
    st.subheader('나의 응답을 이해하기')
    st.write('능력 평가나 진단이 아닌, 나의 판단과 근무 경험을 돌아보는 자료입니다.')
    st.markdown('### 1. 나의 인권감수성')
    rows = []
    for f, (label, meaning) in EASY_GAM.items():
        rows.append(f'<div class="easy-domain"><div><h4>{f} · {label}</h4><p>{html_escape(meaning)}</p></div><div class="easy-score">{scores[f]:.2f} / 4점</div></div>')
    st.markdown('<div class="easy-report">'+''.join(rows)+'</div>',unsafe_allow_html=True)
    st.caption('높을수록 해당 내용을 자신에게 더 해당한다고 응답했습니다. 타인의 평가나 실제 업무 수행을 직접 측정한 결과는 아닙니다.')
    st.markdown('### 2. 나의 직무소진 경험')
    if burnout is None:
        st.info('직무소진 유효 응답을 확인할 수 없습니다.')
    else:
        rows = []
        for f, (label, meaning) in EASY_BAT.items():
            rows.append(f'<div class="easy-domain"><div><h4>{label} · {BURNOUT_NAMES[f]}</h4><p>{html_escape(meaning)}</p></div><div class="easy-score">{burnout[f]:.2f} / 5점</div></div>')
        rows.append(f'<div class="easy-domain"><div><h4>직무소진 전체 평균</h4><p>22문항을 모두 평균한 점수입니다.</p></div><div class="easy-score">{burnout_total_mean(burnout):.2f} / 5점</div></div>')
        st.markdown('<div class="easy-report easy-green">'+''.join(rows)+'</div>',unsafe_allow_html=True)
        st.caption('높을수록 해당 경험을 더 자주 보고했습니다. 소진을 진단하는 기준이나 인사평가 점수가 아닙니다.')
    st.info('인권감수성은 1~4점, 소진은 1~5점입니다. 두 점수를 합치거나 크기를 직접 비교하지 않습니다. 낮거나 높은 영역은 내 응답 안에서의 비교입니다.')


def render_combined_results(scores, burnout):
    profile = combined_profile(scores, burnout)
    st.subheader('나에게 제안하는 성찰 주제')
    st.write(profile_reason(profile))
    if profile['pairs']:
        st.caption(profile['note'])
    for g, b in profile['pairs']:
        theme = COMBINED_THEMES[(g, b)]
        with st.container(border=True):
            st.caption(f'{g} · {EASY_GAM[g][0]} × {BURNOUT_NAMES[b]}')
            st.markdown('### '+theme['title'])
            for title_text, field in [('어떤 의미로 살펴볼까요?', 'meaning'), ('업무에서 떠올려 볼 장면', 'question'), ('이번 주, 한 가지만 시도해 보세요', 'practice'), ('나의 노력과 함께 필요한 자원', 'resources')]:
                st.markdown('**'+title_text+'**')
                st.write(theme[field])
    st.caption(COMBINATION_NOTE)
    with st.expander('다른 성찰 주제도 살펴보기 · 12개 조합'):
        choice = st.selectbox('관심 있는 주제', list(COMBINED_THEMES),
            format_func=lambda p: f'{p[0]} × {BURNOUT_NAMES[p[1]]} · {COMBINED_THEMES[p]["title"]}',
            index=None, key='explore_combined_theme')
        if choice is not None:
            t = COMBINED_THEMES[choice]
            st.caption('직접 선택해 살펴보는 주제입니다. 자동으로 매칭된 결과를 변경하지 않습니다.')
            st.markdown('**'+t['title']+'**')
            for k in ['meaning', 'question', 'practice', 'resources']:
                st.write(t[k])
    st.markdown('**내가 해볼 일 한 가지**')
    st.text_area('다음 근무에서 시도할 작은 실천', key='personal_action_plan', max_chars=1200,
                 placeholder='어떤 상황에서 무엇을 해볼지 적어보세요. 이름이나 사건 식별정보는 적지 마세요.')
    st.caption('이 메모는 연구 응답 시트에 추가 저장하지 않습니다. 입력 후 PDF를 내려받으면 결과지에 포함됩니다.')


def easy_pdf_pages(scores, burnout, report_paragraph, body, heading, caption, title, green_heading, doc):
    """설명 요약 한 쪽과 조합별 성찰 쪽. 기존 상세 해설은 뒤에 그대로 유지합니다."""
    from reportlab.platypus import Table, TableStyle
    from xml.sax.saxutils import escape
    compact = ParagraphStyle('EasyCompact', parent=body, fontSize=9.2, leading=13, spaceAfter=4)
    name_style = ParagraphStyle('EasyName', parent=compact, fontSize=10.2, leading=14, textColor=HexColor('#163752'))
    small_heading = ParagraphStyle('EasySection', parent=heading, fontSize=13, leading=18, spaceBefore=9, spaceAfter=6)
    green_section = ParagraphStyle('EasyGreenSection', parent=small_heading, textColor=HexColor('#24644f'))
    out = [report_paragraph('나의 응답을 이해하기', title),
           report_paragraph('능력 평가나 진단이 아닌, 나의 판단과 근무 경험을 돌아보는 자료입니다.', compact),
           report_paragraph('01  나의 인권감수성', small_heading)]
    def score_table(entries, maximum, bg):
        rows=[]
        for label, meaning, value in entries:
            rows.append([[report_paragraph(escape(label), name_style),report_paragraph(escape(meaning), compact)],
                         report_paragraph(f'{value:.2f} / {maximum}점', name_style)])
        table=Table(rows, colWidths=[doc.width-94,94], hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),HexColor(bg)),
            ('LINEBELOW',(0,0),(-1,-1),.4,HexColor('#dce7eb')),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        return table
    out.append(score_table([(f'{g} · {v[0]}',v[1],scores[g]) for g,v in EASY_GAM.items()],4,'#eff6fc'))
    out.append(report_paragraph('높을수록 해당 내용을 자신에게 더 해당한다고 응답했습니다.',compact))
    out.append(report_paragraph('02  나의 직무소진 경험',green_section))
    if burnout:
        out.append(score_table([(f'{v[0]} ({dict(zip(EASY_BAT, ["탈진", "심적거리", "인지적 어려움", "정서적 어려움"]))[f]})',v[1],burnout[f]) for f,v in EASY_BAT.items()],5,'#eff6f0'))
        out.append(report_paragraph(f'직무소진 전체 평균: {burnout_total_mean(burnout):.2f} / 5점 · 22문항 평균',name_style))
        out.append(report_paragraph('높을수록 해당 경험을 더 자주 보고했습니다. 진단이나 정상·위험 판정이 아닙니다.',compact))
    else:
        out.append(report_paragraph('직무소진 결과를 산출할 수 없습니다.',compact))
    out.append(report_paragraph('인권감수성은 1~4점, 소진은 1~5점입니다. 두 점수를 합치거나 크기를 직접 비교하지 않습니다. 낮거나 높은 영역은 내 응답 안에서의 비교이며 타인과의 순위가 아닙니다.',caption))
    profile=combined_profile(scores,burnout)
    pairs=profile['pairs']
    if not pairs:
        out.extend([PageBreak(),report_paragraph('두 결과를 함께 돌아보기',title),report_paragraph(profile['note'],body),
                    report_paragraph('나에게 필요한 작은 실천',heading),report_paragraph('최근 근무 중 돌아보고 싶은 장면 하나를 고르고, 내가 해볼 행동과 함께 필요한 자원을 나누어 적어보세요.',body),
                    report_paragraph(COMBINATION_NOTE,caption)])
    for g,b in pairs:
        theme=COMBINED_THEMES[(g,b)]
        out.extend([PageBreak(),report_paragraph('나에게 제안하는 성찰 주제',title),
            report_paragraph(f'{g} · {EASY_GAM[g][0]} × {BURNOUT_NAMES[b]}',caption),
            Table([[report_paragraph(escape(theme['title']), green_section)]], colWidths=[doc.width], style=TableStyle([('BACKGROUND',(0,0),(-1,-1),HexColor('#edf6ef')),('LEFTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)])),
            report_paragraph('이 주제가 나온 이유',heading),report_paragraph(profile_reason(profile),body),
            report_paragraph(profile['note'],caption)])
        for title_text,field in [('어떤 의미로 살펴볼까요?','meaning'),('업무에서 떠올려 볼 장면','question'),('이번 주, 한 가지만 시도해 보세요','practice'),('나의 노력과 함께 필요한 자원','resources')]:
            out.extend([report_paragraph(title_text,small_heading),report_paragraph(escape(theme[field]),body)])
        out.append(report_paragraph(COMBINATION_NOTE,caption))
    out.extend([PageBreak(),report_paragraph('자세히 살펴보기 · 영역별 해설과 연구 근거',title),
                report_paragraph('앞의 요약을 더 살펴보고 싶을 때 참고하세요. 기존 도표, 문항별 질문과 연구 근거를 이어서 제공합니다.',body)])
    return out



def make_result_pdf(scores, action_plan, burnout, selected=None):
    selected = selected or {}
    from xml.sax.saxutils import escape
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFError

    buffer = io.BytesIO()
    font = "HYGothic-Medium"
    pdfmetrics.registerFont(UnicodeCIDFont(font))
    for name in ("NotoSansKR-Regular.ttf", "NanumGothic.ttf", "NanumGothicCoding.ttf"):
        path = Path(__file__).with_name("fonts") / name
        if path.is_file():
            try:
                pdfmetrics.registerFont(TTFont("ReportSans", str(path)))
                font = "ReportSans"
                break
            except (TTFError, OSError, ValueError):
                continue

    hanja_path = Path(__file__).with_name("fonts") / "ReportHanja.ttf"
    hanja_chars = set()
    if hanja_path.is_file():
        try:
            pdfmetrics.registerFont(TTFont("ReportHanja", str(hanja_path)))
            hanja_chars = set(pdfmetrics.getFont("ReportHanja").face.charToGlyph)
        except (TTFError, OSError, ValueError):
            pass

    def report_paragraph(text, style):
        if hanja_chars:
            text = ''.join(f'<font name="ReportHanja">{ch}</font>' if 0x4e00 <= ord(ch) <= 0x9fff and ord(ch) in hanja_chars else ch for ch in text)
        if font == "HYGothic-Medium":
            text = text.replace("·", " / ")
        return Paragraph(text, style)

    navy = HexColor("#163752")
    green = HexColor("#24644F")
    muted = HexColor("#536577")
    rule = HexColor("#D9E2EA")
    styles = getSampleStyleSheet()
    body = ParagraphStyle("ResultBody", parent=styles["BodyText"], fontName=font,
                          fontSize=10, leading=14, wordWrap="CJK", spaceAfter=10,
                          textColor=HexColor("#202E3A"))
    heading = ParagraphStyle("ResultHeading", parent=body, fontSize=13,
                             leading=19, spaceBefore=15, textColor=navy, keepWithNext=True)
    title = ParagraphStyle("ResultTitle", parent=heading, fontSize=21, leading=29, spaceAfter=9)
    green_heading = ParagraphStyle("BurnoutHeading", parent=heading, textColor=green)
    green_title = ParagraphStyle("BurnoutTitle", parent=title, textColor=green)
    caption = ParagraphStyle("ReportCaption", parent=body, fontSize=9, textColor=muted)
    detail = ParagraphStyle("ResultDetail", parent=body, leftIndent=23,
                            bulletIndent=8, leading=12.5, spaceAfter=3)
    followup = ParagraphStyle("ResultFollowup", parent=detail, spaceAfter=6)

    def numbered_detail(index, text):
        return report_paragraph(f"{index + 1}. {escape(text)}", detail)
    reference = ParagraphStyle("ReferenceDetail", parent=caption, leftIndent=12)
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=24*mm, bottomMargin=21*mm)

    def draw_background(canvas, page):
        width, height = A4
        canvas.saveState()
        # 옅은 곡선은 여백에만 배치하여 본문 가독성을 유지합니다.
        canvas.setFillColor(HexColor('#edf6fc'))
        canvas.ellipse(width-76*mm, height-18*mm, width+24*mm, height+28*mm, stroke=0, fill=1)
        canvas.setFillColor(HexColor('#f0f7f1'))
        canvas.ellipse(-35*mm, -24*mm, 92*mm, 7*mm, stroke=0, fill=1)
        canvas.setStrokeColor(rule)
        canvas.line(20*mm, height - 19*mm, width - 20*mm, height - 19*mm)
        canvas.line(20*mm, 16*mm, width - 20*mm, 16*mm)
        canvas.setFillColor(muted)
        canvas.setFont(font, 8)
        canvas.drawString(20*mm, height - 15*mm, "교정공무원 감.수.성 인권감수성 판단구조 / K-BAT 직무소진 결과")
        canvas.drawString(20*mm, 11*mm, f"{page.page:02d}")
        canvas.drawRightString(width - 20*mm, 11*mm, "감·수·성 모델·척도 연구·개발 | 홍성교도소 이성덕")
        canvas.restoreState()

    def section_title(text, is_green=False):
        style = ParagraphStyle("SectionBand", parent=green_title if is_green else title,
                               backColor=HexColor("#EDF6EF" if is_green else "#EDF5FB"),
                               borderColor=HexColor("#AFCFBB" if is_green else "#A9CDE4"),
                               borderWidth=0.8, borderRadius=8, borderPadding=8,
                               fontSize=18, leading=26, spaceBefore=12, spaceAfter=18)
        return report_paragraph(text, style)

    from reportlab.platypus import Table, TableStyle
    def research_box(title_text, entries, *, is_green=False):
        color = "#24644F" if is_green else "#163752"
        rows = [[report_paragraph(title_text, green_heading if is_green else heading)]]
        for number, (label, citation, url, role) in enumerate(entries, 1):
            credit = escape(citation if is_green else f"이성덕({citation})")
            rows.append([[
                report_paragraph(f'{number}. <link href="{url}" color="{color}">{escape(label)}</link>', caption),
                report_paragraph(credit, reference),
                report_paragraph(escape(role), reference),
            ]])
        box = Table(rows, colWidths=[doc.width - 12], repeatRows=1)
        box.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#F2F7F3" if is_green else "#F1F6FB")),
            ("BOX", (0, 0), (-1, -1), 0.8, rule),
            ("LINEBELOW", (0, 0), (-1, 0), 0.6, rule),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        return box

    score_cards = Table([[
        report_paragraph(f"{label}<br/><font size='21'>{scores[factor]:.2f}</font>", heading)
        for factor, label in (("감", "감(感)  알아차림"), ("수", "수(受)  판단"), ("성", "성(性)  성찰과 조정"))
    ]], colWidths=[(doc.width - 12) / 3] * 3)
    score_cards.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), HexColor("#EDF4FB")),
        ("INNERGRID", (0, 0), (-1, -1), 3, HexColor("#FFFFFF")),
        ("LEFTPADDING", (0, 0), (-1, -1), 13),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story = [
        section_title("1. 감·수·성 인권감수성 결과"),
        report_paragraph("감·수·성 인권감수성 모델을 활용한 자기성찰 참고자료", body),
        report_paragraph("1) 나의 점수와 삼각형 도표", heading),
        score_cards, Spacer(1, 4*mm),
        report_paragraph("영역별 문항평균  |  1~4점", caption),
        report_paragraph(PROFILE_NOTE, body),
        RLImage(radar_png(scores), width=75*mm, height=75*mm, kind="proportional"),
        report_paragraph("2) 내 점수는 무엇을 보여주나요?", heading),
        *(report_paragraph(line, body) for line in response_summary(scores)),
    ]
    if LOGO_PATH.is_file():
        story.insert(0, RLImage(str(LOGO_PATH), width=13*mm, height=13*mm, kind="proportional"))
    story += [PageBreak(), section_title("2. 한 장면을 감·수·성으로 다시 보기"),
              report_paragraph(SCENE_PROMPT, body)]
    for index, (label, question) in enumerate(SCENE_QUESTIONS.items(), 1):
        factor = label[0]
        story.append(report_paragraph(f"{index}) {label} — {question}", heading))
        story.append(numbered_detail(0, FACTOR_META[factor]["meaning"]))
        story.append(numbered_detail(1, PRACTICE_GUIDES[factor]["steps"]))
    story.extend([PageBreak(), section_title("3. 내 응답에서 돌아볼 여섯 가지")])
    for index, (factor, (note, rows)) in enumerate(selected.items(), 1):
        story.extend([report_paragraph(f"{index}) {factor} — {dict(감='알아차림', 수='판단', 성='성찰과 조정')[factor]}", heading), report_paragraph(note, followup)])
        for item_index, (score, number, item) in enumerate(rows):
            story.append(KeepTogether([
                numbered_detail(item_index, f"{number}번 · {score}점 ({SCALE_LABELS[score]}) · {item}"),
                report_paragraph(f"돌아볼 질문 · {REFLECTION_QUESTIONS[number]}", followup),
            ]))
    story.extend([Spacer(1, 10), research_box("감·수·성 모델과 결과지의 연구 근거", MODEL_REFERENCES)])
    story.extend([PageBreak(), section_title("4. 직무소진 결과", True)])
    if burnout is None:
        story.append(report_paragraph("직무소진 결과를 산출할 수 없습니다.", body))
    else:
        story.append(report_paragraph("1) 나의 점수와 막대그래프", green_heading))
        for factor, value in burnout.items():
            story.append(report_paragraph(f"{BURNOUT_NAMES[factor]} {value:.2f}", body))
            chart_width = doc.width - 12
            chart = Drawing(chart_width, 9)
            chart.add(Rect(0, 2, chart_width, 6, fillColor=HexColor("#e3f0e8"), strokeColor=None))
            chart.add(Rect(0, 2, chart_width * value / 5, 6,
                           fillColor=HexColor("#409773"), strokeColor=None))
            story.append(chart)
        story.append(report_paragraph("2) 내 점수는 무엇을 보여주나요?", green_heading))
        story.append(report_paragraph(BURNOUT_NOTE, body))
        story.extend(report_paragraph(line, body) for line in burnout_summary(burnout))
        story.extend([PageBreak(), section_title("5. 직무소진 영역별 해설", True)])
        story.append(report_paragraph(REFERENCE_NOTE, body))
        for index, (factor, value) in enumerate(burnout.items(), 1):
            story.append(KeepTogether([
                report_paragraph(f"{index}) {BURNOUT_NAMES[factor]} · {value:.2f}점", green_heading),
                *(numbered_detail(item_index, line)
                  for item_index, line in enumerate(burnout_detail_lines(factor, value))),
            ]))

    if burnout is not None:
        story.extend([Spacer(1, 10), research_box("직무소진 결과의 연구 근거", BURNOUT_REFERENCES, is_green=True)])

    story.extend([
        PageBreak(), section_title("6. 나의 실천사항"),
        report_paragraph("다음 근무의 어떤 상황에서 무엇을 해볼지 적어보세요.", body),
    ])
    if action_plan.strip():
        story.extend([
            report_paragraph("설문에서 작성한 실천사항", heading),
            report_paragraph(escape(action_plan.strip()).replace("\n", "<br/>"), body),
        ])
    story.extend([
        report_paragraph("1) 어떤 상황에서", heading),
        Spacer(1, 2*mm),
    ])
    for label, count in (("", 3), ("2) 무엇을 해볼지", 4), ("3) 필요한 도움이나 함께 조정할 일", 3)):
        if label:
            story.extend([Spacer(1, 5*mm), report_paragraph(label, heading), Spacer(1, 2*mm)])
        lines = Drawing(doc.width - 12, count * 9*mm)
        for index in range(count):
            lines.add(Rect(0, index * 9*mm, doc.width - 12, 0.35,
                           fillColor=rule, strokeColor=None))
        story.append(lines)
    story = easy_pdf_pages(scores, burnout, report_paragraph, body, heading, caption, title, green_heading, doc) + story
    doc.build(story, onFirstPage=draw_background, onLaterPages=draw_background)
    return buffer.getvalue()

def init_state():
    if "burnout_index" not in st.session_state:
        st.session_state.burnout_index = 0
    if "burnout_answers" not in st.session_state:
        st.session_state.burnout_answers = {}
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
        st.session_state.page = "burnout"


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
        st.session_state.page = "burnout"


def save_burnout_and_advance(original):
    """화면 전환으로 위젯이 정리되어도 응답을 별도 사전에 보존한다."""
    value = st.session_state.get(f"bat_question_{original}")
    if value not in (1, 2, 3, 4, 5):
        return
    st.session_state.burnout_answers[f"BAT{original}"] = value
    if st.session_state.burnout_index < len(BAT_ITEMS) - 1:
        st.session_state.burnout_index += 1
    elif bat_scores(st.session_state.burnout_answers) is not None:
        st.session_state.page = "demographics"


def previous_burnout_question():
    st.session_state.burnout_index = max(0, st.session_state.burnout_index - 1)


def logo_html(css_class):
    """Streamlit 열 배치와 무관하게 로고 전체가 보이도록 고정 크기의 HTML 이미지를 만듭니다."""
    if not LOGO_PATH.exists():
        return ""
    encoded = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f'<div class="logo-wrap {css_class}"><img src="data:image/png;base64,{encoded}" alt="감·수·성 로고"></div>'


def render_brand_bar():
    st.markdown(logo_html("page-logo"), unsafe_allow_html=True)
    st.markdown('<div class="brand-bar"><b>감·수·성 인권감수성</b> · 자기성찰과 직무소진 자기점검</div>', unsafe_allow_html=True)


init_state()

# 동의하지 않은 세션은 설문 및 결과 경로에 진입하지 않습니다.
if st.session_state.page in {"survey", "burnout", "demographics", "result"} and not st.session_state.get("research_data_consent", False):
    st.session_state.page = "consent"

if st.session_state.page == "intro":
    apply_intro_background()
    st.markdown(logo_html("intro-logo"), unsafe_allow_html=True)
    st.markdown('<div class="intro-kicker">알아차림 · 판단 · 성찰과 조정</div>', unsafe_allow_html=True)
    st.markdown('<div class="intro-title">감·수·성 모델로 돌아보는<br>나의 인권감수성</div>', unsafe_allow_html=True)
    st.markdown('<div class="developer-credit">연구도구·문항 구성 및 화면 개발: 이성덕</div>', unsafe_allow_html=True)
    counts = len(ITEMS), len(BAT_ITEMS), len(DEMOGRAPHIC_OPTIONS)
    st.markdown(
        '<div class="intro-lead">감·수·성 인권감수성 모델은 교정현장에서 내가 무엇을 알아차리고, '
        '어떤 기준으로 판단하며, 내 대응을 어떻게 돌아보고 조정하는지 살펴보는 틀입니다.<br>'
        '이 자기점검에서는 직무소진 경험도 함께 살펴봅니다.<br>'
        f'<b>약 10~15분 · 감·수·성 {counts[0]}문항 · 직무소진 {counts[1]}문항 · '
        f'일반사항 {counts[2]}문항(총 {sum(counts)}문항)</b></div>',
        unsafe_allow_html=True,
    )
    for col, (label, question) in zip(st.columns(3), SCENE_QUESTIONS.items()):
        with col:
            st.markdown(f'<div class="factor-card"><b>{label}</b><span>{question}</span></div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="notice"><b>응답 방법</b><br>감·수·성 문항은 최근 6개월의 근무 경험을 떠올려 답해 주세요. '
        '직무소진은 해당 화면의 안내에 따라 응답해 주세요.<br><br>'
        '<b>참여와 결과</b><br>연구 참여 설명을 읽고 동의하면 자기점검을 시작할 수 있습니다. '
        '참여는 자발적이며, 설문에 참여하지 않아도 교육과 토론에 동일하게 참여할 수 있습니다. '
        '응답을 제출하면 두 결과를 확인하고 통합 PDF를 내려받을 수 있습니다.<br><br>'
        '<b>개인정보와 자료 활용</b><br>이름, 직원번호, 휴대전화 번호, 정확한 소속기관명은 수집하지 않습니다. '
        '교육에서는 개인이 드러나지 않는 집계 결과를 활용하며, 동의 후 제출한 자료는 척도의 타당성 검토와 '
        '인권교육 개선을 위한 연구에 활용합니다.</div>',
        unsafe_allow_html=True,
    )
    if st.button("연구 참여 설명 및 동의 안내 보기", type="primary", use_container_width=True):
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

이 설문은 교정현장에서 자신의 판단 경향과 근무 경험을 돌아보고, 교육에서 함께 다룰 주제와 지원이 필요한 부분을 찾기 위한 **교육용 자기성찰·자기점검 활동**입니다. 참여자는 자신의 응답을 돌아보는 참고자료를 제공받습니다. 개인의 능력이나 자질을 판정하거나 등급을 매기기 위한 활동이 아닙니다. 
아울러 동의한 응답자의 익명화된 자료는 감.수.성 척도의 타당성을 검토하고 향후 인권교육의 개선과 인권감수성 측정을 위한 후속연구에 활용됩니다.

### 참여 내용

- 감·수·성 자기보고 25문항, 직무소진 22문항과 배경정보 7문항에 응답합니다.
- 직무소진은 네 영역별 개인 피드백과 교육자용 익명 비교·집계에 사용됩니다. 진단이나 인사평가 목적으로 사용하지 않습니다.
- 예상 소요시간은 약 10~15분입니다.
- 이름, 직원번호, 휴대전화 번호, 정확한 소속기관명은 수집하지 않습니다.
- 성별·연령대·직급·근무기관 유형·경력·교육경험을 범주형으로 수집합니다.

### 자발성과 개인정보 보호

- 참여는 전적으로 자발적이며, 참여하지 않거나 중단해도 불이익이 없습니다.
- 제출 전에는 언제든 중단할 수 있습니다. 익명으로 제출된 뒤에는 연구자가 특정 응답을 찾아 삭제하기 어려울 수 있습니다.
- 자료는 통계적으로 분석하며 개인별 결과나 작은 집단을 식별할 수 있는 결과는 공개하지 않습니다.
- 자료 보유기간: **{DATA_RETENTION}**
- 연구자료 제공에 동의한 응답만 연구 목적과 인권교육 개선을 위해 저장·활용합니다.
- 연구자료 제공에 동의한 분만 자기점검을 진행할 수 있습니다. 동의하지 않아도 교육과 토론에는 불이익 없이 참여할 수 있습니다.

### 예상되는 불편과 이익

일부 문항에서 자신의 편견·감정·조직관행을 돌아보며 일시적인 불편을 느낄 수 있습니다. 직접적인 보상은 없지만 자신의 판단 경향과 근무 경험을 돌아볼 참고자료를 즉시 확인하고 PDF로 저장할 수 있습니다.
"""
    )
    st.markdown("**나의 응답이 더 나은 인권교육을 만드는 데 도움이 됩니다.**")
    st.write("연구자료 제공에 동의하시면, 응답은 감·수·성 척도를 검토하고 교정현장의 경험을 반영한 인권교육을 개선하는 데 활용됩니다. 동의 후 자기점검을 진행하고 개인 결과와 PDF를 확인할 수 있습니다.")
    st.markdown("**위 설명을 읽고 이해하셨다면, 자발적인 동의 여부를 확인해 주세요.**")
    st.markdown(
        """<style>
        .st-key-research_consent_choice [data-testid="stRadio"] label {
            min-height: 48px;
            padding: 10px 14px;
            border: 1px solid #cfe0ec;
            border-radius: 12px;
            background: #ffffff;
            cursor: pointer;
        }
        .st-key-research_consent_choice [data-testid="stRadio"] label p {
            font-size: 1.1rem;
        }
        </style>""",
        unsafe_allow_html=True,
    )
    consent_choice = st.radio(
        "연구 참여 동의 여부",
        options=["연구자료 제공에 동의합니다"],
        captions=[
            "나의 응답을 인권감수성 연구와 교육 개선에 활용하도록 제공합니다.",
        ],
        index=None,
        horizontal=False,
        key="research_consent_choice",
    )
    st.caption("동의하지 않으시면 선택하지 않고 화면을 닫으셔도 됩니다. 자기점검에는 참여하지 않아도 교육과 토론에는 불이익 없이 참여할 수 있습니다.")
    if st.button("나의 자기점검 시작", type="primary", use_container_width=True, disabled=consent_choice != "연구자료 제공에 동의합니다"):
        st.session_state.research_data_consent = consent_choice == "연구자료 제공에 동의합니다"
        st.session_state.research_saved = False
        st.session_state.page = "survey"
        st.rerun()
    st.stop()


if st.session_state.page == "survey":
    render_brand_bar()
    st.title("나의 인권감수성은 어떤 모습일까?")
    st.markdown("**감·수·성으로 돌아보는 나의 인권적 직무판단**")
    st.caption("인권감수성의 높고 낮음을 판정하기보다, 자신이 보고한 판단 경향을 돌아보는 활동입니다.")
    answered = len(st.session_state.answers)
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

    factor_class = "factor-gam"
    st.markdown(
        f'<div class="question"><span class="{factor_class}">{number}.</span> {question_text}</div>',
        unsafe_allow_html=True,
    )
    key = f"q_{number}"
    if key not in st.session_state and number in st.session_state.answers:
        st.session_state[key] = st.session_state.answers[number]
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


if st.session_state.page == "burnout":
    st.markdown("""
<style>
.stApp {background:linear-gradient(145deg,#f7fcf8 0%,#e5f4eb 52%,#f7fcf8 100%) !important;}
h1,h2,h3 {color:#185c3b !important;}
.brand-bar {background:#f0faf3 !important; border-color:#b9ddc8 !important; color:#216b46 !important;}
.question {background:#f4fcf6 !important; border:1px solid #acd4bc !important; border-left:5px solid #369566 !important; color:#174f35 !important;}
div[data-testid="stButton"] > button {background:linear-gradient(135deg,#42a978,#207849) !important; color:white !important; box-shadow:0 7px 16px rgba(32,120,73,.16) !important;}
div[data-testid="stButton"] > button:hover {background:linear-gradient(135deg,#329362,#17613b) !important;}
[data-testid="stProgress"] [role="progressbar"] > div {background-color:#329362 !important;}
[data-testid="stRadio"] label {color:#185c3b !important;}
[data-testid="stRadio"] input {accent-color:#278453 !important;}
</style>
""", unsafe_allow_html=True)
    render_brand_bar()
    st.title("일하는 동안, 나의 마음과 몸은 어떨까?")
    st.markdown("**직무소진 네 영역으로 살펴보는 나의 근무 경험**")
    st.write("평소 근무 경험에서 각 문장이 자신에게 얼마나 해당하는지 응답해 주세요. 앞선 감·수·성 4점 척도와 달리 여기서는 1~5점으로 응답합니다.")
    current = min(max(st.session_state.burnout_index, 0), len(BAT_ITEMS) - 1)
    original, factor, question = BAT_ITEMS[current]
    answered = sum(st.session_state.burnout_answers.get(c) in (1, 2, 3, 4, 5) for c in BAT_COLUMNS)
    st.progress(answered / len(BAT_ITEMS), text=f"문항 {current + 1} / {len(BAT_ITEMS)} · 응답 완료 {answered} / {len(BAT_ITEMS)}")
    st.caption("1 전혀 아니다 · 2 드물게 그렇다 · 3 때때로 그렇다 · 4 자주 그렇다 · 5 항상 그렇다")
    st.markdown(f'<div class="question">{current + 1}. {question}</div>', unsafe_allow_html=True)
    key = f"bat_question_{original}"
    saved = st.session_state.burnout_answers.get(f"BAT{original}")
    # 재방문 시 사전에 보관한 응답으로 위젯을 복원한다.
    if key not in st.session_state and saved in (1, 2, 3, 4, 5):
        st.session_state[key] = saved
    st.radio("직무소진 응답", options=[1, 2, 3, 4, 5],
             format_func=lambda v: f"{v} · {BAT_LABELS[v]}", index=None,
             key=key, label_visibility="collapsed",
             on_change=save_burnout_and_advance, args=(original,))
    st.caption("응답을 선택하면 자동으로 다음 문항으로 넘어갑니다.")
    left, right = st.columns(2)
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
    if not st.session_state.get("research_data_consent", False):
        st.session_state.page = "consent"
        st.rerun()
    render_brand_bar()
    st.title("기본정보")
    st.markdown('<div class="notice">정확한 기관명은 수집하지 않습니다. 모든 항목은 범주형이며, 각 항목을 선택하시면 제출할 수 있습니다.</div>', unsafe_allow_html=True)
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
    selected = reflection_items(answers)
    burnout = bat_scores(st.session_state.get("burnout_answers", {}))

    st.title("나의 자기점검 결과")
    if st.session_state.research_saved:
        st.success("익명 연구자료가 제출되었습니다. 인권감수성 연구와 교육 개선에 기여해 주셔서 감사합니다.")
    st.caption("두 결과는 자기성찰을 위한 참고자료입니다. 인사평가나 진단에 사용하지 않습니다.")
    st.markdown(
        """
        <style>
        [data-testid="stTabs"] [role="tab"] {
            min-height: 48px;
            padding-inline: 10px;
            white-space: normal;
        }
        [data-testid="stTabs"] [role="tab"] p,
        [data-testid="stExpander"] summary p {
            font-size: 1.15rem !important;
            font-weight: 650;
            line-height: 1.4;
        }
        [data-testid="stTabs"] [data-testid="stExpander"] {
            margin-block: 5px;
        }
        [data-testid="stExpanderDetails"] {
            padding-inline-start: 1.1rem;
        }
        [data-testid="stTabs"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stExpanderDetails"] [data-testid="stMarkdownContainer"] p {
            line-height: 1.42;
        }
        [data-testid="stTabs"] [data-testid="stMarkdownContainer"] p + p,
        [data-testid="stExpanderDetails"] [data-testid="stMarkdownContainer"] p + p {
            margin-top: 0.8rem;
        }
        [data-testid="stTabs"] [data-testid="stMarkdownContainer"],
        [data-testid="stExpanderDetails"] [data-testid="stMarkdownContainer"] {
            padding-bottom: 0.25rem;
        }
        .result-detail {
            display: grid;
            grid-template-columns: 1.35em minmax(0, 1fr);
            gap: 0.3em;
            margin: 0.15rem 0 0.3rem 0.45rem;
            line-height: 1.35;
            overflow-wrap: anywhere;
        }
        .result-detail > span { color: #24627F; font-weight: 650; }
        .result-detail-followup { margin-top: 0.25rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    easy_tab, combined_tab, gam_tab, burnout_tab = st.tabs([
        "내 결과 한눈에", "나의 성찰 주제", "인권감수성 자세히", "직무소진 자세히"])
    with easy_tab:
        render_easy_results(scores, burnout)
    with combined_tab:
        render_combined_results(scores, burnout)

    with gam_tab:
        result_heading("1. 감·수·성 인권감수성 결과")
        st.subheader("1) 나의 점수와 삼각형 도표")
        st.write(" · ".join(f"**{factor} {value:.2f}**" for factor, value in scores.items()))
        st.image(radar_png(scores), width=290)
        st.subheader("2) 내 점수는 무엇을 보여주나요?")
        st.write(PROFILE_NOTE)
        for line in response_summary(scores):
            st.write(line)

        result_heading("2. 한 장면을 감·수·성으로 다시 보기")
        st.write(SCENE_PROMPT)
        for index, (label, question) in enumerate(SCENE_QUESTIONS.items(), 1):
            st.markdown(f"**{index}) {label}**  \n{question}")
        for factor, meta in FACTOR_META.items():
            with st.expander(f"{meta['title']} · 돌아볼 문항과 실천"):
                web_numbered_detail(0, meta["meaning"])
                web_numbered_detail(1, f"실천 제안 · {PRACTICE_GUIDES[factor]['steps']}")
        result_heading("3. 내 응답에서 돌아볼 여섯 가지")
        st.write("각 영역에서 낮은 응답 순으로 두 문항씩 골랐습니다. 경험과 가까운 문항 하나부터 살펴보세요.")
        for index, (factor, (note, rows)) in enumerate(selected.items(), 1):
            with st.expander(f"{index}) {FACTOR_META[factor]['title']} · 돌아볼 두 문항", expanded=True):
                st.caption(note)
                for item_index, (score, number, item) in enumerate(rows):
                    web_numbered_detail(
                        item_index,
                        f"{number}번 · {score}점 ({SCALE_LABELS[score]}) · {item}",
                        f"돌아볼 질문 · {REFLECTION_QUESTIONS[number]}",
                    )
    with burnout_tab:
        result_heading("4. 직무소진 결과", green=True)
        if burnout is None:
            st.info("직무소진 결과를 산출할 수 없습니다.")
        else:
            st.subheader("1) 나의 점수와 막대그래프")
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
            st.subheader("2) 내 점수는 무엇을 보여주나요?")
            st.write(BURNOUT_NOTE)
            for line in burnout_summary(burnout):
                st.write(line)
            maximum = max(round(value, 2) for value in burnout.values())
            minimum = min(round(value, 2) for value in burnout.values())
            result_heading("5. 직무소진 영역별 해설", green=True)
            st.caption(REFERENCE_NOTE)
            for number, (factor, value) in enumerate(burnout.items(), 1):
                expanded = maximum != minimum and round(value, 2) == maximum
                with st.expander(f"{number}) {BURNOUT_NAMES[factor]} · {value:.2f}점", expanded=expanded):
                    for item_index, line in enumerate(burnout_detail_lines(factor, value)):
                        web_numbered_detail(item_index, line)
    result_heading("연구 근거")
    with st.expander("감·수·성 인권감수성 모델 근거자료"):
        for index, (label, citation, url, role) in enumerate(MODEL_REFERENCES):
            if index:
                st.divider()
            st.markdown(f"**[{label}]({url})** — 이성덕({citation})")
            st.caption(role)
    with st.expander("직무소진 결과의 연구 근거"):
        for index, (label, citation, url, role) in enumerate(BURNOUT_REFERENCES):
            if index:
                st.divider()
            st.markdown(f"**[{label}]({url})**")
            st.caption(citation)
            st.write(role)

    st.download_button(
        "통합 PDF 내려받기", data=make_result_pdf(scores, st.session_state.get("personal_action_plan", ""), burnout, selected),
        file_name="나의_감수성_직무소진_자기점검.pdf", mime="application/pdf",
        use_container_width=True,
    )

    st.markdown(
        '<div class="rights-footer">© 2026 이성덕. All rights reserved.<br>'
        '감·수·성 로고 상표출원(심사 중)</div>',
        unsafe_allow_html=True,
    )