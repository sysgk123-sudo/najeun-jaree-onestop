import streamlit as st
import pandas as pd
import os
import urllib.request
from datetime import datetime

try:
    from fpdf import FPDF
except ImportError:
    pass

def get_real_desktop():
    standard_desktop = os.path.expanduser("~/Desktop")
    icloud_desktop = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/Desktop")
    if os.path.exists(standard_desktop):
        return standard_desktop
    elif os.path.exists(icloud_desktop):
        return icloud_desktop
    return standard_desktop

REAL_DESKTOP = get_real_desktop()

st.set_page_config(page_title="낮은자리표 업무 센터", layout="wide")

# 🎯 버전 관리 표기 (v1.0.16 적용 완료 - 위아래 간격 확장 및 로고/타이틀 위치 원상 복구)
APP_VERSION = "v1.0.16"
st.markdown(f"## 📊 낮은자리표 원스톱 업무 센터 <span style='font-size:16px; color:gray;'>({APP_VERSION})</span>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📝 견적서 생성기", "📐 자재/도면 산출기", "📸 SNS/블로그", "💰 자금 관리"])

with tab1:
    st.header("📝 견적서 생성기 (안전 입력 폼 버전)")
    st.subheader("1. 기본 정보")
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("상대 업체명 (예: 낮은자리 인테리어)")
        manager_name = st.text_input("담당자 이름 (예: 홍길동 실장)")
        manager_phone = st.text_input("담당자 번호 (예: 010-1234-5678)")
    with col2:
        site_name = st.text_input("현장명 (예: 송파 더 베네치아)")
        
    st.markdown("---")
    st.subheader("2. 시공 항목 상세 정보")
    
    if "est_rows" not in st.session_state:
        st.session_state.est_rows = [
            {"품목명": "콩자갈 바닥 시공", "수량": 20.0, "단위": "평", "단가(원)": 110000}
        ]

    if st.button("➕ 시공 품목 한 줄 추가하기"):
        st.session_state.est_rows.append({"품목명": "", "수량": 1.0, "단위": "평", "단가(원)": 0})
        st.rerun()

    current_rows = []
    indices_to_delete = []
    
    for i, row in enumerate(st.session_state.est_rows):
        cols = st.columns([2.5, 1.2, 1.2, 1.8, 0.6])
        with cols[0]:
            item_name = st.text_input(f"품목명 #{i+1}", value=row["품목명"], key=f"item_name_{i}")
        with cols[1]:
            item_qty = st.number_input(f"수량 #{i+1}", value=float(row["수량"]), step=1.0, min_value=0.0, key=f"item_qty_{i}")
        with cols[2]:
            unit_options = ["평", "m²", "식", "개"]
            curr_unit = row["단위"] if row["단위"] in unit_options else "평"
            item_unit = st.selectbox(f"단위 #{i+1}", options=unit_options, index=unit_options.index(curr_unit), key=f"item_unit_{i}")
        with cols[3]:
            item_price = st.number_input(f"단가 #{i+1}", value=int(row["단가(원)"]), step=10000, min_value=0, key=f"item_price_{i}", format="%d")
        with cols[4]:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("삭제", key=f"del_row_{i}"):
                indices_to_delete.append(i)
                
        current_rows.append({
            "품목명": item_name,
            "수량": item_qty,
            "단위": item_unit,
            "단가(원)": item_price
        })

    if indices_to_delete:
        for idx in sorted(indices_to_delete, reverse=True):
            st.session_state.est_rows.pop(idx)
        st.rerun()

    st.session_state.est_rows = current_rows
    calc_df = pd.DataFrame(current_rows)
    
    st.markdown("---")
    st.subheader("3. 세부 사항 및 할인")
    memo = st.text_area("기타 (특이사항 및 요청사항)")
    manual_discount = st.number_input("적용할 할인 금액 (원) - 없으면 0", min_value=0, step=10000)
    st.markdown("---")
    
    calc_df['수량'] = pd.to_numeric(calc_df['수량'], errors='coerce').fillna(0.0)
    calc_df['단가(원)'] = pd.to_numeric(calc_df['단가(원)'], errors='coerce').fillna(0)
    
    total_price = (calc_df['수량'] * calc_df['단가(원)']).sum()
    final_price = total_price - manual_discount
    
    st.markdown("### 💰 최종 예상 견적 금액")
    if manual_discount > 0:
        st.markdown(f"**기본 금액:** {int(total_price):,} 원")
        st.markdown(f"**할인 적용:** <span style='color:red;'>- {int(manual_discount):,} 원</span>", unsafe_allow_html=True)
    st.markdown(f"<h2 style='color:blue;'>최종 금액: {int(final_price):,} 원 <span style='font-size:16px; color:gray;'>(부가세 별도)</span></h2>", unsafe_allow_html=True)
        
    if st.button("📄 프로페셔널 견적서 PDF 생성하기"):
        if not site_name:
            st.warning("⚠️ 현장명을 필수로 입력하셔야 PDF가 생성됩니다!")
        elif calc_df.empty or str(calc_df.iloc[0]['품목명']).strip() == "":
            st.warning("⚠️ 최소 1개 이상의 시공 품목을 입력해주세요!")
        else:
            with st.spinner("최고급 양식으로 다품목 견적서를 정돈하는 중입니다..."):
                font_path = "NanumGothic.ttf"
                if not os.path.exists(font_path):
                    urllib.request.urlretrieve("https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf", font_path)
                
                pdf = FPDF()
                pdf.add_page()
                pdf.add_font("Nanum", style="", fname=font_path)
                
                logo_path = ""
                work_folder = os.path.join(REAL_DESKTOP, "낮은자리_업무")
                if os.path.exists(os.path.join(work_folder, "낮은자리_로고.png")):
                    logo_path = os.path.join(work_folder, "낮은자리_로고.png")
                elif os.path.exists(os.path.join(work_folder, "낮은자리 로고.png")):
                    logo_path = os.path.join(work_folder, "낮은자리 로고.png")
                
                # 로고 위치 쾌적하게 확보 (Y=12)
                if logo_path:
                    pdf.image(logo_path, x=15, y=12, w=40)
                
                # 🎯 우측 상단 '견적서' 및 '발행일' 여유 있게 배치
                pdf.set_font("Nanum", size=22)
                pdf.set_xy(110, 15)
                pdf.cell(85, 10, text="견   적   서", align='R')
                
                pdf.set_font("Nanum", size=9)
                today_date = datetime.now().strftime("%Y년 %m월 %d일")
                pdf.set_xy(110, 26)
                pdf.cell(85, 6, text=f"발행일: {today_date}", align='R')
                
                pdf.set_draw_color(100, 100, 100)
                pdf.set_line_width(0.5)
                pdf.line(15, 38, 195, 38)
                
                # 🎯 수신자 정보 및 공급자 정보 균형 있게 배치 (Y축 44 시작)
                info_y = 44
                pdf.set_font("Nanum", size=10)
                
                pdf.set_xy(15, info_y)
                pdf.cell(90, 6, text=f"수 신 : {company_name} 귀하")
                pdf.set_xy(15, info_y + 7)
                pdf.cell(90, 6, text=f"참 조 : {manager_name} ({manager_phone})")
                pdf.set_xy(15, info_y + 14)
                pdf.cell(90, 6, text=f"현 장 명 : {site_name}")
                
                pdf.set_xy(110, info_y)
                pdf.cell(85, 6, text="공 급 자 : 낮은자리 (Wall & Floor Design)")
                pdf.set_xy(110, info_y + 7)
                pdf.cell(85, 6, text="연 락 처 : 010-2261-2873")
                pdf.set_xy(110, info_y + 14)
                pdf.cell(85, 6, text="사업자등록번호 : 111-08-70684")
                
                # 🎯 상단 금액 칸 (Y축 68 위치에 쾌적하게 안착, 총폭 180)
                top_box_y = 68
                pdf.set_fill_color(240, 245, 255)
                pdf.set_xy(15, top_box_y)
                pdf.set_font("Nanum", size=10)
                pdf.cell(180, 10, text=f"   금액일금 : ₩ {int(total_price):,}   [부가세 별도]", border=1, align='L', fill=True)
                
                # 시공 품목 테이블 헤더 (Y축 84 고정, 총폭 180)
                table_header_y = 84
                pdf.set_xy(15, table_header_y)
                pdf.set_fill_color(230, 230, 230)
                pdf.set_font("Nanum", size=10)
                pdf.cell(85, 9, text="시 공 품 목", border=1, align='C', fill=True)
                pdf.cell(25, 9, text="수 량", border=1, align='C', fill=True)
                pdf.cell(35, 9, text="단 가", border=1, align='C', fill=True)
                pdf.cell(35, 9, text="금 액", border=1, align='C', fill=True)
                
                # 시공 품목 행 출력
                current_y = table_header_y + 9
                pdf.set_font("Nanum", size=10)
                rendered_rows = 0
                for index, row in calc_df.iterrows():
                    item_name = str(row['품목명']).strip()
                    if not item_name or item_name == "nan":
                        continue
                        
                    qty = float(row['수량'])
                    unit = str(row['단위'])
                    price = int(row['단가(원)'])
                    row_total = int(qty * price)
                    
                    pdf.set_xy(15, current_y)
                    pdf.cell(85, 9, text=item_name, border=1, align='C')
                    qty_str = f"{int(qty)} {unit}" if qty.is_integer() else f"{qty} {unit}"
                    pdf.cell(25, 9, text=qty_str, border=1, align='C')
                    pdf.cell(35, 9, text=f"₩ {price:,} / {unit}", border=1, align='C')
                    pdf.cell(35, 9, text=f"₩ {row_total:,}", border=1, align='C')
                    current_y += 9
                    rendered_rows += 1
                
                # 패딩 행 (최소 5줄 유지)
                padding_rows = max(1, 5 - rendered_rows)
                for _ in range(padding_rows):
                    pdf.set_xy(15, current_y)
                    pdf.cell(85, 9, text="", border=1)
                    pdf.cell(25, 9, text="", border=1)
                    pdf.cell(35, 9, text="", border=1)
                    pdf.cell(35, 9, text="", border=1)
                    current_y += 9
                
                # 할인 적용 내역
                if manual_discount > 0:
                    pdf.set_xy(15, current_y)
                    pdf.cell(145, 9, text="특별 할인 적용", border=1, align='R')
                    pdf.set_text_color(220, 20, 60)
                    pdf.cell(35, 9, text=f"- ₩ {int(manual_discount):,}", border=1, align='C')
                    pdf.set_text_color(0, 0, 0)
                    current_y += 9

                # 🎯 하단 '총 합계' 박스 (총폭 정확히 180: 145 + 35)
                pdf.set_fill_color(255, 240, 240)
                
                pdf.set_xy(15, current_y)
                pdf.set_font("Nanum", size=11)
                pdf.cell(145, 11, text="   총 합 계    (부가세 별도)", border=1, align='L', fill=True)
                
                pdf.set_xy(160, current_y)
                pdf.set_font("Nanum", size=12)
                pdf.set_text_color(0, 0, 200)
                pdf.cell(35, 11, text=f"₩ {int(final_price):,}", border=1, align='C', fill=True)
                pdf.set_text_color(0, 0, 0)
                
                current_y += 18
                
                # 특이사항 및 전달사항
                pdf.set_xy(15, current_y)
                pdf.set_font("Nanum", size=10)
                pdf.cell(180, 6, text="[ 특이사항 및 전달사항 ]")
                
                current_y += 6
                pdf.set_xy(15, current_y)
                pdf.set_font("Nanum", size=9)
                memo_text = memo if memo else "특이사항 없음"
                pdf.multi_cell(180, 7, text=memo_text, border=1)
                
                current_y += 28
                pdf.set_xy(15, current_y)
                pdf.set_font("Nanum", size=11)
                pdf.cell(180, 8, text="위와 같이 견적서 발행을 확인합니다.", align='C')
                
                pdf_file_path = os.path.join(REAL_DESKTOP, f"견적서_{site_name}.pdf")
                pdf.output(pdf_file_path)
                
                st.success(f"✅ 성공! 바탕화면에 '견적서_{site_name}.pdf' 파일이 저장되었습니다!")

with tab2:
    st.write("📐 자재 및 부속품 산출 대시보드")
with tab3:
    st.write("📸 시공 사례 자동 포스팅 봇")

with tab4:
    excel_path = os.path.join(REAL_DESKTOP, "자금관리.xlsx")
    today_str = datetime.now().strftime("%Y-%m-%d")

    if "fund_data" not in st.session_state:
        if os.path.exists(excel_path):
            st.session_state.fund_data = pd.read_excel(excel_path)
        else:
            st.session_state.fund_data = pd.DataFrame({
                "날짜": [today_str],
                "현장명": ["기본 현장"],
                "항목": ["내용 기입"],
                "유형": ["수입"],
                "금액(원)": [0]
            })

    df = st.session_state.fund_data.copy()
    valid_dates = [str(d) for d in df.get('날짜', []) if len(str(d)) >= 7]
    month_list = sorted(list(set([d[:7] for d in valid_dates])), reverse=True)
    
    col_filter, _ = st.columns([1, 3])
    with col_filter:
        selected_month = st.selectbox("📅 조회할 월(Month) 선택", ["전체 보기"] + month_list)

    if selected_month != "전체 보기" and '날짜' in df.columns:
        filtered_df = df[df['날짜'].astype(str).str.startswith(selected_month)]
    else:
        filtered_df = df

    filtered_df['금액(원)'] = pd.to_numeric(filtered_df['금액(원)'], errors='coerce').fillna(0)
    total_income = filtered_df[filtered_df["유형"] == "수입"]["금액(원)"].sum()
    total_expense = filtered_df[filtered_df["유형"] == "지출"]["금액(원)"].sum()
    net_profit = total_income + total_expense
    
    col1, col2, col3 = st.columns(3)
    col1.metric(f"💰 수입 ({selected_month})", f"₩ {int(total_income):,}")
    col2.metric(f"💸 지출 ({selected_month})", f"₩ {int(total_expense):,}")
    col3.metric(f"📊 순수익 ({selected_month})", f"₩ {int(net_profit):,}")
    st.markdown("---")
    
    st.write("**현장별 기입장**")
    if st.button("➕ 새 내역 추가"):
        new_row = pd.DataFrame([{
            "날짜": today_str,
            "현장명": "",
            "항목": "",
            "유형": "지출",
            "금액(원)": 0
        }])
        st.session_state.fund_data = pd.concat([st.session_state.fund_data, new_row], ignore_index=True)
        st.rerun()

    edited_df = st.data_editor(
        st.session_state.fund_data, 
        num_rows="dynamic", 
        width='stretch',
        hide_index=True,
        key="fund_editor_key"
    )
    st.session_state.fund_data = edited_df

    if st.button("💾 엑셀 파일로 영구 저장하기 (날짜순 정렬)"):
        try:
            if '날짜' in edited_df.columns:
                edited_df = edited_df.sort_values(by="날짜", ascending=True).reset_index(drop=True)
            edited_df.to_excel(excel_path, index=False)
            st.session_state.fund_data = edited_df
            st.success("✅ 성공! 사장님 바탕화면에 '자금관리.xlsx' 파일이 정확히 저장되었습니다!")
            st.rerun()
        except Exception as e:
            st.error("엑셀 저장 중 오류가 발생했습니다.")
