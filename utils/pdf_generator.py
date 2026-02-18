from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from datetime import datetime
from typing import List
import os
from database.models import Transaction

# Import for Persian (Jalali) date conversion
try:
    import jdatetime
    JALALI_SUPPORT = True
except ImportError:
    JALALI_SUPPORT = False

# Import for Persian text reshaping and RTL support
try:
    import arabic_reshaper
    import bidi.algorithm as bidi_algorithm
    PERSIAN_SUPPORT = True
except ImportError:
    PERSIAN_SUPPORT = False


def convert_to_jalali(dt: datetime) -> str:
    """
    Convert Gregorian datetime to Jalali (Persian) date string
    Format: YYYY/MM/DD HH:MM:SS
    """
    if not JALALI_SUPPORT:
        # Fallback to Gregorian if jdatetime is not available
        return dt.strftime('%Y/%m/%d %H:%M:%S')
    
    try:
        jalali = jdatetime.datetime.fromgregorian(datetime=dt)
        return jalali.strftime('%Y/%m/%d %H:%M:%S')
    except Exception:
        # If conversion fails, return Gregorian
        return dt.strftime('%Y/%m/%d %H:%M:%S')


def convert_to_jalali_short(dt: datetime) -> str:
    """
    Convert Gregorian datetime to Jalali (Persian) date string (short format)
    Format: YYYY/MM/DD HH:MM
    """
    if not JALALI_SUPPORT:
        # Fallback to Gregorian if jdatetime is not available
        return dt.strftime('%Y/%m/%d %H:%M')
    
    try:
        jalali = jdatetime.datetime.fromgregorian(datetime=dt)
        return jalali.strftime('%Y/%m/%d %H:%M')
    except Exception:
        # If conversion fails, return Gregorian
        return dt.strftime('%Y/%m/%d %H:%M')


def reshape_persian_text(text: str) -> str:
    """
    Reshape Persian text for proper rendering and apply RTL direction
    Handles HTML tags by reshaping only the text content
    """
    if not PERSIAN_SUPPORT:
        return text
    
    try:
        # Check if text contains HTML tags
        import re
        # Find all HTML tags
        html_pattern = r'<[^>]+>'
        tags = re.findall(html_pattern, text)
        
        if tags:
            # Extract text parts and HTML tags separately
            parts = re.split(html_pattern, text)
            result_parts = []
            tag_index = 0
            
            for i, part in enumerate(parts):
                if part:  # Text part
                    # Reshape only the text part
                    reshaped = arabic_reshaper.reshape(part)
                    bidi_text = bidi_algorithm.get_display(reshaped)
                    result_parts.append(bidi_text)
                
                # Add HTML tag if exists
                if tag_index < len(tags):
                    result_parts.append(tags[tag_index])
                    tag_index += 1
            
            return ''.join(result_parts)
        else:
            # No HTML tags, reshape directly
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = bidi_algorithm.get_display(reshaped_text)
            return bidi_text
    except Exception:
        # If reshaping fails, return original text
        return text

# Register Persian-supporting fonts
# Try common Windows Persian fonts
PERSIAN_FONT = None
PERSIAN_FONT_BOLD = None

# Common Persian font paths on Windows
# Priority: Persian-specific fonts first, then Unicode-supporting fonts
font_paths = [
    (r"C:\Windows\Fonts\BNazanin.ttf", "B-Nazanin"),
    (r"C:\Windows\Fonts\BNazaninBd.ttf", "B-Nazanin-Bold"),
    (r"C:\Windows\Fonts\BTitrBd.ttf", "B-Titr-Bold"),
    (r"C:\Windows\Fonts\tahoma.ttf", "Tahoma"),
    (r"C:\Windows\Fonts\tahomabd.ttf", "Tahoma-Bold"),
    (r"C:\Windows\Fonts\arial.ttf", "Arial"),
    (r"C:\Windows\Fonts\arialbd.ttf", "Arial-Bold"),
]

# Register fonts - try to find both regular and bold versions
regular_font_path = None
bold_font_path = None

for font_path, font_name in font_paths:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            if "Bold" in font_name or "bd" in font_path.lower() or "Bd" in font_path:
                if bold_font_path is None:
                    bold_font_path = font_name
                    PERSIAN_FONT_BOLD = font_name
            else:
                if regular_font_path is None:
                    regular_font_path = font_name
                    PERSIAN_FONT = font_name
        except Exception:
            continue

# If we found a regular font but no bold, use the regular font for both
if PERSIAN_FONT and not PERSIAN_FONT_BOLD:
    PERSIAN_FONT_BOLD = PERSIAN_FONT

# If no font found, use default (will have encoding issues but won't crash)
if PERSIAN_FONT is None:
    PERSIAN_FONT = 'Helvetica'
    PERSIAN_FONT_BOLD = 'Helvetica-Bold'
if PERSIAN_FONT_BOLD is None:
    PERSIAN_FONT_BOLD = PERSIAN_FONT


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
        fontName=PERSIAN_FONT_BOLD,
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=PERSIAN_FONT,
        fontSize=10,
        alignment=TA_RIGHT
    )
    
    # Title
    title_text = reshape_persian_text("۱۰ گردش آخر حساب")
    title = Paragraph(title_text, title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))
    
    # Account number
    account_text_raw = f"شماره حساب: <b>{account_number}</b>"
    account_text = Paragraph(reshape_persian_text(account_text_raw), normal_style)
    elements.append(account_text)
    elements.append(Spacer(1, 0.3*cm))
    
    # Date (using Jalali calendar)
    report_date = convert_to_jalali(datetime.now())
    date_text_raw = f"تاریخ گزارش: {report_date}"
    date_text = Paragraph(reshape_persian_text(date_text_raw), normal_style)
    elements.append(date_text)
    elements.append(Spacer(1, 0.5*cm))
    
    # Table cell style
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName=PERSIAN_FONT,
        fontSize=9,
        alignment=TA_CENTER
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName=PERSIAN_FONT_BOLD,
        fontSize=10,
        alignment=TA_CENTER,
        textColor=colors.whitesmoke
    )
    
    # Table data - use Paragraph objects for proper Persian text rendering
    table_data = [[
        Paragraph(reshape_persian_text('نوع'), table_header_style),
        Paragraph(reshape_persian_text('از حساب'), table_header_style),
        Paragraph(reshape_persian_text('به حساب'), table_header_style),
        Paragraph(reshape_persian_text('مبلغ'), table_header_style),
        Paragraph(reshape_persian_text('کارمزد'), table_header_style),
        Paragraph(reshape_persian_text('وضعیت'), table_header_style),
        Paragraph(reshape_persian_text('تاریخ'), table_header_style)
    ]]
    
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
        # Ensure fee is properly converted from Decimal/None to float
        fee_value = float(trans.fee) if trans.fee is not None else 0.0
        fee = f"{fee_value:,.2f}"
        date = convert_to_jalali_short(trans.created_at)
        
        # Use Paragraph objects for all cells and reshape Persian text
        table_data.append([
            Paragraph(reshape_persian_text(trans_type), table_cell_style),
            Paragraph(reshape_persian_text(str(from_acc)), table_cell_style),
            Paragraph(reshape_persian_text(str(to_acc)), table_cell_style),
            Paragraph(reshape_persian_text(amount), table_cell_style),
            Paragraph(reshape_persian_text(fee), table_cell_style),
            Paragraph(reshape_persian_text(status), table_cell_style),
            Paragraph(reshape_persian_text(date), table_cell_style)
        ])
    
    # Create table
    table = Table(table_data, colWidths=[2*cm, 3*cm, 3*cm, 2.5*cm, 2*cm, 2*cm, 3*cm])
    
    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a90e2')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), PERSIAN_FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), PERSIAN_FONT),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
    ]))
    
    elements.append(table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer

