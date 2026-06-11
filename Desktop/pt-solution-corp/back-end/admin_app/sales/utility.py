import datetime
from fpdf import FPDF


def generate_proforma_pdf_output(invoice_data, items_data):
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(15, 15, 15)

    # --- KOP SURAT ---
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(15, 15)
    pdf.cell(0, 8, "PT. Solution Corporation Indonesia", ln=True)

    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, "Ruko Bassura City, Jl. Jend. Basuki Rachmat, Jakarta Timur", ln=True)
    pdf.cell(0, 5, "Telepon: 0888-2234566 | Email: Solution.Corp@outlook.com", ln=True)

    pdf.ln(2)
    pdf.set_draw_color(0, 0, 0)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(8)

    # --- INFO INVOICE ---
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("helvetica", "B", 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(90, 10, "  PROFORMA INVOICE", 0, 0, 'L', fill=True)

    tgl_raw = invoice_data.get('tanggal', '')
    try:
        if isinstance(tgl_raw, datetime.date):
            tgl_inv = tgl_raw.strftime('%d %B %Y')
        else:
            tgl_obj = datetime.datetime.strptime(str(tgl_raw), '%Y-%m-%d')
            tgl_inv = tgl_obj.strftime('%d %B %Y')
    except:
        tgl_inv = str(tgl_raw) if tgl_raw else "-"

    pdf.set_font("helvetica", "", 10)
    pdf.cell(90, 10, f"Tanggal: {tgl_inv}  ", 0, 1, 'R', fill=True)
    pdf.ln(8)

    # --- PELANGGAN ---
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 6, "Penawaran Kepada:", 0, 1, 'L')

    pdf.set_font("helvetica", "B", 10)
    pdf.cell(0, 6, f"{invoice_data.get('pelanggan', '-')}", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.multi_cell(0, 5, f"{invoice_data.get('alamat_pengiriman', '-')}")
    pdf.ln(8)

    # --- RINCIAN BARANG (HEADER) ---
    pdf.set_font("helvetica", "B", 10)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(85, 8, "  Deskripsi Produk", "B", 0, 'L', fill=True)
    pdf.cell(20, 8, "Qty", "B", 0, 'C', fill=True)
    pdf.cell(35, 8, "Harga Satuan", "B", 0, 'R', fill=True)
    pdf.cell(40, 8, "Total  ", "B", 1, 'R', fill=True)

    pdf.set_font("helvetica", "", 10)
    total_barang = 0

    for item in items_data:
        nama_prod = item.get('nama_produk', '-')
        qty = int(item.get('qty', 0))
        harga = int(item.get('harga', 0))
        subtotal = qty * harga

        pdf.cell(85, 8, f"  {nama_prod}", 0, 0, 'L')
        pdf.cell(20, 8, str(qty), 0, 0, 'C')
        pdf.cell(35, 8, f"Rp {harga:,.0f}  ", 0, 0, 'R')
        pdf.cell(40, 8, f"Rp {subtotal:,.0f}  ", 0, 1, 'R')
        total_barang += subtotal

    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(2)

    # --- RINGKASAN TOTAL ---
    pdf.set_font("helvetica", "", 10)
    pdf.cell(140, 6, "Subtotal Produk", 0, 0, 'R')
    pdf.cell(40, 6, f"Rp {total_barang:,.0f}  ", 0, 1, 'R')

    ongkir = int(invoice_data.get('ongkir', 0))
    pdf.cell(140, 6, "Biaya Pengiriman (Ongkir)", 0, 0, 'R')
    pdf.cell(40, 6, f"Rp {ongkir:,.0f}  ", 0, 1, 'R')

    pdf.ln(2)
    pdf.set_font("helvetica", "B", 11)
    total_akhir = total_barang + ongkir
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(140, 10, "TOTAL ESTIMASI TAGIHAN  ", "T B", 0, 'R', fill=True)
    pdf.cell(40, 10, f"Rp {total_akhir:,.0f}  ", "T B", 1, 'R', fill=True)

    # --- FOOTER & TANDA TANGAN ---
    y_pos = pdf.get_y()
    if y_pos < 220:
        pdf.set_y(-60)
    elif y_pos > 235:
        pdf.add_page()
        pdf.set_y(-60)
    else:
        pdf.ln(10)

    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(120, 5, "Pembayaran via Transfer:", 0, 0, 'L')
    pdf.cell(60, 5, "Hormat Kami,", 0, 1, 'C')

    pdf.set_font("helvetica", "B", 10)
    pdf.cell(120, 5, "BCA 474-9999699 a/n PT Solution Corp Indonesia", 0, 0, 'L')
    pdf.ln(15)

    pdf.set_font("helvetica", "", 10)
    pdf.cell(120, 5, "", 0, 0)
    pdf.cell(60, 5, "( Admin Penjualan )", 0, 1, 'C')

    pdf.ln(4)
    pdf.set_font("helvetica", "I", 8)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 4,
             "Dokumen ini diterbitkan secara otomatis oleh sistem PT Solution Corp Indonesia dan sah tanpa tanda tangan basah.",
             0, 1, 'C')
    pdf.set_font("helvetica", "B", 8)
    pdf.cell(0, 4, "Terima kasih atas kepercayaan Anda kepada PT Solution Corp Indonesia", 0, 1, 'C')

    pdf_output = pdf.output(dest='S')
    return pdf_output