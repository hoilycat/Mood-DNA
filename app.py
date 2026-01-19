import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

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
    
    # 4. [변경] AI 분석 리포트 카드 만들기
    st.write("---")
    st.subheader("📝 AI 디자인 분석 리포트")
    
    dominant_color = colors[0]
    r, g, b = dominant_color[0], dominant_color[1], dominant_color[2]
    
    # 로직에 따라 메시지와 추천 키워드 생성
    if r > b:
        mood_title = "Warm & Energetic (따뜻함/열정)"
        icon = "🔥"
        desc = """
        이 이미지는 **난색(Red/Yellow) 계열**이 지배적입니다. 
        사람들의 시선을 끌거나, 식욕을 돋우거나, 긍정적인 에너지를 전달하는 디자인에 적합합니다.
        """
        keywords = ["#열정", "#에너지", "#친근함", "#주목성"]
        box_color = "#FFF4E6" # 연한 주황 배경
    else:
        mood_title = "Cool & Trust (차분함/신뢰)"
        icon = "❄️"
        desc = """
        이 이미지는 **한색(Blue/Green) 계열**이 지배적입니다.
        신뢰감을 주거나, 논리적인 정보를 전달하거나, 심리적인 안정을 주는 디자인에 적합합니다.
        """
        keywords = ["#신뢰", "#이성적", "#평온함", "#전문성"]
        box_color = "#E6F4FF" # 연한 파랑 배경

    # 예쁜 박스 안에 결과 넣기
    st.markdown(f"""
    <div style="padding: 20px; background-color: {box_color}; border-radius: 10px;">
        <h3>{icon} {mood_title}</h3>
        <p>{desc}</p>
        <p><strong>추천 키워드:</strong> {' '.join(keywords)}</p>
    </div>
    """, unsafe_allow_html=True)

else:
    # 파일이 없을 때 보여줄 안내 문구
    st.info("👈 왼쪽 사이드바에서 이미지를 업로드하면 분석이 시작됩니다!")