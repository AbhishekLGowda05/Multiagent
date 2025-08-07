"""
Visualization utilities for generating charts and reports.
Supports matplotlib-based visualizations for business analytics.
"""

import os
import base64
from io import BytesIO
from typing import List, Dict, Any, Optional
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta

# Set matplotlib to non-interactive backend for server environments
plt.switch_backend('Agg')


def generate_chart(
    data: Optional[List[float]] = None, 
    labels: Optional[List[str]] = None,
    title: str = "Analytics Chart",
    chart_type: str = "line",
    path: str = "chart.png",
    figsize: tuple = (10, 6)
) -> str:
    """
    Create a chart from numeric data and return the file path.
    
    Args:
        data: List of numeric values to plot
        labels: Optional labels for x-axis
        title: Chart title
        chart_type: Type of chart ('line', 'bar', 'pie')
        path: Output file path
        figsize: Figure size (width, height)
    
    Returns:
        Path to saved chart file
    """
    if data is None:
        data = [10, 25, 30, 45, 60, 55, 70]  # Sample data
    
    if labels is None:
        labels = [f"Period {i+1}" for i in range(len(data))]
    
    plt.figure(figsize=figsize)
    
    if chart_type == "line":
        plt.plot(range(len(data)), data, marker="o", linewidth=2, markersize=6)
        plt.xlabel("Time Period")
        plt.ylabel("Value")
    elif chart_type == "bar":
        plt.bar(range(len(data)), data, color='skyblue', alpha=0.7)
        plt.xlabel("Category")
        plt.ylabel("Value")
        if len(labels) == len(data):
            plt.xticks(range(len(data)), labels, rotation=45)
    elif chart_type == "pie":
        plt.pie(data, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
    
    plt.savefig(path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return path


def generate_chart_base64(
    data: Optional[List[float]] = None,
    labels: Optional[List[str]] = None,
    title: str = "Analytics Chart",
    chart_type: str = "line",
    figsize: tuple = (10, 6)
) -> str:
    """
    Generate a chart and return it as a base64 encoded string for embedding in HTML.
    
    Returns:
        Base64 encoded image string
    """
    if data is None:
        data = [10, 25, 30, 45, 60, 55, 70]
    
    if labels is None:
        labels = [f"Period {i+1}" for i in range(len(data))]
    
    plt.figure(figsize=figsize)
    
    if chart_type == "line":
        plt.plot(range(len(data)), data, marker="o", linewidth=2, markersize=6)
        plt.xlabel("Time Period")
        plt.ylabel("Value")
    elif chart_type == "bar":
        plt.bar(range(len(data)), data, color='skyblue', alpha=0.7)
        plt.xlabel("Category")
        plt.ylabel("Value")
        if len(labels) == len(data):
            plt.xticks(range(len(data)), labels, rotation=45)
    elif chart_type == "pie":
        plt.pie(data, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.axis('equal')
    
    plt.title(title, fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save to BytesIO buffer
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
    buffer.seek(0)
    
    # Convert to base64
    image_base64 = base64.b64encode(buffer.getvalue()).decode()
    plt.close()
    buffer.close()
    
    return image_base64


def create_financial_dashboard(
    revenue_data: List[float],
    expense_data: List[float],
    profit_data: List[float],
    periods: List[str],
    output_path: str = "financial_dashboard.png"
) -> str:
    """
    Create a comprehensive financial dashboard with multiple subplots.
    
    Args:
        revenue_data: Revenue figures
        expense_data: Expense figures  
        profit_data: Profit figures
        periods: Time periods for x-axis
        output_path: Output file path
    
    Returns:
        Path to saved dashboard
    """
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    
    # Revenue trend
    ax1.plot(periods, revenue_data, marker='o', color='green', linewidth=2)
    ax1.set_title('Revenue Trend', fontweight='bold')
    ax1.set_ylabel('Revenue ($)')
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # Expense trend
    ax2.plot(periods, expense_data, marker='s', color='red', linewidth=2)
    ax2.set_title('Expense Trend', fontweight='bold')
    ax2.set_ylabel('Expenses ($)')
    ax2.grid(True, alpha=0.3)
    ax2.tick_params(axis='x', rotation=45)
    
    # Profit trend
    ax3.plot(periods, profit_data, marker='^', color='blue', linewidth=2)
    ax3.set_title('Profit Trend', fontweight='bold')
    ax3.set_ylabel('Profit ($)')
    ax3.grid(True, alpha=0.3)
    ax3.tick_params(axis='x', rotation=45)
    
    # Combined comparison
    ax4.plot(periods, revenue_data, label='Revenue', marker='o', color='green')
    ax4.plot(periods, expense_data, label='Expenses', marker='s', color='red')
    ax4.plot(periods, profit_data, label='Profit', marker='^', color='blue')
    ax4.set_title('Financial Overview', fontweight='bold')
    ax4.set_ylabel('Amount ($)')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_sales_chart(
    sales_data: Dict[str, float],
    chart_type: str = "bar",
    output_path: str = "sales_chart.png"
) -> str:
    """
    Create a sales performance chart.
    
    Args:
        sales_data: Dictionary with categories as keys and sales figures as values
        chart_type: Type of chart ('bar', 'pie', 'line')
        output_path: Output file path
    
    Returns:
        Path to saved chart
    """
    categories = list(sales_data.keys())
    values = list(sales_data.values())
    
    plt.figure(figsize=(12, 8))
    
    if chart_type == "bar":
        bars = plt.bar(categories, values, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
        plt.xlabel('Product Categories')
        plt.ylabel('Sales Amount ($)')
        plt.title('Sales Performance by Category', fontsize=16, fontweight='bold')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:,.0f}', ha='center', va='bottom')
                    
    elif chart_type == "pie":
        plt.pie(values, labels=categories, autopct='%1.1f%%', startangle=90,
                colors=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7'])
        plt.title('Sales Distribution by Category', fontsize=16, fontweight='bold')
        plt.axis('equal')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path


def create_inventory_chart(
    inventory_data: Dict[str, int],
    low_stock_threshold: int = 10,
    output_path: str = "inventory_chart.png"
) -> str:
    """
    Create an inventory levels chart with low stock highlighting.
    
    Args:
        inventory_data: Dictionary with item names and stock levels
        low_stock_threshold: Threshold for low stock warning
        output_path: Output file path
    
    Returns:
        Path to saved chart
    """
    items = list(inventory_data.keys())
    stock_levels = list(inventory_data.values())
    
    # Color code based on stock levels
    colors = ['red' if level <= low_stock_threshold else 'green' for level in stock_levels]
    
    plt.figure(figsize=(12, 8))
    bars = plt.bar(items, stock_levels, color=colors, alpha=0.7)
    
    # Add horizontal line for low stock threshold
    plt.axhline(y=low_stock_threshold, color='orange', linestyle='--', 
                label=f'Low Stock Threshold ({low_stock_threshold})')
    
    plt.xlabel('Inventory Items')
    plt.ylabel('Stock Level')
    plt.title('Current Inventory Status', fontsize=16, fontweight='bold')
    plt.legend()
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')
    
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path


def generate_html_report_with_charts(
    title: str,
    content: str,
    chart_paths: List[str],
    output_path: str = "report.html"
) -> str:
    """
    Generate an HTML report with embedded charts.
    
    Args:
        title: Report title
        content: Main content/text
        chart_paths: List of paths to chart images
        output_path: Output HTML file path
    
    Returns:
        Path to generated HTML report
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                line-height: 1.6;
            }}
            .header {{
                background-color: #f4f4f4;
                padding: 20px;
                text-align: center;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            .content {{
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-bottom: 30px;
            }}
            .chart {{
                text-align: center;
                margin: 30px 0;
                padding: 20px;
                background-color: #f9f9f9;
                border-radius: 10px;
            }}
            .chart img {{
                max-width: 100%;
                height: auto;
                border-radius: 5px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .timestamp {{
                color: #666;
                font-style: italic;
                text-align: center;
                margin-top: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{title}</h1>
        </div>
        
        <div class="content">
            <pre>{content}</pre>
        </div>
    """
    
    # Add charts
    for i, chart_path in enumerate(chart_paths):
        if os.path.exists(chart_path):
            # Convert to base64 for embedding
            with open(chart_path, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode()
            
            html_content += f"""
        <div class="chart">
            <h3>Chart {i+1}</h3>
            <img src="data:image/png;base64,{img_base64}" alt="Chart {i+1}">
        </div>
            """
    
    html_content += f"""
        <div class="timestamp">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </body>
    </html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_path
