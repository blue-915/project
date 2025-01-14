# 영어 단어 암기 프로그램 📘

효율적인 영어 단어 학습을 지원하는 **영어 단어 암기 프로그램**입니다.  
이 프로그램은 단어를 학습, 복습, 그리고 중요 단어를 점검 할 수 있도록 만들어졌습니다.
Streamlit과 Google Drive API를 활용하여 직관적인 UI와 데이터 저장 기능을 제공합니다.

---

## 🌟 주요 기능
1. **학습모드**  
   - Day별로 단어를 학습하며, 정답을 선택할 수 있습니다.  
   - 틀린 단어는 자동으로 복습 리스트에 추가됩니다.  

2. **복습모드**  
   - 학습 중 틀린 단어만 모아 복습할 수 있습니다.  
   - 복습이 완료된 단어는 리스트에서 제거됩니다.  

3. **체크리스트**  
   - 중요 단어를 마크하여 별도의 체크리스트로 관리 가능합니다.  
   - 체크리스트에서 단어를 삭제하거나 복습할 수 있습니다.  

4. **진도율 확인**  
   - 전체 학습 진도와 Day별 학습 진도를 그래프로 시각화합니다.  

5. **Google Drive 연동**  
   - 학습 데이터와 체크리스트 데이터를 Google Drive에 저장하여 관리할 수 있습니다.

---

## 🛠️ 설치 및 실행

### 1. 의존성 설치
프로젝트를 실행하기 전에 필요한 패키지를 설치합니다.
```bash
pip install -r requirements.txt
```

### 2. Streamlit 실행
아래 명령어로 프로그램을 실행합니다.
```bash
streamlit run app.py
```

### 3. 환경 변수 설정
Google Drive API 연동을 위해 서비스 계정 키 파일 경로를 설정해야 합니다.
이를 환경 변수를 통해 설정합니다:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service_account.json"
```
---
## 📂 디렉토리 구조
```plane text
project/
│
├── app.py                  # 메인 프로그램
├── requirements.txt        # 필요한 Python 패키지 목록
├── utils/                  # 프로그램 기능 모듈
│   ├── common_utils.py     # 공통 유틸리티
│   ├── learning_utils.py   # 학습 관련 기능
│   ├── review_utils.py     # 복습 관련 기능
│   ├── checklist_utils.py  # 체크리스트 관련 기능
│   └── visual_utils.py     # 진도율 확인 관련 기능
```
---

## 🚀 기술 스택
- 프로그래밍 언어: Python
- 웹 프레임워크: Streamlit
- 데이터 관리: Pandas, Google Drive API
- 배포 플랫폼: Streamlit Cloud