import os
import random
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
from google.cloud import storage
import streamlit as st

# Google Cloud Storage에 파일을 저장하는 함수
def save_to_gcs(dataframe, filename, bucket_name):
    """구글 클라우드 저장소(GCS)에 데이터프레임 저장"""
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
    st.success(f"파일 {filename}이(가) {bucket_name} 버킷에 업로드되었습니다.")

# Google Cloud Storage에서 파일을 찾는 함수
def find_file_in_gcs(filename, bucket_name):
    """구글 클라우드 저장소에서 파일 검색"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    
    # 파일이 존재하는지 확인
    blob = bucket.blob(filename)
    if blob.exists():
        return blob.name  # 파일 경로 반환
    return None

# 오답 데이터를 GCS에 저장하는 함수
def save_incorrect_answers_to_gcs(filtered_data, bucket_name):
    """오답 데이터를 구글 클라우드 저장소(GCS)에 저장"""
    # 'Incorrect' 상태인 단어만 필터링
    incorrect_words = [record['Word'] for record in st.session_state.records if record['Result'] == 'Incorrect']
    
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

    # GCS에 저장
    save_to_gcs(incorrect_df, "incorrect_words.csv", bucket_name)

# 마크된 단어를 GCS에 저장하거나 삭제하는 함수
def save_or_remove_marked_words(marked_words_df, bucket_name):
    """
    마크된 단어를 구글 클라우드 저장소(GCS)에 저장하거나 삭제.

    Parameters:
        marked_words_df (DataFrame): 현재 마크된 단어 데이터프레임.
        bucket_name (str): GCS 버킷 이름
    """
    if marked_words_df.empty:
        # 마크된 단어가 없으면 파일 삭제
        if delete_from_gcs("marked_words.csv", bucket_name):
            st.warning("마크된 단어가 없습니다. GCS에서 파일이 삭제되었습니다.")
        return

    # 데이터프레임을 GCS에 저장
    save_to_gcs(marked_words_df, "marked_words.csv", bucket_name)

# GCS에서 파일을 삭제하는 함수
def delete_from_gcs(filename, bucket_name):
    """구글 클라우드 저장소에서 파일 삭제"""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    
    if blob.exists():
        blob.delete()
        st.success(f"파일 {filename}이 GCS에서 삭제되었습니다.")
        return True
    else:
        st.warning(f"파일 {filename}이 GCS에 존재하지 않습니다.")
        return False

# 단어를 마크하거나 마크 취소하고 GCS에 저장/삭제하는 함수
def toggle_mark_word(word, current_word, bucket_name):
    """
    단어를 마크하거나 마크 취소하고 구글 클라우드 저장소(GCS)에 저장/삭제.

    Parameters:
        word (str): 마크할 단어.
        current_word (dict): 현재 단어의 정보.
        bucket_name (str): GCS 버킷 이름
    """
    # 세션 상태 초기화
    initialize_marked_words_state()

    if word in st.session_state.marked_words:
        remove_word_from_marked_list(word)
    else:
        add_word_to_marked_list(word, current_word)

    # GCS에 저장/삭제
    save_or_remove_marked_words(st.session_state.marked_words_df, bucket_name)

# 세션 상태 관리 초기화 함수
def initialize_marked_words_state():
    """마크 상태 관리 변수 초기화"""
    if "marked_words" not in st.session_state:
        st.session_state.marked_words = []  # 마크된 단어 목록
    if "marked_words_df" not in st.session_state:
        st.session_state.marked_words_df = pd.DataFrame(columns=["Word", "Meaning", "Day", "Date"])  # 마크 데이터프레임

# 단어를 마크 목록에 추가하는 함수
def add_word_to_marked_list(word, current_word):
    """
    단어를 마크 목록에 추가.

    Parameters:
        word (str): 마크할 단어.
        current_word (dict): 현재 단어의 정보.
    """
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

# 단어를 마크 목록에서 제거하는 함수
def remove_word_from_marked_list(word):
    """
    단어를 마크 목록에서 제거.

    Parameters:
        word (str): 마크 취소할 단어.
    """
    st.session_state.marked_words.remove(word)  # 마크된 단어 제거
    st.session_state.marked_words_df = st.session_state.marked_words_df[
        st.session_state.marked_words_df["Word"] != word
    ]
    st.write(f"단어 '{word}'가 마크에서 제거되었습니다.")  # 디버깅 메시지

# 단어의 정답 여부를 확인하고 오답 처리하는 함수
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

# 다음 단어로 이동하는 함수
def move_to_next_word(filtered_data):
    """다음 단어로 이동하는 함수"""
    st.session_state.current_index += 1
    if st.session_state.current_index >= len(filtered_data):
        st.session_state.current_index = 0
        st.warning("모든 단어를 학습했습니다. 다시 처음부터 시작합니다.")

# 단어와 보기 선택지를 갱신하는 함수
def update_word_and_options(filtered_data):
    """단어와 보기 선택지를 갱신하는 함수"""
    current_word, correct_answer, options = get_sequential_word(filtered_data)
    st.session_state.current_word = current_word
    st.session_state.correct_answer = correct_answer
    st.session_state.options = options

# 순차적으로 단어와 정답을 반환하는 함수
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