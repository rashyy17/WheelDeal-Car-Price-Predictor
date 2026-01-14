# 🚗 WheelDeal – Car Price Predictor

WheelDeal is a machine learning–based **car price prediction system** designed to give users a realistic estimate of a vehicle’s market value. It combines **price prediction** with **real‑time market comparison**, making it a one‑stop solution for understanding car prices.

---

## 🔍 What this project does

WheelDeal offers **two core features**:

### 1️⃣ Predict Your Car’s Value

* Enter details of your vehicle
* Get an **estimated resale value** based on market trends
* Prediction is generated using a trained ML model

### 2️⃣ Compare Market Prices

* Uses **web scraping (Selenium)** to fetch prices of **similar vehicles listed online**
* Displays a **predicted price range** based on real market listings
* Helps validate the ML prediction with real‑world data

Together, these features help users make informed decisions while buying or selling a car.

---

## 🧠 Machine Learning Details

* **Dataset**: Kaggle car price dataset
* **Models used**:

  * Linear Regression
  * Decision Tree–based models
  * Random Forest Regressor
  * XGBoost Regressor
* **Training**:

  * Data cleaning and preprocessing
  * Feature selection and model training
  * Model comparison to select best-performing model
  * Trained model saved and reused for predictions
* The model learns pricing patterns based on historical data and market trends

---

## 🛠️ Tech Stack

* **Python**
* **Machine Learning** (scikit‑learn)
* **Flask** (backend logic)
* **Selenium** (web scraping similar vehicle listings)
* **HTML / CSS** (basic frontend)

---

## 📁 Project Structure

```
WheelDeal-Car-Price-Predictor/
│── app.py
│── src/
│── models/
│── data/
│── requirements.txt
│── Procfile
│── README_DEPLOY.md
```

---

## 🚀 How to Run Locally

1. Clone the repository

   ```bash
   git clone https://github.com/rashyy17/WheelDeal-Car-Price-Predictor.git
   cd WheelDeal-Car-Price-Predictor
   ```

2. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Run the application

   ```bash
   python app.py
   ```

4. Open in browser

   ```
   http://localhost:5000
   ```

---

## ⚠️ Important Notes

* The project is **not deployed yet**
* Selenium scraping depends on browser drivers and website structure
* Accuracy may vary depending on market changes and dataset limitations

---

## 🌱 Future Improvements

* Deploy the application (Render / Railway / AWS)
* Add more features affecting car prices
* Improve UI and user experience
* Optimize scraping and caching of market data

---

## 📌 Why WheelDeal?

WheelDeal bridges the gap between **ML predictions** and **real market prices**, giving users a clearer picture of what a car is actually worth.
## 📸 Screenshots

### 🏠 Home Page
![Home Page](https://github.com/user-attachments/assets/6dce8d80-1133-4a17-adf7-925df72adbf8)

---

### 🔮 Web Scraping (OLX comparisions)
![Price Prediction](https://github.com/user-attachments/assets/c1bfbdf0-2ce5-4a4d-ac8a-bd977fd2bfbe)

---

### 📊 Compare 2 cars mode
![Market Comparison](https://github.com/user-attachments/assets/18859802-295f-47f9-b944-769253d3786d)

---

### 📈 Using Selenium to fetch data
![Price Range](https://github.com/user-attachments/assets/41fa7c8c-39ce-46c4-b774-bea4899f3741)
⭐ If you find this project interesting, feel free to star the repo!
