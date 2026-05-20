import streamlit as st
import streamlit_leaflet as sl
import math
import time
from datetime import datetime, timedelta

# -------------------------- 页面基础配置 --------------------------
st.set_page_config(page_title="无人机航线规划&心跳监测", layout="wide")

# -------------------------- 全局变量初始化 --------------------------
if "waypoints" not in st.session_state:
    st.session_state.waypoints = []
if "current_wp_idx" not in st.session_state:
    st.session_state.current_wp_idx = 0
if "is_flying" not in st.session_state:
    st.session_state.is_flying = False
if "heartbeat_running" not in st.session_state:
    st.session_state.heartbeat_running = False
if "obstacles" not in st.session_state:
    st.session_state.obstacles = []
if "fly_speed" not in st.session_state:
    st.session_state.fly_speed = 8.5  # 基础飞行速度m/s
if "safe_distance" not in st.session_state:
    st.session_state.safe_distance = 5.0
if "avoid_mode" not in st.session_state:
    st.session_state.avoid_mode = "右绕航线"

# -------------------------- 核心计算函数（精准修复ETA时间） --------------------------
def get_point_dist(p1, p2):
    """两点平面距离计算"""
    return math.hypot(p2[0]-p1[0], p2[1]-p1[1])

def calc_route_total_dist(waypoints):
    """计算整条航线折线总距离"""
    total = 0.0
    for i in range(len(waypoints)-1):
        total += get_point_dist(waypoints[i], waypoints[i+1])
    return total

def calc_flown_dist(waypoints, current_idx):
    """计算已飞行距离"""
    flown = 0.0
    for i in range(current_idx):
        flown += get_point_dist(waypoints[i], waypoints[i+1])
    return flown

def get_real_speed(current_idx, waypoints, base_speed=8.5, turn_speed=5.0):
    """转弯自动减速，动态真实速度"""
    if 1 <= current_idx <= len(waypoints)-2:
        p0, p1, p2 = waypoints[current_idx-1], waypoints[current_idx], waypoints[current_idx+1]
        v1 = (p1[0]-p0[0], p1[1]-p0[1])
        v2 = (p2[0]-p1[0], p2[1]-p1[1])
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        if dot < 0.8:
            return turn_speed
    return base_speed

# -------------------------- 侧边栏：导航&安全设置 --------------------------
with st.sidebar:
    st.title("导航")
    nav_mode = st.radio("", ["航线规划", "飞行监控"])

    st.markdown("---")
    st.subheader("障碍物圈选")
    obs_name = st.text_input("障碍物名称", value="教学楼")
    obs_height = st.number_input("高度(m)", value=20)
    if st.button("选择终点"):
        st.info("地图点击圈选障碍物")

    st.markdown("---")
    st.subheader("安全设置")
    st.session_state.safe_distance = st.slider("安全距离(米)", min_value=1.0, max_value=20.0, value=5.0)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("上绕避障"):
            st.session_state.avoid_mode = "上绕航线"
    with col2:
        if st.button("左绕航线"):
            st.session_state.avoid_mode = "左绕航线"
    with col3:
        if st.button("右绕航线"):
            st.session_state.avoid_mode = "右绕航线"
    st.success(f"{st.session_state.avoid_mode}已设置!")

# -------------------------- 主界面：地图+飞行状态 --------------------------
# 地图组件
m = sl.Leaflet(height=450, center=[32.21, 118.72], zoom=14)
for wp in st.session_state.waypoints:
    m.add_marker(location=wp, icon="green")
if len(st.session_state.waypoints)>=2:
    m.add_polyline(st.session_state.waypoints, color="orange", weight=3)
map_click = m.add_draw()
st_map = m.display()

# 航线规划模式
if nav_mode == "航线规划":
    st.subheader("📍 航线规划")
    st.info("点击地图添加航点，规划飞行路径")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("清除所有航点"):
            st.session_state.waypoints = []
            st.rerun()
    with col2:
        if len(st.session_state.waypoints)>=2 and st.button("开始模拟飞行"):
            st.session_state.is_flying = True
            st.session_state.current_wp_idx = 0

# 飞行监控模式（核心修复时间逻辑）
elif nav_mode == "飞行监控":
    st.subheader("✈️ 飞行监控")
    waypoints = st.session_state.waypoints
    current_idx = st.session_state.current_wp_idx
    total_dist = calc_route_total_dist(waypoints)
    flown_dist = calc_flown_dist(waypoints, current_idx)
    remaining_dist = total_dist - flown_dist
    real_speed = get_real_speed(current_idx, waypoints, st.session_state.fly_speed)

    # 计算预计到达时间
    if real_speed>0 and remaining_dist>0:
        eta_sec = remaining_dist / real_speed
        arrival_time = datetime.now() + timedelta(seconds=eta_sec)
    else:
        eta_sec = 0
        arrival_time = datetime.now()

    # 顶部状态面板
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("当前航点", f"{current_idx}/{len(waypoints)-1}")
    col2.metric("飞行速度", f"{real_speed:.1f} m/s")
    col3.metric("已用时间", f"{int(flown_dist/real_speed)}秒")
    col4.metric("剩余距离", f"{remaining_dist:.1f} m")
    col5.metric("预计到达", arrival_time.strftime("%H:%M:%S"))

    # 电量&进度
    battery = max(0, 100 - (flown_dist/total_dist)*100) if total_dist>0 else 0
    st.progress(battery/100, text=f"电量模拟 {battery:.1f}%")
    st.progress((flown_dist/total_dist)*100 if total_dist>0 else 1, text=f"任务进度: {100 if total_dist==0 else round((flown_dist/total_dist)*100,1)}%")

    # 心跳监测
    st.markdown("### ❤️ 地面站心跳监测")
    if st.button("开始心跳监测"):
        st.session_state.heartbeat_running = True
    if st.session_state.heartbeat_running:
        st.success("心跳正常，实时通信中...")
        time.sleep(0.1)
        st.rerun()

    # 模拟航点自动前进
    if st.session_state.is_flying and current_idx < len(waypoints)-1:
        time.sleep(0.3)
        st.session_state.current_wp_idx += 1
        st.rerun()
    elif st.session_state.is_flying:
        st.session_state.is_flying = False
        st.success("✅ 航线任务完成！")

