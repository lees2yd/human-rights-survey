import streamlit as st
import pandas as pd
from datetime import datetime
import os
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="인권감수성 설문", layout="wide")
st.warning("VERSION CHECK 2025-01-TEST")

QUESTIONS = [
    "수용자가 소란을 피울 때, 그 안에 두려움이나 불안이 있을 수 있다고 생각한다.",
    "수용자의 말투나 표정을 보며 화남, 슬픔, 걱정 같은 감정을 쉽게 떠올린다.",
    "수용자의 감정을 단정하지 않고, 대화나 관찰로 다시 확인하려 한다.",
    "수용자와 마주할 때 내 감정이 어떠했는지 알아본다.",
    "내 감정이 단순한 기분이 아니라 내가 원하는 욕구(안전, 존중 등)가 있음을 알아차린다.",
    "수용자의 감정을 이해하려는 노력 자체가 내 공감능력을 키운다고 본다.",
    "정신건강 문제 있는 수용자의 과도한 반응이 환청이나 불안 등 다양한 심리적 문제 때문일 수 있는지 먼저 살핀다.",
    "정신건강 문제 있는 수용자가 흥분한 경우, 지시를 간단히 하고 짧게 말한다.",
    "정신문제 있는 수용자에게 불빛·소리·접촉 등이 괴로운 자극일 수 있음을 이해한다.",
    "내가 수용자에 대해 하려는 행동이 단순히 감정 배출인지, 아니면 업무에 꼭 필요한 것인지 구분한다.",
    "감정이 주는 정보를 인식하고 그 정보를 바탕으로 행동한다.",
    "나는 편리함을 포기하더라도 규정을 지키려고 의식적으로 노력한다.",
    "내가 취하는 조치가 목적에 맞으며, 꼭 필요한 정도인지 먼저 살핀다.",
    "수용자에게 조치를 할 때는 반드시 정해진 절차를 따라서 한다.",
    "수용자에 대한 대응은 언제나 헌법 기준에 맞게 조정한다.",
    "정신건강 문제가 있는 수용자의 자해 등 위험 신호가 보이면 정해진 절차에 따라 조치한다.",
    "정신건강 문제가 있는 수용자에게 문제 상황 발생 시 의료·심리 전문가와 상의해 대응을 조정한다.",
    "정신건강 문제가 있는 수용자에 대한 대응방식이 그들의 정신상태에 적합한지 고려한다.",
    "수용자를 대할 때 나의 편견으로 인해 반응이 달라지지 않았는지 다시 생각한다.",
    "나는 수용자를 집단이 아닌 개인으로 이해하려 노력한다.",
    "동료들의 압력에 따라 행동한 적이 없는지 점검한다.",
    "나는 권위에 휘둘리지 않도록 스스로 판단하려 노력한다.",
    "과거와 비교해 나의 업무 습관이 달라졌다고 느낀다.",
    "내 감정이 피로나 스트레스로 과장되었을 가능성을 고려한다.",
    "정신질환을 이유로 수용자를 구분하지 않으려 노력한다.",
    "동료 분위기에 휩쓸린 적이 없는지 다시 생각한다.",
    "정신건강 문제가 있는 수용자를 단정하지 않으려 노력한다."
]

def interpret(total):
    if total <= 47:
        return "매우 낮은 범위: 인권 상황에서 감정 인식, 기준 적용, 성찰의 연결이 제한적일 수 있습니다."
    elif total <= 67:
        return "낮은 범위: 일부 요소는 작동하나 갈등 상황에서 판단이 흔들릴 가능성이 있습니다."
    elif total <= 87:
        return "중간 범위: 전반적으로 균형적이나 상황에 따라 편차가 나타날 수 있습니다."
    else:
        return "높은 범위: 감정–기준–성찰이 비교적 일관되게 통합되어 작동할 가능성이 큽니다."

DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "responses.csv")

SPREADSHEET_KEY = "12l-MzIhszbWb5kV3muWyGoqyfBaKD4CARjqKktndiAg"

def save(row):
    scope = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope,
    )
    client = gspread.authorize(creds)
    
 
    sh = client.open_by_key(SPREADSHEET_KEY)
    sheet = sh.worksheet("sheet1")
    sheet.append_row(list(row.values()))
    st.success("Google Sheets 저장 시도 완료")

st.title("인권감수성 설문 (27문항)")
st.caption("1=전혀 그렇지 않다 / 4=매우 그렇다")

with st.form("survey"):
    answers = []
    for i, q in enumerate(QUESTIONS, 1):
        st.write(f"{i}. {q}")
        answers.append(st.radio("", [1,2,3,4], horizontal=True, key=i))
    submit = st.form_submit_button("제출")

if submit:
    total = sum(answers)

    감 = sum(answers[0:11])     # 1~11
    수 = sum(answers[11:18])    # 12~18
    성 = sum(answers[18:27])    # 19~27

    st.subheader("결과")
    st.write(f"총점: **{total}점** (27~108)")
    st.write(f"감(감정 인식·공감): **{감}점** (11~44)")
    st.write(f"수(기준 수용·판단): **{수}점** (7~28)")
    st.write(f"성(성찰·편견 점검): **{성}점** (9~36)")

    st.info(interpret(total))

    row = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total": total,
        "감": 감,
        "수": 수,
        "성": 성
    }

    for i, a in enumerate(answers, 1):
        row[f"q{i}"] = a

    save(row)
    st.write("저장 위치:", CSV_PATH)
    st.success("응답이 저장되었습니다.")
    st.caption(
    "※ 본 설문은 연구 목적의 자가점검 도구이며, "
    "개인에 대한 진단이나 인사평가를 의미하지 않습니다."
    )





