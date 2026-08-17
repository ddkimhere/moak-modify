# moak-modify

AI 영어 내신 변형문제 생성기입니다.

## HTML / JavaScript 버전

기존 Streamlit 앱(`yms_master_gen.py`)은 그대로 유지하고, 별도의 웹 버전을 함께 제공합니다.

- `index.html` — 웹 화면
- `styles.css` — 화면 스타일
- `app.js` — 지문/문항 설정, 결과 편집, 인쇄
- `api/generate.js` — Gemini API 서버 함수
- `vercel.json` — Vercel 배포 설정

### 배포

Vercel 프로젝트의 Environment Variables에 아래 값을 등록해야 합니다.

```text
GEMINI_API_KEY=본인의_Gemini_API_키
```

API 키는 브라우저 코드에 넣지 않습니다. 웹 화면은 `/api/generate`를 호출하고 서버 함수가 Gemini API를 호출합니다.

### 주요 기능

- 지문 1~20개 입력
- 지문별 문제 유형 복수 선택
- 유형별 문항 수 및 난이도 지정
- 지문당 최대 10문항
- 객관식 정답 번호 균형 배치 및 검증
- 지문 단위 최대 4개 병렬 생성
- 생성 결과 화면에서 직접 수정
- 2단 시험지 인쇄
- 정답 및 해설지 인쇄
- 브라우저 임시 저장(localStorage)
