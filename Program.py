import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3
import datetime
from matplotlib import pyplot as plt


class HabitTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Habit Tracker")
        self.root.geometry("900x650")

        # Database setup
        self.db_setup()

        # Title
        tk.Label(self.root, text="Habit Tracker", font=("Arial", 20, "bold")).pack(pady=10)
        footer_label = tk.Label(self.root, text="Created by Hassan Ahmed, for the Hack Club", font=("Helvetica", 12), bg="#87CEEB", fg="white")
        footer_label.pack(pady=20)
        # Habit Input Frame
        self.input_frame = tk.Frame(self.root)
        self.input_frame.pack(pady=10)

        tk.Label(self.input_frame, text="Habit:").grid(row=0, column=0, padx=5, pady=5)
        self.habit_entry = tk.Entry(self.input_frame, width=30)
        self.habit_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(self.input_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5)
        self.category_entry = tk.Entry(self.input_frame, width=20)
        self.category_entry.grid(row=0, column=3, padx=5, pady=5)

        tk.Button(self.input_frame, text="Add Habit", command=self.add_habit, bg="#4CAF50", fg="white").grid(
            row=0, column=4, padx=5, pady=5
        )

        # Habit List
        self.tree = ttk.Treeview(
            self.root, columns=("Habit", "Category", "Streak", "Status"), show="headings", height=10
        )
        self.tree.heading("Habit", text="Habit")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Streak", text="Streak")
        self.tree.heading("Status", text="Status")
        self.tree.pack(pady=10)

        self.refresh_habit_list()

        # Buttons
        tk.Button(self.root, text="Mark as Complete", command=self.mark_complete, bg="#2196F3", fg="white").pack(
            pady=5
        )
        tk.Button(self.root, text="Show Weekly Insights", command=self.show_weekly_insights, bg="#FF9800", fg="white").pack(
            pady=5
        )
        tk.Button(self.root, text="Export Data", command=self.export_data, bg="#9C27B0", fg="white").pack(pady=5)
        tk.Button(self.root, text="Import Data", command=self.import_data, bg="#673AB7", fg="white").pack(pady=5)
        tk.Button(self.root, text="Send Daily Reminder", command=self.send_reminder, bg="#009688", fg="white").pack(
            pady=5
        )

    def db_setup(self):
        """Initializes the database and ensures columns exist."""
        self.conn = sqlite3.connect("habits.db")
        self.cursor = self.conn.cursor()

        # Check if the table exists and contains all necessary columns
        self.cursor.execute("PRAGMA table_info(habits)")
        columns = [info[1] for info in self.cursor.fetchall()]

        # If table is missing or does not contain all required columns, recreate it
        if not columns or "category" not in columns:
            self.cursor.execute("DROP TABLE IF EXISTS habits")
            self.cursor.execute(
                """
                CREATE TABLE habits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    habit TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'General',
                    date DATE NOT NULL,
                    streak INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL
                )
            """
            )
        self.conn.commit()

    def add_habit(self):
        """Adds a new habit."""
        habit = self.habit_entry.get()
        category = self.category_entry.get() or "General"

        if not habit.strip():
            messagebox.showerror("Error", "Habit cannot be empty.")
            return

        today = datetime.date.today()
        self.cursor.execute(
            "INSERT INTO habits (habit, category, date, streak, status) VALUES (?, ?, ?, ?, ?)",
            (habit, category, today, 0, "Incomplete"),
        )
        self.conn.commit()
        self.refresh_habit_list()
        self.habit_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)
        messagebox.showinfo("Success", f"Habit '{habit}' added!")

    def refresh_habit_list(self):
        """Refreshes the habit list in the TreeView."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        today = datetime.date.today()
        self.cursor.execute("SELECT habit, category, streak, status FROM habits WHERE date = ?", (today,))
        for row in self.cursor.fetchall():
            self.tree.insert("", tk.END, values=row)

    def mark_complete(self):
        """Marks a habit as complete."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "Please select a habit to mark as complete.")
            return

        habit = self.tree.item(selected_item, "values")[0]
        today = datetime.date.today()

        # Update streak and mark as complete
        self.cursor.execute(
            """
            UPDATE habits
            SET streak = streak + 1, status = 'Complete'
            WHERE habit = ? AND date = ?
            """,
            (habit, today),
        )
        self.conn.commit()
        self.refresh_habit_list()
        messagebox.showinfo("Success", f"Habit '{habit}' marked as complete!")

    def show_weekly_insights(self):
        """Displays a graph showing weekly insights."""
        one_week_ago = datetime.date.today() - datetime.timedelta(days=7)
        self.cursor.execute(
            """
            SELECT habit, SUM(streak) FROM habits
            WHERE date >= ? AND status = 'Complete'
            GROUP BY habit
            """,
            (one_week_ago,),
        )
        data = self.cursor.fetchall()

        if not data:
            messagebox.showinfo("No Data", "No data available for the past week.")
            return

        habits, streaks = zip(*data)
        plt.figure(figsize=(8, 5))
        plt.bar(habits, streaks, color="#4CAF50")
        plt.title("Weekly Habit Insights")
        plt.xlabel("Habits")
        plt.ylabel("Streaks")
        plt.show()

    def export_data(self):
        """Exports habit data to a CSV file."""
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return

        with open(file_path, "w") as file:
            self.cursor.execute("SELECT * FROM habits")
            rows = self.cursor.fetchall()
            file.write("id,habit,category,date,streak,status\n")
            for row in rows:
                file.write(",".join(map(str, row)) + "\n")

        messagebox.showinfo("Success", "Data exported successfully!")

    def import_data(self):
        """Imports habit data from a CSV file."""
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return

        with open(file_path, "r") as file:
            next(file)  # Skip header
            for line in file:
                data = line.strip().split(",")
                self.cursor.execute(
                    "INSERT INTO habits (id, habit, category, date, streak, status) VALUES (?, ?, ?, ?, ?, ?)",
                    data,
                )
        self.conn.commit()
        self.refresh_habit_list()
        messagebox.showinfo("Success", "Data imported successfully!")

    def send_reminder(self):
        """Sends a reminder for incomplete habits."""
        today = datetime.date.today()
        self.cursor.execute("SELECT habit FROM habits WHERE status = 'Incomplete' AND date = ?", (today,))
        incomplete_habits = [row[0] for row in self.cursor.fetchall()]
        if incomplete_habits:
            messagebox.showinfo("Reminder", f"Don't forget to complete your habits: {', '.join(incomplete_habits)}")
        else:
            messagebox.showinfo("All Done", "Great job! All habits are complete for today.")

    def __del__(self):
        """Closes the database connection."""
        self.conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = HabitTracker(root)
    root.mainloop()
