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


def load_marked_words_from_drive():
    """구글 드라이브에서 마크된 단어 데이터를 불러오기"""
    credentials = load_google_credentials()
    if not credentials:
        st.warning("구글 인증 실패: 자격 증명이 없습니다.")
        return pd.DataFrame()

    drive_service = build("drive", "v3", credentials=credentials)
    file_id = find_file_in_drive('marked_words.csv', drive_service)
    if not file_id:
        st.warning("구글 드라이브에서 'marked_words.csv' 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

    try:
        request = drive_service.files().get_media(fileId=file_id)
        file_data = request.execute()
        from io import StringIO
        return pd.read_csv(StringIO(file_data.decode('utf-8')))
    except Exception as e:
        st.error(f"마크된 단어 데이터를 불러오는 중 오류 발생: {e}")
        return pd.DataFrame()
    
def delete_marked_word_from_drive(word, marked_df):
    """
    마크된 단어 데이터를 구글 드라이브에서 삭제.

    Parameters:
        word (str): 삭제할 단어.
        marked_df (DataFrame): 현재 마크된 단어 데이터프레임.
    """
    marked_df = marked_df[marked_df["Word"] != word]  # 데이터프레임에서 단어 제거
    save_to_drive(marked_df, "marked_words.csv")  # 수정된 데이터 저장
    return marked_df