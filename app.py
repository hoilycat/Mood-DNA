import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import colorsys
from sklearn.cluster import KMeans
import cv2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

# -----------------------------------------------------------
# 1. [함수] AI 컨설팅 메시지 생성기 (NEW! ✨)
# -----------------------------------------------------------
def get_ai_consulting(mood_data, complexity):
    # 1. 구조(복잡도)에 따른 조언
    struct_comment = ""
    if complexity < 2:
        struct_comment = "이 디자인은 **여백의 미(Negative Space)**를 아주 잘 활용하고 있어요. 사용자의 시선을 핵심 요소로 집중시키는 **'미니멀리즘 전략'**이 돋보입니다."
    elif complexity < 5:
        struct_comment = "이미지와 텍스트의 비율이 **이상적인 균형(Balance)**을 이루고 있습니다. 너무 비어 보이지도, 복잡하지도 않아 **가독성**이 매우 좋습니다."
    else:
        struct_comment = "밀도 높은 그래픽과 디테일이 **풍부한 정보**를 전달하고 있습니다. 화려한 비주얼로 압도해야 하는 **이벤트나 프로모션** 디자인에 적합합니다."

    # 2. 분위기(Mood)에 따른 마케팅 조언
    mood_comment = ""
    keyword = mood_data['keyword']
    
    if "Modern" in keyword:
        mood_comment = "도시적이고 세련된 컬러감은 **IT, 테크, 스타트업** 브랜드의 신뢰도를 높이는 데 효과적입니다."
    elif "Luxury" in keyword:
        mood_comment = "중후하고 깊이 있는 톤은 **프리미엄 제품**이나 **VIP 타겟 서비스**의 품격을 대변하기 좋습니다."
    elif "Energetic" in keyword:
        mood_comment = "통통 튀는 고채도 컬러는 **MZ세대**를 타겟으로 하거나, **클릭률(CTR)**을 높여야 하는 광고 소재로 아주 훌륭합니다."
    else: # Natural
        mood_comment = "눈이 편안한 저채도 컬러는 **웰빙, 라이프스타일, 에세이** 등 감성을 자극하는 분야에서 독보적인 분위기를 만듭니다."

    # 3. 최종 합치기
    full_advice = f"""
    💡 **AI 디자인 컨설턴트의 총평:**
    
    {struct_comment} 또한, {mood_comment}
    
    종합적으로 보았을 때, 이 시안은 **[{keyword}]** 무드를 통해 타겟 고객에게 강력한 시각적 경험을 제공할 수 있는 잠재력이 있습니다.
    """
    return full_advice

# -----------------------------------------------------------
# 2. [함수] 분석 로봇
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
    
    # 무드 판정
    dominant_color = sorted_colors[0]
    r, g, b = int(dominant_color[0]), int(dominant_color[1]), int(dominant_color[2])
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
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
        "mood": mood_result
    }

# -----------------------------------------------------------
# 3. [함수] PDF 리포트 생성기
# -----------------------------------------------------------
def create_pdf_report(dna_data, advice_text):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "Mood-DNA Analysis Report")
    
    # 기본 정보
    mood = dna_data['mood']
    c.setFont("Helvetica", 14)
    c.drawString(50, height - 100, f"Main Mood: {mood['keyword']}")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 130, f"Structure Complexity: {dna_data['complexity']:.2f}%")
    
    # 컨설팅 내용 (PDF에는 영문이나 단순화해서 넣는 게 안전하지만, 일단 형식만 갖춤)
    c.drawString(50, height - 160, "AI Consultant Comment:")
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, height - 180, f"This design shows {mood['keyword']} style with {dna_data['complexity']:.2f}% complexity.")
    c.drawString(50, height - 195, "It is suitable for the target audience matching this mood.")
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# -----------------------------------------------------------
# 4. 메인 화면 (UI)
# -----------------------------------------------------------
st.set_page_config(page_title="Mood-DNA Pro", page_icon="🧬", layout="wide")

st.title("🧬 Mood-DNA : AI 디자인 무드 분석기")

st.sidebar.header("🎛️ 분석 모드 설정")
mode = st.sidebar.radio("모드를 선택하세요:", ["단일 분석 (Single)", "A/B 비교 (Comparison)"])

# ===========================================================
# 모드 1: 단일 분석
# ===========================================================
if mode == "단일 분석 (Single)":
    st.sidebar.markdown("---")
    uploaded_file = st.sidebar.file_uploader("이미지 업로드", type=['jpg', 'png', 'jpeg'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        dna = analyze_image_dna(image)
        
        # ★ 여기서 AI 조언 생성!
        ai_advice = get_ai_consulting(dna['mood'], dna['complexity'])
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.image(dna['image'], caption="원본 이미지", use_container_width=True)
        with col2:
            st.image(dna['edges'], caption=f"구조 분석 (복잡도: {dna['complexity']:.2f}%)", use_container_width=True)
            
        st.info(f"🧬 분석 결과: **[{dna['mood']['keyword']}]** {dna['mood']['icon']}\n\n{dna['mood']['desc']}")
        
        # ★ [NEW] AI 컨설팅 메시지 보여주기 (파란 박스 대신 깔끔한 예쁜 박스로!)
        st.markdown(f"""
        <div style="background-color:#f9f9f9; padding:20px; border-radius:10px; border-left: 5px solid #6c5ce7;">
            {ai_advice}
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("🎨 Color Palette")
            for i, color in enumerate(dna['colors']):
                hex_code = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                st.markdown(f'<div style="background-color:{hex_code};height:40px;border-radius:5px;margin-bottom:5px;"></div>', unsafe_allow_html=True)
                st.caption(f"{hex_code}")
                
        with c2:
            st.subheader("📊 Color Ratio")
            fig, ax = plt.subplots(figsize=(4, 3))
            sorted_hex = ['#{:02x}{:02x}{:02x}'.format(c[0],c[1],c[2]) for c in dna['colors']]
            sorted_colors_norm = [c/255 for c in dna['colors']]
            ax.pie(dna['counts'], labels=sorted_hex, colors=sorted_colors_norm, autopct='%1.1f%%', textprops={'fontsize': 8})
            st.pyplot(fig)

        st.write("---")
        pdf_bytes = create_pdf_report(dna, ai_advice)
        st.download_button(
            label="📄 분석 리포트 PDF 다운로드",
            data=pdf_bytes,
            file_name="mood_dna_report.pdf",
            mime="application/pdf"
        )

# ===========================================================
# 모드 2: A/B 비교 (Comparison) - 수리 완료 버전! 🛠️
# ===========================================================
elif mode == "A/B 비교 (Comparison)":
    st.header("⚖️ A/B Test : 디자인 시안 비교")
    st.write("두 개의 이미지를 업로드하여 **매력도와 무드**를 비교분석합니다.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        file_a = st.file_uploader("A안 이미지", type=['jpg', 'png'], key="a")
    with col_b:
        file_b = st.file_uploader("B안 이미지", type=['jpg', 'png'], key="b")
        
    if file_a and file_b:
        st.write("---")
        # 분석 실행
        dna_a = analyze_image_dna(Image.open(file_a))
        dna_b = analyze_image_dna(Image.open(file_b))
        
        # AI 조언 생성
        advice_a = get_ai_consulting(dna_a['mood'], dna_a['complexity'])
        advice_b = get_ai_consulting(dna_b['mood'], dna_b['complexity'])

        c1, c2 = st.columns(2)
        
        # [A안 결과 화면]
        with c1:
            st.image(dna_a['image'], caption="[A안]", use_container_width=True)
            st.success(f"**{dna_a['mood']['keyword']}**")
            st.write(f"구조 복잡도: {dna_a['complexity']:.2f}%")
            
            # ★ [수리 포인트] 글자수 제한 풀고 '접었다 펴기'로 변경!
            with st.expander("💡 AI 상세 분석 읽기"):
                st.write(advice_a)
            
        # [B안 결과 화면]
        with c2:
            st.image(dna_b['image'], caption="[B안]", use_container_width=True)
            st.success(f"**{dna_b['mood']['keyword']}**")
            st.write(f"구조 복잡도: {dna_b['complexity']:.2f}%")
            
            # ★ [수리 포인트] 여기도 제한 해제!
            with st.expander("💡 AI 상세 분석 읽기"):
                st.write(advice_b)
            
        st.write("---")
        st.subheader("🤖 AI의 비교 코멘트")
        
        # 비교 로직
        diff = abs(dna_a['complexity'] - dna_b['complexity'])
        if diff > 5:
            winner = "A안" if dna_a['complexity'] < dna_b['complexity'] else "B안"
            comment = f"두 시안은 구조적으로 큰 차이가 있습니다. **{winner}**이 훨씬 **미니멀하고 직관적**입니다. 정보 전달이 목적이라면 {winner}을, 화려함이 목적이라면 반대안을 선택하세요."
        else:
            comment = "두 시안의 구조적 복잡도는 비슷합니다. **브랜드 컬러 아이덴티티**에 더 부합하는 쪽을 선택하는 것을 추천합니다."
            
        st.info(comment)

else:
    st.sidebar.info("👈 왼쪽에서 모드를 선택하고 이미지를 업로드해주세요!")