import random
import streamlit as st
import pandas as pd
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive

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



        

def save_incorrect_answers_to_drive(filtered_data):
    """오답을 구글 드라이브에 저장하는 함수"""
    # 오답 데이터 추출
    incorrect_words = []
    for record in st.session_state.records:
        if record["Result"] == "Incorrect":
            if record["Word"] not in incorrect_words:  # 중복 방지
                incorrect_words.append(record["Word"])

    # 오답 데이터프레임 생성
    incorrect_df = filtered_data[filtered_data["Word"].isin(incorrect_words)]
    
    # 구글 드라이브에 저장
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # 인증을 위한 웹 서버 생성
    drive = GoogleDrive(gauth)

    # DataFrame을 CSV로 저장
    csv_data = incorrect_df.to_csv(index=False)

    # 구글 드라이브에 업로드
    file_drive = drive.CreateFile({'title': 'incorrect_words.csv'})
    file_drive.Upload()
    return "오답이 구글 드라이브에 저장되었습니다."

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

def save_to_drive(dataframe, filename):
    """구글 드라이브에 데이터프레임을 저장하는 함수"""
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # 인증을 위한 웹 서버 생성
    drive = GoogleDrive(gauth)

    # DataFrame을 CSV로 저장
    csv_data = dataframe.to_csv(index=False)

    # 구글 드라이브에 업로드
    file_drive = drive.CreateFile({'title': filename})
    file_drive.Upload()
    return f"{filename}이 구글 드라이브에 저장되었습니다."

def save_incorrect_answers_to_drive(filtered_data):
    """오답을 구글 드라이브에 저장하는 함수"""
    incorrect_words = [record["Word"] for record in st.session_state.records if record["Result"] == "Incorrect"]
    incorrect_df = filtered_data[filtered_data["Word"].isin(incorrect_words)]
    
    return save_to_drive(incorrect_df, 'incorrect_words.csv')

def save_marked_words_to_drive(filtered_data):
    """단어 마크한 단어들을 구글 드라이브에 저장하는 함수"""
    marked_words = st.session_state.marked_words  # 세션 상태에서 마크된 단어를 직접 가져옴
    marked_df = filtered_data[filtered_data["Word"].isin(marked_words)]
    
    return save_to_drive(marked_df, 'marked_words.csv')
