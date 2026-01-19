import streamlit as st
from PIL import Image
import numpy as  np
from sklearn.cluster import KMeans

st.title("안녕? 나는 DNA야")
uploaded_file = st.file_uploader("분석할 사진을 선택하거나 여기로 드래그하세요!", type=['jpg','png','jpeg'])
if uploaded_file is not None:
    image =Image.open(uploaded_file)
    st.image(image, caption='업로드된 사진',use_container_width=True)
    st.write("사진의 색깔 DNA를 분석 중이야")
    
    img_array = np.array(image)
    pixels = img_array.reshape(-1,3)
    
    kmeans = KMeans(n_clusters=5)
    kmeans.fit(pixels)
    colors= kmeans.cluster_centers_.astype(int)
    
    st.success("분석 완료! 이 사진의 무드 DNA는 이거야!")
    
    st.write("### 추출된 5가지 메인 컬러")
    
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