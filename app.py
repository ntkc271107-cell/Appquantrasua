import streamlit as st
from datetime import datetime
from io import BytesIO
import csv

# =========================
# CẤU HÌNH TRANG
# =========================

st.set_page_config(
    page_title="Trà Sữa - Tính Tiền",
    page_icon="🧋",
    layout="wide"
)

# =========================
# DỮ LIỆU MENU
# =========================

DRINKS = {
    "Trà sữa truyền thống": 30000,
    "Trà sữa trân châu": 35000,
    "Trà sữa matcha": 38000,
    "Trà sữa socola": 38000,
    "Trà sữa khoai môn": 38000,
    "Trà sữa dâu": 35000,
    "Trà đào": 30000,
    "Trà vải": 30000,
    "Trà chanh": 25000,
    "Trà tắc": 25000,
}

SIZES = {
    "M": 0,
    "L": 5000,
    "XL": 10000,
}

TOPPINGS = {
    "Không topping": 0,
    "Trân châu đen": 5000,
    "Trân châu trắng": 5000,
    "Thạch trái cây": 5000,
    "Thạch dừa": 5000,
    "Pudding trứng": 7000,
    "Kem cheese": 10000,
    "Trân châu hoàng kim": 7000,
}

SUGAR_LEVELS = [
    "0% đường",
    "30% đường",
    "50% đường",
    "70% đường",
    "100% đường",
]

ICE_LEVELS = [
    "0% đá",
    "30% đá",
    "50% đá",
    "70% đá",
    "100% đá",
]


# =========================
# KHỞI TẠO SESSION
# =========================

if "cart" not in st.session_state:
    st.session_state.cart = []

if "invoice" not in st.session_state:
    st.session_state.invoice = None

if "customer_name" not in st.session_state:
    st.session_state.customer_name = ""


# =========================
# HÀM ĐỊNH DẠNG TIỀN
# =========================

def format_money(number):
    return f"{number:,.0f} đ".replace(",", ".")


# =========================
# HÀM TÍNH GIÁ
# =========================

def calculate_price(drink, size, toppings):
    price = DRINKS[drink]
    price += SIZES[size]

    for topping in toppings:
        price += TOPPINGS[topping]

    return price


# =========================
# HÀM TẠO TEXT HÓA ĐƠN
# =========================

def create_invoice_text(invoice):
    lines = []

    lines.append("================================")
    lines.append("        TRÀ SỮA NHÀ MÌNH")
    lines.append("================================")
    lines.append(f"Mã hóa đơn: {invoice['id']}")
    lines.append(f"Khách hàng: {invoice['customer']}")
    lines.append(f"Thời gian: {invoice['time']}")
    lines.append("--------------------------------")

    for i, item in enumerate(invoice["items"], 1):
        lines.append(
            f"{i}. {item['drink']} - Size {item['size']}"
        )
        lines.append(
            f"   Đường: {item['sugar']} | Đá: {item['ice']}"
        )

        if item["toppings"]:
            lines.append(
                "   Topping: " + ", ".join(item["toppings"])
            )

        lines.append(
            f"   SL: {item['quantity']} x "
            f"{format_money(item['unit_price'])} = "
            f"{format_money(item['total'])}"
        )

    lines.append("--------------------------------")
    lines.append(
        f"TỔNG TIỀN: {format_money(invoice['total'])}"
    )
    lines.append("================================")
    lines.append("       CẢM ƠN QUÝ KHÁCH!")
    lines.append("================================")

    return "\n".join(lines)


# =========================
# HÀM XUẤT CSV
# =========================

def create_csv(invoice):
    output = BytesIO()

    content = [
        [
            "Mã hóa đơn",
            "Khách hàng",
            "Thời gian",
            "Tên món",
            "Size",
            "Topping",
            "Đường",
            "Đá",
            "Số lượng",
            "Đơn giá",
            "Thành tiền"
        ]
    ]

    for item in invoice["items"]:
        content.append([
            invoice["id"],
            invoice["customer"],
            invoice["time"],
            item["drink"],
            item["size"],
            ", ".join(item["toppings"]),
            item["sugar"],
            item["ice"],
            item["quantity"],
            item["unit_price"],
            item["total"]
        ])

    text = "\ufeff"
    for row in content:
        text += ",".join(
            '"' + str(x).replace('"', '""') + '"'
            for x in row
        ) + "\n"

    output.write(text.encode("utf-8-sig"))
    output.seek(0)

    return output


# =========================
# HÀM XUẤT PDF
# =========================

def create_pdf(invoice):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return None

    buffer = BytesIO()

    # Thử font Unicode
    font_regular = "Helvetica"
    font_bold = "Helvetica-Bold"

    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]

    try:
        if len(font_paths) >= 2:
            pdfmetrics.registerFont(
                TTFont("DejaVu", font_paths[0])
            )
            pdfmetrics.registerFont(
                TTFont("DejaVuBold", font_paths[1])
            )
            font_regular = "DejaVu"
            font_bold = "DejaVuBold"
    except Exception:
        pass

    pdf = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4
    y = height - 50

    pdf.setFont(font_bold, 18)
    pdf.drawCentredString(
        width / 2,
        y,
        "HOA DON TRA SUA"
    )

    y -= 35

    pdf.setFont(font_regular, 10)
    pdf.drawString(
        50,
        y,
        f"Ma hoa don: {invoice['id']}"
    )

    y -= 18
    pdf.drawString(
        50,
        y,
        f"Khach hang: {invoice['customer']}"
    )

    y -= 18
    pdf.drawString(
        50,
        y,
        f"Thoi gian: {invoice['time']}"
    )

    y -= 30

    pdf.line(50, y, width - 50, y)

    y -= 25

    for index, item in enumerate(invoice["items"], 1):

        if y < 120:
            pdf.showPage()
            y = height - 50

        pdf.setFont(font_bold, 11)

        text = (
            f"{index}. {item['drink']} - Size {item['size']}"
        )

        pdf.drawString(50, y, text)

        y -= 17

        pdf.setFont(font_regular, 9)

        pdf.drawString(
            65,
            y,
            f"Duong: {item['sugar']} | Da: {item['ice']}"
        )

        y -= 16

        if item["toppings"]:
            topping_text = ", ".join(item["toppings"])

            pdf.drawString(
                65,
                y,
                "Topping: " + topping_text
            )

            y -= 16

        pdf.drawString(
            65,
            y,
            f"SL: {item['quantity']} | "
            f"Don gia: {format_money(item['unit_price'])} | "
            f"Thanh tien: {format_money(item['total'])}"
        )

        y -= 25

    pdf.line(50, y, width - 50, y)

    y -= 30

    pdf.setFont(font_bold, 14)

    pdf.drawRightString(
        width - 50,
        y,
        f"TONG TIEN: {format_money(invoice['total'])}"
    )

    y -= 40

    pdf.setFont(font_regular, 10)

    pdf.drawCentredString(
        width / 2,
        y,
        "Cam on quy khach!"
    )

    pdf.save()

    buffer.seek(0)

    return buffer


# =========================
# HEADER
# =========================

st.title("🧋 QUẢN LÝ BILL TRÀ SỮA")

st.caption(
    "Ứng dụng tính tiền và xuất hóa đơn cho quán trà sữa"
)

st.divider()


# =========================
# THÔNG TIN KHÁCH HÀNG
# =========================

st.subheader("👤 Thông tin khách hàng")

customer_name = st.text_input(
    "Tên khách hàng",
    value=st.session_state.customer_name,
    placeholder="Nhập tên khách hàng..."
)

st.session_state.customer_name = customer_name


# =========================
# CHỌN MÓN
# =========================

st.subheader("🧋 Thêm món")

col1, col2 = st.columns(2)

with col1:

    drink = st.selectbox(
        "Loại trà sữa / nước",
        list(DRINKS.keys())
    )

    size = st.selectbox(
        "Size",
        list(SIZES.keys())
    )

    quantity = st.number_input(
        "Số lượng",
        min_value=1,
        max_value=50,
        value=1,
        step=1
    )


with col2:

    toppings = st.multiselect(
        "Topping",
        list(TOPPINGS.keys())
    )

    sugar = st.select_slider(
        "Mức độ đường",
        options=SUGAR_LEVELS,
        value="50% đường"
    )

    ice = st.select_slider(
        "Mức độ đá",
        options=ICE_LEVELS,
        value="50% đá"
    )


# =========================
# XEM GIÁ
# =========================

unit_price = calculate_price(
    drink,
    size,
    toppings
)

total_item = unit_price * quantity

st.info(
    f"💰 Đơn giá: **{format_money(unit_price)}**  \n"
    f"🧾 Thành tiền: **{format_money(total_item)}**"
)


# =========================
# THÊM MÓN
# =========================

if st.button(
    "➕ THÊM MÓN VÀO HÓA ĐƠN",
    type="primary",
    use_container_width=True
):

    if not customer_name.strip():
        st.warning("Vui lòng nhập tên khách hàng.")

    else:

        item = {
            "drink": drink,
            "size": size,
            "toppings": toppings,
            "sugar": sugar,
            "ice": ice,
            "quantity": quantity,
            "unit_price": unit_price,
            "total": total_item
        }

        st.session_state.cart.append(item)

        st.success(
            f"Đã thêm {quantity} x {drink} vào hóa đơn!"
        )

        st.rerun()


# =========================
# GIỎ HÀNG / HÓA ĐƠN TẠM
# =========================

st.divider()

st.subheader("🧾 Danh sách món trong hóa đơn")

if len(st.session_state.cart) == 0:

    st.info(
        "Chưa có món nào. Hãy chọn món và bấm "
        "\"Thêm món vào hóa đơn\"."
    )

else:

    grand_total = 0

    for index, item in enumerate(
        st.session_state.cart
    ):

        grand_total += item["total"]

        with st.container(border=True):

            col_a, col_b, col_c = st.columns(
                [5, 2, 1]
            )

            with col_a:

                st.markdown(
                    f"### {index + 1}. {item['drink']}"
                )

                st.write(
                    f"Size: **{item['size']}**"
                )

                st.write(
                    f"Đường: {item['sugar']} | "
                    f"Đá: {item['ice']}"
                )

                if item["toppings"]:
                    st.write(
                        "Topping: " +
                        ", ".join(item["toppings"])
                    )
                else:
                    st.write("Topping: Không")

            with col_b:

                st.write(
                    f"Số lượng: **{item['quantity']}**"
                )

                st.write(
                    f"Đơn giá: "
                    f"**{format_money(item['unit_price'])}**"
                )

                st.write(
                    f"Thành tiền: "
                    f"**{format_money(item['total'])}**"
                )

            with col_c:

                if st.button(
                    "🗑️ Xóa",
                    key=f"delete_{index}"
                ):

                    st.session_state.cart.pop(index)

                    st.rerun()

    st.divider()

    st.markdown(
        f"""
        <div style="
            padding:20px;
            border-radius:15px;
            background:#f5f5f5;
            text-align:right;
        ">
            <h2>TỔNG THANH TOÁN</h2>
            <h1>{format_money(grand_total)}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================
# THANH TOÁN
# =========================

st.divider()

col_pay1, col_pay2 = st.columns(2)

with col_pay1:

    if st.button(
        "💳 THANH TOÁN",
        type="primary",
        use_container_width=True
    ):

        if not st.session_state.cart:

            st.warning(
                "Hóa đơn chưa có món nào."
            )

        elif not customer_name.strip():

            st.warning(
                "Vui lòng nhập tên khách hàng."
            )

        else:

            total = sum(
                item["total"]
                for item in st.session_state.cart
            )

            invoice_id = datetime.now().strftime(
                "HD%Y%m%d%H%M%S"
            )

            invoice = {
                "id": invoice_id,
                "customer": customer_name,
                "time": datetime.now().strftime(
                    "%d/%m/%Y %H:%M:%S"
                ),
                "items": list(
                    st.session_state.cart
                ),
                "total": total
            }

            st.session_state.invoice = invoice

            st.success(
                "Thanh toán thành công!"
            )

            st.rerun()


with col_pay2:

    if st.button(
        "🧹 XÓA HẾT HÓA ĐƠN",
        use_container_width=True
    ):

        st.session_state.cart = []
        st.session_state.invoice = None

        st.rerun()


# =========================
# HIỂN THỊ HÓA ĐƠN SAU KHI THANH TOÁN
# =========================

if st.session_state.invoice:

    invoice = st.session_state.invoice

    st.divider()

    st.subheader("✅ HÓA ĐƠN ĐÃ THANH TOÁN")

    st.markdown(
        f"""
        **Mã hóa đơn:** `{invoice['id']}`  
        **Khách hàng:** {invoice['customer']}  
        **Thời gian:** {invoice['time']}
        """
    )

    st.divider()

    for index, item in enumerate(
        invoice["items"], 1
    ):

        toppings_text = (
            ", ".join(item["toppings"])
            if item["toppings"]
            else "Không"
        )

        st.markdown(
            f"""
            **{index}. {item['drink']} - Size {item['size']}**

            - Số lượng: {item['quantity']}
            - Topping: {toppings_text}
            - Đường: {item['sugar']}
            - Đá: {item['ice']}
            - Đơn giá: {format_money(item['unit_price'])}
            - Thành tiền: **{format_money(item['total'])}**
            """
        )

        st.divider()

    st.markdown(
        f"# Tổng tiền: {format_money(invoice['total'])}"
    )

    # =========================
    # XUẤT FILE
    # =========================

    col_export1, col_export2, col_export3 = st.columns(3)

    # TEXT
    with col_export1:

        invoice_text = create_invoice_text(invoice)

        st.download_button(
            label="📄 Xuất TXT",
            data=invoice_text.encode("utf-8"),
            file_name=f"{invoice['id']}.txt",
            mime="text/plain",
            use_container_width=True
        )

    # CSV
    with col_export2:

        csv_file = create_csv(invoice)

        st.download_button(
            label="📊 Xuất CSV",
            data=csv_file,
            file_name=f"{invoice['id']}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # PDF
    with col_export3:

        pdf_file = create_pdf(invoice)

        if pdf_file:

            st.download_button(
                label="🧾 Xuất PDF",
                data=pdf_file,
                file_name=f"{invoice['id']}.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        else:

            st.warning(
                "Chưa cài thư viện reportlab."
            )


# =========================
# FOOTER
# =========================

st.divider()

st.caption(
    "🧋 Trà Sữa Nhà Mình • Hệ thống tính tiền hóa đơn"
)
