import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="TV Thermal Mech-Design", layout="wide")
st.title("📺 TV 내부 공기 대류 및 기구 반영 열해석")

# --- 사이드바: 기구 및 물리 설정 ---
with st.sidebar:
    st.header("📏 기구 설계 사양")
    inch = st.slider("TV 크기 (인치)", 32, 85, 55)
    
    st.subheader("📦 보드 설정")
    bx_rel = st.slider("보드 X 위치 (%)", 0, 100, 50)
    by_rel = st.slider("보드 Y 위치 (%)", 0, 100, 40)
    b_size = st.slider("보드 크기 (mm)", 50, 300, 150)
    heat_w = st.number_input("보드 발열량 (W)", value=30)
    
    st.subheader("🛡️ Cover-Rear 설정")
    cover_thick = st.slider("Cover 두께 (mm)", 1.0, 5.0, 2.0, step=0.5)
    gap_dist = st.slider("Board-Cover 간격 (Gap, mm)", 1, 50, 10)
    
    st.subheader("🌡️ 환경 계수")
    # 대류 열전달 계수 (공기 자연대류 보통 5~25)
    h_coeff = st.slider("대류 계수 (h, W/m²K)", 5, 50, 10)

# --- 열해석 엔진 ---
def run_advanced_sim():
    # 격자 설정 (10mm 단위)
    width = int(inch * 25.4 * 0.87 / 10)
    height = int(inch * 25.4 * 0.49 / 10)
    grid = np.full((width, height), 25.0) # 초기 온도 25도
    
    # 보드 좌표 및 크기 계산
    bx = int(width * bx_rel / 100)
    by = int(height * by_rel / 100)
    bs = int(b_size / 10)
    
    # 물리 상수 계산
    # Gap이 좁을수록 전도에 가까워지고, 넓을수록 대류 효율 변화 (단순화 모델)
    thermal_resistance_gap = gap_dist / (0.026 * 1.0) # 공기 열전도도 0.026 가정
    eff_alpha = (1.0 / (thermal_resistance_gap + (cover_thick / 0.2))) * 0.5
    
    # 시뮬레이션 루프 (반복 계산으로 평형 온도 도달)
    for _ in range(150):
        # 1. 주변 전도 (2D 확산)
        center = grid[1:-1, 1:-1]
        grid[1:-1, 1:-1] = center + eff_alpha * (
            grid[:-2, 1:-1] + grid[2:, 1:-1] + 
            grid[1:-1, :-2] + grid[1:-1, 2:] - 4 * center
        )
        
        # 2. 보드 영역 발열 주입
        # Gap이 작을수록 보드 열이 커버에 더 직접적으로 전달됨
        heat_impact = (heat_w / (gap_dist * 0.5)) * 0.2
        grid[bx:bx+bs, by:by+bs] += heat_impact
        
        # 3. 외부 대류 냉각 (h 계수 반영)
        grid -= (grid - 25.0) * (h_coeff * 0.0001)

    return grid, width, height

# --- 결과 시각화 ---
if st.button("🚀 해석 시뮬레이션 시작"):
    result, w, h = run_advanced_sim()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("🔥 Rear-Cover 표면 온도 분포")
        fig, ax = plt.subplots(figsize=(10, 5))
        im = ax.imshow(result.T, cmap='magma', origin='lower', extent=[0, w*10, 0, h*10])
        plt.colorbar(im, label="Temp (°C)")
        ax.set_xlabel("Width (mm)")
        ax.set_ylabel("Height (mm)")
        st.pyplot(fig)
        
    with col2:
        st.subheader("📊 해석 데이터")
        max_t = np.max(result)
        st.metric("최고 온도 (Hotspot)", f"{max_t:.1f} °C")
        
        # 설계 가이드 메시지
        if max_t > 65:
            st.error("⚠️ 경고: 커버 온도가 너무 높습니다. Gap을 키우거나 두께를 조절하세요.")
        elif max_t > 45:
            st.warning("ℹ️ 주의: 온도가 다소 높습니다. 방열 구멍 검토가 필요할 수 있습니다.")
        else:
            st.success("✅ 안전: 현재 기구 설계상 온도가 안정적입니다.")
            
        st.info(f"""
        **설계 조건:**
        - Gap: {gap_dist}mm
        - Thickness: {cover_thick}mm
        - 대류냉각 반영됨
        """)
