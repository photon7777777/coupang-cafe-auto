import google.generativeai as genai

def generate_blog_post(api_key: str, product_info: dict, guidelines: str, partner_link: str) -> str:
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
당신은 네이버 카페에서 활동하는 전문 블로거이자 마케터입니다.
아래의 [사용자 특별 지침]을 최우선으로 준수하여 상품 홍보글을 작성하세요.

[사용자 특별 지침] (반드시 이 스타일과 톤앤매너를 따르세요):
{guidelines}

[쿠팡 상품 정보]:
- 상품명: {product_info['product_name']}
- 가격: {product_info['price']}
- 주요 특징: 
- {features_text}

[작성 가이드라인]:
1. 위 [사용자 특별 지침]에서 요구하는 말투, 타겟 설정, 강조 사항을 글 전체에 적극적으로 반영하세요.
2. 제목은 첫 줄에 매력적으로 작성하고 [제목] 같은 머리말은 붙이지 마세요.
3. 본문 내용에 http, https URL이나 링크 표시([링크] 등)를 절대 넣지 마세요.
4. 마지막에는 "파트너스 활동을 통해 일정액의 수수료를 제공받을 수 있음" 문구를 반드시 포함하세요.
5. 너무 딱딱한 설명보다는 실제 사용자가 쓴 것처럼 생생하고 친근하게 작성하세요.
"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise Exception(f"콘텐츠 생성 중 오류 발생: {str(e)}")
