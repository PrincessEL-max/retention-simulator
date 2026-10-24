# app/streamlit_app.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

from src.value import Params, add_value
from src.strategies import curve, select_targets, LABEL
from src.sensitivity import peta, titik_impas

st.set_page_config(page_title="Simulator Promo Retensi", layout="wide")


@st.cache_data
def muat():
    return pd.read_parquet(Path(__file__).parent / "app_data.parquet")


def rp(x):
    return f"Rp {x / 1e6:,.1f} juta"

LABEL_FITUR = {
    "contract": "Jenis kontrak", "tenure_months": "Lama berlangganan",
    "internet_service": "Jenis internet", "is_echeck": "Bayar e-check",
    "total_charges": "Total tagihan", "paperless_billing": "Tagihan digital",
    "n_streaming": "Jumlah streaming", "is_month_to_month": "Kontrak bulanan",
    "monthly_charge": "Tagihan bulanan", "avg_monthly_hist": "Rata-rata tagihan",
    "n_protection": "Jumlah proteksi", "is_fiber": "Internet fiber",
    "multiple_lines": "Banyak jalur telepon", "phone_service": "Layanan telepon",
    "has_internet": "Punya internet", "senior_citizen": "Lansia",
    "payment_method": "Metode bayar", "has_dependents": "Punya tanggungan",
    "n_addons": "Jumlah add-on", "n_family": "Jumlah keluarga",
    "auto_pay": "Bayar otomatis", "has_partner": "Punya pasangan"}
df = muat()

st.title("Simulator Promo Retensi")
st.caption("Data: IBM Telco Customer Churn (sampel, perusahaan fiktif). Nilai rupiah = ilustrasi skala. "
           "Untung adalah PERKIRAAN di bawah asumsi di panel kiri; save rate belum dibuktikan A/B test.")

with st.sidebar:
    st.header("Asumsi")
    save = st.slider("Save rate (promo menahan calon churner)", 0.05, 0.50, 0.25, 0.05)
    margin = st.slider("Margin kontribusi", 0.10, 0.80, 0.40, 0.05)
    horizon = st.slider("Horizon (bulan)", 6, 24, 12, 1)
    kontak = st.number_input("Biaya kontak per orang (Rp)", 500, 5000, 2000, 500)
    insentif = st.number_input("Biaya insentif per penerima (Rp)", 5000, 20000, 10000, 1000)
    takeup = st.slider("Take-up insentif", 0.15, 0.50, 0.30, 0.05)
    st.header("Keputusan")
    budget = st.slider("Budget (Rp juta)", 1.0, 40.0, 10.0, 0.5) * 1e6
    strategi = st.radio("Cara memilih", ["untung", "risiko", "acak"], format_func=LABEL.get)

P = Params(margin=margin, horizon=int(horizon), save_rate=save,
           contact_cost=float(kontak), incentive_cost=float(insentif), takeup=takeup)
v = add_value(df, P)
t1, t2, t3, tshap, t4 = st.tabs(["Simulator", "Bandingkan cara", "Seberapa kuat asumsi?",
                                  "Kenapa skor ini?", "Catatan"])
with t1:
    tg, r = select_targets(v, budget, P, strategi)
    layak = int((v["ev"] > 0).sum())
    c = st.columns(4)
    c[0].metric("Pelanggan dihubungi", f"{r['n']:,}")
    c[1].metric("Biaya (perkiraan)", rp(r["biaya"]))
    c[2].metric("Untung bersih (perkiraan)", rp(r["perkiraan"]))
    c[3].metric("Untung menurut data", rp(r["kenyataan"]))
    st.write(f"{r['persen_churner']:.0%} pelanggan yang akhirnya pergi ada di daftar ini.")
    if strategi == "untung" and layak * P.eff_cost < budget:
        st.info(f"Budget lebih besar dari kebutuhan: hanya {layak:,} pelanggan yang layak "
                f"(biaya {rp(layak * P.eff_cost)}). Sisanya merugi kalau dihubungi.")
    tab = tg[["id", "contract", "tenure_bucket", "monthly_charge_band", "p_churn", "clv", "ev"]].copy()
    tab.columns = ["ID", "Kontrak", "Lama berlangganan", "Band tagihan",
                   "Peluang pergi", "Nilai pelanggan (Rp)", "Untung bersih (Rp)"]
    st.dataframe(tab.head(100).round({"Peluang pergi": 3, "Nilai pelanggan (Rp)": 0,
                                      "Untung bersih (Rp)": 0}), hide_index=True)
    st.download_button("Unduh daftar (CSV)", tab.to_csv(index=False).encode("utf-8"),
                       "daftar_target.csv", "text/csv")

with t2:
    anggar = np.arange(0, 40_000_001, 500_000)
    cur = curve(v, P, anggar)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
    for a, kol, jd in [(ax[0], "perkiraan", "Menurut perkiraan model"),
                       (ax[1], "kenyataan", "Menurut kenyataan di data")]:
        for s, g in cur.groupby("strategi"):
            a.plot(g["budget"] / 1e6, g[kol] / 1e6, label=LABEL[s])
        a.axvline(budget / 1e6, color="red", ls="--", lw=0.8)
        a.axhline(0, color="gray", lw=0.8)
        a.set_title(jd)
        a.set_xlabel("Budget (Rp juta)")
    ax[0].set_ylabel("Untung bersih (Rp juta)")
    ax[0].legend()
    st.pyplot(fig)
    semua = len(v) * P.eff_cost
    s = curve(v, P, [semua]).set_index("strategi")["kenyataan"]
    st.write(f"Hubungi semua pelanggan: {rp(s['acak'])}. "
             f"Hanya yang layak: {rp(s['untung'])} (menurut data, pada asumsi saat ini).")

with t3:
    ti = titik_impas(df, P)
    st.metric("Save rate minimum agar tidak rugi (daftar target)", f"{ti['daftar_asumsi_awal']:.1%}")
    S = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40]
    C = [1250, 2500, 5000, 7500, 10000, 15000]
    u = peta(df, P, S, C) / 1e6
    fig2, ax2 = plt.subplots(figsize=(8, 3.8))
    im = ax2.imshow(u.values, aspect="auto", cmap="YlGn")
    ax2.set_xticks(range(len(S)))
    ax2.set_xticklabels([f"{x:.0%}" for x in S])
    ax2.set_yticks(range(len(C)))
    ax2.set_yticklabels([f"{x:,}" for x in C])
    ax2.set_xlabel("Save rate")
    ax2.set_ylabel("Biaya efektif per orang (Rp)")
    for i in range(len(C)):
        for j in range(len(S)):
            ax2.text(j, i, f"{u.values[i, j]:.0f}", ha="center", va="center", fontsize=8)
    plt.colorbar(im, label="Untung bersih (Rp juta)")
    st.pyplot(fig2)
    st.caption("Untung menurut data pada margin dan horizon di panel kiri.")

with tshap:
    st.caption("Poin risiko dari model penjelas (SHAP): merah menaikkan skor, biru menurunkan. "
               "Ini penjelasan tentang MODEL, bukan bukti sebab-akibat; fitur yang mirip saling berbagi "
               "pengaruh. Skor di tabel berasal dari model yang tidak melihat pelanggan ini, sedangkan "
               "penjelasan dari model final: hampir sama, tidak identik.")
    if len(tg) == 0:
        st.info("Daftar target kosong pada pengaturan ini.")
    else:
        pid = st.selectbox("Pilih pelanggan dari daftar target", tg["id"].head(100).tolist())
        row = v.loc[v["id"] == pid].iloc[0]
        poin = pd.Series({c[5:]: row[c] for c in v.columns if c.startswith("shap_")})
        top = poin.reindex(poin.abs().sort_values(ascending=False).index)[:8].iloc[::-1]
        fig3, ax3 = plt.subplots(figsize=(7, 3.6))
        ax3.barh([LABEL_FITUR.get(k, k) for k in top.index], top.values,
                 color=["tab:red" if x > 0 else "tab:blue" for x in top.values])
        ax3.axvline(0, color="black", lw=0.8)
        ax3.set_xlabel("Poin risiko")
        plt.tight_layout()
        st.pyplot(fig3)
        st.write(f"Skor peluang pergi: {row['p_churn']:.0%} · kontrak {row['contract']} · "
                 f"lama berlangganan {row['tenure_bucket']} bulan · "
                 f"nilai pelanggan Rp {row['clv']:,.0f}")
        
with t4:
    st.markdown("""
- **Save rate adalah asumsi**, belum dibuktikan. Rancangan A/B test ada di repo.
- Model memprediksi **siapa yang pergi**, bukan **siapa yang bisa ditahan**.
- Data snapshot dari perusahaan fiktif bergaya pascabayar; pasar Indonesia didominasi prabayar.
- Rupiah memakai ARPU blended Rp 46.000: ilustrasi skala, bukan data operator.
- Keputusan yang kokoh: **pilih pelanggan, jangan hubungi semua**. Besar untungnya rapuh terhadap asumsi.
""")