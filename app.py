import streamlit as st
import pandas as pd
import random
import time
from google.cloud import storage

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'utils')))


from utils.common_utils import ( initialize_session,
                                    load_data,
                                    handle_page_navigation,
                                    get_credentials_from_secret_manager,
                                    load_google_credentials,
                                    save_to_gcs,
                                    find_file_in_gcs,
                                    initialize_gcs_client,
)

from utils.learning_utils import (save_to_gcs, 
                                  find_file_in_gcs, 
                                  save_incorrect_answers_to_gcs, 
                                  save_or_remove_marked_words, 
                                  delete_from_gcs, 
                                  toggle_mark_word, 
                                  initialize_marked_words_state, 
                                  add_word_to_marked_list, 
                                  remove_word_from_marked_list, 
                                  check_answer, 
                                  move_to_next_word, 
                                  update_word_and_options, 
                                  get_sequential_word
    
)
from utils.review_utils import ( initialize_session, handle_page_navigation, 
                                get_credentials_from_secret_manager, load_google_credentials, 
                                load_incorrect_words_from_gcs, get_current_word, get_options, 
                                check_answer_and_update, process_and_save_incorrect_answers, 
                                verify_answer, 
                                remove_correct_word_from_df, save_incorrect_df_to_gcs, 
                                show_incorrect_message
)
from utils.checklist_utils import ( load_marked_words_from_gcs,
                                    delete_marked_word_from_gcs,    
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
    

# GCS 인증
def load_google_credentials(secret_name):
    """구글 클라우드 저장소(GCS) 인증을 위한 함수"""
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/app/service-account-file.json")
    
    if not credentials_path:
        st.error("Google Credentials 경로가 설정되지 않았습니다.")
        return None
    
    # 서비스 계정 인증을 가져옵니다.
    credentials = storage.Client.from_service_account_json(credentials_path)
    st.write("Google Cloud Storage Credentials Loaded Successfully")
    return credentials

def main():
    # 구글 클라우드 저장소 인증 정보 로드
    credentials_json = load_google_credentials("project")

    # Your remaining app code...
    st.write("Google Cloud Storage Credentials Loaded Successfully")

    # Example: List the available buckets
    if credentials_json:
        storage_client = credentials_json
        buckets = storage_client.list_buckets()
        for bucket in buckets:
            st.write(bucket.name)


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
        # 정답 확인
        check_answer(selected_option, st.session_state.correct_answer, filtered_data)
        # 오답 처리 및 저장 함수 호출 (GCS에 오답 저장)
        save_incorrect_answers_to_gcs(filtered_data, "your-bucket-name")  # GCS 버킷 이름 추가
        # 다음 단어로 버튼 활성화
        st.session_state.show_next_button = True
         
    # '다음 단어로' 버튼
    if st.session_state.get("show_next_button", False):
        if st.button("다음 단어로", key="next_word"):
            move_to_next_word(filtered_data)  # 인덱스만 갱신
            update_word_and_options(filtered_data)  # 단어와 보기 선택지 갱신
            st.session_state.show_next_button = False  # 다음 단어 버튼 숨기기

    # 단어 마크
    is_marked = current_word["Word"] in st.session_state.get("marked_words", [])
    if st.button("이 단어를 마크하기" if not is_marked else "마크 취소", key="mark_word"):
        toggle_mark_word(current_word["Word"], current_word, "your-bucket-name")  # GCS 버킷 이름 추가

    # 학습 기록 업데이트
    st.write("### 학습 기록")
    st.write(st.session_state.records)

    st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))


def review_page():
    st.title("오답 복습")

    # Google Cloud Storage 서비스 객체 생성
    try:
        storage_client = initialize_gcs_client()  # 기존 호출 함수 사용
    except Exception as e:
        st.error(f"Google Cloud Storage 초기화 실패: {e}")
        return

    # incorrect_df 초기화
    if "incorrect_df" not in st.session_state:
        # GCS에서 오답 데이터를 로드하는 기존 호출 함수 사용
        st.session_state.incorrect_df = load_incorrect_words_from_gcs("your-bucket-name")  # GCS 버킷 이름 전달
        st.write("### Debug: incorrect_df 초기화 완료")
        st.write(st.session_state.incorrect_df)

    # 데이터가 비어 있는 경우 처리
    if st.session_state.incorrect_df.empty:
        st.write("현재 복습할 오답 단어가 없습니다.")
        st.button("홈으로 이동", on_click=lambda: go_to_page("Home"))
        return

    # 필터링된 데이터 확인
    if "filtered_data" not in st.session_state or st.session_state.filtered_data.empty:
        st.error("필터링된 데이터가 없습니다. 홈 화면으로 돌아가세요.")
        return

    filtered_data = st.session_state.filtered_data

    # 세션 상태 초기화
    if "current_word_index" not in st.session_state:
        st.session_state.current_word_index = 0  # 초기 인덱스 설정
    if "current_word" not in st.session_state:
        st.session_state.current_word = None  # 현재 단어 초기화
    if "correct_answer" not in st.session_state:
        st.session_state.correct_answer = None  # 정답 초기화
    if "options" not in st.session_state:
        st.session_state.options = []  # 보기 선택지 초기화
    if "show_next_button" not in st.session_state:
        st.session_state.show_next_button = False  # 다음 단어 버튼 초기화

    # 현재 복습 단어 가져오기
    if st.session_state.current_word is None:
        st.session_state.current_word, st.session_state.correct_answer = get_current_word(
            st.session_state.incorrect_df, st.session_state.current_word_index
        )
        st.session_state.options = get_options(filtered_data, st.session_state.correct_answer)

    # 현재 단어와 보기 출력
    st.write(f"단어: **{st.session_state.current_word['Word']}**")
    selected_option = st.radio("뜻을 선택하세요:", st.session_state.options, key="options_radio")

    # 정답 확인 버튼
    if st.button("정답 확인"):
        if selected_option == st.session_state.correct_answer:
            st.success("정답입니다!")
            # 삭제된 데이터 반영
            st.session_state.incorrect_df = st.session_state.incorrect_df[
                st.session_state.incorrect_df["Word"] != st.session_state.current_word["Word"]
            ]
            st.write("### Debug: 정답 확인 후 incorrect_df 상태")
            st.write(st.session_state.incorrect_df)
            # GCS에 오답 데이터를 저장하는 기존 호출 함수 사용
            save_incorrect_df_to_gcs(st.session_state.incorrect_df, "your-bucket-name")  # GCS 버킷 이름 전달
        else:
            st.error(f"오답입니다! 정답은: {st.session_state.correct_answer}")

    # 다음 단어로 버튼
    if st.button("다음 단어로"):
        if not st.session_state.incorrect_df.empty:
            st.session_state.current_word_index += 1
            if st.session_state.current_word_index >= len(st.session_state.incorrect_df):
                st.session_state.current_word_index = 0
                st.warning("모든 단어를 학습했습니다. 다시 처음부터 시작합니다.")

            st.session_state.current_word, st.session_state.correct_answer = get_current_word(
                st.session_state.incorrect_df, st.session_state.current_word_index
            )
            st.session_state.options = get_options(filtered_data, st.session_state.correct_answer)
            st.write("### Debug: 다음 단어로 버튼 클릭 후 상태")
            st.write({"current_word": st.session_state.current_word, "correct_answer": st.session_state.correct_answer})
            st.write(st.session_state.options)
        else:
            st.write("마지막 단어입니다.")

    # 디버깅: 현재 저장된 오답 데이터프레임 출력
    st.write("### Debug: 현재 저장된 오답 데이터프레임")
    st.write(st.session_state.incorrect_df)

    # 홈 페이지로 이동 버튼
    st.button("홈 페이지로 이동", on_click=lambda: go_to_page("Home"))


        
def review_checklist_page():
    st.title("복습용 체크리스트")

    # 마크된 단어 불러오기
    if "marked_words_df" not in st.session_state:
        # GCS에서 마크된 단어를 불러오는 함수 호출 (기존 호출 함수 활용)
        st.session_state.marked_words_df = load_marked_words_from_gcs("your-bucket-name")  # GCS 버킷 이름 전달
    
    marked_df = st.session_state.marked_words_df

    if marked_df.empty:
        st.write("마크된 단어가 없습니다.")
        return

    # Day 선택
    days = marked_df["Day"].unique()
    selected_day = st.selectbox("Day 선택:", days)

    # 선택한 Day에 해당하는 단어 필터링
    filtered_data = marked_df[marked_df["Day"] == selected_day]

    if filtered_data.empty:
        st.write(f"{selected_day}에 해당하는 마크된 단어가 없습니다.")
        return

    # 체크리스트 생성
    checked_words = []  # 선택된 단어 저장
    for idx, row in filtered_data.iterrows():
        col1, col2, col3 = st.columns([1, 4, 1])
        with col1:
            checked = st.checkbox("", key=f"check_{idx}")
            if checked:
                checked_words.append(row["Word"])
        with col2:
            st.write(f"{row['Word']} - {row['Meaning']}")
        with col3:
            if st.button("삭제", key=f"delete_{idx}"):
                # GCS에서 단어 삭제하는 함수 호출 (기존 호출 함수 활용)
                st.session_state.marked_words_df = delete_marked_word_from_gcs(row["Word"], marked_df, "your-bucket-name")
                st.experimental_set_query_params()  # URL 매개변수 초기화로 페이지 갱신

    # 디버깅: 선택된 단어 상태
    st.write("### Debug: 선택된 단어")
    st.write(checked_words)

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
