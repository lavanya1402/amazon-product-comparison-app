# 🛒 **Amazon Product Comparison App (AI-Powered)**

### ⚡ Built by **Lavanya Srivastava** 

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Framework-Streamlit-ff4b4b?logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/WebScraping-BeautifulSoup-yellow?logo=python" />
  <img src="https://img.shields.io/badge/AI-RecommendationEngine-purple?logo=openai" />
  <img src="https://img.shields.io/badge/Status-Active-success?logo=github" />
</p>

<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=rect&color=gradient&height=80&section=header&text=Amazon%20Product%20Comparison%20App&fontSize=32&fontAlignY=55" />
</p>

A powerful **AI-powered Amazon product comparison tool** that lets users easily compare products using **Product Name**, **ASIN**, or **Amazon URL**, and always returns **at least 5 best-matching products** with rich insights, charts, and final recommendations.

---

# 📌 **Highlights**

### 🔍 **Flexible Input Choices**

You can search using:

* Product Name
* ASIN
* Amazon Product URL

### 🤖 **AI-Driven Recommendations**

Ranking is based on:

* Price
* Rating
* Reviews
* Feature richness
* Weighted AI score (0–100)

### 📊 **Beautiful Visual Charts**

* Price Comparison
* Rating Comparison
* Combined Overall Score Chart

### 📦 **Smart Scraping (Fail-Proof)**

* Uses multiple search strategies
* Ensures **minimum 5 products**
* Cleans and formats messy Amazon data
* Handles complicated selectors

### ⚠️ **Robust Error Handling**

* Invalid input
* Missing data
* Amazon blocking
* Scrape failures
* Network timeouts

### 🧾 **Download as CSV**

Export all comparisons in one click.

---

# 🗂️ **Project Structure**

```
amazon-comparison-project/
│
├── app/
│   ├── scraper.py           # Scrapes product + similar items
│   ├── comparator.py        # Comparison logic & ranking
│   ├── recommender.py       # AI scoring engine
│   ├── utils.py             # Cleaners, formatters, helpers
│   └── main.py              # Streamlit app entry
│
├── data/
│   └── sample_output.csv
│
├── images/
│   └── screenshots/
│       ├── ui_home.png
│       ├── comparison_table.png
│       ├── charts.png
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# ▶️ **How to Run Locally**

### 1️⃣ Clone the repo

```bash
git clone https://github.com/lavanya1402/amazon-product-comparison-app.git
cd amazon-product-comparison-app
```

### 2️⃣ Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate      # Windows → venv\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Launch the app

```bash
streamlit run app/main.py
```

---

# 🧠 **How It Works**

```
User Input
     ↓
Identify Base Product (Name/ASIN/URL)
     ↓
Scrape Similar Products (min. 5)
     ↓
Clean + Standardize Data
     ↓
AI Scoring → Price + Ratings + Reviews
     ↓
Comparison Table + Visual Charts
     ↓
Final Best Product Recommendation
```

---

### 🏠 Home Screen

<img width="940" height="483" alt="image" src="https://github.com/user-attachments/assets/2b770711-50c0-4216-b782-93651df5e5cf" />
<img width="955" height="472" alt="image" src="https://github.com/user-attachments/assets/3f315d75-4fde-43f0-b71f-2d7161f8f030" />
<img width="943" height="488" alt="image" src="https://github.com/user-attachments/assets/9a6d0308-0a74-4563-a74b-7efbde7e798d" />
<img width="925" height="443" alt="image" src="https://github.com/user-attachments/assets/628db8c6-2708-4598-9eb2-53408d632915" />
<img width="917" height="469" alt="image" src="https://github.com/user-attachments/assets/ed691adf-68a8-4fa9-a9ba-98d9e38f4d12" />
<img width="928" height="437" alt="image" src="https://github.com/user-attachments/assets/c591f74b-6426-443a-a5c8-c9c5cfeb2656" />


# 🔮 **Future Enhancements**

* 🛍️ Add Amazon Prime eligibility filter
* 🌐 Multi-region support (US, UK, UAE, India)
* 🤖 Chat-bot interface for exploring products
* 🧠 LLM-based product summary
* 📦 Add “Top 10 Alternatives” mode

---

# 🧾 **License**

```
© 2025 Lavanya Srivastava — All Rights Reserved.
This project is for learning, teaching, and demonstration purposes only.
Commercial use requires permission.
```

---

# 👩‍💻 **Author**

### **Lavanya Srivastava**


🌐 GitHub: [https://github.com/lavanya1402](https://github.com/lavanya1402)
💼 LinkedIn: [https://linkedin.com/in/lavanya-srivastava](https://linkedin.com/in/lavanya-srivastava)
📧 Email: [lavanaya.srivastava@gmail.com](mailto:lavanaya.srivastava@gmail.com)

