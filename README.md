<div align="center">
  <img src="photos/teamlogo%20.jpeg" alt="TechMedics 108+ Logo" width="150" height="auto" />
  <h1>techmedics-108+</h1>
  <p><strong>ATLAS Hackathon Edition</strong> | <em>Bridging the Gap: From Panic to Precision</em></p>

  [![Deployed on Render](https://img.shields.io/badge/Deployed_on-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://techmedics-108.onrender.com/)
  [![Demo Video](https://img.shields.io/badge/Watch-Demo_Video-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://drive.google.com/file/d/1XYbmHxfMWaXSHama5ysZLa_DLIiKNXnn/view?usp=sharing)
</div>

---

## 📅 Hackathon Context: ATLAS
Welcome to **ATLAS – GDG on Campus Hackathon**, hosted by **GDG on Campus - NIST** and powered by **Hack2skill**.

**Theme**: Emergency Response & Healthcare  
**Team**: DOONDILEONS

<div align="center">
  <img src="photos/about.jpeg" alt="Project Overview" width="800" />
</div>

### 👥 Meet The Team
1. **Nallimilli Surya Prakash Reddy**
2. **Mandela Doondi Usha Sri**
3. **Vinayaka Gowdra chandrashekarappa**
4. **Anya Sree Kadali**

---

## 🚀 LIVE DEMO
**Experience the App Live**: [https://techmedics-108.onrender.com/](https://techmedics-108.onrender.com/)

---

## 👨‍⚖️ For the Jury: Verification Guide
**Distinguished Jury Members:**
*   **Dr. Sushanta Kumar** (Associate Professor, ME, NIST University)
*   **Mr. Prabhas Raj** (Founder and CEO, Protionix Group)
*   **Dr. Sandipan Mallik** (Professor, ECE, NIST University)

**Dear Jury Members,**
Thank you for reviewing **techmedics-108+**. We have built a robust, real-time Emergency Response System that works even in low-bandwidth scenarios.

### Step-by-Test Instructions:

#### 1. The "Wow" Factor (Real-time Sync)
*   **Step 1**: Open the [Call Center Dashboard](https://techmedics-108.onrender.com/callcenter) in one tab.
*   **Step 2**: Open the [Ambulance App](https://techmedics-108.onrender.com/api/ambulance/app) in a second tab (or Incognito window).
    *   **Login**: Use ID `DVG-AMB-001` (Pre-loaded test account).
*   **Step 3**: On the Call Center, initiate a call with any number.
*   **Step 4**: Click "Assign Nearest Ambulance".
*   **Result**: Watch the Ambulance App instantly receive an **"EMERGENCY ALERT"** popup without refreshing the page!

#### 2. Advanced Location Sharing (Glassmorphism UI)
*   **Step 1**: Click **"Share Location"**.
*   **Step 2**: Open the link on your phone.
*   **Step 3**: Click **"Share My Exact Location"**.
*   **Result**: The dispatcher map updates *instantly* with precise GPS coordinates.

---

## 🏗️ Architecture & Workflow

### Process Flow
The 108+ system ensures a seamless flow of information from the distress call to the ambulance arrival.
<div align="center">
  <img src="photos/flow%20digram.png" alt="Process Flow Diagram" width="700" />
</div>

### System Architecture
Robust Flask backend with Socket.IO supporting both high-speed connections and SMS fallbacks.
<div align="center">
  <img src="photos/architecture.png" alt="System Architecture" width="700" />
</div>

---

## 📸 Snapshots of MVP
A glimpse into our functional Emergency Response System.

<div align="center">
  <img src="photos/1.jpeg" alt="Call Center" width="45%" />
  <img src="photos/2.jpeg" alt="Driver App" width="45%" />
</div>
<div align="center">
  <img src="photos/3.jpeg" alt="Location Share" width="45%" />
  <img src="photos/4.jpeg" alt="Live Tracking" width="45%" />
</div>
<div align="center">
  <img src="photos/5.jpeg" alt="Snapshot 5" width="60%" />
</div>

---

## 📺 Project Walkthrough
If you cannot test it live, watch our full demonstration video here:
[**WATCH DEMO VIDEO**](https://drive.google.com/file/d/1XYbmHxfMWaXSHama5ysZLa_DLIiKNXnn/view?usp=sharing)

---

## 🛠️ Key Features
- **Real-time Dispatch**: Socket.IO powered instant communication.
- **Smart Assignment**: Algorithms to find the nearest available ambulance.
- **Offline-First SMS**: Fallback SMS protocol.
- **Responsive Design**: Mobile-first interface.
- **Live Tracking**: Leaflet.js maps.

## 💻 Tech Stack
- **Backend**: Python (Flask)
- **Real-time**: Socket.IO
- **Database**: SQLite (SQLAlchemy)
- **Frontend**: HTML5, CSS3 (Glassmorphism)
- **Deployment**: Render (Cloud)

---

<div align="center">
  <p>© 2026 TechMedics Team | Built for ATLAS Hackathon</p>
</div>
