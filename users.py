# users.py
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def get_all_users():
    try:
        # Dynamic safe fallback: Use the active session business scope context
        current_biz = st.session_state.get("user_business_id") or os.getenv("BUSINESS_ID")
        
        response = supabase.table("users").select("*, businesses(name)").eq("business_id", current_biz).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching user details: {e}")
        return []

def edit_user(user_id, user_details):
    try:
        response = supabase.table("users").update(user_details).eq("id", user_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error editing user: {e}")
        return None

# --- PACK ALL UI INTO THIS FUNCTION ---
def show_user_management_ui():
    users_data = get_all_users()

    if users_data:
        df = pd.DataFrame(users_data)
        st.subheader("Current Database State")
        st.dataframe(df)
        
        st.divider()
        st.subheader("Edit User Flow")
        
        user_list = {f"{u.get('email')} ({u.get('id')[:8]}...)": u for u in users_data}
        selected_user_label = st.selectbox("Select user to modify", options=list(user_list.keys()))
        
        selected_user = user_list[selected_user_label]
        user_id = selected_user["id"]
        
        business_id = st.text_input("Business ID", value=selected_user.get("business_id") or "")
        email = st.text_input("Email", value=selected_user.get("email") or "")
        first_name = st.text_input("First Name", value=selected_user.get("first_name") or "")
        last_name = st.text_input("Last Name", value=selected_user.get("last_name") or "")
        
        # 1. Handle the Status Selectbox safely
        status_options = ["permanent", "part_time", "intern", "contract"]
        current_status = selected_user.get("status")

        # Fallback to "permanent" (or whatever you want your default to be) if it's None or not in the list
        if current_status not in status_options:
            status_default_index = 0  # Points to "permanent"
        else:
            status_default_index = status_options.index(current_status)

        status = st.selectbox("Status", options=status_options, index=status_default_index)


        # 2. Handle the Role Selectbox safely (Apply the same logic here to prevent future crashes!)
        role_options = ["admin", "staff", "viewer"]
        current_role = selected_user.get("role")

        if current_role not in role_options:
            role_default_index = 2  # Points to "viewer"
        else:
            role_default_index = role_options.index(current_role)

        role = st.selectbox("Role", options=role_options, index=role_default_index)
        
        is_active_initial = bool(selected_user.get("is_active", True))
        is_active = st.toggle("Is Active User", value=is_active_initial)

        if st.button("Update User Profile", type="primary"):
            updated_payload = {
                "business_id": business_id if business_id else None,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "role": role,
                "status": status,
                "is_active": is_active
            }
            
            result = edit_user(user_id, updated_payload)
            if result:
                st.success(f"Successfully updated user {email}!")
                st.rerun()
    else:
        st.info("No users found.")