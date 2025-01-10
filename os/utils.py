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

def save_incorrect_answers_to_drive(filtered_data):
    """오답 데이터를 구글 드라이브에 저장"""
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
    save_to_drive(incorrect_df, "incorrect_words.csv")



def load_incorrect_words_from_drive():
    """구글 드라이브에서 오답 데이터를 불러오기"""
    credentials = load_google_credentials()
    if not credentials:
        return pd.DataFrame()
    drive_service = build("drive", "v3", credentials=credentials)
    file_id = find_file_in_drive('incorrect_words.csv', drive_service)
    if not file_id:
        return pd.DataFrame()

    request = drive_service.files().get_media(fileId=file_id)
    file_data = request.execute()
    from io import StringIO
    return pd.read_csv(StringIO(file_data.decode('utf-8')))

def get_current_word(incorrect_df, current_index):
    """
    현재 단어와 정답 반환.

    Parameters:
        incorrect_df (DataFrame): 복습할 오답 단어가 포함된 데이터프레임.
        current_index (int): 현재 복습할 단어의 인덱스.

    Returns:
        tuple: (current_word, correct_answer)
            - current_word (Series): 현재 단어의 데이터.
            - correct_answer (str): 현재 단어의 정답(뜻).
    """
    if incorrect_df.empty or current_index >= len(incorrect_df):
        return None, None
    current_word = incorrect_df.iloc[current_index]
    correct_answer = current_word["Meaning"]
    return current_word, correct_answer


def get_options(filtered_data, correct_answer):
    """
    보기 선택지 생성.

    Parameters:
        filtered_data (DataFrame): 학습 페이지 데이터.
        correct_answer (str): 현재 정답.

    Returns:
        list: 보기 선택지 (정답 포함).
    """
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

import os

def check_answer_and_update(selected_option, correct_answer, current_word, incorrect_df):
    """
    정답 확인 버튼 동작 및 데이터 갱신 함수.
    
    Parameters:
        selected_option (str): 사용자가 선택한 답안.
        correct_answer (str): 현재 정답.
        current_word (Series): 현재 단어 데이터.
        incorrect_df (DataFrame): 오답 데이터프레임.

    Returns:
        DataFrame: 갱신된 incorrect_df.
    """
    if selected_option == correct_answer:
        st.success("정답입니다!")

        # 학습 기록에 추가
        st.session_state.records.append({
            "Word": current_word["Word"],
            "Result": "Correct"
        })

        # incorrect_words.csv에서 해당 단어 삭제
        incorrect_df = incorrect_df[incorrect_df["Word"] != current_word["Word"]]

        # 디렉토리가 없으면 생성
        save_dir = "data"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        # CSV 파일 업데이트
        incorrect_df.to_csv(f"{save_dir}/incorrect_words.csv", index=False)

    else:
        st.error(f"오답입니다! 정답은 {correct_answer}입니다.")
        st.session_state.records.append({
            "Word": current_word["Word"],
            "Result": "Incorrect"
        })

    return incorrect_df


def move_to_next_word_and_update(incorrect_df, filtered_data):
    """
    현재 복습 단어의 인덱스를 갱신하고, 단어와 선택지를 업데이트하는 함수.

    Parameters:
        incorrect_df (DataFrame): 복습할 오답 단어 데이터프레임.
        filtered_data (DataFrame): 전체 학습 데이터프레임.

    Returns:
        bool: 다음 단어가 있는 경우 True, 없는 경우 False.
    """
    # 현재 인덱스 갱신
    if "current_index" in st.session_state:
        st.session_state.current_index += 1
    else:
        st.session_state.current_index = 0

    current_index = st.session_state.current_index

    # 현재 인덱스가 데이터프레임 길이를 초과하면 복습 종료
    if current_index >= len(incorrect_df):
        st.error("더 이상 복습할 단어가 없습니다.")
        return False

    # 현재 단어 정보 갱신
    current_word = incorrect_df.iloc[current_index]
    st.session_state.current_word = current_word["Word"]

    # 선택지 갱신
    st.session_state.options = get_options(filtered_data, current_word["Meaning"])
    return True



def load_marked_words_from_drive():
    """구글 드라이브에서 마크된 단어를 불러오는 함수"""
    credentials = get_credentials_from_secret_manager()
    drive_service = build("drive", "v3", credentials=credentials)
    
    file_id = find_file_in_drive("marked_words.csv", drive_service)
    if not file_id:
        return pd.DataFrame()  # 파일이 없으면 빈 데이터프레임 반환

    # 파일 다운로드
    request = drive_service.files().get_media(fileId=file_id)
    file_data = request.execute()

    from io import StringIO
    return pd.read_csv(StringIO(file_data.decode("utf-8")))


def save_marked_words_to_drive(filtered_data):
    """마크된 단어를 구글 드라이브에 저장"""
    marked_words = st.session_state.marked_words
    marked_df = filtered_data[filtered_data['Word'].isin(marked_words)]
    save_to_drive(marked_df, 'marked_words.csv')

def mark_word(word):
    """단어를 마크하거나 마크를 취소"""
    if word in st.session_state.marked_words:
        st.session_state.marked_words.remove(word)
        st.success("단어 마크를 취소했습니다.")
    else:
        st.session_state.marked_words.append(word)
        st.success("단어를 마크했습니다.")
