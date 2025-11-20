import streamlit as st
import duckdb
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 (브라우저 탭 이름 등)
st.set_page_config(page_title="마당서점 관리자", layout="wide", page_icon="📚")

# 2. 데이터베이스 연결
# read_only=False로 해야 데이터 추가(INSERT)가 가능합니다.
conn = duckdb.connect("madang.db", read_only=False)

def query_df(sql: str) -> pd.DataFrame:
    """SELECT 결과를 DataFrame으로 반환"""
    return conn.execute(sql).df()

def execute(sql: str):
    """INSERT/UPDATE/DELETE 실행용"""
    conn.execute(sql)

# 3. 사이드바: 대시보드 요약 정보 보여주기
with st.sidebar:
    st.header("📊 서점 현황판")
    
    # 총 고객 수
    count_cust = query_df("SELECT count(*) as cnt FROM Customer")['cnt'][0]
    st.metric("총 고객 수", f"{count_cust}명")
    
    # 총 주문 건수
    count_order = query_df("SELECT count(*) as cnt FROM Orders")['cnt'][0]
    st.metric("총 주문 건수", f"{count_order}건")
    
    # 총 매출액
    total_sales = query_df("SELECT sum(saleprice) as total FROM Orders")['total'][0]
    # 금액에 콤마(,) 찍어서 보여주기
    st.metric("총 매출액", f"{total_sales:,.0f}원")
    
    st.markdown("---")
    st.write("developed by **JSBD Team**")

# 4. 메인 화면
st.title("📚 마당 서점 관리 시스템")

# 도서 목록 불러오기 (콤보박스용)
books_df = query_df("SELECT bookid, bookname, price FROM Book ORDER BY bookid;")
books_list = [None]
# 책 정보와 원래 가격을 같이 저장해둠
for _, row in books_df.iterrows():
    books_list.append(f"{row['bookid']}. {row['bookname']} ({row['price']}원)")

# 탭 구성
tab1, tab2 = st.tabs(["🔍 고객 조회", "📝 거래 입력"])

# --- 탭 1: 고객 조회 ---
with tab1:
    st.subheader("고객별 구매 내역 조회")
    col1, col2 = st.columns([3, 1]) # 검색창 디자인 조절
    
    with col1:
        name_input = st.text_input("고객명을 입력하세요", placeholder="예: 이민석")
    
    if name_input:
        # SQL 쿼리: 고객 정보와 주문 내역 조인
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
            st.warning(f"😥 '{name_input}' 고객님의 구매 내역이 없습니다.")
        else:
            st.success(f"🔎 '{name_input}' 고객님의 거래 내역을 찾았습니다.")
            st.dataframe(result, use_container_width=True)

# --- 탭 2: 거래 입력 ---
with tab2:
    st.subheader("새로운 거래 추가하기")
    
    with st.form("order_form"):
        col_a, col_b = st.columns(2)
        
        with col_a:
            customer_name = st.text_input("고객명 (필수)")
            customer_addr = st.text_input("주소 (신규 고객일 경우 입력)", placeholder="예: 서울시 강남구")
        
        with col_b:
            selected_book = st.selectbox("구매할 책 선택 (필수)", books_list)
            customer_phone = st.text_input("전화번호 (신규 고객일 경우 입력)", placeholder="010-0000-0000")

        # 판매 금액 입력 (기본값 0원)
        sale_price = st.number_input("실제 판매 금액(원)", min_value=0, step=1000, value=0)

        submitted = st.form_submit_button("거래 저장하기")

        if submitted:
            # 1. 유효성 검사
            if (not customer_name) or (selected_book is None):
                st.error("🚨 고객명과 책은 반드시 선택해야 합니다.")
            else:
                # 2. 고객 ID 확인 또는 생성 logic
                exist_df = query_df(f"SELECT custid FROM Customer WHERE name = '{customer_name}';")
                
                if not exist_df.empty:
                    # 기존 고객이면 ID 가져오기
                    custid = int(exist_df["custid"][0])
                    st.toast(f"기존 고객 '{customer_name}'님으로 인식되었습니다.")
                else:
                    # 신규 고객이면 ID 생성 및 추가
                    max_cust_id = query_df("SELECT COALESCE(MAX(custid), 0) AS maxid FROM Customer;")['maxid'][0]
                    custid = int(max_cust_id) + 1
                    
                    # 입력 안 했으면 기본값 처리
                    addr = customer_addr if customer_addr else '입력없음'
                    phone = customer_phone if customer_phone else '000-0000-0000'
                    
                    insert_customer_sql = f"""
                    INSERT INTO Customer(custid, name, address, phone)
                    VALUES ({custid}, '{customer_name}', '{addr}', '{phone}');
                    """
                    execute(insert_customer_sql)
                    st.toast(f"✨ 신규 고객 '{customer_name}'님이 등록되었습니다.")

                # 3. 주문(Order) 추가 logic
                # 선택된 문자열에서 ID 추출 (예: "1. 축구의 역사 (7000원)" -> 1)
                bookid = int(str(selected_book).split(".")[0])
                
                # 새 주문 ID 생성
                max_order_id = query_df("SELECT COALESCE(MAX(orderid), 0) AS maxid FROM Orders;")['maxid'][0]
                new_orderid = int(max_order_id) + 1
                
                # 오늘 날짜
                orderdate = datetime.now().strftime("%Y-%m-%d")
                
                insert_order_sql = f"""
                INSERT INTO Orders(orderid, custid, bookid, saleprice, orderdate)
                VALUES ({new_orderid}, {custid}, {bookid}, {int(sale_price)}, '{orderdate}');
                """
                execute(insert_order_sql)
                
                st.success(f"✅ 거래가 성공적으로 저장되었습니다! (주문번호: {new_orderid})")
                st.balloons() # 성공 축하 효과
