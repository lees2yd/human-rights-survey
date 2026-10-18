"""K-BAT 22문항: 조수현 예비연구 표 3. 원문 번호 보존, 9번 제외."""
import csv
import io
import secrets
import numpy as np
import plotly.graph_objects as go
import streamlit as st

BAT_ITEMS = [
(1, '탈진', '직장에서 나는 정신적으로 지친다.'),
(2, '탈진', '직장에서 내가 하는 모든 일은 상당한 노력을 요한다.'),
(3, '탈진', '퇴근 후, 기운을 회복하는 것이 어렵다.'),
(4, '탈진', '직장에서 나는 체력적으로 지친다.'),
(5, '탈진', '아침에 일어나면, 직장에서 새로운 하루를 시작할 힘이 부족하다.'),
(6, '탈진', '직장에서 나는 적극적이고 싶지만, 왠지 그렇지 못한다.'),
(7, '탈진', '업무에 열중 할 경우, 평소보다 빨리 지친다.'),
(8, '탈진', '업무가 끝난 후, 나는 정신적으로 지치고 진이 빠진다.'),
(10, '심적거리', '직장에서 나는 내가 무엇을 하는지에 대해 생각하지 않고 기계적으로 일한다.'),
(11, '심적거리', '나는 내가 하는 업무가 정말 싫다.'),
(12, '심적거리', '나는 내 일에 무관심하다.'),
(13, '심적거리', '나는 내 업무가 다른 사람에게 어떠한 의미가 있을 지에 대해서 냉소적이다.'),
(14, '인지적 조절 손상', '나는 직장에서 한 가지 일에 집중하는 것이 힘들다.'),
(15, '인지적 조절 손상', '나는 직장에서 명료하게 생각하는 것이 힘들다.'),
(16, '인지적 조절 손상', '나는 직장에서 잘 까먹고 주의가 산만하다.'),
(17, '인지적 조절 손상', '난 일을 할 때, 집중하기가 힘들다.'),
(18, '인지적 조절 손상', '나는 직장에서 다른 일에 신경 쓰다가 실수를 하곤 한다.'),
(19, '정서적 조절 손상', '직장에서 나는 내 감정을 다스릴 수가 없다.'),
(20, '정서적 조절 손상', '직장에서 내가 감정적으로 어떤 반응을 하는지 인식하지 못한다.'),
(21, '정서적 조절 손상', '직장에서 일이 내가 원하는 대로 흘러가지 않을 경우에 짜증이 난다.'),
(22, '정서적 조절 손상', '직장에서 나는 이유 없이 화가 나거나 슬퍼지곤 한다.'),
(23, '정서적 조절 손상', '직장에서 나는 뜻하지 않게 과하게 반응하곤 한다.'),
]
BAT_FACTORS = list(dict.fromkeys(f for _, f, _ in BAT_ITEMS))
BAT_COLUMNS = [f'BAT{i}' for i, _, _ in BAT_ITEMS]
# 논문은 1/5점 양끝만 명시. 중간 응답 문구는 운영용으로 명시적으로 지정.
BAT_LABELS = {1: '전혀 아니다', 2: '드물게 그렇다', 3: '때때로 그렇다', 4: '자주 그렇다', 5: '항상 그렇다'}

def bat_scores(row):
    """22문항 완전응답만 계산. 결측·비정수·범위 밖 값은 제외."""
    try:
        values = {key: float(row[key]) for key in BAT_COLUMNS}
    except (KeyError, TypeError, ValueError):
        return None
    if any(v not in (1, 2, 3, 4, 5) for v in values.values()):
        return None
    return {f: float(np.mean([values[f'BAT{i}'] for i, factor, _ in BAT_ITEMS if factor == f])) for f in BAT_FACTORS}

def scale_percent(value):
    return (value - 1) / 4 * 100

def csv_bytes(rows):
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode('utf-8-sig')

def render_bat_personal(row):
    scores = bat_scores(row)
    if scores is None:
        st.info('직무소진 22문항 응답을 완료하면 결과가 표시됩니다.')
        return
    st.subheader('나의 직무소진 네 영역')
    st.caption('점수가 높을수록 해당 소진 경험을 많이 보고한 것입니다. 네 영역을 각각 해석하며 총점·진단등급은 산출하지 않습니다.')
    fig = go.Figure(go.Bar(x=list(scores.values()), y=BAT_FACTORS, orientation='h', text=[f'{v:.2f}' for v in scores.values()], textposition='auto'))
    fig.update_layout(xaxis=dict(range=[0, 5], title='문항평균 (1~5점)'), yaxis=dict(autorange='reversed'), margin=dict(l=10, r=20, t=20, b=40), height=330)
    st.plotly_chart(fig, use_container_width=True)
    rows = [{'영역': f, '평균(1~5)': round(v, 3), '척도범위 환산(%)': round(scale_percent(v), 1)} for f, v in scores.items()]
    st.dataframe(rows, hide_index=True, use_container_width=True)
    st.caption('환산율=(평균−1)÷4×100. 척도 범위에서의 위치이며 소진 확률이나 백분위가 아닙니다. 이 개인 결과는 집단 자료를 조회하지 않습니다.')
    st.download_button('나의 소진 결과 CSV', csv_bytes(rows), 'my_burnout.csv', 'text/csv', key='bat_personal_csv')

def render_bat_dashboard(records):
    st.subheader('직무소진 분석 · K-BAT 22문항')
    valid = [(r, bat_scores(r)) for r in records]
    valid = [(r, s) for r, s in valid if s is not None]
    n = len(valid)
    st.write(f'선택 집단 {len(records)}명 중 소진 완전응답 {n}명 · 미수집/불완전 {len(records)-n}명')
    st.caption('기존 25문항 자료는 감·수·성 분석에 유지됩니다. 소진 분석은 22문항 모두 1~5점으로 응답한 자료만 사용하며 결측을 0점으로 처리하지 않습니다.')
    if n < 5:
        st.info('소진 유효응답 5명 이상일 때 집단 및 개인 비교를 표시합니다. 작은 집단의 재식별 가능성을 줄이기 위한 운영 기준입니다.')
        return
    matrix = np.array([[s[f] for f in BAT_FACTORS] for _, s in valid])
    avg = matrix.mean(axis=0)
    summary = []
    for j, f in enumerate(BAT_FACTORS):
        summary.append({'영역': f, '응답자수': n, '평균(1~5)': round(avg[j], 3), '표준편차': round(float(matrix[:, j].std(ddof=1)), 3), '중앙값': round(float(np.median(matrix[:, j])), 3), '척도범위 환산(%)': round(scale_percent(avg[j]), 1), '영역평균 4점 이상 비율(%)': round(float(np.mean(matrix[:, j] >= 4)*100), 1)})
    fig = go.Figure(go.Bar(x=BAT_FACTORS, y=avg, error_y=dict(type='data', array=matrix.std(axis=0, ddof=1)), text=[f'{v:.2f}' for v in avg], textposition='auto'))
    fig.update_layout(yaxis=dict(range=[0, 5], title='문항평균 (1~5점)'), height=380, margin=dict(t=20, b=65))
    st.plotly_chart(fig, use_container_width=True)
    st.caption('오차막대는 응답자 간 표준편차입니다. 감·수·성은 4점, 소진은 5점 척도이므로 두 척도 점수의 높낮이를 직접 비교하지 않습니다.')
    st.dataframe(summary, hide_index=True, use_container_width=True)
    st.caption('척도범위 환산율=(평균−1)÷4×100. 4점 이상 비율=해당 영역 문항평균이 4 이상인 사람 수÷소진 완전응답자 수×100. 임상적 위험군 비율이 아닙니다.')
    st.download_button('소진 집단 요약 CSV', csv_bytes(summary), 'burnout_group_summary.csv', 'text/csv')
    dist = go.Figure()
    for score in range(1, 6):
        percentages = []
        for f in BAT_FACTORS:
            columns = [f'BAT{i}' for i, factor, _ in BAT_ITEMS if factor == f]
            values = [float(r[c]) for r, _ in valid for c in columns]
            percentages.append(sum(v == score for v in values)/len(values)*100)
        dist.add_bar(name=f'{score}점', x=BAT_FACTORS, y=percentages)
    dist.update_layout(barmode='stack', yaxis=dict(range=[0, 100], title='응답 비율 (%)'), height=380, margin=dict(t=25, b=65))
    st.plotly_chart(dist, use_container_width=True)
    st.caption('응답분포의 분모는 영역별 응답자 수×문항 수입니다. 위의 사람 기준 비율과 구분합니다.')
    if st.checkbox('교육자 전용 · 임시 익명번호별 개인 비교 표시', value=False):
        st.caption('번호와 순서는 이 세션의 현재 필터 결과 안에서만 유지됩니다. 시간·성별·연령·직급은 표시하거나 내려받지 않습니다. 번호는 추적용 식별자가 아니며 필터 변경 시 다시 배정됩니다. 소규모 집단과 반복 필터 비교를 통한 추정 가능성까지 제거하지는 못합니다.')
        signature = tuple(tuple(float(r[c]) for c in BAT_COLUMNS) for r, _ in valid)
        if st.session_state.get('_bat_signature') != signature:
            order = list(range(n))
            secrets.SystemRandom().shuffle(order)
            st.session_state['_bat_order'] = order
            st.session_state['_bat_signature'] = signature
        anon = matrix[st.session_state['_bat_order']]
        ids = [f'익명 {i+1:03d}' for i in range(n)]
        heat = go.Figure(go.Heatmap(z=anon, x=BAT_FACTORS, y=ids, zmin=1, zmax=5, colorscale='YlOrRd', colorbar=dict(title='평균'), hovertemplate='%{y}<br>%{x}: %{z:.2f}<extra></extra>'))
        heat.update_layout(height=min(1200, max(400, n*23)), margin=dict(t=25, b=65), yaxis=dict(autorange='reversed'))
        st.plotly_chart(heat, use_container_width=True)
        chosen = st.selectbox('비교할 임시 익명번호', ids)
        k = ids.index(chosen)
        comparison = []
        for j, f in enumerate(BAT_FACTORS):
            v = anon[k, j]
            # 본인 제외, 동점은 절반 반영. 임상 규준이 아닌 선택 표본 내 상대 위치.
            peers = np.delete(anon[:, j], k)
            percentile = (np.sum(peers < v) + .5*np.sum(peers == v))/len(peers)*100
            comparison.append({'영역': f, '개인평균': round(v, 3), '집단평균(본인포함)': round(avg[j], 3), '집단과 차이': round(v-avg[j], 3), '표본 내 상대위치(%)': round(float(percentile), 1)})
        chart = go.Figure()
        chart.add_bar(name=chosen, x=BAT_FACTORS, y=anon[k])
        chart.add_bar(name='집단평균(본인포함)', x=BAT_FACTORS, y=avg)
        chart.update_layout(barmode='group', yaxis=dict(range=[0, 5]), height=380, margin=dict(t=30, b=65))
        st.plotly_chart(chart, use_container_width=True)
        st.dataframe(comparison, hide_index=True, use_container_width=True)
        st.caption('상대위치=(본인보다 낮은 동료 수+동점 동료 수×0.5)÷본인을 제외한 동료 수×100. 현재 선택 표본에 한정되며 전국 교도관 규준이나 소진 확률이 아닙니다.')
