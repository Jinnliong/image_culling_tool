# 🦛 **Project Hippocampus v0.14.1**  
### *An Unorthodox AI Gallery Curator & Systemic Culling Engine*

Project **Hippocampus** is a private, local‑first AI tool designed to transform the chaotic *“shotgun”* approach of modern photography into a curated collection of masterpieces. Built on **The Hippo Framework**, it embraces **Via Negativa** (addition by subtraction) to ruthlessly filter technical failures while using **Phase 3: The Alchemy** to preserve and categorize artistic soul.

Designed specifically for the **Lenovo ThinkPad X1 Carbon Gen 11**, it leverages **Ollama** and **Phi‑3 Vision** to deliver professional‑grade curation — all **100% offline**, with not a single pixel uploaded to the cloud.

---

## 🛠️ **The Hippo Framework Integration**

Hippocampus isn’t just a script; it’s a *philosophical implementation*:

### **Phase 1: The Void**  
Strict quantitative thresholds (Sharpness, Exposure, Composition) remove friction and let the system reveal its nature.

### **Phase 2: The Spark**  
A rapid reframing of the AI’s role from *Judge* to *Assistant* using a 6‑tier categorization logic.

### **Phase 3: The Alchemy**  
The Review Safety Net ensures that even if the AI disqualifies a photo, your human intuition remains the final authority.

---

## ✨ **Key Features**

### 🎨 **6‑Tier Curation System**
Automatically sorts images into:

- **Masterpiece** — Technical + Narrative + Emotion  
- **Storyteller** — Technical + Narrative  
- **Mood** — Technical + Emotion  
- **Technical** — Sharpness / Exposure only  
- **Review Needed** — *The Kintsugi Safety Net*  
- **Discarded** — *The Void*

### 🎯 **Dynamic Calibration**  
A `st.dialog` pop‑up system analyzes *Pro Benchmarks* to mathematically set your operational sliders.

### 📊 **Global Gear Ledger**  
Tracks historically which lenses (OM‑1 vs. Xiaomi 12s Ultra) and settings produce your highest‑rated **Masterpieces**.

### 🛡️ **Privacy First**  
100% offline analysis. No cloud. No subscription. No leaks.

---

## 🚀 **Quick Start**

### **1. Prerequisites**
Ensure Ollama is installed and the vision model is pulled:

```bash
ollama pull phi3:vision
```

### **2. Installation**
Clone the repository and install dependencies:

```bash
# Clone the repository
git clone https://github.com/your-username/hippocampus.git
cd hippocampus

# Install dependencies
pip install streamlit pandas psutil ollama pillow
```

### **3. Execution**
Launch the Command Center:

```bash
streamlit run app.py
```

---

## ⚙️ **System Requirements**

| Component | Recommendation |
|----------|----------------|
| **Device** | Lenovo ThinkPad X1 Carbon Gen 11 (or equivalent) |
| **Memory** | 16GB+ RAM |
| **Processor** | Intel Core i7 (P‑Cores optimized) |
| **Storage** | 500MB for Global Ledger & Reports |

---

## 📜 **Operating Guidelines**

> **"Never react immediately to a loud complaint. Introduce silence."**

### **The Strategic Pause**  
Run a Calibration Batch using Pinterest masters (Saul Leiter, Alex Webb) before starting a major project like the **Greece 2026** collection.

### **The Subtraction Rule**  
If processing is slow, reduce `max_size` in `utils.py` rather than adding more complex code.

### **The Empty Boat**  
Trust the Review folder. Detach ego from the AI’s “DQ” rating and enjoy the curation process.

---

### Developed with ☕ and Resilience by **Hippo (Chin Jinn Liong)**  
**Remember: Every day is an opportunity.**

---

If you'd like, I can also create a **dark‑mode version**, a **minimalist version**, or a **README‑optimized version** for GitHub.
