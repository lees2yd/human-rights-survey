"""실시일·인구학적 집단의 기술통계 및 독립표본 탐색적 비교."""
from itertools import combinations
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from burnout_support import BAT_FACTORS, bat_scores, csv_bytes
try:
    from scipy import stats
except ImportError:
    stats = None

DOMAINS = ['감', '수', '성'] + BAT_FACTORS
MIN_N = 5


def domain_scores(record, items):
    scores = {}
    for factor in ['감', '수', '성']:
        keys = [f'Q{i}' for i, f, _, _ in items if f == factor]
        try:
            values = [float(record[k]) for k in keys]
            if values and all(v in (1, 2, 3, 4) for v in values):
                scores[factor] = float(np.mean(values))
        except (KeyError, TypeError, ValueError):
            pass
    scores.update(bat_scores(record) or {})
    return scores


def holm_adjust(pvalues):
    """Holm 보정. 미검정 항목은 p=1로 보정 집합에 포함한다."""
    p = np.asarray(pvalues, dtype=float)
    order = np.argsort(p)
    result = np.ones(len(p)); prev = 0.
    for rank, index in enumerate(order):
        prev = max(prev, min(1., (len(p)-rank)*p[index]))
        result[index] = prev
    return result.tolist()


def welch_two(a, b):
    """평균차 방향은 A-B. 분산 0/표본 부족 시 추론을 보류한다."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    if min(len(a), len(b)) < MIN_N:
        return {'상태': '영역별 집단당 5명 미만'}
    if stats is None:
        return {'상태': 'scipy 설치 필요'}
    va, vb = a.var(ddof=1), b.var(ddof=1)
    if min(va, vb) <= 1e-12:
        return {'상태': '집단 내 분산 0: 추론 보류'}
    x, y = va/len(a), vb/len(b)
    se = np.sqrt(x+y)
    df = (x+y)**2/(x*x/(len(a)-1)+y*y/(len(b)-1))
    diff = a.mean()-b.mean(); t = diff/se
    p = float(2*stats.t.sf(abs(t), df))
    margin = float(stats.t.ppf(.975, df)*se)
    pooled = np.sqrt(((len(a)-1)*va+(len(b)-1)*vb)/(len(a)+len(b)-2))
    # 소표본 보정 J의 일반적 근사. 부호는 A-B 방향이다.
    g = (1-3/(4*(len(a)+len(b))-9))*diff/pooled
    return {'상태': '검정 완료', '검정': 'Welch t', '통계량': float(t), '자유도1': float(df),
            '자유도2': None, 'p': p, '평균차(A-B)': float(diff),
            '차이95%CI하한': float(diff-margin), '차이95%CI상한': float(diff+margin), 'Hedges g(A-B)': float(g)}


def welch_multi(groups):
    if stats is None:
        return {'상태': 'scipy 설치 필요'}
    if any(len(a)<MIN_N for a in groups):
        return {'상태': '영역별 집단당 5명 미만'}
    arrays = [np.asarray(a,dtype=float) for a in groups]
    n = np.array([len(a) for a in arrays],dtype=float)
    variances = np.array([a.var(ddof=1) for a in arrays])
    if np.any(variances <= 1e-12):
        return {'상태': '집단 내 분산 0: 추론 보류'}
    means=np.array([a.mean() for a in arrays]); k=len(arrays)
    w=n/variances; total=w.sum(); center=np.sum(w*means)/total
    term=np.sum((1-w/total)**2/(n-1))
    f=(np.sum(w*(means-center)**2)/(k-1))/(1+2*(k-2)/(k*k-1)*term)
    df2=(k*k-1)/(3*term)
    return {'상태': '검정 완료','검정': 'Welch ANOVA','통계량':float(f),
            '자유도1':float(k-1),'자유도2':float(df2),'p':float(stats.f.sf(f,k-1,df2))}


def summarize(groups):
    rows=[]
    for label, people in groups.items():
        for domain in DOMAINS:
            values=[p[domain] for p in people if domain in p]
            if len(values)<MIN_N:
                continue
            sd=float(np.std(values,ddof=1)); avg=float(np.mean(values))
            margin=float(stats.t.ppf(.975,len(values)-1)*sd/np.sqrt(len(values))) if stats is not None else None
            rows.append({'집단':label,'영역':domain,'유효응답수':len(values),'평균':round(avg,3),
                         '표준편차':round(sd,3),'중앙값':round(float(np.median(values)),3),
                         '평균95%CI하한':round(avg-margin,3) if margin is not None else None,
                         '평균95%CI상한':round(avg+margin,3) if margin is not None else None})
    return rows


def test_domains(groups):
    labels=list(groups); results=[]
    for d in DOMAINS:
        vectors=[[person[d] for person in groups[label] if d in person] for label in labels]
        base={'영역':d,'집단A':labels[0] if len(labels)==2 else '전체 선택 집단',
              '집단B':labels[1] if len(labels)==2 else '',
              '집단별 유효응답수': ' / '.join(str(len(v)) for v in vectors)}
        if len(labels)<2:
            outcome={'상태':'비교 집단 부족'}
        elif len(labels)==2:
            outcome=welch_two(*vectors)
        else:
            outcome=welch_multi(vectors)
        results.append({**base,**outcome})
    adjusted=holm_adjust([r.get('p',1.) for r in results])
    for r,padj in zip(results,adjusted):
        if 'p' in r:
            r['Holm보정p']=padj
            r['판단']='보정 후 유의한 차이' if padj<.05 else '유의한 차이 확인 안 됨'
    return results


def plot_summary(rows, domains, title):
    fig=go.Figure()
    labels=list(dict.fromkeys(r['집단'] for r in rows))
    for label in labels:
        chosen={r['영역']:r for r in rows if r['집단']==label and r['영역'] in domains}
        present=[d for d in domains if d in chosen]
        if not present: continue
        fig.add_bar(name=label,x=present,y=[chosen[d]['평균'] for d in present],
                    error_y=dict(type='data',array=[chosen[d]['표준편차'] for d in present]),
                    customdata=[chosen[d]['유효응답수'] for d in present],
                    hovertemplate='%{x}<br>평균 %{y:.3f}<br>유효응답 %{customdata}명<extra>%{fullData.name}</extra>')
    fig.update_layout(title=title,barmode='group',height=410,
                      yaxis=dict(title='문항평균',range=[0,4 if domains[0]=='감' else 5]),
                      legend=dict(orientation='h',y=-.3),margin=dict(t=55,b=100))
    st.plotly_chart(fig,use_container_width=True)


def show_results(groups, key, allow_tests=False):
    rows=summarize(groups)
    if not rows:
        st.info('표시 가능한 자료가 없습니다. 영역별로 각 집단의 유효응답이 5명 이상 필요합니다.')
        return
    plot_summary(rows,DOMAINS[:3],'감·수·성 · 1~4점')
    if any(r['영역'] in BAT_FACTORS for r in rows):
        plot_summary(rows,BAT_FACTORS,'직무소진 네 영역 · 1~5점')
    st.caption('오차막대는 응답자 간 표준편차입니다. 표의 평균 95% 신뢰구간과 구분합니다. 감·수·성은 높을수록 해당 판단 경향을, 소진은 높을수록 해당 소진 경험을 많이 보고한 것입니다.')
    st.dataframe(rows,hide_index=True,use_container_width=True)
    st.download_button('집단별 기술통계 CSV',csv_bytes(rows),f'{key}_summary.csv','text/csv',key=f'{key}_summary')
    with st.expander('영역별 특징 요약',expanded=False):
        for label in groups:
            for domains,name in [(DOMAINS[:3],'감·수·성'),(BAT_FACTORS,'소진')]:
                r=[x for x in rows if x['집단']==label and x['영역'] in domains]
                if len(r)!=len(domains): continue
                top=max(r,key=lambda x:x['평균']); low=min(r,key=lambda x:x['평균'])
                if top['평균']==low['평균']:
                    st.write(f"{label} · {name}: 영역 평균이 모두 {top['평균']:.2f}점입니다.")
                else:
                    st.write(f"{label} · {name}: 기술적으로 평균이 가장 높은 영역은 {top['영역']}({top['평균']:.2f}), 가장 낮은 영역은 {low['영역']}({low['평균']:.2f})입니다. 영역 간 차이에 대한 유의성 검정 결과는 아닙니다.")
    if not allow_tests or len(groups)<2:
        return
    confirmed=st.checkbox('비교 자료에 동일인의 중복·반복 응답이 없고, 서로 독립적인 참여자 집단임을 확인했습니다.',key=f'{key}_independent')
    if not confirmed:
        st.info('평균 비교는 볼 수 있습니다. 독립성 확인 전에는 p값을 산출하지 않습니다. 동일인 사전·사후 분석에는 연결용 익명코드가 필요합니다.')
        return
    if stats is None:
        st.warning('통계검정을 사용하려면 requirements.txt에 scipy를 추가하십시오. 기술통계는 계속 표시됩니다.')
        return
    results=test_domains(groups)
    display=[]
    for r in results:
        display.append({k:(f'{v:.3g}' if k in ['p','Holm보정p'] else round(v,4) if isinstance(v,float) else v) for k,v in r.items()})
    st.markdown('**영역별 집단 차이 검정**')
    st.dataframe(display,hide_index=True,use_container_width=True)
    st.download_button('통계검정 결과 CSV',csv_bytes([{k:r.get(k,'') for k in dict.fromkeys(k for r in results for k in r)} for r in results]),f'{key}_tests.csv','text/csv',key=f'{key}_tests')
    tested=[r for r in results if 'p' in r]; significant=[r['영역'] for r in tested if r['Holm보정p']<.05]
    st.write('현재 비교에서 Holm 보정 후 차이가 확인된 영역: '+(' · '.join(significant) if significant else '없음')+f' (검정 완료 {len(tested)}/7영역).')
    st.caption('2집단: Welch t 검정, 평균차 A-B의 개별 95% 신뢰구간, Hedges g. 3집단 이상: Welch ANOVA의 전체 집단 차이 검정이며 어느 집단 사이의 차이인지는 확정하지 않습니다. 보정 p값은 현재 한 번의 비교에 포함된 7영역을 Holm 방식으로 보정합니다. 신뢰구간은 다중비교 보정 전이며, 반복적인 날짜·조건 탐색 전체의 오류율까지 통제하지는 않습니다.')
    st.caption('유의하지 않음은 동일함의 증명이 아닙니다. 교육 전후 인과효과·인구학적 요인의 독립적 영향·기관 내 군집효과를 검증한 결과가 아닙니다. 분산이 0인 집단은 추론을 보류합니다.')


def render_comparison_dashboard(records, items, demographic_labels, category_order):
    st.subheader('실시일·인구학적 집단 비교')
    st.caption('사이드바에서 선택한 기간과 인구학적 조건 안에서 분석합니다. 실시일은 저장된 한국시간 제출일입니다. 날짜가 같은 여러 교육회차는 현재 자료로 분리할 수 없습니다. 각 영역·집단의 유효응답이 5명 미만이면 평균을 숨기고 검정을 보류합니다.')
    people=[(r,domain_scores(r,items)) for r in records]
    dates=sorted({r['_submitted_at'].date() for r,_ in people})
    overview, dates_tab, demo_tab=st.tabs(['실시일별 현황','두 실시일 비교','인구학적 비교·검정'])
    with overview:
        st.caption('많은 날짜를 한꺼번에 표시하면 복잡해질 수 있습니다. 살펴볼 날짜를 선택하십시오.')
        picked=st.multiselect('현황에 표시할 실시일',dates,default=dates[-5:],format_func=str,key='cmp_overview_dates')
        grouped={str(d):[s for r,s in people if r['_submitted_at'].date()==d] for d in picked}
        show_results(grouped,'by_date')
    with dates_tab:
        if len(dates)<2:
            st.info('선택 기간에 서로 다른 실시일이 두 개 이상 있어야 비교할 수 있습니다.')
        else:
            c1,c2=st.columns(2)
            a=c1.selectbox('실시일 A',dates,index=0,format_func=str,key='cmp_date_a')
            other=[d for d in dates if d!=a]
            b=c2.selectbox('실시일 B',other,index=len(other)-1,format_func=str,key='cmp_date_b')
            grouped={str(d):[s for r,s in people if r['_submitted_at'].date()==d] for d in [a,b]}
            show_results(grouped,'date_pair',True)
    with demo_tab:
        col=st.selectbox('분석할 인구학적 요소',list(demographic_labels),format_func=lambda x:demographic_labels[x],key='cmp_demo_column')
        include=st.checkbox('응답하지 않음·미응답 범주도 표시',False,key='cmp_unknown')
        unknown={'','미응답','응답하지 않음','None'}
        available={str(r.get(col,'')) for r,_ in people}
        if not include: available-=unknown
        ordered=[v for v in category_order.get(col,[]) if v in available]
        ordered+=sorted(available-set(ordered))
        categories=st.multiselect('비교할 범주 · 2개 선택 시 두 집단 검정, 3개 이상은 전체 차이 검정',ordered,default=ordered,key=f'cmp_categories_{col}_{include}')
        grouped={label:[s for r,s in people if str(r.get(col,''))==label] for label in categories}
        show_results(grouped,'demographic_compare',True)
        st.caption('사이드바에서 같은 인구학적 항목을 한 범주로 제한하면 다른 범주는 비교할 수 없습니다. 필요하면 해당 필터를 전체로 바꾸십시오. 연령·경력·직급 등의 서로 얽힌 영향을 분리하는 다변량 분석은 포함하지 않습니다.')
