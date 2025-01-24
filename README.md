# 🏠 House Damage Detection System

A web-based application designed to detect and classify house damage levels using AI technology. The system analyzes uploaded images and categorizes them into three distinct levels: **severe damage**, **moderate damage**, and **minor damage**. Built with **Streamlit**, this platform offers accurate damage classification to assist users in evaluating building conditions.

---

## 🼋 Features

- **Accurate Damage Classification**  
  Classifies house damages into:  
  - **Severe Damage**: Total structural failure.  
  - **Moderate Damage**: Significant repairs needed.  
  - **Minor Damage**: Small cracks or cosmetic issues.  

- **User-Friendly Interface**  
  Upload images and receive results easily.

- **Interactive Data Visualization**  
  View detection history and statistics.

- **Database Integration**  
  Stores user accounts and detection results in a **MySQL database**.

- **API Integration**  
  Accessible API endpoints, testable via **Postman**.

---

## 🔧 Technologies Used

- **MobileNetV2**: AI model architecture.
- **Streamlit**: Frontend framework.
- **Plotly**: Interactive charts.
- **TensorFlow/Keras**: Deep learning backend.
- **MySQL**: Database management.
- **Flask**: RESTful API framework.

---

## 🚀 How to Use

### Web Interface
1. **Upload an Image**: Upload a house image.
2. **Get Results**: Receive a damage classification.
3. **View Statistics**: Explore interactive charts.
4. **Manage Account**: Register, login, and access your history.

### API Endpoints (Tested with Postman)

- **`GET /`**: Returns a welcome message.
- **`POST /register`**: Registers a new user.
  ```json
  {
    "email": "example@gmail.com",
    "password": "yourpassword"
  }
  ```
- **`POST /login`**: Authenticates a user.
- **`POST /predict`**: Upload an image for damage classification.
  ```json
  {
    "confidence": 92.15
    "image_name": "img_1",
   "label": "Severe Damage"
  }
  ```
- **`GET /history`**: Fetches detection history for a user.
- 
---

## 🔧 Setup and Installation

1. Clone the repository:  
   ```bash
   git clone https://github.com/nabilamumtaz/house-damage-detection.git
   ```

2. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the database:
   - Create a MySQL database named `user_management`.
   - Import the database structure:
     - **Table `users`**: Stores user account details.
     - **Table `detections`**: Logs detection history.

4. Start the API:
   ```bash
   python app.py
   ```

5. Run the Streamlit app:
   ```bash
   streamlit run main.py
   ```

---

## 🔁 Future Improvements

- Enhance model accuracy.
- Add multilingual support.
- Integrate repair cost estimation.
- Improve API response time.

---

## 👩‍💻 Developers

Developed by:  
- **Nabila Mumtaz**  
- **Tasyfia Farhah Subrina Lubis**  

Part of an internship project at **BPK RI**.
