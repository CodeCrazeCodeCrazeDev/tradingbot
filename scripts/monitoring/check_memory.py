import psutil

mem = psutil.virtual_memory()
print(f"Total RAM: {mem.total / (1024**3):.2f} GB")
print(f"Available RAM: {mem.available / (1024**3):.2f} GB")
print(f"Used RAM: {mem.used / (1024**3):.2f} GB")
print(f"Free RAM: {mem.free / (1024**3):.2f} GB")
print(f"RAM Usage: {mem.percent}%")
print()
print("Top 10 Memory-Consuming Processes:")
for proc in sorted(psutil.process_iter(['name', 'memory_info']), key=lambda p: p.info['memory_info'].rss, reverse=True)[:10]:
    try:
        print(f"  {proc.info['name']}: {proc.info['memory_info'].rss / (1024**2):.2f} MB")
    except:
        pass
