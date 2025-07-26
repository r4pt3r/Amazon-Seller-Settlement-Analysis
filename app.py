import streamlit as st
import pandas as pd
import io

# Page configuration
st.set_page_config(
    page_title="Amazon Settlement Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Amazon Settlement Electronic Analysis")
st.markdown("---")

# Initialize session state
if 'settlement_data' not in st.session_state:
    st.session_state.settlement_data = None
if 'order_summary' not in st.session_state:
    st.session_state.order_summary = None
if 'cogs_uploaded' not in st.session_state:
    st.session_state.cogs_uploaded = False

# Step 1: Upload Settlement File
st.header("Step 1: Upload Settlement File")
uploaded_file = st.file_uploader(
    "Choose a settlement TXT file", 
    type=['txt'],
    help="Upload your Amazon settlement electronic report file"
)

if uploaded_file is not None:
    try:
        # Read the uploaded file
        df = pd.read_csv(uploaded_file, sep='\t')
        st.session_state.settlement_data = df
        
        st.success(f"✅ File uploaded successfully! {len(df)} rows loaded.")
        
        # Show data preview
        with st.expander("📋 Data Preview"):
            st.dataframe(df.head(10))
        
        # Step 2: Extract Key Information
        st.header("Step 2: Settlement Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📅 Settlement Details")
            settlement_start_date = df['settlement-start-date'].iloc[0]
            settlement_end_date = df['settlement-end-date'].iloc[0]
            deposit_date = df['deposit-date'].iloc[0]
            amount_transferred = df['total-amount'].iloc[0]
            
            st.write(f"**Settlement Start Date:** {settlement_start_date}")
            st.write(f"**Settlement End Date:** {settlement_end_date}")
            st.write(f"**Deposit Date:** {deposit_date}")
            st.write(f"**Amount Transferred:** ₹{amount_transferred:,.2f}")
        
        with col2:
            st.subheader("💰 Financial Summary")
            
            # Get opening and closing balance
            opening_balance = df[df['amount-description'] == 'Previous Reserve Amount Balance']['amount'].iloc[0]
            closing_balance = df[df['amount-description'] == 'Current Reserve Amount']['amount'].iloc[0]
            
            # Calculate fees and sales
            total_aba_amount = df[df['amount-type'] == 'Amazon Business Advisory Fee']['amount'].sum()
            total_ads_amount = df[df['amount-type'] == 'Cost of Advertising']['amount'].sum()
            total_sales = df[df['transaction-type'] == 'Order']['amount'].sum()
            
            st.write(f"**Opening Balance:** ₹{opening_balance:,.2f}")
            st.write(f"**Closing Balance:** ₹{closing_balance:,.2f}")
            st.write(f"**Total ABA Charged:** ₹{abs(total_aba_amount):,.2f}")
            st.write(f"**Total ADS Charged:** ₹{abs(total_ads_amount):,.2f}")
            st.write(f"**Total Sales:** ₹{total_sales:,.2f}")
        
        # Step 3: Generate COGS Template
        st.header("Step 3: Generate COGS Template")
        
        # Create order summary with improved calculation
        ORDER = df[df['transaction-type'] == 'Order']
        
        # Step 1: Group by order-id and sku, sum the amounts
        ORDER_SUMMARY = ORDER.groupby(['order-id', 'sku'])['amount'].sum().reset_index(name='total_amount')
        
        # Step 2: Get actual quantities from Principal rows (sum the quantity-purchased field)
        PRINCIPAL_QUANTITIES = ORDER[ORDER['amount-description'] == 'Principal'].groupby(['order-id', 'sku'])['quantity-purchased'].sum().reset_index(name='quantity_ordered')
        
        # Step 3: Merge settlement amounts with actual quantities
        ORDER_SUMMARY = pd.merge(ORDER_SUMMARY, PRINCIPAL_QUANTITIES, on=['order-id', 'sku'], how='left')
        
        # Step 4: Handle cases where no Principal row exists (fill with 0)
        ORDER_SUMMARY['quantity_ordered'] = ORDER_SUMMARY['quantity_ordered'].fillna(0)
        
        # Step 5: Add additional fields from the original data
        ORDER_SUMMARY = pd.merge(ORDER_SUMMARY,
                                ORDER[['order-id', 'sku', 'settlement-id', 'marketplace-name', 'posted-date']].drop_duplicates(),
                                on=['order-id', 'sku'],
                                how='left')
        
        # Round amounts for better readability
        ORDER_SUMMARY['total_amount'] = ORDER_SUMMARY['total_amount'].round(2)
        
        # Sort by order-id and sku
        ORDER_SUMMARY = ORDER_SUMMARY.sort_values(['order-id', 'sku']).reset_index(drop=True)
        
        st.session_state.order_summary = ORDER_SUMMARY
        
        # Generate COGS template
        unique_skus = ORDER_SUMMARY['sku'].unique()
        sku_df = pd.DataFrame(unique_skus, columns=['SKU'])
        sku_df['COGS'] = ''
        
        st.write(f"📦 Found **{len(unique_skus)}** unique SKUs")
        
        # Download COGS template
        cogs_buffer = io.BytesIO()
        with pd.ExcelWriter(cogs_buffer, engine='openpyxl') as writer:
            sku_df.to_excel(writer, index=False, sheet_name='COGS')
        
        st.download_button(
            label="📥 Download COGS Template",
            data=cogs_buffer.getvalue(),
            file_name="COGS_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Step 4: Download Order Summary (without COGS)
        st.header("Step 4: Order Summary (Preliminary)")
        
        st.write(f"📋 **{len(ORDER_SUMMARY)}** order-SKU combinations processed")
        st.write(f"📦 **{ORDER_SUMMARY['sku'].nunique()}** unique SKUs")
        st.write(f"🛒 **{ORDER_SUMMARY['order-id'].nunique()}** unique orders")
        
        with st.expander("👁️ Preview Order Summary"):
            st.dataframe(ORDER_SUMMARY)
        
        # Download preliminary order summary
        order_buffer = io.BytesIO()
        with pd.ExcelWriter(order_buffer, engine='openpyxl') as writer:
            ORDER_SUMMARY.to_excel(writer, index=False, sheet_name='Order_Summary')
        
        st.download_button(
            label="📥 Download Preliminary Order Summary",
            data=order_buffer.getvalue(),
            file_name="Order_Summary_Preliminary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")

# Step 5: Upload COGS File
st.header("Step 5: Upload Completed COGS File")
st.info("💡 Please fill in the COGS values in the downloaded template and upload it back here.")

cogs_file = st.file_uploader(
    "Upload completed COGS Excel file",
    type=['xlsx', 'xls'],
    help="Upload the COGS file with filled cost values"
)

if cogs_file is not None and st.session_state.order_summary is not None:
    try:
        # Read COGS file
        cogs_df = pd.read_excel(cogs_file)
        
        # Validate COGS file
        if 'SKU' not in cogs_df.columns or 'COGS' not in cogs_df.columns:
            st.error("❌ Invalid COGS file format. Please ensure it has 'SKU' and 'COGS' columns.")
        else:
            st.success("✅ COGS file uploaded successfully!")
            st.session_state.cogs_uploaded = True
            
            # Merge COGS with Order Summary
            ORDER_SUMMARY_WITH_COGS = pd.merge(
                st.session_state.order_summary, 
                cogs_df[['SKU', 'COGS']], 
                left_on='sku', 
                right_on='SKU', 
                how='left'
            )
            ORDER_SUMMARY_WITH_COGS = ORDER_SUMMARY_WITH_COGS.drop(columns=['SKU'])
            
            # Calculate profit using the correct column names
            ORDER_SUMMARY_WITH_COGS['profit'] = (
                ORDER_SUMMARY_WITH_COGS['total_amount'] - 
                (ORDER_SUMMARY_WITH_COGS['COGS'] * ORDER_SUMMARY_WITH_COGS['quantity_ordered'])
            )
            
            # Step 6: Final Report
            st.header("Step 6: Final Order P&L Report")
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_revenue = ORDER_SUMMARY_WITH_COGS['total_amount'].sum()
                st.metric("💰 Total Revenue", f"₹{total_revenue:,.2f}")
            
            with col2:
                total_cogs = (ORDER_SUMMARY_WITH_COGS['COGS'] * ORDER_SUMMARY_WITH_COGS['quantity_ordered']).sum()
                st.metric("📦 Total COGS", f"₹{total_cogs:,.2f}")
            
            with col3:
                total_profit = ORDER_SUMMARY_WITH_COGS['profit'].sum()
                st.metric("💵 Total Profit", f"₹{total_profit:,.2f}")
            
            with col4:
                profit_margin = (total_profit / total_revenue) * 100 if total_revenue > 0 else 0
                st.metric("📈 Profit Margin", f"{profit_margin:.1f}%")
            
            # Show final report
            with st.expander("📊 Complete Order P&L Report"):
                st.dataframe(ORDER_SUMMARY_WITH_COGS)
            
            # Top/Bottom performers
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏆 Top 5 Profitable Orders")
                top_orders = ORDER_SUMMARY_WITH_COGS.nlargest(5, 'profit')[['order-id', 'sku', 'total_amount', 'quantity_ordered', 'profit']]
                st.dataframe(top_orders)
            
            with col2:
                st.subheader("⚠️ Bottom 5 Profitable Orders")
                bottom_orders = ORDER_SUMMARY_WITH_COGS.nsmallest(5, 'profit')[['order-id', 'sku', 'total_amount', 'quantity_ordered', 'profit']]
                st.dataframe(bottom_orders)
            
            # Download final report
            final_buffer = io.BytesIO()
            with pd.ExcelWriter(final_buffer, engine='openpyxl') as writer:
                ORDER_SUMMARY_WITH_COGS.to_excel(writer, index=False, sheet_name='Order_PNL')
            
            st.download_button(
                label="📥 Download Final Order P&L Report",
                data=final_buffer.getvalue(),
                file_name="Order_PNL_Final_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
    except Exception as e:
        st.error(f"❌ Error processing COGS file: {str(e)}")

# Instructions
with st.sidebar:
    st.header("📋 Instructions")
    st.markdown("""
    ### How to use this app:
    
    1. **Upload Settlement File**: Upload your Amazon settlement .txt file
    
    2. **Review Summary**: Check the extracted settlement information
    
    3. **Download COGS Template**: Download the Excel template with all unique SKUs
    
    4. **Fill COGS Values**: Open the downloaded template and fill in the cost values for each SKU
    
    5. **Upload Completed COGS**: Upload the completed COGS file back to the app
    
    6. **Download Final Report**: Get your complete Order P&L analysis
    
    ### File Format Requirements:
    - Settlement file: Tab-delimited .txt file
    - COGS file: Excel file with 'SKU' and 'COGS' columns
    """)
    
    st.markdown("---")
    # Add navigation section
    st.header("🔗 Navigation")
    st.page_link("pages/label.py", label="📊 Label Analysis", icon="📊")
    # Add more page links as needed
    
    st.markdown("---")
    st.markdown("**💡 Tips:**")
    st.markdown("- Ensure your COGS values are numeric")
    st.markdown("- Double-check SKU matching")
    st.markdown("- Review profit margins for accuracy")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ using Streamlit")