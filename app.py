import streamlit as st
import pandas as pd
import os
import io
import urllib.request
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

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

APP_VERSION = "v1.0.21 (모바일 사진첩 직접 다운로드 지원)"
st.markdown(f"## 📊 낮은자리표 원스톱 업무 센터 <span style='font-size:16px; color:gray;'>({APP_VERSION})</span>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📝 견적서 생성기", "📐 자재/도면 산출기", "📸 SNS/블로그", "💰 자금 관리"])

with tab1:
    st.header("📝 견적서 생성기 (고화질 사진/PNG 저장 지원)")
    st.subheader("1. 기본 정보")
    
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("수신 (업체/상호명)", value="하베스트", placeholder="수신 업체명 (귀하 제외)")
        manager_name = st.text_input("참조 (담당자 성함)", value="복정욱 대표", placeholder="참조 담당자명")
        manager_phone = st.text_input("참조 연락처", value="010-1234-4567", placeholder="담당자 연락처")
    with col2:
        site_name = st.text_input("현장명", value="인천좋아2층", placeholder="예: 인천좋아2층 (33㎡ / 약 10평)")
        est_date = st.date_input("견적 발행일", datetime.today())
        
    st.markdown("---")
    st.subheader("2. 시공 항목 상세 정보")
    
    if "est_rows" not in st.session_state:
        st.session_state.est_rows = [
            {"품목명": "콩자갈", "수량": 14.0, "단위": "포", "단가(원)": 25000},
            {"품목명": "에폭시 (주제+경화제)", "수량": 1.0, "단위": "말", "단가(원)": 160000},
            {"품목명": "수용성 프라이머", "수량": 1.0, "단위": "말", "단가(원)": 110000},
            {"품목명": "신너", "수량": 1.0, "단위": "가롱", "단가(원)": 30000},
            {"품목명": "시공 인건비", "수량": 1.0, "단위": "인", "단가(원)": 500000}
        ]

    if st.button("➕ 시공 품목 한 줄 추가하기"):
        st.session_state.est_rows.append({"품목명": "", "수량": 1.0, "단위": "평", "단가(원)": 0})
        st.rerun()

    current_rows = []
    indices_to_delete = []

    for i, row in enumerate(st.session_state.est_rows):
        cols = st.columns([2.5, 1.2, 1.2, 1.8, 0.6])
        with cols[0]:
            item_name = st.text_input(f"품목명 #{i+1}", value=row.get("품목명", ""), key=f"item_name_{i}")
        with cols[1]:
            item_qty = st.number_input(f"수량 #{i+1}", value=float(row.get("수량", 1.0)), step=1.0, min_value=0.0, key=f"item_qty_{i}")
        with cols[2]:
            item_unit = st.text_input(f"단위 #{i+1}", value=str(row.get("단위", "평")), key=f"item_unit_{i}")
        with cols[3]:
            item_price = st.number_input(f"단가 #{i+1}", value=int(row.get("단가(원)", 0)), step=10000, min_value=0, key=f"item_price_{i}", format="%d")
        with cols[4]:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("삭제", key=f"del_row_{i}"):
                indices_to_delete.append(i)

        current_rows.append({
            "품목명": item_name,
            "수량": item_qty,
            "단위": item_unit,
            "단가(원)": item_price,
            "금액": int(item_qty * item_price)
        })

    if indices_to_delete:
        for idx in sorted(indices_to_delete, reverse=True):
            st.session_state.est_rows.pop(idx)
        st.rerun()

    st.markdown("---")
    
    raw_subtotal = sum(r["금액"] for r in current_rows)
    
    col_calc1, col_calc2 = st.columns(2)
    with col_calc1:
        st.markdown(f"#### 기본 공급가액 소계: **₩ {raw_subtotal:,}** 원")
        discount_input = st.number_input("할인 / 절사 금액 (원)", value=0, step=1000, min_value=0)
        
    discount_label = ""
    if discount_input > 0:
        if discount_input >= 10000:
            discount_label = "특별할인"
        else:
            discount_label = "단위 절사"
            
    supply_price = max(0, raw_subtotal - discount_input)
    vat_amount = int(supply_price * 0.1)
    grand_total = supply_price + vat_amount

    with col_calc2:
        st.markdown("### 💰 견적 정산 요약")
        if discount_input > 0:
            st.markdown(f"**{discount_label}:** <span style='color:red;'>- ₩ {int(discount_input):,} 원</span>", unsafe_allow_html=True)
        st.markdown(f"**공급가액 (상단 총 견적금액):** ₩ {int(supply_price):,} 원 <span style='color:gray;'>(부가세 별도)</span>", unsafe_allow_html=True)
        st.markdown(f"**부가가치세 (10%):** ₩ {int(vat_amount):,} 원")
        st.markdown(f"<h2 style='color:blue;'>최종 합계: ₩ {int(grand_total):,} 원 <span style='font-size:16px; color:gray;'>(부가세 포함)</span></h2>", unsafe_allow_html=True)

    st.subheader("3. 특이사항 및 비고")
    user_memo = st.text_area("현장 추가 요청사항 (선택사항)", placeholder="현장 특이사항이 있을 경우 입력하세요.")

    default_terms = (
        "* 견적유효기간 30일\n"
        "* 결제는 착수금70% / 잔금30%\n"
        "* 입금 확인시 발주가 진행됩니다.\n"
        "* 카카오뱅크 3333-38-0892030 (낮은자리)"
    )
    st.info(f"**[기본 비고란 자동 표기 안내]**\n\n{default_terms.replace(chr(10), '<br>')}", icon="ℹ️")

    st.markdown("---")

    # 🖼️ 견적서 사진 생성
    if st.button("📸 견적서 사진(PNG) 생성하기"):
        if not site_name:
            st.warning("⚠️ 현장명을 필수로 입력하셔야 사진이 생성됩니다!")
        else:
            with st.spinner("요청하신 서식에 맞춰 고화질 견적서 사진을 생성 중입니다..."):
                font_path = os.path.join(REAL_DESKTOP, "NanumGothic.ttf")
                if not os.path.exists(font_path):
                    try:
                        urllib.request.urlretrieve(
                            "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
                            font_path
                        )
                    except Exception as e:
                        pass

                img_w, img_h = 1240, 1754
                img = Image.new("RGB", (img_w, img_h), "white")
                draw = ImageDraw.Draw(img)

                try:
                    f_title = ImageFont.truetype(font_path, 44)
                    f_head = ImageFont.truetype(font_path, 22)
                    f_bold = ImageFont.truetype(font_path, 20)
                    f_body = ImageFont.truetype(font_path, 18)
                    f_small = ImageFont.truetype(font_path, 16)
                except:
                    f_title = f_head = f_bold = f_body = f_small = ImageFont.load_default()

                margin_x = 90
                content_w = img_w - (margin_x * 2)

                draw.text((img_w // 2, 80), "견   적   서", fill="black", font=f_title, anchor="mm")
                draw.line([(margin_x, 125), (margin_x + content_w, 125)], fill="#1B365D", width=3)

                top_y = 150
                ref_str = f"{manager_name} 귀하" if manager_name else "귀하"
                if manager_phone:
                    ref_str += f" ({manager_phone})"

                draw.text((margin_x, top_y), f"수  신  :  {company_name}", fill="#222222", font=f_head)
                draw.text((margin_x, top_y + 42), f"참  조  :  {ref_str}", fill="#222222", font=f_body)
                draw.text((margin_x, top_y + 84), f"현장명 :  {site_name}", fill="#222222", font=f_body)
                draw.text((margin_x, top_y + 126), f"발행일 :  {est_date.strftime('%Y년 %m월 %d일')}", fill="#555555", font=f_body)

                sup_x = margin_x + content_w - 480
                sup_y = top_y - 10
                row_h = 38
                sup_labels = ["공 급 자", "등록번호", "대    표", "업    태"]
                sup_values = [
                    "낮은자리 (Wall & Floor Design)",
                    "111-08-70684",
                    "낮은자리 (010-2261-2873)",
                    "서비스, 인테리어 시공 전문"
                ]

                for idx in range(4):
                    curr_row_y = sup_y + (idx * row_h)
                    draw.rectangle([sup_x, curr_row_y, sup_x + 130, curr_row_y + row_h], fill="#F1F3F5", outline="#B0B8C1", width=1)
                    draw.text((sup_x + 65, curr_row_y + (row_h // 2)), sup_labels[idx], fill="#333333", font=f_bold, anchor="mm")
                    draw.rectangle([sup_x + 130, curr_row_y, sup_x + 480, curr_row_y + row_h], fill="white", outline="#B0B8C1", width=1)
                    draw.text((sup_x + 145, curr_row_y + (row_h // 2)), sup_values[idx], fill="#111111", font=f_small, anchor="lm")

                banner_y = top_y + 175
                draw.rectangle([margin_x, banner_y, margin_x + content_w, banner_y + 60], fill="#EBF3FB", outline="#B5D1F0", width=2)
                draw.text((margin_x + 25, banner_y + 30), f"  [ 총 견적 금액 ]   ₩ {int(supply_price):,}  ( 부가세 별도 )", fill="#0A3A82", font=f_head, anchor="lm")

                table_y = banner_y + 80
                col_w = [440, 130, 110, 170, 210]
                col_x = [margin_x]
                for w in col_w:
                    col_x.append(col_x[-1] + w)

                headers = ["시 공 품 목", "수 량", "단 위", "단 가", "금 액"]
                th_h = 42

                for c_i in range(5):
                    draw.rectangle([col_x[c_i], table_y, col_x[c_i+1], table_y + th_h], fill="#F1F3F5", outline="#B0B8C1", width=1)
                    draw.text(((col_x[c_i] + col_x[c_i+1]) // 2, table_y + (th_h // 2)), headers[c_i], fill="#222222", font=f_bold, anchor="mm")

                row_y = table_y + th_h
                td_h = 40
                for r in current_rows:
                    if not r["품목명"]:
                        continue
                    qty_str = f"{r['수량']:.1f}" if r["수량"] % 1 != 0 else f"{int(r['수량'])}"
                    draw.rectangle([col_x[0], row_y, col_x[1], row_y + td_h], outline="#D0D7DE", width=1)
                    draw.text((col_x[0] + 15, row_y + (td_h // 2)), r["품목명"], fill="#333333", font=f_body, anchor="lm")
                    draw.rectangle([col_x[1], row_y, col_x[2], row_y + td_h], outline="#D0D7DE", width=1)
                    draw.text(((col_x[1] + col_x[2]) // 2, row_y + (td_h // 2)), qty_str, fill="#333333", font=f_body, anchor="mm")
                    draw.rectangle([col_x[2], row_y, col_x[3], row_y + td_h], outline="#D0D7DE", width=1)
                    draw.text(((col_x[2] + col_x[3]) // 2, row_y + (td_h // 2)), str(r["단위"]), fill="#333333", font=f_body, anchor="mm")
                    draw.rectangle([col_x[3], row_y, col_x[4], row_y + td_h], outline="#D0D7DE", width=1)
                    draw.text((col_x[4] - 15, row_y + (td_h // 2)), f"₩ {int(r['단가(원)']):,}", fill="#333333", font=f_body, anchor="rm")
                    draw.rectangle([col_x[4], row_y, col_x[5], row_y + td_h], outline="#D0D7DE", width=1)
                    draw.text((col_x[5] - 15, row_y + (td_h // 2)), f"₩ {int(r['금액']):,}", fill="#111111", font=f_bold, anchor="rm")
                    row_y += td_h

                draw.rectangle([col_x[0], row_y, col_x[3], row_y + td_h], fill="#F8F9FA", outline="#B0B8C1", width=1)
                draw.text(((col_x[0] + col_x[3]) // 2, row_y + (td_h // 2)), "소 계 (공급가액 합계)", fill="#333333", font=f_body, anchor="mm")
                draw.rectangle([col_x[3], row_y, col_x[5], row_y + td_h], fill="#F8F9FA", outline="#B0B8C1", width=1)
                draw.text((col_x[5] - 15, row_y + (td_h // 2)), f"₩ {raw_subtotal:,}", fill="#333333", font=f_bold, anchor="rm")
                row_y += td_h

                if discount_input > 0:
                    draw.rectangle([col_x[0], row_y, col_x[3], row_y + td_h], fill="white", outline="#B0B8C1", width=1)
                    draw.text(((col_x[0] + col_x[3]) // 2, row_y + (td_h // 2)), f"{discount_label} (공제)", fill="#D32F2F", font=f_body, anchor="mm")
                    draw.rectangle([col_x[3], row_y, col_x[5], row_y + td_h], fill="white", outline="#B0B8C1", width=1)
                    draw.text((col_x[5] - 15, row_y + (td_h // 2)), f"- ₩ {int(discount_input):,}", fill="#D32F2F", font=f_bold, anchor="rm")
                    row_y += td_h

                draw.rectangle([col_x[0], row_y, col_x[3], row_y + td_h], fill="white", outline="#B0B8C1", width=1)
                draw.text(((col_x[0] + col_x[3]) // 2, row_y + (td_h // 2)), "공 급 가 액", fill="#333333", font=f_body, anchor="mm")
                draw.rectangle([col_x[3], row_y, col_x[5], row_y + td_h], fill="white", outline="#B0B8C1", width=1)
                draw.text((col_x[5] - 15, row_y + (td_h // 2)), f"₩ {int(supply_price):,}", fill="#333333", font=f_bold, anchor="rm")
                row_y += td_h

                draw.rectangle([col_x[0], row_y, col_x[3], row_y + td_h], fill="white", outline="#B0B8C1", width=1)
                draw.text(((col_x[0] + col_x[3]) // 2, row_y + (td_h // 2)), "부 가 가 치 세 (10%)", fill="#333333", font=f_body, anchor="mm")
                draw.rectangle([col_x[3], row_y, col_x[5], row_y + td_h], fill="white", outline="#B0B8C1", width=1)
                draw.text((col_x[5] - 15, row_y + (td_h // 2)), f"₩ {int(vat_amount):,}", fill="#333333", font=f_bold, anchor="rm")
                row_y += td_h

                tot_h = 48
                draw.rectangle([col_x[0], row_y, col_x[3], row_y + tot_h], fill="#EBF3FB", outline="#B5D1F0", width=2)
                draw.text(((col_x[0] + col_x[3]) // 2, row_y + (tot_h // 2)), "최 종 합 계  (부 가 세 포 함)", fill="#0A3A82", font=f_bold, anchor="mm")
                draw.rectangle([col_x[3], row_y, col_x[5], row_y + tot_h], fill="#EBF3FB", outline="#B5D1F0", width=2)
                draw.text((col_x[5] - 15, row_y + (tot_h // 2)), f"₩ {int(grand_total):,}", fill="#0A3A82", font=f_head, anchor="rm")
                row_y += tot_h + 25

                if user_memo:
                    draw.text((margin_x, row_y), "[ 현장 특이사항 ]", fill="#222222", font=f_bold)
                    row_y += 30
                    draw.rectangle([margin_x, row_y, margin_x + content_w, row_y + 60], outline="#D0D7DE", width=1)
                    draw.text((margin_x + 15, row_y + 15), user_memo, fill="#444444", font=f_body)
                    row_y += 75

                draw.text((margin_x, row_y), "[ 비 고 ]", fill="#222222", font=f_bold)
                row_y += 28
                notice_box_h = 135
                draw.rectangle([margin_x, row_y, margin_x + content_w, row_y + notice_box_h], fill="#F8F9FA", outline="#D0D7DE", width=1)
                
                notices = [
                    "•  견적유효기간 : 발행일로부터 30일",
                    "•  결제 조건 : 착수금 70%  /  잔금 30%",
                    "•  입금 확인 시 자재 발주 및 시공 일정이 확정 진행됩니다.",
                    "•  입금 계좌 : 카카오뱅크 3333-38-0892030 (낮은자리)"
                ]
                for n_i, n_txt in enumerate(notices):
                    draw.text((margin_x + 20, row_y + 18 + (n_i * 28)), n_txt, fill="#333333", font=f_body)

                row_y += notice_box_h + 35
                draw.text((img_w // 2, row_y), "위와 같이 견적서를 제출합니다.", fill="#222222", font=f_head, anchor="mm")

                # 1. 아이맥 바탕화면에 자동 저장
                safe_site = site_name.replace("/", "_").replace(" ", "_")
                img_file_path = os.path.join(REAL_DESKTOP, f"견적서_{safe_site}.png")
                img.save(img_file_path, "PNG", quality=95)

                # 2. 스마트폰 사진첩 다운로드용 바이트 버퍼 생성
                buf = io.BytesIO()
                img.save(buf, format="PNG", quality=95)
                byte_im = buf.getvalue()

                # 화면에 저장된 이미지 및 다운로드 버튼 표시
                st.session_state["generated_image"] = byte_im
                st.session_state["image_filename"] = f"견적서_{safe_site}.png"
                st.success("✅ 견적서 사진이 생성되었습니다! 아래 다운로드 버튼을 눌러주세요.")

    # 📥 스마트폰 전용 다운로드 버튼 (사진 생성 시 바로 노출)
    if "generated_image" in st.session_state:
        st.download_button(
            label="📥 스마트폰 사진첩에 견적서 저장하기 (다운로드)",
            data=st.session_state["generated_image"],
            file_name=st.session_state["image_filename"],
            mime="image/png",
            use_container_width=True
        )
        st.image(st.session_state["generated_image"], caption="생성된 견적서 미리보기", use_container_width=True)

with tab2:
    st.write("📐 자재 및 부속품 산출 대시보드")
with tab3:
    st.write("📸 시공 사례 자동 포스팅 봇")
with tab4:
    st.write("💰 자금 관리")
