# products.py
import os
import streamlit as st
import pandas as pd
from supabase import Client, create_client
from dotenv import load_dotenv

load_dotenv()

# Safely track company scope parameters
business_uuid = os.getenv("BUSINESS_ID")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# ----------------------------------------------------------------
# Database Operations
# ----------------------------------------------------------------

def get_products_table(show_archived=False):
    """Fetches product profiles matching the active business context."""
    try:
        current_biz = st.session_state.get("user_business_id") or business_uuid
        response = (
            supabase.table('products')
            .select('*')
            .eq("business_id", current_biz)
            .eq("is_archived", show_archived)
            .execute()
        )
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching products data: {e}")
        return []

def enter_product(product_payload):
    """Inserts a single new product profile into the backend schema."""
    try:
        response = supabase.table("products").insert(product_payload).execute()
        return response.data
    except Exception as e:
        st.error(f"Error saving product profile: {e}")
        return None

def update_product(product_id, updated_payload):
    """Updates or archives an existing product record matching the profile ID."""
    try:
        response = supabase.table("products").update(updated_payload).eq("id", product_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error updating product profile: {e}")
        return None

def delete_product_permanently(product_id):
    """Permanently purges a record from the database table."""
    try:
        response = supabase.table("products").delete().eq("id", product_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error hard-deleting product: {e}")
        return None

# ----------------------------------------------------------------
# Main UI Interface Presentation
# ----------------------------------------------------------------
def show_products_management_ui():
    st.title("📦 Product Catalog Management")
    st.write("Select an operation from the control bar to modify, add, or clear catalog lines.")
    
    # Fetch active live records 
    raw_catalog = get_products_table(show_archived=False)
    df_catalog = pd.DataFrame(raw_catalog)

    # ------------------------------------------------------------
    # UNIFIED SINGLE-ROW MANAGEMENT CONTROLS
    # ------------------------------------------------------------
    
    # Render an interactive horizontal control pill row
    action_menu = st.pills(
        label="Select Workspace Action:",
        options=["📊 View Only", "➕ Add Products", "📝 Edit/Archive", "🗄️ Manage Archive"],
        default="📊 View Only",
        selection_mode="single"
    )
    
    st.divider()

    # ------------------------------------------------------------
    # DYNAMIC EXPANSION DRAWER ROUTING (Opens beneath the row menu)
    # ------------------------------------------------------------
    
    # Mode A: Continuous Add Workbench
    if action_menu == "➕ Add Products":
        st.subheader("Add New Products (Multi-Entry Mode)")
        with st.form("multi_add_form", clear_on_submit=True):
            st.info("💡 This view stays active so you can log multiple rows without switching screens.")
            p_name = st.text_input("Product Name *", placeholder="e.g., Fresh Milk (50cl)")
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                p_price = st.number_input("Default Price (₦) *", min_value=0.0, value=0.0, step=50.0)
            with col_b:
                p_unit = st.text_input("Measurement Unit", placeholder="e.g., bottle, pcs")
            with col_c:
                p_category = st.text_input("Category", placeholder="e.g., Dairy, Beverages")
            
            if st.form_submit_button("✨ Save & Add Next Product", type="primary"):
                if not p_name.strip() or p_price <= 0:
                    st.error("Please provide a valid product name and retail price.")
                else:
                    active_biz = st.session_state.get("user_business_id") or business_uuid
                    payload = {
                        "business_id": active_biz,
                        "name": p_name.strip(),
                        "default_price": p_price,
                        "unit": p_unit.strip() if p_unit.strip() else None,
                        "category": p_category.strip() if p_category.strip() else None,
                        "is_archived": False
                    }
                    if enter_product(payload):
                        st.success(f"Saved '{p_name.strip()}' successfully! Enter your next product below.")
                        st.rerun()
        st.divider()

    # Mode B: Update & Modify Workbench
    elif action_menu == "📝 Edit/Archive":
        st.subheader("Edit / Archive Existing Products")
        if df_catalog.empty:
            st.info("No active profiles available to edit.")
        else:
            product_list = {f"{row['name']} (₦{row['default_price']:,.2f})": row for _, row in df_catalog.iterrows()}
            selected_label = st.selectbox("Select product to modify:", options=list(product_list.keys()))
            selected_product = product_list[selected_label]
            
            with st.form("persistent_edit_form"):
                edit_name = st.text_input("Product Name", value=selected_product.get("name") or "")
                
                col_e1, col_e2, col_e3 = st.columns(3)
                with col_e1:
                    edit_price = st.number_input("Price (₦)", min_value=0.0, value=float(selected_product.get("default_price", 0.0)), step=50.0)
                with col_e2:
                    edit_category = st.text_input("Category", value=selected_product.get("category") or "")
                with col_e3:
                    edit_unit = st.text_input("Unit", value=selected_product.get("unit") or "")
                    
                is_archived = st.toggle("Archive this product", value=False)
                
                if st.form_submit_button("💾 Save Profile Changes", type="secondary"):
                    if not edit_name.strip():
                        st.error("Product name cannot be blank.")
                    else:
                        payload = {
                            "name": edit_name.strip(),
                            "default_price": edit_price,
                            "category": edit_category.strip() if edit_category.strip() else None,
                            "unit": edit_unit.strip() if edit_unit.strip() else None,
                            "is_archived": is_archived
                        }
                        if update_product(selected_product["id"], payload):
                            st.success("Changes saved successfully!")
                            st.rerun()
        st.divider()

    # Mode C: Archive Purge / Recovery Controls
    elif action_menu == "🗄️ Manage Archive":
        st.subheader("Archived Products Recovery Laboratory")
        archived_data = get_products_table(show_archived=True)
        if not archived_data:
            st.info("The archive repository is empty.")
        else:
            df_archived = pd.DataFrame(archived_data)
            st.dataframe(df_archived[["name", "category", "default_price"]].rename(
                columns={"name": "Product Name", "category": "Category", "default_price": "Price"}
            ), width='stretch', hide_index=True)
            
            st.divider()
            archive_lookup = {f"{row['name']} [{row['category'] or 'N/A'}]": row for _, row in df_archived.iterrows()}
            
            action_type = st.radio("Choose Action Mode:", ["Restore / Unarchive", "Permanently Delete"], horizontal=True)
            target_label = st.selectbox("Select target archived item:", options=list(archive_lookup.keys()))
            target_id = archive_lookup[target_label]["id"]

            if action_type == "Restore / Unarchive":
                if st.button("🔓 Restore Selected Product", type="secondary"):
                    if update_product(target_id, {"is_archived": False}):
                        st.success("Product restored successfully!")
                        st.rerun()
            else:
                confirm = st.checkbox(f"Confirm you want to delete '{target_label}' forever.")
                if st.button("🚨 PERMANENTLY PURGE RECORD", type="primary"):
                    if confirm:
                        if delete_product_permanently(target_id):
                            st.success("Record permanently deleted.")
                            st.rerun()
                    else:
                        st.warning("Please check the confirmation box first.")
        st.divider()

    # ------------------------------------------------------------
    # MAIN DISPLAY: THE ACTIVE INVENTORY CATALOG TABLE
    # ------------------------------------------------------------
    st.subheader("Active Live Inventory Rows")
    if not df_catalog.empty:
        display_cols = []
        rename_mapping = {}
        column_check = {
            "name": "Product Name",
            "category": "Category",
            "default_price": "Default Price (₦)",
            "unit": "Unit"
        }
        
        for col_key, col_label in column_check.items():
            if col_key in df_catalog.columns:
                display_cols.append(col_key)
                rename_mapping[col_key] = col_label
            
        df_view = df_catalog[display_cols].rename(columns=rename_mapping)
        st.dataframe(df_view, width='stretch', hide_index=True)
    else:
        st.info("No active items registered. Select '➕ Add Products' above to start building your catalog.")