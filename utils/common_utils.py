import os
import random
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import streamlit as st

def initialize_session():
    """세션 상태 초기화"""
    default_states = {
        "page": "Home",
        "marked_words": [],
        "records": [],
        "current_index": 0,
        "known_words": [],
        "unknown_words": [],
        "filtered_data": pd.DataFrame(),
    }
    for key, value in default_states.items():
        if key not in st.session_state:
            st.session_state[key] = value

@st.cache_data
def load_data(file_url):
    return pd.read_excel(file_url)

def handle_page_navigation(page_name):
    """페이지 이동 처리"""
    st.session_state.page = page_name
    
# 경로를 직접 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/mnt/c/Users/User/Downloads/study/service_account.json"

def get_credentials_from_secret_manager():
    """구글 서비스 계정 인증을 위한 함수"""
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS 환경변수가 설정되지 않았습니다.")
    from google.oauth2.service_account import Credentials
    return Credentials.from_service_account_file(credentials_path)

def load_google_credentials():
    """구글 서비스 계정 인증 로드"""
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not credentials_path:
        st.error("Google Credentials 경로가 설정되지 않았습니다.")
        return None
    credentials = Credentials.from_service_account_file(credentials_path)
    st.write("Google Credentials Loaded Successfully")
    return credentials

def save_to_drive(dataframe, filename):
    """구글 드라이브에 데이터프레임 저장"""
    filepath = f"/tmp/{filename}"
    dataframe.to_csv(filepath, index=False)

    credentials = load_google_credentials()
    if not credentials:
        return

    drive_service = build("drive", "v3", credentials=credentials)
    file_id = find_file_in_drive(filename, drive_service)
    if file_id:
        drive_service.files().delete(fileId=file_id).execute()

    file_metadata = {"name": filename}
    media = MediaFileUpload(filepath, mimetype="text/csv")
    drive_service.files().create(body=file_metadata, media_body=media).execute()

def find_file_in_drive(filename, drive_service):
    """구글 드라이브에서 파일 검색"""
    results = drive_service.files().list(q=f"name = '{filename}'", fields="files(id, name)").execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None

# common_utils.py
def initialize_drive_service():
    """
    Google Drive API 서비스 객체를 초기화하는 함수.

    Returns:
        drive_service: Google Drive API 서비스 객체
    """
    credentials = load_google_credentials()
    if credentials:
        return build("drive", "v3", credentials=credentials)
    else:
        raise Exception("Google Drive 인증에 실패했습니다.")