from io import BytesIO
import pandas as pd
from fpdf import FPDF


def to_excel(sheets: dict[str, pd.DataFrame]) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, df in sheets.items():
            df.to_excel(xw, sheet_name=name[:31], index=False)
            ws = xw.sheets[name[:31]]
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = max(len(str(c.value or "")) for c in col) + 3
    return buf.getvalue()


def to_pdf(title: str, sheets: dict[str, pd.DataFrame]) -> bytes:
    pdf = FPDF(orientation="L")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 5, "Estimate for budgeting and planning only - not a formal payroll record.",
             new_x="LMARGIN", new_y="NEXT")
    for name, df in sheets.items():
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, name, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", size=8)
        w = (pdf.w - pdf.l_margin - pdf.r_margin) / len(df.columns)
        for c in df.columns:
            pdf.cell(w, 6, str(c)[:22], border=1)
        pdf.ln()
        for row in df.itertuples(index=False):
            for v in row:
                txt = f"{v:,.2f}" if isinstance(v, float) else str(v)
                pdf.cell(w, 6, txt.encode("latin-1", "replace").decode("latin-1")[:28], border=1)
            pdf.ln()
    return bytes(pdf.output())
