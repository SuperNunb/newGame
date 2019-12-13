from distutils.core import setup
import py2exe

setup(console=['main.py'])

#setup(name = "NewGame" , 
   # version = "1.0" ,
    #options={"build_exe": {"packages":["pygame", "time", "random", "os"],
     #   "include_files":[
   #         "avatars.png", "backgroundSlice.png", "baddies.png", 
  #          "other.png", "statics.png", "levels.wav", "menu.wav", "boss.wav"
 #       ]}},
#    executables = [Executable("main.py")])