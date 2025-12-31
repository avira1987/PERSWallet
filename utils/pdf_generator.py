from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO
from datetime import datetime
from typing import List
from database.models import Transaction


def generate_transactions_pdf(transactions: List[Transaction], account_number: str) -> BytesIO:
    """
    Generate PDF file for last 10 transactions
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_RIGHT
    )
    
    # Title
    title = Paragraph("۱۰ گردش آخر حساب", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))
    
    # Account number
    account_text = Paragraph(f"شماره حساب: <b>{account_number}</b>", normal_style)
    elements.append(account_text)
    elements.append(Spacer(1, 0.3*cm))
    
    # Date
    date_text = Paragraph(f"تاریخ گزارش: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}", normal_style)
    elements.append(date_text)
    elements.append(Spacer(1, 0.5*cm))
    
    # Table data
    table_data = [['نوع', 'از حساب', 'به حساب', 'مبلغ', 'کارمزد', 'وضعیت', 'تاریخ']]
    
    for trans in transactions:
        trans_type = {
            'buy': 'خرید',
            'send': 'ارسال',
            'sell': 'فروش'
        }.get(trans.transaction_type, trans.transaction_type)
        
        status = {
            'pending': 'در انتظار',
            'success': 'موفق',
            'failed': 'ناموفق'
        }.get(trans.status, trans.status)
        
        from_acc = trans.from_account or '-'
        to_acc = trans.to_account or '-'
        amount = f"{float(trans.amount):,.2f}"
        fee = f"{float(trans.fee):,.2f}"
        date = trans.created_at.strftime('%Y/%m/%d %H:%M')
        
        table_data.append([trans_type, from_acc, to_acc, amount, fee, status, date])
    
    # Create table
    table = Table(table_data, colWidths=[2*cm, 3*cm, 3*cm, 2.5*cm, 2*cm, 2*cm, 3*cm])
    
    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer

