# CRM Sales & Inventory Analytics Dashboard

## Project Overview

A comprehensive Business Intelligence solution built with Python, Pandas, and OpenPyXL that simulates a complete CRM, sales pipeline, customer management, and inventory monitoring system. This dashboard produces a professionally formatted Excel workbook with KPIs, visualizations, pivot summaries, and automated insights designed for operational and executive review.

## Business Scenario

A company needs to track:
- Customer relationships and segmentation
- Sales performance and revenue trends
- Product inventory levels and stock management
- Sales pipeline and conversion rates
- Lost opportunities and profit margins

## Features

### 1. Data Generation
- **250 customers** with realistic attributes (industry, location, segment, status)
- **1,000 sales transactions** with revenue, profit, discounts, and sales reps
- **50 products** with inventory tracking and stock levels
- **150 sales pipeline leads** with stages and probability calculations

### 2. Excel Dashboard Sheets

#### CRM Dashboard
- Key Performance Indicators (KPIs):
  - Total Customers
  - Total Revenue
  - Total Profit
  - Active Leads
  - Conversion Rate
  - Average Order Value
- Visualizations:
  - Monthly revenue trend (line chart)
  - Sales by representative (bar chart)
  - Revenue by industry (pie chart)
  - Customer segmentation (pie chart)

#### Inventory Dashboard

![Inventory Management](https://github.com/INNOCENT256-UG/INVENTORY-MANAGEMENT/blob/main/Charts/Inventory%20Management.png)

The Inventory Dashboard concisely surfaces stock status, value, and movement so supply and operations teams can make timely decisions.

Inventory Metrics:
- Current stock value (by SKU and aggregated)
- Total products and SKU counts by category
- Low-stock products (below reorder point)
- Out-of-stock products and backorder risk

Visualizations and recommended views:
- Inventory by category (bar chart) — quick view of category distribution and value concentration
- Top-selling products (ranked bar chart) — identify SKUs that drive revenue and require prioritized replenishment
- Stock movement over time (line/area chart) — track inflows and outflows to spot seasonality or demand shifts
- Stock value heatmap (by warehouse) — detect where capital is tied up

Conditional Formatting and Alerts:
- Red highlighting for products below minimum stock level
- Yellow warning for products approaching reorder level
- Automated flags for slow-moving inventory (over a configurable threshold)


### Inventory exploration: recommended views and how to use them

To make inventory monitoring actionable, include the following exploration views in your workbook. Each view answers a specific operational question and helps prioritize actions.

1. Stock Health Overview (Executive view)
   - Purpose: Provide a one-page summary for stakeholders.
   - Contains: Total stock value, number of SKUs low or out of stock, top 5 stock-value SKUs, and a trend sparkline for total inventory value.
   - Use: Daily or weekly checks to quickly assess supply risk.

2. Reorder and Procurement View (Operational)
   - Purpose: Guide purchasing decisions.
   - Contains: SKU, current stock, minimum stock level, lead time (days), supplier, suggested reorder quantity (based on safety stock and forecasted demand).
   - Use: Run before procurement cycles and integrate into purchase order workflows.

3. Demand & Movement View (Analyst)
   - Purpose: Understand demand patterns and velocity.
   - Contains: Sales velocity (units/day), average lead time, days of stock remaining, top movers, and slow movers.
   - Use: Weekly analysis to update forecasting and safety-stock calculations.

4. Warehouse & Location View (Logistics)
   - Purpose: Visualize inventory distribution and storage utilization.
   - Contains: Stock value by warehouse, SKU counts per location, heatmap of high-density SKUs.
   - Use: Optimize transfers between warehouses and identify consolidation opportunities.

5. Financial Impact View (Finance)
   - Purpose: Connect inventory to working capital and profitability.
   - Contains: Stock value by SKU, carrying cost estimate, contribution margin for top SKUs, and inventory turnover ratio.
   - Use: Monthly reporting and capital allocation.

Best practices for exploration:
- Start with aggregated KPIs then drill down: executives want one-line insights; analysts need underlying tables.
- Combine charts with the raw table (Excel Table) so clicking or filtering retains context.
- Use pivot tables for fast, ad-hoc slicing and add slicers for interactive filtering by period, category, or rep.
- Annotate charts with business context (e.g., "Seasonal peak — expected"), so viewers can interpret the data quickly.
- Automate alerts for thresholds (low stock, negative stock value, extreme lead times) and surface them in the "Automated Insights" sheet.


#### Sales Performance Dashboard
- Salesperson ranking with revenue, profit, and order counts
- Monthly targets vs actual sales with variance analysis
- Profit margin analysis by sales representative
- Best customers list (top 10)
- Lost opportunities analysis

#### Automated Insights
Dynamic business recommendations including:
- Critical inventory alerts
- Sales trend analysis (month-over-month changes)
- Top performing customer segments
- Best sales performers
- Lost opportunity values
- Overall profit margins

#### Pivot Analytics
- Revenue by sales representative and status
- Customer distribution by industry and segment
- Product performance analysis (top 15 products)

### 3. Raw Data Sheets
- **Customers**: Complete customer database with 250 records
- **Sales Transactions**: 1,000 transaction records with full details
- **Product Inventory**: 50 products with stock levels and values
- **Sales Pipeline**: 150 leads with stages and expected revenue

## Technical Implementation

### Technologies Used
- **Python 3.x**
- **Pandas**: Data manipulation and analysis
- **OpenPyXL**: Excel file creation and formatting
- **Excel Tables**: Auto-expanding data ranges
- **Excel Charts**: Native chart objects for visualization
- **Conditional Formatting**: Dynamic cell highlighting

### Key Features
- Excel Tables for automatic data expansion
- Professional formatting with headers, borders, and colors
- Multiple chart types (line, bar, pie)
- Pivot table summaries
- Automated business insights with priority levels
- Professional color-coded metrics

## File Structure

```
DATA ANALYSIS/
├── generate_crm_data.py          # Data generation script
├── build_dashboard.py            # Dashboard builder script
├── CRM_Sales_Inventory_Dashboard.xlsx  # Final Excel dashboard
├── customers.csv                 # Generated customer data
├── sales_transactions.csv        # Generated transaction data
├── product_inventory.csv         # Generated inventory data
├── sales_pipeline.csv            # Generated pipeline data
└── README.md                     # This file
```

## Installation & Usage

### Prerequisites
```bash
pip install pandas openpyxl
```

### Step 1: Generate Data
```bash
python generate_crm_data.py
```

This will create:
- `customers.csv` (250 records)
- `sales_transactions.csv` (1,000 records)
- `product_inventory.csv` (50 records)
- `sales_pipeline.csv` (150 records)

### Step 2: Build Dashboard
```bash
python build_dashboard.py
```

This will create:
- `CRM_Sales_Inventory_Dashboard.xlsx` (9 sheets with all dashboards and charts)

## Dashboard Structure

### Sheet Organization
1. **CRM Dashboard** - Main overview with KPIs and key charts
2. **Customers** - Raw customer data (Excel Table)
3. **Sales Transactions** - Raw transaction data (Excel Table)
4. **Product Inventory** - Raw inventory data (Excel Table)
5. **Sales Pipeline** - Raw pipeline data (Excel Table)
6. **Inventory Dashboard** - Inventory metrics and analysis
7. **Sales Performance** - Sales team performance metrics
8. **Automated Insights** - AI-generated business recommendations
9. **Pivot Analytics** - Pivot table summaries

## Data Schema

### Customers Table
| Column | Type | Description |
|--------|------|-------------|
| Customer ID | String | Unique identifier (CUST-0001) |
| Customer Name | String | Customer name |
| Industry | String | Business industry |
| Location | String | City location |
| Customer Segment | String | Enterprise, SMB, Startup, Government, Non-Profit |
| Registration Date | Date | Customer registration date |
| Customer Status | String | Active, Inactive, Pending, Churned |

### Sales Transactions Table
| Column | Type | Description |
|--------|------|-------------|
| Order ID | String | Unique order identifier |
| Customer ID | String | Reference to customer |
| Product ID | String | Reference to product |
| Sales Representative | String | Sales rep name |
| Order Date | Date | Transaction date |
| Quantity Sold | Integer | Units sold |
| Unit Price | Float | Price per unit |
| Revenue | Float | Total revenue |
| Discount | Float | Discount percentage |
| Profit | Float | Profit amount |
| Sales Status | String | Completed, Pending, Cancelled, Refunded |

### Product Inventory Table
| Column | Type | Description |
|--------|------|-------------|
| Product ID | String | Unique product identifier |
| Product Name | String | Product name |
| Category | String | Electronics, Software, Hardware, Services, Accessories |
| Supplier | String | Supplier name |
| Current Stock | Integer | Units in stock |
| Minimum Stock Level | Integer | Reorder threshold |
| Unit Cost | Float | Cost per unit |
| Stock Value | Float | Total inventory value |
| Warehouse Location | String | Storage location |

### Sales Pipeline Table
| Column | Type | Description |
|--------|------|-------------|
| Lead ID | String | Unique lead identifier |
| Customer Name | String | Potential customer |
| Sales Stage | String | Pipeline stage |
| Opportunity Value | Float | Potential revenue |
| Probability % | Float | Win probability (0-1) |
| Expected Revenue | Float | Value * probability |
| Sales Owner | String | Assigned sales rep |
| Closing Date | Date | Expected close date |

## Key Insights Generated

The dashboard automatically generates insights such as:

1. **Inventory Alerts**: "X products are below minimum stock level and require immediate restocking"
2. **Sales Trends**: "Sales decreased by X% compared to previous month"
3. **Top Performers**: "Customer segment 'Enterprise' generates the highest revenue ($X, X% of total)"
4. **Best Reps**: "Top performer: John Smith with $X in revenue"
5. **Lost Opportunities**: "X opportunities lost with total value of $X"
6. **Profit Margins**: "Overall profit margin: X%"

## Customization

### Adding New Data
The Excel Tables are set up to auto-expand. To add new data:
1. Open the raw data sheets (Customers, Sales Transactions, etc.)
2. Add new rows at the bottom of the table
3. The dashboard will automatically include the new data

### Modifying Metrics
Edit the `build_dashboard.py` file to:
- Change metric calculations
- Add new KPIs
- Modify chart types or data ranges
- Adjust conditional formatting rules

### Regenerating the Dashboard
After modifying data or code:
```bash
python build_dashboard.py
```

## Portfolio Highlights

This project demonstrates:
- **Data Engineering**: Generating realistic, large-scale datasets (1,450+ records)
- **Data Analysis**: Pandas aggregation, merging, and statistical analysis
- **Business Intelligence**: KPI tracking, trend analysis, and insights generation
- **Excel Automation**: Programmatic Excel file creation with professional formatting
- **Visualization**: Multiple chart types for different data dimensions
- **Problem Solving**: Debugging encoding issues, data type handling, and merge logic

## Results

- **9 Excel sheets** with comprehensive data and analytics
- **6+ interactive charts** for data visualization
- **4 Excel Tables** for auto-expanding data ranges
- **Automated insights** with priority-based color coding
- **Conditional formatting** for inventory alerts
- **1,450+ records** across 4 data tables
- **Professional formatting** suitable for executive presentation

## Future Enhancements

Potential additions:
- Slicers for interactive filtering
- More advanced pivot tables
- Additional chart types (scatter plots, heat maps)
- Forecast models for revenue prediction
- Customer lifetime value calculations
- Inventory optimization algorithms
- Export to PDF functionality
- Email automation for insights distribution

## Author

Created as a Data Analyst portfolio project demonstrating advanced Excel automation, data analysis, and business intelligence capabilities.

## License

This project is open source and available for portfolio use.
