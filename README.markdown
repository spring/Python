# Howto setup

1. Get the clean spring sourcecode:

		git clone git://github.com/spring/spring.git spring
		cd spring

2. Get the _Python AI Interface_ code into the right folder

		git clone git://github.com/spring/Python.git AI/Interfaces/Python

3. When Python is detected, the AI Interface will be compiled with spring:

		cmake .
		make

That's it!
