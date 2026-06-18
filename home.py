import os
import pandas as pd
import streamlit as st
from supabase import Client, create_client
from dotenv import load_dotenv

load_dotenv()

# We still set up the client, but queries will dynamically use the logged-in business_id
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_PUBLISHABLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def get_users_table(business_uuid):
    try:
        response = supabase.table("users").select("*").eq("business_id", business_uuid).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching users data: {e}")
        return []

def get_business_details(business_uuid):
    try:
        response = supabase.table("businesses").select("*").eq("id", business_uuid).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching business details: {e}")
        return []    

# =============================================================
# Homepage UI
# ==============================================================

def show_dashboard_ui(user_role, business_uuid):
    # Fetch data dynamically based on passed session business_uuid
    business_data = get_business_details(business_uuid)
    users_data = get_users_table(business_uuid)

    if not business_data:
        st.error("No business details found for this profile.")
        return

    df_business = pd.DataFrame(business_data)
    df_users = pd.DataFrame(users_data)

    # Business Dataframe assignment securely inside execution function
    business_name = df_business.iloc[0, 1]
    owner_name = df_business.iloc[0, 2]
    description = df_business.iloc[0, 3]
    industry = df_business.iloc[0, 4]
    scale = df_business.iloc[0, 5]
    phone = df_business.iloc[0, 6]
    email = df_business.iloc[0, 7]
    city = df_business.iloc[0, 8]
    address = df_business.iloc[0, 9]
    proof_url = df_business.iloc[0, 10]
    created_at = pd.to_datetime(df_business.iloc[0, 11]).strftime('%Y-%m-%d')

    col1, col2, col3 = st.columns([2, 5, 2])
    with col1:
        st.success(f"Welcome back! You are tracking records for Business Domain.")
            
        if user_role in ["admin", "owner"]:
            st.info("💡 Complete Administrator view initialized.")
        elif user_role =="staff":
            st.info("💡 Staff view active.")
        else:
            st.warning("🔒 Standard User View active.")

    with col2:
        with st.container(border=True, vertical_alignment='top'):
            col_1, col_2, col_3 = st.columns([2, 5, 2])
            # Graceful check for profile image placeholder
            try:
                col_1.image("images/profile_placeholder.png")
            except:
                col_1.warning("No image")
            col_2.title(business_name)
            col_2.write(f"<span style='color:red;'>{scale}</span> . {city}, Nigeria", unsafe_allow_html=True)
            col_3.write("Active Since")
            col_3.success(created_at)

    if "id" in df_users.columns:
        col3.markdown(f"# :blue[{df_users['id'].count()}]", text_alignment='center')
    col3.markdown("# **Staffs**", text_alignment='center')

    col_1, col_2 = st.columns(2, border=True, gap='medium')

    with col_1:
        st.info("Business Details")
        for label, val in [("Owner", owner_name), ("Description", description), 
                           ("Industry", industry), ("Scale", scale), 
                           ("Phone", phone), ("Email", email), 
                           ("City", city), ("Address", address), ("Proof URL", proof_url)]:
            col_a, col_b = st.columns([1, 2], vertical_alignment='top')
            col_a.write(f"**{label}**")
            col_b.write(val)

    with col_2:
        st.info("Staff Members")
        if not df_users.empty:
            col_a, col_b = st.columns([2, 1], vertical_alignment='top')
            for i in range(len(df_users)):
                col_a.write(f"{df_users.iloc[i,3]} {df_users.iloc[i,4]}")
                col_b.markdown(f":green[{df_users.iloc[i,5]}]")
        else:
            st.write("No staff data found.")

    st.dataframe(df_business)