# Legal Compliance and Integration Feasibility Report: London Strategic Edge Datasets

This report evaluates the legal feasibility of integrating the free and API datasets provided by **London Strategic Edge (LSE)** into **AlphaAlgo**.

---

## Part 1: Legal Compliance Analysis

Based on the official **London Strategic Edge Terms of Service** (last updated **19 January 2026**), we have performed a thorough review of the licensing and usage constraints. The relevant sections are quoted and analyzed below.

### 1. Machine Learning Model Training
* **Status:** **Prohibited/Ambiguous**
* **ToS Analysis (Section 7 - Intellectual Property):**
  > *"All content, features, and functionality of the platform—including but not limited to text, graphics, logos, icons, software, and **data compilations**—are owned by London Strategic Edge or our licensors and are protected by intellectual property laws. **You may not copy, modify, distribute, or create derivative works without our express written consent.**"*
* **ToS Analysis (Section 6 - Acceptable Use):**
  > *"You agree not to: [...] **Scrape, harvest, or extract data without permission**"*
* **Implication:** Training a machine learning model on these data compilations constitutes the creation of a *derivative work* and copying/extraction of the data. Under standard terms, this is prohibited without express written consent.

### 2. Commercial Use
* **Status:** **Explicitly Prohibited**
* **ToS Analysis (Section 6 - Acceptable Use):**
  > *"You agree not to: [...] **Redistribute, resell, or commercially exploit our data or services**"*
* **Implication:** AlphaAlgo cannot utilize LSE datasets for any commercial trading lines or commercial SaaS/enterprise deployment under the default ToS.

### 3. Internal Research Use
* **Status:** **Ambiguous / Conditionally Permitted**
* **ToS Analysis (Section 2 - Description of Services):**
  > *"Our platform is designed for **informational and educational purposes**."*
* **Implication:** While educational and informational use is permitted on the platform, automated or programmatic ingestion of bulk datasets into an external platform (like AlphaAlgo) for algorithmic validation is blocked by Section 6 (Acceptable Use) which forbids automated systems.

### 4. Redistribution or Derived Datasets
* **Status:** **Explicitly Prohibited**
* **ToS Analysis (Section 6 & 7):**
  Redistribution and reselling are directly prohibited under Section 6. The creation of derivative datasets is prohibited under Section 7:
  > *"You may not copy, modify, distribute, or create derivative works without our express written consent."*

### 5. Automated System Access (API & Downloads)
* **Status:** **Explicitly Prohibited without Permission**
* **ToS Analysis (Section 6 - Acceptable Use):**
  > *"You agree not to: [...] **Use automated systems to access the platform without our permission**"*
* **Implication:** Even if an API Key is obtained, programmatically automating bulk data pulls for algorithmic execution is technically a violation of this provision unless LSE has granted explicit automated platform permission.

---

## Part 2: Official Questions for London Strategic Edge

Since the standard license terms are **restrictive and ambiguous** for automated institutional research, we have **stopped implementation of the ingestion pipeline** to prevent any Terms of Service violation.

The following list of legal and technical questions should be sent to the **London Strategic Edge** support/licensing team (`support@londonstrategicedge.com`) to seek an enterprise waiver or custom data license agreement before any integration proceeds.

### Legal & Licensing Questions
1. **Machine Learning Model Training:** Does the "free key" or REST API license permit the ingestion and processing of your 133 billion ticks/118,000 datasets for the exclusive purpose of training offline machine learning models (e.g., LSTMs, XGBoost, and Reinforcement Learning estimators) inside our proprietary trading system, provided no raw data is redistributed?
2. **Commercial Exploitation Boundary:** While Section 6 prohibits "commercially exploiting your data or services," does this restriction apply strictly to the resale/redistribution of the data itself, or does it also prohibit using signals/edges trained on your data to execute trades in live proprietary trading accounts?
3. **Definition of Derivative Works:** If our system processes your raw ticks to compute custom informational features (such as Transfer Entropy, Conditional Mutual Information, or causal coefficients) and stores only these aggregate features, does London Strategic Edge classify these statistical features as "derivative works" requiring express written consent?
4. **Internal Non-Commercial Research:** Can London Strategic Edge grant an explicit, written waiver for our research platform to use your datasets for internal, non-commercial research, backtesting, and hypothesis-falsification loops?
5. **Automated Platform Ingestion:** Since Section 6 forbids using "automated systems to access the platform without our permission," does the issuance of an API Key (`lse_live_...`) constitute "express permission" to programmatically automate downloads via the REST API within your published rate limits (100 calls/minute, 2 exports/hour), or must we obtain separate written authorization?

### Technical & Integration Parameters
If LSE grants the necessary legal permissions, we will request clarification on the following operational endpoints:
1. **Data Lake Storage and Formats:** Are there specific file schema specifications for your bulk Parquet/Arrow export jobs? Can we store these unchanged in our immutable local cache?
2. **Checksum Integrity:** Does your file export endpoint supply a SHA-256 or MD5 checksum in the HTTP response headers (e.g., `ETag` or custom headers) to programmatically verify that downloaded files have not been corrupted during transfer?
3. **Rate Limit Headers:** Does the REST API send back standard rate limit tracking headers (such as `X-RateLimit-Limit`, `X-RateLimit-Remaining`, or `Retry-After`) to allow our client to programmatically sleep and avoid `429 Too Many Requests` faults?
