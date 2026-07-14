import os
import json
import time
import concurrent.futures
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. API 키 설정 (하드코딩 방식)
api_key = "AQ.Ab8RN6KvtMi5trvzk5__MPYLg2xmsReIXQfgu0LANXc2vQ74xA"
client = genai.Client(api_key=api_key)

# 2. 결과물 출력 형식 정의 (JSON 구조 강제화)
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
또한 다음 네 명의 전문가가 하나의 팀처럼 협업하여 문제를 제작한다.
- 출제위원
- 검토위원
- 평가위원
- 품질관리위원
이 네 역할은 내부적으로만 수행하며, 사용자에게는 최종 결과만 출력한다.

2. 목표
고등학교 내신 5등급제 기준 2~3등급 학생을 대상으로 하는 학교 내신형 변형문제를 1개 제작한다.
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
주제, 제목, 요지, 빈칸추론, 내용일치, 내용불일치, 어휘, 어법, 문장삽입, 순서배열, 문장배열, 요약문 완성, 밑줄 의미, 서술형(단어배열)
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
오답은 반드시 그럴듯해야 단다.
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

15. 서술형 출제 시 특별 규칙 (사용자가 '서술형(단어배열)'을 요구한 경우)
- is_subjective를 true로 설정한다.
- 지문에서 가장 중요한 핵심 문장(주제문 또는 핵심 어법이 포함된 문장) 1개를 발췌하여 우리말 해석(sa_korean_meaning)을 제공한다.
- 해당 문장을 구성하는 영어 단어들을 순서가 유추되지 않게 완전히 뒤섞어 배열(sa_given_words)로 제공한다.
- 객관식 보기(options)는 비워둔다.
- 채점 기준 및 부분 점수 기준은 distractor_analysis 항목에 작성한다.

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
최종 결과물은 실제 고등학교 중간·기말고사에 바로 사용할 수 있는 수준의 완성도를 목표로 단다.
"""

def generate_exam_question(passage: str, q_type: str, difficulty: str):
    """
    지문과 조건을 받아 Gemini API를 통해 한 문항의 변형 문제를 생성합니다.
    서버 트래픽 초과(503/429) 오류를 대비하여 자동 재시도 로직이 강화되었습니다.
    """
    prompt = f"""
    아래 제공된 [원문 지문]을 철저히 분석한 뒤, '{q_type}' 유형의 문제를 '{difficulty}' 난이도로 딱 1문제만 출제하시오.
    반드시 스스로 검토를 거친 후, 오류가 없는 최종 결과물만 JSON 형태로 반환하시오.
    
    [원문 지문]
    {passage}
    """
    
    max_retries = 6  # 최대 6번까지 끈기 있게 재시도
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.5-flash',
                contents=[MASTER_PROMPT, prompt],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=QuestionResponse,
                    temperature=0.2, 
                ),
            )
            return json.loads(response.text)
            
        except Exception as e:
            error_msg = str(e).upper()
            # 503, 429 등 서버 과부하 에러 시 대기 후 재시도
            if "503" in error_msg or "429" in error_msg or "UNAVAILABLE" in error_msg or "QUOTA" in error_msg:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + 1  # 2초, 3초, 5초, 9초... 점진적으로 대기
                    time.sleep(wait_time)
                    continue
            # 다른 종류의 에러이거나 최대 재시도 횟수를 초과하면 에러 발생
            raise e

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
        
        # 결과를 저장할 리스트 미리 생성 (순서 보장을 위해)
        all_results = [None] * num_questions
        
        def process_question(idx, q_data):
            """개별 문항을 처리하는 보조 함수"""
            parsed_result = generate_exam_question(q_data['passage'], q_data['type'], q_data['diff'])
            return idx, parsed_result

        try:
            status_text.text(f"총 {num_questions}문항을 병렬 분석 및 출제 중입니다. 잠시만 기다려주세요...")
            completed = 0
            
            # 구글 서버 과부하를 막기 위해 max_workers를 3으로 제한 (최대 3개씩만 동시 요청)
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(num_questions, 3)) as executor:
                # 모든 문항 출제 작업을 동시에 스레드풀에 예약
                futures = {executor.submit(process_question, i, q): i for i, q in enumerate(questions_data)}
                
                # 먼저 끝나는 작업부터 순차적으로 프로그레스 바 업데이트
                for future in concurrent.futures.as_completed(futures):
                    idx, parsed_result = future.result()
                    all_results[idx] = parsed_result
                    completed += 1
                    progress_bar.progress(completed / num_questions)
                
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
