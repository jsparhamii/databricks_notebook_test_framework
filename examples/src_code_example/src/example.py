# Databricks notebook source
def sum_column(df, col_name, new_col_name=None):
    """
    Sum a column in a DataFrame.
    
    Args:
        df: Input DataFrame
        col_name: Column name to sum
        new_col_name: Optional name for the result column
    
    Returns:
        DataFrame with the sum result
    """
    if new_col_name is None:
        new_col_name = col_name
    result = df.groupBy().sum(col_name).withColumnRenamed(f"sum({col_name})", new_col_name)
    return result

