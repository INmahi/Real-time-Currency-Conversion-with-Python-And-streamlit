# 💱 Real-Time Currency Converter

A clean and interactive Streamlit web app to convert between currencies using real-time exchange rates. Includes currency swapping, fallback using cached rates, and optional historical data.

---

## ✅ How to Run This App

1. **Download Required Libraries**

Make sure you have Python 3.8+ installed. Then run:

```bash
pip install -r requirements.txt
```

2. **Go to the Project Directory**

Navigate to the folder where this app is saved:

```bash
cd your-project-folder-name
```

3. **Run the Streamlit App**

Launch the app using Streamlit:

Go to project directory and run:

```bash
streamlit run app.py
```

---

## 📝 Files

- `app.py` – Main Streamlit app
- `cache_manager.py` – Manages cached exchange rates
- `currency_converter.py` – Handles API requests and conversion logic
- `requirements.txt` – Required Python packages

---

## 📦 Required Packages

Your `requirements.txt` should include:

```
streamlit
requests
pandas
python-dotenv
```

---

Enjoy your currency conversion! 💱
