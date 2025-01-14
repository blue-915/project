import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# 학습 진행 데이터 로드
if "records" not in st.session_state:
    st.session_state.records = []

# 학습 기록 요약 및 시각화 함수
def show_progress_summary():
    """진도별 상황을 요약 및 시각화하는 함수"""

    # 학습 기록이 없을 경우 메시지 표시
    if not st.session_state.records:
        st.warning("아직 학습 기록이 없습니다.")
        return

    # 학습 데이터를 DataFrame으로 변환
    records_df = pd.DataFrame(st.session_state.records)

    # 전체 진도율 계산
    total_attempts = len(records_df)
    correct_attempts = len(records_df[records_df["Result"] == "Correct"])
    overall_progress = round((correct_attempts / total_attempts) * 100, 2)

    # 전체 진도율 출력
    st.subheader("📊 전체 진도율")
    st.metric(label="진도율", value=f"{overall_progress}%")

    # Day별 진도율 계산
    if "Day" in records_df.columns:
        day_progress = records_df.groupby("Day")["Result"].apply(
            lambda x: (x == "Correct").sum() / len(x) * 100
        )

        # Day별 진도율 시각화
        st.subheader("📈 Day별 진도율")
        fig = px.bar(
            day_progress,
            x=day_progress.index,
            y=day_progress.values,
            labels={"x": "Day", "y": "진도율 (%)"},
            title="Day별 진도율",
            color=day_progress.values,
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig)
    else:
        st.warning("Day별 데이터가 없습니다.")

    # 최근 학습 기록 표시
    st.subheader("📝 최근 학습 기록")
    st.write(records_df.tail(10))

# Streamlit UI 구성
st.title("진도별 상황 대시보드")

# 진도별 상황 요약 호출
show_progress_summary()
