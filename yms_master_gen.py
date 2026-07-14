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
# 객관식과 서술형을 모두 소화할 수 있는 통합 스키마
class QuestionResponse(BaseModel):
    question_type: str = Field(description="문제 유형 (예: 빈칸추론, 서술형(단어배열))")
    difficulty: str = Field(description="난이도 (쉬움/보통/어려움)")
    question_text: str = Field(description="학생에게 주어지는 발문 (예: 다음 빈칸에 들어갈 말로 가장 적절한 것은?, 또는 우리말에 맞게 배열하시오)")
    passage: str = Field(description="지문 원문 (빈칸 추론의 경우 빈칸이 뚫려 있어야 함)")
    is_subjective: bool = Field(description="이 문제가 서술형인지 여부 (True/False)")
    options: list[str] = Field(description="객관식인 경우 1~5번 보기 리스트. 서술형이면 빈 리스트([])로 둔다.")
    correct_answer: str = Field(description="객관식은 정답 번호(예: '3'), 서술형은 완성된 영작 문장")
    sa_korean_meaning: str = Field(description="[서술형 전용] 영작해야 할 문장의 우리말 해석 (객관식이면 빈 문자열)")
    sa_given_words: list[str] = Field(description="[서술형 전용] 무작위로 섞인 영어 단어 리스트 (객관식이면 빈 리스트)")
    intent: str = Field(description="출제 의도")
    text_evidence: str = Field(description="본문 내 정답의 근거 문장")
    explanation: str = Field(description="정답에 대한 상세한 해설")
    distractor_analysis: str = Field(description="오답 분석 또는 서술형 채점 기준")
    common_mistakes: str = Field(description="학생들이 자주 하는 실수 포인트")

# 3. 마스터 프롬프트 설정
MASTER_PROMPT = """
AI 영어 내신 출제 시스템 (MASTER PROMPT)

1. 역할(Role)
너는 10년 이상의 경력을 가진 고등학교 영어교사이자 내신 출제 전문가이다.

2. 목표
고등학교 내신 5등급제 기준 2~3등급 학생을 대상으로 하는 학교 내신형 변형문제를 1개 제작한다.
학생의 독해력과 문장 분석 능력을 평가하도록 설계하며, 단순 암기나 운으로 맞힐 수 있는 문제는 금지한다.

3. 출제 원칙
- 원문에 없는 내용을 근거로 문제를 만들지 않는다.
- 모든 정답은 본문에서 확인 가능해야 한다.
- 억지 함정 금지: 논리를 이해해야 풀 수 있도록 제작한다.
- 객관식 오답 원칙: 오답은 본문의 단어를 교묘하게 활용하여 매우 그럴듯하게(매력도 높게) 만들어야 한다.

4. 서술형 출제 시 특별 규칙 (사용자가 '서술형(단어배열)'을 요구한 경우)
- is_subjective를 true로 설정한다.
- 지문에서 가장 중요한 핵심 문장(주제문 또는 핵심 어법이 포함된 문장) 1개를 발췌하여 우리말 해석(sa_korean_meaning)을 제공한다.
- 해당 문장을 구성하는 영어 단어들을 순서가 유추되지 않게 완전히 뒤섞어 배열(sa_given_words)로 제공한다.
- 객관식 보기(options)는 비워둔다.
"""

def generate_exam_question(passage: str, q_type: str, difficulty: str):
    """
    지문과 조건을 받아 Gemini API를 통해 한 문항의 변형 문제를 생성합니다.
    """
    prompt = f"""
    아래 제공된 [원문 지문]을 철저히 분석한 뒤, '{q_type}' 유형의 문제를 '{difficulty}' 난이도로 딱 1문제만 출제하시오.
    반드시 스스로 검토를 거친 후, 오류가 없는 최종 결과물만 JSON 형태로 반환하시오.
    
    [원문 지문]
    {passage}
    """
    
    response = client.models.generate_content(
        model='gemini-1.5-flash',
        contents=[MASTER_PROMPT, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QuestionResponse,
            temperature=0.2, 
        ),
    )
    
    return json.loads(response.text)

# 4. Streamlit 웹 앱 UI 구성
st.set_page_config(page_title="AI 모의고사 출제 엔진", page_icon="🏫", layout="wide")

st.title("🏫 AI 모의고사 시험지 빌더")
st.markdown("여러 개의 지문을 입력하여 한 세트의 모의고사 시험지를 만들어보세요!")

# 지문 개수 설정
num_questions = st.number_input("📚 출제할 문항(지문) 개수를 선택하세요", min_value=1, max_value=20, value=2)

st.divider()

# 다중 지문 입력 폼 동적 생성
questions_data = []
for i in range(num_questions):
    st.markdown(f"### 📝 문항 {i+1} 세팅")
    col_q1, col_q2 = st.columns([7, 3])
    with col_q1:
        passage = st.text_area(f"지문 {i+1}", height=150, key=f"passage_{i}")
    with col_q2:
        q_type = st.selectbox(
            f"유형 {i+1}", 
            ["빈칸추론", "주제", "제목", "요지", "어법", "어휘", "문장삽입", "순서배열", "내용일치", "서술형(단어배열)"], 
            key=f"type_{i}"
        )
        q_diff = st.selectbox(f"난이도 {i+1}", ["보통", "쉬움", "어려움"], key=f"diff_{i}")
    questions_data.append({"passage": passage, "type": q_type, "diff": q_diff})
    st.write("")

st.divider()

# 출제 버튼 및 결과 화면
if st.button("🚀 시험지 전체 출제 시작", type="primary"):
    # 입력 검증
    empty_passages = [i+1 for i, q in enumerate(questions_data) if not q['passage'].strip()]
    if empty_passages:
        st.warning(f"⚠️ 문항 {', '.join(map(str, empty_passages))}의 지문이 비어있습니다. 지문을 모두 입력해주세요!")
    else:
        # 프로그레스 바 및 상태 표시
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        all_results = []
        try:
            for i, q in enumerate(questions_data):
                status_text.text(f"문항 {i+1}/{num_questions} 분석 및 출제 중... ({q['type']})")
                
                # API 호출 (개별 문항)
                parsed_result = generate_exam_question(q['passage'], q['type'], q['diff'])
                all_results.append(parsed_result)
                
                progress_bar.progress((i + 1) / num_questions)
                
            status_text.text("🎉 시험지 제작이 완료되었습니다!")
            st.success(f"총 {num_questions}문항 출제가 완료되었습니다!")
            
            # 탭 분리
            tab1, tab2, tab3 = st.tabs(["💡 생성된 문제 확인 (웹 뷰)", "🖨️ 시험지 인쇄 (2단 편집)", "🖨️ 해설지 인쇄"])
            circle_nums = ["①", "②", "③", "④", "⑤"]
            
            # ==========================================
            # TAB 1: 웹 뷰 (순차 렌더링)
            # ==========================================
            with tab1:
                for idx, result in enumerate(all_results):
                    st.subheader(f"💡 문항 {idx+1}")
                    st.markdown(f"**{idx+1}. {result['question_text']}**")
                    
                    passage_html = result['passage'].replace('\n', '<br>')
                    st.markdown(f"""
                    <div style="border: 1.5px solid #000; padding: 25px; margin-bottom: 20px; font-family: 'Times New Roman', Batang, serif; font-size: 17px; line-height: 1.8; background-color: #ffffff; color: #000000;">
                        {passage_html}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if result['is_subjective']:
                        st.markdown(f"**[우리말 해석]** {result['sa_korean_meaning']}")
                        st.markdown(f"""
                        <div style='border: 1px solid #ccc; padding: 15px; text-align: center; background-color: #f9f9f9; border-radius: 5px; margin: 15px 0;'>
                            <strong>&lt; 보 기 &gt;</strong><br><br>
                            <span style='font-size: 18px;'>{' / '.join(result['sa_given_words'])}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        for i, opt in enumerate(result['options']):
                            num = circle_nums[i] if i < 5 else f"{i+1}."
                            clean_opt = opt.lstrip("①②③④⑤12345. ")
                            st.markdown(f"<span style='font-size: 16px;'>{num} {clean_opt}</span>", unsafe_allow_html=True)
                    
                    with st.expander(f"✅ {idx+1}번 정답 및 해설 보기"):
                        st.markdown(f"**📍 정답:** {result['correct_answer']}")
                        st.markdown(f"**🎯 출제 의도:** {result['intent']}")
                        st.markdown(f"**🔎 본문 근거:** {result['text_evidence']}")
                        st.markdown(f"**📖 상세 해설:** {result['explanation']}")
                        st.markdown(f"**🛑 오답 분석 / 채점 기준:** {result['distractor_analysis']}")
                        st.markdown(f"**⚠️ 잦은 실수:** {result['common_mistakes']}")
                    
                    st.write("---")

            # ==========================================
            # TAB 2: 시험지 출력 (2단 편집, CSS 적용)
            # ==========================================
            with tab2:
                st.info("💡 아래 [출력하기] 버튼을 누르면 실제 모의고사 양식(2단)으로 깔끔하게 인쇄할 수 있습니다.")
                
                exam_html_blocks = []
                for idx, result in enumerate(all_results):
                    passage_html = result['passage'].replace('\n', '<br>')
                    
                    if result['is_subjective']:
                        options_html = f"""
                        <div class="sa-meaning"><strong>[해석]</strong> {result['sa_korean_meaning']}</div>
                        <div class="sa-box">
                            &lt; 보 기 &gt;<br>
                            {' / '.join(result['sa_given_words'])}
                        </div>
                        <div class="sa-answer-line"></div>
                        <div class="sa-answer-line"></div>
                        """
                    else:
                        opt_list = []
                        for i, opt in enumerate(result['options']):
                            num = circle_nums[i] if i < 5 else f"{i+1}."
                            clean_opt = opt.lstrip("①②③④⑤12345. ")
                            opt_list.append(f"<div class='option-item'><span class='opt-num'>{num}</span> {clean_opt}</div>")
                        options_html = "".join(opt_list)
                    
                    block = f"""
                    <div class="question-block">
                        <div class="question-row">
                            <span class="q-num">{idx+1}.</span> <span>{result['question_text']}</span>
                        </div>
                        <div class="passage">{passage_html}</div>
                        <div class="options">{options_html}</div>
                    </div>
                    """
                    exam_html_blocks.append(block)
                
                all_questions_html = "".join(exam_html_blocks)
                
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
                        padding: 15mm 20mm; margin: 0 auto; 
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
                        /* 헤더는 2단 다단을 무시하고 전체 폭을 차지하도록 설정 */
                        column-span: all;
                    }}
                    .grade {{ position: absolute; right: 0; top: 0; font-size: 11pt; font-weight: 700; text-align: left; line-height: 1.6;}}
                    .exam-title {{ font-size: 24pt; font-weight: 900; margin-top: 8px; letter-spacing: 5px; }}
                    
                    /* 2단 편집 레이아웃 */
                    .content-columns {{
                        column-count: 2;
                        column-gap: 15mm;
                        column-rule: 1px solid #ccc;
                    }}
                    
                    /* 문항 블록이 단 사이에서 쪼개지지 않도록 설정 */
                    .question-block {{
                        break-inside: avoid;
                        page-break-inside: avoid;
                        margin-bottom: 40px;
                        display: inline-block; /* 쪼개짐 방지 강제화 */
                        width: 100%;
                    }}

                    .question-row {{ font-size: 11.5pt; font-weight: 700; margin-bottom: 15px; display: flex; align-items: flex-start; }}
                    .q-num {{ font-size: 13pt; margin-right: 6px; }}
                    .passage {{ 
                        border: 1.5px solid #000;
                        padding: 15px; 
                        font-size: 10.5pt; 
                        line-height: 1.65; 
                        margin-bottom: 15px; 
                        text-align: justify; 
                        word-break: keep-all;
                    }}
                    
                    .options {{ font-size: 10.5pt; line-height: 1.8; }}
                    .option-item {{ margin-bottom: 4px; display: flex; align-items: flex-start; }}
                    .opt-num {{ margin-right: 8px; }}

                    /* 서술형 전용 CSS */
                    .sa-box {{ border: 1.5px solid #000; padding: 15px; margin: 15px 0; text-align: center; font-size: 11pt; font-weight: bold; line-height: 1.8; }}
                    .sa-meaning {{ font-size: 10.5pt; margin-bottom: 10px; }}
                    .sa-answer-line {{ border-bottom: 1px solid #000; width: 100%; height: 30px; margin-top: 20px; }}

                    .footer {{ text-align: center; margin-top: 60px; font-size: 12pt; font-family: 'Noto Serif KR', Batang, serif; column-span: all; }}
                    .print-btn {{ display: block; margin: 0 auto 20px auto; padding: 12px 30px; font-size: 16px; font-weight: bold; color: white; background-color: #ff4b4b; border: none; border-radius: 5px; cursor: pointer; }}
                    .print-btn:hover {{ background-color: #ff3333; }}
                    
                    @media print {{
                        body {{ background-color: white; padding: 0; }}
                        .paper {{ box-shadow: none; width: 100%; padding: 0; margin: 0; border: none; }}
                        .print-btn {{ display: none; }}
                    }}
                </style>
                </head>
                <body>
                    <button class="print-btn" onclick="window.print()">🖨️ 시험지 출력하기</button>
                    <div class="paper">
                        <div class="header">
                            <div class="exam-title">YMS 부송관 모의고사</div>
                            <div class="grade">학년 : ____________<br>교재 : ____________</div>
                        </div>
                        
                        <div class="content-columns">
                            {all_questions_html}
                        </div>
                        
                        <div class="footer">- 1 -</div>
                    </div>
                </body>
                </html>
                """
                st.components.v1.html(print_html, height=1200, scrolling=True)

            # ==========================================
            # TAB 3: 해설지 출력
            # ==========================================
            with tab3:
                st.info("💡 아래 [출력하기] 버튼을 누르면 정답 및 해설지만 인쇄할 수 있습니다.")
                
                ans_html_blocks = []
                for idx, result in enumerate(all_results):
                    block = f"""
                    <div class="section-title">📍 [{idx+1}번] 정답</div>
                    <div class="content-box" style="font-size: 14pt;"><strong>{result['correct_answer']}</strong></div>
                    
                    <div class="section-title">🎯 출제 의도</div>
                    <div class="content-box">{result['intent']}</div>
                    
                    <div class="section-title">🔎 본문 근거</div>
                    <div class="content-box">{result['text_evidence']}</div>
                    
                    <div class="section-title">📖 상세 해설</div>
                    <div class="content-box">{result['explanation']}</div>
                    
                    <div class="section-title">🛑 오답 분석 / 채점 기준</div>
                    <div class="content-box">{result['distractor_analysis']}</div>
                    
                    <div class="section-title">⚠️ 학생들의 잦은 실수</div>
                    <div class="content-box">{result['common_mistakes']}</div>
                    <hr style="border: 0; border-top: 1px dashed #ccc; margin: 30px 0;">
                    """
                    ans_html_blocks.append(block)
                
                all_answers_html = "".join(ans_html_blocks)
                
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
                    .exam-title {{ font-size: 20pt; font-weight: 900; letter-spacing: 5px; }}
                    .subject {{ font-size: 16pt; font-weight: 700; margin-top: 8px; color: #555; }}
                    .section-title {{ font-weight: bold; font-size: 12.5pt; margin-top: 25px; margin-bottom: 10px; border-left: 5px solid #0056b3; padding-left: 10px; color: #0056b3; }}
                    .content-box {{ padding-left: 15px; text-align: justify; word-break: keep-all; margin-bottom: 10px; }}
                    .print-btn {{ display: block; margin: 0 auto 20px auto; padding: 12px 30px; font-size: 16px; font-weight: bold; color: white; background-color: #0056b3; border: none; border-radius: 5px; cursor: pointer; }}
                    .print-btn:hover {{ background-color: #004494; }}
                    @media print {{
                        body {{ background-color: white; padding: 0; }}
                        .paper {{ box-shadow: none; width: 100%; border: none; padding: 0; margin: 0; }}
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
                        {all_answers_html}
                    </div>
                </body>
                </html>
                """
                st.components.v1.html(ans_print_html, height=1200, scrolling=True)

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
