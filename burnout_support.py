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
BAT_REFERENCE = {'탈진': (2.84, .77), '심적거리': (2.32, .79),
                 '인지적 조절 손상': (2.13, .69), '정서적 조절 손상': (2.31, .74)}

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

BAT_PLAIN_MEANINGS = {
    '탈진': '몸과 마음의 에너지가 많이 소모되고, 일을 마친 뒤에도 기운을 회복하기 어려운 경험입니다.',
    '심적거리': '일에 대한 관심이나 의미가 줄고, 업무에서 마음이 멀어지는 경험입니다. 동료와 사이가 나쁘다는 뜻은 아닙니다.',
    '인지적 조절 손상': '집중하거나 또렷하게 생각하기 어렵고, 깜빡하거나 실수하는 경험입니다. 지능이나 업무능력이 낮다는 판정이 아닙니다.',
    '정서적 조절 손상': '일하면서 짜증·슬픔이 생기거나, 감정을 알아차리고 반응을 조절하기 어려운 경험입니다. 성격이나 정신질환을 판정하는 말이 아닙니다.',
}
BAT_EXPERIENCE_WORDS = {
    '탈진':'피로와 회복의 어려움', '심적거리':'일에 대한 무관심·거리감',
    '인지적 조절 손상':'집중·기억·명료한 사고의 어려움',
    '정서적 조절 손상':'감정을 알아차리고 반응을 조절하는 어려움',
}


def bat_reference_explanation(factor, value):
    reference, sd = BAT_REFERENCE[factor]
    lower, upper = reference-sd, reference+sd
    if value < lower-1e-9:
        position = "연구의 참고범위보다 아래에 있습니다."
    elif value > upper+1e-9:
        position = "연구의 참고범위보다 위에 있습니다."
    else:
        position = "연구의 참고범위 안에 있습니다."
    experience = BAT_EXPERIENCE_WORDS[factor]
    if abs(value-reference)<.005:
        comparison = f"참고 연구 평균 {reference:.2f}점과 비슷합니다. 비교상 {experience}을 보고한 정도가 연구 평균과 비슷한 응답입니다."
    elif value>reference:
        comparison = f"참고 연구 평균 {reference:.2f}점보다 {value-reference:.2f}점 높습니다. 비교상 {experience}을 더 많이 보고한 응답입니다."
    else:
        comparison = f"참고 연구 평균 {reference:.2f}점보다 {reference-value:.2f}점 낮습니다. 비교상 {experience}을 덜 보고한 응답이며, 어려움이 전혀 없다는 뜻은 아닙니다."
    return f"나의 점수는 {value:.2f}점입니다. {comparison} {position}"


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
    rows = [{'영역': f, '나의 점수': round(v, 3), '연구 참고평균': BAT_REFERENCE[f][0], '연구 참고범위': f'{BAT_REFERENCE[f][0]-BAT_REFERENCE[f][1]:.2f} ~ {BAT_REFERENCE[f][0]+BAT_REFERENCE[f][1]:.2f}'} for f, v in scores.items()]
    st.dataframe(rows, hide_index=True, use_container_width=True)
    st.caption('참고평균·범위는 공기업 사무직 345명의 K-BAT 예비연구 표 5를 바탕으로 했습니다. 범위는 평균을 중심으로 점수의 퍼짐을 반영한 비교용 구간(평균 ± 1표준편차)이며, 교도관의 정상범위나 위험 기준이 아닙니다. 다른 참여자의 응답은 조회하지 않습니다.')
    for factor, value in scores.items():
        st.markdown(f'**{factor}**')
        st.write(BAT_PLAIN_MEANINGS[factor])
        st.write(bat_reference_explanation(factor, value))
    st.caption('높고 낮다는 말은 인격·능력의 좋고 나쁨이 아니라 해당 경험을 보고한 정도입니다. 참고 평균과의 작은 차이를 의미 있는 차이로 단정하지 않습니다. 참고범위 안·밖은 정상·위험 등급이 아닙니다. 근무조건과 실제 어려움을 함께 살펴보세요.')
    st.download_button('나의 소진 결과 CSV', csv_bytes(rows), 'my_burnout.csv', 'text/csv', key='bat_personal_csv')

def render_bat_dashboard(records, items=None):
    from burnout_insights import render_bat_quality, render_bat_insights
    st.subheader('직무소진 분석 · K-BAT 22문항')
    render_bat_quality(records)
    valid = [(r, bat_scores(r)) for r in records]
    valid = [(r, s) for r, s in valid if s is not None]
    n = len(valid)
    st.write(f'선택 집단 {len(records)}명 중 소진 완전응답 {n}명 · 미수집/불완전 {len(records)-n}명')
    st.caption('기존 25문항 자료는 감·수·성 분석에 유지됩니다. 소진 분석은 22문항 모두 1~5점으로 응답한 자료만 사용하며 결측을 0점으로 처리하지 않습니다.')
    if n == 0:
        st.info('소진 22문항 완전응답이 아직 없습니다.')
        return
    if n < 5:
        render_bat_anonymous_detail(valid)
        st.info('개별 점수는 위에서 확인할 수 있습니다. 집단 비율·실시일 및 인구학적 통계비교는 유효응답 5명 이상인 경우에 제공합니다.')
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
    render_bat_insights(valid, items)
    with st.expander('임시 익명번호별 개인·문항 상세 보기', expanded=False):
        render_bat_anonymous_detail(valid)


def anonymous_item_rows(record):
    if bat_scores(record) is None:
        return []
    return [{'설문순서': j, '원문번호': original, '영역': factor, '문항': text,
             '점수': int(float(record[f'BAT{original}']))}
            for j, (original, factor, text) in enumerate(BAT_ITEMS, 1)]


def render_bat_anonymous_detail(valid):
    """교육자 전용: 1명부터 영역·문항별 점수. 개인정보는 결합하지 않는다."""
    n = len(valid)
    if not n:
        return
    st.markdown('#### 임시 익명번호별 영역·문항 점수')
    st.caption('이 영역은 로그인한 교육자용입니다. 번호는 현재 세션·선택 자료 안에서만 유지되며 추적용 식별자가 아닙니다. 제출시각·성별·연령·직급은 함께 표시하지 않습니다.')
    if n < 5:
        st.warning('소수 응답의 개별 점수입니다. 특히 1명일 때는 임시번호를 사용해도 참여 상황을 아는 사람이 응답자를 추정할 수 있습니다. 공개 화면이나 교육생 전체에게 공유할 때 유의하십시오.')
    signature = tuple(tuple(float(r[c]) for c in BAT_COLUMNS) for r, _ in valid)
    if st.session_state.get('_bat_signature') != signature:
        order = list(range(n))
        secrets.SystemRandom().shuffle(order)
        st.session_state['_bat_order'] = order
        st.session_state['_bat_signature'] = signature
    ordered = [valid[i] for i in st.session_state['_bat_order']]
    matrix = np.array([[scores[f] for f in BAT_FACTORS] for _, scores in ordered])
    ids = [f'익명 {i+1:03d}' for i in range(n)]
    if n > 1:
        heat = go.Figure(go.Heatmap(z=matrix, x=BAT_FACTORS, y=ids, zmin=1, zmax=5,
                                   colorscale='YlGn', colorbar=dict(title='평균'),
                                   hovertemplate='%{y}<br>%{x}: %{z:.2f}<extra></extra>'))
        heat.update_layout(height=min(1200,max(340,n*23)),margin=dict(t=20,b=65),yaxis=dict(autorange='reversed'))
        st.plotly_chart(heat,use_container_width=True)
    chosen = st.selectbox('확인할 임시 익명번호',ids,key='bat_detail_id')
    index = ids.index(chosen)
    record, scores = ordered[index]
    from burnout_insights import REFERENCE, REFERENCE_URL
    area_rows = [{'영역':f,'문항수':sum(factor==f for _,factor,_ in BAT_ITEMS),'개인평균(1~5)':round(v,3), '선행연구 참고평균':REFERENCE[f][0], '차이(개인-참고)':round(v-REFERENCE[f][0],3)} for f,v in scores.items()]
    st.dataframe(area_rows,hide_index=True,use_container_width=True)
    st.caption('참고평균은 공기업 사무직 345명의 K-BAT 예비연구 표 5입니다. 교도관 규준이나 위험 기준점이 아니며 직무·응답지침이 달라 차이를 참고로만 해석합니다.')
    st.markdown(f'[참고평균 출처]({REFERENCE_URL})')
    chart=go.Figure(go.Bar(x=BAT_FACTORS,y=[scores[f] for f in BAT_FACTORS],
                           marker_color='#369566',text=[f'{scores[f]:.2f}' for f in BAT_FACTORS],textposition='auto'))
    chart.update_layout(height=350,yaxis=dict(range=[0,5],title='영역 문항평균'),margin=dict(t=20,b=65))
    st.plotly_chart(chart,use_container_width=True)
    items = anonymous_item_rows(record)
    st.markdown('**22문항별 응답 점수**')
    st.dataframe(items,hide_index=True,use_container_width=True,column_config={'문항':st.column_config.TextColumn(width='large')})
    chart=go.Figure(go.Bar(x=[row['점수'] for row in items],y=[f"{row['설문순서']}. {row['영역']}" for row in items],
                           orientation='h',marker_color='#369566',customdata=[row['문항'] for row in items],
                           text=[str(row['점수']) for row in items],textposition='auto',
                           hovertemplate='%{customdata}<br>점수: %{x}<extra></extra>'))
    chart.update_layout(height=760,xaxis=dict(range=[0,5],dtick=1,title='응답 점수 (1~5점)'),
                         yaxis=dict(autorange='reversed'),margin=dict(l=10,r=20,t=20,b=45))
    st.plotly_chart(chart,use_container_width=True)
    st.caption('설문순서는 소진 설문 안의 1~22번입니다. 원문번호는 9번을 제외한 척도 문항 번호입니다. 높은 점수는 해당 경험을 많이 보고했음을 뜻하며 임상적 위험 판정은 아닙니다.')
    if n >= 5:
        average=matrix.mean(axis=0)
        compare=[]
        for j,f in enumerate(BAT_FACTORS):
            peers=np.delete(matrix[:,j],index)
            value=matrix[index,j]
            percentile=(np.sum(peers<value)+.5*np.sum(peers==value))/len(peers)*100
            compare.append({'영역':f,'개인평균':round(value,3),'집단평균(본인포함)':round(average[j],3),
                            '집단과 차이':round(value-average[j],3),'표본 내 상대위치(%)':round(float(percentile),1)})
        st.markdown('**선택 집단과의 비교**')
        st.dataframe(compare,hide_index=True,use_container_width=True)
        st.caption('상대위치=(본인보다 낮은 동료 수+동점 동료 수×0.5)÷본인 제외 동료 수×100. 현재 표본 내 상대위치이며 규준·소진 확률이 아닙니다. 1~4명일 때에는 이 비교를 표시하지 않습니다.')
