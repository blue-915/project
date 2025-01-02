import streamlit as st
import pandas as pd
import random
import time

from utils import get_sequential_word, get_random_word, check_answer, save_incorrect_answers_to_drive, save_marked_words_to_drive, mark_word


@st.cache_data
def load_data(file_url):
    
    
    return pd.read_excel(file_url)

# GitHub에서 파일 URL
file_url = 'https://raw.githubusercontent.com/blue-915/project/a478d554ddf9ff9b522ef24432c5b8b3d2147de1/os/%EB%85%B8%EB%9E%AD%EC%9D%B4%20%EC%A0%84%EB%A9%B4%EA%B0%9C%EC%A0%95%ED%8C%90.xlsx'
data = load_data(file_url)


# 초기 세션 상태 설정
if "page" not in st.session_state:
    st.session_state.page = "Home"  # 초기 페이지는 "Home"

# 페이지 이동 함수
def go_to_page(page_name):
    st.session_state.page = page_name   

# 페이지별 내용
#홈페이지
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
    st.button("학습하기", on_click=lambda: go_to_page("Learn"))
    st.button("복습하기", on_click=lambda: go_to_page("S_Learn"))
    st.button("체크리스트", on_click=lambda: go_to_page("Mark"))

# 학습하기 페이지 (사지선다형)
def learn_page():
    st.title("학습하기")

    # 필터링된 데이터 가져오기
    if "filtered_data" not in st.session_state or st.session_state.filtered_data.empty:
        st.error("필터링된 데이터가 없습니다. 홈 화면에서 분류를 선택하세요.")
        return

    filtered_data = st.session_state.filtered_data

    # 처음에 순차적으로 단어를 선택하여 세션 상태에 저장
    if "current_word" not in st.session_state:
        current_word, correct_answer, options = get_sequential_word(filtered_data)
        st.session_state.current_word = current_word
        st.session_state.correct_answer = correct_answer
        st.session_state.options = options

    # 현재 단어와 선택지 표시
    current_word = st.session_state.current_word
    correct_answer = st.session_state.correct_answer
    options = st.session_state.options

    st.write(f"단어: **{current_word['Word']}**")

    # 정답 선택
    selected_option = st.radio("뜻을 선택하세요:", options)

    # 단어 마크 버튼
    is_marked = current_word["Word"] in st.session_state.marked_words
    mark_button_text = "마크 취소" if is_marked else "이 단어를 마크하기"
    
    if st.button(mark_button_text):
        marked = mark_word(current_word["Word"])  # 단어 마크 처리
        st.experimental_rerun()  # 페이지 새로 고침

    # 정답 확인 버튼
    if st.button("정답 확인"):
        check_answer(selected_option, correct_answer, filtered_data)

    # 오답을 구글 드라이브에 저장
    if st.button("오답 저장하기"):
        save_incorrect_answers_to_drive(filtered_data)

    # 마크된 단어들을 구글 드라이브에 저장
    if st.button("마크된 단어 저장하기"):
        save_marked_words_to_drive(filtered_data)

    # 학습 기록 업데이트
    st.write("### 학습 기록")
    st.write(st.session_state.records)

    # 버튼 UI
    st.button("랜덤 학습하기", on_click=lambda: go_to_page("R_learn"))
    st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))

# 랜덤 학습 페이지
def random_learn_page():
    st.title("랜덤 학습")
    
    if "filtered_data" not in st.session_state or st.session_state.filtered_data.empty:
        st.error("데이터가 없습니다. 홈 화면에서 분류를 선택하세요.")
        st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))
        return

    filtered_data = st.session_state.filtered_data
    
    # 랜덤 단어와 선택지 가져오기
    random_word, correct_answer, options = get_random_word(filtered_data)
    st.write(f"단어: **{random_word['Word']}**")

    # 정답 선택
    selected_option = st.radio("뜻을 선택하세요:", options)

    # 단어 마크 버튼
    is_marked = random_word["Word"] in st.session_state.marked_words
    mark_button_text = "마크 취소" if is_marked else "이 단어를 마크하기"
    
    if st.button(mark_button_text):
        marked = mark_word(random_word["Word"])  # 단어 마크 처리
        st.experimental_rerun()  # 페이지 새로 고침

    # 정답 확인 버튼
    if st.button("정답 확인"):
        check_answer(selected_option, correct_answer, filtered_data)

    # 오답을 구글 드라이브에 저장
    if st.button("오답 저장하기"):
        save_incorrect_answers_to_drive(filtered_data)

    # 마크된 단어들을 구글 드라이브에 저장
    if st.button("마크된 단어 저장하기"):
        save_marked_words_to_drive(filtered_data)

    # 학습 기록 업데이트
    st.write("### 학습 기록")
    st.write(st.session_state.records)

    # 버튼 UI
    st.button("다른 단어 학습하기", on_click=st.experimental_rerun)
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

    # 단어와 선택지 출력
    st.write(f"단어: **{current_word['Word']}**")
    
    # 마크된 단어인지 확인
    is_marked = current_word["Word"] in st.session_state.marked_words
    mark_button_text = "마크 취소" if is_marked else "마크하기"
    
    # 마크 버튼
    if st.button(mark_button_text):
        mark_word(current_word["Word"])  # 단어 마크
        st.experimental_rerun()  # 버튼 클릭 후 페이지 새로고침

    # 정답 선택
    selected_option = st.radio("정답을 선택하세요:", options)

    # 정답 확인 버튼
    if st.button("정답 확인"):
        check_answer_for_review(selected_option, correct_answer, incorrect_df, current_word)

    # 학습 기록 업데이트
    st.write("### 학습 기록")
    st.write(st.session_state.records)

    # 마크된 단어 목록
    st.write("### 마크된 단어 목록")
    st.write(st.session_state.marked_words)

    # 버튼 UI
    st.button("다음 단어로", on_click=next_word)
    st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))

    # 마크된 단어를 구글 드라이브에 저장
    if st.button("마크된 단어 저장"):
        save_marked_words_to_drive()  # 사용자가 마크된 단어를 저장하도록 처리


def next_word():
    # 현재 단어의 인덱스 증가
    st.session_state.current_index += 1
    if st.session_state.current_index >= len(st.session_state.filtered_data):
        st.session_state.current_index = 0  # 마지막 단어 후 첫 번째 단어로 돌아가기
    st.experimental_rerun()  # 페이지 새로 고침



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
    home_page(data)  # data 인자 추가
elif st.session_state.page == "Learn":
    learn_page()
elif st.session_state.page == "R_Learn":
    random_learn_page()
elif st.session_state.page == "S_Learn":
    review_page()
elif st.session_state.page == "Mark":
    review_checklist_page()

