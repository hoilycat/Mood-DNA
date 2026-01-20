import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import colorsys
from sklearn.cluster import KMeans
import cv2
import io
import requests

# PDF 생성을 위한 라이브러리
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader

# 1. [설정] 최상단 배치
st.set_page_config(page_title="Mood-DNA Pro", page_icon="🧬", layout="wide")

# 2. [스타일] 다크모드/라이트모드 통합 UI 디자인
st.markdown("""
    <style>
    /* 메트릭 카드 스타일 */
    .stMetric { 
        background-color: rgba(128, 128, 128, 0.1); 
        padding: 20px; 
        border-radius: 15px; 
        border: 1px solid rgba(128, 128, 128, 0.2); 
    }
    /* AI 리포트 카드 스타일 */
    .report-card {
        background-color: rgba(255, 75, 75, 0.05);
        padding: 25px;
        border-radius: 15px;
        border-left: 6px solid #ff4b4b;
        margin: 20px 0;
        line-height: 1.6;
    }
    /* 버튼 스타일 커스텀 */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------
# [함수 섹션] 핵심 로직들
# -----------------------------------------------------------

# Unsplash 레퍼런스 검색
# ★ [변경] complexity(복잡도) 재료가 하나 더 필요해짐!
def search_unsplash(query, mood_color_rgb, complexity):
    try:
        api_key = st.secrets["unsplash_api_key"]
    except: return []
    
    # 1. 색상 이름 정하기
    r, g, b = mood_color_rgb
    color_name = "Minimal"
    if r > 200 and g > 200 and b > 200: color_name = "White Clean"
    elif r < 50 and g < 50 and b < 50: color_name = "Dark Matte"
    elif b > r + 30 and b > g + 30: color_name = "Corporate Blue" # 파란색은 기업용으로!
    elif r > g + 30 and r > b + 30: color_name = "Red Brand"
    elif g > r + 30 and g > b + 30: color_name = "Green Nature"
    
    # 2. 복잡도에 따라 검색어 다르게 하기
    style_term = "App Interface"
    if complexity < 3.0: style_term = "Minimalist Logo Branding" # 심플하면 로고 검색
    elif complexity < 10.0: style_term = "Clean Web Layout"
    else: style_term = "Graphic Poster Design"
    
    search_query = f"{color_name} {style_term}"
    
    url = "https://api.unsplash.com/search/photos"
    params = {"query": search_query, "client_id": api_key, "per_page": 3, "orientation": "landscape"}
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return [{"url": item['urls']['small'], "photographer": item['user']['name'], "link": item['links']['html']} for item in response.json()['results']]
    except: return []
    return []

# 레이아웃 균형(대칭도) 분석
# ★ [수리 완료] 더 튼튼해진 균형 분석기 (디버깅 기능 추가)
def analyze_layout_balance(image):
    # 1. 이미지를 흑백으로 변환
    img_array = np.array(image)
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # 2. 노이즈 제거 (블러링)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # 3. 윤곽선 따기 (Threshold를 조금 더 민감하게 조정)
    edges = cv2.Canny(blurred, 30, 150)
    
    # 4. 반으로 뚝 자르기
    h, w = edges.shape
    center_x = w // 2
    
    # 왼쪽, 오른쪽 픽셀 수 세기 (int64로 변환해서 숫자 터짐 방지!)
    left_part = edges[:, :center_x]
    right_part = edges[:, center_x:]
    
    l_sum = np.sum(left_part, dtype=np.int64)
    r_sum = np.sum(right_part, dtype=np.int64)
    
    # ★ [디버깅] 균형 분석 출력
    print(f"👀 [균형 분석] 왼쪽 점수: {l_sum}, 오른쪽 점수: {r_sum}")
    
    # 5. 점수 계산 (0으로 나누기 방지)
    total = l_sum + r_sum
    if total == 0:
        return 0.0 # 아무것도 없으면 0점
        
    diff = abs(l_sum - r_sum)
    balance_score = 100 - (diff / total * 100)
    
    # 6. 마이너스 점수 방지 (최소 0점)
    return max(0.0, balance_score)

# 이미지 DNA 분석 엔진 (색상, 구조, 무드 통합)
def analyze_image_dna(image):
    img_rgb = image.convert('RGB')
    resized_img = img_rgb.resize((400, 400))
    img_array = np.array(resized_img)
    
    # 구조 분석
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 100, 200)
    complexity = (np.count_nonzero(edges) / edges.size) * 300 
    balance = analyze_layout_balance(resized_img)
    
    # 색상 분석
    pixels = img_array.reshape(-1, 3)
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10).fit(pixels)
    counts = np.unique(kmeans.labels_, return_counts=True)[1]
    sorted_colors = [kmeans.cluster_centers_.astype(int)[i] for i in np.argsort(counts)[::-1]]
    
    dominant = sorted_colors[0]
    h_dom, s_dom, v_dom = colorsys.rgb_to_hsv(dominant[0]/255, dominant[1]/255, dominant[2]/255)
    
    # 배경 무시 (흰/검)
    if (v_dom > 0.9 and s_dom < 0.1) or (v_dom < 0.15): 
        dominant = sorted_colors[1]
    
    # ★ [여기가 핵심 변경!] 파란색을 따로 분류하는 로직
    r, g, b = dominant
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    mood = {}
    if s < 0.15: mood = {"kw": "Modern & Minimal", "icon": "🏢"}
    elif v < 0.3: mood = {"kw": "Luxury & Solid", "icon": "🎩"}
    elif 0.5 < h < 0.7: mood = {"kw": "Trust & Professional", "icon": "💼"} # 파란색 구출 성공!
    elif s > 0.5 and v > 0.6: mood = {"kw": "Energetic & Creative", "icon": "🎨"}
    else: mood = {"kw": "Natural & Calm", "icon": "🌿"}

    # 온도
    warm_score = sum([1 if c[0] > c[2] else -1 for c in sorted_colors])
    temp = "Warm" if warm_score > 0 else "Cool"

    return {
        "image": resized_img, "edges": edges, "colors": sorted_colors, 
        "counts": np.sort(counts)[::-1], "complexity": complexity, 
        "balance": balance, "temp": temp, "mood": mood, "dominant_rgb": dominant
    }
# 고급 AI 디자인 컨설팅 문구 생성
def get_advanced_consulting(dna):
    m = dna['mood']['kw']
    c = dna['complexity']
    b = dna['balance']
    t = dna['temp']
    
    # 1. 구조 멘트 (더 세분화)
    if c < 2.0: struct = "요소를 극도로 절제한 **미니멀리즘**의 정수입니다."
    elif c < 5.0: struct = "간결하면서도 필요한 조형미를 갖춘 **안정적인 구조**입니다."
    else: struct = "시각적 디테일이 풍부하여 **화려하고 정보지향적**인 느낌을 줍니다."
    
    # 2. 대칭 멘트 (기준 점수 낮춤: 85 -> 75)
    # 사진이 조금 삐뚤어져도 대칭이라고 봐주기 위해 점수를 좀 후하게 줌!
    if b > 75: 
        balance_msg = "좌우 대칭이 균형을 이루어 **신뢰감과 질서**가 느껴집니다."
    else: 
        balance_msg = "비대칭적인 레이아웃으로 **자유롭고 역동적인 리듬감**이 돋보입니다."
    
    # 3. 색상 멘트 (멀티 컬러 대응)
    if t == "Dynamic Multi":
        color_p = "다양한 색상을 사용하여 **창의적이고 통합적인(Diversity)** 브랜드 이미지를 전달합니다."
    else:
        color_p = f"**{t}톤**을 주조색으로 사용하여 "
        color_p += "친근하고 따뜻한" if t == "Warm" else "이성적이고 차분한"
        color_p += " 무드를 형성합니다."
    
    return f"""
    ### 🤖 AI 전문 디자인 컨설팅 리포트
    
    **[종합 분석 요약]**
    이 디자인은 **{m}** 스타일로 분석됩니다.
    
    * **구조적 특징:** {struct}
    * **레이아웃:** {balance_msg}
    * **색상 전략:** {color_p}
    """

# PDF 리포트 생성 함수
def create_pdf_report(dna, advice_text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # 헤더 디자인
    c.setFont("Helvetica-Bold", 22)
    c.setStrokeColorRGB(1, 0.3, 0.3)
    c.line(50, height - 50, width - 50, height - 50)
    c.drawString(50, height - 85, "Mood-DNA : Design Analysis Report")
    
    # 요약 정보
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 120, f"Analysis Result: {dna['mood']['kw']}")
    c.drawString(50, height - 135, f"Visual Complexity: {dna['complexity']:.1f}% | Balance: {dna['balance']:.1f}%")

    # 원본 이미지 & 구조 이미지 나란히 배치
    img_buffer = io.BytesIO()
    dna['image'].save(img_buffer, format='PNG')
    img_buffer.seek(0)
    c.drawImage(ImageReader(img_buffer), 50, height - 380, width=230, height=200, preserveAspectRatio=True)
    
    edge_img = Image.fromarray(dna['edges'])
    edge_buffer = io.BytesIO()
    edge_img.save(edge_buffer, format='PNG')
    edge_buffer.seek(0)
    c.drawImage(ImageReader(edge_buffer), 310, height - 380, width=230, height=200, preserveAspectRatio=True)

    # 컬러 팔레트 그리기
    c.drawString(50, height - 420, "Color Palette (DNA Code):")
    x_pos = 50
    for color in dna['colors']:
        r, g, b = color[0]/255, color[1]/255, color[2]/255
        c.setFillColorRGB(r, g, b)
        c.rect(x_pos, height - 460, 45, 30, fill=1, stroke=0)
        c.setFillColorRGB(0, 0, 0)
        hex_val = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
        c.setFont("Helvetica", 9)
        c.drawString(x_pos, height - 475, hex_val)
        x_pos += 65

    # 텍스트 의견 (영문 요약)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 510, "AI Consultant Opinion (Summary)")
    c.setFont("Helvetica", 11)
    c.drawString(50, height - 530, f"1. Structural Assessment: The design complexity is {dna['complexity']:.1f}%.")
    c.drawString(50, height - 545, f"2. Balance & Symmetry: Measured at {dna['balance']:.1f}%.")
    c.drawString(50, height - 560, f"3. Recommendation: Optimized for {dna['mood']['kw']} branding.")

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# -----------------------------------------------------------
# [Main UI 섹션]
# -----------------------------------------------------------

st.title("🧬 Mood-DNA : AI 디자인 무드 분석기")
st.sidebar.markdown("### 🛠️ Configuration")
mode = st.sidebar.radio("모드 선택", ["단일 분석 (Single)", "A/B 비교 (Comparison)"])

# --- [모드 1] 단일 분석 ---
if mode == "단일 분석 (Single)":
    file = st.sidebar.file_uploader("디자인 파일 업로드", type=['jpg','png','jpeg'])
    
    if file:
        with st.spinner("이미지 DNA 추출 중..."):
            dna = analyze_image_dna(Image.open(file))
            advice = get_advanced_consulting(dna)
        
        # 1. 상단 지표 대시보드
        st.write("### 📊 Analysis Overview")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Main Mood", dna['mood']['kw'], dna['mood']['icon'])
        col2.metric("Complexity", f"{dna['complexity']:.1f}%")
        col3.metric("Layout Balance", f"{dna['balance']:.1f}%")
        col4.metric("Color Temp", dna['temp'])
        
        # 2. 중앙 상세 분석 시각화
        st.write("---")
        c_left, c_mid, c_right = st.columns([1.5, 1, 1.2])
        with c_left:
            st.subheader("🖼️ Original DNA")
            st.image(dna['image'], use_container_width=True)
        with c_mid:
            st.subheader("📐 Structure")
            st.image(dna['edges'], use_container_width=True)
            st.caption("AI가 인식한 선과 형태의 밀도")
        with c_right:
            st.subheader("🎨 Color Palette")
            for i, color in enumerate(dna['colors']):
                hex_c = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                ratio = (dna['counts'][i] / sum(dna['counts'])) * 100
                st.markdown(f'''
                    <div style="display:flex;align-items:center;margin-bottom:10px;">
                        <div style="background-color:{hex_c};width:45px;height:22px;border-radius:4px;border:1px solid #ddd;"></div>
                        <div style="margin-left:12px;font-size:14px;font-family:monospace;">{hex_c} ({ratio:.1f}%)</div>
                    </div>
                ''', unsafe_allow_html=True)

        # 3. AI 컨설팅 카드 & PDF 다운로드
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        st.markdown(advice)
        st.markdown('</div>', unsafe_allow_html=True)
        
        pdf_file = create_pdf_report(dna, advice)
        st.download_button(label="📄 전문 분석 리포트 PDF 다운로드", data=pdf_file, file_name="Mood_DNA_Report.pdf", mime="application/pdf")

        # 4. 레퍼런스 추천
        st.write("---")
        st.subheader("🖼️ AI Recommended References")
        recs = search_unsplash(dna['mood']['kw'].replace("&", ""), dna['dominant_rgb'], dna['complexity'])
        if recs:
            cols = st.columns(3)
            for i, r in enumerate(recs):
                with cols[i]:
                    st.image(r['url'], use_container_width=True)
                    st.caption(f"by {r['photographer']} [Link]({r['link']})")

# --- [모드 2] A/B 비교 ---
elif mode == "A/B 비교 (Comparison)":
    st.header("⚖️ A/B Test : 시안 비교 분석")
    col_u1, col_u2 = st.columns(2)
    with col_u1: fa = st.file_uploader("A안 업로드", type=['jpg','png'], key="a")
    with col_u2: fb = st.file_uploader("B안 업로드", type=['jpg','png'], key="b")
    
    if fa and fb:
        da, db = analyze_image_dna(Image.open(fa)), analyze_image_dna(Image.open(fb))
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            st.image(da['image'], caption="A안", use_container_width=True)
            st.metric("Mood", da['mood']['kw'])
            st.metric("Complexity", f"{da['complexity']:.1f}%")
            with st.expander("A안 상세 리포트"): st.markdown(get_advanced_consulting(da))
        with c2:
            st.image(db['image'], caption="B안", use_container_width=True)
            st.metric("Mood", db['mood']['kw'])
            st.metric("Complexity", f"{db['complexity']:.1f}%")
            with st.expander("B안 상세 리포트"): st.markdown(get_advanced_consulting(db))
        
        st.write("---")
        better = "A안" if da['complexity'] < db['complexity'] else "B안"
        st.success(f"⚖️ **종합 판정:** 구조적으로 더 미니멀하고 간결한 디자인은 **{better}**입니다.")