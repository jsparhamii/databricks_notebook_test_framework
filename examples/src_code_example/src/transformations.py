"""Example application code: Data transformations."""

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def clean_customer_data(df: DataFrame) -> DataFrame:
    """
    Clean customer data by standardizing formats.
    
    Args:
        df: Input dataframe with columns: id, name, email, phone
        
    Returns:
        Cleaned dataframe
    """
    return df.select(
        "id",
        F.upper(F.trim(df.name)).alias("name"),
        F.lower(F.trim(df.email)).alias("email"),
        F.regexp_replace(df.phone, r"[^\d]", "").alias("phone")
    )


def calculate_customer_lifetime_value(df: DataFrame) -> DataFrame:
    """
    Calculate customer lifetime value from transactions.
    
    Args:
        df: Dataframe with columns: customer_id, amount, date
        
    Returns:
        Dataframe with customer_id, total_value, transaction_count
    """
    return df.groupBy("customer_id").agg(
        F.sum("amount").alias("total_value"),
        F.count("*").alias("transaction_count"),
        F.min("date").alias("first_purchase"),
        F.max("date").alias("last_purchase")
    )

