import streamlit as st
import duckdb
import pandas as pd

# 1. 페이지 기본 설정
st.set_page_config(page_title="마당서점 데이터베이스", layout="wide")
st.title("📚 마당서점(Madang) DB 뷰어")

# 2. 데이터베이스 연결 함수
# (주의: DuckDB는 한 번에 하나의 프로세스만 쓰기 모드로 접속 가능합니다.
#  읽기 전용(read_only=True)으로 열면 충돌을 줄일 수 있습니다.)
def get_connection():
    return duckdb.connect(database='madang.db', read_only=True)

try:
    conn = get_connection()
    
    # 3. 탭을 사용하여 테이블별로 데이터를 보여줍니다.
    tab1, tab2, tab3, tab4 = st.tabs(["Customer (고객)", "Book (도서)", "Orders (주문)", "직접 쿼리"])

    with tab1:
        st.header("📋 고객 목록 (Customer)")
        # SQL 결과를 DataFrame으로 변환
        df_customer = conn.sql("SELECT * FROM Customer").df()
        st.dataframe(df_customer, use_container_width=True)
        
        # 이민석 고객이 있는지 확인하는 메시지
        if '이민석' in df_customer['name'].values:
            st.success("✅ '이민석' 고객 데이터가 확인되었습니다!")

    with tab2:
        st.header("📖 도서 목록 (Book)")
        df_book = conn.sql("SELECT * FROM Book").df()
        st.dataframe(df_book, use_container_width=True)

    with tab3:
        st.header("📦 주문 목록 (Orders)")
        df_orders = conn.sql("SELECT * FROM Orders").df()
        st.dataframe(df_orders, use_container_width=True)

    with tab4:
        st.header("🔍 SQL 직접 입력")
        query = st.text_area("SQL 쿼리를 입력하세요", "SELECT * FROM Customer WHERE name = '이민석'")
        if st.button("실행"):
            try:
                result = conn.sql(query).df()
                st.dataframe(result)
            except Exception as e:
                st.error(f"쿼리 오류: {e}")

except Exception as e:
    st.error(f"DB 연결 오류: {e}")
    st.warning("💡 팁: 주피터 노트북 등 다른 곳에서 DB를 열고 있다면 연결을 닫거나 커널을 종료해주세요.")