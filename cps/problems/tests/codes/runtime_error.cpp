#include <iostream>

using namespace std;

int main()
{
    /*
        This is actually a simple division by zero.
        Just making sure that it won't get detected by any optimizations
    */
    int x = 5;
    x--;
    cout << 1 / (x % (x / 2)) << endl;
}