
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

# Reconciliation Logic
def reconcile(bridgerpay_df, backend_df):
    # Convert Backend API timestamps to GMT+6
    backend_df['Created At'] = pd.to_datetime(backend_df['Created At']).dt.tz_convert('Asia/Dhaka')
    backend_df['Updated At'] = pd.to_datetime(backend_df['Updated At']).dt.tz_convert('Asia/Dhaka')

    # Merge the data on transactionId and amount
    reconciled_df = pd.merge(bridgerpay_df[['transactionId', 'amount', 'pspName', 'completionDate']],
                             backend_df[['Transaction ID', 'Total', 'Status', 'Created At']], 
                             left_on='transactionId', right_on='Transaction ID', how='outer', suffixes=('_bridgerpay', '_backend'))

    # Find discrepancies
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
