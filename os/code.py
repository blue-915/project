import streamlit as st
import pandas as pd
import random
import time

# 엑셀 데이터 로드 함수

@st.cache_data
def load_data(file):
    return pd.read_excel(file)

# 초기 세션 상태 설정
if "page" not in st.session_state:
    st.session_state.page = "Home"  # 초기 페이지는 "Home"

# 페이지 이동 함수
def go_to_page(page_name):
    st.session_state.page = page_name

# 페이지별 내용
#홈페이지
def home_page():
    st.title("단어 암기 프로그램")
    st.write("엑셀 파일을 업로드하거나 기본 데이터를 사용해 학습을 시작하세요.")
    uploaded_file = st.file_uploader("엑셀 파일을 업로드하세요", type=["xlsx", "xls"])
    
    # 데이터 업로드 여부
    if uploaded_file:
        st.session_state.data = load_data(uploaded_file)
        st.success("단어 학습을 시작합니다.")
    else:
        st.session_state.data = pd.DataFrame({
            "Day": [1, 1, 2],
            "Word": ["Apple", "Run", "Happy"],
            "Meaning": ["사과", "달리다", "행복한"],
        })
    st.write("### 데이터 미리 보기")
    st.dataframe(st.session_state.data)
    
    # 버튼
    buttons = [
        ("분류 학습 페이지로 이동", "C_Learn"),
        ("랜덤 학습 페이지로 이동", "R_Learn"),
        ("자동 학습 페이지로 이동", "A_Learn")
    ]

    # 버튼 클릭 시 동작
    for label, page in buttons:
        if st.button(label):
            go_to_page(page) 
            if uploaded_file is None:
                st.warning("파일을 업로드 하지 않았습니다. 기본 단어로 학습을 시작합니다.")
                go_to_page(page)       


# 초기 세션 상태 설정
if "known_words" not in st.session_state:
    st.session_state.known_words = []
if "unknown_words" not in st.session_state:
    st.session_state.unknown_words = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "records" not in st.session_state:
    st.session_state.records = []

# 분류별 학습 페이지
#홈페이지
def category_learn_page():
    st.title("분류별 학습")
    if "data" not in st.session_state or st.session_state.data.empty:
        st.error("데이터가 없습니다. 홈 화면에서 엑셀 파일을 업로드하세요.")
        st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))
        return
    
    data = st.session_state.data
    st.write(data.columns)  # 현재 데이터의 컬럼 이름을 출력하여 확인

    # 분류 선택
    if "Day" in data.columns:
        categories = st.multiselect("분류를 선택하세요 (Day):", data["Day"].unique())
        filtered_data = data[data["Day"].isin(categories)] if categories else data
    else:
        st.warning("'Day' 열이 없어 전체 데이터를 사용합니다.")
        filtered_data = data
        
    if filtered_data.empty:
        st.warning("선택된 분류에 해당하는 데이터가 없습니다.")
        return

    st.session_state.filtered_data = filtered_data
    st.button("학습 시작", on_click=lambda: go_to_page("C_start"))
    
# 분류 학습 시작 페이지
def category_learn_start_page():
    if "filtered_data" not in st.session_state or st.session_state.filtered_data.empty:
        st.error("데이터가 없습니다. 분류를 선택한 후 학습을 시작하세요.")
        st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))
        return

    filtered_data = st.session_state.filtered_data
    current_index = st.session_state.get('current_index', 0)  # 인덱스 값 기본값 설정
    current_word = filtered_data.iloc[current_index % len(filtered_data)]

    if "Word" not in current_word:
        st.error("단어 정보가 없습니다. 데이터가 잘못된 형식일 수 있습니다.")
        return

    st.write(f"단어: **{current_word['Word']}**")

    user_input = st.text_input("뜻을 입력하세요:")


    if st.button("정답 확인"):
        if user_input.strip() == current_word["Meaning"]:
            st.success("정답입니다!")
            st.session_state.known_words.append(current_word["Word"])
            st.session_state.records.append({"Word": current_word["Word"], "Result": "Correct"})
        else:
            st.error(f"오답입니다! 정답은: {current_word['Meaning']}")
            st.session_state.unknown_words.append(current_word["Word"])
            st.session_state.records.append({"Word": current_word["Word"], "Result": "Incorrect"})
        
        # 다음 단어 버튼
        if st.button("다음 단어로"):
            st.session_state.current_index += 1
            st.experimental_rerun()

        # 페이지 이동 버튼
        st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))


# 학습 기록 저장 버튼
def save_records():
    if st.session_state.records:
        records_df = pd.DataFrame(st.session_state.records)
        records_df.to_csv("study_records.csv", index=False)
        st.success("학습 기록이 'study_records.csv'로 저장되었습니다.")
    else:
        st.warning("저장할 학습 기록이 없습니다.")
        
def select_category_learn_page(data):
    st.title("분류 선택")
    if "Day" in data.columns:
        categories = st.multiselect("분류를 선택하세요 (Day):", data["Day"].unique())
        if st.button("선택 완료"):
            st.session_state.selected_data = data[data["Day"].isin(categories)]
            st.success(f"{len(st.session_state.selected_data)}개의 단어가 선택되었습니다!")
            st.button("학습 페이지로 이동", on_click=lambda: go_to_page("Learn"))
    else:
        st.error("'Day' 열이 없어 분류를 선택할 수 없습니다.")
        st.session_state.selected_data = data

def selected_category_learn_page():
    st.title("학습 페이지")
    if "selected_data" not in st.session_state or st.session_state.selected_data.empty:
        st.error("선택된 데이터가 없습니다. 분류 선택 페이지로 이동하세요.")
        st.button("분류 선택으로 이동", on_click=lambda: go_to_page("Category"))
        return

    selected_data = st.session_state.selected_data
    random_word = selected_data.sample(1).iloc[0]
    st.write(f"단어: **{random_word['Word']}**")
    user_input = st.text_input("뜻을 입력하세요:")

    if st.button("정답 확인"):
        if user_input.strip() == random_word["Meaning"]:
            st.success("정답입니다!")
        else:
            st.error(f"오답입니다! 정답은: {random_word['Meaning']}")



def random_learn_page():
    st.title("랜덤 단어 학습")
    if "data" not in st.session_state or st.session_state.data.empty:
        st.error("데이터가 없습니다. 홈 화면에서 엑셀 파일을 업로드하세요.")
        st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))
        return

    data = st.session_state.data
    random_word = data.sample(1).iloc[0]
    st.write(f"단어: **{random_word['Word']}**")
    user_input = st.text_input("뜻을 입력하세요:")

    if user_input:
        if user_input.strip() == random_word["Meaning"]:
            st.success("정답입니다!")
        else:
            st.error(f"오답입니다! 정답은: {random_word['Meaning']}")

    st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))
    st.button("자동 학습 페이지로 이동", on_click=lambda: go_to_page("Auto Learn"))

def auto_learn_page():
    st.title("자동 학습")
    if "data" not in st.session_state or st.session_state.data.empty:
        st.error("데이터가 없습니다. 홈 화면에서 엑셀 파일을 업로드하세요.")
        st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))
        return

    data = st.session_state.data
    delay = st.slider("단어와 뜻을 표시할 시간(초):", min_value=1, max_value=10, value=5)

    if st.button("자동 학습 시작"):
        for _, row in data.iterrows():
            st.write(f"단어: **{row['Word']}**")
            time.sleep(delay // 2)
            st.write(f"뜻: {row['Meaning']}")
            time.sleep(delay // 2)

    st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))
    st.button("학습 페이지로 이동", on_click=lambda: go_to_page("Learn"))
    

        



# 현재 페이지에 따라 다른 화면 표시
if st.session_state.page == "Home":
    home_page()
elif st.session_state.page == "C_Learn":
    category_learn_page()
elif st.session_state.page == "C_start":
    category_learn_start_page()
elif st.session_state.page == "select_C":
    select_category_learn_page()
elif st.session_state.page == "s_l_category":
    selected_category_learn_page()
elif st.session_state.page == "R_Learn":
    random_learn_page()
elif st.session_state.page == "A_Learn":
    auto_learn_page()
    
