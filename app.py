import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Load the files
def load_data():
    # You can upload files manually or read directly from GitHub repository
    bridgerpay_file = st.file_uploader("Upload BridgerPay Transactions Report", type=["csv"])
    backend_file = st.file_uploader("Upload Backend API Order List", type=["csv"])
    
    if bridgerpay_file and backend_file:
        bridgerpay_df = pd.read_csv(bridgerpay_file)
        backend_df = pd.read_csv(backend_file)
        return bridgerpay_df, backend_df
    return None, None

# Convert Backend API timestamps to GMT+6, ensuring they are in datetime format
def localize_backend_timestamps(df):
    # Ensure 'Created At' and 'Updated At' columns are in datetime format
    df['Created At'] = pd.to_datetime(df['Created At'], errors='coerce')  # Ensure it's in datetime
    df['Updated At'] = pd.to_datetime(df['Updated At'], errors='coerce')  # Ensure it's in datetime

    # Now check if the datetime objects are naive and localize to Asia/Dhaka (GMT+6)
    if df['Created At'].dt.tz is None:
        df['Created At'] = df['Created At'].dt.tz_localize('Asia/Dhaka')
    if df['Updated At'].dt.tz is None:
        df['Updated At'] = df['Updated At'].dt.tz_localize('Asia/Dhaka')
    
    return df

# Convert BridgerPay timestamps
def localize_bridgerpay_timestamps(df):
    # Ensure 'processing_date' and 'completionDate' are in datetime format
    df['processing_date'] = pd.to_datetime(df['processing_date'], errors='coerce')
    df['completionDate'] = pd.to_datetime(df['completionDate'], errors='coerce')
    
    # Now check if the datetime objects are naive and localize to Asia/Dhaka (GMT+6)
    if df['processing_date'].dt.tz is None:
        df['processing_date'] = df['processing_date'].dt.tz_localize('Asia/Dhaka')
    if df['completionDate'].dt.tz is None:
        df['completionDate'] = df['completionDate'].dt.tz_localize('Asia/Dhaka')
    
    return df

# Reconciliation Logic - Check for column names and clean them
def reconcile(bridgerpay_df, backend_df):
    # Clean column names (remove leading/trailing spaces)
    bridgerpay_df.columns = bridgerpay_df.columns.str.strip()
    backend_df.columns = backend_df.columns.str.strip()

    # Verify that required columns are in the backend API file
    required_columns_backend = ['BP ID', 'Total', 'Status', 'Created At']
    missing_columns = [col for col in required_columns_backend if col not in backend_df.columns]

    if missing_columns:
        st.error(f"Missing columns in Backend API data: {', '.join(missing_columns)}")
        return None, None

    # Localize timestamps to GMT+6
    backend_df = localize_backend_timestamps(backend_df)
    bridgerpay_df = localize_bridgerpay_timestamps(bridgerpay_df)

    # Merge the data on merchantOrderId (BP ID) and amount
    reconciled_df = pd.merge(
        bridgerpay_df[['merchantOrderId', 'amount', 'pspName', 'completionDate']],  # BridgerPay columns
        backend_df[['BP ID', 'Total', 'Status', 'Created At']],  # Backend API columns
        left_on='merchantOrderId', right_on='BP ID', how='outer', suffixes=('_bridgerpay', '_backend')
    )

    # Find discrepancies in amount
    discrepancies = reconciled_df[reconciled_df['amount'] != reconciled_df['Total']]
    return reconciled_df, discrepancies

# Plotting the Discrepancies
def plot_discrepancies(discrepancies):
    if not discrepancies.empty:
        fig, ax = plt.subplots()
        discrepancies['amount'].plot(kind='bar', ax=ax, color='red', label='Amount Discrepancies')
        ax.set_title("Reconciliation Discrepancies")
        ax.set_xlabel('Transaction Index')
        ax.set_ylabel('Amount')
        ax.legend()
        st.pyplot(fig)
    else:
        st.write("No discrepancies found.")

# Streamlit App Layout
def main():
    st.title("Orchestrator to Backend API Reconciliation Dashboard")
    
    bridgerpay_df, backend_df = load_data()
    
    if bridgerpay_df is not None and backend_df is not None:
        reconciled_df, discrepancies = reconcile(bridgerpay_df, backend_df)
        
        # Display Reconciled Data
        st.subheader("Reconciled Data")
        st.dataframe(reconciled_df)
        
        # Display Discrepancies
        st.subheader("Discrepancies in Reconciliation")
        st.dataframe(discrepancies)
        
        # Plot the discrepancies
        plot_discrepancies(discrepancies)
    else:
        st.write("Please upload both BridgerPay and Backend API files.")
    
if __name__ == "__main__":
    main()
