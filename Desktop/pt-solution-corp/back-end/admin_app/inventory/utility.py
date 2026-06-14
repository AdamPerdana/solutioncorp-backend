from fpdf import FPDF
from datetime import datetime


def generate_po_pdf_output(po, items):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)

    # --- KOP SURAT & LOGO AREA ---
    pdf.set_fill_color(41, 128, 185)  # Biru korporat
    pdf.rect(15, 15, 3, 20, 'F')

    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(44, 62, 80)  # Dark Slate Blue
    pdf.set_xy(22, 15)
    pdf.cell(0, 8, "PT. Solution Corporation Indonesia", ln=True)

    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(127, 140, 141)  # Grey
    pdf.set_xy(22, 22)
    pdf.cell(0, 5, "Ruko Bassura City, Jl. Jend. Basuki Rachmat, Jakarta Timur", ln=True)
    pdf.set_x(22)
    pdf.cell(0, 5, "Telepon: 0851-7100-8055 | Email: solution.corp@outlook.com", ln=True)

    pdf.ln(10)

    # --- INFO PO (Kanan - Kiri Layout) ---
    pdf.set_fill_color(236, 240, 241)  # Light Grey
    pdf.rect(15, 45, 180, 25, 'F')

    pdf.set_y(48)
    pdf.set_x(20)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(90, 8, "Purchase Order", 0, 0, 'L')

    # Info Tanggal (Mengamankan jika format tanggal berupa object date atau string)
    if isinstance(po.tanggal, str):
        try:
            dt = datetime.strptime(po.tanggal, '%Y-%m-%d')
            tanggal_po = dt.strftime('%d %B %Y')
        except ValueError:
            tanggal_po = po.tanggal
    elif po.tanggal:
        tanggal_po = po.tanggal.strftime('%d %B %Y')
    else:
        tanggal_po = "-"

    pdf.set_font("helvetica", "", 10)
    pdf.cell(85, 8, f"Tanggal: {tanggal_po}", 0, 1, 'R')

    pdf.set_x(20)
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(127, 140, 141)
    pdf.cell(90, 6, f"Nomor: {po.nomor_po}", 0, 0, 'L')  # 🔥 Disesuaikan ke po.nomor_po (snake_case)
    pdf.cell(85, 6, "Status: Diterbitkan", 0, 1, 'R')
    pdf.ln(10)

    # --- SUPPLIER & PENGIRIMAN ---
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(44, 62, 80)

    # Header Kiri & Kanan
    pdf.set_fill_color(248, 249, 249)
    pdf.cell(90, 8, "  Kepada:", 0, 0, 'L', fill=True)
    pdf.cell(5, 8, "", 0, 0)  # Spacing
    pdf.cell(85, 8, "  Kirim ke:", 0, 1, 'L', fill=True)

    # Baca nama supplier (karena di database PO kita simpan langsung berupa CharField nama supplier)
    nama_supplier = po.supplier if po.supplier else "Tanpa nama"
    alamat = "Jakarta Timur"  # Fallback alamat kirim logistik internal

    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)

    # Menyimpan posisi Y saat ini agar kolom sejajar
    y_before = pdf.get_y()

    # Kolom Kiri
    pdf.set_xy(15, y_before + 2)
    pdf.multi_cell(85, 6, f"{nama_supplier}")

    # Kolom Kanan
    pdf.set_xy(110, y_before + 2)
    pdf.multi_cell(85, 6, f"{alamat}")

    pdf.ln(10)

    # --- TABEL BARANG ---
    pdf.set_fill_color(52, 73, 94)  # Wet Asphalt
    pdf.set_text_color(255, 255, 255)
    pdf.set_draw_color(255, 255, 255)  # Border putih
    pdf.set_font("helvetica", "", 10)

    pdf.cell(85, 10, "  Deskripsi Produk", 1, 0, 'L', fill=True)
    pdf.cell(20, 10, "Qty", 1, 0, 'C', fill=True)
    pdf.cell(35, 10, "Harga Satuan", 1, 0, 'R', fill=True)
    pdf.cell(40, 10, "Total  ", 1, 1, 'R', fill=True)

    pdf.set_text_color(44, 62, 80)
    pdf.set_draw_color(236, 240, 241)  # Border halus antar baris

    total_akhir = 0
    total_qty = 0
    fill = False  # Zebra coloring

    for item in items:
        # 🔥 Penyesuaian variabel properti item sesuai struktur database PurchaseOrderItem Django
        subtotal = item.qty * item.harga_beli

        if fill:
            pdf.set_fill_color(248, 249, 249)
        else:
            pdf.set_fill_color(255, 255, 255)

        pdf.cell(85, 10, f"  {item.nama_produk}", "B", 0, 'L', fill=True)  # 🔥 item.nama_produk
        pdf.cell(20, 10, str(item.qty), "B", 0, 'C', fill=True)  # 🔥 item.qty
        pdf.cell(35, 10, f"Rp {item.harga_beli:,.0f}  ", "B", 0, 'R', fill=True)  # 🔥 item.harga_beli
        pdf.cell(40, 10, f"Rp {subtotal:,.0f}  ", "B", 1, 'R', fill=True)

        total_akhir += subtotal
        total_qty += item.qty
        fill = not fill

    # --- BARIS TOTAL ---
    pdf.set_font("helvetica", "", 10)
    pdf.set_fill_color(245, 247, 250)
    pdf.cell(85, 12, "  Total Keseluruhan", "B", 0, 'L', fill=True)
    pdf.cell(20, 12, str(total_qty), "B", 0, 'C', fill=True)
    pdf.cell(35, 12, "", "B", 0, 'R', fill=True)
    pdf.cell(40, 12, f"Rp {total_akhir:,.0f}  ", "B", 1, 'R', fill=True)
    pdf.ln(15)

    # --- FOOTER / TANDA TANGAN ---
    pdf.set_y(-50)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(120, 5, "Hormat kami,", 0, 0, 'L')
    pdf.cell(60, 5, "Disetujui oleh,", 0, 1, 'C')
    pdf.ln(15)
    pdf.cell(120, 5, "PT. Solution Corporation Indonesia", 0, 0, 'L')
    pdf.cell(60, 5, f"({nama_supplier})", 0, 1, 'C')

    pdf.set_y(-20)
    pdf.set_font("helvetica", "", 8)
    pdf.set_text_color(189, 195, 199)
    pdf.cell(0, 5,
             "Dokumen ini dicetak secara otomatis dari sistem PT Solution Corp Indonesia. Harap konfirmasi pesanan setelah diterima.",
             0, 1, 'C')

    # Mengembalikan data byte string biner mentah PDF
    return pdf.output(dest='S')