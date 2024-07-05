import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import time
import threading
import csv
import datetime
import os
import pygame

# Initialize pygame for sound playback
pygame.mixer.init()

class JobReminderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Job Reminder App")
        self.geometry("400x300")
        self.configure(bg='white')
        
        self.progress_file = "progress.txt"
        self.tasks_file = "tasks.txt"
        self.log_file = "log.txt"
        
        self.create_ui()
        
        # Load tasks
        self.load_tasks()
        
        # Prompt user immediately
        self.ask_user_progress()
        
        # Schedule the hourly reminder
        self.schedule_hourly_reminder()
    
    def create_ui(self):
        label = tk.Label(self, text="Job Reminder App", font=("Helvetica", 16), bg='white')
        label.pack(pady=10)
        
        self.volume_slider = ttk.Scale(self, from_=0, to_=1, orient="horizontal", command=self.slider_callback)
        self.volume_slider.set(0.5)  # Default volume
        self.volume_slider.pack(pady=10)
        
        volume_label = tk.Label(self, text="Volume", font=("Helvetica", 12), bg='white')
        volume_label.pack(pady=5)
    
    def set_volume(self, val):
        volume = float(val)
        pygame.mixer.music.set_volume(volume)
    
    def slider_callback(self, val):
        self.set_volume(val)
        self.play_beep()
    
    def schedule_hourly_reminder(self):
        self.after(1000, self.check_hourly_reminder)
    
    def check_hourly_reminder(self):
        current_minute = datetime.datetime.now().minute
        if current_minute == 0:  # Every hour
            self.remind_user()
        self.after(60000, self.check_hourly_reminder)  # Check every minute
    
    def remind_user(self):
        self.play_beep()
        self.ask_user_progress()
    
    def play_beep(self):
        pygame.mixer.music.load("beep.wav")
        pygame.mixer.music.play()
    
    def ask_user_progress(self):
        answer = simpledialog.askstring("Reminder", "Go find a job!!\n\nWhat have you done today to look for work?")
        if answer:
            self.log_progress(answer)
            self.update_tasks(answer)
            self.log_entry(answer)
            self.check_for_time_wasting(answer)
            self.suggest_tasks(answer)
    
    def log_progress(self, answer):
        now = datetime.datetime.now()
        with open(self.progress_file, "a") as file:
            writer = csv.writer(file)
            writer.writerow([now.strftime("%H:%M"), now.strftime("%Y-%m-%d"), answer])
    
    def load_tasks(self):
        self.tasks = {}
        if os.path.exists(self.tasks_file) and os.path.getsize(self.tasks_file) > 0:
            with open(self.tasks_file, "r") as file:
                reader = csv.reader(file)
                for row in reader:
                    if row:
                        task = row[0]
                        synonyms = row[1:-1]
                        count = int(row[-1])
                        self.tasks[task] = (synonyms, count)
        else:
            self.initialize_tasks()
    
    def initialize_tasks(self):
        tasks = {
            "follow up with recruiters": ["follow up", "contact recruiters", "email recruiters"],
            "update resume": ["update resume", "revise resume", "edit resume"],
            "apply for unemployment": ["apply for unemployment", "unemployment application"],
            "practice for interviews": ["practice for interviews", "interview practice", "mock interviews"],
            "practice SQL": ["practice SQL", "SQL practice", "learning SQL", "study SQL", "SQL stuff"],
            "practice FIX": ["practice FIX", "FIX practice", "learning FIX", "study FIX"],
            "practice DEV": ["practice DEV", "DEV practice", "learning DEV", "study DEV"]
        }
        with open(self.tasks_file, "w") as file:
            writer = csv.writer(file)
            for task, synonyms in tasks.items():
                writer.writerow([task] + synonyms + [0])
        self.load_tasks()
    
    def update_tasks(self, answer):
        matched_task = None
        for task, (synonyms, count) in self.tasks.items():
            for synonym in synonyms:
                if synonym in answer:
                    matched_task = task
                    break
            if matched_task:
                break
        
        if matched_task:
            self.tasks[matched_task] = (self.tasks[matched_task][0], self.tasks[matched_task][1] + 1)
            self.save_tasks()
    
    def save_tasks(self):
        with open(self.tasks_file, "w") as file:
            writer = csv.writer(file)
            for task, (synonyms, count) in self.tasks.items():
                writer.writerow([task] + synonyms + [count])
    
    def log_entry(self, answer):
        now = datetime.datetime.now()
        with open(self.log_file, "a") as file:
            file.write(f"{now.strftime('%H:%M')}, {now.strftime('%Y-%m-%d')}, {answer}\n")
    
    def check_for_time_wasting(self, answer):
        time_wasting_activities = [
            "watching YouTube", "watching movie", "playing with cat", "doing YouTube videos",
            "working on the yard", "flying my drone"
        ]
        if any(activity in answer for activity in time_wasting_activities):
            self.show_progress_report()
    
    def show_progress_report(self):
        progress = []
        if os.path.exists(self.progress_file) and os.path.getsize(self.progress_file) > 0:
            with open(self.progress_file, "r") as file:
                reader = csv.reader(file)
                progress = list(reader)
        
        if progress:
            report = "\n".join([f"{row[1]} {row[0]}: {row[2]}" for row in progress])
            messagebox.showinfo("Progress Report", f"Here's what you've done so far:\n{report}\n\nTime is running out!")
    
    def suggest_tasks(self, answer):
        mentioned_tasks = [task for task, (synonyms, count) in self.tasks.items() if any(syn in answer for syn in synonyms)]
        unmentioned_tasks = [task for task in self.tasks if task not in mentioned_tasks]
        
        suggestions = "\n".join(unmentioned_tasks)
        if unmentioned_tasks:
            messagebox.showinfo("Suggestions", f"Don't forget to also do:\n{suggestions}")
        
        frequent_task = max(self.tasks, key=lambda t: self.tasks[t][1])
        if frequent_task in mentioned_tasks and len(unmentioned_tasks) > 0:
            messagebox.showinfo("Reminder", f"You've been doing {frequent_task} a lot. Don't forget about {unmentioned_tasks[0]}")
    
if __name__ == "__main__":
    app = JobReminderApp()
    app.mainloop()
