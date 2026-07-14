import os
import json
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. API 키 설정 (하드코딩 방식)
api_key = "AQ.Ab8RN6KvtMi5trvzk5__MPYLg2xmsReIXQfgu0LANXc2vQ74xA"
client = genai.Client(api_key=api_key)

# 2. 결과물 출력 형식 정의 (JSON 구조 강제화 - 서술형 추가)
# [기본 모드] 해설이 모두 포함된 전체 구조
class QuestionResponse(BaseModel):
    # 객관식 항목
    question_type: str = Field(description="문제 유형 (예: 빈칸추론)")
    difficulty: str = Field(description="난이도 (쉬움/보통/어려움)")
    question_text: str = Field(description="학생에게 주어지는 발문 (예: 1. 다음 빈칸에 들어갈 말로 가장 적절한 것은?)")
    passage: str = Field(description="지문 원문 (빈칸 추론의 경우 빈칸이 뚫려 있어야 함)")
    options: list[str] = Field(description="1번부터 5번까지의 보기 리스트")
    correct_answer: int = Field(description="정답 번호 (1~5 사이의 정수)")
    intent: str = Field(description="출제 의도")
    text_evidence: str = Field(description="본문 내 정답의 근거 문장")
    explanation: str = Field(description="정답에 대한 상세 해설")
    distractor_analysis: str = Field(description="오답 보기들이 왜 오답인지에 대한 분석")
    common_mistakes: str = Field(description="이 문제에서 2~3등급 학생들이 자주 할 수 있는 실수 포인트")
    
    # 서술형 항목 (핵심 문장 단어 배열)
    sa_question_text: str = Field(description="서술형 발문 (예: 2. 다음 우리말 해석에 맞게 <보기>의 단어들을 바르게 배열하여 문장을 완성하시오.)")
    sa_korean_meaning: str = Field(description="서술형 정답이 되는 핵심 문장의 우리말 해석")
    sa_given_words: list[str] = Field(description="무작위로 섞인 영어 단어 리스트 (정답 문장을 구성하는 단어들)")
    sa_answer: str = Field(description="서술형 정답 (완성된 영어 문장)")
    sa_scoring_criteria: str = Field(description="서술형 채점 기준 (예: 철자 틀림 -1점, 단어 누락 0점 등)")

# [고속 모드] 해설을 생략하여 속도를 극대화한 구조
class FastQuestionResponse(BaseModel):
    question_type: str = Field(description="문제 유형")
    difficulty: str = Field(description="난이도")
    question_text: str = Field(description="객관식 발문")
    passage: str = Field(description="지문 원문")
    options: list[str] = Field(description="보기 리스트")
    correct_answer: int = Field(description="정답 번호")
    sa_question_text: str = Field(description="서술형 발문")
    sa_korean_meaning: str = Field(description="서술형 우리말 해석")
    sa_given_words: list[str] = Field(description="섞인 영어 단어 리스트")
    sa_answer: str = Field(description="서술형 정답 문장")

# 3. 마스터 프롬프트 설정 (서술형 세트 출제 지시 추가)
MASTER_PROMPT = """
AI 영어 내신 출제 시스템 (MASTER PROMPT)

1. 역할(Role)
너는 10년 이상의 경력을 가진 고등학교 영어교사이자 내신 출제 전문가이다.
또한 출제위원, 검토위원, 평가위원, 품질관리위원 네 명의 전문가가 협업하여 문제를 제작한다.

2. 목표
고등학교 내신 5등급제 기준 2~3등급 학생을 대상으로 하는 학교 내신형 변형문제를 제작한다.
문제는 실제 학교 중간·기말고사 수준이어야 하며, 학생의 독해력과 문장 분석 능력을 평가하도록 설계한다.

3. 출제 철학
모든 문제는 학생의 영어 실력을 향상시키는 방향으로 제작한다. 단순 암기나 운으로 맞힐 수 있는 문제는 금지한다.

4. 학생 수준
대상은 내신 2~3등급 학생이다. 긴 문장 구조에서 실수를 하며 논리 연결을 놓치는 경우가 있다.

5. 난이도
어려운 문제도 반드시 본문 안에서 근거를 찾을 수 있어야 한다. 추측이나 상식만으로 풀리는 문제는 금지한다.

6. 출제 절차
지문을 철저히 분석하여 글의 주제, 핵심 문법, 학생들이 가장 많이 틀릴 부분을 도출한 뒤 문제를 제작한다.

7~12. 객관식 출제 원칙
문법은 본문 안에서 출제하고, 빈칸은 글의 핵심 논리를 묻는다. 오답은 매우 그럴듯하게 구성해야 한다. 

13~18. 검토 및 해설 작성 원칙
정답 근거와 오답 분석을 명확히 하고, 학생들이 자주 하는 실수를 짚어준다. 검토를 통해 억지 함정을 배제한다.

[⭐️ 19. 1지문 2문항 출제 절대 원칙 (매우 중요)]
사용자가 요청한 '객관식 문제' 1개와 더불어, 지문의 핵심 주제나 주요 어법이 담긴 가장 중요한 문장을 하나 발췌하여 **'서술형 문제(주어진 단어 배열형)' 1개를 무조건 세트로 함께 출제**한다. 
- 서술형은 주어진 우리말 해석을 보고, 무작위로 섞인 영어 단어(sa_given_words)들을 올바르게 배열하여 문장을 완성하는 형태이다.
- sa_given_words 리스트의 단어들은 순서가 유추되지 않도록 완전히 뒤섞여 있어야 한다.

20. 출력 형식
제시된 JSON 데이터 스키마(형식)에 맞추어 객관식과 서술형 항목을 모두 빠짐없이 기입한다.
"""

def generate_exam_question(passage: str, q_type: str, difficulty: str, is_fast_mode: bool):
    """
    지문과 조건을 받아 Gemini API를 통해 완벽한 형태의 변형 문제를 생성합니다.
    """
    prompt = f"""
    아래 제공된 [원문 지문]을 철저히 분석한 뒤, '{q_type}' 유형의 객관식 문제 1개와 핵심 문장 배열 서술형 1개를 '{difficulty}' 난이도로 세트 출제하시오.
    반드시 마스터 프롬프트의 4단계 검토를 스스로 거친 후, 오류가 없는 최종 결과물만 반환하시오.
    
    [원문 지문]
    {passage}
    """
    
    if is_fast_mode:
        prompt += "\n\n[특별 지시사항] 사용자가 '고속 출제 모드'를 요청했습니다. 해설, 출제 의도, 오답 분석 등은 생략하고 '객관식 문제/정답'과 '서술형 문제/정답'만 신속히 반환하시오."
        target_schema = FastQuestionResponse
    else:
        target_schema = QuestionResponse

    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[MASTER_PROMPT, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=target_schema,
            temperature=0.2, 
        ),
    )
    
    return response.text

# 4. Streamlit 웹 앱 UI 구성
st.set_page_config(page_title="AI 모의고사 출제 엔진", page_icon="🏫", layout="wide")

st.title("🏫 AI 모의고사 변형 문제 출제 엔진")
st.markdown("영어 지문을 입력하고 옵션을 선택하면 AI 위원회가 **객관식 1문항 + 서술형 1문항**을 완벽하게 출제해 줍니다.")

# 지문 입력 영역
user_passage = st.text_area("📚 변형 문제를 만들 영어 지문을 붙여넣으세요:", height=200)

# 옵션 선택 영역
col1, col2 = st.columns(2)
with col1:
    selected_type = st.selectbox(
        "📝 원하는 객관식 문제 유형을 선택하세요", 
        ["빈칸추론", "주제", "제목", "요지", "어법", "어휘", "문장삽입", "순서배열", "내용일치"]
    )
with col2:
    selected_diff = st.selectbox(
        "🔥 난이도를 선택하세요", 
        ["보통", "쉬움", "어려움"]
    )

st.divider()

fast_mode = st.toggle("⚡ 고속 출제 모드 (상세 해설 및 분석 생략으로 출제 속도 2~3배 향상)", value=False)

# 출제 버튼 및 결과 화면
if st.button("🚀 1지문 2문항 세트 출제 시작", type="primary"):
    if not user_passage.strip():
        st.warning("⚠️ 지문을 먼저 입력해주세요!")
    else:
        with st.spinner(f"AI 위원회가 [{selected_type} + 서술형] 세트를 분석 및 출제 중입니다. 잠시만 기다려주세요..."):
            try:
                # 엔진 가동
                result_json_string = generate_exam_question(user_passage, selected_type, selected_diff, fast_mode)
                parsed_result = json.loads(result_json_string)
                
                st.success("🎉 문제 출제가 완료되었습니다!")
                
                tab1, tab2, tab3 = st.tabs(["💡 생성된 문제 (웹 뷰)", "🖨️ 시험지 출력", "🖨️ 해설지 출력"])
                
                passage_html = parsed_result['passage'].replace('\n', '<br>')
                circle_nums = ["①", "②", "③", "④", "⑤"]
                
                # ==========================================
                # TAB 1: 웹 뷰 (해설 포함)
                # ==========================================
                with tab1:
                    st.subheader("💡 생성된 문제")
                    
                    # 1. 객관식 문제
                    st.markdown(f"**1. {parsed_result['question_text']}**")
                    st.write("")
                    
                    st.markdown(f"""
                    <div style="border: 1.5px solid #000; padding: 25px; margin-bottom: 20px; font-family: 'Times New Roman', Batang, serif; font-size: 17px; line-height: 1.8; background-color: #ffffff; color: #000000; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                        {passage_html}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for i, opt in enumerate(parsed_result['options']):
                        num = circle_nums[i] if i < 5 else f"{i+1}."
                        clean_opt = opt.lstrip("①②③④⑤12345. ")
                        st.markdown(f"<span style='font-size: 16px;'>{num} {clean_opt}</span>", unsafe_allow_html=True)
                    
                    st.write("")
                    st.markdown("---")
                    
                    # 2. 서술형 문제
                    st.markdown(f"**2. {parsed_result['sa_question_text']}**")
                    st.markdown(f"**[우리말 해석]** {parsed_result['sa_korean_meaning']}")
                    st.markdown(f"""
                    <div style='border: 1px solid #ccc; padding: 15px; text-align: center; background-color: #f9f9f9; border-radius: 5px; margin: 15px 0;'>
                        <strong>&lt; 보 기 &gt;</strong><br><br>
                        <span style='font-size: 18px;'>{' / '.join(parsed_result['sa_given_words'])}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.write("")
                    
                    # 해설 영역
                    if fast_mode:
                        with st.expander("✅ 정답 확인하기"):
                            st.markdown("### [객관식]")
                            st.markdown(f"**📍 정답:** {parsed_result['correct_answer']}번")
                            st.markdown("### [서술형]")
                            st.markdown(f"**📍 정답:** {parsed_result['sa_answer']}")
                            st.info("⚡ 고속 출제 모드에서는 상세 해설과 오답 분석이 제공되지 않습니다.")
                    else:
                        with st.expander("✅ 정답 및 AI 해설 위원회 리포트 보기"):
                            st.markdown("### 📝 [객관식] 분석 리포트")
                            st.markdown(f"**📍 정답:** {parsed_result['correct_answer']}번")
                            st.markdown(f"**🎯 출제 의도:** {parsed_result['intent']}")
                            st.markdown(f"**🔎 본문 근거:** {parsed_result['text_evidence']}")
                            st.markdown(f"**📖 상세 해설:** {parsed_result['explanation']}")
                            st.markdown(f"**🛑 오답 분석:** {parsed_result['distractor_analysis']}")
                            st.markdown(f"**⚠️ 학생들의 잦은 실수:** {parsed_result['common_mistakes']}")
                            st.markdown("---")
                            st.markdown("### ✍️ [서술형] 분석 리포트")
                            st.markdown(f"**📍 정답:** {parsed_result['sa_answer']}")
                            st.markdown(f"**📋 채점 기준:** {parsed_result['sa_scoring_criteria']}")

                # ==========================================
                # TAB 2: 출력용 미리보기 (시험지 양식)
                # ==========================================
                with tab2:
                    st.info("💡 아래 [출력하기] 버튼을 누르면 실제 모의고사 양식으로 깔끔하게 인쇄할 수 있습니다.")
                    
                    options_html = ""
                    for i, opt in enumerate(parsed_result['options']):
                        num = circle_nums[i] if i < 5 else f"{i+1}."
                        clean_opt = opt.lstrip("①②③④⑤12345. ")
                        options_html += f"<div class='option-item'><span class='opt-num'>{num}</span> {clean_opt}</div>"
                    
                    print_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <meta charset="utf-8">
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
                        .header {{
                            border-bottom: 2.5px solid black;
                            padding-bottom: 12px;
                            margin-bottom: 30px;
                            text-align: center;
                            position: relative;
                            font-family: 'Noto Serif KR', Batang, serif;
                        }}
                        .grade {{ position: absolute; right: 0; top: 0; font-size: 11pt; font-weight: 700; text-align: left; line-height: 1.6;}}
                        .exam-title {{ font-size: 13pt; font-weight: 700; letter-spacing: 1px; margin-top: 10px; }}
                        .subject {{ font-size: 24pt; font-weight: 900; margin-top: 8px; letter-spacing: 8px; }}
                        .question-row {{ font-size: 12.5pt; font-weight: 700; margin-bottom: 15px; font-family: 'Noto Serif KR', Batang, serif; display: flex; align-items: flex-start; }}
                        .q-num {{ font-size: 15pt; margin-right: 6px; }}
                        .passage {{ font-size: 11.5pt; line-height: 1.65; margin-bottom: 25px; text-align: justify; word-break: keep-all; }}
                        .options {{ font-size: 11.5pt; line-height: 1.8; margin-bottom: 40px; }}
                        .option-item {{ margin-bottom: 6px; display: flex; align-items: flex-start; }}
                        .opt-num {{ margin-right: 8px; font-family: 'Noto Serif KR', Batang, serif; }}
                        
                        .sa-box {{ border: 1.5px solid #000; padding: 20px; margin: 15px 0 30px 0; text-align: center; font-size: 12pt; font-weight: bold; line-height: 2.0; }}
                        .sa-meaning {{ font-size: 11.5pt; margin-bottom: 10px; }}
                        .sa-answer-line {{ border-bottom: 1px solid #000; width: 100%; height: 30px; margin-top: 20px; }}
                        
                        .footer {{ text-align: center; margin-top: 60px; font-size: 12pt; font-family: 'Noto Serif KR', Batang, serif; }}
                        .print-btn {{ display: block; margin: 0 auto 20px auto; padding: 12px 30px; font-size: 16px; font-weight: bold; color: white; background-color: #ff4b4b; border: none; border-radius: 5px; cursor: pointer; transition: 0.3s; }}
                        .print-btn:hover {{ background-color: #ff3333; }}
                        @media print {{
                            body {{ background-color: white; padding: 0; }}
                            .paper {{ box-shadow: none; width: 100%; min-height: auto; padding: 0; margin: 0; border: none; }}
                            .print-btn {{ display: none; }}
                        }}
                    </style>
                    </head>
                    <body>
                        <button class="print-btn" onclick="window.print()">🖨️ 이 시험지 출력하기</button>
                        <div class="paper">
                            <div class="header">
                                <div class="exam-title">YMS 부송관 모의고사</div>
                                <div class="subject">영어 영역</div>
                                <div class="grade">학년 : ____________<br>교재 : ____________</div>
                            </div>
                            
                            <!-- 객관식 -->
                            <div class="question-row">
                                <span class="q-num">1.</span> <span>{parsed_result['question_text']}</span>
                            </div>
                            <div class="passage">{passage_html}</div>
                            <div class="options">{options_html}</div>
                            
                            <!-- 서술형 -->
                            <div class="question-row">
                                <span class="q-num">2.</span> <span>{parsed_result['sa_question_text']}</span>
                            </div>
                            <div class="sa-meaning"><strong>[해석]</strong> {parsed_result['sa_korean_meaning']}</div>
                            <div class="sa-meaning" style="font-size: 10.5pt; color: #333;">※ &lt;보기&gt;의 단어들을 모두 사용하여 문맥에 맞게 배열하시오.</div>
                            <div class="sa-box">
                                &lt; 보 기 &gt;<br>
                                {' / '.join(parsed_result['sa_given_words'])}
                            </div>
                            <div style="font-weight: bold; font-size: 12pt;">정답 :</div>
                            <div class="sa-answer-line"></div>
                            <div class="sa-answer-line"></div>
                            
                            <div class="footer">- 1 -</div>
                        </div>
                    </body>
                    </html>
                    """
                    st.components.v1.html(print_html, height=1200, scrolling=True)

                # ==========================================
                # TAB 3: 해설지 출력용 미리보기
                # ==========================================
                with tab3:
                    st.info("💡 아래 [출력하기] 버튼을 누르면 정답 및 해설지를 인쇄할 수 있습니다.")
                    
                    if fast_mode:
                        explanation_html = f"""
                        <div class="section-title">📍 [객관식] 1번 정답</div>
                        <div class="content-box"><strong>{parsed_result['correct_answer']}번</strong></div>
                        <div class="section-title">📍 [서술형] 2번 정답</div>
                        <div class="content-box"><strong>{parsed_result['sa_answer']}</strong></div>
                        <div class="content-box" style="color: #666; margin-top: 20px;">※ 고속 출제 모드로 생성되어 상세 해설이 제공되지 않습니다.</div>
                        """
                    else:
                        explanation_html = f"""
                        <div class="section-title">📍 [객관식 1번] 정답</div>
                        <div class="content-box" style="font-size: 14pt;"><strong>{parsed_result['correct_answer']}번</strong></div>
                        
                        <div class="section-title">🎯 출제 의도</div>
                        <div class="content-box">{parsed_result['intent']}</div>
                        
                        <div class="section-title">🔎 본문 근거</div>
                        <div class="content-box">{parsed_result['text_evidence']}</div>
                        
                        <div class="section-title">📖 상세 해설</div>
                        <div class="content-box">{parsed_result['explanation']}</div>
                        
                        <div class="section-title">🛑 오답 분석</div>
                        <div class="content-box">{parsed_result['distractor_analysis']}</div>
                        
                        <div class="section-title">⚠️ 학생들의 잦은 실수</div>
                        <div class="content-box">{parsed_result['common_mistakes']}</div>
                        
                        <hr style="border: 0; border-top: 1px dashed #ccc; margin: 30px 0;">
                        
                        <div class="section-title">📍 [서술형 2번] 정답</div>
                        <div class="content-box" style="font-size: 14pt;"><strong>{parsed_result['sa_answer']}</strong></div>
                        
                        <div class="section-title">📋 채점 기준 및 부분 점수</div>
                        <div class="content-box">{parsed_result['sa_scoring_criteria']}</div>
                        """
                        
                    ans_print_html = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                    <meta charset="utf-8">
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
                            line-height: 1.8;
                            font-size: 11.5pt;
                        }}
                        .header {{ border-bottom: 2.5px solid black; padding-bottom: 12px; margin-bottom: 30px; text-align: center; font-family: 'Noto Serif KR', Batang, serif; }}
                        .exam-title {{ font-size: 13pt; font-weight: 700; letter-spacing: 1px; color: #555; }}
                        .subject {{ font-size: 24pt; font-weight: 900; margin-top: 8px; letter-spacing: 8px; }}
                        .section-title {{ font-weight: bold; font-size: 12.5pt; margin-top: 25px; margin-bottom: 10px; border-left: 5px solid #0056b3; padding-left: 10px; color: #0056b3; }}
                        .content-box {{ padding-left: 15px; text-align: justify; word-break: keep-all; margin-bottom: 10px; }}
                        .print-btn {{ display: block; margin: 0 auto 20px auto; padding: 12px 30px; font-size: 16px; font-weight: bold; color: white; background-color: #0056b3; border: none; border-radius: 5px; cursor: pointer; transition: 0.3s; }}
                        .print-btn:hover {{ background-color: #004494; }}
                        @media print {{
                            body {{ background-color: white; padding: 0; }}
                            .paper {{ box-shadow: none; width: 100%; min-height: auto; padding: 0; margin: 0; border: none; }}
                            .print-btn {{ display: none; }}
                        }}
                    </style>
                    </head>
                    <body>
                        <button class="print-btn" onclick="window.print()">🖨️ 해설지 출력하기</button>
                        <div class="paper">
                            <div class="header">
                                <div class="exam-title">YMS 부송관 모의고사</div>
                                <div class="subject">정답 및 해설</div>
                            </div>
                            {explanation_html}
                        </div>
                    </body>
                    </html>
                    """
                    st.components.v1.html(ans_print_html, height=1200, scrolling=True)

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
