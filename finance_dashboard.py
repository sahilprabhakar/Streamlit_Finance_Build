import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import sqlite3
import hashlib

# Page configuration
st.set_page_config(
    page_title="Personal Finance Dashboard",
    page_icon="💰",
    layout="wide"
)

# Database setup and helper functions
class FinanceDB:
    def __init__(self, db_name="finance_app.db"):
        self.db_name = db_name
        self.init_database()
    
    def get_connection(self):
        """Create a database connection"""
        return sqlite3.connect(self.db_name, check_same_thread=False)
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                date DATE NOT NULL,
                type TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password for storage"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def create_user(self, username, password):
        """Create a new user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            password_hash = self.hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        conn = self.get_connection()
        cursor = conn.cursor()
        password_hash = self.hash_password(password)
        cursor.execute(
            "SELECT id FROM users WHERE username = ? AND password_hash = ?",
            (username, password_hash)
        )
        user = cursor.fetchone()
        conn.close()
        return user[0] if user else None
    
    def add_transaction(self, user_id, date, trans_type, category, amount, description):
        """Add a new transaction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO transactions (user_id, date, type, category, amount, description)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, date, trans_type, category, amount, description)
        )
        conn.commit()
        conn.close()
    
    def get_transactions(self, user_id):
        """Get all transactions for a user"""
        conn = self.get_connection()
        df = pd.read_sql_query(
            """SELECT id, date, type, category, amount, description 
               FROM transactions 
               WHERE user_id = ? 
               ORDER BY date DESC""",
            conn,
            params=(user_id,)
        )
        conn.close()
        return df
    
    def delete_transaction(self, transaction_id, user_id):
        """Delete a specific transaction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM transactions WHERE id = ? AND user_id = ?",
            (transaction_id, user_id)
        )
        conn.commit()
        conn.close()
    
    def clear_all_transactions(self, user_id):
        """Clear all transactions for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

# Initialize database
db = FinanceDB()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Login/Signup Page
if not st.session_state.logged_in:
    st.title("💰 Personal Finance Dashboard")
    st.markdown("### Welcome! Please login or create an account")
    
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    with tab1:
        st.subheader("Login")
        login_username = st.text_input("Username", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", type="primary"):
            user_id = db.verify_user(login_username, login_password)
            if user_id:
                st.session_state.logged_in = True
                st.session_state.user_id = user_id
                st.session_state.username = login_username
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    with tab2:
        st.subheader("Create Account")
        signup_username = st.text_input("Choose Username", key="signup_user")
        signup_password = st.text_input("Choose Password", type="password", key="signup_pass")
        signup_password_confirm = st.text_input("Confirm Password", type="password", key="signup_pass_confirm")
        
        if st.button("Sign Up", type="primary"):
            if not signup_username or not signup_password:
                st.error("Please fill in all fields")
            elif signup_password != signup_password_confirm:
                st.error("Passwords don't match")
            elif len(signup_password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                if db.create_user(signup_username, signup_password):
                    st.success("Account created! Please login.")
                else:
                    st.error("Username already exists")
    
    st.stop()

# Main App (only shown when logged in)
st.title(f"💰 Personal Finance Dashboard")
st.markdown(f"Welcome back, **{st.session_state.username}**!")

# Logout button in sidebar
with st.sidebar:
    if st.button("Logout", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()
    
    st.divider()
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
            db.add_transaction(
                st.session_state.user_id,
                trans_date,
                trans_type,
                category,
                amount,
                description
            )
            st.success("Transaction added!")
            st.rerun()
        else:
            st.error("Please enter a valid amount")
    
    # Clear all data button
    st.divider()
    if st.button("Clear All Data"):
        db.clear_all_transactions(st.session_state.user_id)
        st.success("All transactions cleared!")
        st.rerun()

# Load transactions from database
df = db.get_transactions(st.session_state.user_id)

# Main content area
if len(df) == 0:
    st.info("👆 Start by adding your first transaction in the sidebar!")
    
    # Show sample data option
    if st.button("Load Sample Data"):
        sample_data = [
            (date(2024, 1, 1), "Income", "Salary", 5000, "Monthly salary"),
            (date(2024, 1, 5), "Expense", "Food", 150, "Groceries"),
            (date(2024, 1, 7), "Expense", "Transportation", 80, "Gas"),
            (date(2024, 1, 10), "Expense", "Entertainment", 120, "Movie and dinner"),
            (date(2024, 1, 12), "Expense", "Bills", 200, "Electricity"),
            (date(2024, 1, 15), "Income", "Freelance", 800, "Web design project"),
            (date(2024, 1, 18), "Expense", "Shopping", 250, "Clothes"),
            (date(2024, 1, 20), "Expense", "Food", 200, "Restaurant"),
        ]
        for trans in sample_data:
            db.add_transaction(st.session_state.user_id, *trans)
        st.rerun()
else:
    # Calculate key metrics
    total_income = df[df['type'] == 'Income']['amount'].sum()
    total_expenses = df[df['type'] == 'Expense']['amount'].sum()
    net_savings = total_income - total_expenses
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Income", f"${total_income:,.2f}")
    
    with col2:
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    
    with col3:
        st.metric("Net Savings", f"${net_savings:,.2f}", 
                 delta=f"{(net_savings/total_income*100):.1f}%" if total_income > 0 else "0%")
    
    with col4:
        st.metric("Transactions", len(df))
    
    st.divider()
    
    # Create two columns for charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Expenses by Category")
        expenses_df = df[df['type'] == 'Expense']
        if len(expenses_df) > 0:
            category_totals = expenses_df.groupby('category')['amount'].sum().reset_index()
            fig_pie = px.pie(category_totals, values='amount', names='category',
                            color_discrete_sequence=px.colors.qualitative.Set3)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No expenses recorded yet")
    
    with col2:
        st.subheader("Income vs Expenses")
        type_totals = df.groupby('type')['amount'].sum().reset_index()
        fig_bar = px.bar(type_totals, x='type', y='amount',
                        color='type',
                        color_discrete_map={'Income': '#2ecc71', 'Expense': '#e74c3c'})
        fig_bar.update_layout(showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Spending trend over time
    st.subheader("Spending Trend Over Time")
    df['date'] = pd.to_datetime(df['date'])
    df_sorted = df.sort_values('date')
    
    income_df = df_sorted[df_sorted['type'] == 'Income'].copy()
    expense_df = df_sorted[df_sorted['type'] == 'Expense'].copy()
    
    fig_line = go.Figure()
    
    if len(income_df) > 0:
        fig_line.add_trace(go.Scatter(x=income_df['date'], y=income_df['amount'],
                                     mode='lines+markers', name='Income',
                                     line=dict(color='#2ecc71', width=3)))
    
    if len(expense_df) > 0:
        fig_line.add_trace(go.Scatter(x=expense_df['date'], y=expense_df['amount'],
                                     mode='lines+markers', name='Expenses',
                                     line=dict(color='#e74c3c', width=3)))
    
    fig_line.update_layout(xaxis_title="Date", yaxis_title="Amount ($)",
                          hovermode='x unified')
    st.plotly_chart(fig_line, use_container_width=True)
    
    # Transaction history table
    st.subheader("Transaction History")
    
    # Add filters
    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        filter_type = st.multiselect("Filter by Type", 
                                    options=df['type'].unique(),
                                    default=df['type'].unique())
    with filter_col2:
        filter_category = st.multiselect("Filter by Category",
                                        options=df['category'].unique(),
                                        default=df['category'].unique())
    
    # Apply filters
    filtered_df = df[
        (df['type'].isin(filter_type)) & 
        (df['category'].isin(filter_category))
    ].copy()
    
    # Display filtered dataframe with delete option
    for idx, row in filtered_df.iterrows():
        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 3, 1])
        col1.write(row['date'].strftime('%Y-%m-%d'))
        col2.write(row['type'])
        col3.write(row['category'])
        col4.write(f"${row['amount']:,.2f}")
        col5.write(row['description'])
        if col6.button("🗑️", key=f"del_{row['id']}"):
            db.delete_transaction(row['id'], st.session_state.user_id)
            st.rerun()
    
    # Download data as CSV
    st.divider()
    csv = df.to_csv(index=False)
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name=f"finance_data_{st.session_state.username}.csv",
        mime="text/csv"
    )