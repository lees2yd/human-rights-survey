"""소진 대시보드: 자료 점검, 참조 평균, 분포, 문항 패턴, 동반 경험, 탐색적 관련성."""
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from burnout_support import BAT_ITEMS, BAT_COLUMNS, BAT_FACTORS, bat_scores, csv_bytes

REFERENCE = {
    '탈진': (2.84, .77), '심적거리': (2.32, .79),
    '인지적 조절 손상': (2.13, .69), '정서적 조절 손상': (2.31, .74),
}
REFERENCE_URL = 'https://burnoutassessmenttool.be/wp-content/uploads/2022/01/2020.11.30-Validation-of-K-BAT-_Korean-Industrial-and-Organizational-Psy..pdf'


def quality_summary(records):
    counts = {'소진 미수집(22문항 모두 빈칸)':0, '일부 결측·비정상 응답':0, '22문항 완전응답':0, '완전응답 중 전 문항 동일점수':0}
    for row in records:
        values=[row.get(c) for c in BAT_COLUMNS]
        if all(v is None or str(v).strip()=='' for v in values):
            counts['소진 미수집(22문항 모두 빈칸)']+=1
        elif bat_scores(row) is None:
            counts['일부 결측·비정상 응답']+=1
        else:
            counts['22문항 완전응답']+=1
            if len({float(v) for v in values})==1:
                counts['완전응답 중 전 문항 동일점수']+=1
    return [{'자료 상태':k,'응답수':v} for k,v in counts.items()]


def bat_matrix(valid):
    return np.array([[s[f] for f in BAT_FACTORS] for _,s in valid], dtype=float)


def reference_rows(valid):
    matrix=bat_matrix(valid)
    result=[]
    for j,f in enumerate(BAT_FACTORS):
        values=matrix[:,j]; avg=float(values.mean()); ref,sd=REFERENCE[f]
        result.append({'영역':f,'유효응답수':len(values),'현재집단평균':round(avg,3),
                       '선행연구평균':ref,'선행연구표준편차':sd,'평균차(현재-참고)':round(avg-ref,3),
                       '현재중앙값':round(float(np.median(values)),3),
                       '현재Q1':round(float(np.quantile(values,.25)),3),'현재Q3':round(float(np.quantile(values,.75)),3),
                       '현재최소':round(float(values.min()),3),'현재최대':round(float(values.max()),3)})
    return result


def aggregate_items(valid):
    rows=[]
    for j,(original,f,text) in enumerate(BAT_ITEMS,1):
        values=np.array([float(r[f'BAT{original}']) for r,_ in valid])
        rows.append({'설문순서':j,'원문번호':original,'영역':f,'문항':text,'유효응답수':len(values),
                     '평균':round(float(values.mean()),3),'표준편차':round(float(values.std(ddof=1)),3) if len(values)>1 else None,
                     '4~5점응답수':int(np.sum(values>=4)),'4~5점응답률(%)':round(float(np.mean(values>=4)*100),1),
                     '1점응답률(%)':round(float(np.mean(values==1)*100),1),'5점응답률(%)':round(float(np.mean(values==5)*100),1)})
    return rows


def overlap_counts(matrix, threshold):
    counts=(matrix>=threshold).sum(axis=1)
    return [{'조건충족영역수':i,'응답자수':int(np.sum(counts==i)),
             '비율(%)':round(float(np.mean(counts==i)*100),1)} for i in range(5)]


def cronbach_alpha(values):
    values=np.asarray(values,dtype=float)
    k=values.shape[1]
    totalvar=np.var(values.sum(axis=1),ddof=1)
    if values.shape[0]<2 or k<2 or totalvar<=1e-12:
        return None
    return float(k/(k-1)*(1-np.var(values,axis=0,ddof=1).sum()/totalvar))


def render_bat_quality(records):
    with st.expander('분석 자료 점검 · 포함/제외 기준',expanded=False):
        st.dataframe(quality_summary(records),hide_index=True,use_container_width=True)
        st.caption('이 표의 분모는 기존 감·수·성 25문항 검증을 통과하여 현재 필터에 포함된 자료입니다. 소진 미수집과 불완전 응답은 소진 집계에서 제외합니다. 동일점수 응답은 실제 경험일 수도 있어 자동 제외하지 않습니다. 중복 응답 여부와 응답 소요시간은 현재 자료로 확인하지 못합니다.')


def render_bat_insights(valid, items=None):
    if len(valid)<5:
        return
    matrix=bat_matrix(valid); n=len(valid)
    ref_tab, dist_tab, item_tab, pattern_tab, relation_tab=st.tabs([
        '참고평균·집단분포','문항별 집단 경향','동반 경험 패턴','감·수·성과의 관련성','척도 점검'])
    with ref_tab:
        rows=reference_rows(valid)
        st.markdown('**현재 집단과 선행연구 참고 평균**')
        fig=go.Figure()
        fig.add_bar(name=f'현재 선택 집단(n={n})',x=BAT_FACTORS,y=matrix.mean(axis=0),marker_color='#369566')
        fig.add_bar(name='공기업 사무직 참고 평균(n=345)',x=BAT_FACTORS,y=[REFERENCE[f][0] for f in BAT_FACTORS],marker_color='#9aaebd')
        fig.update_layout(barmode='group',yaxis=dict(range=[0,5],title='영역 문항평균'),height=390,margin=dict(t=20,b=75))
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(rows,hide_index=True,use_container_width=True)
        st.markdown(f'[참고 근거: K-BAT 예비연구 표 5]({REFERENCE_URL})')
        st.caption('선행연구는 공기업 사무직 345명의 기술통계이며 교도관 규준·정상범위·위험 절단점이 아닙니다. 비교 표본의 직무·시점·응답지침 차이가 있어 참고 목적으로만 표시하며 외부 평균과의 유의성 검정이나 위험등급은 산출하지 않습니다. 현재 설문의 중간 응답 문구는 운영용으로 설정되어 있습니다.')
        fig=go.Figure()
        for j,f in enumerate(BAT_FACTORS):
            fig.add_trace(go.Box(y=matrix[:,j],name=f,boxpoints=False,marker_color='#369566',quartilemethod='linear'))
        fig.update_layout(height=390,yaxis=dict(range=[1,5],title='영역 문항평균'),showlegend=False,margin=dict(t=20,b=65))
        st.plotly_chart(fig,use_container_width=True)
        st.caption('상자그림은 중앙값·사분위 범위와 분포 폭을 보여줍니다. 평균이 같아도 응답의 퍼짐은 다를 수 있습니다. 점수의 높고 낮음을 진단등급으로 해석하지 않습니다.')
        st.download_button('소진 참고평균·분포 CSV',csv_bytes(rows),'burnout_reference_distribution.csv','text/csv')
    with dist_tab:
        rows=aggregate_items(valid)
        order=st.radio('문항 정렬',['설문순서','평균 높은 순','4~5점 응답률 높은 순'],horizontal=True,key='bat_item_sort')
        if order=='평균 높은 순': rows=sorted(rows,key=lambda r:(-r['평균'],r['설문순서']))
        if order=='4~5점 응답률 높은 순': rows=sorted(rows,key=lambda r:(-r['4~5점응답률(%)'],-r['평균'],r['설문순서']))
        labels=[f"{r['설문순서']}. {r['영역']}" for r in rows]
        fig=go.Figure(go.Bar(x=[r['평균'] for r in rows],y=labels,orientation='h',marker_color='#369566',
                            customdata=[[r['문항'],r['4~5점응답률(%)']] for r in rows],
                            hovertemplate='%{customdata[0]}<br>평균 %{x:.2f}<br>4~5점 응답률 %{customdata[1]}%<extra></extra>'))
        fig.update_layout(height=780,xaxis=dict(range=[0,5],title='문항평균'),yaxis=dict(autorange='reversed'),margin=dict(t=20,l=10,b=50))
        st.plotly_chart(fig,use_container_width=True)
        st.dataframe(rows,hide_index=True,use_container_width=True,column_config={'문항':st.column_config.TextColumn(width='large')})
        st.caption('4~5점 응답률의 분모는 해당 문항의 완전응답자 수입니다. 영역평균 4점 이상 비율 및 영역 전체 문항 응답분포와 구분합니다. 1점·5점 비율은 바닥·천장 집중을 점검하기 위한 기술통계입니다. 높은 응답 문항이 곧 위험을 예측하거나 개입 우선순위를 확정하지는 않습니다.')
        st.download_button('소진 22문항 집계 CSV',csv_bytes(rows),'burnout_item_summary.csv','text/csv')
    with item_tab:
        threshold=st.select_slider('동반 경험을 살펴볼 영역평균 조건',options=[3.,3.5,4.,4.5,5.],value=4.,key='bat_overlap_threshold')
        rows=overlap_counts(matrix,threshold)
        st.write(f'한 사람에게 영역평균 {threshold:.1f}점 이상이 몇 개 영역에서 함께 나타나는지 표시합니다.')
        fig=go.Figure(go.Bar(x=[str(r['조건충족영역수'])+'개 영역' for r in rows],y=[r['응답자수'] for r in rows],marker_color='#369566'))
        fig.update_layout(height=330,yaxis=dict(title='응답자 수',dtick=1),margin=dict(t=20,b=40))
        st.plotly_chart(fig,use_container_width=True);st.dataframe(rows,hide_index=True,use_container_width=True)
        co=(matrix>=threshold).astype(int)
        pair=co.T@co/n*100
        fig=go.Figure(go.Heatmap(z=pair,x=BAT_FACTORS,y=BAT_FACTORS,zmin=0,zmax=100,colorscale='YlGn',
                                colorbar=dict(title='%'),hovertemplate='%{y} · %{x}<br>동시 조건충족 %{z:.1f}%<extra></extra>'))
        fig.update_layout(height=420,margin=dict(t=20,l=10,b=80));st.plotly_chart(fig,use_container_width=True)
        st.caption('열지도의 비율은 전체 완전응답자 중 두 영역이 모두 조건을 충족한 비율이며, 대각선은 각 영역의 조건충족 비율입니다. 선택값은 사용자가 지정한 탐색 조건으로 검증된 임상 절단점이 아닙니다. 복합소진 유형·위험군으로 명명하지 않습니다.')
    with pattern_tab:
        if not items:
            st.info('감·수·성 문항 구성을 전달받지 못해 관련성 분석을 생략합니다.')
        elif n<20:
            st.info('탐색적 상관행렬은 소진 완전응답이 20명 이상인 경우 표시합니다. 이 최소치는 충분한 표본수나 타당성을 보장하지 않습니다.')
        else:
            try:
                from scipy.stats import rankdata
            except ImportError:
                st.info('상관행렬을 사용하려면 requirements.txt에 scipy를 추가하십시오.')
            else:
                joint=[]
                for r,s in valid:
                    try:
                        values=[]
                        for f in ['감','수','성']:
                            v=[float(r[f'Q{i}']) for i,ff,_,_ in items if ff==f]
                            if not v or not all(x in (1,2,3,4) for x in v): raise ValueError
                            values.append(float(np.mean(v)))
                        joint.append(values+[s[f] for f in BAT_FACTORS])
                    except (KeyError,TypeError,ValueError):
                        continue
                if len(joint)<20:
                    st.info('두 척도에 모두 완전응답한 자료가 20명 미만입니다.')
                else:
                    data=np.asarray(joint); labels=['감','수','성']+BAT_FACTORS
                    ranked=np.column_stack([rankdata(data[:,j]) for j in range(7)])
                    corr=np.full((7,7),np.nan)
                    usable=np.std(ranked,axis=0)>0
                    indices=np.flatnonzero(usable)
                    if len(indices)>1:
                        corr[np.ix_(indices,indices)]=np.corrcoef(ranked[:,indices],rowvar=False)
                    fig=go.Figure(go.Heatmap(z=corr,x=labels,y=labels,zmin=-1,zmax=1,zmid=0,colorscale='RdBu',
                                            colorbar=dict(title='ρ'),hovertemplate='%{y} · %{x}<br>Spearman ρ=%{z:.3f}<extra></extra>'))
                    fig.update_layout(height=520,margin=dict(t=20,l=10,b=100));st.plotly_chart(fig,use_container_width=True)
                    st.caption(f'공통 완전응답 {len(joint)}명의 Spearman 순위상관입니다. 상수 영역은 빈칸으로 표시합니다. 유의성 검정·인과 추론·교육효과 판정은 하지 않습니다. 감·수·성이 소진을 예방한다는 결론이나 소진이 낮으면 인권감수성이 높다는 판단의 근거로 사용할 수 없습니다.')
    with relation_tab:
        if n<20:
            st.info('영역별 내적일관성은 완전응답 20명 이상인 경우에만 참고로 표시합니다.')
        else:
            rows=[]
            for f in BAT_FACTORS:
                columns=[f'BAT{i}' for i,ff,_ in BAT_ITEMS if ff==f]
                values=np.array([[float(r[c]) for c in columns] for r,_ in valid])
                alpha=cronbach_alpha(values)
                rows.append({'영역':f,'문항수':len(columns),'응답수':n,'Cronbach α':round(alpha,3) if alpha is not None else None})
            st.dataframe(rows,hide_index=True,use_container_width=True)
            st.caption('α는 현재 표본의 내적일관성 참고 지표이며 구조타당도·단일차원성·개인 점수의 정확도를 보증하지 않습니다. 일정 기준으로 자동 합격/불합격 판정하지 않습니다. 음의 α는 문항 공분산·자료 입력을 점검해야 할 신호이며, 총점 분산이 0이면 미산출합니다. 이 화면은 CFA·ω·측정불변성 분석을 대체하지 않습니다.')
