import streamlit as st
import duckdb
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 (단순화)
st.set_page_config(page_title="마당서점 관리 시스템", layout="wide")

# 2. 데이터베이스 연결
conn = duckdb.connect("madang.db", read_only=False)

def query_df(sql: str) -> pd.DataFrame:
    """SELECT 결과를 DataFrame으로 반환"""
    return conn.execute(sql).df()

def execute(sql: str):
    """INSERT/UPDATE/DELETE 실행용"""
    conn.execute(sql)

# 3. 메인 화면 구성
st.title("마당 서점 관리 시스템")

# 도서 목록 불러오기 (콤보박스용)
books_df = query_df("SELECT bookid, bookname FROM Book ORDER BY bookid;")
books_list = [None]
for _, row in books_df.iterrows():
    books_list.append(f"{row['bookid']}. {row['bookname']}")

# 탭 구성
tab1, tab2 = st.tabs(["고객 조회", "거래 입력"])

# --- 탭 1: 고객 조회 ---
with tab1:
    st.subheader("고객별 구매 내역 조회")
    
    name_input = st.text_input("고객명을 입력하세요")
    
    if name_input:
        sql = f"""
        SELECT c.name as '고객명',
               b.bookname as '구매도서',
               o.saleprice as '판매가',
               strftime(o.orderdate, '%Y-%m-%d') AS '주문일자',
               c.phone as '전화번호'
        FROM Customer c
        JOIN Orders o ON c.custid = o.custid
        JOIN Book b ON o.bookid = b.bookid
        WHERE c.name = '{name_input}'
        ORDER BY o.orderdate DESC;
        """
        result = query_df(sql)

        if result.empty:
            st.write(f"'{name_input}' 고객의 구매 내역이 없습니다.")
        else:
            st.dataframe(result, use_container_width=True)

# --- 탭 2: 거래 입력 ---
with tab2:
    st.subheader("새 거래 입력")
    
    # 입력 폼
    customer_name = st.text_input("고객명")
    selected_book = st.selectbox("구매 서적 선택", books_list)
    sale_price = st.number_input("판매 금액(원)", min_value=0, step=1000)

    if st.button("거래 저장"):
        # 유효성 검사
        if (not customer_name) or (selected_book is None):
            st.error("고객명과 서적을 모두 입력해야 합니다.")
        else:
            # 1. 고객 처리 (기존/신규 확인)
            exist_df = query_df(f"SELECT custid FROM Customer WHERE name = '{customer_name}';")
            
            if not exist_df.empty:
                # 기존 고객
                custid = int(exist_df["custid"][0])
            else:
                # 신규 고객 (ID 생성 및 기본값으로 추가)
                max_cust_id = query_df("SELECT COALESCE(MAX(custid), 0) AS maxid FROM Customer;")['maxid'][0]
                custid = int(max_cust_id) + 1
                
                # 주소/전화번호 입력란을 삭제했으므로 기본값 입력
                insert_customer_sql = f"""
                INSERT INTO Customer(custid, name, address, phone)
                VALUES ({custid}, '{customer_name}', 'Seoul', '010-0000-0000');
                """
                execute(insert_customer_sql)

            # 2. 주문 처리
            bookid = int(str(selected_book).split(".")[0])
            
            max_order_id = query_df("SELECT COALESCE(MAX(orderid), 0) AS maxid FROM Orders;")['maxid'][0]
            new_orderid = int(max_order_id) + 1
            
            orderdate = datetime.now().strftime("%Y-%m-%d")
            
            insert_order_sql = f"""
            INSERT INTO Orders(orderid, custid, bookid, saleprice, orderdate)
            VALUES ({new_orderid}, {custid}, {bookid}, {int(sale_price)}, '{orderdate}');
            """
            execute(insert_order_sql)
            
            st.success(f"거래가 저장되었습니다. (고객명: {customer_name})")
