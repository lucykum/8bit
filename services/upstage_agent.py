import requests
import json
import os
import sys
from openai import OpenAI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import UPSTAGE_API_KEY

# Upstage Solar Pro3 클라이언트
client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v1"
)

def parse_pdf(file_path):
    url = "https://api.upstage.ai/v1/document-ai/document-parse"
    headers = {"Authorization": f"Bearer {UPSTAGE_API_KEY}"}
    files = {"document": open(file_path, "rb")}
    data = {"output_formats": '["text"]'}

    print(f"파싱 중: {file_path}")
    response = requests.post(url, headers=headers, files=files, data=data)

    if response.status_code == 200:
        result = response.json()
        print(f"파싱 완료: {file_path}")
        return result
    else:
        print(f"에러 발생: {response.status_code} - {response.text}")
        return None

def parse_all_pdfs():
    kb_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    results = {}

    for filename in os.listdir(kb_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(kb_dir, filename)
            parsed = parse_pdf(file_path)
            if parsed:
                results[filename] = parsed

    output_path = os.path.join(kb_dir, "parsed_knowledge.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n전체 파싱 완료! {len(results)}개 파일 저장됨")
    return results

def load_parsed_text():
    """parsed_knowledge.json에서 텍스트만 추출하여 반환"""
    kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "parsed_knowledge.json")
    with open(kb_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    texts = {}
    for filename, content in data.items():
        texts[filename] = content.get("content", {}).get("text", "")
    return texts

def build_knowledge_context():
    """에이전트 A·B: 파싱된 텍스트를 Solar Pro3로 구조화"""
    texts = load_parsed_text()
    all_text = "\n\n".join([f"[{name}]\n{text[:30000]}" for name, text in texts.items()])

    response = client.chat.completions.create(
        model="solar-pro3",
        messages=[
            {
                "role": "system",
                "content": """당신은 화장품 규제 전문 법률 분석가입니다.
주어진 법령/지침 텍스트에서 다음을 JSON으로 추출하세요:

1. "금지표현": 화장품 광고에서 사용 금지된 표현 목록
   - 각 항목: {"표현", "카테고리"(의약품오인/기능성오인/과장광고/소비자오인), "근거법령", "처벌수위"}

2. "허용표현": 합법적으로 사용 가능한 대체 표현 목록
   - 각 항목: {"표현", "용도", "조건"}

3. "처벌기준": 위반 시 처벌 수위 요약
   - 각 항목: {"위반유형", "처벌내용", "근거조항"}

JSON만 출력하세요. 설명 없이."""
            },
            {
                "role": "user",
                "content": f"다음 화장품 관련 법령 및 지침 텍스트를 분석하세요:\n\n{all_text}"
            }
        ],
        temperature=0.1
    )

    result_text = response.choices[0].message.content

    # JSON 파싱 시도
    try:
        # ```json ... ``` 감싸기 제거
        cleaned = result_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1]
            cleaned = cleaned.rsplit("```", 1)[0]
        structured = json.loads(cleaned)
    except json.JSONDecodeError:
        structured = {"raw_response": result_text}

    # 구조화된 JSON 저장
    output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "structured_knowledge.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(structured, f, ensure_ascii=False, indent=2)

    print("구조화 완료! data/structured_knowledge.json 저장됨")
    return structured

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "structure":
        build_knowledge_context()
    else:
        parse_all_pdfs()
        print("\n이제 구조화를 실행합니다...")
        build_knowledge_context()