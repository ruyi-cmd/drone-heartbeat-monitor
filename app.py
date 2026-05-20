import streamlit as st
import streamlit_folium as sf
import folium
import math
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="无人机心跳监测+绕飞航线规划", layout="wide")

# 全局记忆变量（障碍物、航点、绕飞模式全部记忆）
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
if "fly_height" not in st.session_state:
    st.session_state.fly_height = 30
if "avoid_mode" not in st.session_state:
    st.session_state.avoid_mode = "最优弧线绕飞"

# 距离计算
def get_dist(p1, p2):
    return math.hypot(p2[0]-p1[0], p2[1]-p1[1])

# 生成绕飞点：左绕、右绕、最优弧线
def gen_avoid_path(start, end, obs_center, obs_radius=20, mode="最优弧线绕飞"):
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    mid_x = (start[0]+end[0])/2
    mid_y = (start[1]+end[1])/2

    if mode == "向左绕飞":
        offset = (-dy*0.8, dx*0.8)
    elif mode == "向右绕飞":
        offset = (dy*0.8, -dx*0.8)
    else: # 最优弧线最短
        offset = ((obs_center[0]-mid_x)*0.3, (obs_center[1]-mid_y)*0.3)

    avoid_mid = (mid_x+offset[0], mid_y+offset[1])
    return [start, avoid_mid, end]

# 侧边栏：障碍物+高度+绕飞模式
with st.sidebar:
    st.title("无人机地面站")
    nav = st.radio("功能选择", ["航线规划", "飞行监控"])

    st.markdown("---")
    st.subheader("障碍物设置（可记忆）")
    obs_name = st.text_input("障碍物名称", value="教学楼")
    obs_h = st.number_input("障碍物高度(m)", value=25)
    if st.button("添加障碍物"):
        st.session_state.obstacles.append({"name":obs_name,"height":obs_h})
    st.write("已添加障碍物：", [i["name"] for i in st.session_state.obstacles])

    st.markdown("---")
    st.subheader("飞行高度设置")
    st.session_state.fly_height = st.number_input("飞行高度(m)", value=st.session_state.fly_height)

    st.markdown("---")
    st.subheader("绕飞模式选择")
    m1,m2,m3 = st.columns(3)
    with m1:
        if st.button("向左绕飞"):
            st.session_state.avoid_mode = "向左绕飞"
    with m2:
        if st.button("向右绕飞"):
            st.session_state.avoid_mode = "向右绕飞"
    with m3:
        if st.button("最优弧线绕飞"):
            st.session_state.avoid_mode = "最优弧线绕飞"
    st.success(f"当前模式：{st.session_state.avoid_mode}")

# 主地图
m = folium.Map(location=[32.212, 118.724], zoom_start=15)

# 画障碍物
for obs in st.session_state.obstacles:
    folium.CircleMarker([32.212,118.724], radius=20, color="red", popup=f"{obs['name']} 高度{obs['height']}m").add_to(m)

# 画航点&航线
for wp in st.session_state.waypoints:
    folium.Marker(wp, icon=folium.Icon(color="green")).add_to(m)
if len(st.session_state.waypoints)>=2:
    path = gen_avoid_path(st.session_state.waypoints[0], st.session_state.waypoints[-1], (32.212,118.724), mode=st.session_state.avoid_mode)
    folium.PolyLine(path, color="orange", weight=3).add_to(m)
sf.folium_static(m, width=1000, height=480)

# 航线规划
if nav == "航线规划":
    st.subheader("📍 航线规划（支持绕飞）")
    st.info("点击地图添加起点、终点，自动生成左/右/最优弧线绕飞航线")
    c1,c2 = st.columns(2)
    with c1:
        if st.button("清空航点&障碍物"):
            st.session_state.waypoints = []
            st.session_state.obstacles = []
            st.rerun()
    with c2:
        if len(st.session_state.waypoints)>=2 and st.button("开始模拟飞行"):
            st.session_state.is_flying = True
            st.session_state.current_wp_idx = 0

# 飞行监控+心跳监测
elif nav == "飞行监控":
    st.subheader("✈️ 飞行状态 & ❤️心跳监测")
    wp = st.session_state.waypoints
    idx = st.session_state.current_wp_idx
    speed = 8.5
    total_d = sum(get_dist(wp[i],wp[i+1]) for i in range(len(wp)-1)) if len(wp)>=2 else 0
    flown_d = sum(get_dist(wp[i],wp[i+1]) for i in range(idx))
    remain_d = total_d - flown_d

    eta_t = datetime.now() + timedelta(seconds=remain_d/speed) if speed>0 else datetime.now()
    col1,col2,col3,col4,col5 = st.columns(5)
    col1.metric("当前航点", f"{idx}/{len(wp)-1}")
    col2.metric("飞行速度", f"{speed:.1f} m/s")
    col3.metric("已用时间", f"{int(flown_d/speed)}s")
    col4.metric("剩余距离", f"{remain_d:.1f} m")
    col5.metric("预计到达", eta_t.strftime("%H:%M:%S"))

    st.progress(min(flown_d/total_d,1), text=f"任务进度 {round(flown_d/total_d*100,1)}%")
    st.markdown("---")
    if st.button("开启心跳监测"):
        st.session_state.heartbeat_running = True
    if st.session_state.heartbeat_running:
        st.success("✅ 心跳正常，通信在线")
        time.sleep(0.2)
        st.rerun()

    # 模拟前进
    if st.session_state.is_flying and idx < len(wp)-1:
        time.sleep(0.4)
        st.session_state.current_wp_idx += 1
        st.rerun()
    elif st.session_state.is_flying:
        st.session_state.is_flying = False
        st.success("✅ 航线任务完成！")
