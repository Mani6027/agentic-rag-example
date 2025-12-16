"""
Script to create a sample Excel file for testing the Agentic RAG system.
Run this script to generate sample_sales_data.xlsx
"""

import pandas as pd
import random
from datetime import datetime, timedelta

# Set random seed for reproducibility
random.seed(42)

# Generate sample data
n_records = 200

# Date range
start_date = datetime(2024, 1, 1)
dates = [start_date + timedelta(days=i) for i in range(n_records)]

# Product categories
products = ['Widget A', 'Widget B', 'Gadget X', 'Gadget Y', 'Tool Z']

# Regions
regions = ['North', 'South', 'East', 'West']

# Generate sales data
data = []
for i in range(n_records):
    record = {
        'date': dates[i],
        'product': random.choice(products),
        'region': random.choice(regions),
        'sales': round(random.uniform(100, 5000), 2),
        'quantity': random.randint(1, 50),
        'price': round(random.uniform(20, 200), 2),
    }
    data.append(record)

# Create DataFrame
df = pd.DataFrame(data)

# Calculate revenue (just for demonstration)
df['revenue'] = df['sales']

# Create a second sheet with summary data
summary_data = df.groupby('region').agg({
    'sales': 'sum',
    'quantity': 'sum'
}).reset_index()
summary_data.columns = ['region', 'total_sales', 'total_quantity']

# Write to Excel with multiple sheets
with pd.ExcelWriter('sample_sales_data.xlsx', engine='openpyxl') as writer:
    df.to_excel(writer, sheet_name='Sales', index=False)
    summary_data.to_excel(writer, sheet_name='Summary', index=False)

print("✅ Sample Excel file created: sample_sales_data.xlsx")
print(f"   - Sheet 'Sales': {len(df)} records")
print(f"   - Sheet 'Summary': {len(summary_data)} records")
print("\nSample data preview:")
print(df.head(10))
print("\nYou can now upload this file to test the API!")
