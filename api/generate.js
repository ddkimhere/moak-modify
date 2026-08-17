import { GoogleGenAI, ThinkingLevel } from '@google/genai';

const MODEL = 'gemini-3.1-flash-lite';

const MASTER_PROMPT = `
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
문제를 풀면서 학생이 반드시 문장 구조를 분석하고, 논리를 이해하고, 문법을 적용하고, 문맥 속에서 어휘를 해석하도록 만든다.
단순 암기나 운으로 맞힐 수 있는 문제는 만들지 않는다.
항상 "이 문제를 통해 학생은 무엇을 배우게 되는가?"를 먼저 생각한다.

4. 학생 수준
대상은 내신 2~3등급 학생이다. 기본 독해는 가능하지만 긴 문장 구조, 논리 연결, 문법의 독해 적용에서 실수하는 학생을 평가하도록 만든다.

5. 난이도
쉬움 20% / 보통 60% / 어려움 20%를 기본으로 하되 사용자가 지정한 난이도를 우선한다.
어려운 문제도 반드시 본문 안에서 근거를 찾을 수 있어야 한다.
추측이나 상식만으로 풀리는 문제는 금지한다.

6. 출제 절차
문제를 만들기 전에 글의 주제, 목적, 구조, 문단별 역할, 핵심 문장, 연결어, 핵심 어휘, 핵심 문법, 오답 가능 지점, 출제 가능한 포인트를 분석한다.

7. 문제 유형
주제, 제목, 요지, 빈칸추론, 내용일치, 내용불일치, 어휘, 어법, 문장삽입, 순서배열, 문장배열, 요약문 완성, 밑줄 의미, 서술형(단어배열)을 제작할 수 있다.

8. 문법 출제 원칙
문법은 반드시 본문 안에서 출제한다. 관계사, 분사, 준동사, 시제, 수동태, 병렬구조, 접속사, 가정법, 대명사, 수일치 등을 활용하되 문법 문제를 위해 원문을 억지로 바꾸지 않는다.

9. 빈칸 출제 원칙
빈칸은 글의 핵심 논리를 묻고 글 전체 흐름을 이해해야 풀 수 있도록 제작한다.

10. 어휘 출제 원칙
문맥상 의미를 평가하며 동의어·반의어도 문맥 안에서 판단하게 한다.

11. 오답 제작 원칙
오답은 반드시 그럴듯해야 하며 일부만 맞는 내용, 논리 오류, 인과관계 오류, 지시어 오류, 문법 오류, 문맥상 의미 오류 등을 활용한다. 모든 오답에는 틀린 이유가 존재해야 한다.

12. 출제 포인트 중복 금지
같은 문장을 여러 문제에서 사용할 수 있으나 같은 출제 포인트를 반복하지 않는다.

13. 시험지 구성 원칙
문항은 지문 전체에 고르게 분포하도록 하고 도입, 전개, 예시, 결론을 균형 있게 활용한다.

14. 정답 번호 배치
사용자가 지정한 객관식 정답 번호를 반드시 지키며 특정 번호에 편중되지 않게 한다.

15. 서술형 출제 시 특별 규칙
- is_subjective를 true로 설정한다.
- 지문에서 가장 중요한 핵심 문장 1개를 발췌하여 sa_korean_meaning에 우리말 해석을 제공한다.
- 해당 문장의 영어 단어를 완전히 뒤섞어 sa_given_words로 제공한다.
- options는 빈 배열로 둔다.
- distractor_analysis에는 채점 기준 및 부분 점수 기준을 작성한다.

16. 해설 작성
모든 문제에는 정답, 출제 의도, 본문 근거, 상세 해설, 오답 분석 또는 채점 기준, 학생들이 자주 하는 실수를 작성한다.

17. 내부 검토
정답 유일성, 오답 타당성, 난이도, 유형 균형, 출제 포인트 중복, 오탈자, 번호 오류, 해설 오류, 문체 일관성을 최종 검토한다.

18. AI 자가 검토
최종 출력 전에 정답은 하나뿐인지, 오답이 충분히 그럴듯한지, 본문 근거가 존재하는지, 내신 2~3등급 수준인지, 억지 함정은 없는지, 문법 오류는 없는지, 출제 포인트가 중복되지 않았는지 확인하고 미달하면 수정한다.

19. 출력 형식
제시된 JSON 스키마에 맞춰 문제, 보기, 정답, 출제의도, 해설, 오답분석 등을 빠짐없이 작성한다.

20. 절대 원칙
원문에 없는 내용을 근거로 문제를 만들지 않는다. 모든 정답은 본문에서 확인 가능해야 한다. 원문은 문제 유형에 필요한 최소 범위 외에는 임의로 재작성하지 않는다.
`;

const responseSchema = {
  type: 'object',
  properties: {
    questions: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          question_type: { type: 'string' },
          difficulty: { type: 'string' },
          question_text: { type: 'string' },
          passage: { type: 'string' },
          is_subjective: { type: 'boolean' },
          options: { type: 'array', items: { type: 'string' } },
          correct_answer: { type: 'string' },
          sa_korean_meaning: { type: 'string' },
          sa_given_words: { type: 'array', items: { type: 'string' } },
          intent: { type: 'string' },
          text_evidence: { type: 'string' },
          explanation: { type: 'string' },
          distractor_analysis: { type: 'string' },
          common_mistakes: { type: 'string' }
        },
        required: [
          'question_type', 'difficulty', 'question_text', 'passage', 'is_subjective',
          'options', 'correct_answer', 'sa_korean_meaning', 'sa_given_words',
          'intent', 'text_evidence', 'explanation', 'distractor_analysis', 'common_mistakes'
        ]
      }
    }
  },
  required: ['questions']
};

function normalizeAnswerNumber(value) {
  const text = String(value ?? '').trim();
  const circled = { '①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5' };
  for (const [symbol, number] of Object.entries(circled)) {
    if (text.includes(symbol)) return number;
  }
  return text.match(/[1-5]/)?.[0] ?? '';
}

function buildPrompt(passage, questionPlan) {
  const requestLines = questionPlan.map((item, index) => {
    if (item.target_answer) {
      return `- ${index + 1}번: ${item.type} / 난이도 ${item.difficulty} / 객관식 정답 번호는 반드시 ${item.target_answer}번`;
    }
    return `- ${index + 1}번: ${item.type} / 난이도 ${item.difficulty} / 서술형`;
  }).join('\n');

  return `
아래 제공된 [원문 지문]을 철저히 분석한 뒤, [요청 문제 구성]에 지정된 유형과 개수를 정확히 맞춰
총 ${questionPlan.length}개의 학교 내신형 변형문제를 한 번에 출제하시오.

[요청 문제 구성]
${requestLines}

[배치 출제 추가 규칙]
1. 요청된 유형별 문항 수를 정확히 지킨다.
2. 같은 출제 포인트를 여러 문제에서 반복하지 않는다.
3. 가능하면 지문의 서로 다른 문장과 논리 구간을 고르게 활용한다.
4. 객관식 정답 번호가 한 번호에 편중되지 않도록 전체 세트에서 분산한다.
5. 각 문항은 독립적으로 풀 수 있어야 하며 정답은 반드시 하나여야 한다.
6. 서술형(단어배열)은 기존 서술형 규칙을 그대로 따른다.
7. 문장삽입 문제는 passage의 첫 줄에 반드시 '[주어진 문장] 실제 문장'을 넣고, 한 줄을 비운 뒤 본문을 제시한다. 본문에는 삽입 후보 위치 ①~⑤를 자연스럽게 표시한다.
8. 어법 문제와 어휘/문맥상 낱말 문제는 passage 안의 ①~⑤ 핵심 단어 또는 어구를 반드시 <u>①표현</u>처럼 HTML 밑줄 태그로 표시한다. 번호만 있고 표현에 밑줄이 없는 형태는 금지한다.
9. 객관식 보기는 실제 선택지가 필요한 유형에만 작성한다. 문장삽입처럼 본문 속 ①~⑤ 위치 자체가 선택지인 경우 options는 빈 리스트로 둔다.
10. [요청 문제 구성]에 객관식 정답 번호가 지정되어 있으면 그 번호를 반드시 정답이 되도록 문제와 보기/표시 위치를 설계한다. 정답 번호를 임의로 변경하지 않는다.
11. questions 배열 순서는 요청 문제 구성의 순서를 정확히 따른다.
12. 원문 지문은 필요 유형의 문제 제시에 필요한 범위 외에는 임의로 재작성하지 않는다.
13. 반드시 최종 자가 검토 후 JSON의 questions 배열에 문제들을 담아 반환한다.

[원문 지문]
${passage}`;
}

async function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'POST 요청만 지원합니다.' });
  }

  const apiKey = process.env.GEMINI_API_KEY?.trim();
  if (!apiKey) {
    return res.status(500).json({ error: '서버에 GEMINI_API_KEY가 설정되지 않았습니다.' });
  }

  const { passage, question_plan: questionPlan } = req.body ?? {};
  if (typeof passage !== 'string' || !passage.trim()) {
    return res.status(400).json({ error: '지문이 비어 있습니다.' });
  }
  if (!Array.isArray(questionPlan) || questionPlan.length < 1 || questionPlan.length > 10) {
    return res.status(400).json({ error: '지문당 문항 수는 1~10개여야 합니다.' });
  }

  const ai = new GoogleGenAI({ apiKey });
  const prompt = buildPrompt(passage.trim(), questionPlan);
  let lastError;

  for (let attempt = 0; attempt < 3; attempt += 1) {
    try {
      const response = await ai.models.generateContent({
        model: MODEL,
        contents: [MASTER_PROMPT, prompt],
        config: {
          responseMimeType: 'application/json',
          responseSchema,
          thinkingConfig: { thinkingLevel: ThinkingLevel.MINIMAL },
          maxOutputTokens: 32768,
          temperature: 0.2
        }
      });

      const parsed = JSON.parse(response.text || '{}');
      const questions = Array.isArray(parsed.questions)
        ? parsed.questions.slice(0, questionPlan.length)
        : [];

      if (questions.length !== questionPlan.length) {
        throw new Error(`요청한 ${questionPlan.length}문항 중 ${questions.length}문항만 생성되었습니다.`);
      }

      const mismatches = [];
      questionPlan.forEach((expected, index) => {
        if (!expected.target_answer) return;
        const actual = normalizeAnswerNumber(questions[index]?.correct_answer);
        if (actual !== String(expected.target_answer)) {
          mismatches.push(`${index + 1}번 목표 ${expected.target_answer} / 실제 ${questions[index]?.correct_answer ?? ''}`);
        }
      });
      if (mismatches.length) {
        throw new Error(`정답 번호 배치 불일치: ${mismatches.join('; ')}`);
      }

      return res.status(200).json({ questions });
    } catch (error) {
      lastError = error;
      const msg = String(error?.message ?? error).toUpperCase();
      const retryable = /429|503|UNAVAILABLE|QUOTA|정답 번호 배치 불일치|문항만 생성/.test(msg);
      if (!retryable || attempt === 2) break;
      await sleep((attempt + 1) * 2000);
    }
  }

  console.error(lastError);
  return res.status(500).json({ error: lastError?.message || '문제 생성 중 오류가 발생했습니다.' });
}
