## How to Run (Takes 2 minutes)

```bash
# 1. Clone the project
git clone https://github.com/YOUR_USERNAME/command-gateway.git
cd command-gateway

# 2. Create virtual environment (recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# 3. Install dependencies
pip install flask sqlalchemy

# 4. Run the app
python app.py