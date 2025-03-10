# Experimental Evaluation of SAT Solvers & MWSAT Optimization  

This repository contains homework assignments and a final project for a NI-KOP course.  

## 📌 Overview  

### 1️⃣ [Experimental Evaluation of GSAT and ProbSAT](./uloha_1/)  
📄 **For detailed analysis and results, see the full report:** [KOP_uloha_1.pdf](./uloha_1/KOP_uloha_1.pdf) 
- Conducted an experimental comparison of two local search SAT solvers: **GSAT (Greedy SAT)** and **ProbSAT (Probabilistic SAT)**.  
- Analyzed performance based on:  
  - **Average number of steps** taken to find a solution.  
  - **Weighted success rate**, penalizing unsuccessful runs.  
  - **Scalability** with increasing problem size (20–75 variables).  
- Found that **ProbSAT outperformed GSAT**, especially on larger instances.  

---

### 2️⃣ [MWSAT Optimization Using Simulated Annealing](./project/) 
📄 **For detailed analysis and results, see the full report:** [KOP_uloha_2.pdf](./project/KOP_uloha_2.pdf) 
- Implemented a heuristic solver for the **Maximum Weighted Satisfiability Problem (MWSAT)**.  
- Used **Simulated Annealing**, an optimization method that balances exploration and exploitation.  
- Designed a **fitness function** to maximize variable weights while satisfying as many clauses as possible.  
- Evaluated the solver’s performance on instances with **20–50 variables**, demonstrating its effectiveness in finding near-optimal solutions.  

---
