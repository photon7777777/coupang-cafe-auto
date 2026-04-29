import google.generativeai as genai

def generate_blog_post(api_key: str, product_info: dict, partner_link: str) -> str:
    """Gemini API를 사용하여 블로그/카페 포스팅용 콘텐츠를 생성합니다."""
    genai.configure(api_key=api_key)
    
    # 사용 가능한 모델 찾기
    available_models = [
        m.name for m in genai.list_models() 
        if "generateContent" in m.supported_generation_methods
    ]
    
    if not available_models:
        raise Exception("사용 가능한 Gemini 모델을 찾을 수 없습니다. API 키를 확인해주세요.")
    
    # gemini-1.5 관련 모델이 있다면 우선 선택, 없다면 사용 가능한 첫 번째 모델 선택
    target_model = next((m for m in available_models if "1.5" in m), available_models[0])
    model = genai.GenerativeModel(target_model.replace("models/", ""))
    
    features_text = "\n- ".join(product_info.get("features", []))
    
    prompt = f"""
당신은 네이버 카페에서 활동하며, 실제로 상품을 구매하여 사용 중인 일반인 사용자입니다.
전문적인 홍보성 글보다는 이웃에게 추천하듯 친근하고 솔직한 구매 후기를 작성하세요.

[쿠팡 상품 정보]:
- 상품명: {product_info['product_name']}
- 가격: {product_info['price']}
- 주요 특징: 
- {features_text}

[작성 필수 가이드라인]:
1. 글의 구성 순서를 반드시 지키세요:
   - 첫 번째 줄: 게시글의 제목 (상품명 '{product_info['product_name']}'을 반드시 포함하세요. 클릭률을 극대화할 수 있도록 궁금증을 유발하거나 혜택을 강조하되, 반드시 말이 끝까지 이어지는 완전한 문장으로 60자 이내로 작성하세요.)
   - 두 번째 줄: "쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다." 문구
   - 세 번째 줄부터: 본문 내용 (솔직한 후기 스타일)
2. 제목에 특수문자(#, *)를 남발하지 말고, 실제 카페 인기글처럼 자연스럽게 작성하세요.
3. 말투는 블로그 마케터 느낌이 아닌, 실제 '내돈내산' 후기처럼 자연스러운 구어체(~해요, ~네요, ~더라구요 등)를 사용하세요.
4. 본문 내용에 http, https URL이나 링크 표시([링크] 등)를 절대 넣지 마세요.
5. 전문 용어보다는 실생활에서 느끼는 편리함을 위주로 작성하세요.
6. 너무 정제된 느낌보다는 이웃과 대화하듯 편안하게 작성하세요.
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise Exception(f"콘텐츠 생성 중 오류 발생: {str(e)}")
