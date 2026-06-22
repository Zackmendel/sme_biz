# purchases.py
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

def get_purchases_table():
    try:
        active_biz = st.session_state.get("user_business_id") or business_uuid
        response = supabase.table('purchases').select('*').eq("business_id", active_biz).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching purchases data: {e}")
        return []

def enter_purchases(purchases_payloads):
    try:
        response = supabase.table("purchases").insert(purchases_payloads).execute()
        return response.data
    except Exception as e:
        st.error(f"Error adding purchases data: {e}")
        return None


# ----------------------------------------------------------------
# Main UI Presentation Function
# ----------------------------------------------------------------
def show_purchases_management_ui():
    if "purchases_items" not in st.session_state:
        st.session_state.purchases_items = []

    st.title("Purchases Management")

    # Setup layout columns: Left for Form, Right for the active Cart
    form_col, cart_col = st.columns([3, 2], gap="large")

    with form_col:
        st.subheader("Add Purchases Records")
        supplier_name = st.text_input("Supplier Name", placeholder="Acme Corp")
        st.markdown("### Item Selector")
        col_1, col_2, col_3 = st.columns([2, 1, 1])
        
        with col_1:
            selected_name = st.text_input("Enter Product Name", placeholder="Eg: A4 Paper", value="")
        
        with col_2:
            quantity = st.number_input("Quantity", min_value=1, value=1, step=1)
        
        with col_3:
            total_cost = st.number_input("Total Cost (₦)", min_value=0.0, step=50.0)
        
        if st.button("➕ Add Item to Purchase"):
            if selected_name.strip():
                st.session_state.purchases_items.append({
                    "product_id": None,
                    "item_name": selected_name.strip(),
                    "price_per_unit": total_cost / quantity if quantity > 0 else 0.0,
                    "quantity": quantity,
                    "total": total_cost
                })
                st.rerun()
            else:
                st.warning("Please enter a valid product name first.")

    with cart_col:
        st.subheader("Current Order Summary")
        
        if st.session_state.purchases_items:
            df_cart = pd.DataFrame(st.session_state.purchases_items)
            st.dataframe(df_cart[["item_name", "price_per_unit", "quantity", "total"]], width='stretch')
            
            subtotal = df_cart["total"].sum()
            
            if st.button("Clear Items"):
                st.session_state.purchases_items = []
                st.rerun()
                
            st.divider()
            
            st.metric("Grand Total Due", f"₦{subtotal:,.2f}")
            
            if st.button("🚀 Finalize & Submit Purchase", type="primary"):
                active_biz = st.session_state.get("user_business_id") or business_uuid
                purchases_payloads = []
                for item in st.session_state.purchases_items:
                    payload = {
                        "business_id": active_biz,
                        "user_id": st.session_state.user_id, # ✅ Extracted seamlessly from global state!
                        "product_id": None,
                        "item_name": item["item_name"],
                        "vendor_details": supplier_name.strip() if supplier_name.strip() else None,
                        "quantity": item["quantity"],
                        "price_per_unit": item["price_per_unit"]
                    }
                    purchases_payloads.append(payload)
                
                success = enter_purchases(purchases_payloads)
                if success:
                    st.success(f"Successfully saved purchase with {len(purchases_payloads)} items!")
                    st.session_state.purchases_items = []
                    st.rerun()
        else:
            st.info("No items added to the current purchase yet. Use the left panel to build the invoice.")

    st.divider()
    st.subheader("Historical Purchases Database Log")
    purchases_log_data = get_purchases_table()
    if purchases_log_data:
        st.dataframe(pd.DataFrame(purchases_log_data), width='stretch')
    else:
        st.info("No historical purchases records found for this business UUID context.")