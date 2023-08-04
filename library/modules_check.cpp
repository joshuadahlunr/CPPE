#include <iostream>

int main() {
    #if __has_cpp_attribute(__cpp_modules)
        return 0;
    #else
        return -1;
    #endif
}