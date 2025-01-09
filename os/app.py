import streamlit as st
import pandas as pd
import random
import time

from utils import (
    get_sequential_word,
    check_answer,
    move_to_next_word,
    update_word_and_options,
    get_credentials_from_secret_manager,
    find_file_in_drive,
    download_file_from_drive,
    load_incorrect_words_from_drive,
    save_to_drive,
    save_incorrect_answers_to_drive,
    save_marked_words_to_drive,
    mark_word
)


# 세션 상태 초기화
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "marked_words" not in st.session_state:
    st.session_state.marked_words = []
if "records" not in st.session_state:
    st.session_state.records = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0
if "known_words" not in st.session_state:
    st.session_state.known_words = []
if "unknown_words" not in st.session_state:  
    st.session_state.unknown_words = []
if "filtered_data" not in st.session_state:
    st.session_state.filtered_data = pd.DataFrame()



@st.cache_data
def load_data(file_url):
    return pd.read_excel(file_url)

# GitHub에서 파일 URL
file_url = 'https://raw.githubusercontent.com/blue-915/project/a478d554ddf9ff9b522ef24432c5b8b3d2147de1/os/%EB%85%B8%EB%9E%AD%EC%9D%B4%20%EC%A0%84%EB%A9%B4%EA%B0%9C%EC%A0%95%ED%8C%90.xlsx'
data = load_data(file_url)

# 페이지 이동 함수
def go_to_page(page_name):
    st.session_state.page = page_name
    
# 구글 드라이브 API 인증
def load_google_credentials(secret_name):
    credentials_json = get_credentials_from_secret_manager()  # Get the credentials
    st.write("Google Credentials Loaded Successfully")
    return credentials_json

def main():
    # 구글 인증 정보 로드
    credentials_json = load_google_credentials("project")

    # Your remaining app code...
    st.write("Google Credentials Loaded Successfully")


# 페이지별 내용
# 홈 페이지
def home_page(data):
    st.title("단어 암기 프로그램")
    
    # 데이터가 비어 있는지 확인
    if data.empty:
        st.error("데이터가 없습니다. 데이터를 확인하세요.")
        return

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
    st.button("학습모드", on_click=lambda: go_to_page("Learn"))
    st.button("복습모드", on_click=lambda: go_to_page("S_Learn"))
    st.button("체크리스트", on_click=lambda: go_to_page("Mark"))

def learn_page():
    st.title("학습하기")
    filtered_data = st.session_state.filtered_data
    if filtered_data.empty:
        st.error("필터링된 데이터가 없습니다.")
        return

    # 현재 단어와 선택지 로드
    current_index = st.session_state.current_index
    current_word = filtered_data.iloc[current_index]

    # 보기 초기화
    if "options" not in st.session_state or st.session_state.options is None:
        update_word_and_options(filtered_data)  # 단어와 선택지 초기화
        st.session_state.correct_answer = st.session_state.correct_answer
        st.session_state.options = st.session_state.options

    st.write(f"단어: **{current_word['Word']}**")

    # 보기 선택
    selected_option = st.radio("뜻을 선택하세요:", st.session_state.options, key="options_radio")

    # 정답 확인 버튼
    if st.button("정답 확인", key="check_answer"):
        check_answer(selected_option, st.session_state.correct_answer, filtered_data)
        st.session_state.show_next_button = True  # 다음 단어로 버튼 표시 플래그 설정

    # '다음 단어로' 버튼
    if st.session_state.get("show_next_button", False):
        if st.button("다음 단어로", key="next_word"):
            move_to_next_word(filtered_data)  # 인덱스만 갱신
            update_word_and_options(filtered_data)  # 단어와 보기 선택지 갱신
            st.session_state.show_next_button = False  # 다음 단어 버튼 숨기기

    # 단어 마크
    is_marked = current_word["Word"] in st.session_state.marked_words
    if st.button("이 단어를 마크하기" if not is_marked else "마크 취소", key="mark_word"):
        mark_word(current_word["Word"])



    # 학습 기록 업데이트
    st.write("### 학습 기록")
    st.write(st.session_state.records)

    st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))

def review_page():
    st.title("오답 복습")

    # 오답 데이터를 구글 드라이브에서 불러오기
    incorrect_df = load_incorrect_words_from_drive()

    if incorrect_df.empty:
        st.write("현재 복습할 오답 단어가 없습니다.")
        return

    # 현재 복습할 단어 가져오기
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0  # 첫 번째 단어부터 시작

    current_index = st.session_state.current_index
    current_word, correct_answer, options = get_review_word(incorrect_df, current_index)

    # 보기 초기화
    if "options" not in st.session_state or st.session_state.options is None:
        update_word_and_options(filtered_data)  # 단어와 선택지 초기화
        st.session_state.correct_answer = st.session_state.correct_answer
        st.session_state.options = st.session_state.options

    st.write(f"단어: **{current_word['Word']}**")
    # 보기 선택
    selected_option = st.radio("뜻을 선택하세요:", st.session_state.options, key="options_radio")

    # 정답 확인 버튼
    if st.button("정답 확인", key="check_answer"):
        check_answer_for_review(selected_option, correct_answer, incorrect_df, current_word)
        st.session_state.show_next_button = True  # 다음 단어로 버튼 표시 플래그 설정

    # '다음 단어로' 버튼
    if st.session_state.get("show_next_button", False):
        if st.button("다음 단어로", key="next_word"):
            move_to_next_word(filtered_data)  # 인덱스만 갱신
            update_word_and_options(filtered_data)  # 단어와 보기 선택지 갱신
            st.session_state.show_next_button = False  # 다음 단어 버튼 숨기기

    # 학습 기록 업데이트
    st.write("### 학습 기록")
    st.write(st.session_state.records)

    # 버튼 UI
    st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))


def review_checklist_page():
    st.title("복습용 체크리스트")

    # 마크된 단어가 없으면 안내 메시지 표시
    if "marked_words" not in st.session_state or not st.session_state.marked_words:
        st.write("마크된 단어가 없습니다.")
        return

    st.write("### 복습용 마크된 단어 목록")
    
    # 체크리스트 형식으로 마크된 단어 표시
    selected_words = []
    for word in st.session_state.marked_words:
        if st.checkbox(f"{word}", key=word):  # 단어별로 체크박스 생성
            selected_words.append(word)  # 체크된 단어를 리스트에 추가
    
    # 선택된 단어들이 있을 경우 선택한 단어 목록 출력
    if selected_words:
        st.write("선택한 단어들:")
        for word in selected_words:
            st.write(f"- {word}")
    
    # 체크된 단어가 없으면 안내 메시지 표시
    if not selected_words:
        st.write("체크박스를 선택해주세요.")

    # 홈 페이지로 이동 버튼
    st.button("홈 페이지로 이동", on_click=lambda: go_to_page("Home"))


# 현재 페이지에 따라 다른 화면 표시
if st.session_state.page == "Home":
    home_page(data)
elif st.session_state.page == "Learn":
    learn_page()
elif st.session_state.page == "S_Learn":
    review_page()
elif st.session_state.page == "Mark":
    review_checklist_page()
