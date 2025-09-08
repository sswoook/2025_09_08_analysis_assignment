import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
# import koreanize_matplotlib
import matplotlib.font_manager as fm
import os
import requests

@st.cache_data
def download_and_setup_font():
    font_url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
    font_path = "NanumGothic.ttf"
    
    # 폰트 파일 다운로드 (한 번만)
    if not os.path.exists(font_path):
        response = requests.get(font_url)
        with open(font_path, 'wb') as f:
            f.write(response.content)
    
    # matplotlib에 폰트 추가
    fm.fontManager.addfont(font_path)
    plt.rcParams['font.family'] = 'NanumGothic'
    plt.rcParams['axes.unicode_minus'] = False
    
    return "나눔고딕 설정 완료"
# font 설정 함수 호출
font_status = download_and_setup_font()

st.set_page_config(page_title="퇴직율 대시보드", layout="wide")

# 데이터 들고오기 및 전처리
@st.cache_data
def load_df(path:str ="HR Data.csv") -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8")
        df["퇴직"] = df["퇴직여부"].map({"Yes":1, "No":0}).astype("int8")
        df.drop(['직원수', '18세이상'], axis=1, inplace=True, errors='ignore')
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()
    return df

df = load_df()

if df.empty:
    st.error("데이터가 없습니다. 'HR Data.csv' 파일을 확인하세요.")
    st.stop()  



# 1) 헤더 & KPI
st.title("퇴직율 분석 및 인사이트")
n = len(df); quit_n = int(df["퇴직"].sum())
quit_rate = df["퇴직"].mean()*100
stay_rate = 100 - quit_rate
k1,k2 = st.columns(2)
k3,k4 = st.columns(2)
k1.metric("전체 직원 수", f"{n:,}명", border=True)
k2.metric("퇴직자 수", f"{quit_n:,}명", border=True)
k3.metric("유지율", f"{stay_rate:.1f}%", border=True)
k4.metric("퇴직율", f"{quit_rate:.1f}%", border=True)

# 다운로드 버튼
st.download_button("HR Data CSV",
                    df.to_csv(index=False).encode('utf-8'), 
                    "HR Data.csv",
                    key='download-csv',
                    icon=':material/download:',
                    width="stretch") 

# 스톡옵션정도별 퇴직율
if '스톡옵션정도' in df.columns:
    # 결측치 처리 및 타입 변환
    df['스톡옵션정도'] = df['스톡옵션정도'].fillna(0).astype('int8')
    
    # 스톡옵션정도별 퇴직 여부 카운트 피벗 테이블 생성
    stock_option_pivot = df.pivot_table(index='스톡옵션정도', columns='퇴직', values='직원ID', aggfunc='count').fillna(0)
    
    # 퇴직율 계산 (퇴직=1 비율)
    stock_option_pivot['퇴직율(%)'] = (stock_option_pivot.get(1, 0) / stock_option_pivot.sum(axis=1)) * 100
    
    # 시각화
    fig, ax = plt.subplots(figsize=(7.5, 3.8))
    colors = sns.color_palette("coolwarm", len(stock_option_pivot))

    ax.plot(stock_option_pivot.index, stock_option_pivot['퇴직율(%)'], marker='o', linestyle='-', linewidth=2, markersize=8, color=colors[2])
    for i, val in enumerate(stock_option_pivot['퇴직율(%)']):
        ax.text(i, val + 0.3, f"{val:.1f}%", ha='center', va='bottom', fontsize=10, color=colors[2])

    ax.set_xlabel("스톡옵션정도")
    ax.set_ylabel("퇴직율(%)")
    ax.set_title("스톡옵션정도별 퇴직율 (선 그래프)")
    ax.grid(True, linestyle='--', alpha=0.7)

plt.xticks(rotation=0)
st.pyplot(fig)

col1, col2 = st.columns(2)

# (좌) 급여인상율과 퇴직율 (정수%로 라운딩 후 라인)
if "급여증가분백분율" in df.columns:
    tmp = df[["급여증가분백분율","퇴직"]].dropna().copy()
    tmp["인상률(%)"] = tmp["급여증가분백분율"].round().astype(int)
    sal = tmp.groupby("인상률(%)")["퇴직"].mean()*100
    with col1:
        st.subheader(":up: 급여인상률별 퇴직율")
        fig, ax = plt.subplots(figsize=(6.5, 3.5))

        ax.plot(sal.index, sal.values, marker='o', linestyle='-', linewidth=2, markersize=8, color='mediumseagreen')
        ax.fill_between(sal.index, 0, sal.values, color='mediumseagreen', alpha=0.3)

        for i, val in enumerate(sal.values):
            ax.text(sal.index[i], val + 0.2, f"{val:.1f}%", ha='center', va='bottom', fontsize=9, color='mediumseagreen')

        ax.set_xlabel("급여인상율(%)")
        ax.set_ylabel("퇴직율(%)")
        ax.set_title("급여인상율과 퇴직율 (영역 강조 선 그래프)")
        ax.grid(True, linestyle='--', alpha=0.6)

        plt.xticks(rotation=0)
        st.pyplot(fig)


# (우) 야근정도별 퇴직율 (Yes/No 막대)
col_name = "야근정도"
if col_name in df.columns:
    ot = (df.groupby(col_name)["퇴직"].mean()*100)
    with col2:
        st.subheader("⏰ 야근정도별 퇴직율")
        fig3, ax3 = plt.subplots(figsize=(6.5,3.5))
        sns.barplot(x=ot.index, y=ot.values, ax=ax3)
        ax3.set_ylabel("퇴직율(%)"); 
        ax3.bar_label(ax3.containers[0], fmt="%.1f")
        st.pyplot(fig3)
