import csv
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict

class SampleDataGenerator:
    """
    Generates sample retail sales data for testing the ETL pipeline
    """
    
    def __init__(self):
        self.categories = ['Electronics', 'Clothing', 'Home', 'Sports', 'Books', 'Toys']
        self.payment_methods = ['Credit Card', 'Debit Card', 'Cash', 'PayPal']
        self.store_ids = [f'STORE{i:03d}' for i in range(1, 21)]  # 20 stores
        self.sales_rep_ids = [f'REP{i:03d}' for i in range(1, 51)]  # 50 sales reps
        
        # Product catalog by category
        self.products = {
            'Electronics': [
                ('Laptop Computer', 800, 1500),
                ('Smartphone', 300, 1200),
                ('Tablet', 200, 800),
                ('Headphones', 50, 300),
                ('Smart Watch', 150, 600),
                ('Camera', 400, 2000),
            ],
            'Clothing': [
                ('T-Shirt', 15, 50),
                ('Jeans', 40, 120),
                ('Sneakers', 60, 200),
                ('Jacket', 80, 300),
                ('Dress', 50, 250),
                ('Sweater', 35, 150),
            ],
            'Home': [
                ('Coffee Maker', 80, 400),
                ('Vacuum Cleaner', 150, 600),
                ('Dining Table', 300, 1500),
                ('Bedding Set', 40, 200),
                ('Kitchen Knife Set', 60, 300),
                ('Picture Frame', 15, 80),
            ],
            'Sports': [
                ('Running Shoes', 80, 250),
                ('Yoga Mat', 25, 100),
                ('Dumbbells', 50, 200),
                ('Tennis Racket', 100, 400),
                ('Basketball', 20, 80),
                ('Bike Helmet', 40, 150),
            ],
            'Books': [
                ('Fiction Novel', 10, 25),
                ('Cookbook', 15, 40),
                ('Technical Manual', 30, 80),
                ('Children Book', 8, 20),
                ('Biography', 12, 30),
                ('Travel Guide', 18, 45),
            ],
            'Toys': [
                ('Action Figure', 15, 50),
                ('Board Game', 25, 100),
                ('Building Blocks', 30, 120),
                ('Puzzle', 10, 40),
                ('Toy Car', 12, 60),
                ('Doll', 20, 80),
            ]
        }
    
    def generate_transaction_id(self) -> str:
        """Generate unique transaction ID"""
        return f"TXN{uuid.uuid4().hex[:8].upper()}"
    
    def generate_customer_id(self) -> str:
        """Generate customer ID"""
        return f"CUST{random.randint(1, 10000):05d}"
    
    def generate_product_data(self) -> Dict[str, str]:
        """Generate product data"""
        category = random.choice(self.categories)
        product_name, min_price, max_price = random.choice(self.products[category])
        product_id = f"PROD{uuid.uuid4().hex[:6].upper()}"
        unit_price = round(random.uniform(min_price, max_price), 2)
        
        return {
            'product_id': product_id,
            'product_name': product_name,
            'category': category,
            'unit_price': unit_price
        }
    
    def generate_transaction_date(self, start_date: datetime, end_date: datetime) -> datetime:
        """Generate random transaction date within range"""
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        random_hours = random.randint(9, 21)  # Business hours
        random_minutes = random.randint(0, 59)
        
        return start_date + timedelta(days=random_days, hours=random_hours, minutes=random_minutes)
    
    def generate_sample_data(self, 
                           num_transactions: int = 10000,
                           start_date: datetime = None,
                           end_date: datetime = None) -> List[Dict]:
        """
        Generate sample retail transaction data
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()
        
        transactions = []
        
        for _ in range(num_transactions):
            product_data = self.generate_product_data()
            quantity = random.randint(1, 5)
            total_amount = round(product_data['unit_price'] * quantity, 2)
            transaction_date = self.generate_transaction_date(start_date, end_date)
            
            # Add some data quality issues (5% of records)
            if random.random() < 0.05:
                # Introduce missing or invalid data
                if random.random() < 0.3:
                    product_data['product_name'] = ''  # Missing product name
                elif random.random() < 0.3:
                    quantity = 0  # Invalid quantity
                elif random.random() < 0.3:
                    total_amount = 0  # Invalid amount
            
            transaction = {
                'transaction_id': self.generate_transaction_id(),
                'customer_id': self.generate_customer_id(),
                'product_id': product_data['product_id'],
                'product_name': product_data['product_name'],
                'category': product_data['category'],
                'quantity': quantity,
                'unit_price': product_data['unit_price'],
                'total_amount': total_amount,
                'transaction_date': transaction_date.strftime('%Y-%m-%d %H:%M:%S'),
                'store_id': random.choice(self.store_ids),
                'sales_rep_id': random.choice(self.sales_rep_ids),
                'payment_method': random.choice(self.payment_methods)
            }
            
            transactions.append(transaction)
        
        return transactions
    
    def save_to_csv(self, transactions: List[Dict], filename: str):
        """Save transactions to CSV file"""
        fieldnames = [
            'transaction_id', 'customer_id', 'product_id', 'product_name',
            'category', 'quantity', 'unit_price', 'total_amount',
            'transaction_date', 'store_id', 'sales_rep_id', 'payment_method'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(transactions)
        
        print(f"Generated {len(transactions)} transactions and saved to {filename}")
    
    def generate_monthly_files(self, 
                              base_path: str = "./sample_data",
                              transactions_per_month: int = 2000,
                              num_months: int = 12):
        """
        Generate monthly data files for testing
        """
        import os
        os.makedirs(base_path, exist_ok=True)
        
        end_date = datetime.now()
        
        for month_offset in range(num_months):
            month_end = end_date - timedelta(days=30 * month_offset)
            month_start = month_end - timedelta(days=30)
            
            transactions = self.generate_sample_data(
                num_transactions=transactions_per_month,
                start_date=month_start,
                end_date=month_end
            )
            
            # Create directory structure for partitioning
            year = month_start.year
            month = month_start.month
            
            dir_path = os.path.join(base_path, f"year={year}", f"month={month:02d}")
            os.makedirs(dir_path, exist_ok=True)
            
            filename = os.path.join(dir_path, f"sales_data_{year}_{month:02d}.csv")
            self.save_to_csv(transactions, filename)

def main():
    """
    Generate sample data for testing
    """
    generator = SampleDataGenerator()
    
    # Generate a single large file
    print("Generating single sample file...")
    transactions = generator.generate_sample_data(num_transactions=5000)
    generator.save_to_csv(transactions, "sample_retail_data.csv")
    
    # Generate monthly partitioned files
    print("Generating monthly partitioned files...")
    generator.generate_monthly_files(
        base_path="./sample_data_partitioned",
        transactions_per_month=1000,
        num_months=6
    )
    
    print("Sample data generation completed!")

if __name__ == "__main__":
    main()