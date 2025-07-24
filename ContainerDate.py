import streamlit as st
import pandas as pd

# 📁 파일 경로 설정
PREDEFINED_FILE_PATH = 'combined2.xlsx'

# 📄 데이터 로드
@st.cache_data
def load_data():
    try:
        df = pd.read_excel(PREDEFINED_FILE_PATH, parse_dates=['선적일'])
        return df
    except Exception as e:
        st.error(f"파일 로드 중 오류 발생: {e}")
        return None

# 🔍 조건 기반 필터링 함수
def filter_data(df, start_date, end_date, loading_port, arrival_port, arrival_country, min_containers):
    df = df[(df['선적일'] >= pd.to_datetime(start_date)) & (df['선적일'] <= pd.to_datetime(end_date))]

    if loading_port != 'All':
        df = df[df['선적항'] == loading_port]
    if arrival_country != 'All':
        df = df[df['도착지국가'] == arrival_country]
    if arrival_port != 'All':
        df = df[df['도착항'] == arrival_port]

    grouped = df.groupby('수출자').agg({'컨테이너수': 'sum'}).reset_index()
    grouped = grouped[grouped['컨테이너수'] >= min_containers]
    filtered_df = df[df['수출자'].isin(grouped['수출자'])]

    return filtered_df

# 🧭 Streamlit 앱 UI
def app():
    st.title("국내 컨테이너 수출 고객 탐색기")
    st.write("📊 데이터를 기반으로 고객을 탐색하고, 고객의 수출 컨테이너 현황을 분석합니다.")

    df = load_data()
    if df is None:
        return

    st.sidebar.header("🚩 조건 기반 검색")

    # 날짜 필터
    min_date = df['선적일'].min()
    max_date = df['선적일'].max()

    # 초기값 설정
    if 'start_date' not in st.session_state:
        st.session_state.start_date = min_date
    if 'end_date' not in st.session_state:
        st.session_state.end_date = max_date
    if 'loading_port' not in st.session_state:
        st.session_state.loading_port = 'All'
    if 'arrival_country' not in st.session_state:
        st.session_state.arrival_country = 'All'
    if 'arrival_port' not in st.session_state:
        st.session_state.arrival_port = 'All'
    if 'min_containers' not in st.session_state:
        st.session_state.min_containers = 0

    # 날짜 선택
    st.session_state.start_date = st.sidebar.date_input("📅 시작일", min_value=min_date, max_value=max_date, value=st.session_state.start_date)
    st.session_state.end_date = st.sidebar.date_input("📅 종료일", min_value=min_date, max_value=max_date, value=st.session_state.end_date)

    # 선적항
    loading_port_options = ['All'] + sorted(df['선적항'].dropna().astype(str).unique().tolist())
    try:
        loading_port_index = loading_port_options.index(st.session_state.loading_port)
    except ValueError:
        loading_port_index = 0
    st.session_state.loading_port = st.sidebar.selectbox("⚓ 선적항", loading_port_options, index=loading_port_index)

    # 도착지국가
    arrival_country_options = ['All'] + sorted(df['도착지국가'].dropna().astype(str).unique().tolist())
    try:
        arrival_country_index = arrival_country_options.index(st.session_state.arrival_country)
    except ValueError:
        arrival_country_index = 0
    st.session_state.arrival_country = st.sidebar.selectbox("🌎 도착지국가", arrival_country_options, index=arrival_country_index)

    # 도착항
    if st.session_state.arrival_country != 'All':
        arrival_port_raw = df[df['도착지국가'] == st.session_state.arrival_country]['도착항'].dropna()
    else:
        arrival_port_raw = df['도착항'].dropna()
    arrival_port_options = ['All'] + sorted(arrival_port_raw.astype(str).unique().tolist())
    try:
        arrival_port_index = arrival_port_options.index(st.session_state.arrival_port)
    except ValueError:
        arrival_port_index = 0
    st.session_state.arrival_port = st.sidebar.selectbox("⚓ 도착항", arrival_port_options, index=arrival_port_index)

    # 최소 컨테이너 수
    container_values = [0, 10, 50, 100, 500, 1000, 10000]
    try:
        container_index = container_values.index(st.session_state.min_containers)
    except ValueError:
        container_index = 0
    st.session_state.min_containers = st.sidebar.selectbox("📦 최소 컨테이너 수", container_values, index=container_index)

    # ▶ 고객 검색
    if st.sidebar.button("고객 검색"):
        with st.spinner("⌛ 조건 기반 데이터를 조회 중입니다..."):
            result_df = filter_data(
                df,
                st.session_state.start_date,
                st.session_state.end_date,
                st.session_state.loading_port,
                st.session_state.arrival_port,
                st.session_state.arrival_country,
                st.session_state.min_containers
            )

            if not result_df.empty:
                grouped = result_df.groupby('수출자').agg({'컨테이너수': 'sum'}).reset_index()
                grouped = grouped.sort_values(by='컨테이너수', ascending=False)
                grouped['순위'] = grouped['컨테이너수'].rank(ascending=False, method='min')
                grouped = grouped[['순위', '수출자', '컨테이너수']].reset_index(drop=True)
                st.write("### 🫅 수출자별 총 컨테이너 수", grouped)

                port_grouped = result_df.groupby('컨테이너선사').agg({'컨테이너수': 'sum'}).reset_index()
                port_grouped = port_grouped.sort_values(by='컨테이너수', ascending=False)
                port_grouped['순위'] = port_grouped['컨테이너수'].rank(ascending=False, method='min')
                port_grouped = port_grouped[['순위', '컨테이너선사', '컨테이너수']].reset_index(drop=True)
                st.write("### 🚢 컨테이너선사별 총 컨테이너 수", port_grouped)
            else:
                st.warning("조건에 맞는 데이터가 없습니다.")

    # 🔍 수출자 분석
    st.sidebar.subheader("🔎 수출자 수출 현황")
    exporter_name = st.sidebar.text_input("🔠 수출자 입력")
    if st.sidebar.button("현황 분석"):
        if exporter_name.strip():
            with st.spinner("⌛ 수출자 데이터를 조회 중입니다..."):
                date_filtered_df = df[(df['선적일'] >= pd.to_datetime(st.session_state.start_date)) &
                                      (df['선적일'] <= pd.to_datetime(st.session_state.end_date))]
                filtered = date_filtered_df[date_filtered_df['수출자'].astype(str).str.contains(exporter_name.strip(), na=False)]

                if not filtered.empty:
                    grouped_exporter = filtered.groupby(['수출자', '선적항', '도착지국가', '도착항']).agg({'컨테이너수': 'sum'}).reset_index()
                    grouped_exporter = grouped_exporter.sort_values(by='컨테이너수', ascending=False).reset_index(drop=True)

                    # ✅ 합계 행 추가
                    total_sum = grouped_exporter['컨테이너수'].sum()
                    total_row = pd.DataFrame([{
                        '수출자': '총합계',
                        '선적항': '',
                        '도착지국가': '',
                        '도착항': '',
                        '컨테이너수': total_sum
                    }])
                    grouped_exporter = pd.concat([grouped_exporter, total_row], ignore_index=True)

                    st.markdown("---")
                    st.subheader(f"📦 '{exporter_name}' 선적항-도착항 컨테이너 상세")
                    st.dataframe(grouped_exporter)
                else:
                    st.warning(f"'{exporter_name}' 에 해당하는 수출자를 찾을 수 없습니다.")
        else:
            st.warning("수출자 이름을 입력해 주세요.")

# 앱 실행
if __name__ == "__main__":
    app()
