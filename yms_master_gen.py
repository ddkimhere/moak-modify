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
    
    # 사용자가 직접 해결한 3.5-flash 모델명 적용
    response = client.models.generate_content(
        model='gemini-3.5-flash',
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
                
                # 웹 뷰와 인쇄용 미리보기 뷰를 탭(Tab)으로 분리
                tab1, tab2 = st.tabs(["💡 생성된 문제 (웹 뷰)", "🖨️ 미리보기 및 출력"])
                
                # 지문 줄바꿈 처리 및 보기 번호 세팅
                passage_html = parsed_result['passage'].replace('\n', '<br>')
                circle_nums = ["①", "②", "③", "④", "⑤"]
                
                # ==========================================
                # TAB 1: 웹 뷰 (해설 포함)
                # ==========================================
                with tab1:
                    st.subheader("💡 생성된 문제")
                    
                    # 1. 문제 발문 출력
                    st.markdown(f"**{parsed_result['question_text']}**")
                    st.write("") # 빈 줄
                    
                    # 2. 실제 모의고사 시험지 느낌의 지문 박스 디자인 적용
                    st.markdown(f"""
                    <div style="border: 1.5px solid #000; padding: 25px; margin-bottom: 20px; font-family: 'Times New Roman', Batang, serif; font-size: 17px; line-height: 1.8; background-color: #ffffff; color: #000000; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                        {passage_html}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 3. 보기 출력 (중복 번호 방지 로직 적용)
                    for i, opt in enumerate(parsed_result['options']):
                        num = circle_nums[i] if i < 5 else f"{i+1}."
                        # AI가 보기 안에 번호를 섞어 보냈을 경우, 앞의 번호와 공백을 깔끔하게 제거
                        clean_opt = opt.lstrip("①②③④⑤12345. ")
                        st.markdown(f"<span style='font-size: 16px;'>{num} {clean_opt}</span>", unsafe_allow_html=True)
                    
                    st.write("") # 빈 줄
                    
                    with st.expander("✅ 정답 및 AI 해설 위원회 리포트 보기"):
                        st.markdown(f"**📍 정답:** {parsed_result['correct_answer']}번")
                        st.markdown(f"**🎯 출제 의도:** {parsed_result['intent']}")
                        st.markdown(f"**🔎 본문 근거:** {parsed_result['text_evidence']}")
                        st.markdown(f"**📖 상세 해설:** {parsed_result['explanation']}")
                        st.markdown(f"**🛑 오답 분석:** {parsed_result['distractor_analysis']}")
                        st.markdown(f"**⚠️ 학생들의 잦은 실수:** {parsed_result['common_mistakes']}")

                # ==========================================
                # TAB 2: 출력용 미리보기 (iframe 인쇄 기능)
                # ==========================================
                with tab2:
                    st.info("💡 아래 [출력하기] 버튼을 누르면 시험지 형태로 깔끔하게 인쇄할 수 있습니다.")
                    
                    # 출력용 보기 HTML 텍스트 생성
                    options_html = "<br><br>".join([f"{circle_nums[i] if i < 5 else str(i+1)+'.'} {opt.lstrip('①②③④⑤12345. ')}" for i, opt in enumerate(parsed_result['options'])])
                    
                    # 완벽하게 격리된 HTML 구성 (CSS 인쇄 스타일 포함)
                    print_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <style>
                        body {{ background-color: #f0f2f6; font-family: 'Times New Roman', Batang, 'Malgun Gothic', serif; padding: 20px; }}
                        .paper {{ background-color: white; color: black; padding: 40px; margin: 0 auto; max-width: 800px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border: 1px solid #ccc; }}
                        .question {{ font-size: 18px; font-weight: bold; margin-bottom: 20px; }}
                        .passage {{ border: 1.5px solid #000; padding: 25px; margin-bottom: 20px; font-size: 17px; line-height: 1.8; }}
                        .options {{ font-size: 16px; line-height: 1.8; }}
                        .print-btn {{ display: block; margin: 0 auto 20px auto; padding: 10px 30px; font-size: 16px; font-weight: bold; color: white; background-color: #ff4b4b; border: none; border-radius: 5px; cursor: pointer; }}
                        .print-btn:hover {{ background-color: #ff3333; }}
                        @media print {{
                            body {{ background-color: white; padding: 0; }}
                            .paper {{ box-shadow: none; border: none; max-width: 100%; padding: 0; }}
                            .print-btn {{ display: none; }} /* 인쇄 시 버튼은 숨김 처리 */
                        }}
                    </style>
                    </head>
                    <body>
                        <button class="print-btn" onclick="window.print()">🖨️ 이 문제 출력하기</button>
                        <div class="paper">
                            <div class="question">{parsed_result['question_text']}</div>
                            <div class="passage">{passage_html}</div>
                            <div class="options">{options_html}</div>
                        </div>
                    </body>
                    </html>
                    """
                    # Streamlit의 components.html을 사용하여 출력 전용 격리 공간 생성
                    st.components.v1.html(print_html, height=800, scrolling=True)
                    
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
