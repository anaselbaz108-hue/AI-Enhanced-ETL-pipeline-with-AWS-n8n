# Dataset Schema for AI SQL Generation

## Database Information
- **Database Name**: `retail-sales-db`
- **Table Name**: `processed_zone` (for processed data), `raw_zone` (for raw data)
- **Format**: Parquet (processed), CSV (raw)
- **Partitioning**: By year, month, and day

## Table Schema

### Core Columns

| Column Name | Data Type | Description | Example Values |
|-------------|-----------|-------------|----------------|
| `transaction_id` | STRING | Unique identifier for each transaction | "TXN-2024-001234" |
| `date` | DATE | Transaction date | "2024-01-15" |
| `customer_id` | STRING | Unique customer identifier | "CUST-12345" |
| `gender` | STRING | Customer gender | "Male", "Female" |
| `age` | INTEGER | Customer age | 25, 34, 45 |
| `product_category` | STRING | Product category | "Electronics", "Clothing", "Beauty" |
| `quantity` | INTEGER | Number of units purchased | 1, 2, 5 |
| `price_per_unit` | DECIMAL(10,2) | Price of one unit | 29.99, 149.50 |
| `total_amount` | DECIMAL(10,2) | Total transaction value | 59.98, 149.50 |

### Partition Columns

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `year` | INTEGER | Year partition (extracted from date) |
| `month` | INTEGER | Month partition (extracted from date) |
| `day` | INTEGER | Day partition (extracted from date) |

### Additional Metadata Columns

| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| `processed_date` | DATE | Date when record was processed |
| `data_source` | STRING | Origin of the data |

## Query Guidelines for AI

### Common Query Patterns

1. **Time-based Analysis**
   ```sql
   SELECT product_category, SUM(total_amount) as total_sales
   FROM processed_zone 
   WHERE year = 2024 AND month >= 1
   GROUP BY product_category;
   ```

2. **Gender-based Analysis**
   ```sql
   SELECT gender, 
          COUNT(*) as transaction_count,
          SUM(total_amount) as revenue,
          AVG(total_amount) as avg_transaction
   FROM processed_zone 
   WHERE year = 2024
   GROUP BY gender;
   ```

3. **Age Group Analysis**
   ```sql
   SELECT 
     CASE 
       WHEN age < 25 THEN '18-24'
       WHEN age < 35 THEN '25-34'
       WHEN age < 45 THEN '35-44'
       WHEN age < 55 THEN '45-54'
       ELSE '55+'
     END as age_group,
     COUNT(*) as transactions,
     SUM(total_amount) as revenue
   FROM processed_zone
   WHERE year = 2024
   GROUP BY age_group
   ORDER BY revenue DESC;
   ```

4. **Product Category Performance**
   ```sql
   SELECT product_category, 
          COUNT(*) as transaction_count,
          SUM(quantity) as total_quantity,
          SUM(total_amount) as revenue,
          AVG(price_per_unit) as avg_price
   FROM processed_zone 
   WHERE year = 2024
   GROUP BY product_category
   ORDER BY revenue DESC;
   ```

5. **Customer Analysis**
   ```sql
   SELECT customer_id,
          COUNT(DISTINCT transaction_id) as total_transactions,
          SUM(total_amount) as customer_value,
          AVG(total_amount) as avg_transaction
   FROM processed_zone
   WHERE year = 2024
   GROUP BY customer_id
   ORDER BY customer_value DESC
   LIMIT 10;
   ```

### Performance Optimization

- **Always use partition filters** when possible (year, month, day)
- **Use appropriate aggregations** for large datasets
- **Limit results** for exploratory queries
- **Use column projections** to reduce data scanned

### Sample Natural Language to SQL Mappings

| Natural Language Request | Generated SQL Query |
|--------------------------|-------------------|
| "Show me sales by product category for this year" | `SELECT product_category, SUM(total_amount) FROM processed_zone WHERE year = 2024 GROUP BY product_category` |
| "Top 5 customers by spending last month" | `SELECT customer_id, SUM(total_amount) as spending FROM processed_zone WHERE year = 2024 AND month = 12 GROUP BY customer_id ORDER BY spending DESC LIMIT 5` |
| "Gender-based purchasing patterns" | `SELECT gender, COUNT(*) as transactions, AVG(total_amount) as avg_spend FROM processed_zone WHERE year = 2024 GROUP BY gender` |
| "Average age of customers by product category" | `SELECT product_category, AVG(age) as avg_age FROM processed_zone WHERE year = 2024 GROUP BY product_category` |

## Data Quality Notes

- All currency amounts are in USD
- Dates are in YYYY-MM-DD format
- Gender values are standardized ("Male", "Female")
- Product categories follow a controlled vocabulary
- Ages are positive integers
- Missing values should be handled appropriately in queries