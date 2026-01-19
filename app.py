import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from sklearn.cluster import KMeans

st.title("안녕? 나는 용용이의 Mood-DNA야! 🧬")

uploaded_file = st.file_uploader("분석할 사진을 선택하거나 여기로 드래그하세요!", type=['jpg','png','jpeg'])

if uploaded_file is not None:
    # 1. 이미지 열기 & 변환
    image = Image.open(uploaded_file)
    image = image.convert('RGB')
    st.image(image, caption='업로드된 사진', use_container_width=True)
    st.write("🔍 **사진의 색깔 DNA를 분석 중이야...**")
    
    # 2. 속도 해결 (작게 줄이기)
    resized_image = image.resize((400,400)) 
    img_array = np.array(resized_image)
    pixels = img_array.reshape(-1,3)
    
    # 3. AI 분석 (K-Means)
    kmeans = KMeans(n_clusters=5)
    kmeans.fit(pixels)
    colors = kmeans.cluster_centers_.astype(int)
    
    st.success("분석 완료! 이 사진의 무드 DNA는 이거야!")
    
    # 4. 색깔 상자 보여주기
    st.write("### 🎨 추출된 5가지 메인 컬러")
    
    columns = st.columns(5)
    for i, color in enumerate(colors):
        color_code = f"rgb({color[0]},{color[1]},{color[2]})"
        hex_code = '#{:02x}{:02x}{:02x}'.format(color[0],color[1],color[2])
        
        with columns[i]:
            st.markdown(
                f'<div style="background-color:{color_code}; width: 100%; height:50px; border-radius:5px;"></div>',
                unsafe_allow_html=True
            )
            st.markdown(f"**{hex_code}**")
            st.caption(f"DNA{i+1}")
            
    # 5. 무드 온도계
    st.write("---")
    st.write("### 🌡️ 무드 온도계 분석")
            
    dominant_color = colors[0]
    r, g, b = dominant_color[0], dominant_color[1], dominant_color[2]
            
    if r > b:
        mood = "따뜻하고 열정적인(Warm)"
        icon = "🔥"
        msg = "이 사진은 활력이 넘치고 온기가 느껴져! 긍정적인 에너지가 뿜뿜!"
    else: 
        mood = "차분하고 이성적인(Cool)"
        icon = "❄️"
        msg = "이 사진은 마음을 가라앉히는 차분함이 느껴져, 지적인 분위기인걸?"
            
    st.info(f"이 사진의 메인 무드는 **[{mood}]**이야! {icon}")
    st.caption(msg)
    
    
    # 6. 차트 보여주기 (여기서부터 들여쓰기 필수!)
    st.write("---")
    st.write("### 📊 색깔 비율 분석(파이 차트)")

    fig, ax = plt.subplots(figsize=(8,2))
    unique, counts = np.unique(kmeans.labels_, return_counts=True)

    # 비율 순으로 정렬하기
    sorted_indices = np.argsort(counts)[::-1]
    sorted_counts = counts[sorted_indices]  # [수정] 오타 couints -> counts
    sorted_colors = [colors[i] for i in sorted_indices]
    sorted_hex = ['#{:02x}{:02x}{:02x}'.format(c[0],c[1],c[2]) for c in sorted_colors]

    # 실제 칠할 색상 값
    sorted_colors_norm = [c/255 for c in sorted_colors]
    
    # [수정] 오타 %1.1% -> %1.1f%%
    ax.pie(sorted_counts, labels=sorted_hex, colors=sorted_colors_norm, autopct='%1.1f%%', textprops={'fontsize':8})

    # 스트림릿에 그래프 띄우기
    st.pyplot(fig)