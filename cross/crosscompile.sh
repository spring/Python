
#for cross-compiling install gcc-mingw32 >=4.4
#at ubuntu lucid this is the default

cd ../../../..

SPRINGSRC=`pwd`

echo output will be in ${SPRINGSRC}/dist

if [ ! -f win32.cmake ] ; then
cat > win32.cmake <<EOF
SET(CMAKE_SYSTEM_NAME Windows)
SET(CMAKE_C_COMPILER i586-mingw32msvc-gcc)
SET(CMAKE_CXX_COMPILER i586-mingw32msvc-g++)
SET(CMAKE_FIND_ROOT_PATH /usr/i586-mingw32msvc)
SET(MINGWLIBS ${SPRINGSRC}/mingwlibs)
SET(CMAKE_INSTALL_PREFIX  ${SPRINGSRC}/dist)
EOF
fi

if [ ! -d mingwlibs ]; then
	git clone git://github.com/spring/mingwlibs
	cd mingwlibs
	git checkout remotes/origin/boost_1.42.0_mingw_4.4.2
	git checkout boost_1.42.0_mingw_4.4.2
fi
cd ${SPRINGSRC}
cmake ${SPRINGSRC} "-DCMAKE_TOOLCHAIN_FILE=${SPRINGSRC}/win32.cmake"
make install
