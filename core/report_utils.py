"""
Reporting and Export Utilities
Supports PDF, DOC, Excel, and CSV exports for all entities
"""
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from django.http import HttpResponse
from django.utils import timezone
from datetime import datetime
import csv
import json

try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


def export_to_pdf(data, title, headers, filename=None):
    """Export data to PDF format"""
    buffer = BytesIO()
    
    # Use landscape for wide tables (more than 6 columns)
    use_landscape = len(headers) > 6
    page_size = (A4[1], A4[0]) if use_landscape else A4
    
    doc = SimpleDocTemplate(buffer, pagesize=page_size, 
                           topMargin=15*mm, bottomMargin=15*mm,
                           leftMargin=10*mm, rightMargin=10*mm)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Title
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 12))
    
    # Date
    date_style = ParagraphStyle(
        'DateStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER
    )
    story.append(Paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
    story.append(Spacer(1, 20))
    
    if not data:
        story.append(Paragraph("No data available.", styles['Normal']))
    else:
        # Prepare table data with proper formatting
        table_data = [headers]
        for row in data:
            formatted_row = []
            for cell in row:
                if cell is None:
                    formatted_row.append('')
                elif isinstance(cell, (int, float)):
                    formatted_row.append(str(cell))
                else:
                    # Truncate very long text
                    cell_str = str(cell)
                    if len(cell_str) > 50:
                        cell_str = cell_str[:47] + '...'
                    formatted_row.append(cell_str)
            table_data.append(formatted_row)
        
        # Calculate column widths based on content
        num_cols = len(headers)
        available_width = page_size[0] - 20*mm  # Account for margins
        col_widths = []
        
        # Calculate approximate width per column
        base_width = available_width / num_cols
        
        # Adjust for specific column types
        for i, header in enumerate(headers):
            header_lower = str(header).lower()
            if 'id' in header_lower:
                col_widths.append(base_width * 0.6)  # ID columns are narrower
            elif 'email' in header_lower:
                col_widths.append(base_width * 1.2)  # Email columns are wider
            elif 'name' in header_lower or 'title' in header_lower:
                col_widths.append(base_width * 1.1)  # Name columns slightly wider
            elif 'date' in header_lower:
                col_widths.append(base_width * 0.9)  # Date columns narrower
            elif 'salary' in header_lower or 'amount' in header_lower:
                col_widths.append(base_width * 0.8)  # Numeric columns narrower
            else:
                col_widths.append(base_width)
        
        # Normalize widths to fit available space
        total_width = sum(col_widths)
        col_widths = [w * (available_width / total_width) for w in col_widths]
        
        # Create table with calculated widths
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center align headers
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),   # Left align data
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('TOPPADDING', (0, 0), (-1, 0), 10),
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    if filename:
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
    else:
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="report_{timestamp}.pdf"'
    return response


def export_to_docx(data, title, headers, filename=None):
    """Export data to DOCX format"""
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx is not installed. Install it with: pip install python-docx")
    
    doc = Document()
    
    # Title
    title_para = doc.add_heading(title, 0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Date
    date_para = doc.add_paragraph(f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
    date_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    date_para.runs[0].font.size = Pt(10)
    date_para.runs[0].font.color.rgb = None  # Gray color
    
    doc.add_paragraph()  # Empty line
    
    if not data:
        doc.add_paragraph("No data available.")
    else:
        # Create table
        table = doc.add_table(rows=1, cols=len(headers))
        table.style = 'Light Grid Accent 1'
        
        # Header row
        header_cells = table.rows[0].cells
        for i, header in enumerate(headers):
            header_cells[i].text = str(header)
            header_cells[i].paragraphs[0].runs[0].font.bold = True
        
        # Data rows
        for row_data in data:
            row_cells = table.add_row().cells
            for i, cell_value in enumerate(row_data):
                row_cells[i].text = str(cell_value) if cell_value is not None else ''
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(buffer.read(), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    if filename:
        response['Content-Disposition'] = f'attachment; filename="{filename}.docx"'
    else:
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="report_{timestamp}.docx"'
    return response


def export_to_excel(data, title, headers, filename=None):
    """Export data to Excel format"""
    if not EXCEL_AVAILABLE:
        raise ImportError("openpyxl is not installed. Install it with: pip install openpyxl")
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Report"
    
    # Title
    ws.merge_cells('A1:' + get_column_letter(len(headers)) + '1')
    title_cell = ws['A1']
    title_cell.value = title
    title_cell.font = Font(size=16, bold=True)
    title_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Date
    ws.merge_cells('A2:' + get_column_letter(len(headers)) + '2')
    date_cell = ws['A2']
    date_cell.value = f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
    date_cell.font = Font(size=10)
    date_cell.alignment = Alignment(horizontal='center', vertical='center')
    
    # Headers
    header_row = 3
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_num)
        cell.value = str(header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    # Data rows
    if data:
        for row_num, row_data in enumerate(data, start=header_row + 1):
            for col_num, cell_value in enumerate(row_data, 1):
                cell = ws.cell(row=row_num, column=col_num)
                cell.value = str(cell_value) if cell_value is not None else ''
                cell.alignment = Alignment(horizontal='left', vertical='center')
                cell.border = Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
                # Alternate row colors
                if row_num % 2 == 0:
                    cell.fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
    
    # Auto-adjust column widths
    for col_num in range(1, len(headers) + 1):
        column_letter = get_column_letter(col_num)
        max_length = len(str(headers[col_num - 1]))  # Start with header length
        for row in ws[column_letter]:
            try:
                if row.value and len(str(row.value)) > max_length:
                    max_length = len(str(row.value))
            except:
                pass
        # Set width with min/max constraints
        adjusted_width = min(max(max_length + 2, 10), 60)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(buffer.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    if filename:
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
    else:
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="report_{timestamp}.xlsx"'
    return response


def export_to_csv(data, title, headers, filename=None):
    """Export data to CSV format"""
    response = HttpResponse(content_type='text/csv')
    if filename:
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
    else:
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        response['Content-Disposition'] = f'attachment; filename="report_{timestamp}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([title])
    writer.writerow([f"Generated on: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"])
    writer.writerow([])  # Empty row
    writer.writerow(headers)
    
    for row in data:
        writer.writerow([str(cell) if cell is not None else '' for cell in row])
    
    return response

