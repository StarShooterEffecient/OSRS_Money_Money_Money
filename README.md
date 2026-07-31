# ⚡ OmniFlip Engine v2.0
> **Quantitative OSRS Grand Exchange Trading & Arbitrage Framework**  
> *Fully Autonomous, Serverless, Free GitHub-Hosted Market Engine*

---

## 📌 Overview
**OmniFlip Engine** treats the Old School RuneScape (OSRS) Grand Exchange not merely as an in-game market, but as an active, high-frequency limit-order book subject to microstructural mechanics, behavioral economic biases, and fluid liquidity dynamics.

Unlike standard flipping tools that rely on raw GP spread, OmniFlip factors in:
* **2% GE Tax Dynamics** (including the 5,000,000 GP cap ceiling).
* **Tax-Adjusted Velocity-Margin Score ($VMS$)** to maximize GP yield per hour per GE slot.
* **Behavioral Front-Running Logic ($P_{\text{anchor}} \pm 1$)** to beat psychological human round-number order walls.
* **Potion Decant Arbitrage Matrix** (exploiting dose disparities between 1-dose and 4-dose potions).
* **Self-Refining Memory Layer** storing item confidence weights ($W_{\text{item}}$) in persistent DuckDB/SQLite across workflow cycles.
* **Fractional Kelly Capital Optimizer** providing exact 8-slot allocation recommendations based on liquid bankroll.

---

## 🚀 5-Minute Setup & Deployment Guide

### Step 1: Fork or Upload Repository
1. Push these files to your GitHub repository.
2. Ensure directory layout matches:
   ```text
   ├── .github/
   │   └── workflows/
   │       └── engine.yml
   ├── public/
   │   └── index.html
   ├── engine.py
   ├── README.md
   └── omniflip_memory.db (Auto-created)
   ```

### Step 2: Enable GitHub Pages
1. In your GitHub repository, go to **Settings** -> **Pages**.
2. Under **Build and deployment** -> **Source**, select **GitHub Actions**.

### Step 3: Set Webhook Alerts (Optional)
1. Go to **Settings** -> **Secrets and variables** -> **Actions**.
2. Click **New repository secret**.
3. Name: `DISCORD_WEBHOOK_URL`
4. Value: Paste your Discord Channel Webhook URL.

### Step 4: Run the Engine
1. Go to the **Actions** tab in GitHub.
2. Select **OmniFlip Market Engine Runner** on the left.
3. Click **Run workflow** -> **Run workflow**.
4. The workflow will run automatically every 10 minutes, updating telemetry and publishing your GitHub Pages dashboard at `https://<your-username>.github.io/<repo-name>/`.

---

## 🛠️ Tactical Architecture & Models

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           CROSS-DOMAIN TAXONOMY                                  │
├───────────────────────┬──────────────────────────┬───────────────────────────────┤
│ Model                 │ Theoretical Origin       │ GE Engine Application         │
├───────────────────────┼──────────────────────────┼───────────────────────────────┤
│ Marginal Value        │ Ecological Foraging      │ Force-cancel stale slots when │
│ Theorem (MVT)         │ Biology                  │ EV/hr drops below portfolio μ │
│ Psychological         │ Behavioral Economics     │ Asymmetric offset pricing     │
│ Front-Running         │                          │ ($P_anchor + 13 / -17$)       │
│ Active Sonar Ping     │ Military Naval Tactics   │ 1-Qty micro probe orders to   │
│ Probing               │                          │ map invisible order depth     │
│ Cavitation Collapse   │ Fluid Dynamics           │ Bottom-feeder orders catching │
│                       │                          │ bot-farm dump vacuums         │
└───────────────────────┴──────────────────────────┴───────────────────────────────┘
```

---

## 📊 Core Mathematical Formulas

### 1. Tax-Adjusted Net Margin
$$\text{Tax}(P_{\text{high}}) = \min\left(\lfloor 0.02 \times P_{\text{high}} \rfloor, \; 5\,000\,000\right)$$

$$\text{Net Margin} = P_{\text{high}} - \text{Tax}(P_{\text{high}}) - P_{\text{low}}$$

### 2. Velocity-Margin Score ($VMS$)
$$\text{Velocity Cap} = \min\left(\text{Volume}_{\text{hourly}}, \; \text{Buy Limit}\right)$$

$$\text{VMS} = \text{Net Margin} \times \text{Velocity Cap} \times W_{\text{item}}$$

---

## 📄 License
Released under the MIT License. Built for the OSRS quantitative merchant community.
