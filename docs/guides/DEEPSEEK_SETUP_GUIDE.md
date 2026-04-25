# DeepSeek Integration Setup Guide

## Current Status

✅ **Working:**
- All DeepSeek modules imported successfully
- Directories created
- Configuration valid
- Activation script ready
- Ollama server running

⚠️ **Needs Attention:**
- DeepSeek model not loaded in Ollama

## Quick Fix (5 minutes)

### Option 1: Load DeepSeek in Ollama (Recommended)

```bash
# Pull the DeepSeek Coder model
ollama pull deepseek-coder:6.7b

# Verify it's loaded
ollama list
```

### Option 2: Use Alternative Model

If DeepSeek is too large, you can use a smaller coding model:

```bash
# Option A: CodeLlama (smaller, faster)
ollama pull codellama:7b

# Option B: Mistral (general purpose)
ollama pull mistral:7b

# Option C: Phi-3 (very small, fast)
ollama pull phi3:mini
```

Then update the config in `ACTIVATE_DEEPSEEK_ENGINEER.py`:
```python
config = DeepSeekConfig(
    model_name="codellama:7b",  # or "mistral:7b" or "phi3:mini"
    # ... rest of config
)
```

## Full Setup Instructions

### 1. Install Ollama

**Windows:**
- Download from: https://ollama.com/download
- Run installer
- Ollama will start automatically

**Verify Installation:**
```bash
ollama --version
```

### 2. Pull DeepSeek Model

```bash
# Full model (recommended for best results)
ollama pull deepseek-coder:6.7b

# Or smaller variant if disk space is limited
ollama pull deepseek-coder:1.3b
```

**Model Sizes:**
- `deepseek-coder:1.3b` - 1.3B params, ~800MB, fast
- `deepseek-coder:6.7b` - 6.7B params, ~4GB, balanced
- `deepseek-coder:33b` - 33B params, ~20GB, best quality

### 3. Verify Model is Running

```bash
# List all models
ollama list

# Test the model
ollama run deepseek-coder:6.7b "Write a Python function to add two numbers"
```

### 4. Run Validation

```bash
py validate_deepseek.py
```

You should see all checks pass.

### 5. Activate DeepSeek Engineer

```bash
py ACTIVATE_DEEPSEEK_ENGINEER.py
```

## Alternative Inference Servers

### LM Studio (GUI-based, easier for beginners)

1. Download from: https://lmstudio.ai/
2. Install and launch
3. Go to "Search" tab
4. Search for "deepseek-coder"
5. Download model
6. Go to "Local Server" tab
7. Load model and start server
8. Update endpoint in config:
   ```python
   config = DeepSeekConfig(
       backend=InferenceBackend.LM_STUDIO,
       endpoint="http://localhost:1234/v1/chat/completions"
   )
   ```

### TextGen WebUI (Advanced users)

```bash
# Clone repo
git clone https://github.com/oobabooga/text-generation-webui
cd text-generation-webui

# Install
pip install -r requirements.txt

# Download model through UI
python server.py

# Update config
config = DeepSeekConfig(
    backend=InferenceBackend.TEXTGEN_WEBUI,
    endpoint="http://localhost:5000/api/v1/generate"
)
```

## Configuration Options

### Sandbox Mode (Recommended for first run)

```python
config = DeepSeekConfig(
    sandbox_mode=True,        # Changes are simulated, not applied
    require_approval=True,    # Human approval for all changes
    auto_commit_safe_changes=False  # Don't auto-apply anything
)
```

### Development Mode (Faster iteration)

```python
config = DeepSeekConfig(
    sandbox_mode=False,       # Apply changes directly
    require_approval=False,   # Auto-apply safe changes
    auto_commit_safe_changes=True  # Commit safe changes automatically
)
```

### Production Mode (Maximum safety)

```python
config = DeepSeekConfig(
    sandbox_mode=True,
    require_approval=True,
    auto_commit_safe_changes=False,
    safeguard_config={
        "rules": [
            {"keyword": "import os"},
            {"keyword": "import subprocess"},
            {"keyword": "exec("},
            {"keyword": "eval("}
        ]
    }
)
```

## Troubleshooting

### Issue: "Ollama not found"

**Solution:**
```bash
# Windows: Add to PATH
# Or use full path
"C:\Program Files\Ollama\ollama.exe" serve
```

### Issue: "Model not found"

**Solution:**
```bash
# List available models
ollama list

# Pull the model
ollama pull deepseek-coder:6.7b
```

### Issue: "Connection refused"

**Solution:**
```bash
# Start Ollama server
ollama serve

# Or restart Ollama service
# Windows: Services -> Ollama -> Restart
```

### Issue: "Out of memory"

**Solution:**
```bash
# Use smaller model
ollama pull deepseek-coder:1.3b

# Or use quantized version
ollama pull deepseek-coder:6.7b-q4_0
```

### Issue: "Slow inference"

**Solutions:**
1. Use smaller model: `deepseek-coder:1.3b`
2. Use quantized model: `deepseek-coder:6.7b-q4_0`
3. Reduce max_tokens in config: `max_tokens=1024`
4. Increase temperature for faster sampling: `temperature=0.5`

## Performance Tips

### Optimize for Speed

```python
config = DeepSeekConfig(
    model_name="deepseek-coder:1.3b",  # Smaller model
    temperature=0.5,                    # Faster sampling
    max_tokens=1024,                    # Shorter responses
    timeout=60                          # Lower timeout
)
```

### Optimize for Quality

```python
config = DeepSeekConfig(
    model_name="deepseek-coder:6.7b",  # Larger model
    temperature=0.1,                    # More deterministic
    max_tokens=4096,                    # Longer responses
    timeout=300                         # Higher timeout
)
```

## Usage Examples

### Single Cycle

```bash
py ACTIVATE_DEEPSEEK_ENGINEER.py
# Select option 1: Single Cycle
```

### Continuous Operation

```bash
py ACTIVATE_DEEPSEEK_ENGINEER.py
# Select option 2: Continuous (24-hour cycles)
```

### Custom Interval

```bash
py ACTIVATE_DEEPSEEK_ENGINEER.py
# Select option 3: Custom Continuous
# Enter hours: 6
# Enter max cycles: 10
```

## Safety Features

1. **Sandbox Mode**: All changes simulated first
2. **Rollback Snapshots**: Automatic backups before changes
3. **Read-Only Protection**: Critical files protected
4. **Change Monitoring**: All changes logged
5. **Approval System**: Human review for critical changes
6. **Safety Scoring**: Automatic risk assessment
7. **Test Coverage**: Minimum coverage requirements
8. **RBAC**: Role-based access control

## Next Steps

1. ✅ Run validation: `py validate_deepseek.py`
2. ✅ Load DeepSeek model: `ollama pull deepseek-coder:6.7b`
3. ✅ Test inference: `ollama run deepseek-coder:6.7b "test"`
4. ✅ Activate engineer: `py ACTIVATE_DEEPSEEK_ENGINEER.py`
5. ✅ Monitor logs: Check `logs/deepseek/` directory

## Support

- Ollama Docs: https://ollama.com/docs
- DeepSeek Docs: https://github.com/deepseek-ai/DeepSeek-Coder
- Issues: Check `logs/deepseek/` for detailed error logs
