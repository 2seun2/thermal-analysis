import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 웹페이지 기본 설정
st.set_page_config(page_title="TV Thermal Mech-Design Pro", layout="wide")
st.title("📺 TV 내부 기구 및 실시간 배치 열해석 Pro")

# --- 1. 사이드바: 설계 및 환경 설정 ---
with st.sidebar:
    st.header("📏 기구 설계 사양")
    inch = st.slider("TV 크기 (인치)", 32, 85, 55)
    
    st.subheader("📦 보드(Board) 설정")
    # 와트(W) 대신 섭씨온도(°C) 입력으로 변경
    board_target_temp = st.number_input("보드 목표 온도 (°C)", value=70, min_value=30, max_value=120)
    
    # 위치 및 크기 설정
    bx_rel = st.slider("보드 X 위치 (%)", 0, 100, 50)
    by_rel = st.slider("보드 Y 위치 (%)", 0, 100, 40)
    b_size_mm = st.slider("보드 크기 (mm)", 50, 300, 150)
    
    st.subheader("🛡️ Cover-Rear 설정")
    cover_thick = st.slider("Cover 두께 (mm)", 1.0, 5.0, 2.0, step=0.5)
    gap_dist = st.slider("Board-Cover 간격 (Gap, mm)", 1, 50, 10)
    
    st.subheader("🌡️ 환경 계수")
    ambient_temp = st.number_input("주변 환경 온도 (°C)", value=25)
    h_coeff = st.slider("대류 계수 (h, W/m²K)", 5, 50, 12)

# --- 2. 물리 계산 및 결과 처리 영역 ---

# TV 기구 치수 계산 (mm)
tv_w_mm = int(inch * 25.4 * 0.87)
tv_h_mm = int(inch * 25.4 * 0.49)

# 데이터 계산 함수 (Streamlit Cache를 이용해 속도 향상)
@st.cache_data
def calculate_thermal_data(t_w, t_h, b_target_t, b_x_r, b_y_r, b_s_mm, c_t, g_d, h_c, a_t):
    # 격자 설정 (10mm 단위로 단순화)
    scale = 10
    nx, ny = int(t_w / scale), int(t_h / scale)
    grid = np.full((nx, ny), float(a_t)) # 초기 온도 = 환경 온도
    
    # 보드 좌표 및 크기 계산 (격자 단위)
    bx = int(nx * b_x_r / 100)
    by = int(ny * b_y_r / 100)
    bs = int(b_s_mm / scale)
    
    # 보드 영역 경계 설정 (안전장치 추가)
    bx_e, by_e = min(bx+bs, nx), min(by+bs, ny)
    bx, by = max(0, bx), max(0, by)
    
    # 물리 상수 계산 (Gap 대류/전도 반영 단순화 모델)
    # Gap이 좁을수록 전도 지배적, 넓을수록 대류 효율 변화
    k_air = 0.026 # 공기 열전도도 (W/mK)
    r_gap = (g_d / 1000) / k_air # Gap 열저항 (단위 면적당)
    alpha = (1.0 / (r_gap + (c_t / 1000 / 0.2))) * 0.1 # 열확산 속도 계수
    
    # 시간에 따른 온도 변화 저장을 위한 리스트
    time_history = []
    max_temp_history = []
    
    # 시뮬레이션 루프 (Transient Analysis 단순화)
    # 200번 반복을 5시간 분량으로 가정
    for step in range(200):
        # 1. 주변 전도 (2D 확산)
        center = grid[1:-1, 1:-1]
        grid[1:-1, 1:-1] += alpha * (
            grid[:-2, 1:-1] + grid[2:, 1:-1] + 
            grid[1:-1, :-2] + grid[1:-1, 2:] - 4 * center
        )
        
        # 2. 보드 영역 온도 고정 (목표 온도 주입)
        # Gap 거리에 따른 온도 전달 효율 반영
        efficiency = 1.0 - (g_d / 60) # Gap이 멀면 보드 온도가 커버에 미치는 영향 감소
        grid[bx:bx_e, by:by_e] = b_target_t * efficiency
        
        # 3. 외부 대류 냉각 (h 계수 반영)
        grid -= (grid - float(a_t)) * (h_c * 0.0001)
        
        # 역사 저장 (50스텝 = 1.25시간 가정)
        if step % 50 == 0:
            time_history.append(step / 40.0) # 시간 단위로 변환
            max_temp_history.append(np.max(grid))

    # 마지막 스텝 데이터 저장
    time_history.append(5.0) 
    max_temp_history.append(np.max(grid))

    return grid, time_history, max_temp_history

# --- 3. 실시간 배치 및 결과 시각화 (오른쪽 디스플레이) ---
col_main, col_sub = st.columns([3, 1])

# 우측 상단: 실시간 배치 시각화
with col_sub:
    st.subheader("📍 실시간 보드 배치")
    
    fig_layout, ax_l = plt.subplots(figsize=(4, 2.5))
    ax_l.set_facecolor('#f0f0f0') # 배경색
    
    # TV 외곽선 그리기
    tv_rect = patches.Rectangle((0, 0), tv_w_mm, tv_h_mm, linewidth=2, edgecolor='black', facecolor='white')
    ax_l.add_patch(tv_rect)
    
    # 보드 영역 그리기 (슬라이더 값에 따라 실시간 위치/크기 변경)
    bx_mm = tv_w_mm * (bx_rel / 100)
    by_mm = tv_h_mm * (by_rel / 100)
    board_rect = patches.Rectangle((bx_mm, by_mm), b_size_mm, b_size_mm, linewidth=1, edgecolor='blue', facecolor='#007bff', alpha=0.7)
    ax_l.add_patch(board_rect)
    
    # 축 설정
    ax_l.set_xlim(0, tv_w_mm)
    ax_l.set_ylim(0, tv_h_mm)
    ax_l.set_aspect('equal')
    ax_l.set_xlabel("Width (mm)", fontsize=8)
    ax_l.set_ylabel("Height (mm)", fontsize=8)
    ax_l.tick_params(labelsize=7)
    ax_l.set_title(f"{tv_w_mm}mm x {tv_h_mm}mm (TV)", fontsize=9)
    
    st.pyplot(fig_layout)
    
    st.write(f"보드 타겟 온도: **{board_target_temp}°C**")

# 메인 화면: 해석 실행 버튼 및 결과 그래프
with col_main:
    st.info("💡 왼쪽에서 설정을 조절한 후 아래 버튼을 누르면 정밀 열해석이 수행됩니다.")
    run_btn = st.button("🚀 해석 시뮬레이션 시작")

    if run_btn:
        with st.spinner('5시간 동안의 온도 변화를 계산 중입니다...'):
            # 데이터 계산 수행
            result_map, t_hist, temp_hist = calculate_thermal_data(
                tv_w_mm, tv_h_mm, board_target_temp, bx_rel, by_rel, 
                b_size_mm, cover_thick, gap_dist, h_coeff, ambient_temp
            )
            
            c1, c2 = st.columns([3, 2])
            
            with c1:
                st.subheader("🔥 Cover 표면 최종 온도 분포 (5h 포화)")
                fig_map, ax_m = plt.subplots(figsize=(10, 5))
                # 축 비율을 mm 단위로 맞춤
                im = ax_m.imshow(result_map.T, cmap='magma', origin='lower', extent=[0, tv_w_mm, 0, tv_h_mm])
                plt.colorbar(im, label="Temperature (°C)")
                ax_m.set_xlabel("Width (mm)")
                ax_m.set_ylabel("Height (mm)")
                st.pyplot(fig_map)
                
            with c2:
                st.subheader("📊 시간에 따른 최고 온도 변화")
                fig_time, ax_t = plt.subplots(figsize=(6, 4.5))
                ax_t.plot(t_hist, temp_hist, marker='o', linestyle='-', color='#d63031', linewidth=2)
                ax_t.set_xlabel("Time (Hours)")
                ax_t.set_ylabel("Max Temp (°C)")
                ax_t.grid(True, linestyle='--', alpha=0.7)
                ax_t.set_ylim(ambient_temp - 5, board_target_temp + 10)
                # 현재 최고 온도 표시
                ax_t.annotate(f"{temp_hist[-1]:.1f}°C", xy=(t_hist[-1], temp_hist[-1]), xytext=(t_hist[-1]-1, temp_hist[-1]+3),
                              arrowprops=dict(facecolor='black', shrink=0.05))
                st.pyplot(fig_time)
                
                st.metric("Cover 최종 최고 온도", f"{temp_hist[-1]:.1f} °C", f"{temp_hist[-1]-ambient_temp:.1f} °C 상승")
