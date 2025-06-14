import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from fpdf import FPDF
import tempfile

# --- اسم البرنامج ---
st.set_page_config(page_title="Ammonia Plant Maintenance Dashboard", layout="wide")
st.title("🧰 Ammonia Plant Maintenance Dashboard")
# --- نهاية العنوان ---


def export_df_to_pdf(df, title="Report"):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, txt=title, ln=1, align="C")
    pdf.ln(5)

    col_widths = [max(len(str(x)) for x in [col]+df[col].astype(str).tolist())*2.5 for col in df.columns]
    row_height = 8

    for i, col in enumerate(df.columns):
        pdf.cell(col_widths[i], row_height, str(col), border=1, align="C")
    pdf.ln(row_height)

    for idx, row in df.iterrows():
        for i, col in enumerate(df.columns):
            text = str(row[col])
            pdf.cell(col_widths[i], row_height, text, border=1, align="C")
        pdf.ln(row_height)

    tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(tmpfile.name)
    return tmpfile.name

def load_spare_parts_data():
    critical_df = pd.read_excel("critical_critical_spare_parts.xlsx")
    transactions_df = pd.read_excel("spare_parts_spare_parts_transactions.xlsx")
    return critical_df, transactions_df

if st.button("🔁 Refresh Data"):
    st.cache_data.clear()
    st.session_state.active_tab = "Maintenance Log"

compressors_df = pd.read_excel("monthly_compressor_hours_fixed.xlsx", sheet_name="Sheet1")
log_df = pd.read_excel("maintenance_log_data.xlsx", sheet_name="Sheet1")

machine_list = [
    "Sabroe VMY336B (1)", "Sabroe VMY336B (2)",
    "Howden MK6D (5)", "Howden MK6D (6)",
    "Sabroe SGC 1918 (7)", "Sabroe SGC 1918 (9)", "Sabroe SGC 1918 (10)",
    "Sabroe SGC 2813 (11)", "Sabroe SGC 2813 (12)",
    "Howden MK6D (13)", "Howden MK6D (14)", "Howden MK6D (15)", "Howden MK6D (16)",
    "Cooling Tower (1)", "Cooling Tower (2)", "Cooling Tower (3)",
    "Cooling Tower (4)", "Cooling Tower (5)", "Cooling Tower (6)"
]

tab_options = ["Compressors", "Maintenance Log", "Spare Parts", "KPIs"]
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Maintenance Log"

selected_tab = st.radio("📌 Select Tab", tab_options, index=tab_options.index(st.session_state.active_tab), horizontal=True)
st.session_state.active_tab = selected_tab
if selected_tab == "Compressors":
    st.subheader("📈 Compressor Total Hours")

    # --- فورم إدخال آخر صيانة تمت ---
    st.markdown("### 🛠️ Add Last Maintenance Event")
    with st.form("form_add_last_maintenance"):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            last_maint_machine = st.selectbox("🏭 Compressor", machine_list[:13], key="last_maint_machine")
        with col2:
            maint_type = st.selectbox("🛠️ Maintenance Type", ["5000h", "10000h", "40000h"], key="last_maint_type")
        with col3:
            last_maint_date = st.date_input("📅 Maintenance Date", key="last_maint_date")
        with col4:
            last_maint_hours = st.number_input("🔢 Hours at Maintenance", min_value=0.0, step=0.5, key="last_maint_hours")
        submit_last_maint = st.form_submit_button("✅ Save Last Maintenance")

        if submit_last_maint:
            new_row = pd.DataFrame({
                "Date": [last_maint_date],
                "Compressor": [last_maint_machine],
                "Maintenance Type": [maint_type],
                "Hours at Maintenance": [last_maint_hours]
            })
            updated_df = pd.concat([compressors_df, new_row], ignore_index=True)
            try:
                updated_df.to_excel("monthly_compressor_hours_fixed.xlsx", index=False)
                st.success("✅ Last maintenance saved successfully.")
            except Exception as e:
                st.error(f"❌ Error saving file: {e}")

    # --- فورم إضافة إجمالي الساعات ---
    st.markdown("### ➕ Add Total Hours")
    with st.form("form_add_hours"):
        col1, col2, col3 = st.columns(3)
        with col1:
            date = st.date_input("📅 Date", key="date_input_hours")
        with col2:
            machine = st.selectbox("🏭 Select Compressor", machine_list[:13], key="machine_input_hours")
        with col3:
            hours = st.number_input("⏱️ Total Hours", min_value=0.0, step=0.5, key="hours_input_hours")
        submit_hours = st.form_submit_button("✅ Save Total Hours")

        if submit_hours:
            new_row = pd.DataFrame({"Date": [date], "Compressor": [machine], "Total Hours": [hours]})
            updated_df = pd.concat([compressors_df, new_row], ignore_index=True)
            try:
                updated_df.to_excel("monthly_compressor_hours_fixed.xlsx", index=False)
                st.success("✅ Running hours saved successfully.")
            except Exception as e:
                st.error(f"❌ Error saving file: {e}")

    # --- باقي الكود كما هو ---
    st.markdown("### 🛠️ Log Maintenance Event")
    st.markdown("### 📅 Last Maintenance Records")
    if st.button("📅 Show Last Maintenance"):
        try:
            maint_df = pd.read_excel("monthly_compressor_hours_fixed.xlsx")
            maint_df = maint_df.dropna(subset=["Date", "Compressor", "Maintenance Type", "Hours at Maintenance"])
            maint_df["Date"] = pd.to_datetime(maint_df["Date"], errors="coerce")
            last_maint = maint_df.sort_values("Date").groupby("Compressor").tail(1).sort_values("Compressor")
            df_last = last_maint[["Compressor", "Date", "Maintenance Type", "Hours at Maintenance"]].copy()
            df_last["Date"] = pd.to_datetime(df_last["Date"]).dt.date
            st.dataframe(df_last, use_container_width=True)
            pdf_file = export_df_to_pdf(df_last, title="Last Maintenance Records")
            with open(pdf_file, "rb") as f:
                st.download_button("Export to PDF", f, file_name="last_maintenance.pdf")
        except Exception as e:
            st.error(f"❌ Failed to show last maintenance records: {e}")

    # --- جدول المتبقي للصيانة القادمة + رسائل التحذير ---
    st.markdown("### 🔔 Remaining Hours to Next Maintenance")
    if st.button("🔔 Show Remaining to Next Maintenance"):
        try:
            maint_types = [5000, 10000, 40000]
            maint_df = pd.read_excel("monthly_compressor_hours_fixed.xlsx")
            maint_df["Date"] = pd.to_datetime(maint_df["Date"], errors="coerce")
            current_hours = maint_df.groupby("Compressor")["Total Hours"].max().reset_index()
            result = []
            warnings = {5000: False, 10000: False, 40000: False}

            for compressor in machine_list[:13]:
                comp_maint = maint_df[maint_df["Compressor"] == compressor]
                ch_row = current_hours[current_hours["Compressor"] == compressor]
                if ch_row.empty:
                    continue
                ch = ch_row["Total Hours"].values[0]
                row = {"Compressor": compressor, "Current Total Hours": ch}
                for mt in maint_types:
                    last_maint = comp_maint[comp_maint["Maintenance Type"] == f"{mt}h"]
                    if not last_maint.empty:
                        last_h = last_maint.sort_values("Date")["Hours at Maintenance"].iloc[-1]
                        next_due = last_h + mt
                        remaining = next_due - ch
                        if isinstance(remaining, (int, float)) and remaining != "-":
                            months = remaining / 360
                            val = f"{remaining:.0f} ({months:.1f} mo)"
                            if months < 6 and months > 0:
                                warnings[mt] = True
                        else:
                            val = "-"
                        row[f"Next {mt}h At"] = next_due
                        row[f"Remaining to {mt}h"] = val
                    else:
                        row[f"Next {mt}h At"] = "-"
                        row[f"Remaining to {mt}h"] = "-"
                result.append(row)
            df = pd.DataFrame(result)

            for mt in maint_types:
                if warnings[mt]:
                    st.warning(f"⚠️ Need to order spare parts for {mt} hrs maintenance")

            st.dataframe(df, use_container_width=True)
            pdf_file = export_df_to_pdf(df, title="Remaining to Next Maintenance")
            with open(pdf_file, "rb") as f:
                st.download_button("Export to PDF", f, file_name="remaining_next_maintenance.pdf")
        except Exception as e:
            st.error(f"❌ Failed to calculate remaining hours: {e}")

   

elif selected_tab == "Maintenance Log":
    st.subheader("📝 Maintenance Log")

    if "event_count" not in st.session_state:
        st.session_state.event_count = 1
    if "removed_indices" not in st.session_state:
        st.session_state.removed_indices = set()

    add_event = st.button("➕ Add Event")
    if add_event:
        st.session_state.event_count += 1

    st.markdown("### ✍️ Enter Maintenance Events")
    with st.form("form_add_dynamic_log"):
        log_date = st.date_input("📅 Date (applies to all events)", key="dynamic_log_date")

        event_data = []
        for i in range(st.session_state.event_count):
            st.markdown(f"---\n📝 **Event {i+1}**")
            cols = st.columns([2.5, 1, 3, 2.5, 1])
            with cols[0]:
                machine = st.selectbox(f"🏭 Machine {i+1}", machine_list, key=f"dyn_machine_{i}")
            with cols[1]:
                minutes = st.number_input(f"⏱️ Time (min) {i+1}", min_value=0, step=1, key=f"dyn_minutes_{i}")
            with cols[2]:
                event = st.text_area(f"🛠️ Event Description {i+1}", height=100, key=f"dyn_event_{i}")
            with cols[3]:
                spare = st.text_input(f"🔩 Spare Parts {i+1}", key=f"dyn_spare_{i}")
            with cols[4]:
                if st.form_submit_button(f"❌ Remove {i+1}"):
                    st.session_state.removed_indices.add(i)
            event_data.append((i, machine, minutes, event, spare))

        submit_dynamic = st.form_submit_button("✅ Save All Events")

        if submit_dynamic:
            records = []
            for i, machine, minutes, event, spare in event_data:
                if i in st.session_state.removed_indices:
                    continue
                records.append({
                    "Date": log_date,
                    "Machine": machine,
                    "Time (min)": minutes,
                    "Event": event,
                    "Spare Parts": spare
                })
            if records:
                df_new = pd.DataFrame(records)
                try:
                    updated_log = pd.concat([log_df, df_new], ignore_index=True)
                    updated_log.to_excel("maintenance_log_data.xlsx", index=False)
                    st.success(f"✅ {len(records)} maintenance events saved.")
                    st.session_state.removed_indices.clear()
                except Exception as e:
                    st.exception(e)
            else:
                st.warning("⚠️ No events were entered.")

    st.markdown("### 🔍 Filter by Machine and Date")

    machine_options = ["All Machines"] + machine_list
    selected_machine = st.selectbox("📌 Filter Machine", machine_options, key="filter_machine")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("📆 From Date", value=log_df["Date"].min())
    with col2:
        end_date = st.date_input("📅 To Date", value=log_df["Date"].max())

    if selected_machine == "All Machines":
        filtered_df = log_df
    else:
        filtered_df = log_df[log_df["Machine"] == selected_machine]

    filtered_df = filtered_df[(filtered_df["Date"] >= pd.to_datetime(start_date)) &
                              (filtered_df["Date"] <= pd.to_datetime(end_date))]
    filtered_df = filtered_df.copy()
    filtered_df["Date"] = pd.to_datetime(filtered_df["Date"]).dt.date
    columns_to_display = ["Date", "Machine", "Time (min)", "Event", "Spare Parts"]
    st.dataframe(filtered_df[columns_to_display], use_container_width=True)
    pdf_file = export_df_to_pdf(filtered_df[columns_to_display], title="Maintenance Log")
    with open(pdf_file, "rb") as f:
        st.download_button("Export to PDF", f, file_name="maintenance_log.pdf")

elif selected_tab == "Spare Parts":
    # --- عنوان التبويب مع أيقونة ---
    st.markdown("<h2 style='color:#0b5394; font-weight:bold;'>🔧 Spare Parts Management</h2>", unsafe_allow_html=True)

    # --- مربع الإضافة ---
    with st.container():
        st.markdown("""
        <div style="border:1px solid #dadada; border-radius:15px; padding:20px; margin-bottom:16px; background-color:#f7fbff;">
        <h4 style='color:#00897b;'>➕ Add New Spare Part</h4>
        """, unsafe_allow_html=True)
        with st.form("add_spare_part_form", clear_on_submit=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                part_number = st.text_input("Part Number")
            with col2:
                part_name = st.text_input("Part Name")
            with col3:
                quantity = st.number_input("Quantity", min_value=0, step=1)
            with col4:
                unit = st.text_input("Unit")
            col5, col6 = st.columns(2)
            with col5:
                min_stock = st.number_input("Minimum Stock", min_value=0, step=1)
            with col6:
                location = st.text_input("Location")
            machine = st.selectbox("Machine", machine_list)
            notes = st.text_input("Notes")
            submitted = st.form_submit_button("🟢 Add Spare Part", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- حفظ بند جديد ---
    try:
        critical_df, transactions_df = load_spare_parts_data()
    except Exception as e:
        st.warning("يرجى التأكد من وجود ملف critical_critical_spare_parts.xlsx وspare_parts_spare_parts_transactions.xlsx في نفس مجلد البرنامج.")
        st.exception(e)
        st.stop()
    if submitted:
        new_row = pd.DataFrame([{
            "Part Number": part_number,
            "Part Name": part_name,
            "Quantity": quantity,
            "Unit": unit,
            "Minimum Stock": min_stock,
            "Location": location,
            "Machine": machine,
            "Notes": notes
        }])
        for col in ["Machine", "Notes"]:
            if col not in critical_df.columns:
                critical_df[col] = ""
        critical_df = pd.concat([critical_df, new_row], ignore_index=True)
        critical_df.to_excel("critical_critical_spare_parts.xlsx", index=False)
        st.success("✅ Spare part added successfully!")

    # --- مربع خصم بند ---
    with st.container():
        st.markdown("""
        <div style="border:1px solid #fad0c3; border-radius:15px; padding:20px; margin-bottom:16px; background-color:#fff7f4;">
        <h4 style='color:#c62828;'>➖ Issue (Withdraw) Spare Part</h4>
        """, unsafe_allow_html=True)
        with st.form("issue_spare_part_form", clear_on_submit=True):
            issue_col1, issue_col2, issue_col3 = st.columns(3)
            with issue_col1:
                part_to_issue = st.selectbox("Part Number", critical_df["Part Number"].unique())
            with issue_col2:
                qty_to_issue = st.number_input("Quantity to Issue", min_value=1, step=1)
            with issue_col3:
                machine_to_issue = st.selectbox("Machine", machine_list)
            reason_issue = st.text_input("Note/Reason")
            submit_issue = st.form_submit_button("🔴 Issue Spare Part", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if submit_issue:
        idx = critical_df[critical_df["Part Number"] == part_to_issue].index
        if len(idx) == 0:
            st.error("❌ Part not found!")
        else:
            idx = idx[0]
            current_qty = critical_df.at[idx, "Quantity"]
            if qty_to_issue > current_qty:
                st.error("❌ Not enough quantity in stock!")
            else:
                critical_df.at[idx, "Quantity"] = current_qty - qty_to_issue
                critical_df.to_excel("critical_critical_spare_parts.xlsx", index=False)
                new_tran = pd.DataFrame([{
                    "Date": datetime.now().date(),
                    "Transaction Type": "Issue",
                    "Part Number": part_to_issue,
                    "Part Name": critical_df.at[idx, "Part Name"],
                    "Quantity": qty_to_issue,
                    "Machine": machine_to_issue,
                    "Note": reason_issue
                }])
                for col in ["Machine", "Note"]:
                    if col not in transactions_df.columns:
                        transactions_df[col] = ""
                transactions_df = pd.concat([transactions_df, new_tran], ignore_index=True)
                transactions_df.to_excel("spare_parts_spare_parts_transactions.xlsx", index=False)
                st.success("✅ Spare part issued and transaction saved!")
                min_stock = critical_df.at[idx, "Minimum Stock"]
                if critical_df.at[idx, "Quantity"] < min_stock:
                    st.warning("⚠️ Quantity below minimum stock!")

    # --- فلتر الماكينة ---
    st.markdown("<h5 style='margin-top:20px;'>🏭 <b>Filter by Machine</b></h5>", unsafe_allow_html=True)
    machine_options = ["All Machines"] + machine_list
    selected_machine = st.selectbox("", machine_options, key="critical_machine_filter")
    if selected_machine == "All Machines":
        filtered_critical_df = critical_df
    else:
        filtered_critical_df = critical_df[critical_df["Machine"] == selected_machine]

    # --- جدول القطع الحرجة ---
    st.markdown("""
    <div style="border:1px solid #b7d4ea; border-radius:10px; padding:8px; background-color:#f2faff;">
    <span style="font-size:18px;font-weight:bold;">📋 Critical Spare Parts List</span>
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(filtered_critical_df, use_container_width=True)
    pdf_file_crit = export_df_to_pdf(filtered_critical_df, title="Critical Spare Parts")
    with open(pdf_file_crit, "rb") as f:
        st.download_button("⬇️ Export Critical Spare Parts to PDF", f, file_name="critical_spare_parts.pdf")

    # --- جدول العمليات ---
    st.markdown("""
    <div style="border:1px solid #ffe5b4; border-radius:10px; padding:8px; margin-top:18px; background-color:#fffcf5;">
    <span style="font-size:18px;font-weight:bold;">📑 Spare Parts Transactions</span>
    </div>
    """, unsafe_allow_html=True)
    st.dataframe(transactions_df, use_container_width=True)
    pdf_file_trans = export_df_to_pdf(transactions_df, title="Spare Parts Transactions")
    with open(pdf_file_trans, "rb") as f:
        st.download_button("⬇️ Export Transactions to PDF", f, file_name="spare_parts_transactions.pdf")
elif selected_tab == "KPIs":
    st.title("📊 Compressor Performance KPIs")

    try:
        import matplotlib.pyplot as plt
        import numpy as np

        # --- تحميل وتجهيز البيانات ---
        compressors_df = pd.read_excel("monthly_compressor_hours_fixed.xlsx", sheet_name="Sheet1")
        compressors_df = compressors_df.sort_values(["Compressor", "Date"])
        compressors_df["Date"] = pd.to_datetime(compressors_df["Date"], errors="coerce")
        compressors_df["Month"] = compressors_df["Date"].dt.to_period("M").astype(str)
        compressors_df["Running Hours"] = compressors_df.groupby("Compressor")["Total Hours"].diff().fillna(0)

        # --- فلاتر الماكينة والشهر ---
        col1, col2 = st.columns([1, 1])
        with col1:
            selected_compressor = st.selectbox("Select Compressor", compressors_df["Compressor"].unique(), key="kpi_comp")
        with col2:
            unique_months = compressors_df["Month"].unique()
            selected_month = st.selectbox("Select Month", ["All"] + list(unique_months), key="kpi_month")

        filtered_df = compressors_df[compressors_df["Compressor"] == selected_compressor]
        if selected_month != "All":
            filtered_df = filtered_df[filtered_df["Month"] == selected_month]

        # --- حساب كل مؤشرات الـKPIs ---
        running_hours = filtered_df["Running Hours"].sum()
        downtime_hrs = filtered_df["DOWN TIME (HRS)"].sum() if "DOWN TIME (HRS)" in filtered_df.columns else 0
        faults = filtered_df["NO. OF FAULTS"].sum() if "NO. OF FAULTS" in filtered_df.columns else 0
        if not filtered_df.empty and "Total Hours" in filtered_df.columns:
            total_hours = filtered_df["Total Hours"].max()
        else:
            total_hours = 0

        if running_hours > 0:
            availability = ((running_hours - downtime_hrs) / running_hours) * 100
        else:
            availability = 0

        mttr = downtime_hrs / faults if faults > 0 else 0
        mtbf = running_hours / faults if faults > 0 else 0

        # --- كروت KPIs ملونة ---
        st.markdown(
            """
            <style>
                .kpi-card {
                    background-color: #2e3b2e;
                    border-radius: 15px;
                    padding: 20px 10px 12px 10px;
                    margin-bottom: 8px;
                    box-shadow: 1px 2px 8px 0 #111;
                    text-align: center;
                }
                .kpi-title {
                    font-size:18px;
                    font-weight:bold;
                    color:#ffd54f;
                    margin-bottom:7px;
                }
                .kpi-value {
                    font-size:32px;
                    font-weight:bold;
                    color:#ffde59;
                    margin-bottom:2px;
                }
                .kpi-icon {
                    font-size:23px;
                    margin-bottom:6px;
                }
                .kpi-sub {
                    color:#bdbdbd;
                    font-size:14px;
                    font-weight:600;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        k1, k2, k3, k4, k5, k6, k7 = st.columns(7)

        with k1:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">⏱️</div>
                    <div class="kpi-title">Running Hours</div>
                    <div class="kpi-value">{round(running_hours, 2)}</div>
                    <div class="kpi-sub">hrs</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k2:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">⏸️</div>
                    <div class="kpi-title">Downtime</div>
                    <div class="kpi-value" style="color:#e65100">{round(downtime_hrs, 2)}</div>
                    <div class="kpi-sub">hrs</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k3:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">✅</div>
                    <div class="kpi-title">Availability</div>
                    <div class="kpi-value" style="color:#2e7d32">{availability:.1f}%</div>
                    <div class="kpi-sub">%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k4:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">⚠️</div>
                    <div class="kpi-title">Faults</div>
                    <div class="kpi-value" style="color:#b71c1c">{int(faults)}</div>
                    <div class="kpi-sub">No.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k5:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">🛠️</div>
                    <div class="kpi-title">MTTR</div>
                    <div class="kpi-value" style="color:#1565c0">{mttr:.2f}</div>
                    <div class="kpi-sub">hrs/fault</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k6:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">📈</div>
                    <div class="kpi-title">MTBF</div>
                    <div class="kpi-value" style="color:#4a148c">{mtbf:.2f}</div>
                    <div class="kpi-sub">hrs/fault</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with k7:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon">🔢</div>
                    <div class="kpi-title">Total Hours</div>
                    <div class="kpi-value" style="color:#673ab7">{round(total_hours, 2)}</div>
                    <div class="kpi-sub">hrs</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # --- شارت ديناميكي لأي مؤشر KPI ---
        chart_group = compressors_df[compressors_df["Compressor"] == selected_compressor].groupby("Month").agg({
            "Running Hours": "sum",
            "DOWN TIME (HRS)": "sum",
            "NO. OF FAULTS": "sum"
        }).reset_index()
        chart_group["Availability"] = ((chart_group["Running Hours"] - chart_group["DOWN TIME (HRS)"]) / chart_group["Running Hours"]).replace([float('inf'), -float('inf')], 0) * 100
        chart_group["MTTR"] = chart_group.apply(lambda row: row["DOWN TIME (HRS)"]/row["NO. OF FAULTS"] if row["NO. OF FAULTS"]>0 else 0, axis=1)
        chart_group["MTBF"] = chart_group.apply(lambda row: row["Running Hours"]/row["NO. OF FAULTS"] if row["NO. OF FAULTS"]>0 else 0, axis=1)

        kpi_options = ["Availability", "MTTR", "MTBF"]
        selected_kpi_chart = st.selectbox("Select KPI to Show Chart", kpi_options, key="kpi_chart_select")

        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot(chart_group["Month"], chart_group[selected_kpi_chart], marker='o', linewidth=2, color="#ffde59")

        ax.set_xlabel("Month", fontsize=13, color="#ffd54f")
        ax.set_ylabel(selected_kpi_chart, fontsize=13, color="#ffd54f")
        ax.set_title(f"{selected_kpi_chart} Trend - {selected_compressor}", fontsize=15, color="#ffde59", fontweight="bold")
        plt.xticks(rotation=35, fontsize=12, color="#ffd54f")
        plt.yticks(fontsize=12, color="#ffd54f")
        ax.grid(True, linestyle="--", alpha=0.3, color="#444")
        for i, v in enumerate(chart_group[selected_kpi_chart]):
            ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=11, color="#fff")
        plt.tight_layout()
        st.pyplot(fig)

        # --- شارت مقارنة كل الضواغط في شهر معين (Bar Chart) ---
        all_months = compressors_df["Month"].dropna().unique()
        selected_bar_month = st.selectbox("🔎 Select Month for Running Hours Comparison", sorted(all_months), key="bar_month")

        month_df = compressors_df[compressors_df["Month"] == selected_bar_month]
        bar_data = month_df.groupby("Compressor")["Running Hours"].sum().reset_index()

        fig2, ax2 = plt.subplots(figsize=(10, 4))
        bars = ax2.bar(bar_data["Compressor"], bar_data["Running Hours"], width=0.6)
        colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(bars)))
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        for bar in bars:
            height = bar.get_height()
            ax2.annotate(f'{height:.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 6),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=13, color="#ffd54f")

        ax2.set_xlabel("Compressor", fontsize=14, color="#ffd54f")
        ax2.set_ylabel("Running Hours", fontsize=14, color="#ffd54f")
        ax2.set_title(f"Running Hours per Compressor in {selected_bar_month}", fontsize=15, color="#ffde59", fontweight="bold")
        plt.xticks(rotation=30, fontsize=12, color="#ffd54f")
        plt.yticks(fontsize=12, color="#ffd54f")
        ax2.grid(axis="y", linestyle="--", alpha=0.25, color="#444")
        plt.tight_layout()
        st.pyplot(fig2)

        # --- شارت Total Hours داكنة وألوان عالمية ---
        selected_total_month = st.selectbox("🌙 اختر شهر لمقارنة Total Hours", sorted(all_months), key="total_hours_month")
        month_tot_df = compressors_df[compressors_df["Month"] == selected_total_month]
        total_hours_data = month_tot_df.groupby("Compressor")["Total Hours"].max().reset_index()

        plt.style.use('dark_background')
        fig3, ax3 = plt.subplots(figsize=(11, 5))
        bars3 = ax3.bar(total_hours_data["Compressor"], total_hours_data["Total Hours"], width=0.65)
        colors3 = plt.cm.inferno(np.linspace(0.12, 0.88, len(bars3)))
        for bar, color in zip(bars3, colors3):
            bar.set_color(color)
        for bar in bars3:
            height = bar.get_height()
            ax3.annotate(f'{height:.0f}',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 10),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=14, fontweight='bold', color="#fff")
        ax3.set_xlabel("Compressor", fontsize=15, color="#f5f5f5", labelpad=8)
        ax3.set_ylabel("Total Hours", fontsize=15, color="#f5f5f5", labelpad=8)
        ax3.set_title(f"🌙 Total Hours per Compressor in {selected_total_month}", fontsize=18, color="#ffde59", pad=15, fontweight='bold')
        plt.xticks(rotation=25, fontsize=13, color="#ffd54f")
        plt.yticks(fontsize=13, color="#ffd54f")
        ax3.spines['bottom'].set_color('#888')
        ax3.spines['left'].set_color('#888')
        ax3.grid(axis="y", linestyle="--", alpha=0.25, color="#eee")
        plt.tight_layout()
        st.pyplot(fig3)

    except Exception as e:
        st.error(f"Error loading KPIs data: {e}")
