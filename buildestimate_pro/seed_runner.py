import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from scripts.seed_database import seed
seed()
print("Seeded successfully")
