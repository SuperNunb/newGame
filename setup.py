from cx_Freeze import setup, Executable 

setup(name = "NewGame" , 
    version = "1.0" ,
    options={"build_exe": {"packages":["pygame", "time", "random", "os"],
        "include_files":[
            "img/avatars.png", "img/backgroundSlice.png", "img/baddies.png", 
            "img/other.png", "img/statics.png", "audio/levels.wav", "audio/menu.wav", "audio/boss.wav"
        ]}},
    executables = [Executable("main.py")])