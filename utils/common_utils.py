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
from google.cloud import secretmanager
from google.oauth2.service_account import Credentials
import streamlit as st

# Google Secret Manager에서 Secret을 가져오는 함수
def access_secret_version(project_id, secret_id, version_id="latest"):
    """
    Google Secret Manager에서 Secret 값을 가져오는 함수.
    """
    try:
        # Secret Manager 클라이언트 생성
        client = secretmanager.SecretManagerServiceClient()

        # Secret 경로 생성
        name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

        # Secret 가져오기
        response = client.access_secret_version(name=name)
        secret_data = response.payload.data.decode("UTF-8")

        st.write("DEBUG - Secret 데이터를 성공적으로 가져왔습니다.")
        return secret_data
    except Exception as e:
        st.error(f"DEBUG - Google Secret Manager에서 Secret 가져오기 실패: {e}")
        raise ValueError("Google Secret Manager 연동 오류 발생")

# Google Secret Manager 연동 및 환경 변수 설정
def setup_google_credentials():
    """
    Google Secret Manager에서 서비스 계정 키를 가져와 환경 변수로 설정.
    """
    try:
        # GCP 프로젝트 ID 및 Secret 이름
        project_id = "silent-album-447213-g4"  # GCP 프로젝트 ID를 입력하세요
        secret_id = "projects/232555212335/secrets/project"  # Secret 이름

        # Secret Manager에서 JSON 키 가져오기
        google_credentials_json = access_secret_version(project_id, secret_id)

        # 서비스 계정 키를 임시 파일로 저장
        TEMP_CREDENTIALS_PATH = "/tmp/service_account.json"
        with open(TEMP_CREDENTIALS_PATH, "w") as file:
            file.write(google_credentials_json)
        
        # 환경 변수 설정
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = TEMP_CREDENTIALS_PATH

        # 디버깅: JSON 키 파일 확인
        with open(TEMP_CREDENTIALS_PATH, "r") as file:
            st.write("DEBUG - 저장된 JSON 키 파일 내용:", file.read())

        st.success("Google Credentials 설정 완료")
    except Exception as e:
        st.error(f"DEBUG - Google Credentials 설정 중 오류 발생: {e}")
        raise ValueError("Google Credentials 설정 실패")

# Google Credentials 로드 함수
def load_google_credentials():
    """
    서비스 계정 키를 통해 Google Credentials를 로드.
    """
    try:
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ValueError("환경변수 GOOGLE_APPLICATION_CREDENTIALS가 설정되지 않았습니다.")

        credentials = Credentials.from_service_account_file(credentials_path)
        st.write("DEBUG - Google Credentials 성공적으로 로드되었습니다.")
        return credentials
    except Exception as e:
        st.error(f"DEBUG - Google Credentials 로드 중 오류 발생: {e}")
        return None

# Streamlit 앱 실행
st.title("Google Secret Manager와 연동된 Streamlit 앱")

# Google Secret Manager에서 Secret을 가져오고 환경 변수 설정
setup_google_credentials()

# Google Credentials 로드 테스트
credentials = load_google_credentials()

if credentials:
    st.success("Google API와 연동 성공!")
else:
    st.error("Google API 연동 실패")




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