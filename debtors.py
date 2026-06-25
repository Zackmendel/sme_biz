#debtors.py
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

st.set_page_config(layout="wide", page_title="Business Portal")

def get_debtors_table(business_uuid):
    try:
        response = supabase.table("debtors").select("*").eq("business_id", business_uuid).execute()
        return response.data if response.data else []
    except Exception as e:
        st.error(f"Error fetching debtors data: {e}")
        return []

def set_deptors(business_uuid, debt_details):
    try:
        response = supabase.table("debtors").insert(debt_details).execute()
        return response
    except Exception as e:
        st.error(f"Error adding debtors data: {e}")
        return None

def set_paid_debtor(debtor_id, paid_at):
    try:
        response = supabase.table("debtors").update({"is_paid": True, "paid_at": paid_at}).eq("id", debtor_id).execute()
        return response
    except Exception as e:
        st.error(f"Error updating debtor status: {e}")
        return None


def show_debtors_management_ui():
    debt_table = get_debtors_table(business_uuid)
    if not debt_table:
        df_debt_table = pd.DataFrame(columns=["id", "customer_name", "amount", "is_paid", "created_at", "paid_at"])
    else:
        df_debt_table = pd.DataFrame(debt_table)
        df_debt_table.sort_values(by="created_at", ascending=False, inplace=True)

    outstanding = df_debt_table["amount"].where(df_debt_table["is_paid"] == False).sum()
    paid_debt = df_debt_table["amount"].where(df_debt_table["is_paid"] == True).sum()
    total = df_debt_table["amount"].sum()
    
    col1, col2, col3, col4 = st.columns([4, 2, 2, 2], gap='small')
    with col1:
        st.markdown("# :yellow[Debt Management Dashboard]")
    with col2:
        with st.container(border=True):
            st.metric("Outstanding Debt", f"N {outstanding}")
    with col3:
        with st.container(border=True):
            st.metric("Paid Debt", f"N {paid_debt}")
    with col4:
        with st.container(border=True):
            st.metric("Total ", f"N {total}")

    
    st.markdown("### Add Debtor", text_alignment='right')

    with st.container(border=True):
        col_1, col_2, col_3, col_4 = st.columns(4, gap="large", vertical_alignment='bottom')
        with col_1:
            debtors_name = st.text_input(label="Enter Debtor Name", placeholder= "e.g. Martina", value="", key="debtor_name")
        with col_2:
            debtors_amount = st.number_input(label="Enter Amount Owed", placeholder= "e.g. 1000", value=0, step=100, key="amount_owed")
        with col_3:
            debtors_date = st.date_input(label="Enter Date of Transaction", value=pd.to_datetime("today"), key="date")
        with col_4:
            if st.button("Add Debtor", type="primary"):
                debt_details = {
                    "business_id": business_uuid,
                    "customer_name": debtors_name,
                    "amount": debtors_amount,
                    "created_at": debtors_date.isoformat()
                }
                success = set_deptors(business_uuid, debt_details)
                if success:
                    st.success("Debtor added successfully!")
                    st.rerun()
                else:
                    st.error("Failed to add debtor.")

    # st.divider()

    col_x, col_xx = st.columns(2, gap="medium", border=True)
    with col_x:
        st.markdown("### :red[Unpaid Debts]")
        df_unpaid_table = df_debt_table.loc[df_debt_table['is_paid'] == False]
        if not df_debt_table.empty:
            col_a, col_b, col_c, col_d, col_e = st.columns(5, gap="small")
            with col_a:
                st.markdown("#### :green[Customers]")
            with col_b:
                st.markdown("#### :green[Amount]")
            with col_c:
                st.markdown("#### :red[Paid?]")
            with col_d:
                st.markdown("#### :blue[Date]")
            with col_e:
                st.markdown("#### :blue[Paid at]")

            for _, row in df_unpaid_table.iterrows():
                debtor_id = row.get("id")
                customer_name = row.get("customer_name")
                amount = row.get("amount")
                is_paid = row.get("is_paid", False)
                created_at = pd.to_datetime(row.get("created_at")).strftime("%Y-%m-%d")
                paid_at = row.get("paid_at")

                with st.container(border=True):
                    r_col_a, r_col_b, r_col_c, r_col_d, r_col_e = st.columns(5, gap="small")
                    with r_col_a:
                        st.write(customer_name)

                    with r_col_b:
                        st.write(amount)

                    with r_col_c:
                        if is_paid:
                            st.write("Paid ✅")
                        else:
                            if st.button("Paid", type="primary", key=f"paid_{debtor_id}"):
                                paid_at = pd.Timestamp.now(tz='UTC').isoformat()
                                set_paid_debtor(debtor_id, paid_at)
                                st.rerun()

                    with r_col_d:
                        st.write(created_at)

                    with r_col_e:
                        if pd.notna(paid_at) and paid_at:
                            st.write(pd.to_datetime(paid_at).strftime("%Y-%m-%d"))
                        else:
                            st.write("-")


    with col_xx:
        st.markdown("### :green[Paid Debts]")
        df_paid_table = df_debt_table.loc[df_debt_table['is_paid'] == True]
        if not df_paid_table.empty:
            col_a, col_b, col_c, col_d, col_e = st.columns(5, gap="small")
            with col_a:
                st.markdown("#### :green[Customers]")
            with col_b:
                st.markdown("#### :green[Amount]")
            with col_c:
                st.markdown("#### :red[Paid?]")
            with col_d:
                st.markdown("#### :blue[Date]")
            with col_e:
                st.markdown("#### :blue[Paid at]")

            for _, row in df_paid_table.iterrows():
                debtor_id = row.get("id")
                customer_name = row.get("customer_name")
                amount = row.get("amount")
                is_paid = row.get("is_paid", False)
                created_at = pd.to_datetime(row.get("created_at")).strftime("%Y-%m-%d")
                paid_at = row.get("paid_at")

                with st.container(border=True):
                    r_col_a, r_col_b, r_col_c, r_col_d, r_col_e = st.columns(5, gap="small")
                    with r_col_a:
                        st.write(customer_name)

                    with r_col_b:
                        st.write(amount)

                    with r_col_c:
                        st.write("Paid ✅")

                    with r_col_d:
                        st.write(created_at)

                    with r_col_e:
                        if pd.notna(paid_at) and paid_at:
                            st.write(pd.to_datetime(paid_at).strftime("%Y-%m-%d"))
                        else:
                            st.write("-")





    st.dataframe(df_debt_table)