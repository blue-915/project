import os
import json

import streamlit as st
import pandas as pd

import random

from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def get_sequential_word(filtered_data):
    """순차적으로 단어와 정답을 반환하는 함수"""
    # 세션 상태에 저장된 current_index를 확인
    if "current_index" not in st.session_state:
        st.session_state.current_index = 0  # 처음에는 첫 번째 단어부터 시작
    
    # 데이터에서 현재 인덱스에 해당하는 단어를 선택
    current_word = filtered_data.iloc[st.session_state.current_index]
    correct_answer = current_word["Meaning"]
    
    # 랜덤으로 섞은 답을 선택지로 제공
    options = filtered_data["Meaning"].sample(4).tolist()
    if correct_answer not in options:
        options[0] = correct_answer  # 정답이 선택지에 포함되도록 함
    random.shuffle(options)

    return current_word, correct_answer, options

def check_answer(user_input, correct_answer, filtered_data):
    """사용자의 입력과 정답을 비교하고 결과를 처리하는 함수"""
    if user_input == correct_answer:
        st.success("정답입니다!")
        st.session_state.known_words.append(filtered_data.iloc[st.session_state.current_index]["Word"])
        st.session_state.records.append({"Word": filtered_data.iloc[st.session_state.current_index]["Word"], "Result": "Correct"})
    else:
        st.error(f"오답입니다! 정답은: {correct_answer}")
        st.session_state.unknown_words.append(filtered_data.iloc[st.session_state.current_index]["Word"])
        st.session_state.records.append({"Word": filtered_data.iloc[st.session_state.current_index]["Word"], "Result": "Incorrect"})

def move_to_next_word(filtered_data):
    """다음 단어로 이동하는 함수 (단어 인덱스 갱신 및 종료 메시지 표시)"""
    # 인덱스 증가
    st.session_state.current_index += 1
    if st.session_state.current_index >= len(filtered_data):  # 데이터의 끝에 도달하면 처음으로
        st.session_state.current_index = 0
        st.warning("데이터의 끝에 도달했습니다. 다시 처음으로 돌아갑니다.")  # 끝에 도달했을 때 경고 메시지 표시


def update_word_and_options(filtered_data):
    """단어와 보기 선택지를 갱신하는 함수"""
    current_word, correct_answer, options = get_sequential_word(filtered_data)
    st.session_state.correct_answer = correct_answer
    st.session_state.options = options
    st.session_state.current_word = current_word  # 추가: 새로 갱신된 단어 저장


import os

# 경로를 직접 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/mnt/c/Users/User/Downloads/study/service_account.json"

# 환경변수에서 GOOGLE_APPLICATION_CREDENTIALS 경로 가져오기
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

if credentials_path:
    print(f"GOOGLE_APPLICATION_CREDENTIALS 환경변수: {credentials_path}")
else:
    print("GOOGLE_APPLICATION_CREDENTIALS 환경변수가 설정되지 않았습니다.")

def get_credentials_from_secret_manager():
    """구글 서비스 계정 인증을 위한 함수"""
    from google.oauth2.service_account import Credentials
    credentials = Credentials.from_service_account_file(credentials_path)
    return credentials

def find_file_in_drive(file_name):
    """구글 드라이브에서 특정 파일을 검색하는 함수"""
    credentials = get_credentials_from_secret_manager()
    drive_service = build("drive", "v3", credentials=credentials)

    # 파일 검색
    results = drive_service.files().list(q=f"name = '{file_name}'", fields="files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        print(f"{file_name} 파일이 구글 드라이브에 없습니다.")
        return None  # 파일이 없으면 None 반환

    return files[0]["id"]  # 첫 번째 파일의 ID 반환

def download_file_from_drive(file_id):
    """구글 드라이브에서 파일을 다운로드하고 데이터프레임으로 변환하는 함수"""
    credentials = get_credentials_from_secret_manager()
    drive_service = build("drive", "v3", credentials=credentials)

    # 파일 다운로드
    request = drive_service.files().get_media(fileId=file_id)
    file_data = request.execute()

    # CSV 데이터를 데이터프레임으로 변환
    from io import StringIO
    csv_str = file_data.decode("utf-8")
    df = pd.read_csv(StringIO(csv_str))

    return df

def load_incorrect_words_from_drive():
    """구글 드라이브에서 오답 단어를 불러오는 함수"""
    file_id = find_file_in_drive("incorrect_words.csv")
    if file_id is None:
        return pd.DataFrame()  # 파일이 없으면 빈 데이터프레임 반환

    # 파일을 다운로드하여 데이터프레임으로 변환
    incorrect_df = download_file_from_drive(file_id)
    return incorrect_df

def save_to_drive(dataframe, filename):
    """구글 드라이브에 데이터프레임을 저장하는 함수"""
    # DataFrame을 CSV 파일로 저장
    filepath = f"/tmp/{filename}"
    dataframe.to_csv(filepath, index=False)

    # Google Drive API 클라이언트 생성
    credentials = get_credentials_from_secret_manager()
    drive_service = build("drive", "v3", credentials=credentials)

    # 파일 업로드
    file_metadata = {"name": filename}
    media = MediaFileUpload(filepath, mimetype="text/csv")
    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    return f"{filename}이 구글 드라이브에 저장되었습니다."

import pandas as pd
from datetime import datetime

def save_incorrect_answers_to_drive(filtered_data):
    """오답을 구글 드라이브에 저장하는 함수"""
    # 오답 데이터 추출
    incorrect_words = []
    for record in st.session_state.records:
        if record["Result"] == "Incorrect":
            if record["Word"] not in incorrect_words:  # 중복 방지
                incorrect_words.append(record["Word"])

    # 오답 데이터프레임 생성 (단어 철자와 뜻 포함)
    incorrect_df = filtered_data[filtered_data["Word"].isin(incorrect_words)]
    
    # 현재 날짜 추가
    incorrect_df["Date"] = datetime.now().strftime("%Y-%m-%d")
    incorrect_df["Incorrect"] = "Yes"  # 오답 표시
    
    # 구글 드라이브에 저장
    return save_to_drive(incorrect_df, 'incorrect_words.csv')

def save_marked_words_to_drive(filtered_data):
    """단어 마크한 단어들을 구글 드라이브에 저장하는 함수"""
    marked_words = st.session_state.marked_words  # 세션 상태에서 마크된 단어를 직접 가져옴
    marked_df = filtered_data[filtered_data["Word"].isin(marked_words)]
    
    # 현재 날짜 추가
    marked_df["Date"] = datetime.now().strftime("%Y-%m-%d")
    marked_df["Marked"] = "Yes"  # 마크 표시

    return save_to_drive(marked_df, 'marked_words.csv')


def mark_word(word):
    """단어를 마크하거나 마크를 취소하는 함수"""
    # 마크된 단어 목록을 세션 상태에 저장
    if "marked_words" not in st.session_state:
        st.session_state.marked_words = []  # 마크된 단어 목록 초기화
    
    # 단어가 이미 마크된 상태인지 확인
    if word in st.session_state.marked_words:
        st.session_state.marked_words.remove(word)  # 마크 취소
        return False  # 마크가 취소된 상태
    else:
        st.session_state.marked_words.append(word)  # 마크 처리
        return True  # 마크된 상태
