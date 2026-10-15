"""
AIP444 Assignment 1: AI Code Review 
Author: Wenjun Wei
Student ID: 169010238
Program: Computer Programming and Analysis
Description: A multi-agent CLI code review tool supporting Git Mode and File Mode. 
             It utilizes parallel specialized reviewers (The Security Auditor and The Maintainability Critic) 
             equipped with local file reading and ripgrep tools, whose findings are validated and 
             synthesized by a Lead Developer (Judge) model to generate a professional, self-contained HTML report.
"""

import sys
from typing import List
import math

def calculate_total(prices: List[float]) -> int:
    x = 0.0
    for p in prices:
        x += p
    return x

def main():
    api_key = "sk-12345-abcde-secret-key"

    print(f"Value of pi is: {math.pi}")

    total = calculate_total([10.50, 20.00, 5.25])
    print(f"Total: {total}")

if __name__ == "__main__":
    main()