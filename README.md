🧬 Mood-DNA: AI 디자인 파트너 (v2.0)
Technical Highlights:

Computer Vision: OpenCV 기반 이미지 리사이징 및 RGB 변환 최적화.

Unsupervised Learning: K-Means 클러스터링을 활용한 도미넌트 컬러 추출 및 비율 시각화.

LLM Integration: Gemini API를 연동하여 타겟 사용자 맞춤형 디자인 컨설팅 제공.

Troubleshooting:

Issue: 배포 환경(Linux Headless)에서의 libGL.so.1 ImportError 발생.

Solution: opencv-python-headless로 의존성을 교체하여 GUI 환경 의존성 문제 해결 및 서버 경량화 달성.
