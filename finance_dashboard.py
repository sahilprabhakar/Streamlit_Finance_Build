import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# Page configuration
st.set_page_config(
    page_title="Personal Finance Dashboard",
    page_icon="💰",
    layout="wide"
)

# Initialize session state for storing transactions
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

# Title and description
st.title("💰 Personal Finance Dashboard")
st.markdown("Track your income and expenses with beautiful visualizations")

# Sidebar for adding transactions
with st.sidebar:
    st.header("Add Transaction")
    
    # Transaction type
    trans_type = st.selectbox("Type", ["Income", "Expense"])
    
    # Amount
    amount = st.number_input("Amount ($)", min_value=0.01, step=0.01)
    
    # Category based on type
    if trans_type == "Expense":
        categories = ["Food", "Transportation", "Entertainment", "Shopping", 
                     "Bills", "Healthcare", "Other"]
    else:
        categories = ["Salary", "Freelance", "Investment", "Gift", "Other"]
    
    category = st.selectbox("Category", categories)
    
    # Description
    description = st.text_input("Description (optional)")
    
    # Date
    trans_date = st.date_input("Date", date.today())
    
    # Add button
    if st.button("Add Transaction", type="primary"):
        if amount > 0:
            transaction = {
                "Date": trans_date,
                "Type": trans_type,
                "Category": category,
                "Amount": amount,
                "Description": description
            }
            st.session_state.transactions.append(transaction)
            st.success("Transaction added!")
            st.rerun()
        else:
            st.error("Please enter a valid amount")
    
    # Clear all data button
    st.divider()
    if st.button("Clear All Data", type="secondary"):
        st.session_state.transactions = []
        st.rerun()

# Main content area
if len(st.session_state.transactions) == 0:
    st.info("👆 Start by adding your first transaction in the sidebar!")
    
    # Show sample data option
    if st.button("Load Sample Data"):
        st.session_state.transactions = [
            {"Date": date(2024, 1, 1), "Type": "Income", "Category": "Salary", "Amount": 5000, "Description": "Monthly salary"},
            {"Date": date(2024, 1, 5), "Type": "Expense", "Category": "Food", "Amount": 150, "Description": "Groceries"},
            {"Date": date(2024, 1, 7), "Type": "Expense", "Category": "Transportation", "Amount": 80, "Description": "Gas"},
            {"Date": date(2024, 1, 10), "Type": "Expense", "Category": "Entertainment", "Amount": 120, "Description": "Movie and dinner"},
            {"Date": date(2024, 1, 12), "Type": "Expense", "Category": "Bills", "Amount": 200, "Description": "Electricity"},
            {"Date": date(2024, 1, 15), "Type": "Income", "Category": "Freelance", "Amount": 800, "Description": "Web design project"},
            {"Date": date(2024, 1, 18), "Type": "Expense", "Category": "Shopping", "Amount": 250, "Description": "Clothes"},
            {"Date": date(2024, 1, 20), "Type": "Expense", "Category": "Food", "Amount": 200, "Description": "Restaurant"},
        ]
        st.rerun()
else:
    # Convert to DataFrame
    df = pd.DataFrame(st.session_state.transactions)
    
    # Calculate key metrics
    total_income = df[df['Type'] == 'Income']['Amount'].sum()
    total_expenses = df[df['Type'] == 'Expense']['Amount'].sum()
    net_savings = total_income - total_expenses
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Income", f"${total_income:,.2f}", delta=None)
    
    with col2:
        st.metric("Total Expenses", f"${total_expenses:,.2f}", delta=None)
    
    with col3:
        savings_delta = "positive" if net_savings > 0 else "negative"
        st.metric("Net Savings", f"${net_savings:,.2f}", 
                 delta=f"{(net_savings/total_income*100):.1f}%" if total_income > 0 else "0%")
    
    with col4:
        num_transactions = len(df)
        st.metric("Transactions", num_transactions)
    
    st.divider()
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Expenses by Category")
        expenses_df = df[df['Type'] == 'Expense']
        if len(expenses_df) > 0:
            category_totals = expenses_df.groupby('Category')['Amount'].sum().reset_index()
            fig_pie = px.pie(category_totals, values='Amount', names='Category',
                            color_discrete_sequence=px.colors.qualitative.Set3)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, width='stretch')
        else:
            st.info("No expenses recorded yet")
    
    with col2:
        st.subheader("Income vs Expenses")
        type_totals = df.groupby('Type')['Amount'].sum().reset_index()
        fig_bar = px.bar(type_totals, x='Type', y='Amount',
                        color='Type',
                        color_discrete_map={'Income': '#2ecc71', 'Expense': '#e74c3c'})
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, width='stretch')
    
    # Spending trend over time
    st.subheader("Spending Trend Over Time")
    df['Date'] = pd.to_datetime(df['Date'])
    df_sorted = df.sort_values('Date')
    
    # Create cumulative line chart
    income_df = df_sorted[df_sorted['Type'] == 'Income'].copy()
    expense_df = df_sorted[df_sorted['Type'] == 'Expense'].copy()
    
    fig_line = go.Figure()
    
    if len(income_df) > 0:
        fig_line.add_trace(go.Scatter(x=income_df['Date'], y=income_df['Amount'],
                                     mode='lines+markers', name='Income',
                                     line=dict(color='#2ecc71', width=3)))
    
    if len(expense_df) > 0:
        fig_line.add_trace(go.Scatter(x=expense_df['Date'], y=expense_df['Amount'],
                                     mode='lines+markers', name='Expenses',
                                     line=dict(color='#e74c3c', width=3)))
    
    fig_line.update_layout(xaxis_title="Date", yaxis_title="Amount ($)",
                          hovermode='x unified')
    st.plotly_chart(fig_line, width='stretch')
    
    # Transaction history table
    st.subheader("Transaction History")
    
    # Add filters
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        filter_type = st.multiselect("Filter by Type", 
                                    options=df['Type'].unique(),
                                    default=df['Type'].unique())
    with filter_col2:
        filter_category = st.multiselect("Filter by Category",
                                        options=df['Category'].unique(),
                                        default=df['Category'].unique())
    
    # Apply filters
    filtered_df = df[
        (df['Type'].isin(filter_type)) & 
        (df['Category'].isin(filter_category))
    ]
    
    # Display filtered dataframe
    display_df = filtered_df.sort_values('Date', ascending=False).reset_index(drop=True)
    display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d')
    display_df['Amount'] = display_df['Amount'].apply(lambda x: f"${x:,.2f}")
    
    st.dataframe(display_df, width='stretch', hide_index=True)
    
    # Download data as CSV
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Data as CSV",
        data=csv,
        file_name="finance_data.csv",
        mime="text/csv"
    )