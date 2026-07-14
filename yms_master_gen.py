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

# 3. 마스터 프롬프트 설정 (선생님의 완벽한 20가지 원칙 전체 적용)
MASTER_PROMPT = """
AI 영어 내신 출제 시스템 (MASTER PROMPT)

1. 역할(Role)
너는 10년 이상의 경력을 가진 고등학교 영어교사이자 내신 출제 전문가이다.
또한 다음 네 명의 전문가가 하나의 팀처럼 협업하여 문제를 제작한다.
- 출제위원
- 검토위원
- 평가위원
- 품질관리위원
이 네 역할은 내부적으로만 수행하며, 사용자에게는 최종 결과만 출력한다.

2. 목표
고등학교 내신 5등급제 기준 2~3등급 학생을 대상으로 하는 학교 내신형 변형문제를 제작한다.
문제는 실제 학교 중간·기말고사 수준이어야 하며, 학생의 독해력과 문장 분석 능력을 평가하도록 설계한다.
절대로 출제자의 의도를 맞히는 문제를 만들지 않는다.

3. 출제 철학
모든 문제는 학생의 영어 실력을 향상시키는 방향으로 제작한다.
문제를 풀면서 학생이 반드시
- 문장 구조를 분석하고
- 논리를 이해하고
- 문법을 적용하고
- 문맥 속에서 어휘를 해석하도록 만든다.
단순 암기나 운으로 맞힐 수 있는 문제는 만들지 않는다.
항상 다음 질문을 먼저 생각한다.
"이 문제를 통해 학생은 무엇을 배우게 되는가?"

4. 학생 수준
대상은 내신 2~3등급 학생이다.
학생들은
- 기본적인 독해는 가능하지만
- 긴 문장 구조에서 실수를 하며
- 논리 연결을 놓치는 경우가 있고
- 문법을 독해에 적용하는 능력이 부족하다.
문제는 이러한 능력을 평가하도록 만든다.

5. 난이도
쉬움 20% / 보통 60% / 어려움 20%
어려운 문제도 반드시 본문 안에서 근거를 찾을 수 있어야 한다.
추측이나 상식만으로 풀리는 문제는 금지한다.

6. 출제 절차
문제를 만들기 전에 반드시 다음을 분석한다.
글의 주제, 글의 목적, 글의 구조, 문단별 역할, 핵심 문장, 핵심 연결어, 핵심 어휘, 핵심 문법, 학생들이 가장 많이 틀릴 부분, 출제 가능한 포인트
이 분석이 끝난 후에만 문제를 제작한다.

7. 문제 유형
지문당 다음 유형을 제작할 수 있다.
주제, 제목, 요지, 빈칸추론, 내용일치, 내용불일치, 어휘, 어법, 문장삽입, 순서배열, 문장배열, 요약문 완성, 밑줄 의미, 서술형
사용자가 원하는 유형만 제작해도 된다.

8. 문법 출제 원칙
문법은 반드시 본문 안에서 출제한다.
다음 요소만 활용한다: 관계사, 분사, 준동사, 시제, 수동태, 병렬구조, 접속사, 가정법, 대명사, 수일치
문법을 위해 문장을 억지로 수정하지 않는다.

9. 빈칸 출제 원칙
빈칸은 글의 핵심 논리를 묻는다.
단순 어휘 암기가 아니라 글 전체의 흐름을 이해해야 풀 수 있도록 제작한다.

10. 어휘 출제 원칙
문맥상 의미를 평가한다.
동의어·반의어는 문맥 안에서 판단하도록 만든다.

11. 오답 제작 원칙
오답은 반드시 그럴듯해야 한다.
다음 유형을 활용한다: 일부만 맞는 내용, 논리 오류, 인과관계 오류, 지시어 오류, 문법 오류, 문맥상 의미 오류
말이 되지 않는 오답은 금지한다.
모든 오답에는 틀린 이유가 존재해야 한다.

12. 출제 포인트 중복 금지
같은 문장을 여러 문제에서 사용할 수는 있다. 하지만 같은 출제 포인트를 반복해서는 안 된다.
예를 들어 어법 문제로 사용한 문장은 다른 문제에서는 내용 이해나 논리 이해를 평가하도록 한다.

13. 시험지 구성 원칙
시험 전체를 하나의 평가 도구로 설계한다.
문항은 지문 전체에 고르게 분포하도록 한다.
도입, 전개, 예시, 결론을 균형 있게 활용한다.

14. 정답 번호 배치
정답 번호는 특정 번호에 편중되지 않도록 균형 있게 배치한다.

15. 서술형
서술형에는 반드시 모범답안, 채점 기준, 부분점수 기준을 함께 작성한다.

16. 해설 작성
모든 문제에는 정답, 정답 근거, 오답 분석, 본문 근거, 학생들이 자주 하는 실수를 작성한다.

17. 내부 검토 시스템
- 출제위원: 출제 의도를 먼저 정하고 문제를 제작한다.
- 검토위원: 정답이 하나뿐인가, 오답도 정답이 될 가능성은 없는가, 문장이 애매하지 않은가, 본문 근거가 충분한가 확인한다.
- 평가위원: 난이도 균형, 유형 균형, 시간 배분, 출제 포인트 중복 여부 확인한다.
- 품질관리위원: 오탈자, 번호 오류, 해설 오류, 문체 일관성, 출력 형식 확인한다.
이 모든 과정은 내부적으로 수행하며, 사용자에게는 최종 결과만 출력한다.

18. AI 자가 검토
최종 출력 전에 반드시 다음을 확인한다.
□ 정답은 하나뿐인가
□ 오답이 충분히 그럴듯한가
□ 본문 근거가 존재하는가
□ 내신 2~3등급 수준인가
□ 억지 함정은 없는가
□ 문법 오류는 없는가
□ 출제 포인트가 중복되지 않았는가
□ 학생의 사고력을 평가하는가
기준을 만족하지 못하면 수정 후 최종 출력한다.

19. 출력 형식
제시된 JSON 데이터 스키마(형식)에 맞추어 문제, 보기, 정답, 출제의도, 해설, 오답분석 등을 빠짐없이 기입한다.

20. 절대 원칙
원문에 없는 내용을 근거로 문제를 만들지 않는다.
모든 정답은 본문에서 확인 가능해야 한다.
문제를 어렵게 만드는 것이 아니라 사고 과정을 깊게 만든다.
학생이 문제를 풀면서 영어 실력이 향상되도록 설계한다.
최종 결과물은 실제 고등학교 중간·기말고사에 바로 사용할 수 있는 수준의 완성도를 목표로 한다.
"""

def generate_exam_question(passage: str, q_type: str, difficulty: str):
    """
    지문과 조건을 받아 Gemini API를 통해 완벽한 형태의 변형 문제를 생성합니다.
    """
    prompt = f"""
    아래 제공된 [원문 지문]을 철저히 분석한 뒤, '{q_type}' 유형의 문제를 '{difficulty}' 난이도로 출제하시오.
    반드시 마스터 프롬프트의 4단계 검토(출제->검토->평가->품질관리)를 스스로 거친 후, 오류가 없는 최종 결과물만 반환하시오.
    
    [원문 지문]
    {passage}
    """
    
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
                    st.markdown(f"**1. {parsed_result['question_text']}**")
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
                # TAB 2: 출력용 미리보기 (실제 전국연합학력평가 포맷 적용)
                # ==========================================
                with tab2:
                    st.info("💡 아래 [출력하기] 버튼을 누르면 실제 모의고사 양식으로 깔끔하게 인쇄할 수 있습니다.")
                    
                    # 출력용 보기 HTML 텍스트 생성
                    options_html = ""
                    for i, opt in enumerate(parsed_result['options']):
                        num = circle_nums[i] if i < 5 else f"{i+1}."
                        clean_opt = opt.lstrip("①②③④⑤12345. ")
                        options_html += f"<div class='option-item'><span class='opt-num'>{num}</span> {clean_opt}</div>"
                    
                    # 완벽하게 격리된 HTML 구성 (수능/모의고사 전용 CSS 스타일 포함)
                    print_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <meta charset="utf-8">
                    <!-- 수능용 바탕체 구현을 위한 구글 폰트 로드 -->
                    <link rel="preconnect" href="https://fonts.googleapis.com">
                    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
                    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700;900&display=swap" rel="stylesheet">
                    <style>
                        body {{ background-color: #f0f2f6; margin: 0; padding: 20px; }}
                        .paper {{ 
                            background-color: white; color: black; 
                            width: 210mm; min-height: 297mm; 
                            padding: 20mm; margin: 0 auto; 
                            box-shadow: 0 4px 8px rgba(0,0,0,0.1); 
                            box-sizing: border-box;
                            font-family: 'Times New Roman', 'Noto Serif KR', Batang, serif;
                        }}
                        /* 수능/모의고사 스타일 헤더 */
                        .header {{
                            border-bottom: 2.5px solid black;
                            padding-bottom: 12px;
                            margin-bottom: 30px;
                            text-align: center;
                            position: relative;
                            font-family: 'Noto Serif KR', Batang, serif;
                        }}
                        .period {{ position: absolute; left: 0; top: 0; font-size: 11pt; font-weight: 700; }}
                        .grade {{ position: absolute; right: 0; top: 0; font-size: 11pt; font-weight: 700; }}
                        .exam-title {{ font-size: 12pt; font-weight: 700; letter-spacing: 1px; }}
                        .subject {{ font-size: 24pt; font-weight: 900; margin-top: 8px; letter-spacing: 8px; }}
                        
                        /* 문제 및 지문 영역 */
                        .question-row {{ font-size: 12.5pt; font-weight: 700; margin-bottom: 15px; font-family: 'Noto Serif KR', Batang, serif; display: flex; align-items: flex-start; }}
                        .q-num {{ font-size: 15pt; margin-right: 6px; }}
                        .passage {{ 
                            font-size: 11.5pt; 
                            line-height: 1.65; 
                            margin-bottom: 25px; 
                            text-align: justify; 
                            word-break: keep-all;
                        }}
                        
                        /* 보기 영역 */
                        .options {{ font-size: 11.5pt; line-height: 1.8; }}
                        .option-item {{ margin-bottom: 6px; display: flex; align-items: flex-start; }}
                        .opt-num {{ margin-right: 8px; font-family: 'Noto Serif KR', Batang, serif; }}

                        /* 하단 페이지 번호 */
                        .footer {{ text-align: center; margin-top: 60px; font-size: 12pt; font-family: 'Noto Serif KR', Batang, serif; }}

                        /* 출력 버튼 디자인 */
                        .print-btn {{ display: block; margin: 0 auto 20px auto; padding: 12px 30px; font-size: 16px; font-weight: bold; color: white; background-color: #ff4b4b; border: none; border-radius: 5px; cursor: pointer; transition: 0.3s; }}
                        .print-btn:hover {{ background-color: #ff3333; box-shadow: 0 2px 5px rgba(0,0,0,0.2); }}
                        
                        /* 실제 종이 인쇄 시 적용되는 설정 */
                        @media print {{
                            body {{ background-color: white; padding: 0; }}
                            .paper {{ box-shadow: none; width: 100%; min-height: auto; padding: 0; margin: 0; }}
                            .print-btn {{ display: none; }}
                        }}
                    </style>
                    </head>
                    <body>
                        <button class="print-btn" onclick="window.print()">🖨️ 이 문제 출력하기</button>
                        <div class="paper">
                            <!-- 실제 모의고사 헤더 부분 -->
                            <div class="header">
                                <div class="period">제 3 교시</div>
                                <div class="exam-title">전국연합학력평가 변형문제지</div>
                                <div class="subject">영어 영역</div>
                                <div class="grade">고 2</div>
                            </div>
                            
                            <!-- 문제 영역 -->
                            <div class="question-row">
                                <span class="q-num">1.</span> <span>{parsed_result['question_text']}</span>
                            </div>
                            <div class="passage">{passage_html}</div>
                            
                            <!-- 보기 영역 -->
                            <div class="options">{options_html}</div>
                            
                            <!-- 하단 페이지 번호 -->
                            <div class="footer">- 1 -</div>
                        </div>
                    </body>
                    </html>
                    """
                    # Streamlit의 components.html을 사용하여 출력 전용 격리 공간 생성
                    st.components.v1.html(print_html, height=1000, scrolling=True)
                    
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
