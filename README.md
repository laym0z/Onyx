<p align="center">
    <img src="assets/Logo.png" height=200/>
</p>
<h1 align="center">Onyx</h1>


# 📝About the project


This code converts your Obsidian repository into a convenient website that you can host and share with others.


---

# 💻Installation


First, you need to copy the repository to your local computer, create a virtual environment, and install the components required for the project:

```
git clone https://github.com/laym0z/Converter.git
cd Converter
python3 -m venv venv

#activate on Windows
.\venv\Scripts\activate

#activate on Linux
source venv/bin/activate

#pip install on Windows
.\venv\Scripts\pip.exe install -r requirements.txt

#pip install on Linux
venv/bin/pip install -r requirements.txt
```

---

# ⚙️Command options


```
--src [PATH]    # the source obsidian vault
--dst [PATH]    # the destination foulder where is converted vault gonna be stored

--rc            # write and overwrite style.css
```

---

# 🎓Example of use

```
.\venv\Scripts\python.exe .\converter.py --src "D:\Source\Path" --dst "D:\Destination\Path" --rc
```

```
.\venv\Scripts\python.exe .\converter.py --src "D:\Source\Path" --dst "D:\Destination\Path"
```
