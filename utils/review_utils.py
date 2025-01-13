import os
import random
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from google.cloud import storage  # Google Cloud Storage 클라이언트를 임포트
import streamlit as st

from utils.common_utils import (initialize_session,
                                handle_page_navigation,
                                get_credentials_from_secret_manager,
                                load_google_credentials)

# 구글 클라우드 저장소에서 오답 데이터를 불러오는 함수
def load_incorrect_words_from_gcs(bucket_name):
    """구글 클라우드 저장소(GCS)에서 오답 데이터를 불러오기"""
    credentials = load_google_credentials()
    if not credentials:
        st.warning("구글 인증 실패: 자격 증명이 없습니다.")
        return pd.DataFrame()

    # Google Cloud Storage 클라이언트 초기화
    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)

    # 파일 검색
    blob = bucket.blob('incorrect_words.csv')
    if not blob.exists():
        st.warning("구글 클라우드 저장소에서 'incorrect_words.csv' 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

    try:
        # 파일 다운로드
        file_data = blob.download_as_text()
        from io import StringIO
        return pd.read_csv(StringIO(file_data))
    except Exception as e:
        st.error(f"오답 데이터를 불러오는 중 오류 발생: {e}")
        return pd.DataFrame()

# 현재 단어와 정답 반환
def get_current_word(incorrect_df, current_index):
    """
    현재 단어와 정답 반환.
    """
    if incorrect_df.empty or current_index >= len(incorrect_df):
        return None, None
    current_word = incorrect_df.iloc[current_index]
    correct_answer = current_word["Meaning"]
    return current_word, correct_answer

# 보기 선택지 생성
def get_options(filtered_data, correct_answer):
    """
    보기 선택지 생성.
    """
    if filtered_data.empty:
        return [correct_answer]

    options = filtered_data["Meaning"].dropna().sample(3, replace=False).tolist()
    if correct_answer not in options:
        options.append(correct_answer)
    random.shuffle(options)
    return options

# 정답 확인 및 업데이트 함수
def check_answer_and_update(selected_option, correct_answer, current_word, incorrect_df, bucket_name):
    """
    정답 확인 및 데이터 갱신 함수.
    """
    incorrect_df = process_and_save_incorrect_answers(
        selected_option, correct_answer, current_word, incorrect_df, bucket_name
    )
    return incorrect_df

# 오답 처리 및 GCS에 저장
def process_and_save_incorrect_answers(selected_option, correct_answer, current_word, incorrect_df, bucket_name):
    """
    오답 단어를 처리하고 데이터프레임을 갱신하며, GCS에 저장.
    """
    is_correct = verify_answer(selected_option, correct_answer)

    if is_correct:
        incorrect_df = remove_correct_word_from_df(current_word, incorrect_df)
        save_incorrect_df_to_gcs(incorrect_df, bucket_name)
    else:
        show_incorrect_message(correct_answer)

    return incorrect_df

# 정답 여부 확인
def verify_answer(selected_option, correct_answer):
    if selected_option == correct_answer:
        st.success("정답입니다!")
        return True
    else:
        return False

# 정답인 단어 삭제
def remove_correct_word_from_df(current_word, incorrect_df):
    updated_df = incorrect_df[incorrect_df["Word"] != current_word["Word"]]
    return updated_df

# GCS에 오답 데이터 저장
def save_incorrect_df_to_gcs(incorrect_df, bucket_name):
    incorrect_df.to_csv("incorrect_words.csv", index=False)
    # Google Cloud Storage 클라이언트
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # Blob 생성 및 파일 업로드
    blob = bucket.blob('incorrect_words.csv')
    blob.upload_from_filename('incorrect_words.csv')
    st.success("오답 데이터가 Google Cloud Storage에 저장되었습니다.")

# 오답 메시지 출력
def show_incorrect_message(correct_answer):
    st.error(f"오답입니다! 정답은: {correct_answer}")

# 복습 인덱스를 갱신하고, 단어와 선택지를 업데이트하는 함수
def move_to_next_word_and_update(incorrect_df, filtered_data):
    """
    복습 단어의 인덱스를 갱신하고, 단어와 선택지를 업데이트하는 함수.
    """
    if "current_index" in st.session_state:
        st.session_state.current_index += 1
    else:
        st.session_state.current_index = 0

    current_index = st.session_state.current_index

    if current_index >= len(incorrect_df):
        st.error("더 이상 복습할 단어가 없습니다.")
        return False

    try:
        current_word = incorrect_df.iloc[current_index]
        st.session_state.current_word = current_word["Word"]
        st.session_state.options = get_options(filtered_data, current_word["Meaning"])
        return True
    except Exception as e:
        st.error(f"오류 발생: {e}")
        return False