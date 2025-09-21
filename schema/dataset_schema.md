# Dataset Schema for AI SQL Generation

## Database Information
- **Database Name**: `insights_db`
- **Table Name**: `sales_data`
- **Format**: Parquet
- **Partitioning**: By year and month

## Table Schema

### Core Columns

| Column Name | Data Type | Description | Example Values |
|-------------|-----------|-------------|----------------|
| `order_id` | STRING | Unique identifier for each order | "ORD-2024-001234" |
| `customer_id` | STRING | Unique customer identifier | "CUST-12345" |
| `date` | DATE | Transaction date | "2024-01-15" |
| `region` | STRING | Geographic region | "North America", "Europe", "Asia-Pacific" |
| `product_category` | STRING | Product category | "Electronics", "Clothing", "Books" |
| `product_name` | STRING | Specific product name | "iPhone 15", "Samsung TV" |
| `sales_amount` | DECIMAL(10,2) | Revenue amount | 1299.99 |
| `quantity` | INTEGER | Number of items sold | 2 |
| `discount_percent` | DECIMAL(5,2) | Discount applied | 10.50 |
| `sales_rep_id` | STRING | Sales representative | "REP-789" |

### Partition Columns

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `year` | INTEGER | Year partition (extracted from date) |
| `month` | INTEGER | Month partition (extracted from date) |

### Additional Metadata Columns

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `processed_date` | DATE | Date when record was processed |
| `data_source` | STRING | Origin of the data |

## Query Guidelines for AI

### Common Query Patterns

1. **Time-based Analysis**
   ```sql
   SELECT region, SUM(sales_amount) as total_sales
   FROM sales_data 
   WHERE year = 2024 AND month >= 1
   GROUP BY region;
   ```

2. **Product Performance**
   ```sql
   SELECT product_category, 
          COUNT(*) as order_count,
          SUM(sales_amount) as revenue
   FROM sales_data 
   WHERE year = 2024
   GROUP BY product_category
   ORDER BY revenue DESC;
   ```

3. **Customer Analysis**
   ```sql
   SELECT customer_id,
          COUNT(DISTINCT order_id) as total_orders,
          SUM(sales_amount) as customer_value
   FROM sales_data
   WHERE year = 2024
   GROUP BY customer_id
   ORDER BY customer_value DESC
   LIMIT 10;
   ```

### Performance Optimization

- **Always use partition filters** when possible (year, month)
- **Use appropriate aggregations** for large datasets
- **Limit results** for exploratory queries
- **Use column projections** to reduce data scanned

### Sample Natural Language to SQL Mappings

| Natural Language Request | Generated SQL Query |
|--------------------------|-------------------|
| "Show me sales by region for this year" | `SELECT region, SUM(sales_amount) FROM sales_data WHERE year = 2024 GROUP BY region` |
| "Top 5 products by revenue last month" | `SELECT product_name, SUM(sales_amount) as revenue FROM sales_data WHERE year = 2024 AND month = 12 GROUP BY product_name ORDER BY revenue DESC LIMIT 5` |
| "Customer retention analysis" | `SELECT COUNT(DISTINCT customer_id) as customers, COUNT(DISTINCT order_id) as orders FROM sales_data WHERE year = 2024` |

## Data Quality Notes

- All currency amounts are in USD
- Dates are in YYYY-MM-DD format
- Region names are standardized
- Product categories follow a controlled vocabulary
- Missing values should be handled appropriately in queries