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

def load_incorrect_words_from_drive(): # 구글 드라이브에서 오답 데이터를 불러오기
    credentials = load_google_credentials()
    if not credentials:
        st.warning("구글 인증 실패: 자격 증명이 없습니다.")
        return pd.DataFrame()
    drive_service = build("drive", "v3", credentials=credentials)
    file_id = find_file_in_drive('incorrect_words.csv', drive_service)
    if not file_id:
        st.warning("구글 드라이브에서 'incorrect_words.csv' 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

    try:
        request = drive_service.files().get_media(fileId=file_id)
        file_data = request.execute()
        from io import StringIO
        return pd.read_csv(StringIO(file_data.decode('utf-8')))
    except Exception as e:
        st.error(f"오답 데이터를 불러오는 중 오류 발생: {e}")
        return pd.DataFrame()
    
def get_current_word(incorrect_df, current_index): # 현재 단어와 정답 반환.
    if incorrect_df.empty or current_index >= len(incorrect_df):
        return None, None
    current_word = incorrect_df.iloc[current_index]
    correct_answer = current_word["Meaning"]
    return current_word, correct_answer

def get_options(filtered_data, correct_answer): # 보기 선택지 생성.
    if filtered_data.empty:
        return [correct_answer]  # 데이터가 없으면 정답만 반환

    # 학습 페이지의 데이터프레임에서 무작위로 3개의 선택지 추출
    options = filtered_data["Meaning"].dropna().sample(3, replace=False).tolist()

    # 정답 추가 (중복 방지)
    if correct_answer not in options:
        options.append(correct_answer)

    # 선택지 셔플링
    random.shuffle(options)
    return options

def check_answer_and_update(selected_option, correct_answer, current_word, incorrect_df, drive_service): # 정답 확인 버튼 동작 및 데이터 갱신 함수.
    incorrect_df = process_and_save_incorrect_answers(
        selected_option, correct_answer, current_word, incorrect_df, drive_service
    )
    return incorrect_df


def process_and_save_incorrect_answers(selected_option, correct_answer, current_word, incorrect_df, drive_service): # 오답 단어를 처리하고 데이터프레임을 갱신하며, 구글 드라이브에 저장.
    is_correct = verify_answer(selected_option, correct_answer)

    if is_correct:
        # 정답인 경우: 데이터프레임 갱신 및 저장
        incorrect_df = remove_correct_word_from_df(current_word, incorrect_df)
        save_incorrect_df_to_drive(incorrect_df, drive_service)
    else:
        # 오답인 경우: 메시지 출력
        show_incorrect_message(correct_answer)

    return incorrect_df


def verify_answer(selected_option, correct_answer):
    if selected_option == correct_answer:
        st.success("정답입니다!")
        return True
    else:
        return False
    
def remove_correct_word_from_df(current_word, incorrect_df):
    updated_df = incorrect_df[incorrect_df["Word"] != current_word["Word"]]
    st.write("### Debug: 삭제 후 남은 오답 데이터프레임")
    st.write(updated_df)
    return updated_df

def save_incorrect_df_to_drive(incorrect_df, drive_service):
    incorrect_df.to_csv("incorrect_words.csv", index=False)
    file_metadata = {"name": "incorrect_words.csv", "mimeType": "text/csv"}
    media = MediaFileUpload("incorrect_words.csv", mimetype="text/csv")
    file_id = find_file_in_drive("incorrect_words.csv", drive_service)

    if file_id:
        drive_service.files().update(fileId=file_id, media_body=media).execute()
    else:
        drive_service.files().create(body=file_metadata, media_body=media).execute()

    st.success("오답 데이터가 Google Drive에 저장되었습니다.")

def show_incorrect_message(correct_answer):
    st.error(f"오답입니다! 정답은: {correct_answer}")




def move_to_next_word_and_update(incorrect_df, filtered_data): # 현재 복습 단어의 인덱스를 갱신하고, 단어와 선택지를 업데이트하는 함수.

    # 현재 인덱스 갱신
    if "current_index" in st.session_state:
        st.session_state.current_index += 1
    else:
        st.session_state.current_index = 0

    current_index = st.session_state.current_index

    # 디버깅 출력
    st.write(f"### Debug: 현재 인덱스 {current_index}, 데이터프레임 길이 {len(incorrect_df)}")

    if current_index >= len(incorrect_df):
        st.error("더 이상 복습할 단어가 없습니다.")
        return False

    # 현재 단어 정보 갱신
    try:
        current_word = incorrect_df.iloc[current_index]
        st.session_state.current_word = current_word["Word"]

        # 디버깅 출력
        st.write(f"### Debug: 현재 단어 {st.session_state.current_word}")

        # 선택지 갱신
        st.session_state.options = get_options(filtered_data, current_word["Meaning"])
        return True
    except Exception as e:
        st.error(f"오류 발생: {e}")
        return False
        