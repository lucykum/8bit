import json
import os
from openai import OpenAI

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import UPSTAGE_API_KEY

client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1"
)

def load_knowledge():
    """구조화된 지식 JSON 로드"""
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "structured_knowledge.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def analyze_copy(user_input: str) -> dict:
    """에이전트 C: 마케팅 문구 분석 + 대체 카피 생성"""
    knowledge = load_knowledge()
    forbidden = knowledge.get("금지표현", [])
    allowed = knowledge.get("허용표현", [])
    penalties = knowledge.get("처벌기준", [])

    knowledge_str = (
        "## 금지표현 목록\n"
        + json.dumps(forbidden, ensure_ascii=False, indent=2)
        + "\n\n## 허용표현 목록\n"
        + json.dumps(allowed, ensure_ascii=False, indent=2)
        + "\n\n## 처벌기준\n"
        + json.dumps(penalties, ensure_ascii=False, indent=2)
    )

    response = client.chat.completions.create(
        model="solar-pro3",
        messages=[
            {
                "role": "system",
                "content": f"""당신은 '그린라이트 AI'의 수석 마케팅 컴플라이언스 디렉터입니다.

[규제 지식 베이스]
{knowledge_str}

[임무]
사용자가 입력한 화장품 마케팅 문구를 분석하여 반드시 아래 JSON 형식으로만 응답하세요.

{{
  "컴포넌트1_위험도카드": {{
    "종합위험등급": "상/중/하",
    "위험요약": "한 줄 요약",
    "예상처벌": "처벌 수위"
  }},
  "컴포넌트2_위반키워드테이블": [
    {{
      "원본표현": "위험 단어·구문 단위로 분리 (예: '주름개선', '마법의' 각각 별도 항목)",
      "위험도": "상/중/하",
      "대체추천": "합법적 대체 표현",
      "근거": "관련 법령/지침"
    }}
  ],
  "컴포넌트3_완성카피": {{
    "썸네일제목": ["제목1", "제목2", "제목3"],
    "본문카피": "완성된 본문 카피라이팅",
    "해시태그": ["#태그1", "#태그2"]
  }}
}}

JSON만 출력하세요. 설명이나 마크다운 없이."""
            },
            {
                "role": "user",
                "content": f"다음 화장품 마케팅 문구를 분석해주세요:\n\n{user_input}"
            }
        ],
        temperature=0.3
    )

    result_text = response.choices[0].message.content

    try:
        cleaned = result_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "파싱 실패", "raw": result_text}

if __name__ == "__main__":
    test_input = "이 앰플은 피부 깊숙이 침투하여 여드름을 치료하고 아토피를 완화시켜줍니다. 의사도 추천하는 최고의 미백 효과!"
    result = analyze_copy(test_input)
    print(json.dumps(result, ensure_ascii=False, indent=2))