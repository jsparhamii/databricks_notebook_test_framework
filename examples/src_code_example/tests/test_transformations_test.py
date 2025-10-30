"""Tests for transformations module."""

# Add parent's src/ directory to Python path
import sys
from pathlib import Path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from databricks_notebook_test_framework import NotebookTestFixture
from transformations import clean_customer_data, calculate_customer_lifetime_value


class TestCleanCustomerData(NotebookTestFixture):
    """Test the clean_customer_data function."""
    
    def run_setup(self):
        """Create test data."""
        # Create test customers with messy data
        self.raw_customers = spark.createDataFrame([
            (1, "  alice smith  ", "Alice.Smith@EXAMPLE.COM  ", "(555) 123-4567"),
            (2, "bob jones", "  BOB@example.com", "555-234-5678"),
            (3, "CHARLIE BROWN", "charlie@example.com", "5553456789"),
        ], ["id", "name", "email", "phone"])
        
        # Apply transformation
        self.cleaned = clean_customer_data(self.raw_customers)
    
    def test_names_are_uppercase_and_trimmed(self):
        """Names should be uppercase with no leading/trailing spaces."""
        for row in self.cleaned.collect():
            name = row["name"]
            assert name == name.upper(), f"Name not uppercase: {name}"
            assert name == name.strip(), f"Name has whitespace: '{name}'"
    
    def test_emails_are_lowercase_and_trimmed(self):
        """Emails should be lowercase with no leading/trailing spaces."""
        for row in self.cleaned.collect():
            email = row["email"]
            assert email == email.lower(), f"Email not lowercase: {email}"
            assert email == email.strip(), f"Email has whitespace: '{email}'"
    
    def test_phones_have_only_digits(self):
        """Phone numbers should contain only digits."""
        for row in self.cleaned.collect():
            phone = row["phone"]
            assert phone.isdigit(), f"Phone contains non-digits: {phone}"
            assert len(phone) == 10, f"Phone should be 10 digits, got {len(phone)}"
    
    def test_all_rows_preserved(self):
        """Should not lose any rows during cleaning."""
        assert self.raw_customers.count() == self.cleaned.count()


class TestCalculateCustomerLifetimeValue(NotebookTestFixture):
    """Test the calculate_customer_lifetime_value function."""
    
    def run_setup(self):
        """Create test transactions."""
        self.transactions = spark.createDataFrame([
            (1, 100.0, "2024-01-01"),
            (1, 150.0, "2024-01-15"),
            (1, 200.0, "2024-02-01"),
            (2, 50.0, "2024-01-10"),
            (2, 75.0, "2024-01-20"),
        ], ["customer_id", "amount", "date"])
        
        # Calculate CLV
        self.clv = calculate_customer_lifetime_value(self.transactions)
    
    def test_correct_total_value(self):
        """Total value should sum all transactions per customer."""
        customer_1 = self.clv.filter("customer_id = 1").collect()[0]
        customer_2 = self.clv.filter("customer_id = 2").collect()[0]
        
        assert customer_1["total_value"] == 450.0, "Customer 1 total incorrect"
        assert customer_2["total_value"] == 125.0, "Customer 2 total incorrect"
    
    def test_correct_transaction_count(self):
        """Transaction count should be accurate."""
        customer_1 = self.clv.filter("customer_id = 1").collect()[0]
        customer_2 = self.clv.filter("customer_id = 2").collect()[0]
        
        assert customer_1["transaction_count"] == 3, "Customer 1 count incorrect"
        assert customer_2["transaction_count"] == 2, "Customer 2 count incorrect"
    
    def test_date_ranges(self):
        """First and last purchase dates should be correct."""
        customer_1 = self.clv.filter("customer_id = 1").collect()[0]
        
        assert str(customer_1["first_purchase"]) == "2024-01-01"
        assert str(customer_1["last_purchase"]) == "2024-02-01"
    
    def test_all_customers_included(self):
        """Should have one row per customer."""
        assert self.clv.count() == 2, "Should have 2 customers"

