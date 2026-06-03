# 📊 기업 재무 분석 도구

고급 재무 진단 시스템 - 포괄적인 기술적 및 기본적 구조 매핑

## 🌟 주요 기능

### 미국 주식 (US Market)
- **Yahoo Finance** 데이터 활용
- 실시간 주가 데이터
- 재무제표 분석
- 기술적 분석 (일목균형표)
- 밸류에이션 지표

### 한국 주식 (KR Market)
- **DART API** 재무 데이터
- **FinanceDataReader** 주가 데이터
- 연결재무제표 및 별도재무제표
- 한국 회계기준 분석

## 🛠 기술 스택

- **프레임워크**: Streamlit
- **데이터 수집**: 
  - yfinance (미국 주식)
  - FinanceDataReader (한국 주식)
  - opendartreader (한국 재무)
- **데이터 분석**: Pandas, NumPy
- **배포**: Streamlit Cloud

## 📋 설치 및 실행

### 로컬 환경

```bash
# 1. 저장소 클론
git clone https://github.com/your-username/financial-analysis-tool.git
cd financial-analysis-tool

# 2. 가상환경 생성 (선택)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# 3. 패키지 설치
pip install -r requirements.txt

# 4. .env 파일 생성 (한국 주식 사용 시)
echo DART_API_KEY=your_api_key_here > .env

# 5. 앱 실행
python -m streamlit run financial_analysis_app.py
```

### 웹 접속
- **로컬**: http://localhost:8501
- **배포**: https://your-app.streamlit.app

## 🔑 API 키 설정

### DART API 키 (한국 주식용)

1. [DART 개발자센터](https://opendart.fss.or.kr/) 방문
2. 회원가입 후 API Key 발급
3. 로컬: `.env` 파일에 추가
   ```
   DART_API_KEY=your_api_key_here
   ```
4. Streamlit Cloud: "Secrets" 설정에 추가

## 📊 주요 화면

### Overview 탭
- 현재 주가 정보
- 52주 주가 변동폭
- 50일 이동평균
- PER 등 기본 지표

### 재무제표 탭
- 재무상태표 (Balance Sheet)
- 손익계산서 (Financials)
- 주요 비율 분석

### 기술적 분석 탭
- 일목균형표 (Ichimoku)
- 추세 및 모멘텀 분석

### 뉴스 탭
- 실시간 관련 뉴스

## 🚀 배포 가이드

자세한 배포 방법은 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) 참조

## 🛡 보안 주의사항

- ⚠️ API 키는 절대 코드에 하드코딩하지 마세요
- `.env` 파일과 `.streamlit/secrets.toml`은 `.gitignore`에 포함됩니다
- GitHub에 업로드되지 않습니다
- 배포 환경에서는 Streamlit Cloud의 "Secrets" 기능을 사용합니다

## 📝 라이선스

MIT License

## 🤝 기여

버그 리포트 및 기능 제안은 Issues를 통해 제출해주세요.

## 📞 지원

질문이 있으신 경우:
1. [Streamlit 문서](https://docs.streamlit.io/)
2. [DART API 문서](https://opendart.fss.or.kr/)
3. GitHub Issues
