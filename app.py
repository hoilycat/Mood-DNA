import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import colorsys
from sklearn.cluster import KMeans
import cv2

# 1. 페이지 설정 (탭 이름이랑 아이콘 바꾸기)
st.set_page_config(page_title="Mood-DNA 분석기", page_icon="🧬", layout="wide")

st.title("🧬 Mood-DNA : 디자인 무드 분석 솔루션")
st.markdown("---")

# 2. [변경] 사이드바(Sidebar) 만들기 - 도구함
# st.sidebar 를 쓰면 왼쪽에 별도 공간이 생겨!
st.sidebar.header("📂 이미지 업로드")
st.sidebar.write("분석할 디자인 시안이나 사진을 올려주세요.")
uploaded_file = st.sidebar.file_uploader("파일 선택", type=['jpg', 'png', 'jpeg'])

if uploaded_file is not None:
    # 이미지 열기 & 변환
    image = Image.open(uploaded_file)
    image = image.convert('RGB')
    
    # 속도 빠르게 줄이기
    resized_image = image.resize((400, 400))
    img_array = np.array(resized_image)
    pixels = img_array.reshape(-1, 3)
    
    # K-Means 분석
    kmeans = KMeans(n_clusters=5)
    kmeans.fit(pixels)
    colors = kmeans.cluster_centers_.astype(int)
    
    # ------------------------------------------------
    # 3. [변경] 레이아웃 나누기 (2단 컬럼)
    # 왼쪽(col1)엔 사진, 오른쪽(col2)엔 그래프를 둘 거야!
    col1, col2 = st.columns([1, 1]) # 1:1 비율로 나누기
    
    with col1:
        st.subheader("📸 원본 이미지")
        st.image(image, use_container_width=True)
        
    with col2:
        st.subheader("📊 색상 비율 분석")
        
        # 파이 차트 그리기
        fig, ax = plt.subplots(figsize=(6, 4)) # 크기 조절
        unique, counts = np.unique(kmeans.labels_, return_counts=True)
        
        sorted_indices = np.argsort(counts)[::-1]
        sorted_counts = counts[sorted_indices]
        sorted_colors = [colors[i] for i in sorted_indices]
        sorted_hex = ['#{:02x}{:02x}{:02x}'.format(c[0],c[1],c[2]) for c in sorted_colors]
        sorted_colors_norm = [c/255 for c in sorted_colors]
        
        ax.pie(sorted_counts, labels=sorted_hex, colors=sorted_colors_norm, autopct='%1.1f%%', textprops={'fontsize': 10})
        st.pyplot(fig)
    
    # ------------------------------------------------
# ... (위에는 파이 차트 그리는 코드) ...
    st.pyplot(fig)  # <-- 기존 코드 끝나는 곳

    # ------------------------------------------------
    # 🦴 [NEW] Step 1. 형태(Shape) 분석 - OpenCV
    # ------------------------------------------------
    st.write("---")
    st.subheader("📐 디자인 구조(Structure) 분석")
    st.write("이미지의 윤곽선을 추출하여 **복잡도**와 **직선/곡선 성향**을 분석합니다.")

    # 1. OpenCV는 이미지를 읽을 때 색깔 순서가 반대(BGR)라서 RGB로 바꿔줘야 해! (넘파이 배열 활용)
    # 아까 만든 resized_image(작은 사진)를 쓰자!
    open_cv_image = np.array(resized_image) 
    
    # 2. 흑백으로 변환 (윤곽선은 흑백일 때 제일 잘 보여!)
    gray_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2GRAY)
    
    # 3. Canny Edge Detection (윤곽선 따기 마법)
    # 숫자 100, 200은 "얼마나 진한 선만 남길래?" 하는 기준이야.
    edges = cv2.Canny(gray_image, 100, 200)

    # 4. 분석 로직: 흰색 점(선)이 얼마나 많은가?
    # 전체 픽셀 수 대비 선이 차지하는 비율 계산
    total_pixels = edges.size
    edge_pixels = np.count_nonzero(edges)
    complexity_ratio = (edge_pixels / total_pixels) * 100
    
    # 5. 복잡도 판정 (단순함 vs 복잡함)
    if complexity_ratio < 2:
        struct_mood = "Minimal & Simple (단순함/여백)"
        struct_desc = "윤곽선이 적고 여백이 많습니다. 미니멀하고 깔끔한 디자인입니다."
        struct_icon = "⬜"
    elif complexity_ratio < 5:
        struct_mood = "Balanced (균형 잡힘)"
        struct_desc = "적당한 밀도의 조형미가 느껴집니다. 안정적인 구조입니다."
        struct_icon = "⚖️"
    else:
        struct_mood = "Complex & Detailed (복잡함/디테일)"
        struct_desc = "밀도가 높고 디테일이 많습니다. 화려하거나 정보량이 많은 디자인입니다."
        struct_icon = "🕸️"

    # 6. 화면에 보여주기 (컬럼 나눠서 비교!)
    col_img1, col_img2 = st.columns(2)
    
    with col_img1:
        st.caption("📷 원본 (Original)")
        st.image(resized_image, use_container_width=True)
        
    with col_img2:
        st.caption(f"🦴 구조 추출 (Edge) - 복잡도: {complexity_ratio:.2f}%")
        # 윤곽선 이미지는 흑백이라서 clamp 옵션이 필요해
        st.image(edges, use_container_width=True, clamp=True)
    
    # 구조 분석 결과 박스
    st.info(f"📐 구조 분석 결과: **[{struct_mood}]** {struct_icon}\n\n{struct_desc}")
    st.write("---")
    st.subheader("🎨 추출된 메인 컬러 팔레트")
    
    # 컬러 팔레트 보여주기
    pal_cols = st.columns(5)
    for i, color in enumerate(colors):
        hex_code = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
        color_code = f"rgb({color[0]},{color[1]},{color[2]})"
        
        with pal_cols[i]:
            st.markdown(
                f'<div style="background-color:{color_code}; width: 100%; height:60px; border-radius: 10px; margin-bottom: 10px;"></div>',
                unsafe_allow_html=True
            )
            st.markdown(f"**{hex_code}**")
            st.caption(f"Color {i+1}")

    # ------------------------------------------------
    
  # ------------------------------------------------
    # 4. [업그레이드] AI 분석 리포트 (HSV 로직 적용)
    st.write("---")
    st.subheader("📝 AI 디자인 분석 리포트")
    
    # 가장 많이 쓴 색깔 가져오기
    dominant_color = colors[0]
    r, g, b = int(dominant_color[0]), int(dominant_color[1]), int(dominant_color[2])
    
    # 1. RGB를 HSV(색상, 채도, 명도)로 변환하기
    # (컴퓨터는 0~1 사이 숫자로 계산하는 걸 좋아해서 255로 나눠줌)
    h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    
    # 2. HSV 값을 이용한 정밀 판독 로직 (if문의 마법!)
    # h(색상): 360도 원에서 위치, s(채도): 0~1, v(명도): 0~1
    
    mood_keyword = ""
    desc = ""
    icon = ""
    box_color = ""
    text_color = "#000000" # 글자색 기본 검정

    # (1) 무채색/어두운색 판별 (채도가 낮거나 명도가 낮음)
    if s < 0.2: 
        mood_keyword = "Modern & Minimal (모던/미니멀)"
        icon = "🏢"
        desc = "색감이 절제되어 세련되고 깔끔한 인상을 줍니다. 현대적이고 도시적인 브랜드에 어울려요."
        box_color = "#F0F0F0" # 회색 배경
    elif v < 0.3:
        mood_keyword = "Luxury & Heavy (고급/중후함)"
        icon = "🎩"
        desc = "어둡고 진한 컬러가 주를 이루어 중후하고 고급스러운 분위기를 풍깁니다. 프리미엄 라인에 추천해요."
        box_color = "#2b2b2b" # 진한 회색 배경
        text_color = "#ffffff" # 어두우니까 글자는 흰색으로!
        
    # (2) 유채색 판별 (색깔이 뚜렷함)
    else:
        # 채도가 높고 명도도 높으면 -> 쨍하고 밝음 (Vivid/Pop)
        if s > 0.5 and v > 0.5:
            mood_keyword = "Energetic & Pop (활기찬/팝)"
            icon = "🎉"
            desc = "채도가 높아 눈에 확 띄는 강렬한 에너지가 느껴집니다. 젊고 활동적인 타겟층에게 어필하기 좋아요."
            box_color = "#FFF8E1" # 밝은 노랑 배경
        # 그 외 (채도가 적당하거나 밝음) -> 자연스럽고 부드러움 (Natural/Soft)
        else:
            mood_keyword = "Natural & Soft (네추럴/소프트)"
            icon = "🌿"
            desc = "눈이 편안해지는 부드러운 색감입니다. 힐링, 감성, 자연주의 컨셉에 아주 잘 어울려요."
            box_color = "#E8F5E9" # 연한 초록 배경

    # 최종 리포트 출력
    st.markdown(f"""
    <div style="padding: 20px; background-color: {box_color}; border-radius: 10px; border: 1px solid #ddd;">
        <h3 style="color: {text_color};">{icon} {mood_keyword}</h3>
        <p style="color: {text_color};">{desc}</p>
        <hr>
        <p style="color: {text_color}; font-size: 0.9em;">
            <strong>📊 데이터 상세 분석:</strong><br>
            • 주조색(RGB): {r}, {g}, {b}<br>
            • 채도(Saturation): {int(s*100)}% (색의 선명도)<br>
            • 명도(Value): {int(v*100)}% (색의 밝기)
        </p>
    </div>
    """, unsafe_allow_html=True)