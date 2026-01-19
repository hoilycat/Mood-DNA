import streamlit as st
from PIL import Image
st.title("안녕? 나는 DNA야")
upload_file = st.file_uploader("분석할 사진을 선택하거나 여기로 드래그하세요!")
if uploaded_file is not None:
    image =Image.open(uploaded_file)
    st.image(image, cpation='업로드된 사진',use_container_width=True)
    st.success("사진 업로드 성공!")