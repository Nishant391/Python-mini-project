# ⚡ Pulse Nutrition — Simple Calorie & Protein Tracker

A clean, modern, intuitive daily calorie and protein tracking web application built with **Python**, **Streamlit**, and **SQLite3**, designed for speed, simplicity, and ease of use.

---

## 🌟 Key Improvements & Features

1. **Clean, Eye-Friendly Design**:
   - Replaced cluttered neon glows with a sleek, modern dark slate aesthetic.
   - Clear typography with high readability and calm visual hierarchy.

2. **Ultra-Simple Daily Summary**:
   - **Calories Card**: Consumed kcal, daily target, remaining calories, and clean progress bar.
   - **Protein Card**: Consumed grams, daily target, remaining protein to hit, and progress bar.
   - **Macro Balance**: Instant protein energy ratio and per-meal averages.

3. **Fast Quick-Add Meal Workflow**:
   - **1-Click Presets**: Immediately log popular staples (Chicken Breast 200g, Whey Shake, Eggs & Toast, Greek Yogurt, Steak Bowl) with a single click.
   - **Direct Inline Logging**: Clean, horizontal quick-log form right on the main tab—no hunting inside hidden accordions.

4. **Logical Chronological Meal Organization**:
   - Organized naturally by time of day: **Breakfast (🍳)** ➔ **Lunch (🥗)** ➔ **Dinner (🥩)** ➔ **Snacks (🍎)**.
   - Clear subtotal badges for calories and protein per category.
   - Fast 1-click item removal (`✕`).

5. **Tabbed Navigation**:
   - **📋 Today's Meals**: Everything you need for logging and managing your daily intake.
   - **📊 Analytics & Trends**: Meal distribution donut charts and 7-day progress trajectory with goal benchmark lines.
   - **🎯 Goals & Settings**: Easy goal configuration with 1-click presets (Fat Loss, Maintenance, Muscle Bulk) and CSV export.

6. **Fast Date Navigation**:
   - Quick **◀ Prev** and **Next ▶** day navigation buttons with 1-click jump back to **Today**.

---

## 🚀 Installation & Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application
```bash
streamlit run app.py
```

The application will launch in your browser at **`http://localhost:8501`**.

---

## 📁 Project Structure

```
pymini/
├── app.py              # Main Streamlit application (Database, Clean UI & Analytics)
├── requirements.txt    # Python dependencies (streamlit, plotly, pandas)
├── tracker.db          # SQLite persistent database (auto-generated)
└── README.md           # Documentation & instructions
```
