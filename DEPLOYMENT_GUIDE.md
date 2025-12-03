# Streamlit Cloud 배포 가이드

## 📦 배포 준비 완료

다음 파일들이 준비되어 있습니다:
- ✅ `app.py` - 메인 애플리케이션 (로고 & Copyright 포함)
- ✅ `requirements.txt` - Python 의존성
- ✅ `README.md` - 프로젝트 문서
- ✅ `.streamlit/config.toml` - Streamlit 설정
- ✅ `assets/logo_icon.png` - ENVELOPS 로고

## 🚀 Streamlit Cloud 배포 단계

### 1단계: GitHub 저장소 생성 및 푸시

```bash
# Git 초기화 (아직 안 했다면)
cd C:\Users\splx\Documents\SolarFlow_V1.1\Microgrid
git init

# .gitignore 생성 (필요시)
echo "__pycache__/" > .gitignore
echo "*.pyc" >> .gitignore
echo ".DS_Store" >> .gitignore

# 파일 추가
git add .
git commit -m "Initial commit: Ethiopia APV Financial Model v2.0 with ENVELOPS branding"

# GitHub에 푸시 (저장소 URL 필요)
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

### 2단계: Streamlit Community Cloud 설정

1. **Streamlit Cloud 접속**
   - 웹사이트: https://share.streamlit.io
   - GitHub 계정으로 로그인

2. **New app 클릭**
   - 우측 상단 "New app" 버튼 클릭

3. **저장소 설정**
   - **Repository**: 방금 생성한 GitHub 저장소 선택
   - **Branch**: `main` (또는 사용 중인 브랜치)
   - **Main file path**: `app.py`
   
4. **Advanced settings** (선택사항)
   - Python version: 3.10
   - Custom subdomain: 원하는 URL 설정 가능

5. **Deploy!** 클릭
   - 배포 시작 (보통 2-3분 소요)
   - 진행 상황을 실시간으로 볼 수 있음

### 3단계: 배포 완료

배포가 완료되면:
- **URL**: `https://your-app-name.streamlit.app`
- **자동 업데이트**: GitHub에 푸시하면 자동으로 재배포
- **상태 확인**: Streamlit Cloud 대시보드에서 모니터링

## 🔧 배포 후 확인사항

- [ ] 앱이 정상적으로 로드되는지 확인
- [ ] ENVELOPS 로고가 표시되는지 확인
- [ ] Copyright 푸터가 하단에 표시되는지 확인
- [ ] 모든 7개 비즈니스 모델이 작동하는지 테스트
- [ ] Degradation Curves 차트가 렌더링되는지 확인
- [ ] Scenario Comparison이 실행되는지 확인

## 📝 주요 파일 구조

```
Microgrid/
├── app.py                      # 메인 애플리케이션
├── requirements.txt            # Python 패키지
├── README.md                   # 프로젝트 문서
├── .streamlit/
│   └── config.toml            # Streamlit 설정
└── assets/
    └── logo_icon.png          # 회사 로고
```

## 🎯 내부 테스트를 위한 팁

1. **비공개 설정** (선택사항)
   - Streamlit Cloud에서 Settings → Access control
   - "Require viewers to log in" 체크
   - 승인된 이메일 주소만 접근 가능

2. **앱 공유**
   - URL을 내부 테스터들에게 공유
   - 비공개 설정한 경우 이메일 주소 등록 필요

3. **업데이트 방법**
   ```bash
   # 코드 수정 후
   git add .
   git commit -m "Update: description of changes"
   git push
   # Streamlit Cloud가 자동으로 재배포
   ```

4. **로그 확인**
   - Streamlit Cloud 대시보드에서 "Manage app" → "Logs"
   - 에러 발생 시 실시간 로그 확인 가능

## ⚠️ 문제 해결

### 배포 실패 시
1. **requirements.txt 확인**: 모든 패키지가 정확히 명시되어 있는지
2. **Python 버전**: 3.10 이상 권장
3. **로그 확인**: Streamlit Cloud의 로그에서 에러 메시지 확인

### 로고가 표시되지 않을 때
1. `assets/` 폴더가 Git에 포함되었는지 확인
2. GitHub 저장소에서 파일이 푸시되었는지 확인
3. 파일 경로가 정확한지 확인

## 🔗 유용한 링크

- **Streamlit Cloud 문서**: https://docs.streamlit.io/streamlit-community-cloud
- **Streamlit Cloud 대시보드**: https://share.streamlit.io
- **Streamlit 포럼**: https://discuss.streamlit.io

## 📧 지원

배포 과정에서 문제가 발생하면:
1. Streamlit Cloud 로그 확인
2. 개발팀에 로그와 함께 문의
3. GitHub Issues에 문제 기록

---

**준비 완료!** 위 단계를 따라 배포하시면 됩니다. 🚀

**예상 배포 시간**: GitHub 푸시 후 약 2-3분
**예상 URL 형식**: `https://ethiopia-apv-model.streamlit.app`
