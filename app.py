import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# 1. 재질 및 부품 데이터 (선택 가능하도록 구성)
MATERIAL_DATA = {
    "Plastic (ABS)": {"k": 0.25, "density": 1050},
    "Aluminum 6061": {"k": 167.0, "density": 2700},
    "Steel (SECC)": {"k": 50.0, "density": 7850},
    "PCB (FR-4)": {"k": 0.3, "density": 1850}
}

st.set_page_config(page_title="TV Thermal Analyzer", layout="wide")
st.title("📺 TV 내부 부품별 열해석 시뮬레이터")

# 2. 사이드바 입력창
with st.sidebar:
    st.header("🛠 설정 파라미터")
    inch = st.slider("TV 크기 (인치)", 32, 85, 55)
    
    st.subheader("📍 보드(Board) 설정")
    bx_rel = st.slider("보드 X 위치 (%)", 0, 100, 50)
    by_rel = st.slider("보드 Y 위치 (%)", 0, 100, 40)
    heat_w = st.number_input("보드 발열량 (W)", value=25)
    
    st.subheader("🧪 재질 및 환경")
    mat_choice = st.selectbox("TV 케이스 재질 선택", list(MATERIAL_DATA.keys()))
    k_val = MATERIAL_DATA[mat_choice]["k"]
    sim_hours = st.number_input("가동 시간 (hour)", value=1)

# 3. 열해석 엔진 (FDM 방식)
def run_thermal_analysis():
    # TV 규격 변환 (mm)
    width = int(inch * 25.4 * 0.87 / 10) # 계산 속도를 위해 10mm 격자
    height = int(inch * 25.4 * 0.49 / 10)
    
    # 초기 상태 (상온 25도)
    grid = np.full((width, height), 25.0)
    
    # 보드 위치 및 크기 (고정 크기 가정)
    bx, by = int(width * bx_rel / 100), int(height * by_rel / 100)
    bw, bh = 5, 5 # 50mm x 50mm 보드
    
    # 열확산 계수 (alpha) 단순화 모델
    alpha = k_val * 0.1
    
    # 시간 스텝 반복
    for _ in range(200): # 시뮬레이션 반복 횟수
        # 주변 전도 계산
        grid[1:-1, 1:-1] += alpha * (
            grid[:-2, 1:-1] + grid[2:, 1:-1] + 
            grid[1:-1, :-2] + grid[1:-1, 2:] - 4 * grid[1:-1, 1:-1]
        )
        # 보드 발열 적용
        grid[bx:bx+bw, by:by+bh] += (heat_w * 0.05)
        
    return grid

# 4. 결과 출력
if st.button("🔥 열해석 실행"):
    with st.spinner('계산 중...'):
        result_map = run_thermal_analysis()
        
        col1, col2 = st.columns([3, 1])
        with col1:
            fig, ax = plt.subplots()
            im = ax.imshow(result_map.T, cmap='jet', origin='lower')
            plt.colorbar(im, label="Temp (°C)")
            ax.set_title(f"{inch} inch TV Thermal Map ({mat_choice})")
            st.pyplot(fig)
            
        with col2:
            st.metric("최고 온도", f"{np.max(result_map):.1f} °C")
            st.metric("평균 온도", f"{np.mean(result_map):.1f} °C")
            st.success("해석이 완료되었습니다.")
