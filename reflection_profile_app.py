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
from reportlab.platypus import PageBreak, Image as RLImage, Paragraph, SimpleDocTemplate


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
        if number in {7, 8, 9, 15, 16, 17, 24, 25}:
            grouped[factor].append(answers[number])
    return {factor: round(float(np.mean(values)), 2) for factor, values in grouped.items()}


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
    "탈진": "회복시간과 휴식 여건을 살펴보세요.",
    "심적거리": "업무 부담을 살피고 동료와 상의할 수 있는 부분을 찾아보세요.",
    "인지적 조절 손상": "집중이 흐려지는 상황을 찾고 확인표나 업무 재확인을 활용해 보세요.",
    "정서적 조절 손상": "감정 변화의 신호를 알아차리고 잠시 멈추거나 도움을 요청해 보세요.",
}
SCENE_PROMPT = "최근 수용자에게 대응했던 근무 장면 하나를 떠올려 보세요."
SCENE_QUESTIONS = {
    "감 · 알아차림": "그때 나와 상대에게 어떤 감정이나 도움이 필요한 신호가 있었나요?",
    "수 · 판단": "내 조치는 왜 필요했고, 어떤 절차나 권리를 덜 제한하는 방법을 고려했나요?",
    "성 · 성찰과 조정": "내 피로, 선입견, 동료 분위기는 대응에 어떤 영향을 주었고, 다음에는 무엇을 조정할까요?",
}
RECOVERY_QUESTION = "최근 근무에서 회복이나 지원이 가장 필요했던 순간은 언제였나요?"
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
BURNOUT_NOTE = "각 영역은 1~5점의 문항평균입니다. 값이 높을수록 해당 경험을 더 자주 보고한 것으로 해석합니다."
REFERENCE_NOTE = "공기업 사무직 345명의 선행연구 결과입니다. 평균 ± 1표준편차는 해당 표본의 점수 분포를 설명하는 참고값입니다. 해당 평균은 공기업 사무직 표본이 보고한 경험 빈도의 평균입니다. 직무와 응답 여건의 차이를 고려해 참고용으로 읽어 주세요. 교정공무원 규준이나 정상·위험 판정 기준으로 사용하지 않습니다."


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


def burnout_comparison(factor, score):
    mean, sd = BAT_REFERENCE[factor]
    difference = round(score - mean, 2)
    relation = "같습니다" if difference == 0 else (
        f"{abs(difference):.2f}점 높습니다" if difference > 0 else f"{abs(difference):.2f}점 낮습니다"
    )
    return (
        f"나의 평균 {score:.2f}점은 선행연구 평균 {mean:.2f}점과 비교해 {relation}. "
        f"해당 표본의 평균 ± 1표준편차 구간은 {mean-sd:.2f}~{mean+sd:.2f}점입니다."
    )


def make_result_pdf(scores, action_plan, burnout, selected=None):
    selected = selected or {}
    from xml.sax.saxutils import escape
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFError

    buffer = io.BytesIO()
    font = "HYSMyeongJo-Medium"
    pdfmetrics.registerFont(UnicodeCIDFont(font))
    if KOREAN_FONT_PATH:
        try:
            pdfmetrics.registerFont(TTFont("KoreanFont", KOREAN_FONT_PATH))
            font = "KoreanFont"
        except (TTFError, OSError, ValueError):
            pass

    styles = getSampleStyleSheet()
    body = ParagraphStyle("ResultBody", parent=styles["BodyText"], fontName=font,
                          fontSize=10, leading=16, wordWrap="CJK", spaceAfter=5)
    heading = ParagraphStyle("ResultHeading", parent=body, fontSize=13,
                             leading=19, spaceBefore=9, textColor=HexColor("#164b79"))
    title = ParagraphStyle("ResultTitle", parent=heading, fontSize=18, leading=25)
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm,
                            topMargin=17*mm, bottomMargin=17*mm)
    def draw_background(canvas, page):
        width, height = A4
        canvas.saveState()
        canvas.setFillColor(HexColor("#f7fcff"))
        canvas.rect(0, 0, width, height, fill=1, stroke=0)
        canvas.setFillColor(HexColor("#dff1fb"))
        ridge = canvas.beginPath()
        ridge.moveTo(0, 0)
        ridge.curveTo(40*mm, 20*mm, 65*mm, 9*mm, 100*mm, 16*mm)
        ridge.curveTo(140*mm, 25*mm, 175*mm, 8*mm, width, 19*mm)
        ridge.lineTo(width, 0)
        ridge.close()
        canvas.drawPath(ridge, fill=1, stroke=0)
        canvas.setFillColor(HexColor("#164b79"))
        canvas.setFont(font, 8)
        canvas.drawString(18*mm, 8*mm, "감·수·성 자기성찰 참고자료")
        canvas.drawRightString(width - 18*mm, 8*mm, str(page.page))
        canvas.restoreState()

    score_line = "  ·  ".join(f"{factor} {score:.2f}" for factor, score in scores.items())
    story = [
        Paragraph("나의 감·수·성 인권감수성과 직무소진", title),
        Paragraph("감·수·성 인권감수성 모델을 활용한 자기성찰 참고자료", body),
        Paragraph("감·수·성 인권감수성 결과", heading),
        Paragraph(score_line, body),
        Paragraph(PROFILE_NOTE, body),
        RLImage(radar_png(scores), width=45*mm, height=45*mm, kind="proportional"),
        Paragraph("내 점수는 무엇을 보여주나요?", heading),
        *(Paragraph(line, body) for line in response_summary(scores)),
        Paragraph("직무소진 결과", heading),
    ]
    if LOGO_PATH.is_file():
        story.insert(0, RLImage(str(LOGO_PATH), width=13*mm, height=13*mm, kind="proportional"))
    if burnout is None:
        story.append(Paragraph("직무소진 결과를 산출할 수 없습니다.", body))
    else:
        story.append(Paragraph(BURNOUT_NOTE, body))
        for factor, value in burnout.items():
            story.append(Paragraph(f"{BURNOUT_NAMES[factor]} {value:.2f}", body))
            chart_width = doc.width - 12
            chart = Drawing(chart_width, 9)
            chart.add(Rect(0, 2, chart_width, 6, fillColor=HexColor("#e3f0e8"), strokeColor=None))
            chart.add(Rect(0, 2, chart_width * value / 5, 6,
                           fillColor=HexColor("#409773"), strokeColor=None))
            story.extend([chart, Paragraph(BAT_PLAIN_MEANINGS[factor], body),
                          Paragraph(BAT_PRACTICE[factor], body)])

    story += [PageBreak(), Paragraph("한 장면을 감·수·성으로 다시 보기", title),
              Paragraph(SCENE_PROMPT, body)]
    for label, question in SCENE_QUESTIONS.items():
        factor = label[0]
        story.append(Paragraph(f"{label} — {question}", heading))
        story.append(Paragraph(FACTOR_META[factor]["meaning"], body))
        story.append(Paragraph(PRACTICE_GUIDES[factor]["steps"], body))
    story.append(Paragraph("내 응답에서 돌아볼 여섯 가지", heading))
    for factor, (note, rows) in selected.items():
        story.extend([Paragraph(factor, heading), Paragraph(note, body)])
        for score, number, item in rows:
            story.append(Paragraph(f"{number}번 · {score}점 ({SCALE_LABELS[score]}) · {escape(item)}", body))
            story.append(Paragraph(f"돌아볼 질문 · {REFLECTION_QUESTIONS[number]}", body))
    story += [
        Paragraph("회복과 지원 돌아보기", heading),
        Paragraph(RECOVERY_QUESTION, body),
        Paragraph("참고자료", heading),
        Paragraph(f'<link href="{SCALE_PAPER_URL}">감·수·성 예비척도 개발 논문</link>', body),
    ]
    if burnout is not None:
        story.append(Paragraph(REFERENCE_NOTE, body))
        for factor in burnout:
            story.append(Paragraph(f"{BURNOUT_NAMES[factor]} · {burnout_comparison(factor, burnout[factor])}", body))
        story.append(Paragraph('<link href="https://doi.org/10.24230/kjiop.v33i4.461-499">한국판 K-BAT 타당화 예비연구</link>', body))
    story.extend([Paragraph("다음 근무에서 해볼 한 가지", heading),
                  Paragraph(escape(action_plan.strip()).replace("\n", "<br/>") or "작성한 내용이 없습니다.", body)])
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
    st.markdown('<div class="brand-bar"><b>감·수·성 인권감수성</b> · 자기성찰과 직무소진 자기점검</div>', unsafe_allow_html=True)


init_state()

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
- 응답은 연구 목적과 인권교육 개선을 위해서만 사용합니다.

### 예상되는 불편과 이익

일부 문항에서 자신의 편견·감정·조직관행을 돌아보며 일시적인 불편을 느낄 수 있습니다. 직접적인 보상은 없지만 자신의 판단 경향과 근무 경험을 돌아볼 참고자료를 즉시 확인하고 PDF로 저장할 수 있습니다.
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
    selected = reflection_items(answers)
    burnout = bat_scores(st.session_state.get("burnout_answers", {}))

    st.title("나의 자기점검 결과")
    if st.session_state.research_saved:
        st.success("익명 연구자료가 제출되었습니다.")
    st.caption("두 결과는 자기성찰을 위한 참고자료입니다. 인사평가나 진단에 사용하지 않습니다.")
    gam_tab, burnout_tab = st.tabs(["감·수·성 인권감수성 결과", "직무소진 결과"])

    with gam_tab:
        st.subheader("감·수·성 인권감수성 결과")
        st.write(" · ".join(f"**{factor} {value:.2f}**" for factor, value in scores.items()))
        st.image(radar_png(scores), width=290)
        st.subheader("내 점수는 무엇을 보여주나요?")
        st.write(PROFILE_NOTE)
        for line in response_summary(scores):
            st.write(line)

        st.subheader("한 장면을 감·수·성으로 다시 보기")
        st.write(SCENE_PROMPT)
        for label, question in SCENE_QUESTIONS.items():
            st.markdown(f"**{label}**  \n{question}")
        for factor, meta in FACTOR_META.items():
            with st.expander(f"{meta['title']} · 돌아볼 문항과 실천"):
                st.write(meta["meaning"])
                st.write(f"**실천 제안** · {PRACTICE_GUIDES[factor]['steps']}")
        st.subheader("내 응답에서 돌아볼 여섯 가지")
        st.write("각 영역에서 낮은 응답 순으로 두 문항씩 골랐습니다. 경험과 가까운 문항 하나부터 살펴보세요.")
        for factor, (note, rows) in selected.items():
            with st.expander(f"{FACTOR_META[factor]['title']} · 돌아볼 두 문항", expanded=True):
                st.caption(note)
                for score, number, item in rows:
                    st.markdown(f"**{number}번 · {score}점 ({SCALE_LABELS[score]})**")
                    st.write(item)
                    st.write(f"**돌아볼 질문** · {REFLECTION_QUESTIONS[number]}")
        with st.expander("상세 결과와 근거자료"):
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
            st.markdown("**선행연구 평균과 나의 응답 비교**")
            st.write(REFERENCE_NOTE)
            for factor, value in burnout.items():
                st.write(f"**{BURNOUT_NAMES[factor]}** · {burnout_comparison(factor, value)}")
            st.write(f"**{RECOVERY_QUESTION}**")
            for factor, value in burnout.items():
                with st.expander(f"{BURNOUT_NAMES[factor]} · {value:.2f}점"):
                    st.write(BAT_PLAIN_MEANINGS[factor])
                    st.write(f"**회복과 지원을 위한 제안** · {BAT_PRACTICE[factor]}")
            st.markdown("[비교 수치의 근거 · 한국판 직무소진평가척도 예비연구](https://doi.org/10.24230/kjiop.v33i4.461-499)")

    st.subheader("다음 근무에서 해볼 한 가지")
    action_plan = st.text_area(
        "오늘 돌아본 내용에서 하나를 골라, 다음 근무의 어떤 상황에서 무엇을 해볼지 적어보세요. (선택)",
        placeholder="예: 안전을 확보한 뒤 무엇이 가장 불편한지 짧게 확인하겠습니다.",
        max_chars=300,
    )
    st.download_button(
        "통합 PDF 내려받기", data=make_result_pdf(scores, action_plan, burnout, selected),
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

