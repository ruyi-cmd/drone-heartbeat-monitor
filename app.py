import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import time
from datetime import datetime

# ---------------------- 原有心跳监测部分 ----------------------
st.title("无人机通信心跳监测可视化")

# 模拟心跳数据（你原有的逻辑）
if "heartbeat_data" not in st.session_state:
    st.session_state.heartbeat_data = []

col1, col2 = st.columns(2)
with col1:
    if st.button("发送心跳"):
        timestamp = datetime.now()
        st.session_state.heartbeat_data.append({
            "序号": len(st.session_state.heartbeat_data)+1,
            "时间": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "时间戳": timestamp.timestamp()
        })
with col2:
    st.checkbox("自动模拟心跳（每秒1次）", key="auto_heartbeat")

if st.session_state.auto_heartbeat:
    timestamp = datetime.now()
    st.session_state.heartbeat_data.append({
        "序号": len(st.session_state.heartbeat_data)+1,
        "时间": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "时间戳": timestamp.timestamp()
    })
    time.sleep(1)
    st.rerun()

# 显示心跳时序图和表格
if st.session_state.heartbeat_data:
    df = pd.DataFrame(st.session_state.heartbeat_data)
    st.subheader("心跳时序变化")
    st.line_chart(df.set_index("时间")["时间戳"])
    st.dataframe(df)

# ---------------------- 新增地图功能部分 ----------------------
st.subheader("无人机路径规划地图")

# 输入经纬度（GCJ-02坐标系，校园内坐标）
col_a, col_b = st.columns(2)
with col_a:
    st.write("**起点 A**")
    lat_a = st.number_input("纬度", value=32.2322, format="%.6f")
    lon_a = st.number_input("经度", value=118.7490, format="%.6f")
with col_b:
    st.write("**终点 B**")
    lat_b = st.number_input("纬度", value=32.2343, format="%.6f")
    lon_b = st.number_input("经度", value=118.7490, format="%.6f")

# 飞行高度设置
flight_height = st.slider("设定飞行高度(m)", min_value=10, max_value=150, value=50)

# 生成地图
if st.button("生成路径地图"):
    # 以校园为中心创建地图
    m = folium.Map(location=[(lat_a+lat_b)/2, (lon_a+lon_b)/2], zoom_start=18)
    
    # 标记起点A和终点B
    folium.Marker([lat_a, lon_a], popup="起点 A", icon=folium.Icon(color="red")).add_to(m)
    folium.Marker([lat_b, lon_b], popup="终点 B", icon=folium.Icon(color="green")).add_to(m)
    
    # 绘制两点连线（后续可加入避障算法）
    folium.PolyLine(locations=[[lat_a, lon_a], [lat_b, lon_b]], color="blue", weight=3).add_to(m)
    
    # 在Streamlit中显示地图
    folium_static(m, width=1000, height=600)
