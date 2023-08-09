#ifndef __CPPE__HPP__
#define __CPPE__HPP__

#include "boost/predef.h"

#if COMP_MSVC
    #define _GLIBCXX_HOSTED 1
    #include "import_std.hpp"
#else
    #if __has_cpp_attribute(__cpp_modules) && __has_cpp_attribute(__cpp_lib_modules)
        import std;
    #else
        #include "import_std.hpp"
    #endif
#endif

#include "control_flow.hpp"
#include "product_sum.hpp"

// Enables a more modern function syntax!
#ifndef fn
#define fn auto
#endif

#endif // __CPPE__HPP__