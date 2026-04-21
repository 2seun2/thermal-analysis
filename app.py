import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 웹페이지 기본 설정
st.set_page_config(page_title="TV Thermal Mech-Design Pro", layout="wide")
st.title("📺 TV 기구 열해석 시뮬레이터 (발열원 온도 기반)")

# --- 1. 사이드바: 설계 및 환경 설정 ---
with st.sidebar:
    st.header("📏 기구 설계 사양")
    inch = st.slider("TV 크기 (인치)", 32, 85, 55)
    
    st.subheader("📦 보드(Board) 설정")
    # 사용자의 요청대로 '목표 온도'가 아닌 '보드 자체의 발열 온도'로 설정
    board_heat_temp = st.number_input("보드 발생 열온도 (°C)", value=80, min_value=0, max_value=200)
    
    bx_rel = st.slider("보드 X 위치 (%)", 0, 100, 50)
    by_rel = st.slider("보드 Y 위치 (%)", 0, 100, 40)
    b_size_mm = st.slider("보드 크기 (mm)", 50, 300, 150)
    
    st.subheader("🛡️ Cover-Rear 설정")
    cover_thick = st.slider("Cover 두께 (mm)", 1.0, 5.0, 2.0, step=0.5)
    gap_dist = st.slider("Board-Cover 간격 (Gap, mm)", 1, 50, 10)
    
    st.subheader("⏳ 시뮬레이션 설정")
    # 가동 시간 설정 추가
    sim_time_hr = st.slider("총 가동 시간 (Hours)", 1, 24, 5)
    h_coeff = st.slider("대류 냉각 계수 (h)", 5, 50, 12)

# --- 2. 물리 계산 엔진 ---

tv_w_mm = int(inch * 25.4 * 0.87)
tv_h_mm = int(inch * 25.4 * 0.49)

@st.cache_data
def run_thermal_simulation(t_w, t_h, b_heat_t, b_x_r, b_y_r, b_s_mm, c_t, g_d, h_c, s_time):
    # 격자 설정 (계산 속도를 위해 15mm 단위 격자)
    scale = 15
    nx, ny = int(t_w / scale), int(t_h / scale)
    grid = np.zeros((nx, ny)) # 주변 온도를 제외한 순수 상승 온도를 위해 0으로 시작
    
    bx = int(nx * b_x_r / 100)
    by = int(ny * b_y_r / 100)
    bs = int(b_s_mm / scale)
    bx_e, by_e = min(bx+bs, nx), min(by+bs, ny)
    
    # 열저항 및 확산 계수 계산
    # Gap이 클수록 커버로 전달되는 열량 급감 (1/d 관계)
    conduction_rate = (1.0 / (g_d * 0.5 + c_t)) * 0.15
    cooling_rate = h_c * 0.0002
    
    time_history = []
    temp_history = []
    
    # 가동 시간에 따른 반복 횟수 결정 (1시간당 약 40스텝)
    total_steps = s_time * 40
    
    for step in range(total_steps + 1):
        # 1. 열 전도 계산
        center = grid[1:-1, 1:-1]
        grid[1:-1, 1:-1] += conduction_rate * (
            grid[:-2, 1:-1] + grid[2:, 1:-1] + 
            grid[1:-1, :-2] + grid[1:-1, 2:] - 4 * center
        )
        
        # 2. 보드 발열원 적용 (고정 발열 온도 소스)
        grid[bx:bx_e, by:by_e] = b_heat_t
        
        # 3. 냉각 효과
        grid -= grid * cooling_rate
        
        # 데이터 기록
        if step % 5 == 0 or step == total_steps:
            time_history.append(step / 40.0)
            temp_history.append(np.max(grid))

    return grid, time_history, temp_history

# --- 3. 화면 구성 ---
col_main, col_sub = st.columns([3, 1])

with col_sub:
    st.subheader("📍 실시간 배치")
    fig_l, ax_l = plt.subplots(figsize=(4, 3))
    ax_l.add_patch(patches.Rectangle((0, 0), tv_w_mm, tv_h_mm, color='white', ec='black', lw=2))
    bx_mm, by_mm = tv_w_mm * (bx_rel / 100), tv_h_mm * (by_rel / 100)
    ax_l.add_patch(patches.Rectangle((bx_mm, by_mm), b_size_mm, b_size_mm, color='red', alpha=0.6, label='Board'))
    ax_l.set_xlim(0, tv_w_mm); ax_l.set_ylim(0, tv_h_mm)
    ax_l.set_aspect('equal')
    st.pyplot(fig_l)
    st.write(f"보드 발열: {board_heat_temp}°C")
    st.write(f"설정 시간: {sim_time_hr}시간")

with col_main:
    if st.button("🚀 해석 시뮬레이션 시작"):
        res_grid, t_axis, temp_axis = run_thermal_simulation(
            tv_w_mm, tv_h_mm, board_heat_temp, bx_rel, by_rel, 
            b_size_mm, cover_thick, gap_dist, h_coeff, sim_time_hr
        )
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"🔥 {sim_time_hr}h 후 온도 분포")
            fig_m, ax_m = plt.subplots()
            im = ax_m.imshow(res_grid.T, cmap='hot', origin='lower', extent=[0, tv_w_mm, 0, tv_h_mm])
            plt.colorbar(im, label="Temperature Rise (°C)")
            st.pyplot(fig_m)
            
        with c2:
            st.subheader("📈 시간별 최고 온도 상승 곡선")
            fig_t, ax_t = plt.subplots()
            ax_t.plot(t_axis, temp_axis, color='red', linewidth=2)
            ax_t.set_xlabel("Time (Hours)")
            ax_t.set_ylabel("Temp (°C)")
            ax_t.grid(True, alpha=0.3)
            st.pyplot(fig_t)
            st.metric("최종 도달 온도", f"{temp_axis[-1]:.1f} °C")
