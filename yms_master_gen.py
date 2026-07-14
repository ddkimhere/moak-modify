import streamlit as st
import google.generativeai as genai

# [설정] 페이지 기본 구성
st.set_page_config(page_title="YMS AI 내신 출제 마스터", layout="wide")
st.title("👨‍🏫 YMS AI 내신 출제 마스터 시스템")

# [사이드바] API 키 입력
api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

# [Master Prompt 정의] - 선생님의 원칙을 그대로 시스템에 이식
SYSTEM_INSTRUCTION = """
1. 역할: 너는 10년 경력의 고등학교 영어교사이자 내신 출제 전문가이다. 
(출제위원, 검토위원, 평가위원, 품질관리위원 4인 팀으로 협업하여 최종 결과만 출력)
2. 목표: 고교 내신 2~3등급 대상, 학교 내신형 변형문제 제작.
3. 철학: 문장 구조 분석, 논리 이해, 문법 적용, 문맥 어휘 해석 능력 평가.
4. 난이도: 쉬움 20%, 보통 60%, 어려움 20%. (근거 없는 추측 금지)
5. 출제 절차: 주제/목적/구조/문단역할/핵심문장/연결어/어휘/문법 분석 후 제작.
6. 출제 원칙: 
- 문법: 관계사, 분사, 준동사, 시제 등 본문 활용.
- 빈칸: 글 전체 흐름을 이해해야 풀 수 있는 핵심 논리.
- 어휘: 문맥상 의미 평가.
- 오답: 그럴듯하게 제작 (논리 오류, 인과관계 오류 등).
7. 시험지 구성: 지문 전체를 평가 도구로 설계.
8. 정답 배치: 특정 번호 편중 금지, 균형 배치.
9. 서술형: 모범답안, 채점기준, 부분점수 기준 필수 포함.
10. 검토 시스템: 출제-검토-평가-품질관리-AI자가검토 과정을 내부적으로 수행 후 결과 출력.
11. 출력 형식: 반드시 아래 형식을 엄수할 것.
【문제 번호】
유형
난이도
문제
보기(①~⑤)
정답
출제 의도
본문 근거
해설
오답 분석
학생들이 자주 하는 실수
(서술형인 경우) 모범답안/채점기준/부분점수 기준
12. 절대 원칙: 원문에 없는 내용으로 출제 금지. 모든 정답은 본문 근거 필수.
"""

# [지문 입력 및 옵션]
passage = st.text_area("지문 본문을 입력하세요:", height=300)
question_types = st.multiselect("출제 유형:", 
    ["주제", "제목", "요지", "빈칸추론", "내용일치", "어법", "문장삽입", "순서배열", "요약문 완성", "서술형"],
    default=["빈칸추론", "어법", "서술형"])

if st.button("전문가 팀 출제 시작"):
    if not api_key:
        st.error("API Key를 입력해주세요.")
    elif not passage:
        st.warning("지문을 입력해주세요.")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-pro', system_instruction=SYSTEM_INSTRUCTION)
            
            with st.spinner("전문가 팀이 지문을 분석하고 문제를 제작 중입니다..."):
                response = model.generate_content(f"다음 지문을 분석하여 {question_types} 유형으로 문제를 제작하라:\n\n{passage}")
                st.markdown("---")
                st.write(response.text)
        except Exception as e:
            st.error(f"오류 발생: {e}")