Howto setup

First get the clean spring sourcecode:

 git clone git://github.com/spring/spring.git spring

then get the springpyai code into the right folder

 git clone git://springpyai.git.sourceforge.net/gitroot/springpyai/springpyai spring/AI/Interfaces/Python

and link the nullpythonai to the right folder to get it compiled
 
 ln -s ../Interfaces/Python/test/NullPythonAI/ spring/AI/Skirmish/NullPythonAI 

That's it, when python is detected, the Interface will be compiled automaticly
