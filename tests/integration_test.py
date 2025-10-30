"""
Integration test example for testing multiple notebooks together.
"""

from databricks_notebook_test_framework import NotebookTestFixture


class TestIntegrationPipeline(NotebookTestFixture):
    """
    Integration tests for a data pipeline.
    This tests the flow between multiple notebooks/processes.
    """
    
    def run_setup(self):
        """Setup: Create input data and tables."""
        # Create bronze layer test data
        self.bronze_data = spark.createDataFrame([
            (1, "product_a", 100, "2024-01-01", "complete"),
            (2, "product_b", 200, "2024-01-01", "complete"),
            (3, "product_c", 150, "2024-01-02", "complete"),
            (4, "product_d", 300, "2024-01-02", "pending"),
        ], ["order_id", "product", "amount", "date", "status"])
        
        # Save to temporary location
        self.bronze_table = "test_bronze_orders"
        self.bronze_data.write.format("delta").mode("overwrite").saveAsTable(self.bronze_table)
        
        # Create silver layer (transformed data)
        spark.sql(f"""
            CREATE OR REPLACE TABLE test_silver_orders AS
            SELECT 
                order_id,
                product,
                amount,
                date,
                status,
                CASE 
                    WHEN status = 'complete' THEN amount 
                    ELSE 0 
                END as completed_amount
            FROM {self.bronze_table}
        """)
        
        # Create gold layer (aggregated data)
        spark.sql("""
            CREATE OR REPLACE TABLE test_gold_daily_summary AS
            SELECT 
                date,
                COUNT(*) as total_orders,
                SUM(completed_amount) as total_revenue,
                COUNT(CASE WHEN status = 'complete' THEN 1 END) as completed_orders
            FROM test_silver_orders
            GROUP BY date
        """)
    
    def test_bronze_to_silver_transformation(self):
        """Test that bronze to silver transformation is correct."""
        silver = spark.table("test_silver_orders")
        
        # Check that all rows are present
        assert silver.count() == 4, "Expected 4 rows in silver table"
        
        # Check that completed_amount is calculated correctly
        completed_amounts = silver.filter("status = 'complete'").select("completed_amount")
        for row in completed_amounts.collect():
            assert row["completed_amount"] > 0, "Completed orders should have positive amount"
        
        pending_amounts = silver.filter("status = 'pending'").select("completed_amount")
        for row in pending_amounts.collect():
            assert row["completed_amount"] == 0, "Pending orders should have zero completed amount"
    
    def test_silver_to_gold_aggregation(self):
        """Test that silver to gold aggregation is correct."""
        gold = spark.table("test_gold_daily_summary")
        
        # Check that we have 2 days of data
        assert gold.count() == 2, "Expected 2 days in gold table"
        
        # Check aggregations for first day
        day1 = gold.filter("date = '2024-01-01'").collect()[0]
        assert day1["total_orders"] == 2, "Expected 2 orders on 2024-01-01"
        assert day1["total_revenue"] == 300, "Expected revenue of 300 on 2024-01-01"
        assert day1["completed_orders"] == 2, "Expected 2 completed orders on 2024-01-01"
        
        # Check aggregations for second day
        day2 = gold.filter("date = '2024-01-02'").collect()[0]
        assert day2["total_orders"] == 2, "Expected 2 orders on 2024-01-02"
        assert day2["total_revenue"] == 150, "Expected revenue of 150 on 2024-01-02"
        assert day2["completed_orders"] == 1, "Expected 1 completed order on 2024-01-02"
    
    def test_end_to_end_revenue(self):
        """Test end-to-end revenue calculation."""
        # Calculate total revenue from gold table
        gold_revenue = spark.sql("""
            SELECT SUM(total_revenue) as total
            FROM test_gold_daily_summary
        """).collect()[0]["total"]
        
        # Calculate expected revenue from bronze
        expected_revenue = spark.sql(f"""
            SELECT SUM(amount) as total
            FROM {self.bronze_table}
            WHERE status = 'complete'
        """).collect()[0]["total"]
        
        assert gold_revenue == expected_revenue, \
            f"Gold revenue {gold_revenue} doesn't match expected {expected_revenue}"
    
    def test_data_completeness(self):
        """Test that no data is lost in the pipeline."""
        bronze_count = spark.table(self.bronze_table).count()
        silver_count = spark.table("test_silver_orders").count()
        
        assert bronze_count == silver_count, \
            "Row count mismatch between bronze and silver layers"
    
    def test_idempotency(self):
        """Test that running the pipeline again produces the same results."""
        # Get current gold data
        gold_before = spark.table("test_gold_daily_summary").collect()
        
        # Rerun silver transformation
        spark.sql(f"""
            CREATE OR REPLACE TABLE test_silver_orders AS
            SELECT 
                order_id,
                product,
                amount,
                date,
                status,
                CASE 
                    WHEN status = 'complete' THEN amount 
                    ELSE 0 
                END as completed_amount
            FROM {self.bronze_table}
        """)
        
        # Rerun gold aggregation
        spark.sql("""
            CREATE OR REPLACE TABLE test_gold_daily_summary AS
            SELECT 
                date,
                COUNT(*) as total_orders,
                SUM(completed_amount) as total_revenue,
                COUNT(CASE WHEN status = 'complete' THEN 1 END) as completed_orders
            FROM test_silver_orders
            GROUP BY date
        """)
        
        # Get gold data after rerun
        gold_after = spark.table("test_gold_daily_summary").collect()
        
        # Compare
        assert len(gold_before) == len(gold_after), "Row count changed after rerun"
        
        # Sort and compare values
        gold_before_sorted = sorted(gold_before, key=lambda x: x["date"])
        gold_after_sorted = sorted(gold_after, key=lambda x: x["date"])
        
        for before, after in zip(gold_before_sorted, gold_after_sorted):
            assert before["total_revenue"] == after["total_revenue"], \
                "Revenue values changed after rerun (not idempotent)"
    
    def run_cleanup(self):
        """Cleanup: Drop all test tables."""
        spark.sql(f"DROP TABLE IF EXISTS {self.bronze_table}")
        spark.sql("DROP TABLE IF EXISTS test_silver_orders")
        spark.sql("DROP TABLE IF EXISTS test_gold_daily_summary")

