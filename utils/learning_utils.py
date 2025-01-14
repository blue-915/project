import os
import random
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import streamlit as st

from utils.common_utils import (initialize_session,
                                handle_page_navigation,
                                get_credentials_from_secret_manager,
                                load_google_credentials,
                                save_to_drive,
                                find_file_in_drive)


def get_sequential_word(filtered_data):
    """순차적으로 단어와 정답을 반환하는 함수"""
    current_index = st.session_state.current_index
    current_word = filtered_data.iloc[current_index]
    correct_answer = current_word['Meaning']

    options = filtered_data['Meaning'].sample(4).tolist()
    if correct_answer not in options:
        options[0] = correct_answer
    random.shuffle(options)

    return current_word, correct_answer, options

def check_answer(user_input, correct_answer, filtered_data):
    current_word = filtered_data.iloc[st.session_state.current_index]

    if user_input == correct_answer:
        st.success("정답입니다!")
        st.session_state.records.append({
            "Word": current_word["Word"],
            "Result": "Correct"
        })
    else:
        st.error(f"오답입니다! 정답은: {correct_answer}")
        st.session_state.records.append({
            "Word": current_word["Word"],
            "Result": "Incorrect"
        })


def move_to_next_word(filtered_data):
    """다음 단어로 이동하는 함수"""
    st.session_state.current_index += 1
    if st.session_state.current_index >= len(filtered_data):
        st.session_state.current_index = 0
        st.warning("모든 단어를 학습했습니다. 다시 처음부터 시작합니다.")

def update_word_and_options(filtered_data):
    """단어와 보기 선택지를 갱신하는 함수"""
    current_word, correct_answer, options = get_sequential_word(filtered_data)
    st.session_state.current_word = current_word
    st.session_state.correct_answer = correct_answer
    st.session_state.options = options

from datetime import datetime
import pandas as pd

def process_and_save_incorrect_answers(selected_option, correct_answer, current_word):
    """
    오답 단어를 처리하고 구글 드라이브에 저장하는 함수.
    
    Parameters:
        selected_option (str): 사용자가 선택한 답안.
        correct_answer (str): 현재 문제의 정답.
        current_word (dict): 현재 문제의 단어 정보.
    """
    # 정답 여부 확인
    if selected_option != correct_answer:
        # 오답 데이터 생성
        incorrect_entry = {
            "Day": current_word.get("Day", "Unspecified"),  # Day 정보
            "Word": current_word["Word"],                  # 단어
            "Meaning": current_word.get("Meaning", "No meaning provided"),  # 뜻
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # 저장된 날짜
        }

        # 세션 상태에 오답 데이터 누적
        if "unknown_words" not in st.session_state:
            st.session_state.unknown_words = []  # 초기화
        st.session_state.unknown_words.append(incorrect_entry)

        # 누적된 오답 데이터를 데이터프레임으로 변환
        incorrect_df = pd.DataFrame(st.session_state.unknown_words)

        # 구글 드라이브에 저장
        save_incorrect_answers_to_drive(incorrect_df)

        # 디버깅용 출력
        st.write("현재 저장된 오답 데이터프레임:")
        st.write(incorrect_df)

    else:
        st.write("정답입니다! 저장된 오답 데이터는 변경되지 않았습니다.")


from datetime import datetime

def save_incorrect_answers_to_drive(filtered_data): # 오답 데이터를 구글 드라이브에 저장
    
    # 디버깅용 출력
    st.write("현재 filtered_data:")
    st.write(filtered_data)
    st.write("현재 records:")
    st.write(st.session_state.records)

    # 'Incorrect' 상태인 단어만 필터링
    incorrect_words = [record['Word'] for record in st.session_state.records if record['Result'] == 'Incorrect']
    st.write(f"오답 단어 목록: {incorrect_words}")  # 디버깅용 출력
    
    # 오답 단어를 포함하는 데이터프레임 필터링
    incorrect_df = filtered_data[filtered_data["Word"].isin(incorrect_words)]

    if incorrect_df.empty:
        st.warning("오답 데이터가 없습니다. 저장을 건너뜁니다.")
        return

    # 데이터프레임 컬럼 구성 (Day, Word, Meaning, Date)
    incorrect_df = incorrect_df.copy()  # 경고 방지
    incorrect_df["Day"] = incorrect_df.get("Day", "Unspecified")  # Day 컬럼 추가 (없을 경우 기본값)
    incorrect_df["Meaning"] = incorrect_df.get("Meaning", "No meaning provided")  # Meaning 컬럼 추가
    incorrect_df["Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Date 추가

    # 디버깅 출력
    st.write("최종 저장 데이터프레임:")
    st.write(incorrect_df)

    # 저장
    if save_to_drive(incorrect_df, "incorrect_words.csv"):
        st.success("단어가 구글드라이브에 저장되었습니다.")

def toggle_mark_word(word, current_word):

    # 세션 상태 초기화
    initialize_marked_words_state()

    if word in st.session_state.marked_words:
        remove_word_from_marked_list(word)
    else:
        add_word_to_marked_list(word, current_word)

    # 디버깅 출력
    st.write("### 현재 마크된 단어 데이터프레임:")
    st.write(st.session_state.marked_words_df)

    # 구글 드라이브에 저장/삭제
    save_or_remove_marked_words(st.session_state.marked_words_df)

def initialize_marked_words_state(): # 마크 상태 관리 변수 초기화
    if "marked_words" not in st.session_state:
        st.session_state.marked_words = []  # 마크된 단어 목록
    if "marked_words_df" not in st.session_state:
        st.session_state.marked_words_df = pd.DataFrame(columns=["Word", "Meaning", "Day", "Date"])  # 마크 데이터프레임

def add_word_to_marked_list(word, current_word):
    st.session_state.marked_words.append(word)  # 마크된 단어 추가
    new_entry = {
        "Word": current_word["Word"],
        "Meaning": current_word.get("Meaning", "No meaning provided"),
        "Day": current_word.get("Day", "Unspecified"),
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    st.session_state.marked_words_df = pd.concat(
        [st.session_state.marked_words_df, pd.DataFrame([new_entry])], ignore_index=True
    )
    st.write(f"단어 '{word}'가 마크되었습니다.")  # 디버깅 메시지

def remove_word_from_marked_list(word): # 단어를 마크 목록에서 제거.
    
    st.session_state.marked_words.remove(word)  # 마크된 단어 제거
    st.session_state.marked_words_df = st.session_state.marked_words_df[
        st.session_state.marked_words_df["Word"] != word
    ]
    st.write(f"단어 '{word}'가 마크에서 제거되었습니다.")  # 디버깅 메시지

def save_or_remove_marked_words(marked_words_df): # 마크된 단어를 구글 드라이브에 저장하거나 삭제.
    if marked_words_df.empty:
        # 마크된 단어가 없으면 파일 삭제
        if delete_from_drive("marked_words.csv"):
            st.warning("마크된 단어가 없습니다. 구글 드라이브에서 파일이 삭제되었습니다.")
        return

    # 데이터프레임을 구글 드라이브에 저장
    if save_to_drive(marked_words_df, "marked_words.csv"):
        st.success("마크된 단어가 구글 드라이브에 저장되었습니다.")