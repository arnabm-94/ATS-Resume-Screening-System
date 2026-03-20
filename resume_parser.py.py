import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import re
import shutil
import pdfplumber
from docx import Document
import threading

def read_file(file_path):
    extension = os.path.splitext(file_path)[1].lower()
    try:
        if extension == '.pdf':
            return read_pdf(file_path)
        elif extension == '.docx':
            return read_docx(file_path)
        elif extension == '.txt':
            return read_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {extension}")
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return ""

def read_pdf(file_path):
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error reading PDF file {file_path}: {e}")
    return text

def read_docx(file_path):
    text = ""
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX file {file_path}: {e}")
    return text

def read_txt(file_path):
    text = ""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
    except Exception as e:
        print(f"Error reading TXT file {file_path}: {e}")
    return text

def extract_keywords(text):
    text = text.lower()
    words = re.findall(r'\b[a-z]+\b', text)
    stop_words = set([
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'but', 'by', 'for', 'if', 'in', 
        'into', 'is', 'it', 'no', 'not', 'of', 'on', 'or', 'such', 'that', 'the', 
        'their', 'then', 'there', 'these', 'they', 'this', 'to', 'was', 'will', 
        'with'
    ])
    keywords = [word for word in words if word not in stop_words]
    return set(keywords)

def calculate_match(job_description_keywords, resume_keywords):
    if not job_description_keywords:
        return 0,set()

    match_keywords = job_description_keywords.intersection(resume_keywords)
    match_percentage = (len(match_keywords) / len(job_description_keywords)) * 100
    return match_percentage, match_keywords

def process_resumes(job_description_path, resumes_folder_path, threshold, progress_var, status_var):
    job_description = read_file(job_description_path)
    job_description_keywords = extract_keywords(job_description)
    
    files = [f for f in os.listdir(resumes_folder_path) if os.path.isfile(os.path.join(resumes_folder_path, f))]
    total_files = len(files)
    matching_resumes = []
    
    if total_files == 0:
        status_var.set("No resumes found.")
        return matching_resumes
    
    #Create SELECTED RESUMES FOLDER
    selected_folder = os.path.join(resumes_folder_path, "SELECTED RESUMES")
    os.makedirs(selected_folder, exist_ok= True)

    for idx, filename in enumerate(files):
        file_path = os.path.join(resumes_folder_path, filename)
        
        #SKIP the SELECTED RESUMES folder itself 
        if filename == "SELECTED RESUMES":
            continue
        
        try:
            resume = read_file(file_path)
            resume_keywords = extract_keywords(resume)
            match_percentage, _ = calculate_match(job_description_keywords, resume_keywords)
            
            if match_percentage >= threshold:
                matching_resumes.append((filename, match_percentage))
                
                #COPY file to SELECTED RESUMES folder
                destination_path = os.path.join(selected_folder, filename)
                
                #Avoid Overwriting
                if not os.path.exists(destination_path):
                    shutil.copy2(file_path, destination_path)
                
        except ValueError as e:
            print(f"Skipping file {filename}: {e}")
        
        # Update the progress bar
        progress_var.set((idx + 1) / total_files * 100)
        root.update_idletasks()
    
    status_var.set("Processing complete.")
    return matching_resumes

def run_analysis():
    job_description_path = job_description_var.get()
    resumes_folder_path = resumes_folder_var.get()
    
    if not os.path.exists(job_description_path) or not os.path.isdir(resumes_folder_path):
        messagebox.showerror("Error", "Please provide valid file paths.")
        return
    
    threshold = int(threshold_var.get())
    progress_var.set(0)
    status_var.set("Processing...")
    
    # Run the processing in a separate thread to avoid freezing the UI
    threading.Thread(target=process_and_display_results, args=(job_description_path, resumes_folder_path, threshold)).start()

def process_and_display_results(job_description_path, resumes_folder_path, threshold):
    matching_resumes = process_resumes(job_description_path, resumes_folder_path, threshold, progress_var, status_var)
    
    # Display results after processing is complete
    results = "\n".join(f"{resume}: {percentage:.2f}%" for resume, percentage in matching_resumes) if matching_resumes else "No resumes match the threshold."
    
    # Use `after` to update the UI with results after the thread finishes
    root.after(0, lambda: messagebox.showinfo("Analysis Result", results))

# GUI Setup
root = tk.Tk()
root.title("Application Tracking System")

tk.Label(root, text="Job Description File:").pack(padx=10, pady=5)
job_description_var = tk.StringVar()
tk.Entry(root, textvariable=job_description_var, width=50).pack(padx=10, pady=5)
tk.Button(root, text="Browse", command=lambda: job_description_var.set(filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("PDF files", "*.pdf"), ("Word files", "*.docx")]))).pack(padx=10, pady=5)

tk.Label(root, text="Resumes Folder:").pack(padx=10, pady=5)
resumes_folder_var = tk.StringVar()
tk.Entry(root, textvariable=resumes_folder_var, width=50).pack(padx=10, pady=5)
tk.Button(root, text="Browse", command=lambda: resumes_folder_var.set(filedialog.askdirectory())).pack(padx=10, pady=5)

tk.Label(root, text="Match Threshold (%):").pack(padx=10, pady=5)
threshold_var = tk.StringVar(value="30")
tk.Entry(root, textvariable=threshold_var, width=10).pack(padx=10, pady=5)

tk.Button(root, text="Run Analysis", command=run_analysis).pack(padx=10, pady=20)

# Progress Bar
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(root, variable=progress_var, maximum=100, length=400)
progress_bar.pack(padx=10, pady=5)

# Status Label
status_var = tk.StringVar(value="Ready")
status_label = tk.Label(root, textvariable=status_var)
status_label.pack(padx=10, pady=5)

root.mainloop()
