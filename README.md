# 📊 BORSA ARENA — Quant & Social Hub

> Türkiye'nin ücretsiz, algoritmik yatırım platformu.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://borsa-arena.streamlit.app)

---

## 🚀 5 Dakikada Deploy Et (Tamamen Ücretsiz)

### Adım 1: GitHub'a Yükle

```bash
# 1. GitHub'da yeni repo oluştur: github.com/new
# Repo adı: borsa-arena (public olsun)

# 2. Dosyaları yükle
git init
git add .
git commit -m "🚀 Borsa Arena v0.1.0 - İlk commit"
git remote add origin https://github.com/KULLANICI_ADIN/borsa-arena.git
git push -u origin main
```

### Adım 2: Streamlit Cloud'a Deploy Et

1. **share.streamlit.io** adresine git
2. Google veya GitHub ile ücretsiz giriş yap
3. **"New app"** butonuna tıkla
4. Ayarlar:
   - **Repository:** `KULLANICI_ADIN/borsa-arena`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. **"Deploy!"** butonuna bas
6. ~2 dakika bekle → Uygulama canlıya geçer!

### Adım 3: Secrets Ayarla (Supabase)

Streamlit Cloud → App → Settings → **Secrets** bölümüne yapıştır:

```toml
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_KEY = "eyJ..."
```

> **Not:** Supabase olmadan da çalışır! Demo mod aktif olur.
> `demo@borsaarena.com` / `demo123` ile giriş yapılabilir.

---

## 💻 Yerel Geliştirme

```bash
# Kurulum
pip install -r requirements.txt

# Çalıştır
streamlit run app.py

# Tarayıcıda aç: http://localhost:8501
```

---

## 🗂️ Proje Yapısı

```
borsa-arena/
├── app.py                    ← Ana uygulama + navigasyon
├── requirements.txt          ← Python bağımlılıkları
├── .streamlit/
│   ├── config.toml           ← Dark tema ayarları
│   └── secrets.toml          ← API anahtarları (paylaşma!)
├── pages/
│   ├── dashboard.py          ← BIST 100 anlık görünüm
│   ├── strategy_lab.py       ← 50+ indikatör + backtest
│   ├── fantasy_lig.py        ← İlk 11 hisse oyunu
│   ├── correlation.py        ← Korelasyon ısı haritası
│   └── social.py             ← Sinyal ağı + sohbet
└── utils/
    ├── auth.py               ← Kullanıcı girişi (Supabase/demo)
    ├── data.py               ← Veri çekme (yfinance)
    ├── indicators.py         ← 50+ teknik indikatör
    ├── backtest.py           ← Backtest motoru
    └── charts.py             ← Plotly grafik üretici
```

---

## 📦 Modüller

| Modül | Açıklama | Durum |
|-------|----------|-------|
| 🏠 Dashboard | BIST 100 anlık durum, hızlı grafik | ✅ Hazır |
| 🔬 Strateji Lab | 50+ indikatör, backtest, sinyal tarayıcı | ✅ Hazır |
| ⚽ Fantezi Lig | İlk 11 hisse, haftalık puan, liderlik | ✅ Hazır |
| 🌡️ Korelasyon | Isı haritası, sektör analizi, lead-lag | ✅ Hazır |
| 📡 Sosyal Sinyal | Sinyal akışı, paylaşım, sohbet odaları | ✅ Hazır |
| 💎 DCF Değerleme | İndirgenmiş nakit akışı hesaplama | 🔜 v0.2 |
| 🎯 Arbitraj Radar | ADR/GDR fiyat farklarını tarama | 🔜 v0.2 |
| 🤖 Pine Script Bridge | TradingView webhook entegrasyonu | 🔜 v0.3 |

---

## 🔧 Teknik Altyapı

| Katman | Teknoloji | Maliyet |
|--------|-----------|---------|
| Frontend/Backend | Streamlit | **Ücretsiz** |
| Hosting | Streamlit Community Cloud | **Ücretsiz** |
| Veritabanı | Supabase (PostgreSQL) | **Ücretsiz** (500MB) |
| Veri Kaynağı | yfinance | **Ücretsiz** |
| İndikatörler | pandas-ta (50+ indikatör) | **Ücretsiz** |
| Grafikler | Plotly | **Ücretsiz** |
| **TOPLAM** | | **₺0 / ay** |

---

## 👥 Giriş Bilgileri (Demo)

| Kullanıcı | Şifre | Rütbe |
|-----------|-------|-------|
| `demo@borsaarena.com` | `demo123` | Silver |
| `admin@borsaarena.com` | `admin123` | Platinum |

---

## ⚠️ Yasal Uyarı

Borsa Arena bir **fintech eğitim platformudur**. Sunulan içerikler yatırım tavsiyesi değildir.
Geçmiş performans gelecekteki getirileri garanti etmez.

---

## 📜 Lisans

MIT License — Özgürce kullanabilirsin, geliştirebilirsin.

---

## 🗺️ Yol Haritası

**v0.1** (Şu an) → Temel modüller, demo auth, BIST verileri  
**v0.2** → Supabase entegrasyonu, DCF hesaplama, arbitraj radar  
**v0.3** → Pine Script webhook, mobil PWA, bildirimler  
**v1.0** → Premium plan, API erişimi, kurumsal araçlar  
