<div align="center">
  <img src="frontend/src/app/icon.svg" alt="Raven Logo" width="120"/>
  <h1>Raven</h1>
  <p><strong>Advanced Open Source Intelligence Framework</strong></p>
</div>

---

Raven is a highly concurrent, multi-faceted Open Source Intelligence (OSINT) platform. It allows investigators to run deep intelligence collection across thousands of sources instantly using either a lightning-fast Command Line Interface or an interactive, node-based Web Dashboard.

## 🚀 Features

- **Blazing Fast Collection:** Uses `asyncio` and `aiohttp` to search across over 1,800+ sites simultaneously.
- **Dual Interface:** Run swift local scans via the CLI, or launch the web server for a rich Graphical User Interface.
- **Node Graph Intelligence:** Visualize relationships between targets, usernames, emails, and findings with force-directed graphs.
- **Dossier Generation:** Automatically compiles comprehensive intelligence reports.
- **Local & Private:** All your case data, targets, and evidence are stored locally in an SQLite database. Nothing is sent to third-party servers.

---

## 🛠️ Installation & Setup

Raven relies on **Python 3** for its backend core and **Node.js** for its frontend interface. 

### 1. Clone the Repository
```bash
git clone https://github.com/aasimxyz/raven.git
cd raven
```

### 2. Quick Setup (Windows)
Run the setup command from your terminal:
```bash
setup.bat
```
This script will automatically configure your Python virtual environment, install all backend dependencies, and compile the frontend React application.

### 3. Usage & Execution
Once setup is complete, you can use the platform directly! For the best experience, add the `raven` root folder to your Windows **Environment Variables (`PATH`)** to use the global `raven` command from any directory. Otherwise, you can just run `raven.bat` from the project folder.

---

## 📖 Usage

You can use Raven entirely from the terminal, or launch the Web UI.

### Command Line Interface

If you have added Raven to your PATH, simply run:

```text
> raven -help

Raven CLI

 Command            Explanation                      Example                   
 -h, -help, --help  Show this help message and exit  raven -help               
 -u, --username     Search by username               raven -u username         
 -e, --email        Search by email                  raven -e test@example.com 
 -p, --phone        Search by phone number           raven -p +1234567890      
 -web, --web        Start the web server             raven -web                
```

### Web Dashboard

To launch the interactive Intelligence Feed and Node Graph view:

```bash
raven -web
```
This will start the backend server and serve the React UI at `http://localhost:8000`.

---

## 🔒 Privacy & Data

All queries, evidence, and investigations are stored securely in `workspace/osint.db`. Your intelligence data never leaves your machine. 

## ⚖️ License

Distributed under the MIT License. See `LICENSE` for more information.
