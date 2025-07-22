import streamlit as st
import pandas as pd

# 파일 경로 설정
PREDEFINED_FILE_PATH = '202506.xlsx'

# 데이터 로드
def load_data():
    try:
        df = pd.read_excel(PREDEFINED_FILE_PATH)
        return df
    except Exception as e:
        st.error(f"파일 로드 중 오류 발생: {e}")
        return None

# 데이터 필터링 함수
def filter_data(df, start_date, end_date, arrival_port, arrival_country, min_containers):
    df = df[(df['선적일'] >= pd.to_datetime(start_date)) & (df['선적일'] <= pd.to_datetime(end_date))]
    
    if arrival_country != 'All':
        df = df[df['도착지국가'] == arrival_country]
    if arrival_port != 'All':
        df = df[df['도착항'] == arrival_port]
    
    grouped = df.groupby('수출자').agg({'컨테이너수': 'sum'}).reset_index()
    grouped = grouped[grouped['컨테이너수'] >= min_containers]
    filtered_df = df[df['수출자'].isin(grouped['수출자'])]
    
    return filtered_df

# 앱 UI
def app():
    st.title("🔍 부산항 컨테이너 수출 고객 검색기")

    df = load_data()
    if df is not None:
        st.sidebar.header("🚩 검색 조건")
        st.sidebar.markdown(" ")
        # 날짜 선택
        min_date = df['선적일'].min()
        max_date = df['선적일'].max()
        start_date = st.sidebar.date_input("📅 시작일", min_value=min_date, max_value=max_date, value=min_date)
        end_date = st.sidebar.date_input("📅 종료일", min_value=min_date, max_value=max_date, value=max_date)

        # 도착지국가 필터
        arrival_country = st.sidebar.selectbox("🌎 도착지국가", ['All'] + sorted(df['도착지국가'].dropna().astype(str).unique().tolist()))

        # 도착항 필터 (도착지국가에 따라 동적으로 변함)
        if arrival_country != 'All':
            ports = df[df['도착지국가'] == arrival_country]['도착항'].dropna().astype(str).unique()
        else:
            ports = df['도착항'].dropna().astype(str).unique()
        arrival_port = st.sidebar.selectbox("⚓ 도착항", ['All'] + sorted(ports.tolist()))

        # 최소 컨테이너 수 필터
        min_containers = st.sidebar.selectbox("📦 최소 컨테이너 수", [0, 10, 50, 100, 500, 1000, 10000])

        if st.sidebar.button("검색"):
            result_df = filter_data(df, start_date, end_date, arrival_port, arrival_country, min_containers)
            
            if not result_df.empty:
                grouped = result_df.groupby('수출자').agg({'컨테이너수': 'sum'}).reset_index()
                grouped = grouped.sort_values(by='컨테이너수', ascending=False)
                grouped['순위'] = grouped['컨테이너수'].rank(ascending=False, method='min')
                grouped = grouped[['순위', '수출자', '컨테이너수']].reset_index(drop=True)

                # ✅ 인덱스 없이 결과 표시
                st.write("🚢 수출자별 총 컨테이너 수", grouped)
            else:
                st.warning("조건에 맞는 데이터가 없습니다.")
    else:
        st.warning("파일을 불러올 수 없습니다.")

if __name__ == "__main__":
    app()