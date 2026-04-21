import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="TV Thermal Analysis Pro", layout="wide")
st.title("📺 TV 기구 열해석: 재질 및 지점별 온도 추이")

# --- 1. 사이드바 설정 ---
with st.sidebar:
    st.header("📏 설계 사양")
    inch = st.slider("TV 크기 (인치)", 32, 85, 55)
    
    # 재질 선택 추가
    st.subheader("🧪 Cover-Rear 재질")
    mat_type = st.radio("재질 선택", ["Engineering Plastic (ABS/PC)", "Metal (Aluminum/Steel)"])
    mat_k = 0.25 if "Plastic" in mat_type else 50.0  # 열전도 계수 설정
    
    st.subheader("📦 보드 설정")
    board_heat_temp = st.number_input("보드 발열 온도 (°C)", value=80)
    bx_rel = st.slider("보드 X 위치 (%)", 0, 100, 50)
    by_rel = st.slider("보드 Y 위치 (%)", 0, 100, 40)
    b_size_mm = st.slider("보드 크기 (mm)", 50, 300, 150)
    
    st.subheader("🛡️ 기구 설정")
    cover_thick = st.slider("Cover 두께 (mm)", 1.0, 5.0, 2.0, step=0.5)
    gap_dist = st.slider("Gap (mm)", 1, 50, 10)
    sim_time_hr = st.slider("가동 시간 (h)", 1, 24, 5)

# --- 2. 물리 계산 엔진 ---
tv_w_mm = int(inch * 25.4 * 0.87)
tv_h_mm = int(inch * 25.4 * 0.49)
scale = 15
nx, ny = int(tv_w_mm / scale), int(tv_h_mm / scale)

@st.cache_data
def run_simulation(t_w, t_h, b_heat_t, b_x_r, b_y_r, b_s_mm, c_t, g_d, k_val, s_time):
    grid_history = []
    grid = np.zeros((nx, ny))
    
    bx = int(nx * b_x_r / 100); by = int(ny * b_y_r / 100)
    bs = int(b_s_mm / scale)
    bx_e, by_e = min(bx+bs, nx), min(by+bs, ny)
    
    # 재질 특성에 따른 전도 효율 계산
    cond_rate = (k_val / (g_d * 2.0 + c_t)) * 0.05
    total_steps = s_time * 20
    
    for step in range(total_steps + 1):
        center = grid[1:-1, 1:-1]
        grid[1:-1, 1:-1] += cond_rate * (
            grid[:-2, 1:-1] + grid[2:, 1:-1] + 
            grid[1:-1, :-2] + grid[1:-1, 2:] - 4 * center
        )
        grid[bx:bx_e, by:by_e] = b_heat_t
        grid -= grid * 0.002 # 단순 대류 냉각
        
        if step % 2 == 0: grid_history.append(grid.copy())
            
    return np.array(grid_history)

# 시뮬레이션 실행
history = run_simulation(tv_w_mm, tv_h_mm, board_heat_temp, bx_rel, by_rel, b_size_mm, cover_thick, gap_dist, mat_k, sim_time_hr)
final_map = history[-1]

# --- 3. 화면 레이아웃 ---
col_map, col_graph = st.columns([2, 1])

with col_map:
    st.subheader("🔥 온도 분포 (클릭하여 지점 측정)")
    st.caption("이미지 상의 특정 지점을 클릭하면 우측에 해당 위치의 온도 그래프가 나옵니다.")
    
    fig_m, ax_m = plt.subplots(figsize=(10, 5))
    im = ax_m.imshow(final_map.T, cmap='hot', origin='lower')
    ax_m.axis('off')
    
    # 맵 이미지를 클릭 가능한 좌표로 출력
    value = streamlit_image_coordinates(fig_m, key="thermal_map")

with col_graph:
    st.subheader("📈 선택 지점 온도 추이")
    
    if value:
        # 클릭된 좌표를 격자 인덱스로 변환
        # value['x'], value['y']는 이미지 픽셀 좌표이므로 정규화 필요
        img_w, img_h = 1000, 500 # 기준 사이즈
        click_x = int((value['x'] / 640) * nx) # Streamlit 기본 width 대응
        click_y = int(((480 - value['y']) / 480) * ny)
        
        # 범위 초과 방지
        click_x = max(0, min(click_x, nx-1))
        click_y = max(0, min(click_y, ny-1))
        
        # 해당 좌표의 역사 데이터 추출
        point_history = [step[click_x, click_y] for step in history]
        time_axis = np.linspace(0, sim_time_hr, len(point_history))
        
        fig_t, ax_t = plt.subplots()
        ax_t.plot(time_axis, point_history, color='cyan', linewidth=2)
        ax_t.set_xlabel("Time (h)"); ax_t.set_ylabel("Temp (°C)")
        ax_t.set_title(f"Point ({click_x*scale}, {click_y*scale}) mm")
        ax_t.grid(True, alpha=0.2)
        st.pyplot(fig_t)
        
        st.metric("현재 지점 온도", f"{point_history[-1]:.1f} °C")
    else:
        st.info("맵의 특정 부위를 클릭해 보세요.")

    # 재질 정보 표시
    st.write("---")
    st.write(f"**현재 재질:** {mat_type}")
    st.write(f"**열전도도(k):** {mat_k} W/m·K")
