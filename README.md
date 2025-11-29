# 🛒 **Amazon Product Comparison App (AI-Powered)**

### ⚡ Built by **Lavanya Srivastava** — • Agentic AI Specialist • Corporate Trainer

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

# 📸 **Screenshots**

> *<img width="898" height="469" alt="image" src="https://github.com/user-attachments/assets/820e45f8-115d-4628-8c93-ba2285bfeedf" />
<img width="953" height="469" alt="image" src="https://github.com/user-attachments/assets/182d65ef-b680-4918-910b-3945a6917096" />
*<img width="930" height="171" alt="image" src="https://github.com/user-attachments/assets/91f0acc0-f02d-4a4e-8821-36a2a619b75e" /><img width="629" height="130" alt="image" src="https://github.com/user-attachments/assets/e35eaa7f-629f-42bc-89b9-771dd11e57ea" />![Uploading image.png…]()




### 🏠 Home Screen

![Home Screen](images/screenshots/home.png)

### 📊 Comparison Table

![Comparison Table](images/screenshots/table.png)

### 📈 Price + Rating Chart

![Charts](images/screenshots/chart.png)

---

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

Agentic AI Specialist | Corporate Trainer

🌐 GitHub: [https://github.com/lavanya1402](https://github.com/lavanya1402)
💼 LinkedIn: [https://linkedin.com/in/lavanya-srivastava](https://linkedin.com/in/lavanya-srivastava)
📧 Email: [lavanaya.srivastava@gmail.com](mailto:lavanaya.srivastava@gmail.com)

