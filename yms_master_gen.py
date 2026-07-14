import os
import json
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. API 키 설정 (하드코딩 방식)
api_key = "AQ.Ab8RN6KvtMi5trvzk5__MPYLg2xmsReIXQfgu0LANXc2vQ74xA"
client = genai.Client(api_key=api_key)

# 2. 결과물 출력 형식 정의 (JSON 구조 강제화)
class QuestionResponse(BaseModel):
    question_type: str = Field(description="문제 유형 (예: 빈칸추론)")
    difficulty: str = Field(description="난이도 (쉬움/보통/어려움)")
    question_text: str = Field(description="학생에게 주어지는 발문 (예: 다음 빈칸에 들어갈 말로 가장 적절한 것은?)")
    passage: str = Field(description="지문 원문 (빈칸 추론의 경우 빈칸이 뚫려 있어야 함)")
    options: list[str] = Field(description="1번부터 5번까지의 보기 리스트")
    correct_answer: int = Field(description="정답 번호 (1~5 사이의 정수)")
    intent: str = Field(description="출제 의도")
    text_evidence: str = Field(description="본문 내 정답의 근거 문장")
    explanation: str = Field(description="정답에 대한 상세한 해설")
    distractor_analysis: str = Field(description="오답 보기들이 왜 오답인지에 대한 분석")
    common_mistakes: str = Field(description="이 문제에서 2~3등급 학생들이 자주 할 수 있는 실수 포인트")

# 3. 마스터 프롬프트 설정
MASTER_PROMPT = """
너는 10년 이상의 경력을 가진 고등학교 영어교사이자 내신 출제 전문가이다.
또한 출제위원, 검토위원, 평가위원, 품질관리위원 네 명의 전문가가 하나의 팀처럼 협업하여 문제를 제작한다.

[목표]
고등학교 내신 5등급제 기준 2~3등급 학생을 대상으로 하는 학교 내신형 변형문제를 제작한다.
학생의 독해력과 문장 분석 능력을 평가하도록 설계하며, 단순 암기나 운으로 맞힐 수 있는 문제는 금지한다.

[절대 원칙]
1. 원문에 없는 내용을 근거로 문제를 만들지 않는다.
2. 모든 정답은 본문에서 확인 가능해야 한다.
3. 억지 함정 금지: 논리를 이해해야 풀 수 있도록 제작한다.
4. 오답 제작 원칙: 오답은 본문의 단어를 교묘하게 활용하여 매우 그럴듯하게(매력도 높게) 만들어야 하며, 모든 오답에는 틀린 이유가 존재해야 한다.
"""

def generate_exam_question(passage: str, q_type: str, difficulty: str):
    """
    지문과 조건을 받아 Gemini API를 통해 완벽한 형태의 변형 문제를 생성합니다.
    """
    prompt = f"""
    아래 제공된 [원문 지문]을 철저히 분석한 뒤, '{q_type}' 유형의 문제를 '{difficulty}' 난이도로 출제하시오.
    반드시 4단계 검토(출제->검토->평가->품질관리)를 스스로 거친 후, 오류가 없는 최종 결과물만 반환하시오.
    
    [원문 지문]
    {passage}
    """
    
    # 모델 이름을 현재 확실하게 지원되는 gemini-2.5-flash-preview-09-2025 로 변경합니다.
    response = client.models.generate_content(
        model='gemini-2.5-flash-preview-09-2025',
        contents=[MASTER_PROMPT, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QuestionResponse,
            temperature=0.2, 
        ),
    )
    
    return response.text

# 4. Streamlit 웹 앱 UI 구성
st.set_page_config(page_title="AI 모의고사 출제 엔진", page_icon="🏫", layout="wide")

st.title("🏫 AI 모의고사 변형 문제 출제 엔진")
st.markdown("영어 지문을 입력하고 옵션을 선택하면 AI 위원회가 완벽한 문제를 출제해 줍니다.")

# 지문 입력 영역
user_passage = st.text_area("📚 변형 문제를 만들 영어 지문을 붙여넣으세요:", height=200)

# 옵션 선택 영역
col1, col2 = st.columns(2)
with col1:
    selected_type = st.selectbox(
        "📝 원하는 문제 유형을 선택하세요", 
        ["빈칸추론", "주제", "제목", "요지", "어법", "어휘", "문장삽입", "순서배열", "내용일치"]
    )
with col2:
    selected_diff = st.selectbox(
        "🔥 난이도를 선택하세요", 
        ["보통", "쉬움", "어려움"]
    )

st.divider()

# 출제 버튼 및 결과 화면
if st.button("🚀 문제 출제 시작", type="primary"):
    if not user_passage.strip():
        st.warning("⚠️ 지문을 먼저 입력해주세요!")
    else:
        with st.spinner(f"AI 위원회(출제/검토/평가/품질)가 [{selected_type} / {selected_diff}] 문제를 분석 및 출제 중입니다. 잠시만 기다려주세요..."):
            try:
                # 엔진 가동
                result_json_string = generate_exam_question(user_passage, selected_type, selected_diff)
                parsed_result = json.loads(result_json_string)
                
                st.success("🎉 문제 출제가 완료되었습니다!")
                
                # 결과 UI 예쁘게 배치
                st.subheader("💡 생성된 문제")
                st.markdown(f"**Q. {parsed_result['question_text']}**")
                
                st.info(parsed_result['passage'])
                
                for i, opt in enumerate(parsed_result['options'], 1):
                    st.markdown(f"①②③④⑤[{i-1}] {opt}" if i <= 5 else f"**{i}**. {opt}") # 간단한 번호 포매팅
                
                st.write("") # 빈 줄
                
                with st.expander("✅ 정답 및 AI 해설 위원회 리포트 보기"):
                    st.markdown(f"**📍 정답:** {parsed_result['correct_answer']}번")
                    st.markdown(f"**🎯 출제 의도:** {parsed_result['intent']}")
                    st.markdown(f"**🔎 본문 근거:** {parsed_result['text_evidence']}")
                    st.markdown(f"**📖 상세 해설:** {parsed_result['explanation']}")
                    st.markdown(f"**🛑 오답 분석:** {parsed_result['distractor_analysis']}")
                    st.markdown(f"**⚠️ 학생들의 잦은 실수:** {parsed_result['common_mistakes']}")
                    
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
