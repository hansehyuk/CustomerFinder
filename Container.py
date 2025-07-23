import streamlit as st
import pandas as pd

# 📁 파일 경로 설정
PREDEFINED_FILE_PATH = r'C:\Users\hanse\Desktop\combine\combined.xlsx'

# 📄 데이터 로드
def load_data():
    try:
        df = pd.read_excel(PREDEFINED_FILE_PATH, parse_dates=['선적일'])  # 날짜 자동 변환
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
    st.title("🔍 국내 컨테이너 수출 고객 탐색기")

    df = load_data()
    if df is not None:
        st.sidebar.header("🚩 조건 기반 검색")
        st.sidebar.markdown(" ")

        # 날짜 필터
        min_date = df['선적일'].min()
        max_date = df['선적일'].max()
        start_date = st.sidebar.date_input("📅 시작일", min_value=min_date, max_value=max_date, value=min_date)
        end_date = st.sidebar.date_input("📅 종료일", min_value=min_date, max_value=max_date, value=max_date)

        # 선적항 필터
        loading_port = st.sidebar.selectbox("⚓ 선적항", ['All'] + sorted(df['선적항'].dropna().astype(str).unique().tolist()))

        # 도착지 국가 및 항 필터
        arrival_country = st.sidebar.selectbox("🌎 도착지국가", ['All'] + sorted(df['도착지국가'].dropna().astype(str).unique().tolist()))

        if arrival_country != 'All':
            ports = df[df['도착지국가'] == arrival_country]['도착항'].dropna().astype(str).unique()
        else:
            ports = df['도착항'].dropna().astype(str).unique()
        arrival_port = st.sidebar.selectbox("⚓ 도착항", ['All'] + sorted(ports.tolist()))

        # 최소 컨테이너 수 필터
        min_containers = st.sidebar.selectbox("📦 최소 컨테이너 수", [0, 10, 50, 100, 500, 1000, 10000])

        # ▶ 조건 기반 검색 버튼
        if st.sidebar.button("조건 검색"):
            with st.spinner("⌛ 조건 기반 데이터를 조회 중입니다..."):
                result_df = filter_data(df, start_date, end_date, loading_port, arrival_port, arrival_country, min_containers)

                if not result_df.empty:
                    # 수출자별 컨테이너 수
                    grouped = result_df.groupby('수출자').agg({'컨테이너수': 'sum'}).reset_index()
                    grouped = grouped.sort_values(by='컨테이너수', ascending=False)
                    grouped['순위'] = grouped['컨테이너수'].rank(ascending=False, method='min')
                    grouped = grouped[['순위', '수출자', '컨테이너수']].reset_index(drop=True)
                    st.write("### 🫅 수출자별 총 컨테이너 수", grouped)

                    # 컨테이너 선사별 현황
                    port_grouped = result_df.groupby('컨테이너선사').agg({'컨테이너수': 'sum'}).reset_index()
                    port_grouped = port_grouped.sort_values(by='컨테이너수', ascending=False)
                    port_grouped['순위'] = port_grouped['컨테이너수'].rank(ascending=False, method='min')
                    port_grouped = port_grouped[['순위', '컨테이너선사', '컨테이너수']].reset_index(drop=True)
                    st.write("### 🚢 컨테이너선사별 총 컨테이너 수", port_grouped)
                else:
                    st.warning("조건에 맞는 데이터가 없습니다.")
        else:
            st.info("좌측 사이드바에서 검색 조건을 설정하고 '조건 검색' 버튼을 눌러주세요.")

        # -----------------------------
        # ⬇️ 별도의 수출자 이름 검색 (사이드바 하단)
        # -----------------------------
        st.sidebar.subheader("🔎 수출자 검색")
        exporter_name = st.sidebar.text_input("⚓ 수출자 입력")
        exporter_search_btn = st.sidebar.button("검색")

        if exporter_search_btn:
            if exporter_name.strip():
                with st.spinner("⌛ 수출자 데이터를 조회 중입니다..."):
                    # ✅ 시작일 ~ 종료일 필터 먼저 적용
                    date_filtered_df = df[(df['선적일'] >= pd.to_datetime(start_date)) &
                                          (df['선적일'] <= pd.to_datetime(end_date))]

                    # ✅ 수출자 이름 포함 검색
                    filtered = date_filtered_df[date_filtered_df['수출자'].astype(str).str.contains(exporter_name.strip(), na=False)]

                    if not filtered.empty:
                        grouped_exporter = filtered.groupby(['수출자', '선적항', '도착항']).agg({'컨테이너수': 'sum'}).reset_index()
                        grouped_exporter = grouped_exporter.sort_values(by='컨테이너수', ascending=False).reset_index(drop=True)
                        st.markdown("---")
                        st.subheader(f"📦 수출자 '{exporter_name}' 선적항-도착항별 컨테이너 수")
                        st.dataframe(grouped_exporter)
                    else:
                        st.warning(f"'{exporter_name}' 에 해당하는 수출자를 찾을 수 없습니다. 대소문자를 구분해 입력해 주세요.")
            else:
                st.warning("수출자 이름을 입력해 주세요.")
    else:
        st.error("❌ 데이터를 불러올 수 없습니다. 파일 경로 또는 형식을 확인하세요.")

# 앱 실행
if __name__ == "__main__":
    app()