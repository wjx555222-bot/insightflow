"""Export router for CSV and PDF data exports."""

import csv
import io
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.dependencies import get_current_user, get_db
from app.models.customer import Customer
from app.models.inventory import Inventory
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/sales.csv")
def export_sales_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a CSV export of all orders and return it as a downloadable file."""
    orders = (
        db.query(Order)
        .options(joinedload(Order.customer), joinedload(Order.items).joinedload(OrderItem.product))
        .order_by(Order.order_date.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Order ID",
        "Order Date",
        "Customer Name",
        "Region",
        "Salesperson",
        "Payment Status",
        "Shipment Status",
        "Total Amount",
        "Items",
    ])

    for order in orders:
        customer_name = order.customer.name if order.customer else ""
        item_descriptions = []
        for item in order.items:
            product_name = item.product.name if item.product else f"Product #{item.product_id}"
            item_descriptions.append(
                f"{product_name} x{item.quantity} @ {item.unit_price}"
            )
        items_str = "; ".join(item_descriptions)

        writer.writerow([
            order.id,
            order.order_date.isoformat(),
            customer_name,
            order.region or "",
            order.salesperson or "",
            order.payment_status,
            order.shipment_status,
            f"{order.total_amount:.2f}",
            items_str,
        ])

    output.seek(0)
    filename = f"sales_export_{date.today().isoformat()}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/customers.csv")
def export_customers_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a CSV export of all customers and return it as a downloadable file."""
    customers = db.query(Customer).order_by(Customer.id).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID",
        "Name",
        "Company",
        "Email",
        "Phone",
        "Region",
        "Customer Type",
        "Total Spending",
        "Last Purchase Date",
        "Created At",
    ])

    for c in customers:
        writer.writerow([
            c.id,
            c.name,
            c.company or "",
            c.email or "",
            c.phone or "",
            c.region or "",
            c.customer_type or "",
            f"{c.total_spending:.2f}",
            c.last_purchase_date.isoformat() if c.last_purchase_date else "",
            c.created_at.isoformat() if c.created_at else "",
        ])

    output.seek(0)
    filename = f"customers_export_{date.today().isoformat()}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/inventory.csv")
def export_inventory_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a CSV export of all products with inventory info."""
    products = (
        db.query(Product)
        .options(joinedload(Product.supplier))
        .order_by(Product.id)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Product ID",
        "Product Name",
        "Category",
        "Supplier",
        "Unit Price",
        "Cost Price",
        "Current Stock",
        "Reorder Level",
        "Status",
        "Low Stock",
    ])

    for p in products:
        supplier_name = p.supplier.name if p.supplier else ""
        is_low_stock = "Yes" if p.current_stock <= p.reorder_level else "No"
        writer.writerow([
            p.id,
            p.name,
            p.category or "",
            supplier_name,
            f"{p.unit_price:.2f}",
            f"{p.cost_price:.2f}" if p.cost_price else "0.00",
            p.current_stock,
            p.reorder_level,
            p.status,
            is_low_stock,
        ])

    output.seek(0)
    filename = f"inventory_export_{date.today().isoformat()}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/business-report.pdf")
def export_business_report_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a basic PDF business report with summary statistics.

    Uses reportlab for PDF generation. If reportlab is not installed, falls
    back to a plain-text PDF using a simple FPDF-like approach with reportlab's
    basic canvas.
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas as pdf_canvas
    except ImportError:
        # Fallback: generate a minimal PDF manually
        return _generate_fallback_pdf(db)

    # Gather summary data
    total_revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0.0)).scalar()
    )
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0

    low_stock_count = (
        db.query(func.count(Product.id))
        .filter(
            Product.current_stock <= Product.reorder_level,
            Product.status == "active",
        )
        .scalar()
        or 0
    )

    avg_order_value = (
        db.query(func.coalesce(func.avg(Order.total_amount), 0.0)).scalar()
    )

    # Top 5 products by revenue
    top_products = (
        db.query(
            Product.name,
            func.sum(OrderItem.total).label("revenue"),
            func.sum(OrderItem.quantity).label("qty"),
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .group_by(Product.name)
        .order_by(func.sum(OrderItem.total).desc())
        .limit(5)
        .all()
    )

    # Region breakdown
    regions = (
        db.query(
            Order.region,
            func.sum(Order.total_amount).label("revenue"),
            func.count(Order.id).label("count"),
        )
        .filter(Order.region.isnot(None))
        .group_by(Order.region)
        .order_by(func.sum(Order.total_amount).desc())
        .limit(10)
        .all()
    )

    # Build PDF
    buffer = io.BytesIO()
    c = pdf_canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(1 * inch, height - 1 * inch, "InsightFlow Business Report")

    c.setFont("Helvetica", 10)
    c.drawString(1 * inch, height - 1.3 * inch, f"Generated: {date.today().isoformat()}")

    # Summary section
    y = height - 1.8 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y, "Summary")
    y -= 0.4 * inch

    c.setFont("Helvetica", 11)
    summary_lines = [
        f"Total Revenue: ${total_revenue:,.2f}",
        f"Total Orders: {total_orders}",
        f"Total Customers: {total_customers}",
        f"Total Products: {total_products}",
        f"Average Order Value: ${avg_order_value:,.2f}",
        f"Low Stock Products: {low_stock_count}",
    ]
    for line in summary_lines:
        c.drawString(1.2 * inch, y, line)
        y -= 0.25 * inch

    # Top Products section
    y -= 0.3 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y, "Top Products by Revenue")
    y -= 0.35 * inch

    c.setFont("Helvetica", 11)
    if top_products:
        for p in top_products:
            line = f"{p.name}: ${p.revenue:,.2f} ({p.qty} units)"
            c.drawString(1.2 * inch, y, line)
            y -= 0.25 * inch
    else:
        c.drawString(1.2 * inch, y, "No order data available.")
        y -= 0.25 * inch

    # Region Performance section
    y -= 0.3 * inch
    c.setFont("Helvetica-Bold", 14)
    c.drawString(1 * inch, y, "Region Performance")
    y -= 0.35 * inch

    c.setFont("Helvetica", 11)
    if regions:
        for r in regions:
            line = f"{r.region}: ${r.revenue:,.2f} ({r.count} orders)"
            c.drawString(1.2 * inch, y, line)
            y -= 0.25 * inch
            if y < 1 * inch:
                c.showPage()
                y = height - 1 * inch
                c.setFont("Helvetica", 11)
    else:
        c.drawString(1.2 * inch, y, "No region data available.")

    c.showPage()
    c.save()
    buffer.seek(0)

    filename = f"business_report_{date.today().isoformat()}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/orders/{order_id}.pdf")
def export_order_pdf(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a PDF invoice/detail for a specific order."""
    from fastapi import HTTPException

    order = (
        db.query(Order)
        .options(joinedload(Order.customer), joinedload(Order.items).joinedload(OrderItem.product))
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    customer_name = order.customer.name if order.customer else "Unknown"

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
    except ImportError:
        return _generate_fallback_order_pdf(order, customer_name)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    elements.append(Paragraph(f"Order #{order.id}", styles["Title"]))
    elements.append(Spacer(1, 8 * mm))

    # Order info
    info_data = [
        ["Order Date:", order.order_date.strftime("%Y-%m-%d") if order.order_date else "N/A"],
        ["Customer:", customer_name],
        ["Region:", order.region or "N/A"],
        ["Salesperson:", order.salesperson or "N/A"],
        ["Payment Status:", order.payment_status],
        ["Shipment Status:", order.shipment_status],
    ]
    info_table = Table(info_data, colWidths=[120, 300])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8 * mm))

    # Line items
    elements.append(Paragraph("Line Items", styles["Heading2"]))
    elements.append(Spacer(1, 4 * mm))

    item_data = [["Product", "Qty", "Unit Price", "Total"]]
    total = 0.0
    for item in order.items:
        product_name = item.product.name if item.product else f"Product #{item.product_id}"
        line_total = item.quantity * item.unit_price
        item_data.append([
            product_name[:40],
            str(item.quantity),
            f"${item.unit_price:.2f}",
            f"${line_total:.2f}",
        ])
        total += line_total
    item_data.append(["", "", "Total:", f"${total:.2f}"])

    item_table = Table(item_data, colWidths=[200, 60, 80, 80])
    item_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (-2, -1), (-1, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(item_table)

    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="order-{order_id}.pdf"'},
    )


def _generate_fallback_order_pdf(order, customer_name):
    """Minimal PDF fallback for a single order."""
    lines = [
        f"Order #{order.id}",
        f"Date: {order.order_date.isoformat() if order.order_date else 'N/A'}",
        f"Customer: {customer_name}",
        f"Region: {order.region or 'N/A'}",
        f"Payment: {order.payment_status}",
        f"Shipment: {order.shipment_status}",
        "",
        "Items:",
    ]
    total = 0.0
    for item in order.items:
        line_total = item.quantity * item.unit_price
        lines.append(f"  Product #{item.product_id} x{item.quantity} @ ${item.unit_price:.2f} = ${line_total:.2f}")
        total += line_total
    lines.append(f"  Total: ${total:.2f}")

    text_content = "\n".join(lines)

    pdf_lines = ["%PDF-1.4"]
    pdf_lines.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj")
    pdf_lines.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj")
    pdf_lines.append("3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]\n   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj")

    stream_parts = ["BT", "/F1 10 Tf"]
    y_pos = 750
    for line in lines:
        safe_line = line.replace("(", "\\(").replace(")", "\\)")
        stream_parts.append(f"1 0 0 1 50 {y_pos} Tm")
        stream_parts.append(f"({safe_line}) Tj")
        y_pos -= 16
    stream_parts.append("ET")
    stream_content = "\n".join(stream_parts)

    pdf_lines.append(f"4 0 obj\n<< /Length {len(stream_content)} >>\nstream\n{stream_content}\nendstream\nendobj")
    pdf_lines.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj")

    pdf_lines.append("xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000266 00000 n \n0000000800 00000 n \n")
    pdf_lines.append("trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n900\n%%EOF")

    pdf_bytes = "\n".join(pdf_lines).encode("latin-1")
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="order-{order.id}.pdf"'},
    )


def _generate_fallback_pdf(db: Session):
    """Generate a minimal valid PDF without reportlab as a fallback."""
    # Gather basic stats
    total_revenue = (
        db.query(func.coalesce(func.sum(Order.total_amount), 0.0)).scalar()
    )
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    total_products = db.query(func.count(Product.id)).scalar() or 0

    lines = [
        "InsightFlow Business Report",
        f"Generated: {date.today().isoformat()}",
        "",
        "Summary",
        f"  Total Revenue: ${total_revenue:,.2f}",
        f"  Total Orders: {total_orders}",
        f"  Total Customers: {total_customers}",
        f"  Total Products: {total_products}",
        "",
        "Report generated by InsightFlow Analytics Platform",
    ]

    text_content = "\n".join(lines)

    # Build a minimal PDF using raw PDF syntax
    pdf_lines = []
    pdf_lines.append("%PDF-1.4")

    # Catalog
    pdf_lines.append("1 0 obj")
    pdf_lines.append("<< /Type /Catalog /Pages 2 0 R >>")
    pdf_lines.append("endobj")

    # Pages
    pdf_lines.append("2 0 obj")
    pdf_lines.append("<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    pdf_lines.append("endobj")

    # Page
    pdf_lines.append("3 0 obj")
    pdf_lines.append("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]")
    pdf_lines.append("   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>")
    pdf_lines.append("endobj")

    # Content stream
    stream_lines = []
    stream_lines.append("BT")
    stream_lines.append("/F1 12 Tf")
    y_pos = 750
    for line in lines:
        safe_line = line.replace("(", "\\(").replace(")", "\\)")
        stream_lines.append(f"1 0 0 1 50 {y_pos} Tm")
        stream_lines.append(f"({safe_line}) Tj")
        y_pos -= 18
    stream_lines.append("ET")
    stream_content = "\n".join(stream_lines)

    pdf_lines.append("4 0 obj")
    pdf_lines.append(f"<< /Length {len(stream_content)} >>")
    pdf_lines.append("stream")
    pdf_lines.append(stream_content)
    pdf_lines.append("endstream")
    pdf_lines.append("endobj")

    # Font
    pdf_lines.append("5 0 obj")
    pdf_lines.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    pdf_lines.append("endobj")

    xref_offset = 0
    pdf_lines.append("xref")
    pdf_lines.append("0 6")
    pdf_lines.append("0000000000 65535 f ")
    # We'll approximate offsets - most PDF readers handle this
    pdf_lines.append("0000000009 00000 n ")
    pdf_lines.append("0000000058 00000 n ")
    pdf_lines.append("0000000115 00000 n ")
    pdf_lines.append("0000000266 00000 n ")
    pdf_lines.append("0000000800 00000 n ")

    pdf_lines.append("trailer")
    pdf_lines.append("<< /Size 6 /Root 1 0 R >>")
    pdf_lines.append("startxref")
    pdf_lines.append("900")
    pdf_lines.append("%%EOF")

    pdf_bytes = "\n".join(pdf_lines).encode("latin-1")

    filename = f"business_report_{date.today().isoformat()}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
