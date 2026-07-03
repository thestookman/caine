#caine
Hello; this is caine. This is my second version so it is not self taught YET but its pretty fun.
I dont care if u use my cerebra api like i genuinly dont care u shud prob get ur own bc its free but ok.
YOU MUST NEED PYTHON3 FOR THIS.

# How to Run Caine (v2)

Follow these steps to set up your environment, configure your free Cerebras API key, and launch Caine.

## 1. Setup Your Environment Variables
You must set your Cerebras API key so Caine can communicate with the inference engine. Run the command below that matches your operating system.

### macOS and Linux
```bash
export CEREBRAS_API_KEY="your_api_key_here"
```

### Windows (Command Prompt)
```cmd
set CEREBRAS_API_KEY="your_api_key_here"
```

### Windows (PowerShell)
```powershell
\$env:CEREBRAS_API_KEY="your_api_key_here"
```

### Local Configuration Option
Alternatively, create a file named `.env` in your root project folder and add your key:
```env
CEREBRAS_API_KEY=your_api_key_here
```

## 2. Install Required Dependencies
Before running the application, ensure all required software packages and libraries are installed.

### Python Environment
```bash
pip install -r requirements.txt
```

### Node.js Environment
```bash
npm install
```

## 3. Launch Caine
Execute the main entry script to start running the application.

### If built with Python
```bash
python main.py
```

### If built with Node.js
```bash
node index.js
```
