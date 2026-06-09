import sqlite3
import time
import os
from typing import Optional, Tuple
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

class EnergyCostTracer:
    def __init__(self, db_path: str = "energy_cost.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize the SQLite database with the required schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS energy_logs (
                    timestamp REAL,
                    operation_type TEXT,
                    file_path TEXT,
                    energy_cost_before REAL,
                    energy_cost_after REAL,
                    duration_ms REAL
                )
            """)
            conn.commit()
    
    def log_operation(self, operation_type: str, file_path: str, 
                     energy_cost_before: float, energy_cost_after: float, 
                     duration_ms: float):
        """
        Log an operation with energy consumption data.
        
        Args:
            operation_type: Type of operation (file_write, commit, code_run)
            file_path: Path to the file being modified
            energy_cost_before: Energy cost before operation (0-1)
            energy_cost_after: Energy cost after operation (0-1)
            duration_ms: Duration of operation in milliseconds
        """
        timestamp = time.time()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO energy_logs 
                (timestamp, operation_type, file_path, energy_cost_before, 
                 energy_cost_after, duration_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (timestamp, operation_type, file_path, energy_cost_before, 
                  energy_cost_after, duration_ms))
            conn.commit()
    
    def plot_energy_trends(self, output_path: Optional[str] = None):
        """
        Plot energy trends per operation type over time.
        
        Args:
            output_path: Path to save the plot image. If None, displays the plot.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, operation_type, energy_cost_after - energy_cost_before 
                FROM energy_logs 
                ORDER BY timestamp
            """)
            results = cursor.fetchall()
        
        if not results:
            print("No data to plot")
            return
        
        # Organize data by operation type
        data_by_type = {}
        for timestamp, op_type, energy_diff in results:
            if op_type not in data_by_type:
                data_by_type[op_type] = {'timestamps': [], 'energy_diffs': []}
            data_by_type[op_type]['timestamps'].append(
                datetime.fromtimestamp(timestamp))
            data_by_type[op_type]['energy_diffs'].append(energy_diff)
        
        # Create the plot
        plt.figure(figsize=(12, 6))
        for op_type, data in data_by_type.items():
            plt.plot(data['timestamps'], data['energy_diffs'], 
                    marker='o', label=op_type)
        
        plt.xlabel('Time')
        plt.ylabel('Energy Cost Difference')
        plt.title('Energy Consumption by Operation Type Over Time')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Format x-axis dates
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.gca().xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        if output_path:
            plt.savefig(output_path)
            plt.close()
        else:
            plt.show()

# Example usage:
# tracer = EnergyCostTracer()
# tracer.log_operation("file_write", "/path/to/file.py", 0.2, 0.25, 150.0)
# tracer.plot_energy_trends("energy_trends.png")