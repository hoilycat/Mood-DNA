import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import colorsys
from sklearn.cluster import KMeans
import cv2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader  # <--- [추가] PDF에 사진 넣는 도구
import io
import os
import requests

# -----------------------------------------------------------
# [함수] Unsplash 이미지 검색기 (스마트 버전 🧠)
# -----------------------------------------------------------
def search_unsplash(query, mood_color_rgb):
    # 1. 비밀 금고(.streamlit/secrets.toml)에서 키 꺼내기
    try:
        api_key = st.secrets["unsplash_api_key"]
    except:
        # 키가 없으면 그냥 빈 리스트 반환 (에러 방지)
        return []

    # 2. 색깔 이름을 영어로 추측하기 (검색어용)
    r, g, b = mood_color_rgb
    color_name = "Minimal" # 기본값
    
    # 색상 판별 로직 (단순화)
    if r > 200 and g > 200 and b > 200: color_name = "White Clean"
    elif r < 50 and g < 50 and b < 50: color_name = "Dark Mode"
    elif r > g and r > b: color_name = "Red"
    elif g > r and g > b: color_name = "Green"
    elif b > r and b > g: color_name = "Blue"
    elif r > 200 and g > 200: color_name = "Yellow"
    
    # 3. 검색어 조합: "Green Minimal UI Design Layout" 처럼 구체적으로!
    # query(예: Natural) + color_name(예: Green) + UI Design
    search_query = f"{color_name} {query} UI Design Layout"
    
    # 4. 요청 보내기
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": search_query,
        "client_id": api_key,
        "per_page": 3,
        "orientation": "landscape" # 가로 사진이 레퍼런스로 보기 좋음
    }
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            results = []
            for item in data['results']:
                results.append({
                    "url": item['urls']['small'],
                    "photographer": item['user']['name'],
                    "link": item['links']['html']
                })
            return results
        else:
            return []
    except:
        return []

# -----------------------------------------------------------
# [함수] 분석 로봇 (스타벅스 해결 버전)
# -----------------------------------------------------------
def analyze_image_dna(image):
    img_rgb = image.convert('RGB')
    resized_img = img_rgb.resize((400, 400))
    img_array = np.array(resized_img)
    
    # 구조 분석
    open_cv_image = np.array(resized_img)
    gray_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray_image, 100, 200)
    total_pixels = edges.size
    edge_pixels = np.count_nonzero(edges)
    complexity_ratio = (edge_pixels / total_pixels) * 100
    
    # 색상 분석
    pixels = img_array.reshape(-1, 3)
    kmeans = KMeans(n_clusters=5, random_state=42)
    kmeans.fit(pixels)
    colors = kmeans.cluster_centers_.astype(int)
    
    unique, counts = np.unique(kmeans.labels_, return_counts=True)
    sorted_indices = np.argsort(counts)[::-1]
    sorted_counts = counts[sorted_indices]
    sorted_colors = [colors[i] for i in sorted_indices]
    
    # 배경색(흰/검) 무시 로직
    dominant_color = sorted_colors[0]
    r, g, b = int(dominant_color[0]), int(dominant_color[1]), int(dominant_color[2])
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    if (v > 0.9 and s < 0.1) or (v < 0.1): # 너무 하얗거나 너무 까맣다면
        dominant_color = sorted_colors[1] # 2등 색깔 선택
        r, g, b = int(dominant_color[0]), int(dominant_color[1]), int(dominant_color[2])
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    # 무드 판정
    mood_result = {}
    if s < 0.2:
        mood_result = {"keyword": "Modern & Minimal", "icon": "🏢", "desc": "절제되고 세련된 도시적 감성"}
    elif v < 0.3:
        mood_result = {"keyword": "Luxury & Heavy", "icon": "🎩", "desc": "중후하고 고급스러운 프리미엄 감성"}
    elif s > 0.5 and v > 0.5:
        mood_result = {"keyword": "Energetic & Pop", "icon": "🎉", "desc": "강렬한 에너지와 젊음의 감성"}
    else:
        mood_result = {"keyword": "Natural & Soft", "icon": "🌿", "desc": "편안하고 부드러운 힐링 감성"}

    return {
        "image": resized_img,
        "edges": edges,
        "colors": sorted_colors,
        "counts": sorted_counts,
        "complexity": complexity_ratio,
        "mood": mood_result,
        "dominant_rgb": dominant_color
    }

# -----------------------------------------------------------
# [함수] AI 컨설팅 메시지
# -----------------------------------------------------------
def get_ai_consulting(mood_data, complexity):
    struct_comment = ""
    if complexity < 2: struct_comment = "이 디자인은 **여백의 미**를 활용한 **'미니멀리즘 전략'**이 돋보입니다."
    elif complexity < 5: struct_comment = "이미지와 텍스트의 **이상적인 균형(Balance)**을 이루고 있습니다."
    else: struct_comment = "밀도 높은 디테일이 **풍부한 정보**를 전달하고 있습니다."

    mood_comment = ""
    keyword = mood_data['keyword']
    if "Modern" in keyword: mood_comment = "도시적이고 세련된 컬러감은 **IT/테크** 브랜드에 적합합니다."
    elif "Luxury" in keyword: mood_comment = "중후한 톤은 **프리미엄 제품**의 품격을 대변합니다."
    elif "Energetic" in keyword: mood_comment = "고채도 컬러는 **MZ세대** 타겟 광고에 효과적입니다."
    else: mood_comment = "편안한 톤은 **웰빙/라이프스타일** 분야에 어울립니다."

    return f"""
    💡 **AI 디자인 컨설턴트의 총평:**
    {struct_comment} {mood_comment}
    종합적으로 **[{keyword}]** 무드를 통해 타겟 고객에게 강력한 인상을 남길 수 있습니다.
    """

# -----------------------------------------------------------
# [함수] PDF 생성 (업그레이드: 이미지+차트 포함! 🎨)
# -----------------------------------------------------------
def create_pdf_report(dna_data, advice_text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # 1. 제목
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, height - 50, "Mood-DNA Analysis Report")
    c.setLineWidth(1)
    c.line(50, height - 60, width - 50, height - 60)

    # 2. 메인 무드
    mood = dna_data['mood']
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 100, f"Main Mood: {mood['keyword']}")
    
    c.setFont("Helvetica", 12)
    c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(50, height - 120, f"{mood['desc']}") # 영어만 지원됨 (한글 깨짐 주의)
    c.setFillColorRGB(0, 0, 0)

    # 3. 원본 이미지 넣기 (왼쪽)
    img_buffer = io.BytesIO()
    dna_data['image'].save(img_buffer, format='PNG')
    img_buffer.seek(0)
    c.drawImage(ImageReader(img_buffer), 50, height - 350, width=200, height=200, preserveAspectRatio=True)

    # 4. 컬러 팔레트 그리기 (오른쪽)
    c.drawString(280, height - 150, "Color Palette & Ratio")
    y_pos = height - 180
    for i, color in enumerate(dna_data['colors']):
        r, g, b = color[0]/255, color[1]/255, color[2]/255
        c.setFillColorRGB(r, g, b)
        c.rect(280, y_pos, 40, 20, fill=1, stroke=0) # 사각형
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 10)
        hex_code = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
        percent = dna_data['counts'][i] / sum(dna_data['counts']) * 100
        c.drawString(330, y_pos + 5, f"{hex_code} ({percent:.1f}%)")
        y_pos -= 30

    # 5. 구조 분석 점수
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 380, "Structure Analysis")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 400, f"Complexity Score: {dna_data['complexity']:.2f}%")
    
    # 6. AI 코멘트 (요약)
    c.drawString(50, height - 460, "AI Consultant Summary:")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, height - 480, "This design uses color harmony effectively.")
    c.drawString(50, height - 495, "Recommended for branding targeting the specific mood.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# -----------------------------------------------------------
# 메인 UI
# -----------------------------------------------------------
st.set_page_config(page_title="Mood-DNA Pro", page_icon="🧬", layout="wide")

st.title("🧬 Mood-DNA : AI 디자인 무드 분석기")
st.sidebar.header("🎛️ 분석 모드 설정")
mode = st.sidebar.radio("모드를 선택하세요:", ["단일 분석 (Single)", "A/B 비교 (Comparison)"])

# ======================= [모드 1] 단일 분석 =======================
if mode == "단일 분석 (Single)":
    st.sidebar.markdown("---")
    uploaded_file = st.sidebar.file_uploader("이미지 업로드", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        dna = analyze_image_dna(image)
        ai_advice = get_ai_consulting(dna['mood'], dna['complexity'])
        
        # 상단 결과
        c1, c2 = st.columns([1, 1])
        with c1: st.image(dna['image'], caption="원본 이미지", use_container_width=True)
        with c2: st.image(dna['edges'], caption=f"구조 분석 ({dna['complexity']:.2f}%)", use_container_width=True)
            
        st.info(f"🧬 분석 결과: **[{dna['mood']['keyword']}]** {dna['mood']['icon']}\n\n{dna['mood']['desc']}")
        with st.expander("💡 AI 상세 컨설팅 보기"):
            st.write(ai_advice)

        st.write("---")
        
        # 컬러 & 차트
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("🎨 Color Palette")
            for i, color in enumerate(dna['colors']):
                hex_code = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                st.markdown(f'<div style="background-color:{hex_code};height:40px;border-radius:5px;margin-bottom:5px;"></div>', unsafe_allow_html=True)
                st.caption(hex_code)
        with c2:
            st.subheader("📊 Color Ratio")
            fig, ax = plt.subplots(figsize=(4, 3))
            sorted_hex = ['#{:02x}{:02x}{:02x}'.format(c[0],c[1],c[2]) for c in dna['colors']]
            sorted_colors_norm = [c/255 for c in dna['colors']]
            ax.pie(dna['counts'], labels=sorted_hex, colors=sorted_colors_norm, autopct='%1.1f%%', textprops={'fontsize': 8})
            st.pyplot(fig)

        # ★ [NEW] Unsplash 추천 시스템 (입력창 없이 자동!)
        st.write("---")
        st.subheader("🖼️ AI 추천 레퍼런스 (Powered by Unsplash)")
        
        with st.spinner(f"🌐 '{dna['mood']['keyword']}' 스타일의 UI 레퍼런스 검색 중..."):
            # 키는 함수 안에서 secrets를 통해 자동으로 가져옴!
            # 검색어에 'Natural' 뿐만 아니라 'Green'(색상)도 같이 넣어서 검색함!
            recommendations = search_unsplash(dna['mood']['keyword'].replace("&", ""), dna['dominant_rgb'])
                
        if recommendations:
            rec_cols = st.columns(3)
            for i, rec in enumerate(recommendations):
                with rec_cols[i]:
                    st.image(rec['url'], use_container_width=True)
                    st.caption(f"by {rec['photographer']}")
                    st.markdown(f"[Unsplash에서 보기]({rec['link']})")
        else:
            st.info("🔒 API 키가 설정되지 않았거나 검색 결과가 없습니다. (로컬 데모 모드로 작동 중)")

        st.write("---")
        pdf_bytes = create_pdf_report(dna, ai_advice)
        st.download_button("📄 리포트 PDF 다운로드 (이미지 포함)", pdf_bytes, "report.pdf", "application/pdf")

# ======================= [모드 2] A/B 비교 =======================
elif mode == "A/B 비교 (Comparison)":
    st.header("⚖️ A/B Test : 디자인 시안 비교")
    ca, cb = st.columns(2)
    with ca: fa = st.file_uploader("A안", type=['jpg','png'], key="a")
    with cb: fb = st.file_uploader("B안", type=['jpg','png'], key="b")
        
    if fa and fb:
        st.write("---")
        da = analyze_image_dna(Image.open(fa))
        db = analyze_image_dna(Image.open(fb))
        aa = get_ai_consulting(da['mood'], da['complexity'])
        ab = get_ai_consulting(db['mood'], db['complexity'])

        c1, c2 = st.columns(2)
        with c1:
            st.image(da['image'], caption="[A안]", use_container_width=True)
            st.success(f"**{da['mood']['keyword']}**")
            with st.expander("AI 분석"): st.write(aa)
        with c2:
            st.image(db['image'], caption="[B안]", use_container_width=True)
            st.success(f"**{db['mood']['keyword']}**")
            with st.expander("AI 분석"): st.write(ab)
            
        st.write("---")
        st.subheader("🤖 비교 코멘트")
        winner = "A안" if da['complexity'] < db['complexity'] else "B안"
        st.info(f"구조적으로 **{winner}**이 더 심플합니다. 색상 무드에 따라 선택하세요.")

else:
    st.sidebar.info("👈 왼쪽에서 모드를 선택해주세요!")