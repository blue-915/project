import os
import random
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from google.cloud import storage  # Google Cloud Storage 사용
import streamlit as st

from utils.common_utils import (initialize_session,
                                handle_page_navigation,
                                get_credentials_from_secret_manager,
                                load_google_credentials,
                                save_to_gcs,  # GCS 관련 함수 호출
                                find_file_in_gcs)  # GCS 관련 함수 호출

def load_marked_words_from_gcs(bucket_name):
    """구글 클라우드 저장소(GCS)에서 마크된 단어 데이터를 불러오기"""
    credentials = load_google_credentials()
    if not credentials:
        st.warning("구글 인증 실패: 자격 증명이 없습니다.")
        return pd.DataFrame()

    storage_client = storage.Client(credentials=credentials)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob("marked_words.csv")

    if not blob.exists():
        st.warning("구글 클라우드 저장소에서 'marked_words.csv' 파일을 찾을 수 없습니다.")
        return pd.DataFrame()

    try:
        file_data = blob.download_as_text()
        from io import StringIO
        return pd.read_csv(StringIO(file_data))
    except Exception as e:
        st.error(f"마크된 단어 데이터를 불러오는 중 오류 발생: {e}")
        return pd.DataFrame()

def delete_marked_word_from_gcs(word, marked_df, bucket_name):
    """
    마크된 단어 데이터를 구글 클라우드 저장소(GCS)에서 삭제.

    Parameters:
        word (str): 삭제할 단어.
        marked_df (DataFrame): 현재 마크된 단어 데이터프레임.
        bucket_name (str): GCS 버킷 이름
    """
    marked_df = marked_df[marked_df["Word"] != word]  # 데이터프레임에서 단어 제거
    save_to_gcs(marked_df, "marked_words.csv", bucket_name)  # 수정된 데이터 GCS에 저장
    return marked_df