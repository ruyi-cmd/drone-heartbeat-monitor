import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import time
from datetime import datetime

# 页面配置
st.set_page_config(page_title="无人机智能化应用Demo", layout="wide")

# ---------------------- 原有心跳包监测模块 ----------------------
st.title("无人机通信心跳监测可视化")

# 初始化会话状态
if "heartbeat_data" not in st.session_state:
    st.session_state.heartbeat_data = []

# 操作按钮区
col1, col2 = st.columns(2)
with col1:
    if st.button("发送心跳"):
        timestamp = datetime.now()
        st.session_state.heartbeat_data.append({
            "序号": len(st.session_state.heartbeat_data) + 1,
            "时间": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "时间戳": timestamp.timestamp()
        })
with col2:
    auto_heartbeat = st.checkbox("自动模拟心跳（每秒1次）")

# 自动心跳逻辑
if auto_heartbeat:
    timestamp = datetime.now()
    st.session_state.heartbeat_data.append({
        "序号": len(st.session_state.heartbeat_data) + 1,
        "时间": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "时间戳": timestamp.timestamp()
    })
    time.sleep(1)
    st.rerun()

# 可视化心跳数据
if st.session_state.heartbeat_data:
    df = pd.DataFrame(st.session_state.heartbeat_data)
    st.subheader("心跳时序变化")
    st.line_chart(df.set_index("时间")["时间戳"], use_container_width=True)
    st.dataframe(df, use_container_width=True)

st.divider()

# ---------------------- 新增无人机地图路径规划模块 ----------------------
st.title("无人机路径规划与地图显示")

st.info("""
**作业要求说明**：
1.  输入GCJ-02坐标系经纬度，设置起点A和终点B（需在校园内）
2.  两点之间需包含多个障碍物
3.  放大后可清晰查看二维地图样貌，便于圈选障碍物
""")

# 控制面板：坐标与飞行参数
with st.expander("📊 控制面板", expanded=True):
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("起点 A")
        lat_a = st.number_input("纬度 (起点A)", value=32.2322, format="%.6f", key="lat_a")
        lon_a = st.number_input("经度 (起点A)", value=118.7490, format="%.6f", key="lon_a")
    with col_b:
        st.subheader("终点 B")
        lat_b = st.number_input("纬度 (终点B)", value=32.2343, format="%.6f", key="lat_b")
        lon_b = st.number_input("经度 (终点B)", value=118.7490, format="%.6f", key="lon_b")

    st.subheader("飞行参数")
    flight_height = st.slider("设定飞行高度 (m)", min_value=10, max_value=150, value=50)

# 生成地图
if st.button("🗺️ 生成路径地图"):
    # 以两点中点为地图中心，放大到校园级别
    center_lat = (lat_a + lat_b) / 2
    center_lon = (lon_a + lon_b) / 2
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=19,  # 放大到足够看清建筑物
        tiles="OpenStreetMap"  # 二维底图，便于圈选障碍物
    )

    # 标记起点A和终点B
    folium.Marker(
        [lat_a, lon_a],
        popup="起点 A",
        icon=folium.Icon(color="red", icon="play")
    ).add_to(m)
    folium.Marker(
        [lat_b, lon_b],
        popup="终点 B",
        icon=folium.Icon(color="green", icon="stop")
    ).add_to(m)

    # 绘制直线路径（后续可替换为避障算法）
    folium.PolyLine(
        locations=[[lat_a, lon_a], [lat_b, lon_b]],
        color="blue",
        weight=4,
        opacity=0.7
    ).add_to(m)

    # 示例障碍物（可根据实际校园坐标修改）
    obstacle_points = [
        [(lat_a + 0.0005, lon_a), (lat_a + 0.0005, lon_a + 0.0003),
         (lat_a + 0.0010, lon_a + 0.0003), (lat_a + 0.0010, lon_a)],
        [(lat_a + 0.0015, lon_a + 0.0002), (lat_a + 0.0015, lon_a + 0.0005),
         (lat_a + 0.0020, lon_a + 0.0005), (lat_a + 0.0020, lon_a + 0.0002)]
    ]
    for obs in obstacle_points:
        folium.Polygon(
            locations=obs,
            color="gray",
            fill=True,
            fill_color="gray",
            fill_opacity=0.5,
            popup="障碍物"
        ).add_to(m)

    # 在Streamlit中渲染地图
    folium_static(m, width=1200, height=700)

st.divider()
st.caption("分组作业3-项目Demo | 无人机智能化应用2421")
import math
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import time
from datetime import datetime

# ---------------------- 坐标转换核心工具类 ----------------------
class CoordTransformer:
    """
    WGS-84 与 GCJ-02 坐标系转换工具
    * WGS-84：全球通用坐标系（GPS、谷歌地球）
    * GCJ-02：国测局坐标系（高德、百度、国内地图）
    """
    def __init__(self):
        self.a = 6378245.0  # 长半轴
        self.ee = 0.00669342162296594323  # 第一偏心率平方

    def _transform_lat(self, x, y):
        ret = -100.0 + 2.0*x + 3.0*y + 0.2*y*y + 0.1*x*y + 0.2*math.sqrt(abs(x))
        ret += (20.0*math.sin(6.0*x*math.pi) + 20.0*math.sin(2.0*x*math.pi)) * 2.0 / 3.0
        ret += (20.0*math.sin(y*math.pi) + 40.0*math.sin(y/3.0*math.pi)) * 2.0 / 3.0
        ret += (160.0*math.sin(y/12.0*math.pi) + 320.0*math.sin(y*math.pi/30.0)) * 2.0 / 3.0
        return ret

    def _transform_lon(self, x, y):
        ret = 300.0 + x + 2.0*y + 0.1*x*x + 0.1*x*y + 0.1*math.sqrt(abs(x))
        ret += (20.0*math.sin(6.0*x*math.pi) + 20.0*math.sin(2.0*x*math.pi)) * 2.0 / 3.0
        ret += (20.0*math.sin(x*math.pi) + 40.0*math.sin(x/3.0*math.pi)) * 2.0 / 3.0
        ret += (150.0*math.sin(x/12.0*math.pi) + 300.0*math.sin(x/30.0*math.pi)) * 2.0 / 3.0
        return ret

    def wgs84_to_gcj02(self, lat, lon):
        """WGS-84 转 GCJ-02"""
        if not (72.004 <= lon <= 137.8347 and 0.8293 <= lat <= 55.8271):
            return lat, lon # 国外范围直接返回，不转换
        
        dLat = self._transform_lat(lon-105.0, lat-35.0)
        dLon = self._transform_lon(lon-105.0, lat-35.0)
        radLat = lat / 180.0 * math.pi
        magic = math.sin(radLat)
        magic = 1 - self.ee * magic * magic
        sqrtMagic = math.sqrt(magic)
        dLat = (dLat * 180.0) / ((self.a * (1 - self.ee)) / (magic * sqrtMagic) * math.pi)
        dLon = (dLon * 180.0) / (self.a / sqrtMagic * math.cos(radLat) * math.pi)
        return lat + dLat, lon + dLon

# 全局初始化转换器
transformer = CoordTransformer()

# 页面配置
st.set_page_config(page_title="无人机智能化应用Demo", layout="wide")

# ---------------------- 侧边栏导航 ----------------------
with st.sidebar:
    st.title("导航")
    page = st.radio("功能页面", ["航线规划", "飞行监控"], key="page_radio")
    st.divider()
    
    st.title("坐标系设置")
    coord_system = st.radio("输入坐标系", ["WGS-84", "GCJ-02(高德/百度)"], key="coord_system_radio")
    st.divider()
    
    st.title("系统状态")
    if "a_set" not in st.session_state:
        st.session_state.a_set = False
    if "b_set" not in st.session_state:
        st.session_state.b_set = False
    st.success("A点已设" if st.session_state.a_set else "A点未设")
    st.success("B点已设" if st.session_state.b_set else "B点未设")

# ---------------------- 页面1：航线规划 ----------------------
if page == "航线规划":
    st.title("无人机路径规划与地图显示")
    
    st.info("""
    **作业要求说明**：
    1.  输入经纬度，设置起点A和终点B（需在校园内）
    2.  支持坐标系转换（WGS-84 ↔ GCJ-02）
    3.  两点之间需包含多个障碍物
    4.  放大后可清晰查看二维地图样貌，便于圈选障碍物
    """)

    # 控制面板：坐标与飞行参数
    with st.expander("📊 控制面板", expanded=True):
        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("起点 A")
            lat_a_input = st.number_input("纬度 (起点A)", value=32.2322, format="%.6f", key="lat_a")
            lon_a_input = st.number_input("经度 (起点A)", value=118.7490, format="%.6f", key="lon_a")
        with col_b:
            st.subheader("终点 B")
            lat_b_input = st.number_input("纬度 (终点B)", value=32.2343, format="%.6f", key="lat_b")
            lon_b_input = st.number_input("经度 (终点B)", value=118.7490, format="%.6f", key="lon_b")

        st.subheader("飞行参数")
        flight_height = st.slider("设定飞行高度 (m)", min_value=10, max_value=150, value=50, key="flight_height_slider")

    # 坐标系转换
    if coord_system == "WGS-84":
        lat_a, lon_a = transformer.wgs84_to_gcj02(lat_a_input, lon_a_input)
        lat_b, lon_b = transformer.wgs84_to_gcj02(lat_b_input, lon_b_input)
        st.info("已将 WGS-84 坐标转换为 GCJ-02 坐标用于地图显示")
    else:
        lat_a, lon_a = lat_a_input, lon_a_input
        lat_b, lon_b = lat_b_input, lon_b_input

    # 更新系统状态
    st.session_state.a_set = True
    st.session_state.b_set = True

    # 生成地图（添加唯一key）
    if st.button("🗺️ 生成路径地图", key="generate_route_map"):
        # 以两点中点为地图中心，放大到校园级别
        center_lat = (lat_a + lat_b) / 2
        center_lon = (lon_a + lon_b) / 2
        
        # 使用高德地图瓦片源
        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=20,  # 放大到最高精度
            tiles="https://webrd01.is.autonavi.cn/appmaptile?lang=zh&size=2&scale=1&style=8&x={x}&y={y}&z={z}",
            attr="高德地图"
        )

        # 标记起点A和终点B
        folium.Marker(
            [lat_a, lon_a],
            popup="起点 A",
            icon=folium.Icon(color="red", icon="play")
        ).add_to(m)
        folium.Marker(
            [lat_b, lon_b],
            popup="终点 B",
            icon=folium.Icon(color="green", icon="stop")
        ).add_to(m)

        # 绘制直线路径
        folium.PolyLine(
            locations=[[lat_a, lon_a], [lat_b, lon_b]],
            color="blue",
            weight=4,
            opacity=0.7
        ).add_to(m)

        # 示例障碍物
        obstacle_points = [
            [(lat_a + 0.0005, lon_a), (lat_a + 0.0005, lon_a + 0.0003),
             (lat_a + 0.0010, lon_a + 0.0003), (lat_a + 0.0010, lon_a)],
            [(lat_a + 0.0015, lon_a + 0.0002), (lat_a + 0.0015, lon_a + 0.0005),
             (lat_a + 0.0020, lon_a + 0.0005), (lat_a + 0.0020, lon_a + 0.0002)]
        ]
        for obs in obstacle_points:
            folium.Polygon(
                locations=obs,
                color="gray",
                fill=True,
                fill_color="gray",
                fill_opacity=0.5,
                popup="障碍物"
            ).add_to(m)

        # 在Streamlit中渲染地图
        folium_static(m, width=1200, height=700)

# ---------------------- 页面2：飞行监控（心跳包） ----------------------
elif page == "飞行监控":
    st.title("无人机通信心跳监测可视化")

    # 初始化会话状态
    if "heartbeat_data" not in st.session_state:
        st.session_state.heartbeat_data = []

    # 操作按钮区
    col1, col2 = st.columns(2)
    with col1:
        if st.button("发送心跳", key="send_heartbeat"):
            timestamp = datetime.now()
            st.session_state.heartbeat_data.append({
                "序号": len(st.session_state.heartbeat_data) + 1,
                "时间": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "时间戳": timestamp.timestamp()
            })
    with col2:
        auto_heartbeat = st.checkbox("自动模拟心跳（每秒1次）", key="auto_heartbeat_checkbox")

    # 自动心跳逻辑
    if auto_heartbeat:
        timestamp = datetime.now()
        st.session_state.heartbeat_data.append({
            "序号": len(st.session_state.heartbeat_data) + 1,
            "时间": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "时间戳": timestamp.timestamp()
        })
        time.sleep(1)
        st.rerun()

    # 可视化心跳数据
    if st.session_state.heartbeat_data:
        df = pd.DataFrame(st.session_state.heartbeat_data)
        st.subheader("心跳时序变化")
        st.line_chart(df.set_index("时间")["时间戳"], use_container_width=True, key="heartbeat_line_chart")
        st.dataframe(df, use_container_width=True, key="heartbeat_dataframe")

st.divider()
st.caption("分组作业3-项目Demo | 无人机智能化应用2421")
      
