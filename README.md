# Graduation Project  
## K–Amplitude Dependent Band Structure Analysis

This repository contains Python post-processing scripts developed for my undergraduate
graduation project in **Engineering Mechanics**.

The scripts are mainly used to analyze **k–amplitude dependent band structures**
exported from **COMSOL Multiphysics**, including data cleaning, real-part extraction
of complex values, and visualization of band diagrams.

---

## 📌 Project Background

Mechanical metamaterials often exhibit band-gap characteristics that depend on
structural parameters and excitation amplitude.  
In this project, COMSOL is used to compute band structures under different amplitude
conditions, and Python is employed for systematic post-processing and visualization.

This repository focuses on the **data processing and analysis stage** of the workflow.

---
##    Project Progress
---

## 📂 Repository Structure

```text
graduation_project/
├── k_amp_analyse.py      # Main post-processing script (version 1)
├── k_amp_analyse2.py     # Improved version with extended analysis (version 2)
└── README.md
```
---

Requirements
- Python 3.x
- numpy
- pandas
- matplotlib

Usage
- Export band structure data from COMSOL as a CSV file
- Place the CSV file in the same directory as the script
- Modify the CSV file path in the script if necessary
- Run the script:
      python k_amp_analyse.py

Output
The scripts will automatically:
- Clean raw CSV data (including comment lines)
- Convert complex numbers (e.g. COMSOL i format) and extract real parts
- Organize band data by amplitude
- Generate band structure plots

Output files are saved to the automatically created post_out/ directory.

Versions
- v1: Initial implementation of k–amplitude band analysis
- v2: Improved robustness and extended post-processing logic

Author
- XuanCheng Su
- Undergraduate Student, Engineering Mechanics
