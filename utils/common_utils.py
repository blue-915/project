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
    

import os
from google.oauth2 import service_account
import streamlit as st

def get_credentials_from_secret_manager():
    """구글 서비스 계정 인증을 위한 함수"""
    # Kubernetes에서 마운트된 서비스 계정 파일 경로를 환경 변수로 설정
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/app/service-account-file.json")
    
    if not credentials_path:
        raise ValueError("GOOGLE_APPLICATION_CREDENTIALS 환경변수가 설정되지 않았습니다.")
    
    # 서비스 계정 인증을 가져옵니다.
    return service_account.Credentials.from_service_account_file(credentials_path)

def load_google_credentials():
    """구글 서비스 계정 인증 로드"""
    # Kubernetes에서 마운트된 서비스 계정 파일 경로를 환경 변수로 설정
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/app/service-account-file.json")
    
    if not credentials_path:
        st.error("Google Credentials 경로가 설정되지 않았습니다.")
        return None
    
    # 서비스 계정 인증을 가져옵니다.
    credentials = service_account.Credentials.from_service_account_file(credentials_path)
    st.write("Google Credentials Loaded Successfully")
    return credentials


from google.cloud import storage
import pandas as pd

def save_to_gcs(dataframe, filename, bucket_name):
    """구글 클라우드 저장소에 데이터프레임 저장"""
    filepath = f"/tmp/{filename}"
    dataframe.to_csv(filepath, index=False)

    # Google Cloud Storage 클라이언트 초기화
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # 기존에 같은 이름의 파일이 있으면 삭제
    blob = bucket.blob(filename)
    if blob.exists():
        blob.delete()

    # 파일 업로드
    blob.upload_from_filename(filepath)
    print(f"파일 {filename}이(가) {bucket_name} 버킷에 업로드되었습니다.")

def find_file_in_gcs(filename, bucket_name):
    """구글 클라우드 저장소에서 파일 검색"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # 파일이 존재하는지 확인
    blob = bucket.blob(filename)
    if blob.exists():
        return blob.name  # 파일 경로 반환
    return None

# common_utils.py
def initialize_gcs_client():
    """
    Google Cloud Storage 클라이언트 객체를 초기화하는 함수.

    Returns:
        storage_client: Google Cloud Storage 클라이언트 객체
    """
    storage_client = storage.Client()
    return storage_client