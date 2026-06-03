# 기업 재무 분석 도구 - Streamlit 배포 가이드

## 배포 전 준비사항

### 1. GitHub 저장소 생성

```bash
git init
git add .
git commit -m "Initial commit: Corporate Financial Analysis Tool"
git branch -M main
git remote add origin https://github.com/your-username/financial-analysis-tool.git
git push -u origin main
```

### 2. Streamlit Cloud에서 배포

#### 단계 1: Streamlit Cloud 가입
- https://streamlit.io/cloud 접속
- GitHub 계정으로 로그인

#### 단계 2: 새 앱 배포
1. "New app" 버튼 클릭
2. GitHub 저장소 선택 (`financial-analysis-tool`)
3. Branch: `main` 선택
4. Main file path: `financial_analysis_app.py` 입력
5. 배포 시작

#### 단계 3: Secrets 설정 (중요!)
Streamlit Cloud 대시보드에서:
1. 앱 설정 (⚙️) 클릭
2. "Secrets" 탭 이동
3. 다음 내용 추가:

```toml
DART_API_KEY = "your_dart_api_key_here"
```

### 3. 로컬 환경에서 secrets 테스트

`.streamlit/secrets.toml` 파일을 생성 (로컬에서만, GitHub에는 업로드하지 않음):

```toml
DART_API_KEY = "your_dart_api_key_here"
```

그리고 코드에서 다음과 같이 접근:

```python
dart_api_key = st.secrets.get("DART_API_KEY", os.getenv("DART_API_KEY", ""))
```

## 배포된 앱 URL

배포 완료 후 접속: `https://your-username-financial-analysis-tool.streamlit.app`

## 필수 파일 확인

- ✅ `requirements.txt` - 모든 의존성 패키지
- ✅ `.gitignore` - `.env` 파일 제외 설정
- ✅ `.streamlit/config.toml` - Streamlit 설정
- ✅ `financial_analysis_app.py` - 메인 앱

## 주의사항

⚠️ **API 키 보안**
- `.env` 파일은 절대 GitHub에 업로드하지 마세요 (`.gitignore`에 추가됨)
- Streamlit Cloud의 "Secrets" 메뉴에서만 API 키를 저장하세요
- 로컬 테스트를 위해 `.streamlit/secrets.toml`은 `.gitignore`에 포함되어 있습니다

## 배포 후 문제 해결

### 패키지 설치 오류
- `requirements.txt`에 필요한 모든 패키지가 포함되어 있는지 확인
- Python 버전 호환성 확인 (Streamlit Cloud는 Python 3.8 이상 지원)

### API 키 오류
- Streamlit Cloud의 "Secrets" 설정 확인
- API 키 형식이 정확한지 확인

### 성능 문제
- 데이터 캐싱 확인 (`@st.cache_data` 사용 중)
- FinanceDataReader와 DART API 요청 최적화

## 추가 리소스

- [Streamlit Cloud 문서](https://docs.streamlit.io/streamlit-cloud/get-started)
- [Streamlit Secrets 관리](https://docs.streamlit.io/streamlit-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
- [DART API 문서](https://opendart.fss.or.kr/)
