-- Overall ETL validation
SELECT COUNT(*) AS total_records,
       MIN(year) AS earliest_year,
       MAX(year) AS latest_year,
       COUNT(DISTINCT kind_of_business) AS business_categories,
       SUM(sales IS NULL) AS null_sales_records
FROM monthly_retail_sales;

-- Latest-year month coverage
SELECT year, month, month_name,
       COUNT(*) AS rows_total,
       COUNT(sales) AS rows_with_sales,
       SUM(sales IS NULL) AS null_sales_rows
FROM monthly_retail_sales
WHERE year = (SELECT MAX(year) FROM monthly_retail_sales)
GROUP BY year, month, month_name
ORDER BY month;
