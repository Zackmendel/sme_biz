# sales.py
import os
import streamlit as st
import pandas as pd
from supabase import Client, create_client
from dotenv import load_dotenv

load_dotenv()

business_uuid = os.getenv("BUSINESS_ID")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# ----------------------------------------------------------------
# Database Functions
# ----------------------------------------------------------------

def get_sales_table():
    try:
        response = supabase.table('sales').select('*').eq("business_id", business_uuid).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching sales data: {e}")
        return []

def get_product_list():
    try:
        response = supabase.table("products").select("*").eq("business_id", business_uuid).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching product details: {e}")
        return []

def enter_sales(sales_payloads):
    try:
        response = supabase.table("sales").insert(sales_payloads).execute()
        return response.data
    except Exception as e:
        st.error(f"Error adding sales data: {e}")
        return None



# ----------------------------------------------------------------
# Main UI Presentation Function
# ----------------------------------------------------------------
def show_sales_management_ui():
    # Fetch underlying reference data inside the view context
    products_data = get_product_list()
    df_products = pd.DataFrame(products_data)

    if not df_products.empty:
        product_lookup = df_products.set_index('name')[['id', 'default_price']].to_dict(orient='index')
        product_options = list(product_lookup.keys())
    else:
        product_lookup = {}
        product_options = []

    if "sale_items" not in st.session_state:
        st.session_state.sale_items = []

    st.title("Sales Management")

    # Setup layout columns: Left for Form, Right for the active Cart
    form_col, cart_col = st.columns([3, 2], gap="large")

    with form_col:
        st.subheader("Add Sale Records")
        customer_details = st.text_input("Customer Details/Name", placeholder="John Doe")
        st.markdown("### Item Selector")
        col_1, col_2, col_3 = st.columns([2, 1, 1])
        
        with col_1:
            selected_name = st.selectbox("Select Product", options=product_options)
        
        default_price = product_lookup.get(selected_name, {}).get('default_price', 0.0) if selected_name else 0.0
        
        with col_2:
            price_per_unit = st.number_input("Price per Unit", min_value=0.0, value=float(default_price), step=0.5)
            
        with col_3:
            quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
        
        if st.button("➕ Add Item to Sale"):
            if selected_name:
                item_id = product_lookup[selected_name]['id']
                row_total = price_per_unit * quantity
                
                st.session_state.sale_items.append({
                    "product_id": item_id,
                    "item_name": selected_name,
                    "price_per_unit": price_per_unit,
                    "quantity": quantity,
                    "total": row_total
                })
                st.rerun()
            else:
                st.warning("Please select a valid product first.")

    with cart_col:
        st.subheader("Current Order Summary")
        
        if st.session_state.sale_items:
            df_cart = pd.DataFrame(st.session_state.sale_items)
            st.dataframe(df_cart[["item_name", "price_per_unit", "quantity", "total"]], width='stretch')
            
            subtotal = df_cart["total"].sum()
            
            if st.button("Clear Items"):
                st.session_state.sale_items = []
                st.rerun()
                
            st.divider()
            
            st.metric("Subtotal", f"₦{subtotal:,.2f}")
            discount = st.number_input("Apply Global Discount (₦)", min_value=0.0, max_value=float(subtotal), value=0.0, step=1.0)
            final_total = max(0.0, subtotal - discount)
            st.metric("Grand Total Due", f"₦{final_total:,.2f}")
            
            if st.button("🚀 Finalize & Submit Sale", type="primary"):
                if not customer_details.strip():
                    st.error("Please enter Customer Details before finalizing.")
                else:
                    sales_payloads = []
                    for item in st.session_state.sale_items:
                        allocated_discount = discount if len(sales_payloads) == 0 else 0.0

                        payload = {
                            "business_id": business_uuid,
                            "user_id": st.session_state.user_id, # ✅ Extracted seamlessly from global state!
                            "product_id": item["product_id"],
                            "item_name": item["item_name"],
                            "customer_details": customer_details,
                            "quantity": item["quantity"],
                            "price_per_unit": item["price_per_unit"],
                            "discount": allocated_discount,
                        }
                        sales_payloads.append(payload)
                    
                    success = enter_sales(sales_payloads)
                    if success:
                        st.success(f"Successfully saved sale with {len(sales_payloads)} items!")
                        st.session_state.sale_items = []
                        st.rerun()
        else:
            st.info("No items added to the current sale yet. Use the left panel to build the invoice.")

    st.divider()
    st.subheader("Historical Sales Database Log")
    sales_log_data = get_sales_table()
    if sales_log_data:
        st.dataframe(pd.DataFrame(sales_log_data), width='stretch')
    else:
        st.info("No historical sales records found for this business UUID context.")