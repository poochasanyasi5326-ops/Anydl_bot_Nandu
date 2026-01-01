def progress_bar(current, total):
    percent = int(current * 100 / total)
    return f"⬇️ {percent}%"
