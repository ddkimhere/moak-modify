import os
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

# 1. API 키 확인 및 클라이언트 초기화
# 환경 변수 대신 API 키를 직접 입력합니다 (주의: 코드 공유 시 유출에 주의하세요!)
api_key = "AQ.Ab8RN6KvtMi5trvzk5__MPYLg2xmsReIXQfgu0LANXc2vQ74xA"

client = genai.Client(api_key=api_key)

# 2. 결과물 출력 형식 정의 (프론트엔드와 연결하기 쉽도록 JSON 구조 강제화)
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
2. 모든 정답은 본문에서 확인 가능해야 단다.
3. 억지 함정 금지: 논리를 이해해야 풀 수 있도록 제작한다.
4. 오답 제작 원칙: 오답은 본문의 단어를 교묘하게 활용하여 매우 그럴듯하게(매력도 높게) 만들어야 하며, 모든 오답에는 틀린 이유가 존재해야 한다.
"""

def generate_exam_question(passage: str, q_type: str, difficulty: str):
    """
    지문과 조건을 받아 Gemini API를 통해 완벽한 형태의 변형 문제를 생성합니다.
    """
    print(f"\n[{q_type} / {difficulty}] 난이도로 문제 생성을 시작합니다...")
    print("AI 위원회(출제/검토/평가/품질)가 분석 및 검증 중입니다. 잠시만 기다려주세요...\n")
    
    # AI에게 전달할 최종 명령
    prompt = f"""
    아래 제공된 [원문 지문]을 철저히 분석한 뒤, '{q_type}' 유형의 문제를 '{difficulty}' 난이도로 출제하시오.
    반드시 4단계 검토(출제->검토->평가->품질관리)를 스스로 거친 후, 오류가 없는 최종 결과물만 반환하시오.
    
    [원문 지문]
    {passage}
    """
    
    # 모델 이름을 가장 최신 기본 개방 모델인 gemini-2.5-flash 로 설정합니다.
    # 구글 최신 SDK의 Structured Outputs 기능 적용
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[MASTER_PROMPT, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QuestionResponse,
            temperature=0.2, # 일관성 있고 정확한 출제를 위해 낮게 설정
        ),
    )
    
    return response.text

# 4. 실행 테스트 (터미널에서 직접 입력받도록 수정)
if __name__ == "__main__":
    print("\n================================================")
    print("  🏫 AI 모의고사 변형 문제 출제 엔진 작동 시작  ")
    print("================================================\n")
    
    print("[1단계] 변형 문제를 만들 영어 지문을 아래에 붙여넣으세요.")
    print("(※ 지문을 모두 붙여넣은 뒤, 입력을 끝내려면 엔터(Enter)를 연속으로 두 번 누르세요):")
    print("-" * 50)
    
    lines = []
    while True:
        try:
            line = input()
            # 아무것도 입력하지 않고 엔터를 쳤을 때 (연속 엔터 감지)
            if not line.strip() and len(lines) > 0:
                break
            if line.strip():
                lines.append(line)
        except EOFError:
            break
            
    user_passage = "\n".join(lines)
    
    if not user_passage.strip():
        print("\n입력된 지문이 없습니다. 프로그램을 종료합니다.")
    else:
        print("-" * 50)
        print("\n[2단계] 문제 출제 조건을 입력해 주세요.")
        
        # 사용자로부터 원하는 유형과 난이도를 입력받습니다.
        selected_type = input("▶ 원하는 문제 유형을 입력하세요 (예: 빈칸추론, 어법, 문장삽입 등): ")
        if not selected_type.strip():
            selected_type = "빈칸추론" # 기본값
            
        selected_diff = input("▶ 원하는 난이도를 입력하세요 (예: 쉬움, 보통, 어려움): ")
        if not selected_diff.strip():
            selected_diff = "보통" # 기본값
        
        try:
            # 엔진 가동
            result_json_string = generate_exam_question(user_passage, selected_type, selected_diff)
            
            # 보기 좋게 출력
            parsed_result = json.loads(result_json_string)
            print("\n====== [ 🎉 문제 출제 완료 🎉 ] ======\n")
            print(json.dumps(parsed_result, indent=4, ensure_ascii=False))
            
        except Exception as e:
            print(f"\n오류가 발생했습니다: {e}")
            
