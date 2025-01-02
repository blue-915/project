import streamlit as st
import pandas as pd
import random
import time

@st.cache_data
def load_data(file_url):
    return pd.read_excel(file_url)

# GitHub에서 파일 URL
file_url = 'https://github.com/blue-915/project/tree/1f73226fcc320523f87e5e1f3518b3799913891a/os/노랭이 전면개정판.xlsx'

# 데이터 로드
data = load_data(file_url)

# 데이터 표시
st.write(data)