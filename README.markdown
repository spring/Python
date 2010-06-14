# Howto setup

1. Get the clean spring sourcecode:

		git clone git://github.com/spring/spring.git spring
		cd spring

2. Get the _Python AI Interface_ code into the right folder

		git clone git://github.com/spring/Python.git AI/Interfaces/Python

3. Link the _NullPythonAI_ to the right folder to get it compiled
 
		ln -s ../Interfaces/Python/test/NullPythonAI AI/Skirmish/NullPythonAI

That's it. When Python is detected, the AI Interface will be compiled
automaticly together with spring:

	cmake
	make

