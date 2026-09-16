"""감·수·성 교육필요 분석 대시보드

기존 reflection_profile_app.py가 저장한 responses 시트를 읽기 전용으로 분석한다.
개별 응답자 평가가 아니라, 강의 집단의 교육 우선순위와 교육안을 제시하기 위한 파일이다.
"""

import io
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import gspread
import plotly.graph_objects as go
import streamlit as st
from google.oauth2.service_account import Credentials
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


st.set_page_config(page_title="감·수·성 교육필요 대시보드", page_icon="📘", layout="wide")

WORKSHEET_NAME = "responses"
PRIORITY_COUNT = 3
FONT_PATH = Path(__file__).parent / "fonts" / "NanumGothicCoding.ttf"

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

DEMOGRAPHICS = {
    "성별": "성별", "연령대": "연령대", "직급": "직급", "근무기관유형": "근무기관 유형",
    "교정경력": "교정 경력", "인권교육경험": "최근 3년간 인권교육 경험", "정신건강교육경험": "정신건강 관련 교육 경험",
}

DEMOGRAPHIC_CATEGORY_ORDER = {
    "성별": ["남성", "여성", "응답하지 않음"],
    "연령대": ["20대", "30대", "40대", "50대 이상", "응답하지 않음"],
    "직급": ["9급", "8급", "7급", "6급", "5급 이상", "응답하지 않음"],
    "근무기관유형": ["교도소", "구치소", "소년교도소·소년시설", "기타 교정기관", "응답하지 않음"],
    "교정경력": ["5년 미만", "5~10년 미만", "10~20년 미만", "20년 이상", "응답하지 않음"],
    "인권교육경험": ["없음", "1회", "2~3회", "4회 이상", "응답하지 않음"],
    "정신건강교육경험": ["없음", "1회", "2회 이상", "응답하지 않음"],
}

# 두 논문에서 제안한 감정 인식-헌법적 기준 적용-성찰의 훈련 구조를 교육안으로 구체화한다.
GUIDES = {
    "감": {
        "title": "감(感): 정서적·상황적 인식 훈련",
        "goal": "상대방과 자신의 불안·고통·수치·분노 등 정서 신호를 단정하지 않고 알아차리며, 취약성과 권리침해 가능성을 탐지한다.",
        "activity": "사례의 말투·표정·행동을 관찰 사실로 먼저 적고, 가능한 정서와 욕구를 구분한다. 이어 ‘내가 느낀 감정’을 감정 명명 카드 또는 짧은 감정일지로 표현한다.",
        "discussion": "이 상황에서 확인할 수 있는 사실은 무엇이고, 내가 추정한 감정은 무엇인가? 상대방의 행동을 불응으로 단정하기 전에 어떤 불안·취약성의 가능성을 살펴볼 수 있는가?",
        "practice": "다음 근무에서 긴장된 대응 상황 한 건을 골라 ‘관찰 사실-상대의 가능한 정서-나의 감정-확인한 질문’을 4줄로 기록한다.",
        "case": "수용자가 큰 소리로 항의하고 지시를 반복해 묻는다. 담당자는 무시당했다는 느낌과 긴장을 경험한다. 수용자는 최근 수면장애와 불안을 호소한 바 있다.",
    },
    "수": {
        "title": "수(受): 비례성·절차·협력에 따른 판단 훈련",
        "goal": "즉각적 감정 반응을 목적, 필요성, 최소침해성, 절차적 정당성 및 전문적 협력의 기준으로 재검토해 정당화 가능한 대응을 선택한다.",
        "activity": "동일 사례에 대해 가능한 대응 세 가지를 만들고, ‘목적-필요성-덜 제한적인 대안-절차·협력 필요성’ 체크리스트로 비교한다. 조별로 가장 적절한 대안을 선택하고 근거를 설명한다.",
        "discussion": "이 조치의 직무상 목적은 무엇인가? 더 적게 제한하는 대안은 없는가? 지금 확인해야 할 절차와 보고·의료·심리 협력은 무엇인가?",
        "practice": "다음 조치 전 30초 동안 ‘목적은 무엇인가-꼭 필요한가-대안은 없는가-누구와 협력할 것인가’를 메모하거나 구두로 점검한다.",
        "case": "흥분한 수용자가 자해를 암시하며 면담실 문을 두드린다. 담당자는 질서유지를 위해 즉시 강한 통제를 고려하지만, 과거 정신건강 치료 및 자해 위험 기록이 있다.",
    },
    "성": {
        "title": "성(性): 편견·권위·관행의 성찰과 조정",
        "goal": "피로, 선입견, 동료 분위기, 권위와 관행이 판단에 미치는 영향을 점검하고, 권한 행사의 위험을 줄이는 대안을 선택한다.",
        "activity": "사례 직후 자신의 판단을 ‘사실-감정-자동 생각-동료·관행의 영향-다음 대안’으로 나누어 성찰 저널에 쓴다. 이어 동료 피드백으로 대안 행동을 한 가지 고른다.",
        "discussion": "내가 강하게 반응하려는 동기는 안전을 위한 것인가, 피로·억울함·권위감의 영향도 있는가? 동료 분위기나 관행이 나의 판단을 대신하지 않았는가? 설명해야 할 대상과 내용은 무엇인가?",
        "practice": "다음 주 한 번, 강한 감정이 든 업무 상황에서 ‘사실과 해석을 분리했는가, 설명할 수 있는 근거가 있는가’를 확인하고 대안 한 가지를 기록한다.",
        "case": "동료들이 특정 수용자를 ‘늘 문제를 일으키는 사람’이라고 부르며 강한 말투로 지시한다. 담당자도 피로가 누적된 상태에서 같은 방식으로 대응하려 한다.",
    },
}

THEORY_AND_METHOD = {
    "감": "경험학습 관점: 구체적 사건에서 관찰한 정서 신호를 감정 명명과 확인 질문으로 전환한다.",
    "수": "사례·문제기반 학습 관점: 헌법 제10조의 인간 존엄과 제37조 제2항의 비례성 원리를 직무 대안 비교에 적용한다.",
    "성": "성찰학습 관점: Schön의 행동 중·행동 후 성찰과 비판적 성찰을 활용해 편견·권위·관행의 영향을 점검한다.",
}

EDUCATION_VARIANTS = {
    "감": [
        ("정서 신호 탐지 실습", "사례 문장에서 관찰 사실과 정서 단어를 분리한 뒤, 불안·수치·고통·분노가 권리침해의 신호가 될 수 있는 맥락을 토의한다."),
        ("감정 명명-욕구 연결", "강한 반응이 있었던 직무 상황을 ‘감정-욕구-확인 질문’으로 재서술하고, 비난 언어를 공감적 언어로 바꾼다."),
        ("취약성 대응 역할연습", "정신건강·자극 과부하·불안 가능성이 있는 상황에서 짧고 명료한 지시, 자극 조절, 확인 질문을 역할연습한다."),
    ],
    "수": [
        ("비례성 4단계 판정", "하나의 통제 상황에 대해 목적의 정당성, 수단의 적합성, 침해 최소성, 법익 균형을 적용하여 세 가지 대응안을 비교한다."),
        ("절차·설명·기록 점검", "조치 전·중·후에 필요한 고지, 보고, 기록, 검토를 배열하고 ‘설명 가능한 대응’인지 점검한다."),
        ("전문가 협력 시뮬레이션", "자해·환청·급성 불안 사례에서 교정직원, 의료·심리 전문가, 관리자 사이의 정보공유와 역할 분담을 설계한다."),
    ],
    "성": [
        ("권한 행사 성찰 저널", "사실-감정-자동 생각-권위·관행의 영향-대안 행동의 다섯 칸으로 사건을 되짚는다."),
        ("동료 압력 대안 토의", "‘원래 이렇게 한다’는 관행이 등장하는 사례에서 동료와 관계를 해치지 않으면서 다른 판단을 제안하는 문장을 연습한다."),
        ("피로와 판단 조정", "피로·스트레스가 과잉반응에 미칠 수 있는 지점을 확인하고, 도움 요청·교대·재확인 같은 현실적 조정 행동을 정한다."),
    ],
}

SUBDOMAIN_GUIDES = {
    "정서 인식": "감정 명명과 욕구 연결", "공감적 이해": "확인 질문을 통한 공감적 이해", "취약성 이해": "정신건강·환경 자극의 취약성 이해",
    "비례성 판단": "목적·필요성·최소침해성 판단", "절차적 정당성 판단": "절차·보고·설명의 정당성", "전문적 통합판단·협력": "전문가 협력과 대응 조정",
    "편견 성찰": "낙인·고정관념 점검", "권위·관행 성찰": "동료 압력·권위 의존 점검", "자기점검·조정": "피로·스트레스와 판단 조정",
}


def apply_style():
    st.markdown("""<style>
    .stApp{background:linear-gradient(145deg,#f8fcff,#e9f6ff);color:#173f66}
    .block-container{max-width:1280px;padding-top:1.7rem;padding-bottom:3rem}
    h1,h2,h3{color:#163f67;word-break:keep-all}.stMarkdown p,.stMarkdown li{word-break:keep-all;line-height:1.7}
    .notice{padding:1rem 1.15rem;background:#fff;border-left:5px solid #4aa9df;border-radius:12px;color:#315b7c}
    .guide{padding:1rem 1.1rem;border:1px solid #d1eafa;border-radius:15px;background:rgba(255,255,255,.86);margin:.6rem 0}
    .guide h4{color:#217fb7;margin:.1rem 0 .55rem}.tag{color:#4a789a;font-size:.88rem;font-weight:700}
    @media(max-width:520px){.block-container{padding:.9rem .7rem 2.5rem}.guide{padding:.85rem}.stMarkdown p,.stMarkdown li{font-size:.95rem}}
    </style>""", unsafe_allow_html=True)


def google_sheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    credentials = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scope)
    client = gspread.authorize(credentials)
    spreadsheet_key = st.secrets["google_sheets"]["spreadsheet_key"]
    return client.open_by_key(spreadsheet_key).worksheet(WORKSHEET_NAME)


def require_dashboard_login():
    """응답 원자료가 보이는 화면이므로 교육자 전용 비밀번호를 필수로 둔다."""
    configured_password = st.secrets.get("dashboard", {}).get("password")
    if not configured_password:
        st.error("대시보드 비밀번호가 설정되지 않았습니다.")
        st.info("Streamlit Secrets에 [dashboard] 아래 password 값을 추가한 뒤 다시 실행하십시오.")
        st.stop()
    if st.session_state.get("dashboard_authenticated"):
        return
    st.subheader("교육자 전용 분석 화면")
    entered = st.text_input("관리자 비밀번호", type="password")
    if st.button("대시보드 열기", type="primary"):
        if entered == configured_password:
            st.session_state.dashboard_authenticated = True
            st.rerun()
        st.error("비밀번호가 일치하지 않습니다.")
    st.stop()


@st.cache_data(ttl=300, show_spinner=False)
def load_records():
    rows = google_sheet().get_all_records()
    required = {"응답시각"} | {f"Q{number}" for number, _, _, _ in ITEMS}
    if not rows:
        return [], "응답 자료가 아직 없습니다."
    missing = required - set(rows[0])
    if missing:
        return [], f"응답 시트에 필요한 열이 없습니다: {', '.join(sorted(missing))}"
    cleaned = []
    for row in rows:
        try:
            parsed = dict(row)
            # 설문 앱이 저장하는 형식: 2026-09-16 13:45:00 (한국 표준시)
            parsed["_submitted_at"] = datetime.strptime(str(row["응답시각"]), "%Y-%m-%d %H:%M:%S")
            for number, _, _, _ in ITEMS:
                value = float(row[f"Q{number}"])
                if value not in (1, 2, 3, 4):
                    raise ValueError
                parsed[f"Q{number}"] = value
            cleaned.append(parsed)
        except (KeyError, TypeError, ValueError):
            continue
    return cleaned, ""


def mean(values):
    return round(sum(values) / len(values), 2) if values else None


def filtered_records(records, filters, start_date, end_date):
    selected = []
    for row in records:
        submitted_date = row["_submitted_at"].date()
        in_date_range = start_date <= submitted_date <= end_date
        matches_demographics = all(choice == "전체" or row.get(column, "") == choice for column, choice in filters.items())
        if in_date_range and matches_demographics:
            selected.append(row)
    return selected


def item_stats(records):
    result = []
    for number, factor, subdomain, text in ITEMS:
        values = [row[f"Q{number}"] for row in records]
        result.append({"번호": number, "영역": factor, "하위영역": subdomain, "문항": text, "평균": mean(values), "낮은 응답(1~2) 비율": round(sum(v <= 2 for v in values) / len(values) * 100, 1)})
    return result


def factor_stats(records):
    result = []
    for factor in ("감", "수", "성"):
        numbers = [number for number, item_factor, _, _ in ITEMS if item_factor == factor]
        values = [row[f"Q{number}"] for row in records for number in numbers]
        result.append({"영역": factor, "평균": mean(values), "낮은 응답(1~2) 비율": round(sum(v <= 2 for v in values) / len(values) * 100, 1)})
    return result


def factor_score_map(records):
    return {row["영역"]: row["평균"] for row in factor_stats(records)}


def demographic_distribution(records):
    """현재 선택 집단의 기본정보 분포를 표와 막대그래프에 쓸 형태로 만든다."""
    rows = []
    for group_index, (column, label) in enumerate(DEMOGRAPHICS.items()):
        counts = Counter(str(row.get(column, "미응답")) or "미응답" for row in records)
        configured = DEMOGRAPHIC_CATEGORY_ORDER[column]
        categories = [category for category in configured if category in counts]
        categories += sorted(category for category in counts if category not in configured)
        for category in categories:
            count = counts[category]
            rows.append({"항목": label, "범주": category, "인원": count, "비율": round(count / len(records) * 100, 1), "묶음순서": group_index})
    return rows


def factor_by_demographic(records, column):
    groups = defaultdict(list)
    for row in records:
        groups[str(row.get(column, "미응답")) or "미응답"].append(row)
    rows = []
    for category, group in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
        scores = factor_score_map(group)
        rows.append({"범주": category, "인원": len(group), "감": scores["감"], "수": scores["수"], "성": scores["성"]})
    return rows


def priority_topics(records):
    stats = item_stats(records)
    # 감·수·성 세 영역에서 각각 하나씩 선택한다. 같은 영역의 낮은 문항이 여러 개여도
    # 다른 영역의 다음 낮은 문항을 우선하여 교육계획이 세 판단영역을 함께 다루게 한다.
    ordered = sorted(stats, key=lambda x: (x["평균"], -x["낮은 응답(1~2) 비율"], x["번호"]))
    selected, used_factors = [], set()
    for row in ordered:
        if row["영역"] not in used_factors:
            selected.append(row)
            used_factors.add(row["영역"])
        if len(selected) == PRIORITY_COUNT:
            break
    return selected


def render_learning_plan(priority):
    factor = priority["영역"]
    guide = GUIDES[factor]
    variants = "<br>".join(f"- <b>{name}</b>: {method}" for name, method in EDUCATION_VARIANTS[factor])
    st.markdown(f"<div class='guide'><h4>{guide['title']}</h4><p><span class='tag'>선정 근거</span><br>Q{priority['번호']} · {priority['하위영역']} · 평균 {priority['평균']:.2f} / 4점, 낮은 응답(1~2점) {priority['낮은 응답(1~2) 비율']:.1f}%</p><p><span class='tag'>교육목표</span><br>{guide['goal']}</p><p><span class='tag'>교육 이론·판단 틀</span><br>{THEORY_AND_METHOD[factor]}</p><p><span class='tag'>핵심 사례활동</span><br><b>사례:</b> {guide['case']}<br>{guide['activity']}</p><p><span class='tag'>선택 가능한 확장 활동</span><br>{variants}</p><p><span class='tag'>토의질문</span><br>{guide['discussion']}</p><p><span class='tag'>실천과제</span><br>{guide['practice']}</p><p><span class='tag'>세부 주제</span><br>{SUBDOMAIN_GUIDES[priority['하위영역']]}</p></div>", unsafe_allow_html=True)


def render_chart(stats):
    fig = go.Figure(go.Bar(x=[row["영역"] for row in stats], y=[row["평균"] for row in stats], marker_color=["#58afe0", "#2c83bd", "#175b91"], text=[f"{row['평균']:.2f}" for row in stats], textposition="outside"))
    fig.update_layout(yaxis=dict(range=[1, 4.25], title="문항 평균(1~4점)"), xaxis_title="", height=360, margin=dict(l=20, r=20, t=30, b=20), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,.58)")
    return fig


def render_demographic_chart(rows):
    group_colors = ["#1976AD", "#75C4E9"]
    colors_by_bar = [group_colors[row["묶음순서"] % 2] for row in rows]
    fig = go.Figure(go.Bar(
        x=[[row["항목"] for row in rows], [row["범주"] for row in rows]], y=[row["인원"] for row in rows],
        marker_color=colors_by_bar, text=[f"{row['인원']}명<br>{row['비율']:.1f}%" for row in rows], textposition="outside",
        hovertemplate="%{x[0]} · %{x[1]}<br>%{y}명<extra></extra>",
    ))
    fig.update_layout(height=430, showlegend=False, yaxis_title="인원", margin=dict(l=20, r=20, t=25, b=78), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,.58)")
    fig.update_xaxes(tickfont=dict(size=10), showgrid=False)
    return fig


def render_group_comparison(rows, label):
    fig = go.Figure()
    colors = {"감": "#58afe0", "수": "#2c83bd", "성": "#175b91"}
    for factor in ("감", "수", "성"):
        fig.add_trace(go.Bar(name=factor, x=[f"{row['범주']}\n(n={row['인원']})" for row in rows], y=[row[factor] for row in rows], marker_color=colors[factor], text=[f"{row[factor]:.2f}" for row in rows], textposition="outside"))
    fig.update_layout(barmode="group", height=410, yaxis=dict(range=[1, 4.25], title="문항 평균(1~4점)"), xaxis_title=label, margin=dict(l=20, r=20, t=25, b=85), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(255,255,255,.58)")
    return fig


def render_profile_summary(records):
    stats = item_stats(records)
    high = sorted(stats, key=lambda row: (-row["평균"], row["낮은 응답(1~2) 비율"], row["번호"]))[:3]
    low = sorted(stats, key=lambda row: (row["평균"], -row["낮은 응답(1~2) 비율"], row["번호"]))[:3]
    left, right = st.columns(2)
    with left:
        st.success("### 상대적으로 높은 응답 경향")
        st.caption("이 집단이 비교적 익숙하게 보고한 판단·성찰 지점입니다. 우열이나 성취 판정이 아닙니다.")
        for row in high:
            st.markdown(f"**Q{row['번호']} · {row['영역']} / {row['하위영역']} - {row['평균']:.2f}점**  \n{row['문항']}")
    with right:
        st.info("### 더 우선적으로 다뤄 볼 응답 경향")
        st.caption("이 집단의 다음 교육에서 사례와 실습을 연결해 볼 지점입니다. 개인이나 집단의 결함을 뜻하지 않습니다.")
        for row in low:
            st.markdown(f"**Q{row['번호']} · {row['영역']} / {row['하위영역']} - {row['평균']:.2f}점**  \n{row['문항']}")


def course_blocks(priorities, option):
    factor_sequence = []
    for item in priorities:
        if item["영역"] not in factor_sequence:
            factor_sequence.append(item["영역"])
    if option == "2시간 핵심 과정":
        blocks = [("15분", "집단 응답 경향 읽기", "세 판단영역은 개인 평가가 아니라 직무 판단의 성찰 지점임을 확인"), ("60분", "우선 주제 사례 실습", "선정된 세 주제의 관찰-판단-성찰 미니 실습"), ("30분", "통합 직무사례 토의", "감정 신호, 비례·절차, 권한 성찰을 한 사례에 연결"), ("15분", "행동계획", "다음 근무에서 실천할 한 가지와 동료 피드백 약속")]
    else:
        blocks = [("25분", "집단 응답 경향과 인권적 직무판단", "교육의 목적·한계·성찰 원칙을 공유"), ("135분", "영역별 심화 모듈", "감-수-성 우선 주제를 각각 사례, 역할연습, 토의로 운영"), ("55분", "통합 시뮬레이션", "교정 현장 상황에서 감정 인식-비례성·절차-성찰을 연결해 대응안 비교"), ("25분", "성찰 저널과 사후 실천", "사실·감정·판단 근거·동료·관행·대안을 기록하고 실행계획 작성")]
    return factor_sequence, blocks


def render_course_plan(priorities):
    option = st.radio("강의 시간", ["2시간 핵심 과정", "4시간 심화 과정"], horizontal=True)
    factor_sequence, blocks = course_blocks(priorities, option)
    st.markdown(f"**이번 분석에서 반영할 중심 영역:** {' · '.join(factor_sequence)}")
    for duration, title, content in blocks:
        st.markdown(f"<div class='guide'><h4>{duration} | {title}</h4><p>{content}</p></div>", unsafe_allow_html=True)
    return option


def pdf_font_name():
    """저장소의 한글 폰트를 우선 사용해 PDF에서 한글이 깨지지 않게 한다."""
    if "NanumGothic" in pdfmetrics.getRegisteredFontNames():
        return "NanumGothic"
    candidates = [FONT_PATH, Path("fonts/NanumGothicCoding.ttf"), Path("/usr/share/fonts/truetype/nanum/NanumGothic.ttf")]
    for path in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont("NanumGothic", str(path)))
            return "NanumGothic"
    raise RuntimeError("한글 PDF 폰트를 찾지 못했습니다. fonts/NanumGothicCoding.ttf 파일을 저장소에 유지해 주세요.")


def pdf_paragraph(text, style):
    return Paragraph(str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"), style)


def build_pdf_report(records, filters, start_date, end_date, course_option):
    """현재 선택 조건의 집단 결과만 담은 교육계획 PDF 바이트를 만든다."""
    font = pdf_font_name()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=16 * mm, leftMargin=16 * mm, topMargin=15 * mm, bottomMargin=15 * mm)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title_ko", parent=styles["Title"], fontName=font, fontSize=18, leading=25, textColor=colors.HexColor("#163F67"), spaceAfter=8)
    h1 = ParagraphStyle("h1_ko", parent=styles["Heading1"], fontName=font, fontSize=13, leading=19, textColor=colors.HexColor("#1B6FAD"), spaceBefore=12, spaceAfter=7)
    h2 = ParagraphStyle("h2_ko", parent=styles["Heading2"], fontName=font, fontSize=11, leading=16, textColor=colors.HexColor("#163F67"), spaceBefore=8, spaceAfter=4)
    body = ParagraphStyle("body_ko", parent=styles["BodyText"], fontName=font, fontSize=8.7, leading=14, textColor=colors.HexColor("#263E53"))
    small = ParagraphStyle("small_ko", parent=body, fontSize=7.6, leading=11, textColor=colors.HexColor("#587187"))
    story = [Paragraph("감·수·성 교육필요 분석 및 교육계획", title)]
    story += [Paragraph("교정공무원 인권적 직무판단 자기성찰 설문 - 교육자용 집단 분석", body), Spacer(1, 4 * mm)]
    filter_text = " · ".join(f"{DEMOGRAPHICS[key]}: {value}" for key, value in filters.items() if value != "전체") or "인구학적 필터 없음"
    story += [pdf_paragraph(f"분석 기간: {start_date:%Y-%m-%d} ~ {end_date:%Y-%m-%d} | 분석 인원: {len(records)}명", body), pdf_paragraph(f"적용 조건: {filter_text}", small)]
    story += [pdf_paragraph("본 결과는 집단의 응답 경향을 교육 설계에 연결하기 위한 자료입니다. 개인의 능력·도덕성·직무수행을 평가하거나 인사자료로 활용하지 않습니다.", small), Spacer(1, 3 * mm)]

    story.append(Paragraph("1. 감·수·성 영역별 응답 경향", h1))
    factors = factor_stats(records)
    factor_data = [[pdf_paragraph("영역", body), pdf_paragraph("문항 평균(4점)", body), pdf_paragraph("낮은 응답(1~2점)", body)]]
    for row in factors:
        factor_data.append([pdf_paragraph(row["영역"], body), pdf_paragraph(f"{row['평균']:.2f}", body), pdf_paragraph(f"{row['낮은 응답(1~2) 비율']:.1f}%", body)])
    factor_table = Table(factor_data, colWidths=[35 * mm, 55 * mm, 65 * mm])
    factor_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDF1FC")), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#B9DDEF")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [factor_table, Spacer(1, 3 * mm)]

    stats = item_stats(records)
    high = sorted(stats, key=lambda row: (-row["평균"], row["낮은 응답(1~2) 비율"], row["번호"]))[:3]
    low = sorted(stats, key=lambda row: (row["평균"], -row["낮은 응답(1~2) 비율"], row["번호"]))[:3]
    story.append(Paragraph("2. 상대적으로 높은 응답과 우선 성찰 지점", h1))
    for heading, rows, lead in [("상대적으로 높은 응답 경향", high, "이 집단이 비교적 익숙하게 보고한 교육 자원"), ("더 우선적으로 다뤄 볼 응답 경향", low, "다음 교육에서 사례·실습과 연결할 우선 성찰 지점")]:
        story.append(pdf_paragraph(f"{heading} - {lead}", h2))
        for row in rows:
            story.append(pdf_paragraph(f"Q{row['번호']} | {row['영역']}·{row['하위영역']} | 평균 {row['평균']:.2f}: {row['문항']}", body))

    story.append(Paragraph("3. 인구학적 구성", h1))
    demo_data = [[pdf_paragraph("항목", body), pdf_paragraph("범주", body), pdf_paragraph("인원", body), pdf_paragraph("비율", body)]]
    for row in demographic_distribution(records):
        demo_data.append([pdf_paragraph(row["항목"], small), pdf_paragraph(row["범주"], small), pdf_paragraph(f"{row['인원']}명", small), pdf_paragraph(f"{row['비율']:.1f}%", small)])
    demo_table = Table(demo_data, colWidths=[45 * mm, 65 * mm, 22 * mm, 23 * mm], repeatRows=1)
    demo_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDF1FC")), ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#C8E4F3")), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story += [demo_table, PageBreak()]

    priorities = priority_topics(records)
    story.append(Paragraph("4. 분석 결과에 따른 우선 교육 주제", h1))
    for index, priority in enumerate(priorities, 1):
        guide = GUIDES[priority["영역"]]
        story.append(Paragraph(f"{index}. {priority['영역']} - {priority['하위영역']} (Q{priority['번호']}, 평균 {priority['평균']:.2f})", h2))
        story.append(pdf_paragraph(f"문항: {priority['문항']}", body))
        story.append(pdf_paragraph(f"교육목표: {guide['goal']}", body))
        story.append(pdf_paragraph(f"교육 이론·판단 틀: {THEORY_AND_METHOD[priority['영역']]}", body))
        story.append(pdf_paragraph(f"사례활동: {guide['case']} / {guide['activity']}", body))
        story.append(pdf_paragraph(f"토의질문: {guide['discussion']}", body))
        story.append(pdf_paragraph(f"실천과제: {guide['practice']}", body))
        story.append(Spacer(1, 2 * mm))

    factors_order, blocks = course_blocks(priorities, course_option)
    story.append(Paragraph("5. 권장 교육과정 운영안", h1))
    story.append(pdf_paragraph(f"과정 유형: {course_option} / 중심 영역: {' · '.join(factors_order)}", body))
    course_data = [[pdf_paragraph("시간", body), pdf_paragraph("교육 내용", body), pdf_paragraph("운영 방법", body)]]
    for duration, topic, content in blocks:
        course_data.append([pdf_paragraph(duration, body), pdf_paragraph(topic, body), pdf_paragraph(content, body)])
    course_table = Table(course_data, colWidths=[22 * mm, 52 * mm, 81 * mm], repeatRows=1)
    course_table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDF1FC")), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#B9DDEF")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [course_table, Spacer(1, 3 * mm), Paragraph("교육 운영 시 참여자의 심리적 안전과 발언 선택권을 보장하고, 성찰을 강요하지 않습니다. 결과는 교육 주제 선정의 보조자료로 한정합니다.", small)]
    doc.build(story)
    return buffer.getvalue()


def start():
    apply_style()
    st.title("감·수·성 교육필요 분석 대시보드")
    st.caption("교정공무원 인권적 직무판단 자기성찰 설문 - 교육자용 집단 분석 화면")
    st.markdown("<div class='notice'>이 화면은 개인의 인권감수성을 평가하거나 인사자료로 활용하기 위한 것이 아닙니다. 익명 응답의 <b>집단 수준 경향</b>을 바탕으로 강의의 교육 필요와 실습 주제를 설계하기 위한 도구입니다. 소수 응답의 비교는 변동이 클 수 있으므로, 수치와 현장 맥락을 함께 해석하십시오.</div>", unsafe_allow_html=True)
    require_dashboard_login()

    with st.sidebar:
        st.header("분석 설정")
        if st.button("자료 새로고침"):
            load_records.clear()
        records, error = load_records()
        if error:
            st.error(error)
            st.stop()
        response_dates = [row["_submitted_at"].date() for row in records]
        first_date, last_date = min(response_dates), max(response_dates)
        st.subheader("응답 기간")
        date_range = st.date_input(
            "응답시각 범위",
            value=(first_date, last_date),
            min_value=first_date,
            max_value=last_date,
            help="시작일과 종료일을 모두 선택하면 해당 날짜(00:00~23:59)에 제출된 응답만 분석합니다.",
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date, end_date = first_date, last_date
            st.info("시작일과 종료일을 모두 선택하면 기간 필터가 적용됩니다.")
        filters = {}
        for column, label in DEMOGRAPHICS.items():
            options = sorted({str(row.get(column, "미응답")) or "미응답" for row in records})
            filters[column] = st.selectbox(label, ["전체"] + options)

    selected = filtered_records(records, filters, start_date, end_date)
    st.subheader("분석 대상")
    c1, c2, c3 = st.columns(3)
    c1.metric("전체 유효 응답", len(records))
    c2.metric("현재 선택 집단", len(selected))
    c3.metric("분석 상태", "분석 가능")
    st.caption(f"적용된 응답 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    if len(selected) == 0:
        st.warning("선택 조건에 맞는 응답이 없습니다. 기간 또는 인구학적 필터를 조정해 주세요.")
        st.stop()

    factors = factor_stats(selected)
    left, right = st.columns([1.05, .95])
    with left:
        st.subheader("영역별 응답 경향")
        st.plotly_chart(render_chart(factors), use_container_width=True)
    with right:
        st.subheader("해석 원칙")
        st.markdown("- 높은 응답은 이 집단이 비교적 익숙하게 보고한 **자원**입니다.\n- 낮은 응답은 다음 교육에서 더 구체적으로 연습해 볼 **우선 성찰 지점**입니다.\n- 개인이나 집단의 능력·도덕성·직무수행 우열을 뜻하지 않습니다.\n- 소수 응답의 수치는 변동이 크므로, 단일 문항보다 영역·하위영역·현장 사례를 함께 검토하십시오.")
        st.dataframe(factors, use_container_width=True, hide_index=True)

    st.subheader("한눈에 보는 인구학적 구성")
    demo_rows = demographic_distribution(selected)
    demo_display_rows = [{key: value for key, value in row.items() if key != "묶음순서"} for row in demo_rows]
    demo_left, demo_right = st.columns([1.12, .88])
    with demo_left:
        st.plotly_chart(render_demographic_chart(demo_rows), use_container_width=True)
    with demo_right:
        st.dataframe(demo_display_rows, use_container_width=True, hide_index=True, column_config={"비율": st.column_config.NumberColumn(format="%.1f%%")})

    st.subheader("인구학적 집단별 감·수·성 비교")
    chosen_column = st.selectbox("비교할 인구학적 항목", list(DEMOGRAPHICS), format_func=lambda column: DEMOGRAPHICS[column])
    comparison_rows = factor_by_demographic(selected, chosen_column)
    compare_left, compare_right = st.columns([1.18, .82])
    with compare_left:
        st.plotly_chart(render_group_comparison(comparison_rows, DEMOGRAPHICS[chosen_column]), use_container_width=True)
    with compare_right:
        st.caption("범주별 평균은 해당 범주 안에서의 감·수·성 문항 평균입니다.")
        st.dataframe(comparison_rows, use_container_width=True, hide_index=True, column_config={"감": st.column_config.NumberColumn(format="%.2f"), "수": st.column_config.NumberColumn(format="%.2f"), "성": st.column_config.NumberColumn(format="%.2f")})

    st.subheader("높은 응답과 우선 성찰 지점")
    render_profile_summary(selected)

    st.subheader("이번 강의의 우선 교육 주제")
    st.caption("선정 방식: 감·수·성 각 영역에서 평균이 가장 낮고 1~2점 응답 비율이 높은 문항을 하나씩 제시합니다. 한 영역의 낮은 문항이 여러 개여도 다른 영역의 다음 낮은 문항을 우선해, 세 판단영역을 함께 다룹니다.")
    priorities = priority_topics(selected)
    for index, priority in enumerate(priorities, 1):
        st.markdown(f"### {index}. {priority['영역']} - {priority['하위영역']}")
        st.write(f"**Q{priority['번호']}.** {priority['문항']}")
        render_learning_plan(priority)

    st.subheader("분석 결과를 반영한 교육과정 구성")
    st.caption("헌법적 비례성·절차 판단, 경험학습, 사례기반 학습, 성찰저널과 동료 피드백을 결합한 선택형 운영안입니다.")
    course_option = render_course_plan(priorities)

    st.subheader("교육계획 PDF 내려받기")
    st.caption("현재 선택한 응답기간과 인구학적 조건, 분석 결과 및 교육계획을 한글 PDF로 정리합니다.")
    try:
        pdf_bytes = build_pdf_report(selected, filters, start_date, end_date, course_option)
        st.download_button(
            "교육필요 분석 및 교육계획 PDF 다운로드",
            data=pdf_bytes,
            file_name=f"감수성_교육필요_분석_{start_date:%Y%m%d}-{end_date:%Y%m%d}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )
    except RuntimeError as error:
        st.error(f"PDF를 만들지 못했습니다: {error}")

    st.subheader("문항별 교육필요 확인")
    rows = item_stats(selected)
    st.dataframe(sorted(rows, key=lambda x: (x["평균"], -x["낮은 응답(1~2) 비율"])), use_container_width=True, hide_index=True, column_config={"평균": st.column_config.NumberColumn(format="%.2f"), "낮은 응답(1~2) 비율": st.column_config.NumberColumn(format="%.1f%%")})

    st.subheader("교육 운영 원칙")
    st.markdown("**권장 흐름:** 사례 제시 → 관찰·감정 언어 추출 → 비례성·절차 대안 비교 → 권위·편견·피로 성찰 → 한 가지 실천 약속.  \n공감이나 성찰을 강요하지 말고, 참여자의 심리적 안전·자율성·발언 선택권을 보장하십시오. 이 결과는 교육 주제 선정의 보조 자료이며, 진단·등급화·인사평가·기관 간 비교의 근거로 사용하지 않습니다.")
    st.caption(f"생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')} | 데이터는 읽기 전용으로 조회됩니다.")


if __name__ == "__main__":
    start()
